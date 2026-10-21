import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import IngestionTask, Repository, User
from schemas import IngestionStatusResponse, IngestionTrigger
from services.auth import get_current_user

router = APIRouter(prefix="/repos/{repo_id}/ingest", tags=["ingestion"])


@router.post("/trigger", response_model=IngestionStatusResponse, status_code=202)
async def trigger_ingestion(
    repo_id: str,
    payload: IngestionTrigger,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = await db.get(Repository, repo_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not found")

    active_task = await db.execute(
        select(IngestionTask).where(
            IngestionTask.repo_id == repo_id,
            IngestionTask.status.in_(["queued", "running"]),
        )
    )
    if active_task.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Ingestion already in progress")

    task = IngestionTask(
        id=str(uuid.uuid4()),
        repo_id=repo_id,
        triggered_by=user.id,
        mode=payload.mode,
        status="queued",
        branch=payload.branch or repo.default_branch,
        progress=0,
    )
    db.add(task)
    repo.status = "analyzing"
    await db.flush()
    await db.refresh(task)

    background_tasks.add_task(_run_ingestion, task.id, repo_id, payload.mode, payload.branch)

    return task


@router.get("/status", response_model=IngestionStatusResponse | None)
async def get_ingestion_status(
    repo_id: str,
    task_id: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(IngestionTask).where(IngestionTask.repo_id == repo_id)

    if task_id:
        query = query.where(IngestionTask.id == task_id)
    else:
        query = query.order_by(IngestionTask.created_at.desc())

    query = query.limit(1)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def _run_ingestion(task_id: str, repo_id: str, mode: str, branch: str | None):
    from tasks.ingestion_tasks import run_ingestion_pipeline

    try:
        await run_ingestion_pipeline(task_id, repo_id, mode, branch)
    except Exception as e:
        from database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            task = await session.get(IngestionTask, task_id)
            if task:
                task.status = "failed"
                task.error = str(e)
            repo = await session.get(Repository, repo_id)
            if repo:
                repo.status = "error"
                repo.error_message = str(e)
            await session.commit()
