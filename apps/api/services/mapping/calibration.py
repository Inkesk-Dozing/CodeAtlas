"""Confidence calibration and tier classification for issue-to-code mapping.

Implements:
- Weighted linear combination:
    Score = 0.35 * S_sem + 0.30 * S_struct + 0.15 * S_topo + 0.10 * S_hist + 0.10 * S_hot
- Sigmoid calibration mapping raw multi-signal scores into smooth, intuitive percentages [0.0, 1.0].
- Actionable tier categorization:
    - High: >= 0.75 (Green badge - primary files to edit)
    - Medium: 0.50 - 0.74 (Yellow badge - secondary dependencies or context)
    - Low: < 0.50 (Gray badge - exploratory reference)
"""
from __future__ import annotations

import math
from typing import Literal

ConfidenceTier = Literal["high", "medium", "low"]

# Authoritative Issue #58 5-signal base weights
CALIBRATED_WEIGHTS: dict[str, float] = {
    "semantic": 0.35,
    "structural": 0.30,
    "topological": 0.15,
    "historical": 0.10,
    "hotspot": 0.10,
}

# Tier boundaries matching issue specifications
TIER_HIGH_THRESHOLD = 0.75
TIER_MEDIUM_THRESHOLD = 0.50


def compute_weighted_score(
    signals: dict[str, float],
    weights: dict[str, float] | None = None,
) -> float:
    """Computes the weighted linear combination of the 5 mapping signals.

    Score = 0.35 * S_sem + 0.30 * S_struct + 0.15 * S_topo + 0.10 * S_hist + 0.10 * S_hot
    """
    w = weights if weights is not None else CALIBRATED_WEIGHTS
    score = (
        signals.get("semantic", 0.0) * w.get("semantic", 0.35)
        + signals.get("structural", 0.0) * w.get("structural", 0.30)
        + signals.get("topological", 0.0) * w.get("topological", 0.15)
        + signals.get("historical", 0.0) * w.get("historical", 0.10)
        + signals.get("hotspot", 0.0) * w.get("hotspot", 0.10)
    )
    return round(score, 4)


def calibrate_confidence_sigmoid(
    raw_score: float,
    k: float = 6.0,
    x0: float = 0.50,
) -> float:
    """Applies a smooth sigmoid calibration curve mapping raw score to [0.0, 1.0].

    sigma(x) = 1 / (1 + exp(-k * (x - x0)))
    Normalized so that:
      - raw_score <= 0.0 -> near 0.0
      - raw_score == x0 -> exactly 0.50
      - raw_score >= 1.0 -> near 1.0
    """
    if raw_score <= 0.0:
        return 0.0
    if raw_score >= 1.0:
        return 1.0

    # Unnormalized logistic value
    sigmoid_val = 1.0 / (1.0 + math.exp(-k * (raw_score - x0)))

    # Normalize between sigma(0) and sigma(1)
    sig_min = 1.0 / (1.0 + math.exp(-k * (0.0 - x0)))
    sig_max = 1.0 / (1.0 + math.exp(-k * (1.0 - x0)))

    calibrated = (sigmoid_val - sig_min) / (sig_max - sig_min)
    return round(min(1.0, max(0.0, calibrated)), 4)


def classify_confidence_tier(confidence: float) -> ConfidenceTier:
    """Classifies calibrated confidence into High, Medium, or Low tier.

    - High: >= 0.75 (primary candidate to edit)
    - Medium: 0.50 - 0.74 (secondary dependency or caller context)
    - Low: < 0.50 (exploratory reference)
    """
    if confidence >= TIER_HIGH_THRESHOLD:
        return "high"
    if confidence >= TIER_MEDIUM_THRESHOLD:
        return "medium"
    return "low"
