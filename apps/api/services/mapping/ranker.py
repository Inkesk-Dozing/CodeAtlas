"""Issue → code mapping service.

Combines five signals into a single confidence score per node:

1. semantic      - pgvector cosine similarity between issue text and node embedding
2. structural    - lexical overlap of tokens against name/path/summary (pg_trgm + ILIKE)
3. topological   - graph proximity to top lexical hits (1-hop propagation)
4. historical    - prior human feedback on previous mappings for the same node
5. hotspot       - node degree (higher fan-in/fan-out = more central = more likely)

Weights are calibrated so that a node matching on multiple signals reaches the
"high" confidence tier only when at least two independent signals agree.
"""
from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models import CodeEdge, CodeNode, Issue, MappingFeedback

logger = logging.getLogger(__name__)

MODEL_VERSION = "v2.0.0-hybrid"

WEIGHTS = {
    "semantic": 0.40,
    "structural": 0.30,
    "topological": 0.12,
    "historical": 0.10,
    "hotspot": 0.08,
}

TIER_THRESHOLDS = {"high": 0.75, "medium": 0.50, "low": 0.30}

STOPWORDS = frozenset(
    ["a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from", "has", "have", "how", "i", "in", "is", "it", "its", "of", "on", "or", "that", "the", "this", "to", "was", "we", "what", "when", "where", "which", "who", "will", "with", "you", "your", "not", "no", "can", "could", "should", "would", "may", "might", "do", "does", "did", "be", "been", "being"]
)

CODE_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]*")


@dataclass
class RankedNode:
    node: CodeNode
    score: float = 0.0
    signals: dict[str, float] = field(default_factory=dict)
    evidence_keywords: list[str] = field(default_factory=list)
    evidence_patterns: list[str] = field(default_factory=list)


def tokenize(text_content: str, *, keep_stopwords: bool = False) -> list[str]:
    tokens = [t.lower() for t in CODE_TOKEN_RE.findall(text_content or "")]
    if keep_stopwords:
        return tokens
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


def split_ident(token: str) -> list[str]:
    """Split camelCase / snake_case identifiers into sub-tokens."""
    parts = re.findall(r"[A-Z]+(?![a-z])|[A-Z][a-z0-9]*|[a-z0-9]+", token)
    return [p.lower() for p in parts if len(p) > 1]


def tier_for(confidence: float) -> str:
    if confidence >= TIER_THRESHOLDS["high"]:
        return "high"
    if confidence >= TIER_THRESHOLDS["medium"]:
        return "medium"
    if confidence >= TIER_THRESHOLDS["low"]:
        return "low"
    return "excluded"


def build_issue_text(issue: Issue) -> str:
    labels = ", ".join(issue.labels) if issue.labels else ""
    return f"{issue.title}\n{issue.body or ''}\nlabels: {labels}".strip()


async def embed_text(content: str) -> list[float] | None:
    try:
        import httpx

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.ollama_url}/api/embeddings",
                json={"model": settings.ollama_embed_model, "prompt": content[:4000]},
                timeout=15.0,
            )
            if resp.status_code == 200:
                return resp.json().get("embedding")
    except Exception:
        logger.debug("embedding service unavailable", exc_info=True)
    return None


