"""Reciprocal Rank Fusion (RRF) for Hybrid Semantic-Structural Search (Issue #61).

Combines rankings from multiple heterogeneous search retrievers (e.g. pgvector semantic
cosine similarity and lexical/structural trigram matching) without requiring manual score normalization:
- Formula:
    RRF_score(d) = sum_{m in models} (1 / (k + rank_m(d)))
  where k is the smoothing constant (default: 60).
- Highly resilient to outlier confidence distributions between vector cosine distance and text matching.
- Merges matches, eliminates duplicate candidates, and yields calibrated relative ranks.
"""
from __future__ import annotations

from typing import Any, TypeVar

T = TypeVar("T")

DEFAULT_RRF_K = 60


def reciprocal_rank_fusion(
    ranked_lists: list[list[dict[str, Any]]],
    id_key: str = "id",
    k: int = DEFAULT_RRF_K,
) -> list[tuple[dict[str, Any], float]]:
    """Merges multiple ranked candidate lists using Reciprocal Rank Fusion (RRF).

    Args:
        ranked_lists: List of ranked lists of items (each item is a dict with `id_key`).
        id_key: Key uniquely identifying each item across lists.
        k: Smoothing parameter (standard default is 60).

    Returns:
        Sorted list of tuples (item_dict, rrf_score) descending by rrf_score.
    """
    scores: dict[str, float] = {}
    items: dict[str, dict[str, Any]] = {}

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, start=1):
            item_id = str(item[id_key])
            if item_id not in items:
                items[item_id] = item
            # RRF formula: 1.0 / (k + rank)
            contribution = 1.0 / float(k + rank)
            scores[item_id] = scores.get(item_id, 0.0) + contribution

    sorted_ids = sorted(scores.keys(), key=lambda i: scores[i], reverse=True)
    return [(items[item_id], round(scores[item_id], 6)) for item_id in sorted_ids]
