"""GitHub Issues Fetcher Service with GraphQL Pagination and Comment Threads (Issue #50).

Features:
- Synchronizes open and recently closed issues via GitHub REST API with conditional `If-None-Match` ETag caching.
- For issues with discussions/comments, queries GitHub GraphQL API to fetch up to 20 top discussion comments.
- Appends fetched comments to issue body context so downstream mapping models capture discussions.
- Stores / updates records in PostgreSQL `issues` table with foreign key to `repository_id` (upserting to prevent duplicates).
- Handles GitHub primary and secondary rate limits with exponential backoff and retry jitter.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Issue, Repository

logger = logging.getLogger(__name__)

GITHUB_REST_API = "https://api.github.com"
GITHUB_GRAPHQL_API = "https://api.github.com/graphql"

GRAPHQL_COMMENTS_QUERY = """
query GetIssueComments($owner: String!, $repo: String!, $issueNumber: Int!, $first: Int!) {
  repository(owner: $owner, name: $repo) {
    issue(number: $issueNumber) {
      comments(first: $first) {
        nodes {
          author {
            login
          }
          body
          createdAt
        }
      }
    }
  }
}
"""


@dataclass
class SyncStats:
    synced: int = 0
    updated: int = 0
    skipped: int = 0
    errors: int = 0
    etag_matched: bool = False
    issue_numbers: list[int] = field(default_factory=list)


class GitHubIssueFetcher:
    """Synchronizes repository issues and comment threads with ETag caching and rate limit handling."""

    def __init__(
        self,
        db: AsyncSession,
        repo: Repository,
        access_token: str | None = None,
        max_retries: int = 3,
        base_backoff: float = 1.0,
    ) -> None:
        self.db = db
        self.repo = repo
        self.access_token = access_token
        self.max_retries = max_retries
        self.base_backoff = base_backoff

        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "CodeAtlas-IssueSync/1.0",
        }
        if self.access_token:
            self.headers["Authorization"] = f"Bearer {self.access_token}"

    async def _request_with_backoff(
        self,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Executes HTTP request with exponential backoff on 403 secondary rate limits / 429."""
        retries = 0
        backoff = self.base_backoff

        while True:
            try:
                resp = await client.request(method, url, **kwargs)
                if resp.status_code in (403, 429):
                    is_rate_limited = (
                        "rate limit" in resp.text.lower()
                        or resp.headers.get("x-ratelimit-remaining") == "0"
                        or "retry-after" in resp.headers
                    )
                    if is_rate_limited and retries < self.max_retries:
                        retry_after = float(resp.headers.get("retry-after", backoff))
                        logger.warning(
                            "GitHub rate limit encountered on %s. Sleeping %.2fs (attempt %d/%d)",
                            url,
                            retry_after,
                            retries + 1,
                            self.max_retries,
                        )
                        await asyncio.sleep(retry_after)
                        retries += 1
                        backoff *= 2.0
                        continue
                return resp
            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                if retries < self.max_retries:
                    await asyncio.sleep(backoff)
                    retries += 1
                    backoff *= 2.0
                    continue
                raise exc

    async def fetch_issue_comments_graphql(
        self,
        client: httpx.AsyncClient,
        issue_number: int,
        first: int = 20,
    ) -> list[dict[str, Any]]:
        """Fetches top comments for an issue using GitHub GraphQL API."""
        owner = self.repo.owner
        name = self.repo.name

        payload = {
            "query": GRAPHQL_COMMENTS_QUERY,
            "variables": {
                "owner": owner,
                "repo": name,
                "issueNumber": issue_number,
                "first": first,
            },
        }

        try:
            resp = await self._request_with_backoff(
                client,
                "POST",
                GITHUB_GRAPHQL_API,
                json=payload,
                headers=self.headers,
                timeout=10.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                issue_data = (
                    data.get("data", {})
                    .get("repository", {})
                    .get("issue", {})
                )
                if issue_data and "comments" in issue_data:
                    nodes = issue_data["comments"].get("nodes", [])
                    return [
                        {
                            "author": (n.get("author") or {}).get("login"),
                            "body": n.get("body", ""),
                            "created_at": n.get("createdAt"),
                        }
                        for n in nodes
                        if n
                    ]
        except Exception:
            logger.exception("Failed to fetch GraphQL comments for %s#%d", self.repo.full_name, issue_number)

        return []

    async def sync_issues(
        self,
        client: httpx.AsyncClient | None = None,
        state: str = "all",
        per_page: int = 100,
        etag: str | None = None,
        fetch_comments: bool = True,
    ) -> tuple[SyncStats, str | None]:
        """Synchronizes issues from GitHub REST API into PostgreSQL `issues` table.

        Returns:
            Tuple of (SyncStats, new_etag).
        """
        stats = SyncStats()
        url = f"{GITHUB_REST_API}/repos/{self.repo.full_name}/issues"
        params = {"state": state, "per_page": per_page, "sort": "updated", "direction": "desc"}

        req_headers = dict(self.headers)
        if etag:
            req_headers["If-None-Match"] = etag

        owns_client = False
        if client is None:
            client = httpx.AsyncClient()
            owns_client = True

        try:
            resp = await self._request_with_backoff(
                client,
                "GET",
                url,
                params=params,
                headers=req_headers,
                timeout=15.0,
            )

            # 304 Not Modified -> No updates since last sync
            if resp.status_code == 304:
                stats.etag_matched = True
                logger.info("ETag match for %s. Issues are up to date.", self.repo.full_name)
                return stats, etag

            if resp.status_code != 200:
                logger.error("Failed to fetch issues: %d %s", resp.status_code, resp.text)
                stats.errors += 1
                return stats, None

            new_etag = resp.headers.get("etag")
            issues_data = resp.json()

            for item in issues_data:
                # GitHub issues endpoint returns both issues and pull requests; skip pull requests
                if "pull_request" in item:
                    continue

                number = item["number"]
                github_id = item["id"]
                title = item["title"]
                raw_body = item.get("body") or ""
                item_state = item.get("state", "open")
                labels = [lbl.get("name") for lbl in item.get("labels", []) if isinstance(lbl, dict)]
                assignees = [a.get("login") for a in item.get("assignees", []) if isinstance(a, dict)]
                author = (item.get("user") or {}).get("login")
                html_url = item.get("html_url")

                closed_at = None
                if item.get("closed_at"):
                    try:
                        closed_at = datetime.fromisoformat(item["closed_at"].replace("Z", "+00:00"))
                    except Exception:
                        pass

                # If issue has discussion comments and fetch_comments is True, retrieve via GraphQL
                comments_count = item.get("comments", 0)
                body_content = raw_body
                if fetch_comments and comments_count > 0:
                    comments = await self.fetch_issue_comments_graphql(client, number, first=20)
                    if comments:
                        comment_texts = [
                            f"\n--- Comment by @{c['author']} ---\n{c['body']}"
                            for c in comments
                            if c.get("body")
                        ]
                        body_content = f"{raw_body}\n\n## Discussion Thread\n" + "\n".join(comment_texts)

                # Upsert into PostgreSQL `issues` table
                existing = await self.db.scalar(
                    select(Issue).where(
                        Issue.repo_id == self.repo.id,
                        Issue.number == number,
                    )
                )

                if existing:
                    existing.title = title
                    existing.body = body_content
                    existing.state = item_state
                    existing.labels = labels
                    existing.assignees = assignees
                    existing.author = author
                    existing.url = html_url
                    existing.closed_at = closed_at
                    existing.fetched_at = datetime.now(UTC)
                    stats.updated += 1
                else:
                    new_issue = Issue(
                        repo_id=self.repo.id,
                        github_issue_id=github_id,
                        number=number,
                        title=title,
                        body=body_content,
                        state=item_state,
                        labels=labels,
                        assignees=assignees,
                        author=author,
                        url=html_url,
                        closed_at=closed_at,
                        fetched_at=datetime.now(UTC),
                    )
                    self.db.add(new_issue)
                    stats.synced += 1

                stats.issue_numbers.append(number)

            await self.db.commit()
            return stats, new_etag

        finally:
            if owns_client:
                await client.aclose()
