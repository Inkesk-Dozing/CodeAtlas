"""Unit tests for 5-Signal Confidence Calibration & Tier Assignment (Issue #58)."""
from __future__ import annotations

import pytest

from services.mapping.calibration import (
    CALIBRATED_WEIGHTS,
    calibrate_confidence_sigmoid,
    classify_confidence_tier,
    compute_weighted_score,
)


def test_calibrated_weights_sum_to_one() -> None:
    # 0.35 + 0.30 + 0.15 + 0.10 + 0.10 = 1.00
    total = sum(CALIBRATED_WEIGHTS.values())
    assert abs(total - 1.0) < 1e-6
    assert CALIBRATED_WEIGHTS["semantic"] == 0.35
    assert CALIBRATED_WEIGHTS["structural"] == 0.30
    assert CALIBRATED_WEIGHTS["topological"] == 0.15
    assert CALIBRATED_WEIGHTS["historical"] == 0.10
    assert CALIBRATED_WEIGHTS["hotspot"] == 0.10


def test_compute_weighted_score() -> None:
    signals = {
        "semantic": 0.80,
        "structural": 0.90,
        "topological": 0.50,
        "historical": 0.50,
        "hotspot": 0.60,
    }
    # 0.80 * 0.35 = 0.280
    # 0.90 * 0.30 = 0.270
    # 0.50 * 0.15 = 0.075
    # 0.50 * 0.10 = 0.050
    # 0.60 * 0.10 = 0.060
    # Total = 0.735
    score = compute_weighted_score(signals)
    assert score == pytest.approx(0.735, abs=1e-3)


def test_sigmoid_confidence_calibration() -> None:
    # Monotonicity test
    scores = [0.0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0]
    calibrated = [calibrate_confidence_sigmoid(s) for s in scores]

    assert calibrated[0] == 0.0
    assert calibrated[-1] == 1.0
    assert calibrated[3] == pytest.approx(0.50, abs=1e-2)  # midpoint at x0 = 0.50

    # Strict monotonicity
    for i in range(len(calibrated) - 1):
        assert calibrated[i] <= calibrated[i + 1]


def test_classify_confidence_tier() -> None:
    # High: >= 0.75
    assert classify_confidence_tier(0.75) == "high"
    assert classify_confidence_tier(0.85) == "high"
    assert classify_confidence_tier(1.00) == "high"

    # Medium: 0.50 - 0.74
    assert classify_confidence_tier(0.50) == "medium"
    assert classify_confidence_tier(0.65) == "medium"
    assert classify_confidence_tier(0.7499) == "medium"

    # Low: < 0.50
    assert classify_confidence_tier(0.4999) == "low"
    assert classify_confidence_tier(0.25) == "low"
    assert classify_confidence_tier(0.00) == "low"
