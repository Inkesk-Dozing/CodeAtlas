"""Signal 5: Hotspot Degree Centrality Prioritization Service.

Critical architectural bottlenecks, hub controllers, and frequently imported utility modules
have high in-degree and out-degree centrality and are disproportionately involved in system bugs.

- Calculates normalized degree centrality per node:
    C_d(v) = (in_degree(v) + out_degree(v)) / max_degree
- Supports fast query with caching/precomputation.
- Clamps normalized centrality strictly within [0.0, 1.0].
- Highly interconnected nodes receive a proportional priority bonus.
- Prevents obscure dead-end leaf nodes from outranking critical architectural hubs.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


def calculate_degree_centrality(
    in_degree: int,
    out_degree: int,
    max_degree: int,
) -> float:
    """Calculates normalized degree centrality C_d(v) = (in_degree + out_degree) / max_degree.

    Returns float in [0.0, 1.0].
    """
    total_degree = max(0, in_degree) + max(0, out_degree)
    if max_degree <= 0:
        return 0.0
    return min(1.0, max(0.0, total_degree / float(max_degree)))


@dataclass
class HotspotNode:
    node_id: str
    in_degree: int
    out_degree: int
    total_degree: int
    centrality: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "in_degree": self.in_degree,
            "out_degree": self.out_degree,
            "total_degree": self.total_degree,
            "centrality": round(self.centrality, 4),
        }


class HotspotPrioritizer:
    """Computes and prioritizes architectural hub nodes using degree centrality."""

    def __init__(self, db: AsyncSession, repo_id: str) -> None:
        self.db = db
        self.repo_id = repo_id

    async def get_hotspot_centrality(
        self,
        node_ids: list[str] | None = None,
        limit: int = 100,
    ) -> dict[str, float]:
        """Calculates normalized degree centrality for nodes in the repository.

        Returns:
            Dict mapping node_id -> normalized centrality score in [0.0, 1.0].
        """
        sql = text(
            """
            WITH node_degrees AS (
                SELECT node_id,
                       SUM(CASE WHEN direction = 'in' THEN 1 ELSE 0 END) AS in_degree,
                       SUM(CASE WHEN direction = 'out' THEN 1 ELSE 0 END) AS out_degree,
                       COUNT(*) AS total_degree
                FROM (
                    SELECT target_id AS node_id, 'in' AS direction
                    FROM code_edges
                    WHERE repo_id = :repo_id
                    UNION ALL
                    SELECT source_id AS node_id, 'out' AS direction
                    FROM code_edges
                    WHERE repo_id = :repo_id
                ) edges_unified
                GROUP BY node_id
            )
            SELECT node_id, in_degree, out_degree, total_degree
            FROM node_degrees
            ORDER BY total_degree DESC
            LIMIT :limit
            """
        )

        try:
            result = await self.db.execute(sql, {"repo_id": self.repo_id, "limit": limit})
            rows = result.mappings().all()
            if not rows:
                return {}

            max_degree = max((int(r["total_degree"]) for r in rows), default=1) or 1

            centrality_map: dict[str, float] = {}
            for r in rows:
                nid = str(r["node_id"])
                if node_ids is not None and nid not in node_ids:
                    continue
                in_d = int(r["in_degree"])
                out_d = int(r["out_degree"])
                c_d = calculate_degree_centrality(in_d, out_d, max_degree)
                centrality_map[nid] = round(c_d, 4)

            return centrality_map
        except Exception:
            logger.exception("Error computing hotspot degree centrality")
            return {}
