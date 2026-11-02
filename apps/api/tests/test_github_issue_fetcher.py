"""Unit tests for GitHub Issues Fetcher Service with GraphQL & ETag Caching (Issue #50)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from models import Issue, Repository
from services.github.issue_fetcher import (
    GITHUB_GRAPHQL_API,
    GitHubIssueFetcher,
)


@pytest.fixture
def mock_repo() -> Repository:
    repo = MagicMock(spec=Repository)
    repo.id = "repo_test_123"
    repo.owner = "Inkesk-Dozing"
    repo.name = "CodeAtlas"
    repo.full_name = "Inkesk-Dozing/CodeAtlas"
    return repo


@pytest.mark.asyncio
async def test_etag_caching_returns_not_modified(mock_repo: Repository) -> None:
    mock_db = AsyncMock()
    fetcher = GitHubIssueFetcher(db=mock_db, repo=mock_repo, access_token="fake_token")

    # Mock 304 Not Modified
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 304

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.return_value = mock_resp

    stats, new_etag = await fetcher.sync_issues(
        client=mock_client,
        etag='"etag_cache_123"',
    )

    # Acceptance criteria: ETag match skips redundant parsing
    assert stats.etag_matched is True
    assert stats.synced == 0
    assert stats.updated == 0
    assert new_etag == '"etag_cache_123"'


@pytest.mark.asyncio
async def test_sync_issues_creates_and_updates_without_duplicate_keys(mock_repo: Repository) -> None:
    mock_db = AsyncMock()
    fetcher = GitHubIssueFetcher(db=mock_db, repo=mock_repo, access_token="fake_token")

    # Mock REST response with 2 issues (one new, one existing)
    mock_rest_resp = MagicMock(spec=httpx.Response)
    mock_rest_resp.status_code = 200
    mock_rest_resp.headers = {"etag": '"etag_new_456"'}
    mock_rest_resp.json.return_value = [
        {
            "id": 101,
            "number": 1,
            "title": "Bug in login auth",
            "body": "User cannot sign in",
            "state": "open",
            "labels": [{"name": "bug"}],
            "assignees": [{"login": "alice"}],
            "user": {"login": "bob"},
            "html_url": "https://github.com/org/repo/issues/1",
            "comments": 2,
        },
        {
            "id": 102,
            "number": 2,
            "title": "A pull request item",
            "pull_request": {"url": "https://api.github.com/repos/org/repo/pulls/2"},
        },
    ]

    # Mock GraphQL response for issue comments
    mock_graphql_resp = MagicMock(spec=httpx.Response)
    mock_graphql_resp.status_code = 200
    mock_graphql_resp.json.return_value = {
        "data": {
            "repository": {
                "issue": {
                    "comments": {
                        "nodes": [
                            {
                                "author": {"login": "charlie"},
                                "body": "Fixed in PR #5",
                                "createdAt": "2026-11-01T12:00:00Z",
                            }
                        ]
                    }
                }
            }
        }
    }

    # Dispatch request based on URL
    async def fake_request(method: str, url: str, **kwargs):
        if url == GITHUB_GRAPHQL_API:
            return mock_graphql_resp
        return mock_rest_resp

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.side_effect = fake_request

    # Existing issue in database
    existing_issue = MagicMock(spec=Issue)
    existing_issue.number = 1
    mock_db.scalar.return_value = existing_issue

    stats, new_etag = await fetcher.sync_issues(client=mock_client, fetch_comments=True)

    # Acceptance criteria:
    # 1. Updates existing issue record on subsequent syncs without duplicate keys
    assert stats.updated == 1
    assert stats.synced == 0
    assert 1 in stats.issue_numbers
    # Pull requests should be filtered out
    assert 2 not in stats.issue_numbers
    # Comment thread attached to body
    assert "## Discussion Thread" in existing_issue.body
    assert "@charlie" in existing_issue.body
    assert new_etag == '"etag_new_456"'
    mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_rate_limit_backoff_handling(mock_repo: Repository) -> None:
    mock_db = AsyncMock()
    fetcher = GitHubIssueFetcher(
        db=mock_db,
        repo=mock_repo,
        access_token="fake_token",
        max_retries=2,
        base_backoff=0.01,
    )

    # First attempt: 403 secondary rate limit with Retry-After header
    # Second attempt: 200 OK empty list
    resp_rate_limited = MagicMock(spec=httpx.Response)
    resp_rate_limited.status_code = 403
    resp_rate_limited.headers = {"retry-after": "0.01"}
    resp_rate_limited.text = "You have exceeded a secondary rate limit"

    resp_ok = MagicMock(spec=httpx.Response)
    resp_ok.status_code = 200
    resp_ok.headers = {"etag": '"etag_recovered"'}
    resp_ok.json.return_value = []

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.side_effect = [resp_rate_limited, resp_ok]

    stats, new_etag = await fetcher.sync_issues(client=mock_client)

    # Acceptance criteria: Handles rate limits with exponential backoff & succeeds
    assert stats.errors == 0
    assert new_etag == '"etag_recovered"'
    assert mock_client.request.call_count == 2
