"""Unit and integration tests for Signal 1: Semantic Candidate Retrieval (Issue #53)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.mapping.semantic import (
    DEFAULT_SEMANTIC_LIMIT,
    SemanticRetriever,
    generate_issue_embedding,
)


@pytest.mark.asyncio
async def test_generate_issue_embedding_empty_input() -> None:
    assert await generate_issue_embedding("") is None
    assert await generate_issue_embedding("   ") is None


@pytest.mark.asyncio
async def test_generate_issue_embedding_mock_success() -> None:
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"embedding": [0.1, 0.2, 0.3, 0.4]}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
        vec = await generate_issue_embedding("user session expires immediately")
        assert vec == [0.1, 0.2, 0.3, 0.4]


@pytest.mark.asyncio
async def test_semantic_retriever_query_bounded_scores() -> None:
    # Mock database session
    mock_db = AsyncMock()

    # Simulate raw db results with various positive, negative, and extreme scores
    mock_mappings = [
        {"id": "node_1", "semantic_score": 0.8854},
        {"id": "node_2", "semantic_score": 0.4521},
        {"id": "node_3", "semantic_score": 1.05},  # Upper bound test
        {"id": "node_4", "semantic_score": -0.15},  # Lower bound / below threshold test
        {"id": "node_5", "semantic_score": 0.12},  # Below min threshold (0.20)
    ]
    mock_result = MagicMock()
    mock_result.mappings.return_value = mock_mappings
    mock_db.execute.return_value = mock_result

    retriever = SemanticRetriever(db=mock_db, repo_id="repo_123", limit=DEFAULT_SEMANTIC_LIMIT)
    results = await retriever.retrieve_by_vector([0.1] * 768)

    # Acceptance criteria:
    # 1. Normalized semantic similarity score bounded between [0.0, 1.0]
    for node_id, score in results.items():
        assert 0.0 <= score <= 1.0, f"Score for {node_id} out of bounds: {score}"

    assert "node_1" in results
    assert results["node_1"] == 0.8854

    # Bounded to 1.0 max
    assert "node_3" in results
    assert results["node_3"] == 1.0

    # Below threshold (< 0.20) must be filtered out
    assert "node_4" not in results
    assert "node_5" not in results


@pytest.mark.asyncio
async def test_semantic_retriever_empty_vector_returns_empty() -> None:
    mock_db = AsyncMock()
    retriever = SemanticRetriever(db=mock_db, repo_id="repo_123")
    res = await retriever.retrieve_by_vector([])
    assert res == {}
