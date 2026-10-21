import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from models import GitHubInstallation, Issue, Repository
from schemas import WebhookResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def verify_signature(payload: bytes, signature: str | None) -> bool:
    if not signature:
        return False
    if not signature.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(
        settings.github_webhook_secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/github", response_model=WebhookResponse)
async def github_webhook(
    request: Request,
    x_github_event: str = Header(...),
    x_hub_signature_256: str = Header(...),
    x_github_delivery: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    body = await request.body()

    if not verify_signature(body, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from None

    logger.info("Received GitHub webhook: event=%s delivery=%s", x_github_event, x_github_delivery)

    if x_github_event == "installation":
        await _handle_installation(payload, db)
    elif x_github_event == "installation_repositories":
        await _handle_installation_repos(payload, db)
    elif x_github_event == "push":
        await _handle_push(payload, db)
    elif x_github_event == "issues":
        await _handle_issue(payload, db)
    elif x_github_event == "ping":
        pass

    return WebhookResponse(received=True, event=x_github_event, delivery_id=x_github_delivery)


async def _handle_installation(payload: dict, db: AsyncSession):
    action = payload.get("action")
    installation = payload.get("installation", {})
    account = installation.get("account", {})

    if action in ("created", "new_permissions_accepted"):
        existing = await db.execute(
            select(GitHubInstallation).where(
                GitHubInstallation.installation_id == installation.get("id")
            )
        )
        inst = existing.scalar_one_or_none()
        if inst is None:
            inst = GitHubInstallation(
                installation_id=installation.get("id"),
                github_account_name=account.get("login", ""),
                github_account_type=account.get("type", ""),
                permissions=installation.get("permissions", {}),
            )
            db.add(inst)
        else:
            inst.permissions = installation.get("permissions", {})
            inst.suspended = False

    elif action in ("deleted", "suspend"):
        existing = await db.execute(
            select(GitHubInstallation).where(
                GitHubInstallation.installation_id == installation.get("id")
            )
        )
        inst = existing.scalar_one_or_none()
        if inst:
            if action == "suspend":
                inst.suspended = True
            else:
                await db.delete(inst)

    await db.flush()


async def _handle_installation_repos(payload: dict, db: AsyncSession):
    installation_id = payload.get("installation", {}).get("id")
    repos_added = payload.get("repositories_added", [])
    repos_removed = payload.get("repositories_removed", [])

    for repo_data in repos_added:
        existing = await db.execute(
            select(Repository).where(Repository.github_id == repo_data.get("id"))
        )
        if existing.scalar_one_or_none() is None:
            full_name = repo_data.get("full_name", "")
            owner, name = full_name.split("/") if "/" in full_name else ("", full_name)
            repo = Repository(
                github_id=repo_data.get("id"),
                installation_id=installation_id,
                name=name,
                full_name=full_name,
                owner=owner,
                clone_url=f"https://github.com/{full_name}.git",
                is_private=repo_data.get("private", True),
            )
            db.add(repo)

    for repo_data in repos_removed:
        existing = await db.execute(
            select(Repository).where(Repository.github_id == repo_data.get("id"))
        )
        repo = existing.scalar_one_or_none()
        if repo:
            repo.status = "disabled"

    await db.flush()


async def _handle_push(payload: dict, db: AsyncSession):
    repo_full_name = payload.get("repository", {}).get("full_name", "")
    ref = payload.get("ref", "")
    after_sha = payload.get("after", "")

    if not ref.startswith("refs/heads/"):
        return

    branch = ref.replace("refs/heads/", "")

    existing = await db.execute(
        select(Repository).where(Repository.full_name == repo_full_name)
    )
    repo = existing.scalar_one_or_none()
    if repo is None or repo.status == "disabled":
        return

    logger.info("Push to %s branch=%s sha=%s — triggering incremental update", repo_full_name, branch, after_sha[:8])

    from tasks.ingestion_tasks import trigger_incremental_update

    await trigger_incremental_update(str(repo.id), branch, after_sha)


async def _handle_issue(payload: dict, db: AsyncSession):
    action = payload.get("action")
    if action not in ("opened", "edited", "reopened"):
        return

    issue_data = payload.get("issue", {})
    repo_data = payload.get("repository", {})

    existing = await db.execute(
        select(Repository).where(Repository.full_name == repo_data.get("full_name", ""))
    )
    repo = existing.scalar_one_or_none()
    if repo is None:
        return

    existing_issue = await db.execute(
        select(Issue).where(Issue.repo_id == repo.id, Issue.number == issue_data.get("number"))
    )

    issue = existing_issue.scalar_one_or_none()
    if issue:
        issue.title = issue_data.get("title", issue.title)
        issue.body = issue_data.get("body", issue.body)
        issue.state = issue_data.get("state", issue.state)
        issue.labels = [label.get("name") for label in issue_data.get("labels", [])]
    else:
        issue = Issue(
            repo_id=repo.id,
            github_issue_id=issue_data.get("id", 0),
            number=issue_data.get("number", 0),
            title=issue_data.get("title", ""),
            body=issue_data.get("body"),
            state=issue_data.get("state", "open"),
            labels=[label.get("name") for label in issue_data.get("labels", [])],
            assignees=[a.get("login") for a in issue_data.get("assignees", [])],
            author=issue_data.get("user", {}).get("login"),
            url=issue_data.get("html_url"),
        )
        db.add(issue)

    await db.flush()
