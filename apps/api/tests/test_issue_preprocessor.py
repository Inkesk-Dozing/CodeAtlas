"""Tests for IssueTextPreprocessor (Issue #51)."""
from __future__ import annotations

from services.mapping.preprocessor import IssueTextPreprocessor, StackTraceFrame


def test_extract_file_paths_precision() -> None:
    preprocessor = IssueTextPreprocessor()
    title = "Fix crash in apps/api/routers/auth.py"
    body = """
    We noticed that `apps/api/routers/auth.py` crashes when calling `generate_token()`.
    Also check `apps/web/src/components/canvas/GraphCanvas.tsx` and `packages/shared/src/types/graph.ts`.
    Unrelated mentions: python.org or version 1.2.3 should not be file paths.
    """
    res = preprocessor.preprocess(title, body)

    assert "apps/api/routers/auth.py" in res.file_paths
    assert "apps/web/src/components/canvas/GraphCanvas.tsx" in res.file_paths
    assert "packages/shared/src/types/graph.ts" in res.file_paths


def test_extract_code_symbols() -> None:
    preprocessor = IssueTextPreprocessor()
    title = "Bug in `validate_token` during user login"
    body = "Calling `UserSession.get_active_session()` raises an error in `jwt_handler`."

    res = preprocessor.preprocess(title, body)
    assert "validate_token" in res.code_symbols
    assert "UserSession.get_active_session()" in res.code_symbols
    assert "jwt_handler" in res.code_symbols


def test_extract_python_stack_trace_and_exceptions() -> None:
    preprocessor = IssueTextPreprocessor()
    title = "Unhandled KeyError when parsing repository metadata"
    body = """
    Traceback (most recent call last):
      File "apps/api/services/ingestion/orchestrator.py", line 142, in process_repo
        metadata = repo_data["commit_hash"]
    KeyError: 'commit_hash'
    """
    res = preprocessor.preprocess(title, body)

    assert len(res.stack_trace_frames) == 1
    frame = res.stack_trace_frames[0]
    assert isinstance(frame, StackTraceFrame)
    assert frame.file_path == "apps/api/services/ingestion/orchestrator.py"
    assert frame.line_number == 142
    assert frame.function_name == "process_repo"
    assert any("KeyError: 'commit_hash'" in exc for exc in res.exceptions)
    assert "apps/api/services/ingestion/orchestrator.py" in res.file_paths


def test_extract_node_stack_trace() -> None:
    preprocessor = IssueTextPreprocessor()
    title = "TypeError in GraphCanvas rendering"
    body = """
    TypeError: Cannot read properties of undefined (reading 'nodes')
        at renderCanvas (apps/web/src/components/canvas/GraphCanvas.tsx:88:12)
        at updateGraph (apps/web/src/stores/useGraphStore.ts:45:5)
    """
    res = preprocessor.preprocess(title, body)

    assert len(res.stack_trace_frames) == 2
    paths = [f.file_path for f in res.stack_trace_frames]
    assert "apps/web/src/components/canvas/GraphCanvas.tsx" in paths
    assert "apps/web/src/stores/useGraphStore.ts" in paths


def test_extract_http_routes() -> None:
    preprocessor = IssueTextPreprocessor()
    title = "500 Internal Server Error on /api/v1/auth/callback"
    body = "Requests to `/api/v1/repos/{id}/graph/subgraph` fail intermittently."

    res = preprocessor.preprocess(title, body)
    assert "/api/v1/auth/callback" in res.http_routes
    assert any("/api/v1/repos/{id}/graph/subgraph" in r for r in res.http_routes)


def test_cleaned_text_strips_boilerplate() -> None:
    preprocessor = IssueTextPreprocessor()
    title = "Bug in repository sync"
    body = """
    Hey team!
    ## Steps to reproduce:
    1. Click on sync repository
    2. Wait for completion

    Expected behavior:
    Sync completes cleanly.

    Actual behavior:
    Network timeout in `sync_worker.py`.
    """
    res = preprocessor.preprocess(title, body, labels=["component:sync", "bug"])

    assert "Hey team" not in res.cleaned_text
    assert "Steps to reproduce" not in res.cleaned_text
    assert "Expected behavior" not in res.cleaned_text
    assert "sync_worker.py" in res.cleaned_text
    assert "labels: component:sync, bug" in res.cleaned_text


def test_weighted_tokens_gives_higher_multipliers_to_symbols() -> None:
    preprocessor = IssueTextPreprocessor(high_weight_multiplier=3)
    title = "Fix `AuthService` in `apps/api/routers/auth.py`"
    body = "The service fails unexpectedly."

    res = preprocessor.preprocess(title, body)
    assert res.weighted_tokens.count("authservice") >= 3
    assert res.weighted_tokens.count("auth") >= 3

