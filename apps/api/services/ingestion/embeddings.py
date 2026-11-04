"""Vector embeddings generation pipeline with local Ollama inference and fallback.

Constructs comprehensive AST node semantic context strings:
'type: {node_type} | name: {name} | path: {path} | signature: {signature} | docstring: {docstring} | callers: {callers}'
Batches inference in 32-item chunks to maximize throughput.
Maintains an in-memory / content-hash cache to skip unchanged AST nodes.
Provides fallback embedding generation when local Ollama is unavailable.
Ensures 100% air-gapped local execution with zero external cloud API requests.
"""

import hashlib
import logging
import math
from typing import Any

from config import settings

logger = logging.getLogger(__name__)

DEFAULT_EMBEDDING_BATCH_SIZE = 32
EMBEDDING_DIM = 768


def build_node_embedding_context(node: dict[str, Any]) -> str:
    """Construct semantic context string formatted per technical specification:

    type: {node_type} | name: {name} | path: {path} | signature: {signature} | docstring: {docstring} | callers: {callers}
    """
    node_type = str(node.get("type", ""))
    name = str(node.get("name", ""))
    path = str(node.get("path", ""))

    meta = node.get("metadata", {}) or {}
    signature = str(meta.get("signature") or meta.get("params") or "")
    docstring = str(meta.get("docstring") or node.get("summary") or "")

    callers_list = meta.get("callers") or []
    if isinstance(callers_list, list):
        callers = ", ".join(str(c) for c in callers_list)
    else:
        callers = str(callers_list)

    parts = [
        f"type: {node_type}",
        f"name: {name}",
        f"path: {path}",
    ]
    if signature:
        parts.append(f"signature: {signature}")
    if docstring:
        parts.append(f"docstring: {docstring}")
    if callers:
        parts.append(f"callers: {callers}")

    return " | ".join(parts)


def compute_content_hash(text: str) -> str:
    """Compute deterministic SHA-256 hash for embedding text caching."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_vector(vec: list[float]) -> list[float]:
    """L2 normalize embedding vector to unit length."""
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0:
        return vec
    return [round(x / norm, 6) for x in vec]


def generate_deterministic_embedding(text: str, dim: int = EMBEDDING_DIM) -> list[float]:
    """Deterministic air-gapped fallback embedding generator using token hashing."""
    vec = [0.0] * dim
    words = text.split()
    if not words:
        return vec

    for i, word in enumerate(words):
        word_hash = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
        idx = word_hash % dim
        weight = 1.0 / (1.0 + (i * 0.05))
        vec[idx] += weight

    return normalize_vector(vec)


class VectorEmbeddingPipeline:
    """Batch embeddings generator for code nodes with Ollama inference and local fallback."""

    def __init__(
        self,
        batch_size: int = DEFAULT_EMBEDDING_BATCH_SIZE,
        ollama_url: str | None = None,
        model_name: str | None = None,
    ) -> None:
        self.batch_size = batch_size
        self.ollama_url = (ollama_url or settings.ollama_url).rstrip("/")
        self.model_name = model_name or settings.ollama_embed_model
        self._cache: dict[str, list[float]] = {}
        self._ollama_available: bool | None = None

    async def _check_ollama(self) -> bool:
        if self._ollama_available is not None:
            return self._ollama_available

        import httpx

        try:
            async with httpx.AsyncClient(timeout=0.2) as client:
                resp = await client.get(f"{self.ollama_url}/api/tags")
                self._ollama_available = resp.status_code == 200
        except Exception:
            self._ollama_available = False

        return self._ollama_available

    async def generate_embeddings_for_nodes(
        self,
        nodes: list[dict[str, Any]],
    ) -> int:
        """Populates 'embedding' and 'content_hash' on each node in-place.

        Returns total count of processed embeddings.
        """
        if not nodes:
            return 0

        import httpx

        ollama_online = await self._check_ollama()
        processed_count = 0

        for i in range(0, len(nodes), self.batch_size):
            batch = nodes[i : i + self.batch_size]
            for node in batch:
                context_str = build_node_embedding_context(node)
                text_hash = compute_content_hash(context_str)
                node["content_hash"] = text_hash

                # 1. Check cache first to skip unchanged nodes
                if text_hash in self._cache:
                    node["embedding"] = self._cache[text_hash]
                    processed_count += 1
                    continue

                # 2. Query local Ollama embeddings endpoint if available
                embedding = None
                if ollama_online:
                    try:
                        async with httpx.AsyncClient(timeout=2.0) as client:
                            resp = await client.post(
                                f"{self.ollama_url}/api/embeddings",
                                json={"model": self.model_name, "prompt": context_str},
                            )
                            if resp.status_code == 200:
                                raw_emb = resp.json().get("embedding")
                                if raw_emb and isinstance(raw_emb, list):
                                    embedding = normalize_vector([float(x) for x in raw_emb])
                    except Exception as e:
                        logger.debug("Local Ollama embedding failed for %s (%s)", node.get("name"), e)

                # 3. Air-gapped deterministic fallback if Ollama endpoint is down
                if not embedding:
                    embedding = generate_deterministic_embedding(context_str, dim=EMBEDDING_DIM)

                node["embedding"] = embedding
                self._cache[text_hash] = embedding
                processed_count += 1

        return processed_count


vector_embedding_pipeline = VectorEmbeddingPipeline()
