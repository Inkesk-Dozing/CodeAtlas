from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class SymbolKind(StrEnum):
    """Standardized entity kind definitions across language AST parsers."""
    FUNCTION = "function"
    CLASS = "class"
    MODULE = "module"
    ROUTE = "route"
    COMPONENT = "component"
    MODEL = "model"
    INTERFACE = "interface"
    VARIABLE = "variable"
    HOOK = "hook"


@dataclass
class CodeNode:
    """Standardized AST code node representation for graph ingestion."""
    name: str
    kind: str
    line: int = 0
    end_line: int = 0
    path: str = ""
    signature: str = ""
    docstring: str | None = None
    is_exported: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeEdge:
    """Standardized semantic or structural relationship between code nodes."""
    source: str
    target: str
    type: str  # imports, extends, implements, routes_to, contains, calls
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedSymbol:
    name: str
    kind: str
    line: int = 0
    end_line: int = 0
    signature: str = ""
    docstring: str | None = None
    is_async: bool = False
    is_exported: bool = False
    is_static: bool = False
    visibility: str = "public"
    parent: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedImport:
    source: str
    names: list[str] = field(default_factory=list)
    is_default: bool = False
    is_namespace: bool = False
    line: int = 0
    is_internal: bool = False
    is_monorepo: bool = False
    is_third_party: bool = False


@dataclass
class ParsedRoute:
    method: str
    path: str
    handler: str = ""
    middleware: list[str] = field(default_factory=list)
    framework: str = ""
    line: int = 0
    params: list[str] = field(default_factory=list)


@dataclass
class ParseResult:
    symbols: list[ParsedSymbol] = field(default_factory=list)
    imports: list[ParsedImport] = field(default_factory=list)
    routes: list[ParsedRoute] = field(default_factory=list)
    exports: list[str] = field(default_factory=list)
    classes: list[ParsedSymbol] = field(default_factory=list)
    functions: list[ParsedSymbol] = field(default_factory=list)
    variables: list[ParsedSymbol] = field(default_factory=list)
    interfaces: list[ParsedSymbol] = field(default_factory=list)
    components: list[ParsedSymbol] = field(default_factory=list)
    hooks: list[ParsedSymbol] = field(default_factory=list)
    models: list[ParsedSymbol] = field(default_factory=list)
    loc: int = 0
    errors: list[str] = field(default_factory=list)
    path: str = ""
    _nodes: list[CodeNode] | None = None
    _edges: list[CodeEdge] | None = None

    @property
    def nodes(self) -> list[CodeNode]:
        """Convert extracted symbols to standardized CodeNodes."""
        if self._nodes is None:
            self._nodes = self.to_nodes(self.path)
        return self._nodes

    @nodes.setter
    def nodes(self, value: list[CodeNode]) -> None:
        self._nodes = value

    @property
    def edges(self) -> list[CodeEdge]:
        """Convert extracted imports and routes to standardized CodeEdges."""
        if self._edges is None:
            self._edges = self.to_edges(self.path)
        return self._edges

    @edges.setter
    def edges(self, value: list[CodeEdge]) -> None:
        self._edges = value

    def to_nodes(self, path: str = "") -> list[CodeNode]:
        """Generate standardized CodeNode representations from parsed symbols."""
        file_path = path or self.path
        nodes: list[CodeNode] = []

        # File-level module node
        if file_path:
            file_name = file_path.split("/")[-1]
            nodes.append(CodeNode(
                name=file_name,
                kind=SymbolKind.MODULE,
                line=1,
                end_line=max(1, self.loc),
                path=file_path,
                is_exported=True,
                metadata={"loc": self.loc},
            ))

        for sym in self.symbols:
            nodes.append(CodeNode(
                name=sym.name,
                kind=sym.kind,
                line=sym.line,
                end_line=sym.end_line,
                path=file_path,
                signature=sym.signature,
                docstring=sym.docstring,
                is_exported=sym.is_exported,
                metadata=sym.metadata,
            ))

        for route in self.routes:
            nodes.append(CodeNode(
                name=f"{route.method} {route.path}",
                kind=SymbolKind.ROUTE,
                line=route.line,
                end_line=route.line,
                path=file_path,
                signature=f"{route.method} {route.path} -> {route.handler}",
                is_exported=True,
                metadata={
                    "method": route.method,
                    "path": route.path,
                    "handler": route.handler,
                    "framework": route.framework,
                    "middleware": route.middleware,
                },
            ))

        return nodes

    def to_edges(self, path: str = "") -> list[CodeEdge]:
        """Generate standardized CodeEdge representations from imports and routes."""
        file_path = path or self.path
        edges: list[CodeEdge] = []

        for imp in self.imports:
            edges.append(CodeEdge(
                source=file_path,
                target=imp.source,
                type="imports",
                metadata={
                    "names": imp.names,
                    "line": imp.line,
                    "is_internal": imp.is_internal,
                    "is_monorepo": imp.is_monorepo,
                    "is_third_party": imp.is_third_party,
                },
            ))

        for cls in self.classes:
            bases = cls.metadata.get("bases") or ([cls.metadata.get("extends")] if cls.metadata.get("extends") else [])
            for base in bases:
                if base:
                    edges.append(CodeEdge(
                        source=cls.name,
                        target=base,
                        type="extends",
                        metadata={"class": cls.name, "path": file_path},
                    ))
            for impl in cls.metadata.get("implements", []):
                edges.append(CodeEdge(
                    source=cls.name,
                    target=impl,
                    type="implements",
                    metadata={"class": cls.name, "path": file_path},
                ))

        for route in self.routes:
            if route.handler:
                edges.append(CodeEdge(
                    source=f"{route.method} {route.path}",
                    target=route.handler,
                    type="routes_to",
                    metadata={"framework": route.framework, "path": file_path},
                ))

        return edges


# Standardized alias for uniform API
ParsedFile = ParseResult


class BaseParser(ABC):
    @abstractmethod
    def parse(self, content: str, path: str) -> ParseResult:
        """Parse source file content into a standardized ParseResult/ParsedFile."""
        ...

    def extract_nodes(self, content: str, path: str) -> list[CodeNode]:
        """Extract standardized code nodes from file content."""
        return self.parse(content, path).to_nodes(path)

    def extract_edges(self, content: str, path: str) -> list[CodeEdge]:
        """Extract standardized code edges from file content."""
        return self.parse(content, path).to_edges(path)

    def extract_imports(self, content: str, path: str) -> list[ParsedImport]:
        """Extract imported dependencies from file content."""
        return self.parse(content, path).imports

    def extract_exports(self, content: str, path: str) -> list[str]:
        """Extract exported symbols from file content."""
        return self.parse(content, path).exports

    @staticmethod
    def _count_loc(content: str) -> int:
        return sum(1 for line in content.splitlines() if line.strip() and not line.strip().startswith(("//", "#", "*", "/*")))
