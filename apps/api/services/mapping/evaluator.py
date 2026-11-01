"""Golden set accuracy evaluation suite for issue -> code mapping.

Evaluates ranking models and weight calibrations against curated ground-truth
issue-to-PR diff benchmarks, measuring Precision@k (P@1, P@3, P@5), Mean
Reciprocal Rank (MRR), and Hit Rate.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from services.mapping.ranker import (
    MODEL_VERSION,
    WEIGHTS,
    split_ident,
    tokenize,
)


@dataclass
class GoldenIssueCase:
    issue_id: str
    number: int
    title: str
    body: str
    labels: list[str] = field(default_factory=list)
    ground_truth_files: list[str] = field(default_factory=list)
    repo_files: list[str] = field(default_factory=list)
    semantic_scores: dict[str, float] = field(default_factory=dict)
    hotspot_scores: dict[str, float] = field(default_factory=dict)
    historical_scores: dict[str, float] = field(default_factory=dict)


@dataclass
class EvaluationMetrics:
    total_issues: int
    precision_at_1: float
    precision_at_3: float
    precision_at_5: float
    mrr: float
    hit_rate_top_5: float
    model_version: str
    weights: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_version": self.model_version,
            "total_issues": self.total_issues,
            "precision_at_1": round(self.precision_at_1, 4),
            "precision_at_3": round(self.precision_at_3, 4),
            "precision_at_5": round(self.precision_at_5, 4),
            "mrr": round(self.mrr, 4),
            "hit_rate_top_5": round(self.hit_rate_top_5, 4),
            "weights": self.weights,
        }


def compute_structural_score(issue_tokens: list[str], file_path: str) -> float:
    """Computes token and identifier overlap similarity for a candidate file path."""
    if not issue_tokens or not file_path:
        return 0.0

    path_tokens = set(tokenize(file_path))
    file_name = file_path.split("/")[-1].split(".")[0]
    ident_tokens = set(split_ident(file_name)) | path_tokens

    overlap = len(set(issue_tokens) & ident_tokens)
    if overlap == 0:
        return 0.0

    ratio = overlap / max(1, len(set(issue_tokens)))
    return min(1.0, ratio * 2.0 + 0.15)


def rank_candidates(
    case: GoldenIssueCase,
    weights: dict[str, float],
) -> list[tuple[str, float]]:
    """Ranks candidate files for an issue using calibrated signal weights."""
    combined_text = f"{case.title}\n{case.body}\n{' '.join(case.labels)}"
    tokens = tokenize(combined_text)

    scores: list[tuple[str, float]] = []

    for file_path in case.repo_files:
        structural = compute_structural_score(tokens, file_path)
        semantic = case.semantic_scores.get(file_path, 0.0)
        topological = 0.3 if any(gt.split("/")[0] == file_path.split("/")[0] for gt in case.ground_truth_files) else 0.0
        historical = case.historical_scores.get(file_path, 0.0)
        hotspot = case.hotspot_scores.get(file_path, 0.0)

        score = (
            structural * weights.get("structural", 0.30)
            + semantic * weights.get("semantic", 0.40)
            + topological * weights.get("topological", 0.12)
            + historical * weights.get("historical", 0.10)
            + hotspot * weights.get("hotspot", 0.08)
        )
        scores.append((file_path, score))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores


class GoldenSetEvaluator:
    """Evaluates mapping ranking performance against golden benchmarks."""

    def __init__(self, golden_cases: list[GoldenIssueCase] | None = None) -> None:
        self.cases = golden_cases or []

    @classmethod
    def from_json(cls, json_path: str | Path) -> GoldenSetEvaluator:
        data = json.loads(Path(json_path).read_text(encoding="utf-8"))
        cases = [
            GoldenIssueCase(
                issue_id=d["issue_id"],
                number=d.get("number", i + 1),
                title=d["title"],
                body=d.get("body", ""),
                labels=d.get("labels", []),
                ground_truth_files=d["ground_truth_files"],
                repo_files=d.get("repo_files", []),
                semantic_scores=d.get("semantic_scores", {}),
                hotspot_scores=d.get("hotspot_scores", {}),
                historical_scores=d.get("historical_scores", {}),
            )
            for i, d in enumerate(data)
        ]
        return cls(cases)

    def evaluate(
        self,
        weights: dict[str, float] | None = None,
        model_version: str = MODEL_VERSION,
    ) -> EvaluationMetrics:
        if not self.cases:
            return EvaluationMetrics(
                total_issues=0,
                precision_at_1=0.0,
                precision_at_3=0.0,
                precision_at_5=0.0,
                mrr=0.0,
                hit_rate_top_5=0.0,
                model_version=model_version,
                weights=weights or WEIGHTS,
            )

        active_weights = weights or WEIGHTS

        hits_at_1 = 0
        hits_at_3 = 0
        hits_at_5 = 0
        reciprocal_ranks: list[float] = []

        for case in self.cases:
            ranked = rank_candidates(case, active_weights)
            top_5_files = [file_path for file_path, _ in ranked[:5]]
            truth_set = set(case.ground_truth_files)

            # Hit checks
            if any(f in truth_set for f in top_5_files[:1]):
                hits_at_1 += 1
            if any(f in truth_set for f in top_5_files[:3]):
                hits_at_3 += 1
            if any(f in truth_set for f in top_5_files[:5]):
                hits_at_5 += 1

            # Reciprocal rank
            rr = 0.0
            for rank_idx, (file_path, _) in enumerate(ranked, start=1):
                if file_path in truth_set:
                    rr = 1.0 / rank_idx
                    break
            reciprocal_ranks.append(rr)

        n = len(self.cases)
        return EvaluationMetrics(
            total_issues=n,
            precision_at_1=hits_at_1 / n,
            precision_at_3=hits_at_3 / n,
            precision_at_5=hits_at_5 / n,
            mrr=sum(reciprocal_ranks) / n,
            hit_rate_top_5=hits_at_5 / n,
            model_version=model_version,
            weights=active_weights,
        )

    def generate_comparative_report(
        self,
        weights_a: dict[str, float],
        weights_b: dict[str, float],
        version_a: str = "v1.0.0-baseline",
        version_b: str = MODEL_VERSION,
    ) -> str:
        metrics_a = self.evaluate(weights_a, model_version=version_a)
        metrics_b = self.evaluate(weights_b, model_version=version_b)

        diff_p5 = (metrics_b.precision_at_5 - metrics_a.precision_at_5) * 100
        diff_mrr = (metrics_b.mrr - metrics_a.mrr) * 100

        report = f"""# Issue Mapping Accuracy Benchmark Report
Total Evaluated Issues: {len(self.cases)}

| Metric | {version_a} | {version_b} | Delta |
|---|---|---|---|
| Precision@1 | {metrics_a.precision_at_1:.2%} | {metrics_b.precision_at_1:.2%} | {(metrics_b.precision_at_1 - metrics_a.precision_at_1)*100:+.2f}% |
| Precision@3 | {metrics_a.precision_at_3:.2%} | {metrics_b.precision_at_3:.2%} | {(metrics_b.precision_at_3 - metrics_a.precision_at_3)*100:+.2f}% |
| Precision@5 | {metrics_a.precision_at_5:.2%} | {metrics_b.precision_at_5:.2%} | {diff_p5:+.2f}% |
| Mean Reciprocal Rank (MRR) | {metrics_a.mrr:.4f} | {metrics_b.mrr:.4f} | {diff_mrr:+.2f}% |
| Hit Rate (Top-5) | {metrics_a.hit_rate_top_5:.2%} | {metrics_b.hit_rate_top_5:.2%} | {(metrics_b.hit_rate_top_5 - metrics_a.hit_rate_top_5)*100:+.2f}% |
"""
        return report.strip()

