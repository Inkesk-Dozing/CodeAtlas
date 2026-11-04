"""Unit tests for Reciprocal Rank Fusion & Hybrid Search Engine (Issue #61)."""
from __future__ import annotations

from services.mapping.rrf import reciprocal_rank_fusion


def test_reciprocal_rank_fusion_single_list() -> None:
    ranked = [{"id": "doc1", "title": "Doc 1"}, {"id": "doc2", "title": "Doc 2"}]
    fused = reciprocal_rank_fusion([ranked], k=60)
    assert len(fused) == 2
    assert fused[0][0]["id"] == "doc1"
    assert fused[1][0]["id"] == "doc2"
    # Score 1: 1 / (60 + 1) = 1 / 61
    # Score 2: 1 / (60 + 2) = 1 / 62
    assert fused[0][1] > fused[1][1]


def test_reciprocal_rank_fusion_combines_and_boosts_intersecting_items() -> None:
    # Model 1 (Semantic): A is #1, B is #2
    list_sem = [{"id": "node_A", "name": "AuthRouter"}, {"id": "node_B", "name": "UserService"}]
    # Model 2 (Structural): C is #1, A is #2
    list_struct = [{"id": "node_C", "name": "AuthController"}, {"id": "node_A", "name": "AuthRouter"}]

    fused = reciprocal_rank_fusion([list_sem, list_struct], k=60)

    # Acceptance criteria:
    # Item A is ranked top-2 in both lists -> receives sum of both RRF contributions:
    # A = 1/61 + 1/62 = 0.016393 + 0.016129 = 0.032522
    # B = 1/62 = 0.016129
    # C = 1/61 = 0.016393
    # Therefore, A clearly outranks both B and C
    assert fused[0][0]["id"] == "node_A"
    assert fused[0][1] > fused[1][1]
    assert fused[0][1] > fused[2][1]
    # Correct deduplication
    assert len(fused) == 3


def test_reciprocal_rank_fusion_empty_lists() -> None:
    assert reciprocal_rank_fusion([]) == []
    assert reciprocal_rank_fusion([[]]) == []
