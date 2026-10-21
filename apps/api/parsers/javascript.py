import re

from parsers.base import (
    BaseParser,
    ParsedImport,
    ParsedRoute,
    ParsedSymbol,
    ParseResult,
)

IMPORT_PATTERNS = [
    re.compile(
        r"import\s+(?:(\w+)\s*,\s*)?(?:\{([^}]*)\}|\*\s+as\s+(\w+)|(\w+))?\s*from\s+['\"]([^'\"]+)['\"]"
    ),
    re.compile(r"import\s+['\"]([^'\"]+)['\"]"),
    re.compile(r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"),
]

EXPORT_PATTERNS = [
    re.compile(r"export\s+(?:default\s+)?(?:async\s+)?(?:function|class|const|let|var|interface|type|enum)\s+(\w+)"),
    re.compile(r"export\s+\{([^}]*)\}"),
]

FUNCTION_PATTERNS = [
    re.compile(r"(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*(\w+)\s*\("),
    re.compile(r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|\w+)\s*=>"),
]

CLASS_PATTERNS = [
    re.compile(
        r"(?:export\s+)?(?:default\s+)?(?:abstract\s+)?class\s+(\w+)"
        r"(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w,\s]+))?"
    ),
]

INTERFACE_PATTERNS = [
    re.compile(r"(?:export\s+)?interface\s+(\w+)"),
    re.compile(r"(?:export\s+)?type\s+(\w+)\s*="),
]

ROUTE_PATTERNS = [
    re.compile(r"(?:app|router)\.(get|post|put|delete|patch|all)\s*\(\s*['\"]([^'\"]+)['\"]\s*(?:,\s*([^,)]+))?"),
    re.compile(r"@(Get|Post|Put|Delete|Patch)\s*\(\s*['\"]([^'\"]*)['\"]\s*\)"),
    re.compile(r"@(Controller)\s*\(\s*['\"]([^'\"]*)['\"]\s*\)"),
]

COMPONENT_PATTERNS = [
    re.compile(r"(?:export\s+)?(?:default\s+)?(?:function)\s+([A-Z]\w*)\s*\("),
    re.compile(r"(?:export\s+)?(?:const|let)\s+([A-Z]\w*)\s*=\s*(?:React\.memo\s*\()?\s*(?:async\s+)?(?:\([^)]*\)|\w+)\s*=>"),
    re.compile(r"(?:export\s+)?(?:default\s+)?class\s+([A-Z]\w*)\s+extends\s+(?:React\.)?(?:Pure)?Component"),
]

HOOK_PATTERNS = [
    re.compile(r"(?:export\s+)?(?:const|function)\s+(use[A-Z]\w*)"),
]

DECORATOR_PATTERNS = [
    re.compile(r"@(\w+)"),
]


class JavaScriptParser(BaseParser):
    def __init__(self, language: str = "typescript"):
        self.language = language

    def parse(self, content: str, path: str) -> ParseResult:
        result = ParseResult(loc=self._count_loc(content))
        lines = content.splitlines()

        result.imports = self._extract_imports(content, lines)
        result.exports = self._extract_exports(content)
        result.functions = self._extract_functions(content, lines)
        result.classes = self._extract_classes(content, lines)
        result.interfaces = self._extract_interfaces(content, lines)
        result.routes = self._extract_routes(content, lines)
        result.components = self._extract_components(content, lines)
        result.hooks = self._extract_hooks(content)
        result.models = self._extract_models(content, lines)

        result.symbols = (
            result.functions + result.classes + result.interfaces
            + result.components + result.hooks + result.models
        )

        return result

    def _extract_imports(self, content: str, lines: list[str]) -> list[ParsedImport]:
        imports = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            for pattern in IMPORT_PATTERNS:
                match = pattern.search(stripped)
                if match:
                    groups = match.groups()
                    if len(groups) >= 5 and groups[4]:
                        names = []
                        if groups[0]:
                            names.append(groups[0])
                        if groups[1]:
                            names.extend([n.strip().split(" as ")[0] for n in groups[1].split(",") if n.strip()])
                        if groups[2]:
                            names.append(groups[2])
                        if groups[3]:
                            names.append(groups[3])
                        imports.append(ParsedImport(
                            source=groups[4], names=names, line=i + 1,
                            is_default=bool(groups[0] or groups[3]),
                            is_namespace=bool(groups[2]),
                        ))
                    elif groups[0] and not groups[1]:
                        imports.append(ParsedImport(source=groups[0], line=i + 1))
                    break
        return imports

    def _extract_exports(self, content: str) -> list[str]:
        exports = []
        for pattern in EXPORT_PATTERNS:
            for match in pattern.finditer(content):
                if match.group(1):
                    exports.extend(
                        n.strip().split(" as ")[0].strip()
                        for n in match.group(1).split(",")
                        if n.strip()
                    )
        return list(set(exports))

    def _extract_functions(self, content: str, lines: list[str]) -> list[ParsedSymbol]:
        functions = []
        for pattern in FUNCTION_PATTERNS:
            for match in pattern.finditer(content):
                name = match.group(1)
                line_num = content[:match.start()].count("\n") + 1
                is_async = "async" in content[max(0, match.start()-30):match.start()]
                is_exported = "export" in content[max(0, match.start()-30):match.start()]

                end_line = self._find_block_end(lines, line_num - 1)
                sig_match = re.search(r"\(([^)]*)\)", content[match.start():match.start() + 500])
                signature = f"{name}({sig_match.group(1) if sig_match else ''})"

                functions.append(ParsedSymbol(
                    name=name,
                    kind="function",
                    line=line_num,
                    end_line=end_line,
                    signature=signature,
                    is_async=is_async,
                    is_exported=is_exported,
                ))
        return functions

    def _extract_classes(self, content: str, lines: list[str]) -> list[ParsedSymbol]:
        classes = []
        for pattern in CLASS_PATTERNS:
            for match in pattern.finditer(content):
                name = match.group(1)
                line_num = content[:match.start()].count("\n") + 1
                end_line = self._find_block_end(lines, line_num - 1)

                block = "\n".join(lines[line_num - 1:end_line])
                decorators = re.findall(r"@(\w+)", block[:200])

                methods = []
                for m in re.finditer(
                    r"(?:public|private|protected|static|async|\s)*\s+(\w+)\s*\([^)]*\)\s*(?::\s*[\w<>\[\]| ]+)?\s*\{",
                    block,
                ):
                    m_name = m.group(1)
                    if m_name in ("if", "for", "while", "switch", "catch", "constructor", "return"):
                        if m_name == "constructor":
                            methods.append(m_name)
                        continue
                    methods.append(m_name)

                is_exported = "export" in content[max(0, match.start()-30):match.start()]

                classes.append(ParsedSymbol(
                    name=name,
                    kind="class",
                    line=line_num,
                    end_line=end_line,
                    is_exported=is_exported,
                    metadata={
                        "extends": match.group(2),
                        "implements": [i.strip() for i in (match.group(3) or "").split(",") if i.strip()],
                        "decorators": decorators,
                        "methods": methods,
                        "is_service": any(d in decorators for d in ("Injectable", "Service", "Component")),
                    },
                ))
        return classes

    def _extract_interfaces(self, content: str, lines: list[str]) -> list[ParsedSymbol]:
        interfaces = []
        for pattern in INTERFACE_PATTERNS:
            for match in pattern.finditer(content):
                name = match.group(1)
                line_num = content[:match.start()].count("\n") + 1
                interfaces.append(ParsedSymbol(
                    name=name,
                    kind="interface",
                    line=line_num,
                    is_exported="export" in content[max(0, match.start()-20):match.start()],
                ))
        return interfaces

    def _extract_routes(self, content: str, lines: list[str]) -> list[ParsedRoute]:
        routes = []
        framework = self._detect_framework(content)

        for pattern in ROUTE_PATTERNS:
            for match in pattern.finditer(content):
                if match.group(1).lower() in ("get", "post", "put", "delete", "patch", "all"):
                    method = match.group(1).upper()
                    path = match.group(2)
                    handler = match.group(3).strip() if match.group(3) else ""
                    line_num = content[:match.start()].count("\n") + 1

                    middleware = []
                    for mw in ("authenticate", "authorize", "validate", "rateLimit", "cors"):
                        if mw in content[max(0, match.start()-200):match.start() + 200]:
                            middleware.append(mw)

                    routes.append(ParsedRoute(
                        method=method,
                        path=path,
                        handler=handler,
                        middleware=middleware,
                        framework=framework,
                        line=line_num,
                    ))
        return routes

    def _extract_components(self, content: str, lines: list[str]) -> list[ParsedSymbol]:
        components = []
        for pattern in COMPONENT_PATTERNS:
            for match in pattern.finditer(content):
                name = match.group(1)
                line_num = content[:match.start()].count("\n") + 1
                end_line = self._find_block_end(lines, line_num - 1)
                block = "\n".join(lines[line_num - 1:end_line])

                hooks = re.findall(r"\b(use[A-Z]\w*)\s*\(", block)
                props_match = re.search(r"\(\s*\{([^}]*)\}", block)
                props = []
                if props_match:
                    props = [p.strip().split(":")[0].strip() for p in props_match.group(1).split(",") if p.strip()]

                renders = re.findall(r"<([A-Z]\w*)", block)

                components.append(ParsedSymbol(
                    name=name,
                    kind="component",
                    line=line_num,
                    end_line=end_line,
                    is_exported="export" in content[max(0, match.start()-30):match.start()],
                    metadata={
                        "hooks_used": list(set(hooks)),
                        "props": props,
                        "renders": list(set(renders))[:10],
                    },
                ))
        return components

    def _extract_hooks(self, content: str) -> list[ParsedSymbol]:
        hooks = []
        for pattern in HOOK_PATTERNS:
            for match in pattern.finditer(content):
                name = match.group(1)
                line_num = content[:match.start()].count("\n") + 1
                hooks.append(ParsedSymbol(
                    name=name,
                    kind="hook",
                    line=line_num,
                    is_exported="export" in content[max(0, match.start()-20):match.start()],
                ))
        return hooks

    def _extract_models(self, content: str, lines: list[str]) -> list[ParsedSymbol]:
        models = []

        prisma_match = re.finditer(r"model\s+(\w+)\s*\{", content)
        for match in prisma_match:
            name = match.group(1)
            line_num = content[:match.start()].count("\n") + 1
            models.append(ParsedSymbol(name=name, kind="model", line=line_num, metadata={"orm": "prisma"}))

        sqlalchemy_match = re.finditer(r"class\s+(\w+)\s*\([^)]*Base[^)]*\)", content)
        for match in sqlalchemy_match:
            name = match.group(1)
            line_num = content[:match.start()].count("\n") + 1
            models.append(ParsedSymbol(name=name, kind="model", line=line_num, metadata={"orm": "sqlalchemy"}))

        return models

    def _detect_framework(self, content: str) -> str:
        if "fastify" in content or "Fastify" in content:
            return "fastify"
        if "express" in content or "Express" in content:
            return "express"
        if "@Controller" in content or "@Get" in content:
            return "nestjs"
        if "next/router" in content or "NextResponse" in content:
            return "nextjs"
        if "Hono" in content:
            return "hono"
        return "unknown"

    @staticmethod
    def _find_block_end(lines: list[str], start_idx: int) -> int:
        depth = 0
        opened = False
        for i in range(start_idx, min(start_idx + 500, len(lines))):
            depth += lines[i].count("{") - lines[i].count("}")
            if "{" in lines[i]:
                opened = True
            if opened and depth <= 0:
                return i + 1
        return min(start_idx + 50, len(lines))
