"""Tests for repository health check and ingestion failure rollback."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from main import app
from models import IngestionError, IngestionTask, Repository, User
from services.auth import create_access_token, get_current_user


@pytest.fixture
def auth_headers():
    token = create_access_token(user_id="test-user-id", role="admin")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def override_current_user():
    mock_user = User(
        id="test-user-id",
        github_id=999,
        username="testuser",
        email="test@example.com",
    )
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_repository_health_endpoint_not_found(auth_headers):
    mock_session = AsyncMock()
    mock_session.get.return_value = None

    async def _override_get_db():
        yield mock_session

    from database import get_db

    app.dependency_overrides[get_db] = _override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/repos/non-existent-id/ingest/health", headers=auth_headers)
            assert resp.status_code == 404
            assert resp.json()["detail"] == "Repository not found"
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_repository_health_success(auth_headers):
    mock_repo = Repository(
        id="repo-123",
        github_id=12345,
        installation_id=67890,
        name="test-repo",
        full_name="org/test-repo",
        owner="org",
        clone_url="https://github.com/org/test-repo.git",
        status="ready",
        node_count=150,
        edge_count=320,
    )
    mock_error = IngestionError(
        id="err-1",
        repo_id="repo-123",
        task_id="task-1",
        error_stage="embed",
        error_message="OOM during batch embedding",
        traceback="Traceback...",
        details={"stage": "embed"},
    )

    from unittest.mock import MagicMock

    from database import get_db

    mock_session = AsyncMock()
    mock_session.get.return_value = mock_repo

    mock_errors_result = MagicMock()
    mock_errors_result.scalars.return_value.all.return_value = [mock_error]
    mock_session.execute.return_value = mock_errors_result

    async def _override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = _override_get_db

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/repos/repo-123/ingest/health", headers=auth_headers)
            assert resp.status_code == 200
            data = resp.json()
            assert data["repo_id"] == "repo-123"
            assert data["status"] == "ready"
            assert data["health"] == "healthy"
            assert data["node_count"] == 150
            assert data["active_graph_valid"] is True
            assert len(data["recent_errors"]) == 1
            assert data["recent_errors"][0]["error_stage"] == "embed"
            assert "OOM" in data["recent_errors"][0]["error_message"]
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_ingestion_rollback_preserves_active_graph():
    from tasks.ingestion_tasks import run_ingestion_pipeline

    repo = Repository(
        id="repo-rollback-test",
        github_id=99999,
        installation_id=11111,
        name="rollback-repo",
        full_name="org/rollback-repo",
        owner="org",
        clone_url="https://github.com/org/rollback-repo.git",
        default_branch="main",
        status="ready",
        node_count=80,
        edge_count=120,
        settings={},
    )
    task = IngestionTask(
        id="task-fail-test",
        repo_id=repo.id,
        mode="full",
        status="queued",
        current_stage="clone",
        progress=0,
    )

    mock_session = AsyncMock()

    async def _mock_get(entity_class, entity_id):
        if entity_class == Repository:
            return repo
        if entity_class == IngestionTask:
            return task
        return None

    mock_session.get = AsyncMock(side_effect=_mock_get)
    mock_session.commit = AsyncMock()

    with patch("tasks.ingestion_tasks.AsyncSessionLocal") as mock_session_local, \
         patch("tasks.ingestion_tasks._clone_repository", side_effect=RuntimeError("Simulated clone network timeout")):
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_session
        mock_ctx.__aexit__.return_value = None
        mock_session_local.return_value = mock_ctx

        with pytest.raises(RuntimeError, match="Simulated clone network timeout"):
            await run_ingestion_pipeline("task-fail-test", "repo-rollback-test", "full", None)

        # Verify task is marked failed
        assert task.status == "failed"
        assert "Simulated clone network timeout" in task.error
        assert task.error_stage == "clone"

        # Verify rollback preserved active graph since node_count > 0
        assert repo.status == "ready"
        assert repo.node_count == 80
        assert "Simulated clone network timeout" in repo.error_message

        # Verify IngestionError was recorded
        added_objs = [call.args[0] for call in mock_session.add.call_args_list]
        error_records = [obj for obj in added_objs if isinstance(obj, IngestionError)]
        assert len(error_records) == 1
        assert error_records[0].error_stage == "clone"
        assert "Simulated clone network timeout" in error_records[0].error_message


@pytest.mark.asyncio
async def test_ingestion_failure_without_previous_graph():
    from tasks.ingestion_tasks import run_ingestion_pipeline

    repo = Repository(
        id="repo-new-fail",
        github_id=88888,
        installation_id=22222,
        name="new-fail-repo",
        full_name="org/new-fail-repo",
        owner="org",
        clone_url="https://github.com/org/new-fail-repo.git",
        default_branch="main",
        status="pending",
        node_count=0,
        edge_count=0,
        settings={},
    )
    task = IngestionTask(
        id="task-new-fail",
        repo_id=repo.id,
        mode="full",
        status="queued",
        current_stage="clone",
        progress=0,
    )

    mock_session = AsyncMock()

    async def _mock_get(entity_class, entity_id):
        if entity_class == Repository:
            return repo
        if entity_class == IngestionTask:
            return task
        return None

    mock_session.get = AsyncMock(side_effect=_mock_get)
    mock_session.commit = AsyncMock()

    with patch("tasks.ingestion_tasks.AsyncSessionLocal") as mock_session_local, \
         patch("tasks.ingestion_tasks._clone_repository", side_effect=RuntimeError("Parsing corrupted AST")):
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_session
        mock_ctx.__aexit__.return_value = None
        mock_session_local.return_value = mock_ctx

        with pytest.raises(RuntimeError, match="Parsing corrupted AST"):
            await run_ingestion_pipeline("task-new-fail", "repo-new-fail", "full", None)

        # For a brand new repo with 0 nodes, status becomes error
        assert repo.status == "error"
        assert task.status == "failed"


@pytest.mark.asyncio
async def test_retry_failed_ingestion(auth_headers):
    mock_repo = Repository(
        id="repo-retry",
        github_id=33333,
        installation_id=44444,
        name="retry-repo",
        full_name="org/retry-repo",
        owner="org",
        clone_url="https://github.com/org/retry-repo.git",
        default_branch="main",
        status="error",
        error_message="Previous failure",
    )

    from unittest.mock import MagicMock

    from database import get_db

    mock_session = AsyncMock()
    mock_session.get.return_value = mock_repo

    mock_active_query = MagicMock()
    mock_active_query.scalar_one_or_none.return_value = None

    mock_last_task = MagicMock()
    mock_last_task.scalar_one_or_none.return_value = None

    mock_session.execute.side_effect = [mock_active_query, mock_last_task]

    async def _override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = _override_get_db

    try:
        with patch("routers.ingestion._run_ingestion"):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post("/api/v1/repos/repo-retry/ingest/retry", headers=auth_headers)
                assert resp.status_code == 202
                data = resp.json()
                assert data["repo_id"] == "repo-retry"
                assert data["status"] == "queued"
                assert mock_repo.status == "analyzing"
    finally:
        app.dependency_overrides.pop(get_db, None)

