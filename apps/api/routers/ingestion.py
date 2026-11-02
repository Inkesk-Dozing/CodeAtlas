import uuid

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import IngestionError, IngestionTask, Repository, User
from schemas import (
    IngestionErrorResponse,
    IngestionStatusResponse,
    IngestionTrigger,
    RepositoryHealthResponse,
)
from services.auth import get_current_user
from services.ingestion.broadcaster import progress_broadcaster

router = APIRouter(prefix="/repos/{repo_id}/ingest", tags=["ingestion"])


@router.websocket("/ws")
async def ingestion_progress_ws(
    websocket: WebSocket,
    repo_id: str,
):
    """Real-time ingestion pipeline progress tracking WebSocket stream."""
    await websocket.accept()

    # Emit latest cached state if available
    latest = progress_broadcaster.get_latest(repo_id)
    if latest:
        try:
            await websocket.send_json(latest)
        except Exception:
            return

    try:
        async for event in progress_broadcaster.subscribe(repo_id):
            await websocket.send_json(event)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


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
        files_total=0,
        files_processed=0,
        nodes_created=0,
        edges_created=0,
        stage_timings={},
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


@router.get("/health", response_model=RepositoryHealthResponse)
async def get_repository_health(
    repo_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = await db.get(Repository, repo_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not found")

    errors_result = await db.execute(
        select(IngestionError)
        .where(IngestionError.repo_id == repo_id)
        .order_by(IngestionError.created_at.desc())
        .limit(10)
    )
    errors = errors_result.scalars().all()

    active_graph_valid = repo.status in ("ready", "analyzing") and repo.node_count > 0
    health = "healthy" if repo.status == "ready" else ("degraded" if active_graph_valid else "broken")

    return RepositoryHealthResponse(
        repo_id=repo_id,
        status=repo.status,
        health=health,
        node_count=repo.node_count,
        edge_count=repo.edge_count,
        last_analyzed_at=repo.last_analyzed_at,
        active_graph_valid=active_graph_valid,
        recent_errors=[
            IngestionErrorResponse(
                id=err.id,
                repo_id=err.repo_id,
                task_id=err.task_id,
                error_stage=err.error_stage,
                error_message=err.error_message,
                traceback=err.traceback,
                details=err.details,
                created_at=err.created_at,
            )
            for err in errors
        ],
    )


@router.get("/errors", response_model=list[IngestionErrorResponse])
async def list_ingestion_errors(
    repo_id: str,
    limit: int = 20,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = await db.get(Repository, repo_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not found")

    result = await db.execute(
        select(IngestionError)
        .where(IngestionError.repo_id == repo_id)
        .order_by(IngestionError.created_at.desc())
        .limit(min(limit, 100))
    )
    errors = result.scalars().all()
    return [
        IngestionErrorResponse(
            id=err.id,
            repo_id=err.repo_id,
            task_id=err.task_id,
            error_stage=err.error_stage,
            error_message=err.error_message,
            traceback=err.traceback,
            details=err.details,
            created_at=err.created_at,
        )
        for err in errors
    ]


@router.post("/retry", response_model=IngestionStatusResponse, status_code=202)
async def retry_failed_ingestion(
    repo_id: str,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = await db.get(Repository, repo_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Check if there is an active running task
    active_task = await db.execute(
        select(IngestionTask).where(
            IngestionTask.repo_id == repo_id,
            IngestionTask.status.in_(["queued", "running"]),
        )
    )
    if active_task.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Ingestion already in progress")

    # Get last task to inherit branch or default branch
    last_task = (
        await db.execute(
            select(IngestionTask)
            .where(IngestionTask.repo_id == repo_id)
            .order_by(IngestionTask.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    target_branch = (last_task.branch if last_task and last_task.branch else repo.default_branch)

    task = IngestionTask(
        id=str(uuid.uuid4()),
        repo_id=repo_id,
        triggered_by=user.id,
        mode="full",
        status="queued",
        branch=target_branch,
        progress=0,
        files_total=0,
        files_processed=0,
        nodes_created=0,
        edges_created=0,
        stage_timings={},
    )
    db.add(task)
    repo.status = "analyzing"
    await db.flush()
    await db.refresh(task)

    background_tasks.add_task(_run_ingestion, task.id, repo_id, "full", target_branch)
    return task



async def _run_ingestion(task_id: str, repo_id: str, mode: str, branch: str | None):
    from tasks.ingestion_tasks import run_ingestion_pipeline

    try:
        await run_ingestion_pipeline(task_id, repo_id, mode, branch)
    except Exception as e:
        import traceback

        from database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            task = await session.get(IngestionTask, task_id)
            if task:
                task.status = "failed"
                task.error = str(e)
            repo = await session.get(Repository, repo_id)
            if repo:
                # If repository already has an active graph, preserve it in ready/degraded state
                if repo.node_count > 0:
                    repo.status = "ready"
                else:
                    repo.status = "error"
                repo.error_message = str(e)

            # Record IngestionError
            error_log = IngestionError(
                repo_id=repo_id,
                task_id=task_id,
                error_stage=task.current_stage if task else "unknown",
                error_message=str(e),
                traceback=traceback.format_exc(),
                details={"mode": mode, "branch": branch},
            )
            session.add(error_log)
            await session.commit()
