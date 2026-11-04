"""Signal 1: Semantic Issue Candidate Retrieval Service using pgvector cosine distance.

Retrieves candidate code nodes conceptually relevant to issue text via dense vector embeddings:
- Embedding generation using configured embedding models (Ollama / local fallback / Sentence-Transformers).
- High-speed cosine distance nearest-neighbor queries against `code_nodes` with pgvector HNSW indexing:
  `1 - (embedding <=> CAST(:qv AS vector)) AS semantic_score`
- Normalization ensuring output scores are strictly bounded in `[0.0, 1.0]`.
- Configurable top-k limit (default top-50) and similarity threshold filtering.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings

logger = logging.getLogger(__name__)

DEFAULT_SEMANTIC_LIMIT = 50
DEFAULT_MIN_SIMILARITY_THRESHOLD = 0.20


@dataclass
class SemanticCandidate:
    node_id: str
    semantic_score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "semantic_score": round(self.semantic_score, 4),
        }


async def generate_issue_embedding(
    text_content: str,
    embed_url: str | None = None,
    model_name: str | None = None,
) -> list[float] | None:
    """Generates dense vector embedding for issue text using embedding endpoint."""
    if not text_content or not text_content.strip():
        return None

    target_url = embed_url or settings.ollama_url
    target_model = model_name or settings.ollama_embed_model

    try:
        import httpx

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{target_url}/api/embeddings",
                json={"model": target_model, "prompt": text_content[:4000]},
                timeout=15.0,
            )
            if resp.status_code == 200:
                embedding = resp.json().get("embedding")
                if isinstance(embedding, list) and len(embedding) > 0:
                    return [float(x) for x in embedding]
    except Exception:
        logger.debug("Ollama embedding endpoint unavailable at %s", target_url, exc_info=True)

    return None


class SemanticRetriever:
    """Retrieves top-N semantic candidates using pgvector cosine similarity."""

    def __init__(
        self,
        db: AsyncSession,
        repo_id: str,
        limit: int = DEFAULT_SEMANTIC_LIMIT,
        min_threshold: float = DEFAULT_MIN_SIMILARITY_THRESHOLD,
    ) -> None:
        self.db = db
        self.repo_id = repo_id
        self.limit = limit
        self.min_threshold = min_threshold

    async def retrieve_candidates(
        self,
        issue_text: str,
        embedding: list[float] | None = None,
    ) -> dict[str, float]:
        """Returns mapping of node_id -> normalized semantic_score bounded in [0.0, 1.0]."""
        vector = embedding or await generate_issue_embedding(issue_text)
        if not vector:
            return {}

        return await self.retrieve_by_vector(vector)

    async def retrieve_by_vector(self, vector: list[float]) -> dict[str, float]:
        """Executes pgvector cosine similarity nearest-neighbor search."""
        if not vector:
            return {}

        vector_str = f"[{','.join(str(x) for x in vector)}]"

        sql = text(
            f"""
            SELECT id,
                   1 - (embedding <=> CAST(:qv AS vector)) AS semantic_score
            FROM code_nodes
            WHERE repo_id = :repo_id AND embedding IS NOT NULL
            ORDER BY embedding <=> CAST(:qv AS vector) ASC
            LIMIT {self.limit}
            """
        )

        try:
            result = await self.db.execute(sql, {"qv": vector_str, "repo_id": self.repo_id})
            candidates: dict[str, float] = {}

            for row in result.mappings():
                raw_score = float(row["semantic_score"] or 0.0)
                # Bounded normalization between [0.0, 1.0]
                normalized_score = max(0.0, min(1.0, raw_score))
                if normalized_score >= self.min_threshold:
                    candidates[str(row["id"])] = normalized_score

            return candidates
        except Exception:
            logger.exception("Error executing pgvector semantic candidate retrieval")
            return {}


@dataclass
class NearestNeighborResult:
    id: str
    name: str
    path: str
    type: str
    similarity_score: float
    distance: float


async def query_nearest_neighbors(
    db: AsyncSession,
    repo_id: str,
    vector: list[float],
    top_k: int = 10,
    ef_search: int = 40,
) -> list[NearestNeighborResult]:
    """Execute parameterized nearest-neighbor query with strict repository_id scoping.

    Utilizes the tuned HNSW index on code_nodes(embedding vector_cosine_ops)
    with configured m=16, ef_construction=64 and runtime ef_search tuning.
    """
    if not vector:
        return []

    vector_str = f"[{','.join(str(x) for x in vector)}]"

    try:
        await db.execute(text(f"SET LOCAL hnsw.ef_search = {int(ef_search)}"))
    except Exception:
        pass

    sql = text(
        """
        SELECT id, name, path, type,
               embedding <=> CAST(:qv AS vector) AS distance,
               1 - (embedding <=> CAST(:qv AS vector)) AS similarity_score
        FROM code_nodes
        WHERE repo_id = :repo_id AND embedding IS NOT NULL
        ORDER BY distance ASC
        LIMIT :top_k
        """
    )

    try:
        result = await db.execute(sql, {"qv": vector_str, "repo_id": repo_id, "top_k": top_k})
        neighbors: list[NearestNeighborResult] = []

        for row in result.mappings():
            raw_sim = float(row["similarity_score"] or 0.0)
            dist = float(row["distance"] or 0.0)
            neighbors.append(
                NearestNeighborResult(
                    id=str(row["id"]),
                    name=str(row["name"]),
                    path=str(row["path"]),
                    type=str(row["type"]),
                    similarity_score=max(0.0, min(1.0, raw_sim)),
                    distance=max(0.0, dist),
                )
            )

        return neighbors
    except Exception:
        logger.exception("Error executing nearest neighbor query")
        return []


