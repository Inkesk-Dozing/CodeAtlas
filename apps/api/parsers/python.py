import re

from parsers.base import (
    BaseParser,
    ParsedImport,
    ParsedRoute,
    ParsedSymbol,
    ParseResult,
)

IMPORT_PATTERNS = [
    re.compile(r"^from\s+([\w.]+)\s+import\s+\(?\s*(.*?)\s*\)?\s*$", re.MULTILINE),
    re.compile(r"^import\s+([\w.]+)(?:\s+as\s+\w+)?\s*$", re.MULTILINE),
]

FUNCTION_PATTERNS = [
    re.compile(r"(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\)", re.MULTILINE),
]

CLASS_PATTERNS = [
    re.compile(r"(?:@(\w+(?:\([^)]*\))?)\s*\n\s*)*class\s+(\w+)\s*(?:\(([^)]*)\))?:", re.MULTILINE),
]

ROUTE_PATTERNS = [
    re.compile(r"@(?:app|router|api)\.(get|post|put|delete|patch|route)\s*\(\s*['\"]([^'\"]+)['\"]"),
    re.compile(r"@app\.route\s*\(\s*['\"]([^'\"]+)['\"]"),
    re.compile(r"path\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*(\w+)"),
]

MODEL_PATTERNS = [
    re.compile(r"class\s+(\w+)\s*\(\s*(?:models\.Model|Model|Base|db\.Model)\s*\)"),
    re.compile(r"^model\s+(\w+)", re.MULTILINE),
]

DECORATOR_PATTERNS = [
    re.compile(r"@(\w+)"),
]


