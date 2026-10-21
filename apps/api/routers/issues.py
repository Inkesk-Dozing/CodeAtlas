import logging
import time
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal, get_db
from models import Issue, IssueMapping, MappingFeedback, Repository, User
from schemas import (
    CodeMapping,
    CodeNodeResponse,
    IssueAnalyzeRequest,
    IssueMappingResponse,
    IssueResponse,
    MappingFeedbackRequest,
)
from services.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/repos/{repo_id}/issues", tags=["issues"])


async def _verify_repo(repo_id: str, db: AsyncSession) -> Repository:
    repo = await db.get(Repository, repo_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@router.get("", response_model=list[IssueResponse])
async def list_issues(
    repo_id: str,
    state: str = "open",
    limit: int = 30,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _verify_repo(repo_id, db)

    query = (
        select(Issue)
        .where(Issue.repo_id == repo_id, Issue.state == state)
        .order_by(Issue.number.desc())
        .limit(min(limit, 100))
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/{issue_number}/analyze", status_code=202)
async def analyze_issue(
    repo_id: str,
    issue_number: int,
    payload: IssueAnalyzeRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _verify_repo(repo_id, db)

    existing = await db.execute(
        select(IssueMapping)
        .join(Issue, IssueMapping.issue_id == Issue.id)
        .where(Issue.repo_id == repo_id, Issue.number == issue_number)
    )
    existing_mapping = existing.scalar_one_or_none()

    if existing_mapping and not payload.force_refresh and existing_mapping.status in (
        "completed",
        "processing",
    ):
        return {"task_id": existing_mapping.id, "status": existing_mapping.status}

    issue = await db.execute(
        select(Issue).where(Issue.repo_id == repo_id, Issue.number == issue_number)
    )
    issue_obj = issue.scalar_one_or_none()
    if issue_obj is None:
        raise HTTPException(status_code=404, detail="Issue not found")

    if existing_mapping:
        existing_mapping.status = "processing"
        existing_mapping.mappings = []
        existing_mapping.generated_at = None
    else:
        mapping = IssueMapping(
            id=str(uuid.uuid4()),
            issue_id=issue_obj.id,
            repo_id=repo_id,
            status="processing",
            mappings=[],
        )
        db.add(mapping)
        existing_mapping = mapping

    await db.flush()

    background_tasks.add_task(_run_issue_mapping, existing_mapping.id, repo_id, issue_number)

    return {"task_id": existing_mapping.id, "status": "processing"}


async def _run_issue_mapping(mapping_id: str, repo_id: str, issue_number: int) -> None:
    from services.mapping.ranker import MODEL_VERSION, IssueMapper

    started = time.time()
    try:
        async with AsyncSessionLocal() as session:
            mapping = await session.get(IssueMapping, mapping_id)
            issue = await session.scalar(
                select(Issue).where(Issue.repo_id == repo_id, Issue.number == issue_number)
            )
            if mapping is None or issue is None:
                return

            mapper = IssueMapper(session, repo_id)
            results = await mapper.analyze(issue)

            payload = []
            for r in results:
                payload.append(
                    CodeMapping(
                        node=CodeNodeResponse.model_validate(r.pop("node")),
                        **r,
                    ).model_dump(mode="json")
                )

            mapping.mappings = payload
            mapping.status = "completed"
            mapping.model_version = MODEL_VERSION
            mapping.generation_ms = int((time.time() - started) * 1000)
            mapping.generated_at = datetime.now(UTC)
            await session.commit()
    except Exception:
        logger.exception("issue mapping failed for %s#%s", repo_id, issue_number)
        async with AsyncSessionLocal() as session:
            mapping = await session.get(IssueMapping, mapping_id)
            if mapping:
                mapping.status = "failed"
                await session.commit()


@router.get("/{issue_number}/mapping", response_model=IssueMappingResponse | None)
async def get_issue_mapping(
    repo_id: str,
    issue_number: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _verify_repo(repo_id, db)

    query = (
        select(IssueMapping)
        .join(Issue, IssueMapping.issue_id == Issue.id)
        .where(Issue.repo_id == repo_id, Issue.number == issue_number)
        .order_by(IssueMapping.created_at.desc())
        .limit(1)
    )
    result = await db.execute(query)
    mapping = result.scalar_one_or_none()

    if mapping is None:
        return None

    return IssueMappingResponse(
        issue_number=issue_number,
        status=mapping.status,
        mappings=mapping.mappings,
        model_version=mapping.model_version,
        generated_at=mapping.generated_at,
    )


@router.post("/{issue_number}/feedback", status_code=201)
async def submit_feedback(
    repo_id: str,
    issue_number: int,
    payload: MappingFeedbackRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _verify_repo(repo_id, db)

    query = (
        select(IssueMapping)
        .join(Issue, IssueMapping.issue_id == Issue.id)
        .where(Issue.repo_id == repo_id, Issue.number == issue_number)
        .order_by(IssueMapping.created_at.desc())
        .limit(1)
    )
    result = await db.execute(query)
    mapping = result.scalar_one_or_none()

    if mapping is None:
        raise HTTPException(status_code=404, detail="No mapping found for this issue")

    feedback = MappingFeedback(
        id=str(uuid.uuid4()),
        mapping_id=mapping.id,
        node_id=payload.node_id,
        user_id=user.id,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(feedback)
    await db.flush()
    return {"status": "recorded"}
