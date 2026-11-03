"""Tests for vector embeddings generation pipeline with local Ollama inference."""

import math

import pytest

from services.ingestion.embeddings import (
    EMBEDDING_DIM,
    VectorEmbeddingPipeline,
    build_node_embedding_context,
    generate_deterministic_embedding,
    normalize_vector,
)


def test_build_node_embedding_context():
    node = {
        "type": "function",
        "name": "authenticate_user",
        "path": "src/services/auth.py",
        "metadata": {
            "signature": "(username: str, password: str) -> User",
            "docstring": "Authenticates user against credential store.",
            "callers": ["login_route", "oauth_callback"],
        },
    }

    ctx = build_node_embedding_context(node)
    assert "type: function" in ctx
    assert "name: authenticate_user" in ctx
    assert "path: src/services/auth.py" in ctx
    assert "signature: (username: str, password: str) -> User" in ctx
    assert "docstring: Authenticates user against credential store." in ctx
    assert "callers: login_route, oauth_callback" in ctx


def test_normalize_vector():
    vec = [3.0, 4.0]
    normed = normalize_vector(vec)
    assert normed == [0.6, 0.8]
    assert math.isclose(math.sqrt(sum(x * x for x in normed)), 1.0, rel_tol=1e-4)


def test_generate_deterministic_embedding():
    text = "type: function | name: get_user | path: src/api.py"
    emb = generate_deterministic_embedding(text, dim=EMBEDDING_DIM)

    assert len(emb) == EMBEDDING_DIM
    # Check normalized
    length = math.sqrt(sum(x * x for x in emb))
    assert math.isclose(length, 1.0, rel_tol=1e-4)

    # Determinism check
    emb2 = generate_deterministic_embedding(text, dim=EMBEDDING_DIM)
    assert emb == emb2


@pytest.mark.asyncio
async def test_vector_embedding_pipeline_batching_and_fallback():
    pipeline = VectorEmbeddingPipeline(batch_size=32)

    nodes = [
        {
            "id": f"node-{i}",
            "type": "function",
            "name": f"func_{i}",
            "path": f"src/mod_{i}.py",
            "metadata": {
                "signature": "() -> None",
                "docstring": f"Function {i}",
            },
        }
        for i in range(65)
    ]

    count = await pipeline.generate_embeddings_for_nodes(nodes)
    assert count == 65

    # Check each node received embedding and hash
    for node in nodes:
        assert "embedding" in node
        assert len(node["embedding"]) == EMBEDDING_DIM
        assert "content_hash" in node
        assert len(node["content_hash"]) == 64


@pytest.mark.asyncio
async def test_vector_embedding_pipeline_cache_skip():
    pipeline = VectorEmbeddingPipeline(batch_size=32)
    node = {
        "id": "node-cached",
        "type": "class",
        "name": "AuthService",
        "path": "src/auth.py",
    }

    # First run populates cache
    await pipeline.generate_embeddings_for_nodes([node])
    first_emb = node["embedding"]

    # Second run with same context should hit cache
    node_copy = dict(node)
    node_copy["embedding"] = None

    await pipeline.generate_embeddings_for_nodes([node_copy])
    assert node_copy["embedding"] == first_emb
