"""High-speed Subgraph & Neighborhood Extraction Service (Issue #48).

Executes recursive neighborhood traversal over `code_nodes` and `code_edges`:
- Directional traversal:
  - 'upstream': Callers, consumers, incoming dependencies (target -> source)
  - 'downstream': Callees, dependencies, outgoing references (source -> target)
  - 'both': Undirected expansion across both incoming and outgoing edges
- Recursive depth expansion (1 to 5 hops).
- Response conforms to the shared `GraphData` / `GraphResponse` contract.
- Traversal optimization bounded by `max_nodes` to prevent memory blowup on large repositories.
"""
from __future__ import annotations

import logging
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import CodeEdge, CodeNode

logger = logging.getLogger(__name__)

TraversalDirection = Literal["upstream", "downstream", "both"]


class SubgraphExtractor:
    """Traverses neighborhood subgraphs in PostgreSQL with directional filtering and hop limits."""

    def __init__(self, db: AsyncSession, repo_id: str) -> None:
        self.db = db
        self.repo_id = repo_id

    async def extract_subgraph(
        self,
        node_ids: list[str],
        depth: int = 1,
        direction: TraversalDirection = "both",
        edge_types: list[str] | None = None,
        max_nodes: int = 200,
    ) -> tuple[list[CodeNode], list[CodeEdge]]:
        """Extracts the $N$-hop neighborhood of `node_ids` respecting direction and type filters.

        Returns:
            Tuple of (nodes, unique_edges).
        """
        if not node_ids:
            return [], []

        # Validate seed nodes exist
        seed_result = await self.db.execute(
            select(CodeNode).where(
                CodeNode.repo_id == self.repo_id,
                CodeNode.id.in_(node_ids),
            )
        )
        seed_nodes = seed_result.scalars().all()
        if not seed_nodes:
            return [], []

        visited: set[str] = {n.id for n in seed_nodes}
        frontier: set[str] = set(visited)
        collected_edges: list[CodeEdge] = []
        collected_edge_ids: set[str] = set()

        for _ in range(depth):
            if not frontier or len(visited) >= max_nodes:
                break

            # Build query based on traversal direction
            stmt = select(CodeEdge).where(CodeEdge.repo_id == self.repo_id)

            if edge_types:
                stmt = stmt.where(CodeEdge.type.in_(edge_types))

            if direction == "downstream":
                # Outgoing: source in frontier -> explore target
                stmt = stmt.where(CodeEdge.source_id.in_(frontier))
            elif direction == "upstream":
                # Incoming: target in frontier -> explore source
                stmt = stmt.where(CodeEdge.target_id.in_(frontier))
            else:
                # Both directions
                stmt = stmt.where(
                    (CodeEdge.source_id.in_(frontier)) | (CodeEdge.target_id.in_(frontier))
                )

            edge_result = await self.db.execute(stmt)
            round_edges = edge_result.scalars().all()

            next_frontier: set[str] = set()

            for edge in round_edges:
                if edge.id not in collected_edge_ids:
                    collected_edge_ids.add(edge.id)
                    collected_edges.append(edge)

                # Determine candidates to expand
                candidate_ids: list[str] = []
                if direction == "downstream":
                    candidate_ids.append(edge.target_id)
                elif direction == "upstream":
                    candidate_ids.append(edge.source_id)
                else:
                    candidate_ids.extend([edge.source_id, edge.target_id])

                for nid in candidate_ids:
                    if nid not in visited and len(visited) < max_nodes:
                        visited.add(nid)
                        next_frontier.add(nid)

            frontier = next_frontier

        # Fetch full node entities for visited nodes
        nodes_result = await self.db.execute(
            select(CodeNode).where(CodeNode.id.in_(visited))
        )
        nodes = nodes_result.scalars().all()

        return nodes, collected_edges
