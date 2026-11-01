"""Unit and integration tests for Signal 2: Structural Matcher (Issue #54)."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from models import CodeNode
from services.mapping.preprocessor import PreprocessedIssue
from services.mapping.structural import (
    StructuralMatcher,
    compute_trigram_similarity,
    normalize_identifier,
)


def test_normalize_identifier_variants() -> None:
    # camelCase
    assert normalize_identifier("tokenVerifier") == ["token", "verifier"]
    # PascalCase
    assert normalize_identifier("UserSessionManager") == ["user", "session", "manager"]
    # snake_case
    assert normalize_identifier("validate_github_token") == ["validate", "github", "token"]
    # kebab-case
    assert normalize_identifier("graph-canvas-node") == ["graph", "canvas", "node"]
    # mixed path
    assert normalize_identifier("apps/api/routers/auth.py") == ["apps", "api", "routers", "auth", "py"]


def test_compute_trigram_similarity() -> None:
    # Exact match
    assert compute_trigram_similarity("TokenVerifier", "tokenverifier") == 1.0
    # High similarity
    sim_high = compute_trigram_similarity("authenticator", "authentication")
    assert sim_high > 0.40
    # Dissimilar
    sim_low = compute_trigram_similarity("canvas", "database")
    assert sim_low == 0.0 or sim_low < 0.20


@pytest.mark.asyncio
async def test_structural_matcher_exact_filename_match() -> None:
    mock_db = AsyncMock()
    matcher = StructuralMatcher(db=mock_db, repo_id="repo_1")

    node_auth = CodeNode(id="node_auth", repo_id="repo_1", name="auth.py", path="apps/api/routers/auth.py", type="file")
    node_canvas = CodeNode(id="node_canvas", repo_id="repo_1", name="GraphCanvas.tsx", path="apps/web/src/components/canvas/GraphCanvas.tsx", type="file")
    node_db = CodeNode(id="node_db", repo_id="repo_1", name="models.py", path="apps/api/database/models.py", type="file")

    preprocessed = PreprocessedIssue(
        original_title="Fix auth bug in auth.py",
        original_body="Check apps/api/routers/auth.py",
        cleaned_text="Fix auth bug in auth.py Check apps/api/routers/auth.py",
        file_paths=["apps/api/routers/auth.py"],
        code_symbols=["auth.py"],
    )

    scores = await matcher.match_candidates(
        query_tokens=["auth", "routers"],
        query_ident_tokens={"auth", "routers"},
        preprocessed=preprocessed,
        nodes=[node_auth, node_canvas, node_db],
    )

    # Acceptance criteria:
    # 1. Exact filename match receives 1.0 structural score
    assert scores["node_auth"] == 1.0
    # 2. Structural score bounded between [0.0, 1.0]
    for score in scores.values():
        assert 0.0 <= score <= 1.0


@pytest.mark.asyncio
async def test_structural_matcher_partial_path_and_symbol_match() -> None:
    mock_db = AsyncMock()
    matcher = StructuralMatcher(db=mock_db, repo_id="repo_1")

    node_handler = CodeNode(id="node_handler", repo_id="repo_1", name="TokenVerifier", path="apps/api/services/auth/verifier.py", type="class")
    node_service = CodeNode(id="node_service", repo_id="repo_1", name="orchestrator", path="apps/api/services/ingestion/orchestrator.py", type="module")

    # Partial path match: mentioned "services/auth"
    preprocessed_path = PreprocessedIssue(
        original_title="Error in services/auth",
        original_body="",
        cleaned_text="Error in services/auth",
        file_paths=["services/auth"],
    )
    scores_path = await matcher.match_candidates(
        query_tokens=["services", "auth"],
        query_ident_tokens={"services", "auth"},
        preprocessed=preprocessed_path,
        nodes=[node_handler, node_service],
    )
    assert scores_path["node_handler"] >= 0.70

    # Symbol match: mentioned `TokenVerifier`
    preprocessed_sym = PreprocessedIssue(
        original_title="Fix TokenVerifier error",
        original_body="",
        cleaned_text="Fix TokenVerifier error",
        code_symbols=["TokenVerifier"],
    )
    scores_sym = await matcher.match_candidates(
        query_tokens=["tokenverifier"],
        query_ident_tokens={"token", "verifier"},
        preprocessed=preprocessed_sym,
        nodes=[node_handler, node_service],
    )
    assert scores_sym["node_handler"] >= 0.50
