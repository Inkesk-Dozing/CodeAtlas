from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


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


@dataclass
class ParsedRoute:
    method: str
    path: str
    handler: str = ""
    middleware: list[str] = field(default_factory=list)
    framework: str = ""
    line: int = 0


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


class BaseParser(ABC):
    @abstractmethod
    def parse(self, content: str, path: str) -> ParseResult:
        ...

    @staticmethod
    def _count_loc(content: str) -> int:
        return sum(1 for line in content.splitlines() if line.strip() and not line.strip().startswith(("//", "#", "*", "/*")))
