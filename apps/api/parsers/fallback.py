"""Fallback parser for generic, configuration, and unsupported file types."""

import re

from parsers.base import (
    BaseParser,
    ParsedSymbol,
    ParseResult,
    SymbolKind,
)


class FallbackParser(BaseParser):
    """Graceful fallback parser providing line, token, and basic symbol extraction."""

    def parse(self, content: str, path: str) -> ParseResult:
        result = ParseResult(loc=self._count_loc(content), path=path)
        lines = content.splitlines()

        # Extract basic key-value or definition tokens for configuration/text files
        symbols: list[ParsedSymbol] = []
        exports: list[str] = []

        for i, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith(("#", "//", "/*", "*", ";")):
                continue

            # Check key = value or key: value
            kv_match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_\.-]*)\s*[:=]\s*(.+)$", stripped)
            if kv_match:
                key = kv_match.group(1)
                val = kv_match.group(2).strip().strip("'\"")
                symbols.append(ParsedSymbol(
                    name=key,
                    kind=SymbolKind.VARIABLE,
                    line=i,
                    end_line=i,
                    signature=f"{key} = {val[:40]}",
                    metadata={"fallback": True, "raw_line": stripped[:100]},
                ))
                exports.append(key)

        result.symbols = symbols
        result.variables = symbols
        result.exports = exports
        return result
