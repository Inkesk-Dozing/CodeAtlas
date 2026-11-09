"""Multi-language AST Parser framework and dispatch registry."""

import os

from parsers.base import (
    BaseParser,
    CodeEdge,
    CodeNode,
    ParsedFile,
    ParsedImport,
    ParsedRoute,
    ParsedSymbol,
    ParseResult,
    SymbolKind,
)
from parsers.fallback import FallbackParser
from parsers.golang import GoParser
from parsers.javascript import JavaScriptParser
from parsers.orm import PrismaParser
from parsers.python import PythonParser
from parsers.routes import JavaSpringParser
from parsers.rust import RustParser

# Direct extension to language mapping for O(1) routing
EXTENSION_MAP: dict[str, str] = {
    # Python
    ".py": "python",
    ".pyw": "python",
    ".pyi": "python",
    # JavaScript & TypeScript
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    # Go
    ".go": "go",
    # Rust
    ".rs": "rust",
    # Java / Spring
    ".java": "java",
    # Database ORM
    ".prisma": "prisma",
    # Generic / Config
    ".json": "generic",
    ".yaml": "generic",
    ".yml": "generic",
    ".toml": "generic",
    ".md": "generic",
    ".txt": "generic",
    ".sql": "generic",
    ".sh": "generic",
}


class ParserRegistry:
    """O(1) dispatch registry mapping languages and file extensions to concrete parsers."""

    def __init__(self) -> None:
        self._extension_map: dict[str, str] = dict(EXTENSION_MAP)
        self._language_parsers: dict[str, BaseParser] = {}
        self._fallback_parser = FallbackParser()
        self._init_defaults()

    def _init_defaults(self) -> None:
        # Pre-instantiate primary parsers for immediate O(1) lookup
        self._language_parsers["python"] = PythonParser()
        self._language_parsers["typescript"] = JavaScriptParser("typescript")
        self._language_parsers["javascript"] = JavaScriptParser("javascript")
        self._language_parsers["go"] = GoParser()
        self._language_parsers["rust"] = RustParser()
        self._language_parsers["java"] = JavaSpringParser()
        self._language_parsers["prisma"] = PrismaParser()
        self._language_parsers["generic"] = self._fallback_parser

    def register(self, language_or_ext: str, parser: BaseParser) -> None:
        """Register a concrete parser for a language or file extension."""
        key = language_or_ext.lower().strip()
        if key.startswith("."):
            self._extension_map[key] = key
            self._language_parsers[key] = parser
        else:
            self._language_parsers[key] = parser

    def get_parser(self, language_or_ext: str, fallback: bool = False) -> BaseParser | None:
        """O(1) parser lookup by language name or file extension."""
        if not language_or_ext:
            return self._fallback_parser if fallback else None

        key = language_or_ext.lower().strip()

        # Direct language match
        if key in self._language_parsers:
            return self._language_parsers[key]

        # Check aliases
        if key in ("golang",):
            return self._language_parsers["go"]
        if key in ("rs",):
            return self._language_parsers["rust"]
        if key in ("spring",):
            return self._language_parsers["java"]
        if key in ("schema.prisma",):
            return self._language_parsers["prisma"]

        # Check extension lookup
        ext = key if key.startswith(".") else f".{key}"
        if ext in self._extension_map:
            mapped_lang = self._extension_map[ext]
            return self._language_parsers.get(mapped_lang, self._fallback_parser if fallback else None)

        return self._fallback_parser if fallback else None

    def get_parser_for_file(self, file_path: str, fallback: bool = True) -> BaseParser | None:
        """O(1) file extension dispatcher routing file paths to the appropriate parser."""
        _, ext = os.path.splitext(file_path.lower())
        if ext in self._extension_map:
            lang = self._extension_map[ext]
            return self._language_parsers.get(lang, self._fallback_parser if fallback else None)
        return self._fallback_parser if fallback else None


_default_registry = ParserRegistry()


def get_parser(language: str) -> BaseParser | None:
    """Retrieve concrete parser by language or extension (backward compatible)."""
    return _default_registry.get_parser(language, fallback=False)


def get_parser_for_file(file_path: str, fallback: bool = True) -> BaseParser:
    """O(1) file extension dispatcher routing file paths to the appropriate parser with graceful fallback."""
    parser = _default_registry.get_parser_for_file(file_path, fallback=fallback)
    return parser if parser is not None else _default_registry._fallback_parser


def get_fallback_parser() -> BaseParser:
    """Retrieve default fallback parser for unsupported file types."""
    return _default_registry._fallback_parser


__all__ = [
    "EXTENSION_MAP",
    "BaseParser",
    "CodeEdge",
    "CodeNode",
    "FallbackParser",
    "GoParser",
    "JavaSpringParser",
    "ParseResult",
    "ParsedFile",
    "ParsedImport",
    "ParsedRoute",
    "ParsedSymbol",
    "ParserRegistry",
    "PrismaParser",
    "RustParser",
    "SymbolKind",
    "get_fallback_parser",
    "get_parser",
    "get_parser_for_file",
]
