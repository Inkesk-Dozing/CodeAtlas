"""Issue Intent Classifier for CodeAtlas Issue Mapping.

Classifies GitHub issues into primary intent categories:
- BUG: Runtime defects, crashes, unexpected behaviors, regressions
- FEATURE: New capability, enhancement, feature request, addition
- REFACTOR: Code cleanup, performance optimization, restructuring, tech debt
- SECURITY: Vulnerabilities, CVEs, token handling, authentication bypass, sanitized inputs
- DOCS: Documentation updates, typos, guides, README, specs

Uses multi-feature scoring:
1. Label indicators (e.g. `bug`, `enhancement`, `security`, `documentation`)
2. Title & body keyword lexicon matches
3. Structural indicators (presence of stack traces, reproduction steps, code blocks)

Provides intent-adjusted search strategy weights and node-type filters.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from services.mapping.preprocessor import PreprocessedIssue


class IssueIntent(StrEnum):
    BUG = "BUG"
    FEATURE = "FEATURE"
    REFACTOR = "REFACTOR"
    SECURITY = "SECURITY"
    DOCS = "DOCS"


# Label pattern mappings
LABEL_PATTERNS: dict[IssueIntent, list[re.Pattern]] = {
    IssueIntent.BUG: [
        re.compile(r"^bug\b", re.IGNORECASE),
        re.compile(r"^defect\b", re.IGNORECASE),
        re.compile(r"^error\b", re.IGNORECASE),
        re.compile(r"^regression\b", re.IGNORECASE),
        re.compile(r"^fix\b", re.IGNORECASE),
    ],
    IssueIntent.FEATURE: [
        re.compile(r"^enhancement\b", re.IGNORECASE),
        re.compile(r"^feature\b", re.IGNORECASE),
        re.compile(r"^feat\b", re.IGNORECASE),
        re.compile(r"^request\b", re.IGNORECASE),
    ],
    IssueIntent.REFACTOR: [
        re.compile(r"^refactor\b", re.IGNORECASE),
        re.compile(r"^cleanup\b", re.IGNORECASE),
        re.compile(r"^performance\b", re.IGNORECASE),
        re.compile(r"^perf\b", re.IGNORECASE),
        re.compile(r"^optimization\b", re.IGNORECASE),
        re.compile(r"^tech-debt\b", re.IGNORECASE),
    ],
    IssueIntent.SECURITY: [
        re.compile(r"^security\b", re.IGNORECASE),
        re.compile(r"^cve\b", re.IGNORECASE),
        re.compile(r"^vulnerability\b", re.IGNORECASE),
        re.compile(r"^audit\b", re.IGNORECASE),
    ],
    IssueIntent.DOCS: [
        re.compile(r"^doc", re.IGNORECASE),
        re.compile(r"^documentation\b", re.IGNORECASE),
        re.compile(r"^typo\b", re.IGNORECASE),
        re.compile(r"^readme\b", re.IGNORECASE),
    ],
}

# Keyword lexicon mappings
KEYWORD_PATTERNS: dict[IssueIntent, list[str]] = {
    IssueIntent.BUG: [
        "bug", "crash", "error", "fail", "failure", "broken", "traceback",
        "exception", "panic", "segfault", "regression", "unexpected", "incorrect",
        "hang", "freeze", "infinite loop", "not working", "cannot", "unable to",
    ],
    IssueIntent.FEATURE: [
        "feature", "add", "support", "implement", "introduce", "new", "allow",
        "enable", "capability", "provide", "integration", "enhancement", "option",
        "extension", "extend",
    ],
    IssueIntent.REFACTOR: [
        "refactor", "cleanup", "clean up", "reorganize", "restructure", "simplify",
        "optimize", "optimization", "performance", "speed up", "latency", "memory leak",
        "deprecate", "redundant", "deduplicate", "modularize", "decouple",
    ],
    IssueIntent.SECURITY: [
        "security", "vulnerability", "cve", "exploit", "injection", "sanitize",
        "xss", "csrf", "sqli", "auth bypass", "credential", "leak", "secret",
        "token leak", "unauthorized", "forgery",
    ],
    IssueIntent.DOCS: [
        "doc", "docs", "documentation", "readme", "guide", "tutorial", "typo",
        "spelling", "grammar", "specification", "jsdoc", "docstring", "manual",
    ],
}

# Search strategy adjustment parameters based on intent
INTENT_STRATEGIES: dict[IssueIntent, dict[str, Any]] = {
    IssueIntent.BUG: {
        "description": "Prioritizes historical hotspots, stack trace symbols, and direct handler functions",
        "weight_adjustments": {
            "semantic": 0.35,
            "structural": 0.35,
            "topological": 0.12,
            "historical": 0.10,
            "hotspot": 0.08,
        },
        "preferred_node_types": ["function", "method", "class"],
    },
    IssueIntent.FEATURE: {
        "description": "Emphasizes semantic concepts, entrypoint routes, and interface specifications",
        "weight_adjustments": {
            "semantic": 0.50,
            "structural": 0.25,
            "topological": 0.15,
            "historical": 0.05,
            "hotspot": 0.05,
        },
        "preferred_node_types": ["route", "interface", "class", "module"],
    },
    IssueIntent.REFACTOR: {
        "description": "Focuses on high-degree centrality hotspots, structural layout, and dependency fan-in",
        "weight_adjustments": {
            "semantic": 0.25,
            "structural": 0.30,
            "topological": 0.20,
            "historical": 0.10,
            "hotspot": 0.15,
        },
        "preferred_node_types": ["module", "package", "class", "function"],
    },
    IssueIntent.SECURITY: {
        "description": "Targets authentication middleware, permission guards, session handlers, and input validation",
        "weight_adjustments": {
            "semantic": 0.45,
            "structural": 0.35,
            "topological": 0.10,
            "historical": 0.05,
            "hotspot": 0.05,
        },
        "preferred_node_types": ["function", "route", "middleware", "class"],
    },
    IssueIntent.DOCS: {
        "description": "Weights markdown documents, module docstrings, and export definitions",
        "weight_adjustments": {
            "semantic": 0.60,
            "structural": 0.25,
            "topological": 0.05,
            "historical": 0.05,
            "hotspot": 0.05,
        },
        "preferred_node_types": ["file", "module"],
    },
}


@dataclass
class ClassificationResult:
    primary_intent: IssueIntent
    confidence: float
    scores: dict[str, float]
    search_strategy: dict[str, Any]
    detected_signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "primary_intent": self.primary_intent.value,
            "confidence": round(self.confidence, 4),
            "scores": {k: round(v, 4) for k, v in self.scores.items()},
            "detected_signals": self.detected_signals,
            "search_strategy": self.search_strategy,
        }


class IssueIntentClassifier:
    """Classifies issues into Bug, Feature, Refactor, Security, or Docs intents."""

    def __init__(self) -> None:
        pass

    def classify(
        self,
        title: str,
        body: str = "",
        labels: list[str] | None = None,
        preprocessed: PreprocessedIssue | None = None,
    ) -> ClassificationResult:
        labels_list = labels or []
        detected_signals: list[str] = []

        scores: dict[IssueIntent, float] = {
            IssueIntent.BUG: 0.0,
            IssueIntent.FEATURE: 0.0,
            IssueIntent.REFACTOR: 0.0,
            IssueIntent.SECURITY: 0.0,
            IssueIntent.DOCS: 0.0,
        }

        # 1. Label Analysis (Strong Signal: +4.0 per matching label)
        for lbl in labels_list:
            clean_lbl = lbl.lower().replace("type:", "").replace("area:", "").strip()
            for intent, patterns in LABEL_PATTERNS.items():
                if any(p.search(clean_lbl) for p in patterns):
                    scores[intent] += 4.0
                    detected_signals.append(f"label:{lbl}->{intent.value}")

        # 2. Structural Evidence (from PreprocessedIssue or raw content)
        has_stack_trace = False
        has_exceptions = False
        if preprocessed:
            has_stack_trace = len(preprocessed.stack_trace_frames) > 0
            has_exceptions = len(preprocessed.exceptions) > 0
        else:
            if "traceback (most recent call last)" in body.lower() or "at " in body:
                has_stack_trace = True
            if "error:" in body.lower() or "exception:" in body.lower():
                has_exceptions = True

        if has_stack_trace:
            scores[IssueIntent.BUG] += 3.5
            detected_signals.append("structural:stack_trace")

        if has_exceptions:
            scores[IssueIntent.BUG] += 2.0
            detected_signals.append("structural:exception_line")

        # 3. Title & Body Keyword Analysis
        # Title matches carry 2.5x weight compared to body
        title_lower = title.lower()
        body_lower = (body or "").lower()

        for intent, kw_list in KEYWORD_PATTERNS.items():
            for kw in kw_list:
                kw_regex = re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE)
                if kw_regex.search(title_lower):
                    scores[intent] += 2.5
                    detected_signals.append(f"title_kw:{kw}->{intent.value}")
                elif kw_regex.search(body_lower):
                    scores[intent] += 1.0

        # Special Security Boost (Security keywords in title or CVE identifiers)
        if re.search(r"\bcve-\d{4}-\d+\b", f"{title_lower} {body_lower}"):
            scores[IssueIntent.SECURITY] += 6.0
            detected_signals.append("cve_pattern")

        # Fallback if no signals detected
        if all(score == 0.0 for score in scores.values()):
            scores[IssueIntent.FEATURE] = 1.0
            detected_signals.append("default_fallback")

        # Determine winner and normalized confidence
        sorted_intents = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        winner_intent, top_score = sorted_intents[0]
        runner_up_score = sorted_intents[1][1] if len(sorted_intents) > 1 else 0.0

        total_score = sum(scores.values())
        if total_score > 0:
            raw_confidence = top_score / total_score
            # Confidence boost if winning margin over runner-up is substantial
            margin = (top_score - runner_up_score) / max(1.0, top_score)
            confidence = min(0.99, max(0.50, raw_confidence * 0.7 + margin * 0.3))
        else:
            confidence = 0.50

        strategy = INTENT_STRATEGIES[winner_intent]

        return ClassificationResult(
            primary_intent=winner_intent,
            confidence=confidence,
            scores={k.value: v for k, v in scores.items()},
            search_strategy=strategy,
            detected_signals=detected_signals,
        )

