"""Signal 2: Structural Heuristic Matcher via Trigram & Exact Symbol Match.

Matches extracted symbols, filenames, and file paths against repository code nodes:
- Exact filename match receives 1.0 structural score.
- Partial path match receives 0.7 structural score.
- Symbol substring / identifier match receives 0.5 structural score.
- Trigram similarity calculation using PostgreSQL `similarity(code_nodes.name, query_symbol)`
  or Python fallback trigram calculation.
- Case-insensitive tokenization and splitting across camelCase, snake_case, and kebab-case.
- Output scores strictly bounded in [0.0, 1.0].
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import CodeNode
from services.mapping.preprocessor import PreprocessedIssue

logger = logging.getLogger(__name__)

SCORE_EXACT_FILENAME = 1.0
SCORE_PARTIAL_PATH = 0.70
SCORE_SYMBOL_MATCH = 0.50
SCORE_TRIGRAM_BASE = 0.35


def normalize_identifier(ident: str) -> list[str]:
    """Splits camelCase, snake_case, kebab-case, or dot-separated identifiers into lowercase tokens."""
    if not ident:
        return []
    # Replace separators with spaces
    cleaned = re.sub(r"[-_./\\]+", " ", ident)
    # Split camelCase / PascalCase
    parts = re.findall(r"[A-Z]+(?![a-z])|[A-Z][a-z0-9]*|[a-z0-9]+", cleaned)
    return [p.lower() for p in parts if len(p) > 1]


def compute_trigram_similarity(str1: str, str2: str) -> float:
    """Computes character trigram Jaccard/Dice similarity between two strings."""
    s1, s2 = str1.lower().strip(), str2.lower().strip()
    if not s1 or not s2:
        return 0.0
    if s1 == s2:
        return 1.0

    # Pad strings as done by PostgreSQL pg_trgm (two leading spaces, one trailing space)
    padded1 = f"  {s1} "
    padded2 = f"  {s2} "

    trigrams1 = {padded1[i:i + 3] for i in range(len(padded1) - 2)}
    trigrams2 = {padded2[i:i + 3] for i in range(len(padded2) - 2)}

    intersection = len(trigrams1 & trigrams2)
    union = len(trigrams1 | trigrams2)
    if union == 0:
        return 0.0
    return intersection / union


@dataclass
class StructuralMatchResult:
    node_id: str
    score: float
    matched_pattern: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "score": round(self.score, 4),
            "matched_pattern": self.matched_pattern,
        }


class StructuralMatcher:
    """Matches issue file paths, symbols, and tokens against repository CodeNodes."""

    def __init__(self, db: AsyncSession, repo_id: str) -> None:
        self.db = db
        self.repo_id = repo_id

    async def match_candidates(
        self,
        query_tokens: list[str],
        query_ident_tokens: set[str],
        preprocessed: PreprocessedIssue | None = None,
        nodes: list[CodeNode] | None = None,
    ) -> dict[str, float]:
        """Calculates structural heuristic scores bounded in [0.0, 1.0]."""
        # Fetch repository nodes if not supplied in-memory
        if nodes is None:
            stmt = select(CodeNode).where(CodeNode.repo_id == self.repo_id)
            exec_res = await self.db.execute(stmt)
            repo_nodes = list(exec_res.scalars().all())
        else:
            repo_nodes = nodes

        if not repo_nodes:
            return {}

        extracted_files = [f.lower().replace("\\", "/") for f in (preprocessed.file_paths if preprocessed else [])]
        extracted_symbols = [s.lower() for s in (preprocessed.code_symbols if preprocessed else [])]

        scores: dict[str, float] = {}

        for node in repo_nodes:
            node_path = (node.path or "").lower().replace("\\", "/")
            node_name = (node.name or "").lower()
            node_filename = node_path.split("/")[-1] if "/" in node_path else node_path
            node_stem = node_filename.split(".")[0] if "." in node_filename else node_filename

            best_score = 0.0

            # 1. Exact Filename Match (1.0)
            for ef in extracted_files:
                ef_filename = ef.split("/")[-1] if "/" in ef else ef
                if ef in (node_path, node_name) or ef_filename == node_filename:
                    best_score = max(best_score, SCORE_EXACT_FILENAME)
                    break

            # 2. Partial Path Match (0.7)
            if best_score < SCORE_EXACT_FILENAME:
                for ef in extracted_files:
                    if ef in node_path or node_path in ef:
                        best_score = max(best_score, SCORE_PARTIAL_PATH)
                        break

            # 3. Explicit Code Symbol Match (0.5)
            if best_score < SCORE_PARTIAL_PATH:
                for sym in extracted_symbols:
                    if sym == node_name or sym in node_name:
                        best_score = max(best_score, SCORE_SYMBOL_MATCH)
                        break

            # 4. Trigram & Identifier Overlap Similarity
            node_tokens = set(normalize_identifier(node.name)) | set(normalize_identifier(node_stem))
            token_overlap = len(query_ident_tokens & node_tokens)
            if token_overlap > 0:
                overlap_ratio = token_overlap / max(1, len(node_tokens))
                ident_score = min(0.65, 0.30 + overlap_ratio * 0.35)
                best_score = max(best_score, ident_score)

            # Check trigram against query symbols / tokens
            for q_tok in query_tokens[:15]:
                if len(q_tok) >= 3:
                    trig_sim = compute_trigram_similarity(q_tok, node_name)
                    if trig_sim >= 0.40:
                        trig_score = min(0.60, SCORE_TRIGRAM_BASE + trig_sim * 0.25)
                        best_score = max(best_score, trig_score)

            if best_score > 0.05:
                # Guaranteed bounded between [0.0, 1.0]
                scores[node.id] = min(1.0, max(0.0, round(best_score, 4)))

        return scores
