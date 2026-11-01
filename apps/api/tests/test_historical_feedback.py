"""Unit and integration tests for Signal 4: Historical Feedback Weighting (Issue #56)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from services.mapping.historical import (
    HistoricalFeedbackWeighter,
    calculate_historical_adjustment,
    normalize_historical_score,
)


def test_calculate_historical_adjustment_formula() -> None:
    # Acceptance criterion: Default prior neutral (0.0) when no historical data exists
    # S_hist = (0 - 0) / (0 + 0 + 2) = 0.0
    s_neutral = calculate_historical_adjustment(positive=0, negative=0)
    assert s_neutral == 0.0
    assert normalize_historical_score(s_neutral) == 0.50

    # Strong positive: 8 positive, 0 negative -> (8 - 0) / 10 = +0.8
    s_pos = calculate_historical_adjustment(positive=8, negative=0)
    assert s_pos == 0.80
    assert normalize_historical_score(s_pos) == 0.90

    # Strong negative (downvoted): 0 positive, 8 negative -> (0 - 8) / 10 = -0.8
    s_neg = calculate_historical_adjustment(positive=0, negative=8)
    assert s_neg == -0.80
    assert normalize_historical_score(s_neg) == 0.10

    # Equal positive and negative: 5 positive, 5 negative -> 0 / 12 = 0.0
    assert calculate_historical_adjustment(positive=5, negative=5) == 0.0


@pytest.mark.asyncio
async def test_historical_feedback_weighter_query() -> None:
    mock_db = AsyncMock()

    # Create mock result rows:
    # row 1: node_upvoted with 6 positive, 0 negative -> S_hist = 6/8 = 0.75 -> norm = 0.875
    # row 2: node_downvoted with 0 positive, 6 negative -> S_hist = -6/8 = -0.75 -> norm = 0.125
    row_up = MagicMock()
    row_up.node_id = "node_up"
    row_up.positive = 6.0
    row_up.negative = 0.0

    row_down = MagicMock()
    row_down.node_id = "node_down"
    row_down.positive = 0.0
    row_down.negative = 6.0

    mock_db.execute.return_value = [row_up, row_down]

    weighter = HistoricalFeedbackWeighter(db=mock_db, repo_id="repo_1")
    weights = await weighter.get_historical_weights()

    # Acceptance criteria:
    # 1. Validated files gain confidence boost on future similar issues
    assert weights["node_up"] > 0.80
    # 2. Downvoted incorrect files penalized
    assert weights["node_down"] < 0.20
    # 3. All scores bounded in [0.0, 1.0]
    for w in weights.values():
        assert 0.0 <= w <= 1.0
