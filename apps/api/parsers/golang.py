import re

from parsers.base import (
    BaseParser,
    ParsedImport,
    ParsedRoute,
    ParsedSymbol,
    ParseResult,
)

# Package declaration: package main
PACKAGE_PATTERN = re.compile(r"^\s*package\s+([a-zA-Z0-9_]+)", re.MULTILINE)

# Single-line or multi-line imports:
# import "fmt"
# import (
#     "net/http"
#     gin "github.com/gin-gonic/gin"
# )
IMPORT_SINGLE_PATTERN = re.compile(
    r'^\s*import\s+(?:([a-zA-Z0-9_]+)\s+)?["\']([^"\']+)["\']',
    re.MULTILINE,
)
IMPORT_BLOCK_PATTERN = re.compile(
    r'^\s*import\s*\(\s*([\s\S]*?)\s*\)',
    re.MULTILINE,
)
IMPORT_ITEM_PATTERN = re.compile(
    r'(?:([a-zA-Z0-9_]+|\.)\s+)?["\']([^"\']+)["\']'
)

# Structs: type User struct { ... }
STRUCT_PATTERN = re.compile(
    r"^\s*type\s+([a-zA-Z0-9_]+)\s+struct\s*\{([\s\S]*?)\}",
    re.MULTILINE,
)

# Interfaces: type Reader interface { ... }
INTERFACE_PATTERN = re.compile(
    r"^\s*type\s+([a-zA-Z0-9_]+)\s+interface\s*\{([\s\S]*?)\}",
    re.MULTILINE,
)

# Functions & Methods:
# Package-level: func DoSomething(x int) (string, error) { ... }
# Method receiver: func (s *Service) Do(ctx context.Context) error { ... }
# Value receiver: func (s Service) Name() string { ... }
METHOD_PATTERN = re.compile(
    r"^\s*func\s*\(\s*(?:([a-zA-Z0-9_]+)\s+)?(\*?\s*[a-zA-Z0-9_]+)\s*\)\s*([a-zA-Z0-9_]+)\s*\(([^)]*)\)\s*(.*?)\s*\{",
    re.MULTILINE,
)
FUNCTION_PATTERN = re.compile(
    r"^\s*func\s+([a-zA-Z0-9_]+)\s*\(([^)]*)\)\s*(.*?)\s*\{",
    re.MULTILINE,
)

# HTTP Route patterns in Go (Gin, Echo, Chi, standard net/http, Fiber)
# Gin/Echo: r.GET("/api/v1/users", handler), router.POST("/items", h)
# Chi: r.Get("/users", h), r.Post("/users", h)
# net/http: http.HandleFunc("/path", h), mux.HandleFunc("/path", h)
ROUTE_PATTERNS = [
    re.compile(
        r"""(?:[a-zA-Z0-9_]+)\.(GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD|Get|Post|Put|Delete|Patch|Options|Head)\s*\(\s*["']([^"']+)["']\s*,\s*([a-zA-Z0-9_.]+)?(?:\s*,|\s*\))""",
        re.MULTILINE,
    ),
    re.compile(
        r"""(?:http|mux|[a-zA-Z0-9_]+)\.HandleFunc\s*\(\s*["']([^"']+)["']\s*,\s*([a-zA-Z0-9_.]+)?(?:\s*,|\s*\))""",
        re.MULTILINE,
    ),
]


