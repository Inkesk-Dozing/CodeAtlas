"""Issue text preprocessor for issue-to-code mapping.

Extracts high-signal structural artifacts from raw issue content:
- Explicit file paths (e.g. apps/api/auth.py, src/components/Button.tsx)
- Backticked code symbols and identifiers (`validate_token`, `UserSession`)
- HTTP API endpoints and routes (/api/v1/auth/callback)
- Python / Node.js stack trace frames (file, line number, function, exception message)
- Cleaned and normalized text suitable for dense embedding generation with conversational noise removed
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# Match markdown code fences (``` ... ```)
CODE_FENCE_RE = re.compile(r"```(?:[a-zA-Z0-9_\-]+)?\n([\s\S]*?)```", re.MULTILINE)

# Match inline backticked symbols: `identifier` or `path/to/file`
INLINE_BACKTICK_RE = re.compile(r"`([^`\n\r]+)`")

# Match common file extensions in repository structures
FILE_PATH_RE = re.compile(
    r"(?:[\w\-./\\]+[/\\launch]?[\w\-]+?\.(?:py|tsx?|jsx?|rs|go|vue|java|cpp|c|h|rb|php|sql|ya?ml|json|toml|md|css|scss|html))\b",
    re.IGNORECASE,
)

# Match HTTP API route patterns: e.g. /api/v1/auth/callback, /repos/{id}/graph
HTTP_ROUTE_RE = re.compile(
    r"(?:^|[\s\"'(`])((?:/(?:api|v[0-9]+|rest|graphql|v1|v2|v3)[\w\-/{}._]*|/[\w\-._]+/(?:[\w\-._]+/?){2,}))",
    re.MULTILINE,
)

# Python stack trace frame: File "path/to/file.py", line 123, in func_name
PYTHON_TRACE_RE = re.compile(
    r'File\s+["\']([^"\']+)["\'],\s+line\s+(\d+)(?:,\s+in\s+([A-Za-z0-9_<>]+))?',
    re.MULTILINE,
)

# Python exception line: ValueError: something went wrong (allowing leading whitespace)
PYTHON_EXCEPTION_RE = re.compile(
    r"^\s*([A-Z][A-Za-z0-9_]*(?:Error|Exception|Warning|Fault|Interrupt)):\s*(.*)$",
    re.MULTILINE,
)

# Node.js stack trace frame: at functionName (path/to/file.js:123:45) or at path/to/file.js:123:45
NODE_TRACE_RE = re.compile(
    r"^\s*at\s+(?:([A-Za-z0-9_$.<>[\] ]+?)\s+\()?([^\s():]+):(\d+)(?::(\d+))?\)?",
    re.MULTILINE,
)

# Conversational boilerplate patterns to strip for clean embedding text
BOILERPLATE_PATTERNS = [
    re.compile(r"^\s*(?:##?\s*)?(?:steps to reproduce|how to reproduce|reproduction steps|expected behavior|actual behavior|description|environment|additional context|context|steps):?", re.IGNORECASE | re.MULTILINE),
    re.compile(r"\b(?:steps to reproduce|expected behavior|actual behavior|reproduction steps)\b:?", re.IGNORECASE),
    re.compile(r"\b(?:hey team|hi all|hello|thanks in advance|please help|any idea|reproduce with the following|repro:)\b", re.IGNORECASE),
    re.compile(r"<!--[\s\S]*?-->"),  # HTML comments
    re.compile(r"^\s*[-*]\s*\[[ xX]\]", re.MULTILINE),  # Checkboxes
]


@dataclass
class StackTraceFrame:
    file_path: str
    line_number: int | None = None
    function_name: str | None = None


@dataclass
class PreprocessedIssue:
    original_title: str
    original_body: str
    cleaned_text: str
    file_paths: list[str] = field(default_factory=list)
    code_symbols: list[str] = field(default_factory=list)
    http_routes: list[str] = field(default_factory=list)
    stack_trace_frames: list[StackTraceFrame] = field(default_factory=list)
    exceptions: list[str] = field(default_factory=list)
    weighted_tokens: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_paths": self.file_paths,
            "code_symbols": self.code_symbols,
            "http_routes": self.http_routes,
            "exceptions": self.exceptions,
            "stack_trace_frames": [
                {
                    "file": f.file_path,
                    "line": f.line_number,
                    "function": f.function_name,
                }
                for f in self.stack_trace_frames
            ],
            "cleaned_text": self.cleaned_text,
            "weighted_tokens": self.weighted_tokens,
        }


class IssueTextPreprocessor:
    """Preprocesses issue markdown to isolate file paths, stack traces, code symbols, and routes."""

    def __init__(self, high_weight_multiplier: int = 3) -> None:
        self.high_weight_multiplier = high_weight_multiplier

    def preprocess(
        self,
        title: str,
        body: str = "",
        labels: list[str] | None = None,
    ) -> PreprocessedIssue:
        raw_content = f"{title}\n{body or ''}"
        labels_list = labels or []

        # 1. Extract Stack Traces & Exceptions
        stack_frames: list[StackTraceFrame] = []
        exceptions: list[str] = []

        # Python traces
        for match in PYTHON_TRACE_RE.finditer(raw_content):
            filepath = match.group(1).replace("\\", "/")
            line_no = int(match.group(2)) if match.group(2) else None
            func_name = match.group(3)
            stack_frames.append(StackTraceFrame(file_path=filepath, line_number=line_no, function_name=func_name))

        for match in PYTHON_EXCEPTION_RE.finditer(raw_content):
            exc_type = match.group(1).strip()
            exc_msg = match.group(2).strip()
            exceptions.append(f"{exc_type}: {exc_msg}" if exc_msg else exc_type)

        # Node.js traces
        for match in NODE_TRACE_RE.finditer(raw_content):
            func_name = match.group(1)
            filepath = match.group(2).replace("\\", "/")
            line_no = int(match.group(3)) if match.group(3) else None
            stack_frames.append(StackTraceFrame(file_path=filepath, line_number=line_no, function_name=func_name))

        # 2. Extract Code Symbols from Inline Backticks and Code Fences
        symbols_set: set[str] = set()
        for match in INLINE_BACKTICK_RE.finditer(raw_content):
            sym = match.group(1).strip()
            if sym and not sym.startswith("http") and len(sym) < 80:
                symbols_set.add(sym)

        # 3. Extract File Paths
        file_paths_set: set[str] = set()
        for match in FILE_PATH_RE.finditer(raw_content):
            raw_path = match.group(0).strip("`'\"(),:;").replace("\\", "/")
            # Filter obvious non-filepath false positives
            if not raw_path.startswith("http") and "/" in raw_path:
                file_paths_set.add(raw_path)
            elif "." in raw_path and not raw_path.startswith("."):
                # Standalone file e.g. auth.py, Button.tsx
                file_paths_set.add(raw_path)

        # Also add files from stack trace frames
        for frame in stack_frames:
            if not frame.file_path.startswith(("<", "http", "/usr", "/opt", "node_modules", "site-packages")):
                file_paths_set.add(frame.file_path)

        # 4. Extract HTTP API Routes
        routes_set: set[str] = set()
        for match in HTTP_ROUTE_RE.finditer(raw_content):
            route = match.group(1).strip("`'\"(),:;")
            if route.startswith("/") and len(route) > 3:
                routes_set.add(route)

        # 5. Clean text for semantic embedding
        cleaned = raw_content
        for pattern in BOILERPLATE_PATTERNS:
            cleaned = pattern.sub("", cleaned)

        # Strip markdown syntax while preserving text (keep underscore in identifiers)
        cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)  # Links [text](url) -> text
        cleaned = re.sub(r"[*~`#>]+", " ", cleaned)  # formatting characters (excluding underscore)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # Append label hints to cleaned text
        if labels_list:
            cleaned = f"{cleaned} (labels: {', '.join(labels_list)})"

        # 6. Build weighted tokens for ranking
        # Higher weights for extracted file paths, code symbols, and exception types
        weighted_tokens: list[str] = []
        for fp in file_paths_set:
            stem = fp.split("/")[-1].split(".")[0]
            weighted_tokens.extend([stem] * self.high_weight_multiplier)

        for sym in symbols_set:
            # clean identifier
            tokens = re.findall(r"[A-Za-z0-9_]+", sym)
            for tok in tokens:
                weighted_tokens.extend([tok.lower()] * self.high_weight_multiplier)

        for exc in exceptions:
            exc_class = exc.split(":")[0].strip()
            weighted_tokens.extend([exc_class.lower()] * self.high_weight_multiplier)

        return PreprocessedIssue(
            original_title=title,
            original_body=body,
            cleaned_text=cleaned,
            file_paths=sorted(file_paths_set),
            code_symbols=sorted(symbols_set),
            http_routes=sorted(routes_set),
            stack_trace_frames=stack_frames,
            exceptions=exceptions,
            weighted_tokens=weighted_tokens,
        )
