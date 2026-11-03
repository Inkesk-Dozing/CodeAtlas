"""Tests for pgvector HNSW index configuration and fast cosine distance queries."""

import importlib
from unittest.mock import AsyncMock, MagicMock

import pytest

from models.entities import CodeNode
from services.mapping.semantic import (
    NearestNeighborResult,
    query_nearest_neighbors,
)


def test_code_node_hnsw_index_configuration():
    hnsw_index = next((idx for idx in CodeNode.__table__.indexes if idx.name == "idx_nodes_embedding"), None)
    assert hnsw_index is not None

    pg_options = hnsw_index.dialect_options.get("postgresql", {})
    assert pg_options.get("using") == "hnsw"
    assert pg_options.get("with") == {"m": 16, "ef_construction": 64}
    assert pg_options.get("ops") == {"embedding": "vector_cosine_ops"}


def test_migration_0004_definition():
    migration_mod = importlib.import_module("migrations.versions.0004_hnsw_cosine_index_tuning")
    assert migration_mod.revision == "0004_hnsw_cosine_index_tuning"
    assert migration_mod.down_revision == "0003_subgraph_traversal_indexes"
    assert callable(migration_mod.upgrade)
    assert callable(migration_mod.downgrade)


@pytest.mark.asyncio
async def test_query_nearest_neighbors_parameterized_and_scoped():
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.mappings.return_value = [
        {
            "id": "node-1",
            "name": "AuthService",
            "path": "src/auth/service.py",
            "type": "class",
            "distance": 0.05,
            "similarity_score": 0.95,
        },
        {
            "id": "node-2",
            "name": "login_handler",
            "path": "src/auth/handler.py",
            "type": "function",
            "distance": 0.12,
            "similarity_score": 0.88,
        },
    ]
    mock_db.execute.return_value = mock_result

    repo_id = "test-repo-99"
    vector = [0.1] * 384

    neighbors = await query_nearest_neighbors(
        db=mock_db,
        repo_id=repo_id,
        vector=vector,
        top_k=5,
        ef_search=40,
    )

    assert len(neighbors) == 2
    assert isinstance(neighbors[0], NearestNeighborResult)
    assert neighbors[0].id == "node-1"
    assert neighbors[0].similarity_score == 0.95
    assert neighbors[0].distance == 0.05
    assert neighbors[1].id == "node-2"

    # Verify query had repo_id and top_k bound
    assert mock_db.execute.await_count == 2  # SET LOCAL + SELECT query
    last_call = mock_db.execute.await_args
    params = last_call.args[1]
    assert params["repo_id"] == repo_id
    assert params["top_k"] == 5


@pytest.mark.asyncio
async def test_query_nearest_neighbors_empty_vector():
    mock_db = AsyncMock()
    res = await query_nearest_neighbors(mock_db, "repo-1", [])
    assert res == []
    assert mock_db.execute.await_count == 0
