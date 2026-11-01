"""Unit and integration tests for Signal 3: Topological Neighbor Propagation (Issue #55)."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from models import CodeEdge
from services.mapping.topological import (
    DEFAULT_ATTENUATION_FACTOR,
    TopologicalPropagator,
)


@pytest.mark.asyncio
async def test_topological_propagation_with_attenuation() -> None:
    mock_db = AsyncMock()
    propagator = TopologicalPropagator(db=mock_db, repo_id="repo_1", attenuation=DEFAULT_ATTENUATION_FACTOR)

    # Seed candidate: auth_router with high confidence 0.80
    seed_scores = {"auth_router": 0.80}

    # Edges: auth_router -> user_service (calls)
    edge1 = CodeEdge(id="e1", repo_id="repo_1", source_id="auth_router", target_id="user_service", type="calls")

    topological_scores = await propagator.propagate_1hop(seed_scores=seed_scores, edges=[edge1])

    # Acceptance criteria:
    # 1. Surfaces dependent service files not explicitly in seed scores
    assert "user_service" in topological_scores
    # 2. Attenuation factor gamma = 0.5 discount applied: 0.80 * 0.5 = 0.40
    assert topological_scores["user_service"] == 0.40
    # 3. Bounded score between [0.0, 1.0]
    assert 0.0 <= topological_scores["user_service"] <= 1.0


@pytest.mark.asyncio
async def test_topological_propagation_multi_edge_reinforcement() -> None:
    mock_db = AsyncMock()
    propagator = TopologicalPropagator(db=mock_db, repo_id="repo_1", attenuation=0.5)

    # Two high-confidence seeds connected to the same model: User
    seed_scores = {
        "auth_router": 0.80,  # 0.80 * 0.5 = 0.40
        "user_service": 0.70,  # 0.70 * 0.5 = 0.35
    }

    edge1 = CodeEdge(id="e1", repo_id="repo_1", source_id="auth_router", target_id="user_model", type="imports")
    edge2 = CodeEdge(id="e2", repo_id="repo_1", source_id="user_service", target_id="user_model", type="uses")

    scores = await propagator.propagate_1hop(seed_scores=seed_scores, edges=[edge1, edge2])

    # Acceptance criteria:
    # Boost nodes that have multiple incoming edges from high-confidence candidates
    # Union formula: 1 - (1 - 0.40) * (1 - 0.35) = 1 - 0.60 * 0.65 = 1 - 0.39 = 0.61
    assert "user_model" in scores
    assert scores["user_model"] > 0.40
    assert scores["user_model"] == 0.61
    assert scores["user_model"] <= 1.0


@pytest.mark.asyncio
async def test_bounded_graph_traversal_prevents_runaway_scores() -> None:
    mock_db = AsyncMock()
    propagator = TopologicalPropagator(db=mock_db, repo_id="repo_1", attenuation=0.5)

    # Dense seed connections into a single central node
    seed_scores = {f"seed_{i}": 1.0 for i in range(15)}
    edges = [
        CodeEdge(id=f"e_{i}", repo_id="repo_1", source_id=f"seed_{i}", target_id="central_hub", type="calls")
        for i in range(15)
    ]

    scores = await propagator.propagate_1hop(seed_scores=seed_scores, edges=edges)

    # Acceptance criteria: Bounded graph traversal prevents runaway score inflation
    assert "central_hub" in scores
    assert scores["central_hub"] <= 1.0
    assert 0.0 <= scores["central_hub"] <= 1.0


@pytest.mark.asyncio
async def test_bidirectional_neighbor_propagation() -> None:
    mock_db = AsyncMock()
    propagator = TopologicalPropagator(db=mock_db, repo_id="repo_1", attenuation=0.5)

    seed_scores = {"core_engine": 0.60}

    # caller -> core_engine (incoming)
    edge_in = CodeEdge(id="e_in", repo_id="repo_1", source_id="api_gateway", target_id="core_engine", type="calls")
    # core_engine -> db_pool (outgoing)
    edge_out = CodeEdge(id="e_out", repo_id="repo_1", source_id="core_engine", target_id="db_pool", type="uses")

    scores = await propagator.propagate_1hop(seed_scores=seed_scores, edges=[edge_in, edge_out])

    # Both caller and callee should receive propagated confidence
    assert "api_gateway" in scores
    assert "db_pool" in scores
    assert scores["api_gateway"] == 0.30
    assert scores["db_pool"] == 0.30
