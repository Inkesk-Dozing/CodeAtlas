"""Tests for real-time ingestion pipeline progress tracking via WebSocket & Broadcaster."""

import asyncio

import pytest
from starlette.testclient import TestClient

from main import app
from services.ingestion.broadcaster import IngestionBroadcaster, progress_broadcaster


@pytest.mark.asyncio
async def test_monotonic_progress_enforcement():
    broadcaster = IngestionBroadcaster()
    task_id = "test-monotonic-task"

    assert broadcaster._enforce_monotonic_progress(task_id, 0) == 0
    assert broadcaster._enforce_monotonic_progress(task_id, 10) == 10
    assert broadcaster._enforce_monotonic_progress(task_id, 40) == 40
    # Attempting to decrease progress should be clamped to previous max
    assert broadcaster._enforce_monotonic_progress(task_id, 25) == 40
    assert broadcaster._enforce_monotonic_progress(task_id, 65) == 65
    assert broadcaster._enforce_monotonic_progress(task_id, 90) == 90
    assert broadcaster._enforce_monotonic_progress(task_id, 100) == 100
    # Progress above 100 should be clamped to 100
    assert broadcaster._enforce_monotonic_progress(task_id, 120) == 100


@pytest.mark.asyncio
async def test_broadcaster_pub_sub_distribution():
    broadcaster = IngestionBroadcaster()
    repo_id = "repo-sync-test"
    task_id = "task-sync-1"

    received_events = []

    async def _listener():
        async for event in broadcaster.subscribe(repo_id, timeout=2.0):
            received_events.append(event)
            if event.get("type") == "completed":
                break

    listener_task = asyncio.create_task(_listener())
    await asyncio.sleep(0.05)

    await broadcaster.publish_stage_transition(
        repo_id=repo_id,
        task_id=task_id,
        stage="clone",
        progress=0,
        files_total=5,
    )
    await broadcaster.publish_progress(
        repo_id=repo_id,
        task_id=task_id,
        stage="parse",
        progress=40,
        files_total=5,
        files_processed=5,
    )
    await broadcaster.publish_completed(
        repo_id=repo_id,
        task_id=task_id,
        nodes_created=50,
        edges_created=120,
        stage_timings={"clone": 0.2, "parse": 0.5},
    )

    await listener_task

    assert len(received_events) == 3
    assert received_events[0]["type"] == "stage_transition"
    assert received_events[0]["stage"] == "clone"
    assert received_events[0]["progress"] == 0

    assert received_events[1]["type"] == "progress"
    assert received_events[1]["stage"] == "parse"
    assert received_events[1]["progress"] == 40

    assert received_events[2]["type"] == "completed"
    assert received_events[2]["progress"] == 100
    assert received_events[2]["nodes_created"] == 50
    assert received_events[2]["edges_created"] == 120


@pytest.mark.asyncio
async def test_broadcaster_failure_event():
    broadcaster = IngestionBroadcaster()
    repo_id = "repo-fail-test"
    task_id = "task-fail-1"

    received = []

    async def _listener():
        async for event in broadcaster.subscribe(repo_id, timeout=2.0):
            received.append(event)
            if event.get("type") == "failed":
                break

    task = asyncio.create_task(_listener())
    await asyncio.sleep(0.05)

    await broadcaster.publish_failed(
        repo_id=repo_id,
        task_id=task_id,
        stage="embed",
        error_message="Ollama inference connection timed out",
        diagnostic_log="Traceback (most recent call last): ConnectionRefusedError",
        stage_timings={"clone": 0.1, "parse": 0.2, "extract": 0.3},
    )

    await task
    assert len(received) == 1
    assert received[0]["type"] == "failed"
    assert received[0]["stage"] == "embed"
    assert received[0]["error"] == "Ollama inference connection timed out"
    assert "ConnectionRefusedError" in received[0]["diagnostic_log"]


@pytest.mark.asyncio
async def test_websocket_channel_streaming():
    repo_id = "ws-repo-test-99"

    # Pre-populate state in progress_broadcaster
    await progress_broadcaster.publish_stage_transition(
        repo_id=repo_id,
        task_id="ws-task-1",
        stage="extract",
        progress=65,
        files_total=10,
        files_processed=10,
    )

    client = TestClient(app)
    with client.websocket_connect(f"/api/v1/repos/{repo_id}/ingest/ws") as ws:
        data = ws.receive_json()
        assert data["type"] == "stage_transition"
        assert data["stage"] == "extract"
        assert data["progress"] == 65
        assert data["repo_id"] == repo_id