class IssueMapper:
    def __init__(self, db: AsyncSession, repo_id: str):
        self.db = db
        self.repo_id = repo_id

    async def analyze(self, issue: Issue, limit: int = 25) -> list[dict]:
        start = time.time()

        issue_text = build_issue_text(issue)
        query_tokens = tokenize(issue_text)
        query_ident_tokens = {sub for t in query_tokens for sub in split_ident(t)}

        lexical_hits = await self._lexical_signal(query_tokens, query_ident_tokens)
        semantic_hits = await self._semantic_signal(issue_text)
        historical = await self._historical_signal()
        hotspots = await self._hotspot_signal()

        combined: dict[str, RankedNode] = {}

        def acc(node: CodeNode) -> RankedNode:
            if node.id not in combined:
                combined[node.id] = RankedNode(node=node)
            return combined[node.id]

        for node_id, score in lexical_hits.items():
            rn = acc(node_id)
            rn.signals["structural"] = score

        for node_id, score in semantic_hits.items():
            rn = acc(node_id)
            rn.signals["semantic"] = score

        for node_id, score in historical.items():
            rn = acc(node_id)
            rn.signals["historical"] = score

        for node_id, score in hotspots.items():
            rn = acc(node_id)
            rn.signals["hotspot"] = score

        await self._propagation_signal(combined, query_tokens, query_ident_tokens)

        for rn in combined.values():
            rn.score = sum(rn.signals.get(k, 0.0) * w for k, w in WEIGHTS.items())
            rn.evidence_keywords = self._matched_keywords(rn, query_tokens)

        ranked = sorted(combined.values(), key=lambda r: r.score, reverse=True)
        top = [r for r in ranked if r.score >= TIER_THRESHOLDS["low"]][:limit]

        for rn in top:
            await self._attach_suggested_actions(rn)

        logger.info(
            "issue #%s mapped to %d candidates in %.2fs",
            issue.number,
            len(top),
            time.time() - start,
        )

        return [self._to_mapping(r) for r in top]

    # ── signals ──────────────────────────────────────────────────────────

    async def _lexical_signal(
        self, tokens: list[str], ident_tokens: set[str]
    ) -> dict[str, float]:
        if not tokens:
            return {}

        clause = " OR ".join(
            f"(name ILIKE :p{i} OR path ILIKE :p{i} OR COALESCE(summary,'') ILIKE :p{i})"
            for i in range(min(len(tokens), 24))
        )
        params = {f"p{i}": f"%{t}%" for i, t in enumerate(tokens[:24])}
        params["repo_id"] = self.repo_id

        sql = text(
            f"""
            SELECT id,
                   similarity(lower(name || ' ' || path || ' ' || COALESCE(summary,'')), :q) AS sim
            FROM code_nodes
            WHERE repo_id = :repo_id AND ({clause})
            ORDER BY sim DESC
            LIMIT 100
            """
        )
        params["q"] = " ".join(tokens)
        result = await self.db.execute(sql, params)

        hits: dict[str, float] = {}
        for row in result.mappings():
            base = float(row["sim"] or 0.0)
            node = await self.db.get(CodeNode, str(row["id"]))
            if node is None:
                continue
            name_parts = set(split_ident(node.name)) | set(node.name.lower().replace("_", " ").split())
            overlap = len(ident_tokens & name_parts) / max(1, len(ident_tokens))
            hits[node.id] = min(1.0, 0.5 * base + 0.5 * overlap + 0.15 * overlap)
        return hits

    async def _semantic_signal(self, issue_text: str) -> dict[str, float]:
        vector = await embed_text(issue_text)
        if not vector:
            return {}

        sql = text(
            """
            SELECT id, 1 - (embedding <=> CAST(:qv AS vector)) AS score
            FROM code_nodes
            WHERE repo_id = :repo_id AND embedding IS NOT NULL
            ORDER BY embedding <=> CAST(:qv AS vector)
            LIMIT 40
            """
        )
        result = await self.db.execute(sql, {"qv": str(vector), "repo_id": self.repo_id})
        return {
            str(row["id"]): max(0.0, min(1.0, float(row["score"])))
            for row in result.mappings()
            if float(row["score"] or 0) > 0.2
        }

    async def _historical_signal(self) -> dict[str, float]:
        sql = select(
            MappingFeedback.node_id,
            func.count(MappingFeedback.id).label("total"),
            func.sum(
                text(
                    "CASE WHEN rating = 'relevant' THEN 1.0 "
                    "WHEN rating = 'partially_relevant' THEN 0.5 ELSE 0.0 END"
                )
            ).label("positive"),
        ).where(
            MappingFeedback.node_id.in_(
                select(CodeNode.id).where(CodeNode.repo_id == self.repo_id)
            )
        )
        sql = sql.group_by(MappingFeedback.node_id)

        result = await self.db.execute(sql)
        scores: dict[str, float] = {}
        for row in result:
            total = int(row.total or 0)
            positive = float(row.positive or 0.0)
            if total >= 3:
                scores[str(row.node_id)] = positive / total
        return scores

    async def _hotspot_signal(self) -> dict[str, float]:
        sql = text(
            """
            SELECT node_id, count(*) AS degree
            FROM (
                SELECT source_id AS node_id FROM code_edges WHERE repo_id = :repo_id
                UNION ALL
                SELECT target_id AS node_id FROM code_edges WHERE repo_id = :repo_id
            ) e
            GROUP BY node_id
            ORDER BY degree DESC
            LIMIT 60
            """
        )
        result = await self.db.execute(sql, {"repo_id": self.repo_id})
        degrees = [(str(row["node_id"]), int(row["degree"])) for row in result.mappings()]
        if not degrees:
            return {}
        max_degree = max(d for _, d in degrees) or 1
        return {nid: (d / max_degree) ** 0.5 for nid, d in degrees}

    async def _propagation_signal(
        self,
        combined: dict[str, RankedNode],
        tokens: list[str],
        ident_tokens: set[str],
    ) -> None:
        seed_ids = [
            rid
            for rid, rn in combined.items()
            if rn.signals.get("structural", 0.0) > 0.3 or rn.signals.get("semantic", 0.0) > 0.5
        ]
        if not seed_ids:
            return

        edges = await self.db.execute(
            select(CodeEdge).where(
                CodeEdge.repo_id == self.repo_id,
                (CodeEdge.source_id.in_(seed_ids)) | (CodeEdge.target_id.in_(seed_ids)),
            ).limit(300)
        )
        neighbor_ids: set[str] = set()
        for edge in edges.scalars().all():
            neighbor_ids.add(edge.target_id)
            neighbor_ids.add(edge.source_id)
        neighbor_ids -= set(seed_ids)
        if not neighbor_ids:
            return

        nodes = await self.db.execute(select(CodeNode).where(CodeNode.id.in_(neighbor_ids)))
        for node in nodes.scalars().all():
            if node.id in combined:
                rn = combined[node.id]
            else:
                rn = RankedNode(node=node)
                combined[node.id] = rn
            name_parts = set(split_ident(node.name)) | set(node.path.lower().split("/"))
            token_overlap = len({t for t in tokens if t in node.path.lower()}) / max(
                1, len(tokens)
            )
            ident_overlap = len(ident_tokens & name_parts) / max(1, len(ident_tokens))
            rn.signals["topological"] = min(1.0, 0.4 * token_overlap + 0.6 * ident_overlap + 0.2)
            if rn.evidence_patterns is not None:
                rn.evidence_patterns.append("reachable from top candidate")

    def _matched_keywords(self, rn: RankedNode, tokens: list[str]) -> list[str]:
        haystack = f"{rn.node.name} {rn.node.path} {rn.node.summary or ''}".lower()
        return [t for t in tokens if t in haystack][:10]

    async def _attach_suggested_actions(self, rn: RankedNode) -> None:
        actions: list[str] = []
        node_type = rn.node.type
        if node_type in ("route", "endpoint", "handler"):
            actions.append("Inspect route handler for the reported behavior")
        elif node_type in ("component", "view", "page"):
            actions.append("Review UI component rendering logic")
        elif node_type in ("function", "method"):
            actions.append("Add/adjust unit test coverage")
        elif node_type in ("class", "service", "model"):
            actions.append("Trace class responsibilities end-to-end")
        elif node_type in ("file", "module", "config"):
            actions.append("Check module configuration and side effects")
        else:
            actions.append("Inspect definition and its callers")

        if rn.signals.get("hotspot", 0) > 0.7:
            actions.append("High-fan-out hotspot: changes here impact many callers")
        if rn.signals.get("historical", 0) >= 0.66:
            actions.append("Previously validated relevant by reviewers")
        rn.evidence_patterns = list(dict.fromkeys(rn.evidence_patterns + actions))

    def _to_mapping(self, rn: RankedNode) -> dict:
        tier = tier_for(rn.score)
        return {
            "node": rn.node,
            "confidence": round(rn.score, 4),
            "confidence_tier": tier,
            "evidence": {
                "semantic_match": rn.signals.get("semantic", 0.0) >= 0.5,
                "structural_match": rn.signals.get("structural", 0.0) >= 0.3,
                "historical_match": rn.signals.get("historical", 0.0) > 0.0,
                "propagation_match": rn.signals.get("topological", 0.0) > 0.0,
                "matched_keywords": rn.evidence_keywords,
                "matched_patterns": [p for p in rn.evidence_patterns if p.startswith("reachable")],
            },
            "suggested_actions": [
                p for p in rn.evidence_patterns if not p.startswith("reachable")
            ],
        }
