"""Unit and integration tests for Signal 5: Hotspot Degree Centrality Prioritization (Issue #57)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from services.mapping.hotspot import (
    HotspotPrioritizer,
    calculate_degree_centrality,
)


def test_calculate_degree_centrality_formula() -> None:
    # Acceptance criterion:
    # C_d(v) = (in_degree + out_degree) / max_degree
    # 1. Obscure dead-end leaf node: in_degree=1, out_degree=0, max_degree=20 -> 1/20 = 0.05
    leaf_score = calculate_degree_centrality(in_degree=1, out_degree=0, max_degree=20)
    assert leaf_score == 0.05

    # 2. Critical central hub: in_degree=12, out_degree=8, max_degree=20 -> 20/20 = 1.00
    hub_score = calculate_degree_centrality(in_degree=12, out_degree=8, max_degree=20)
    assert hub_score == 1.00

    # 3. Intermediate node: in_degree=4, out_degree=2, max_degree=20 -> 6/20 = 0.30
    mid_score = calculate_degree_centrality(in_degree=4, out_degree=2, max_degree=20)
    assert mid_score == 0.30

    # 4. Zero max_degree edge case
    assert calculate_degree_centrality(in_degree=0, out_degree=0, max_degree=0) == 0.0

    # 5. Clamped to [0.0, 1.0]
    assert 0.0 <= leaf_score <= 1.0
    assert 0.0 <= hub_score <= 1.0


@pytest.mark.asyncio
async def test_hotspot_prioritizer_centrality_query() -> None:
    mock_db = AsyncMock()

    # Mock database result rows for degrees
    # max_degree is 25 (central_controller)
    # central_controller: in=15, out=10, total=25 -> centrality = 1.0
    # auth_service: in=8, out=4, total=12 -> centrality = 12/25 = 0.48
    # leaf_helper: in=1, out=0, total=1 -> centrality = 1/25 = 0.04
    mock_rows = [
        {"node_id": "central_controller", "in_degree": 15, "out_degree": 10, "total_degree": 25},
        {"node_id": "auth_service", "in_degree": 8, "out_degree": 4, "total_degree": 12},
        {"node_id": "leaf_helper", "in_degree": 1, "out_degree": 0, "total_degree": 1},
    ]

    mock_result = MagicMock()
    mock_result.mappings.return_value.all.return_value = mock_rows
    mock_db.execute.return_value = mock_result

    prioritizer = HotspotPrioritizer(db=mock_db, repo_id="repo_1")
    centrality_map = await prioritizer.get_hotspot_centrality()

    # Acceptance criteria:
    # 1. Highly interconnected architectural hubs receive proportional priority bonus
    assert centrality_map["central_controller"] == 1.0
    assert centrality_map["auth_service"] == 0.48

    # 2. Prevents obscure dead-end leaf nodes from outranking critical controllers
    assert centrality_map["central_controller"] > centrality_map["leaf_helper"]
    assert centrality_map["leaf_helper"] == 0.04

    # 3. Bounded strictly in [0.0, 1.0]
    for score in centrality_map.values():
        assert 0.0 <= score <= 1.0