class GoParser(BaseParser):
    def parse(self, content: str, path: str) -> ParseResult:
        result = ParseResult(loc=self._count_loc(content))
        lines = content.splitlines()

        package_name = self._extract_package(content)
        result.imports = self._extract_imports(content, lines)
        result.classes = self._extract_structs(content, lines, package_name)
        result.interfaces = self._extract_interfaces(content, lines, package_name)
        result.functions = self._extract_functions(content, lines, package_name)
        result.routes = self._extract_routes(content, lines)

        # In Go, capitalized identifiers are exported
        result.exports = [
            s.name for s in (result.classes + result.interfaces + result.functions)
            if s.is_exported
        ]

        result.symbols = result.classes + result.interfaces + result.functions
        return result

    def _extract_package(self, content: str) -> str:
        match = PACKAGE_PATTERN.search(content)
        return match.group(1) if match else "main"

    def _extract_imports(self, content: str, lines: list[str]) -> list[ParsedImport]:
        imports: list[ParsedImport] = []

        # Single imports: import "fmt" or import alias "path"
        for match in IMPORT_SINGLE_PATTERN.finditer(content):
            alias = match.group(1) or ""
            pkg_path = match.group(2)
            line_no = content[: match.start()].count("\n") + 1
            imports.append(
                ParsedImport(
                    source=pkg_path,
                    names=[alias] if alias else [],
                    line=line_no,
                )
            )

        # Block imports: import ( ... )
        for block_match in IMPORT_BLOCK_PATTERN.finditer(content):
            block_body = block_match.group(1)
            block_start = block_match.start(1)
            for item in IMPORT_ITEM_PATTERN.finditer(block_body):
                alias = item.group(1) or ""
                pkg_path = item.group(2)
                line_no = content[: block_start + item.start()].count("\n") + 1
                imports.append(
                    ParsedImport(
                        source=pkg_path,
                        names=[alias] if alias else [],
                        line=line_no,
                    )
                )

        return imports

    def _extract_structs(self, content: str, lines: list[str], package_name: str) -> list[ParsedSymbol]:
        structs: list[ParsedSymbol] = []
        for match in STRUCT_PATTERN.finditer(content):
            name = match.group(1)
            body = match.group(2)
            line_no = content[: match.start()].count("\n") + 1
            end_line = content[: match.end()].count("\n") + 1

            # Detect embedded structs and fields
            fields = []
            embedded = []
            for raw_line in body.splitlines():
                field_line = raw_line.strip()
                if not field_line or field_line.startswith("//"):
                    continue
                parts = field_line.split()
                if len(parts) == 1:
                    embedded.append(parts[0].lstrip("*"))
                elif len(parts) >= 2:
                    fields.append(parts[0])

            is_exported = name[0].isupper() if name else False
            structs.append(
                ParsedSymbol(
                    name=name,
                    kind="struct",
                    line=line_no,
                    end_line=end_line,
                    signature=f"type {name} struct",
                    is_exported=is_exported,
                    visibility="public" if is_exported else "private",
                    parent=package_name,
                    metadata={
                        "package": package_name,
                        "fields": fields,
                        "embedded": embedded,
                    },
                )
            )
        return structs

    def _extract_interfaces(self, content: str, lines: list[str], package_name: str) -> list[ParsedSymbol]:
        interfaces: list[ParsedSymbol] = []
        for match in INTERFACE_PATTERN.finditer(content):
            name = match.group(1)
            body = match.group(2)
            line_no = content[: match.start()].count("\n") + 1
            end_line = content[: match.end()].count("\n") + 1

            method_signatures = []
            for raw_line in body.splitlines():
                line = raw_line.strip()
                if line and not line.startswith("//"):
                    method_signatures.append(line)

            is_exported = name[0].isupper() if name else False
            interfaces.append(
                ParsedSymbol(
                    name=name,
                    kind="interface",
                    line=line_no,
                    end_line=end_line,
                    signature=f"type {name} interface",
                    is_exported=is_exported,
                    visibility="public" if is_exported else "private",
                    parent=package_name,
                    metadata={
                        "package": package_name,
                        "methods": method_signatures,
                    },
                )
            )
        return interfaces

    def _extract_functions(self, content: str, lines: list[str], package_name: str) -> list[ParsedSymbol]:
        functions: list[ParsedSymbol] = []

        # 1. Receiver Methods: func (s *Service) Do(ctx context.Context) error
        method_spans: list[tuple[int, int]] = []
        for match in METHOD_PATTERN.finditer(content):
            method_spans.append((match.start(), match.end()))
            _receiver_var = match.group(1) or ""
            receiver_type = match.group(2).strip().replace(" ", "").lstrip("*")
            method_name = match.group(3)
            params = match.group(4).strip()
            returns = match.group(5).strip()

            line_no = content[: match.start()].count("\n") + 1
            end_line = self._find_closing_brace_line(content, match.end() - 1, line_no)

            is_exported = method_name[0].isupper() if method_name else False
            signature = f"func ({match.group(2).strip()}) {method_name}({params}) {returns}".strip()

            functions.append(
                ParsedSymbol(
                    name=method_name,
                    kind="method",
                    line=line_no,
                    end_line=end_line,
                    signature=signature,
                    is_exported=is_exported,
                    visibility="public" if is_exported else "private",
                    parent=receiver_type,
                    metadata={
                        "package": package_name,
                        "receiver": receiver_type,
                        "receiver_type": match.group(2).strip(),
                        "params": params,
                        "returns": returns,
                    },
                )
            )

        # 2. Package-level functions: func DoSomething(...)
        for match in FUNCTION_PATTERN.finditer(content):
            start = match.start()
            # If this is inside or immediately matching a receiver method, skip
            if any(ms <= start <= me for ms, me in method_spans):
                continue

            fn_name = match.group(1)
            params = match.group(2).strip()
            returns = match.group(3).strip()

            line_no = content[: match.start()].count("\n") + 1
            end_line = self._find_closing_brace_line(content, match.end() - 1, line_no)

            is_exported = fn_name[0].isupper() if fn_name else False
            signature = f"func {fn_name}({params}) {returns}".strip()

            functions.append(
                ParsedSymbol(
                    name=fn_name,
                    kind="function",
                    line=line_no,
                    end_line=end_line,
                    signature=signature,
                    is_exported=is_exported,
                    visibility="public" if is_exported else "private",
                    parent=package_name,
                    metadata={
                        "package": package_name,
                        "params": params,
                        "returns": returns,
                    },
                )
            )

        return functions

    def _extract_routes(self, content: str, lines: list[str]) -> list[ParsedRoute]:
        routes: list[ParsedRoute] = []
        for pattern in ROUTE_PATTERNS:
            for match in pattern.finditer(content):
                line_no = content[: match.start()].count("\n") + 1
                groups = match.groups()
                if len(groups) == 3:
                    method = groups[0].upper()
                    path = groups[1]
                    handler = groups[2] or ""
                    framework = "gin/echo"
                else:
                    method = "ALL"
                    path = groups[0]
                    handler = groups[1] or ""
                    framework = "net/http"

                routes.append(
                    ParsedRoute(
                        method=method,
                        path=path,
                        handler=handler,
                        framework=framework,
                        line=line_no,
                    )
                )
        return routes

    def _find_closing_brace_line(self, content: str, open_brace_idx: int, fallback_line: int) -> int:
        depth = 0
        in_string = False
        in_char = False
        escape = False

        for idx in range(open_brace_idx, len(content)):
            char = content[idx]

            if escape:
                escape = False
                continue

            if char == "\\":
                escape = True
                continue

            if char == '"' and not in_char:
                in_string = not in_string
                continue

            if char == "'" and not in_string:
                in_char = not in_char
                continue

            if in_string or in_char:
                continue

            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return content[:idx].count("\n") + 1

        return fallback_line

