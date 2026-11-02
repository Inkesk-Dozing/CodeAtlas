"""Signal 4: Historical Reviewer Feedback Weighting Service.

Aggregates engineer feedback (thumbs up / thumbs down / relevant / irrelevant)
to adjust candidate confidence:
- Queries `mapping_feedback` table for prior user ratings.
- Calculates Laplace-smoothed Bayesian historical score:
    S_hist = (positive - negative) / (positive + negative + 2)
  yielding a value strictly in (-1.0, 1.0).
- Normalizes S_hist to [0.0, 1.0] for weighted signal combination:
    Normalized S_hist = (S_hist + 1.0) / 2.0
  where:
    - Default prior (0 positive, 0 negative): S_hist = 0.0 -> Normalized = 0.5 (neutral)
    - Strongly downvoted (e.g. 0 pos, 8 neg): S_hist = -8/10 = -0.8 -> Normalized = 0.1 (penalized)
    - Strongly upvoted (e.g. 8 pos, 0 neg): S_hist = +8/10 = +0.8 -> Normalized = 0.9 (boosted)
- Penalizes false positives and boosts validated mappings on subsequent similar issues.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from models import CodeNode, MappingFeedback

logger = logging.getLogger(__name__)

DEFAULT_NEUTRAL_SCORE = 0.50


def calculate_historical_adjustment(positive: float, negative: float) -> float:
    """Calculates S_hist = (positive - negative) / (positive + negative + 2).

    Returns raw score in [-1.0, 1.0].
    """
    pos = max(0.0, float(positive))
    neg = max(0.0, float(negative))
    denom = pos + neg + 2.0
    return (pos - neg) / denom


def normalize_historical_score(s_hist: float) -> float:
    """Normalizes raw S_hist from [-1.0, 1.0] to [0.0, 1.0]."""
    clamped = max(-1.0, min(1.0, s_hist))
    return round((clamped + 1.0) / 2.0, 4)


@dataclass
class FeedbackSummary:
    node_id: str
    positive_count: float
    negative_count: float
    raw_adjustment: float
    normalized_score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "positive": self.positive_count,
            "negative": self.negative_count,
            "raw_adjustment": round(self.raw_adjustment, 4),
            "normalized_score": round(self.normalized_score, 4),
        }


class HistoricalFeedbackWeighter:
    """Aggregates and computes historical feedback weights across repository nodes."""

    def __init__(self, db: AsyncSession, repo_id: str) -> None:
        self.db = db
        self.repo_id = repo_id

    async def get_historical_weights(
        self,
        node_ids: list[str] | None = None,
    ) -> dict[str, float]:
        """Queries prior feedback ratings and returns mapping of node_id -> normalized historical score in [0.0, 1.0]."""
        # Build query counting positive vs negative ratings
        # Positive ratings: relevant (1.0), partially_relevant (0.5), thumbs_up (1.0)
        # Negative ratings: irrelevant (1.0), thumbs_down (1.0), wrong (1.0)
        stmt = select(
            MappingFeedback.node_id,
            func.sum(
                text(
                    "CASE "
                    "WHEN rating IN ('relevant', 'thumbs_up', 'up') THEN 1.0 "
                    "WHEN rating = 'partially_relevant' THEN 0.5 "
                    "ELSE 0.0 END"
                )
            ).label("positive"),
            func.sum(
                text(
                    "CASE "
                    "WHEN rating IN ('irrelevant', 'thumbs_down', 'down', 'wrong') THEN 1.0 "
                    "ELSE 0.0 END"
                )
            ).label("negative"),
        ).where(
            MappingFeedback.node_id.in_(
                select(CodeNode.id).where(CodeNode.repo_id == self.repo_id)
            )
        )

        if node_ids is not None:
            if not node_ids:
                return {}
            stmt = stmt.where(MappingFeedback.node_id.in_(node_ids))

        stmt = stmt.group_by(MappingFeedback.node_id)

        try:
            result = await self.db.execute(stmt)
            scores: dict[str, float] = {}

            for row in result:
                nid = str(row.node_id)
                pos = float(row.positive or 0.0)
                neg = float(row.negative or 0.0)

                raw_adj = calculate_historical_adjustment(pos, neg)
                scores[nid] = round(normalize_historical_score(raw_adj), 4)

            return scores
        except Exception:
            logger.exception("Error querying historical mapping feedback")
            return {}
