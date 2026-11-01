"""Tests for the golden set accuracy evaluation suite and benchmark harness."""
from __future__ import annotations

from pathlib import Path

import pytest

from services.mapping.evaluator import (
    EvaluationMetrics,
    GoldenIssueCase,
    GoldenSetEvaluator,
    compute_structural_score,
    rank_candidates,
)
from services.mapping.ranker import MODEL_VERSION, WEIGHTS

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
GOLDEN_SET_PATH = FIXTURES_DIR / "golden_mapping_set.json"


@pytest.fixture
def golden_cases() -> list[GoldenIssueCase]:
    assert GOLDEN_SET_PATH.exists(), f"Golden set file missing: {GOLDEN_SET_PATH}"
    evaluator = GoldenSetEvaluator.from_json(GOLDEN_SET_PATH)
    return evaluator.cases


def test_golden_set_fixture_has_100_cases(golden_cases: list[GoldenIssueCase]) -> None:
    assert len(golden_cases) == 100
    for case in golden_cases:
        assert case.issue_id.startswith("issue_")
        assert case.title
        assert len(case.ground_truth_files) >= 1
        assert len(case.repo_files) >= 5
        # Ensure ground truth file is in candidate files
        assert all(gt in case.repo_files for gt in case.ground_truth_files)


def test_compute_structural_score() -> None:
    tokens = ["canvas", "virtualization", "viewport", "zoom"]
    # Path match
    score = compute_structural_score(tokens, "apps/web/src/components/canvas/GraphCanvas.tsx")
    assert score > 0.0

    # Non match
    score_unrelated = compute_structural_score(tokens, "apps/api/routers/auth.py")
    assert score_unrelated == 0.0

    # Empty edge cases
    assert compute_structural_score([], "apps/api/routers/auth.py") == 0.0
    assert compute_structural_score(tokens, "") == 0.0


def test_rank_candidates() -> None:
    case = GoldenIssueCase(
        issue_id="test_01",
        number=1,
        title="Fix canvas viewport zoom",
        body="Zoom calculation needs bounds check",
        labels=["component:canvas", "bug"],
        ground_truth_files=["apps/web/src/components/canvas/GraphCanvas.tsx"],
        repo_files=[
            "apps/web/src/components/canvas/GraphCanvas.tsx",
            "apps/api/routers/auth.py",
            "apps/api/database/models.py",
        ],
        semantic_scores={"apps/web/src/components/canvas/GraphCanvas.tsx": 0.95},
        hotspot_scores={"apps/web/src/components/canvas/GraphCanvas.tsx": 0.8},
        historical_scores={"apps/web/src/components/canvas/GraphCanvas.tsx": 0.85},
    )

    ranked = rank_candidates(case, WEIGHTS)
    assert len(ranked) == 3
    # Top ranked should be the ground truth
    assert ranked[0][0] == "apps/web/src/components/canvas/GraphCanvas.tsx"
    assert ranked[0][1] > ranked[1][1]


def test_golden_set_evaluator_metrics_assertion() -> None:
    evaluator = GoldenSetEvaluator.from_json(GOLDEN_SET_PATH)
    metrics = evaluator.evaluate(weights=WEIGHTS, model_version=MODEL_VERSION)

    assert isinstance(metrics, EvaluationMetrics)
    assert metrics.total_issues == 100

    # Acceptance criterion: Precision@5 >= 75%
    assert metrics.precision_at_5 >= 0.75, f"P@5 was {metrics.precision_at_5:.2%}, expected >= 75%"

    # Sanity checks on ranking metrics
    assert 0.0 <= metrics.precision_at_1 <= metrics.precision_at_3 <= metrics.precision_at_5 <= 1.0
    assert metrics.mrr > 0.0
    assert metrics.hit_rate_top_5 >= 0.75

    as_dict = metrics.to_dict()
    assert as_dict["total_issues"] == 100
    assert as_dict["model_version"] == MODEL_VERSION
    assert "precision_at_5" in as_dict


def test_comparative_report_generation() -> None:
    evaluator = GoldenSetEvaluator.from_json(GOLDEN_SET_PATH)
    baseline_weights = {
        "semantic": 0.1,
        "structural": 0.1,
        "topological": 0.1,
        "historical": 0.5,
        "hotspot": 0.2,
    }
    report = evaluator.generate_comparative_report(
        weights_a=baseline_weights,
        weights_b=WEIGHTS,
        version_a="v1.0.0-baseline",
        version_b="v2.0.0-hybrid",
    )

    assert "# Issue Mapping Accuracy Benchmark Report" in report
    assert "Total Evaluated Issues: 100" in report
    assert "v1.0.0-baseline" in report
    assert "v2.0.0-hybrid" in report
    assert "Precision@5" in report
    assert "Mean Reciprocal Rank (MRR)" in report


def test_empty_evaluator() -> None:
    empty_evaluator = GoldenSetEvaluator([])
    metrics = empty_evaluator.evaluate()
    assert metrics.total_issues == 0
    assert metrics.precision_at_5 == 0.0
    assert metrics.mrr == 0.0
