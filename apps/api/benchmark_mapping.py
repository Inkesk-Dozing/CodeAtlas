"""CLI benchmark script to evaluate mapping accuracy against the golden benchmark dataset.

Usage:
    python apps/api/benchmark_mapping.py [--golden-set PATH] [--threshold FLOAT] [--compare]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add api directory to sys.path
api_root = Path(__file__).resolve().parent
if str(api_root) not in sys.path:
    sys.path.insert(0, str(api_root))

from services.mapping.evaluator import GoldenSetEvaluator  # noqa: E402
from services.mapping.ranker import MODEL_VERSION, WEIGHTS  # noqa: E402

# Historical / baseline weights before hybrid calibration
BASELINE_WEIGHTS: dict[str, float] = {
    "semantic": 0.20,
    "structural": 0.20,
    "topological": 0.20,
    "historical": 0.20,
    "hotspot": 0.20,
}


def run_benchmark(
    golden_path: Path,
    threshold: float = 0.75,
    compare: bool = True,
) -> int:
    if not golden_path.exists():
        print(f"Error: Golden set file not found at {golden_path}", file=sys.stderr)
        return 1

    evaluator = GoldenSetEvaluator.from_json(golden_path)
    metrics = evaluator.evaluate(weights=WEIGHTS, model_version=MODEL_VERSION)

    print(f"=== Mapping Benchmark Run ({metrics.model_version}) ===")
    print(f"Total Issues Evaluated : {metrics.total_issues}")
    print(f"Precision@1            : {metrics.precision_at_1:.2%}")
    print(f"Precision@3            : {metrics.precision_at_3:.2%}")
    print(f"Precision@5            : {metrics.precision_at_5:.2%}")
    print(f"Mean Reciprocal Rank   : {metrics.mrr:.4f}")
    print(f"Hit Rate (Top-5)       : {metrics.hit_rate_top_5:.2%}")
    print(f"Target P@5 Threshold   : {threshold:.2%}")

    if compare:
        print("\n" + evaluator.generate_comparative_report(
            weights_a=BASELINE_WEIGHTS,
            weights_b=WEIGHTS,
            version_a="v1.0.0-baseline",
            version_b=MODEL_VERSION,
        ))

    if metrics.precision_at_5 < threshold:
        print(
            f"\n[FAIL] Precision@5 ({metrics.precision_at_5:.2%}) is below threshold ({threshold:.2%})!",
            file=sys.stderr,
        )
        return 1

    print(f"\n[PASS] Precision@5 ({metrics.precision_at_5:.2%}) >= threshold ({threshold:.2%}).")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate CodeAtlas issue mapping model against golden dataset.")
    parser.add_argument(
        "--golden-set",
        type=Path,
        default=api_root / "tests" / "fixtures" / "golden_mapping_set.json",
        help="Path to golden set JSON file.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.75,
        help="Minimum required Precision@5 (default: 0.75).",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        default=True,
        help="Generate comparative report between baseline and calibrated weights.",
    )
    args = parser.parse_args()

    exit_code = run_benchmark(
        golden_path=args.golden_set,
        threshold=args.threshold,
        compare=args.compare,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
