import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import IngestionTask, Repository, User
from schemas import (
    RepositoryCreate,
    RepositoryResponse,
    RepositoryStats,
    RepositoryUpdate,
)
from services.auth import get_current_user

router = APIRouter(prefix="/repos", tags=["repositories"])


@router.get("", response_model=list[RepositoryResponse])
async def list_repositories(
    status: str | None = None,
    limit: int = 20,
    cursor: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Repository).order_by(Repository.created_at.desc()).limit(min(limit, 100))

    if status:
        query = query.where(Repository.status == status)
    if cursor:
        query = query.where(Repository.id < cursor)

    result = await db.execute(query)
    repos = result.scalars().all()
    return repos


@router.get("/{repo_id}", response_model=RepositoryResponse)
async def get_repository(
    repo_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = await db.get(Repository, repo_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@router.post("", response_model=RepositoryResponse, status_code=201)
async def create_repository(
    payload: RepositoryCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(Repository).where(Repository.github_id == payload.github_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Repository already exists")

    repo = Repository(
        id=str(uuid.uuid4()),
        github_id=payload.github_id,
        installation_id=payload.installation_id,
        name=payload.name,
        full_name=payload.full_name,
        owner=payload.owner,
        clone_url=payload.clone_url,
        default_branch=payload.default_branch,
        is_private=payload.is_private,
        language=payload.language,
        description=payload.description,
        settings=payload.settings.model_dump(),
        status="pending",
    )
    db.add(repo)
    await db.flush()
    await db.refresh(repo)
    return repo


@router.patch("/{repo_id}", response_model=RepositoryResponse)
async def update_repository(
    repo_id: str,
    payload: RepositoryUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = await db.get(Repository, repo_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not found")

    if payload.settings is not None:
        repo.settings = payload.settings.model_dump()
    if payload.status is not None:
        repo.status = payload.status

    await db.flush()
    await db.refresh(repo)
    return repo


@router.delete("/{repo_id}", status_code=204)
async def delete_repository(
    repo_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = await db.get(Repository, repo_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not found")

    await db.delete(repo)
    await db.flush()


@router.get("/{repo_id}/stats", response_model=RepositoryStats)
async def get_repository_stats(
    repo_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from models import CodeEdge, CodeNode

    repo = await db.get(Repository, repo_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not found")

    node_count = await db.scalar(
        select(func.count(CodeNode.id)).where(CodeNode.repo_id == repo_id)
    )
    edge_count = await db.scalar(
        select(func.count(CodeEdge.id)).where(CodeEdge.repo_id == repo_id)
    )

    type_result = await db.execute(
        select(CodeNode.type, func.count(CodeNode.id))
        .where(CodeNode.repo_id == repo_id)
        .group_by(CodeNode.type)
    )
    by_type = {row[0]: row[1] for row in type_result.all()}

    lang_result = await db.execute(
        select(CodeNode.language, func.count(CodeNode.id))
        .where(CodeNode.repo_id == repo_id, CodeNode.language.isnot(None))
        .group_by(CodeNode.language)
    )
    by_language = {row[0]: row[1] for row in lang_result.all()}

    last_task_result = await db.execute(
        select(IngestionTask)
        .where(IngestionTask.repo_id == repo_id)
        .order_by(IngestionTask.created_at.desc())
        .limit(1)
    )
    last_task = last_task_result.scalar_one_or_none()

    last_ingestion = None
    if last_task:
        last_ingestion = {
            "id": last_task.id,
            "status": last_task.status,
            "started_at": last_task.started_at.isoformat() if last_task.started_at else None,
            "completed_at": last_task.completed_at.isoformat() if last_task.completed_at else None,
            "files_processed": last_task.files_processed,
        }

    return RepositoryStats(
        node_count=node_count or 0,
        edge_count=edge_count or 0,
        by_type=by_type,
        by_language=by_language,
        last_ingestion=last_ingestion,
    )
