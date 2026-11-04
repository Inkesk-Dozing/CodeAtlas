"""Tests for incremental git diff parser and push webhook re-indexing engine."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models import Repository
from services.ingestion.broadcaster import progress_broadcaster
from services.ingestion.diff_parser import (
    ChangedFile,
    IncrementalDiffEngine,
    parse_git_diff_name_status,
)


def test_parse_git_diff_name_status():
    diff_payload = (
        "A\tsrc/utils/math.py\n"
        "M\tsrc/api/server.py\n"
        "D\tsrc/legacy/old_helper.py\n"
        "R100\tsrc/old_name.ts\tsrc/new_name.ts\n"
        "\n"
    )

    changes = parse_git_diff_name_status(diff_payload)
    assert len(changes) == 4

    assert changes[0] == ChangedFile(path="src/utils/math.py", status="added")
    assert changes[1] == ChangedFile(path="src/api/server.py", status="modified")
    assert changes[2] == ChangedFile(path="src/legacy/old_helper.py", status="deleted")
    assert changes[3] == ChangedFile(
        path="src/new_name.ts", status="renamed", old_path="src/old_name.ts"
    )


@pytest.mark.asyncio
async def test_incremental_diff_applies_and_purges_orphans():
    repo_id = "test-incremental-repo"
    mock_repo = Repository(
        id=repo_id,
        github_id=98765,
        installation_id=54321,
        name="test-repo",
        full_name="org/test-repo",
        owner="org",
        clone_url="https://github.com/org/test-repo.git",
        settings={"graph_version": 2},
        node_count=10,
        edge_count=15,
    )

    mock_db = AsyncMock()
    mock_db.get.return_value = mock_repo

    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 8

    mock_nodes_result = MagicMock()
    mock_nodes_result.scalars.return_value.all.return_value = ["node-deleted-1", "node-deleted-2"]

    mock_db.execute.side_effect = [
        mock_nodes_result,  # existing nodes for deleted paths
        MagicMock(),        # delete edges
        MagicMock(),        # delete nodes
        MagicMock(),        # purge orphaned edges
        mock_count_result,  # count nodes
        mock_count_result,  # count edges
    ]

    engine = IncrementalDiffEngine(repo_id)

    changes = [
        ChangedFile(path="src/deleted_file.py", status="deleted"),
        ChangedFile(path="src/new_file.py", status="added"),
    ]

    file_contents = {
        "src/new_file.py": "def new_function():\n    return 42\n",
    }

    t0 = time.time()
    result = await engine.apply_incremental_diff(
        db=mock_db,
        changes=changes,
        file_contents=file_contents,
        commit_sha="c0ffee1234567890",
    )
    duration = time.time() - t0

    # Acceptance criteria: incremental update for files completes in < 5 seconds
    assert duration < 5.0

    # Verified graph version bumped
    assert result["type"] == "graph_updated"
    assert result["graph_version"] == 3
    assert result["commit_sha"] == "c0ffee1234567890"
    assert result["files_changed"] == 2
    assert result["files_deleted"] == 1
    assert result["files_added"] == 1


@pytest.mark.asyncio
async def test_incremental_diff_broadcasts_websocket_notification():
    repo_id = "ws-notify-repo"
    mock_repo = Repository(
        id=repo_id,
        github_id=11223,
        installation_id=33445,
        name="notify-repo",
        full_name="org/notify-repo",
        owner="org",
        clone_url="https://github.com/org/notify-repo.git",
        settings={"graph_version": 5},
    )

    mock_db = AsyncMock()
    mock_db.get.return_value = mock_repo

    mock_empty_nodes = MagicMock()
    mock_empty_nodes.scalars.return_value.all.return_value = []

    mock_count = MagicMock()
    mock_count.scalar.return_value = 12

    mock_db.execute.side_effect = [
        mock_empty_nodes,   # existing nodes for modified path
        MagicMock(),        # purge orphaned edges
        mock_count,         # count nodes
        mock_count,         # count edges
    ]

    published_events = []
    with patch.object(progress_broadcaster, "publish", side_effect=lambda r, evt: published_events.append((r, evt))):
        engine = IncrementalDiffEngine(repo_id)
        await engine.apply_incremental_diff(
            db=mock_db,
            changes=[ChangedFile(path="src/mod.py", status="modified")],
            file_contents={},
            commit_sha="abc12345",
        )

    assert len(published_events) == 1
    target_repo, event = published_events[0]
    assert target_repo == repo_id
    assert event["type"] == "graph_updated"
    assert event["graph_version"] == 6
    assert event["commit_sha"] == "abc12345"
