"""Tests for high-speed PostgreSQL batch upsert graph persistence layer."""

import time
from unittest.mock import AsyncMock

import pytest

from services.ingestion.persistence import BatchGraphPersistence


@pytest.mark.asyncio
async def test_batch_graph_persistence_chunking_and_upsert():
    mock_db = AsyncMock()

    nodes = [
        {
            "id": f"node-{i}",
            "type": "function",
            "name": f"func_{i}",
            "path": f"src/mod_{i // 500}.py",
            "language": "python",
            "metadata": {"docstring": "Sample func"},
            "summary": f"Summary {i}",
            "content_hash": f"hash_{i}",
            "embedding": [0.01] * 384,
        }
        for i in range(2500)
    ]

    edges = [
        {
            "id": f"edge-{i}",
            "source_key": f"{nodes[i]['path']}::{nodes[i]['name']}::{nodes[i]['type']}",
            "target_key": f"{nodes[i + 1]['path']}::{nodes[i + 1]['name']}::{nodes[i + 1]['type']}",
            "type": "calls",
            "weight": 1.0,
            "metadata": {},
        }
        for i in range(2499)
    ]

    persistence = BatchGraphPersistence(node_batch_size=1000, edge_batch_size=1000)

    t0 = time.time()
    node_count, edge_count = await persistence.persist_graph(
        db=mock_db,
        repo_id="test-repo-persist",
        nodes=nodes,
        edges=edges,
    )
    elapsed = time.time() - t0

    assert node_count == 2500
    assert edge_count == 2499
    assert elapsed < 5.0  # Fast execution

    # 2500 nodes in batches of 1000 => 3 chunks
    # 2499 edges in batches of 1000 => 3 chunks
    # Total db.execute calls = 6
    assert mock_db.execute.await_count == 6


@pytest.mark.asyncio
async def test_batch_graph_persistence_idempotency_empty():
    mock_db = AsyncMock()
    persistence = BatchGraphPersistence()

    node_count, edge_count = await persistence.persist_graph(
        db=mock_db,
        repo_id="repo-empty",
        nodes=[],
        edges=[],
    )

    assert node_count == 0
    assert edge_count == 0
    assert mock_db.execute.await_count == 0


@pytest.mark.asyncio
async def test_batch_graph_persistence_redis_cache():
    mock_db = AsyncMock()
    mock_redis = AsyncMock()

    nodes = [
        {
            "id": "node-1",
            "type": "class",
            "name": "AuthService",
            "path": "src/auth.py",
        }
    ]

    persistence = BatchGraphPersistence(node_batch_size=1000, edge_batch_size=1000)
    node_count, edge_count = await persistence.persist_graph(
        db=mock_db,
        repo_id="repo-redis-test",
        nodes=nodes,
        edges=[],
        redis_client=mock_redis,
    )

    assert node_count == 1
    assert edge_count == 0
    assert mock_redis.hset.await_count == 1
    assert mock_redis.expire.await_count == 1
