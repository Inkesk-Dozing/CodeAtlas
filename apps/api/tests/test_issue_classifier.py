"""Tests for IssueIntentClassifier (Issue #52)."""
from __future__ import annotations

import pytest

from services.mapping.classifier import (
    IssueIntent,
    IssueIntentClassifier,
)
from services.mapping.preprocessor import IssueTextPreprocessor


@pytest.fixture
def classifier() -> IssueIntentClassifier:
    return IssueIntentClassifier()


def test_classify_bug_intent_with_stack_trace(classifier: IssueIntentClassifier) -> None:
    title = "Unhandled KeyError in repository ingestion orchestrator"
    body = """
    Traceback (most recent call last):
      File "apps/api/services/ingestion/orchestrator.py", line 142, in process_repo
        metadata = repo_data["commit_hash"]
    KeyError: 'commit_hash'
    """
    preprocessor = IssueTextPreprocessor()
    preprocessed = preprocessor.preprocess(title, body)

    result = classifier.classify(title, body, preprocessed=preprocessed)
    assert result.primary_intent == IssueIntent.BUG
    assert result.confidence > 0.70
    assert "structural:stack_trace" in result.detected_signals
    assert "function" in result.search_strategy["preferred_node_types"]


def test_classify_feature_intent_from_label_and_title(classifier: IssueIntentClassifier) -> None:
    title = "Add support for Python 3.13 tree-sitter AST parser"
    body = "Please implement new parsing capabilities for async comprehension syntax."
    labels = ["enhancement", "type:feature"]

    result = classifier.classify(title, body, labels=labels)
    assert result.primary_intent == IssueIntent.FEATURE
    assert result.confidence > 0.75
    assert result.search_strategy["weight_adjustments"]["semantic"] == 0.50
    assert "route" in result.search_strategy["preferred_node_types"] or "interface" in result.search_strategy["preferred_node_types"]


def test_classify_refactor_intent(classifier: IssueIntentClassifier) -> None:
    title = "Refactor Celery ingestion worker and optimize memory leak recycling"
    body = "Clean up redundant task states and simplify worker lifecycle hooks to reduce latency."
    labels = ["type:refactor", "priority:P1-high"]

    result = classifier.classify(title, body, labels=labels)
    assert result.primary_intent == IssueIntent.REFACTOR
    assert result.confidence > 0.70
    assert result.search_strategy["weight_adjustments"]["hotspot"] == 0.15


def test_classify_security_intent_with_cve(classifier: IssueIntentClassifier) -> None:
    title = "Remediate CVE-2026-3829 vulnerability in JWT session parser"
    body = "Discovered potential auth bypass and secret token leak in webhook signature verification."
    labels = ["security"]

    result = classifier.classify(title, body, labels=labels)
    assert result.primary_intent == IssueIntent.SECURITY
    assert result.confidence >= 0.80
    assert "cve_pattern" in result.detected_signals
    assert "middleware" in result.search_strategy["preferred_node_types"]


def test_classify_docs_intent(classifier: IssueIntentClassifier) -> None:
    title = "Update README and API documentation for v2.0 release"
    body = "Fix typo in quickstart guide and update tutorial specs."
    labels = ["documentation"]

    result = classifier.classify(title, body, labels=labels)
    assert result.primary_intent == IssueIntent.DOCS
    assert result.confidence > 0.75
    assert result.search_strategy["weight_adjustments"]["semantic"] == 0.60


def test_classification_accuracy_on_issue_corpus(classifier: IssueIntentClassifier) -> None:
    """Acceptance criterion: Classification accuracy > 88% on sample corpus."""
    corpus = [
        # BUGS
        ("Crash on startup when database is down", "Connection refused error in session pool", ["bug"], IssueIntent.BUG),
        ("Fix broken link in canvas viewport navigation", "Clicking node fails with undefined error", [], IssueIntent.BUG),
        ("Regression in graph cluster expansion", "Nodes disappear when collapsing parent level 2", ["type:bug"], IssueIntent.BUG),
        ("Null pointer panic during AST parsing", "File syntax_tree.go:42 panics on empty slice", [], IssueIntent.BUG),
        ("TypeError: Cannot read properties of undefined in EdgeLayer", "Stack trace at renderCanvas (EdgeLayer.tsx:42)", [], IssueIntent.BUG),

        # FEATURES
        ("Add support for Go language interfaces and structs", "Implement AST visitors for Go files", ["enhancement"], IssueIntent.FEATURE),
        ("Introduce real-time WebSocket progress tracker", "Allow UI to listen for ingestion status updates", ["feature"], IssueIntent.FEATURE),
        ("Support monorepo workspace boundary analysis", "Enable package detection for pnpm and npm", ["type:feature"], IssueIntent.FEATURE),
        ("Provide interactive canvas navigation controls and minimap", "New zoom controls toolbar", [], IssueIntent.FEATURE),
        ("Add export to SVG functionality in GraphCanvas", "Allow downloading canvas as vector image", [], IssueIntent.FEATURE),

        # REFACTOR
        ("Refactor database ORM models and clean up schemas", "Deduplicate columns across tables", ["refactor"], IssueIntent.REFACTOR),
        ("Optimize subgraph traversal query latency", "Improve performance of recursive CTE queries", ["perf"], IssueIntent.REFACTOR),
        ("Simplify ingestion task runner lifecycle hooks", "Reorganize worker initialization steps", [], IssueIntent.REFACTOR),
        ("Modularize graph store actions in Zustand", "Decouple viewport logic from selection state", ["cleanup"], IssueIntent.REFACTOR),

        # SECURITY
        ("Vulnerability in GitHub App webhook HMAC verification", "Potential signature spoofing risk", ["security"], IssueIntent.SECURITY),
        ("Sanitize SQL inputs in repository filter query", "Prevent possible SQL injection exploit", ["cve"], IssueIntent.SECURITY),
        ("Remediate CVE-2026-9012 auth token leak in debug logs", "Mask credentials during request tracing", [], IssueIntent.SECURITY),
        ("Enforce CORS and CSRF protections on API endpoints", "Prevent unauthorized cross-origin requests", ["security"], IssueIntent.SECURITY),

        # DOCS
        ("Update architectural documentation for Phase 2", "Document 5-signal mapping ranker design", ["docs"], IssueIntent.DOCS),
        ("Fix typo in CONTRIBUTING.md guide", "Grammar corrections in PR guidelines", ["documentation"], IssueIntent.DOCS),
        ("Write deployment manual for Kubernetes Helm chart", "Add step-by-step instructions for cluster setup", [], IssueIntent.DOCS),
        ("Add JSDoc specifications for graph utility functions", "Document parameter types and return contracts", ["doc"], IssueIntent.DOCS),
    ]

    correct = 0
    for title, body, labels, expected_intent in corpus:
        res = classifier.classify(title, body, labels=labels)
        if res.primary_intent == expected_intent:
            correct += 1

    accuracy = correct / len(corpus)
    assert accuracy >= 0.88, f"Classification accuracy was {accuracy:.2%}, expected > 88%"