class PythonParser(BaseParser):
    def parse(self, content: str, path: str) -> ParseResult:
        result = ParseResult(loc=self._count_loc(content))
        lines = content.splitlines()

        result.imports = self._extract_imports(content)
        result.functions = self._extract_functions(content, lines)
        result.classes = self._extract_classes(content, lines)
        result.routes = self._extract_routes(content, lines)
        result.models = self._extract_models(content, lines)
        result.exports = [s.name for s in result.classes + result.functions if not s.name.startswith("_")]

        result.symbols = result.functions + result.classes + result.models

        return result

    def _extract_imports(self, content: str) -> list[ParsedImport]:
        imports = []
        from_pattern, plain_pattern = IMPORT_PATTERNS

        for match in from_pattern.finditer(content):
            names = []
            for part in (match.group(2) or "").split(","):
                part = part.strip().strip("()")
                if part:
                    if " as " in part:
                        part = part.split(" as ")[0].strip()
                    names.append(part)
            imports.append(ParsedImport(source=match.group(1), names=names))

        for match in plain_pattern.finditer(content):
            imports.append(ParsedImport(source=match.group(1)))

        return imports

    def _extract_functions(self, content: str, lines: list[str]) -> list[ParsedSymbol]:
        functions = []
        for pattern in FUNCTION_PATTERNS:
            for match in pattern.finditer(content):
                name = match.group(1)
                if name.startswith("_") and name != "__init__":
                    continue

                line_num = content[:match.start()].count("\n") + 1
                params_str = match.group(2)
                params = [p.strip().split(":")[0].split("=")[0].strip() for p in params_str.split(",") if p.strip()]

                docstring = self._extract_docstring(lines, line_num - 1)
                is_async = "async def" in content[match.start():match.start() + 20]

                decorator_block = self._get_decorators(content, match.start())
                is_route = any(d.startswith(("app.", "router.", "route")) for d in decorator_block)

                functions.append(ParsedSymbol(
                    name=name,
                    kind="function",
                    line=line_num,
                    signature=f"{name}({', '.join(params)})",
                    docstring=docstring,
                    is_async=is_async,
                    metadata={"decorators": decorator_block, "params": params, "is_route": is_route},
                ))
        return functions

    def _extract_classes(self, content: str, lines: list[str]) -> list[ParsedSymbol]:
        classes = []
        for pattern in CLASS_PATTERNS:
            for match in pattern.finditer(content):
                name = match.group(2)
                bases = match.group(3) or ""

                line_num = content[:match.start()].count("\n") + 1
                all_decorators = self._get_decorators(content, match.start())

                end_line = self._find_class_end(lines, line_num - 1)
                block = "\n".join(lines[line_num - 1:end_line])

                methods = []
                for m in re.finditer(r"(?:async\s+)?def\s+(\w+)\s*\(", block):
                    m_name = m.group(1)
                    if not m_name.startswith("__") or m_name == "__init__":
                        methods.append(m_name)

                docstring = self._extract_docstring(lines, line_num - 1)

                is_service = any(
                    d.split("(")[0] in ("service", "Service", "injectable", "component", "Component", "router", "Router", "APIRouter")
                    for d in all_decorators
                )

                classes.append(ParsedSymbol(
                    name=name,
                    kind="class",
                    line=line_num,
                    end_line=end_line,
                    docstring=docstring,
                    is_exported=not name.startswith("_"),
                    metadata={
                        "bases": [b.strip() for b in bases.split(",") if b.strip()],
                        "decorators": all_decorators,
                        "methods": methods,
                        "is_service": is_service,
                    },
                ))
        return classes

    def _extract_routes(self, content: str, lines: list[str]) -> list[ParsedRoute]:
        routes = []
        framework = self._detect_framework(content)

        for pattern in ROUTE_PATTERNS:
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count("\n") + 1

                if match.group(1).upper() in ("GET", "POST", "PUT", "DELETE", "PATCH", "ROUTE"):
                    method = match.group(1).upper()
                    path = match.group(2)
                else:
                    method = "GET"
                    path = match.group(1)

                handler = ""
                after_route = content[match.end():match.end() + 200]
                handler_match = re.search(r"(?:def\s+(\w+)|(\w+))", after_route)
                if handler_match:
                    handler = handler_match.group(1) or handler_match.group(2)

                routes.append(ParsedRoute(
                    method=method,
                    path=path,
                    handler=handler,
                    framework=framework,
                    line=line_num,
                ))
        return routes

    def _extract_models(self, content: str, lines: list[str]) -> list[ParsedSymbol]:
        models = []
        for pattern in MODEL_PATTERNS:
            for match in pattern.finditer(content):
                name = match.group(1)
                line_num = content[:match.start()].count("\n") + 1
                end_line = self._find_class_end(lines, line_num - 1)
                block = "\n".join(lines[line_num - 1:end_line])

                fields = []
                for f in re.finditer(r"(\w+)\s*=\s*(?:db\.Column|Column|Mapped|Mapped\[)", block):
                    fields.append(f.group(1))

                models.append(ParsedSymbol(
                    name=name,
                    kind="model",
                    line=line_num,
                    end_line=end_line,
                    metadata={"fields": fields},
                ))
        return models

    def _detect_framework(self, content: str) -> str:
        if "FastAPI" in content or "fastapi" in content:
            return "fastapi"
        if "flask" in content.lower() or "Flask" in content:
            return "flask"
        if "django" in content.lower() or "Django" in content:
            return "django"
        if "sanic" in content.lower():
            return "sanic"
        return "unknown"

    @staticmethod
    def _extract_docstring(lines: list[str], start_idx: int) -> str | None:
        for i in range(start_idx + 1, min(start_idx + 5, len(lines))):
            stripped = lines[i].strip()
            if stripped.startswith(('"""', "'''")):
                doc = stripped.strip("\"'")
                if doc:
                    return doc
                for j in range(i + 1, min(i + 20, len(lines))):
                    if lines[j].strip().startswith(('"""', "'''")):
                        return "\n".join(lines[i + 1 : j]).strip()
                    return "\n".join(lines[i + 1 : j]).strip()
        return None

    @staticmethod
    def _get_decorators(content: str, match_start: int) -> list[str]:
        before = content[:match_start]
        lines_before = before.split("\n")[-10:]
        decorators = []
        for line in reversed(lines_before):
            stripped = line.strip()
            if stripped.startswith("@"):
                decorators.append(stripped[1:])
            elif stripped and not stripped.startswith("#"):
                break
        return list(reversed(decorators))

    @staticmethod
    def _find_class_end(lines: list[str], start_idx: int) -> int:
        for i in range(start_idx + 1, min(start_idx + 500, len(lines))):
            if lines[i] and not lines[i][0].isspace() and not lines[i].strip().startswith("@"):
                return i
        return min(start_idx + 100, len(lines))
