"""Tree-sitter native Python AST parser with fallback to regex extraction."""

import logging
import re
from typing import Any

from parsers.base import (
    BaseParser,
    ParsedImport,
    ParsedRoute,
    ParsedSymbol,
    ParseResult,
)
from parsers.orm import PythonORMParser

logger = logging.getLogger(__name__)

# Try loading tree-sitter Python grammar
_TREE_SITTER_AVAILABLE = False
_PY_LANGUAGE = None

try:
    import tree_sitter_python
    from tree_sitter import Language, Parser

    _PY_LANGUAGE = Language(tree_sitter_python.language())
    _TREE_SITTER_AVAILABLE = True
except Exception as e:
    logger.debug(f"Tree-sitter Python grammar unavailable, using regex fallback: {e}")
    _TREE_SITTER_AVAILABLE = False


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


class PythonParser(BaseParser):
    def __init__(self) -> None:
        self.use_native = _TREE_SITTER_AVAILABLE
        self._ts_parser: Any = None
        if self.use_native and _PY_LANGUAGE is not None:
            try:
                self._ts_parser = Parser(_PY_LANGUAGE)
            except Exception:
                self.use_native = False

    def parse(self, content: str, path: str) -> ParseResult:
        if self.use_native and self._ts_parser is not None:
            try:
                return self._parse_tree_sitter(content, path)
            except Exception as e:
                logger.warning(f"Tree-sitter parse failed for {path}, falling back to regex: {e}")
                return self._parse_regex(content, path)
        return self._parse_regex(content, path)

    # ----------------------------------------------------------------------
    # Tree-sitter Native Parser
    # ----------------------------------------------------------------------

    def _parse_tree_sitter(self, content: str, path: str) -> ParseResult:
        result = ParseResult(loc=self._count_loc(content))
        lines = content.splitlines()
        content_bytes = content.encode("utf-8")
        tree = self._ts_parser.parse(content_bytes)
        root = tree.root_node

        framework = self._detect_framework(content)
        classes: list[ParsedSymbol] = []
        functions: list[ParsedSymbol] = []
        routes: list[ParsedRoute] = []
        imports: list[ParsedImport] = []
        models: list[ParsedSymbol] = []

        # Recursively traverse top-level statements
        self._traverse_node(
            root,
            lines,
            framework,
            classes,
            functions,
            routes,
            imports,
            models,
            parent_class=None,
        )

        result.imports = imports
        result.functions = functions
        result.classes = classes
        result.routes = routes
        result.models = models
        result.exports = [s.name for s in result.classes + result.functions if not s.name.startswith("_")]
        result.symbols = result.functions + result.classes + result.models

        return result

    def _traverse_node(
        self,
        node: Any,
        lines: list[str],
        framework: str,
        classes: list[ParsedSymbol],
        functions: list[ParsedSymbol],
        routes: list[ParsedRoute],
        imports: list[ParsedImport],
        models: list[ParsedSymbol],
        parent_class: str | None = None,
    ) -> None:
        for child in node.children:
            ntype = child.type

            if ntype in ("import_statement", "import_from_statement"):
                self._handle_import_node(child, imports)

            elif ntype == "function_definition":
                self._handle_function_node(child, lines, framework, functions, routes, decorators=[], parent_class=parent_class)

            elif ntype == "decorated_definition":
                self._handle_decorated_node(child, lines, framework, classes, functions, routes, models, parent_class=parent_class)

            elif ntype == "class_definition":
                self._handle_class_node(child, lines, framework, classes, functions, routes, models, decorators=[])

            elif ntype == "expression_statement":
                # Check for django path(...) route definitions
                self._check_expression_route(child, framework, routes)

    def _handle_import_node(self, node: Any, imports: list[ParsedImport]) -> None:
        line_num = node.start_point[0] + 1
        if node.type == "import_statement":
            # e.g. import os, sys as s
            for child in node.children:
                if child.type == "dotted_name":
                    imports.append(ParsedImport(source=child.text.decode("utf-8"), line=line_num))
                elif child.type == "aliased_import":
                    orig = child.child_by_field_name("name")
                    if orig:
                        imports.append(ParsedImport(source=orig.text.decode("utf-8"), line=line_num))
        elif node.type == "import_from_statement":
            # e.g. from fastapi import APIRouter, Depends as dep
            module_node = node.child_by_field_name("module_name")
            if not module_node:
                # Fallback to finding dotted_name or relative_import before 'import'
                for c in node.children:
                    if c.type in ("dotted_name", "relative_import"):
                        module_node = c
                        break
            source = module_node.text.decode("utf-8") if module_node else ""
            names: list[str] = []
            for c in node.children:
                if c.type == "dotted_name" and c != module_node:
                    names.append(c.text.decode("utf-8"))
                elif c.type == "aliased_import":
                    orig = c.child_by_field_name("name")
                    if orig:
                        names.append(orig.text.decode("utf-8"))
                elif c.type == "identifier":
                    names.append(c.text.decode("utf-8"))
            if source:
                imports.append(ParsedImport(source=source, names=names, line=line_num))

    def _handle_function_node(
        self,
        node: Any,
        lines: list[str],
        framework: str,
        functions: list[ParsedSymbol],
        routes: list[ParsedRoute],
        decorators: list[str],
        parent_class: str | None = None,
    ) -> None:
        name_node = node.child_by_field_name("name")
        if not name_node:
            return
        name = name_node.text.decode("utf-8")

        if name.startswith("_") and name != "__init__":
            return

        line_num = node.start_point[0] + 1
        end_line = node.end_point[0] + 1

        # Check async
        is_async = any(c.type == "async" for c in node.children)

        # Extract parameters
        params: list[str] = []
        param_node = node.child_by_field_name("parameters")
        if param_node:
            for p in param_node.children:
                if p.type in ("identifier", "typed_parameter", "default_parameter", "typed_default_parameter"):
                    p_name = p.child_by_field_name("name")
                    if p_name:
                        params.append(p_name.text.decode("utf-8"))
                    elif p.type == "identifier":
                        params.append(p.text.decode("utf-8"))
                    elif p.children and p.children[0].type == "identifier":
                        params.append(p.children[0].text.decode("utf-8"))

        docstring = self._extract_node_docstring(node)

        # Check routes
        is_route = False
        for dec in decorators:
            dec_clean = dec.strip("@")
            if any(dec_clean.startswith(prefix) for prefix in ("app.", "router.", "api.", "route")):
                is_route = True
                route_match = re.search(r"\.(get|post|put|delete|patch|route)\s*\(\s*['\"]([^'\"]+)['\"]", dec_clean)
                if route_match:
                    method = route_match.group(1).upper()
                    if method == "ROUTE":
                        method = "GET"
                    path = route_match.group(2)
                    routes.append(ParsedRoute(
                        method=method,
                        path=path,
                        handler=name,
                        framework=framework,
                        line=line_num,
                    ))

        functions.append(ParsedSymbol(
            name=name,
            kind="function",
            line=line_num,
            end_line=end_line,
            signature=f"{name}({', '.join(params)})",
            docstring=docstring,
            is_async=is_async,
            parent=parent_class,
            metadata={"decorators": decorators, "params": params, "is_route": is_route},
        ))

    def _handle_decorated_node(
        self,
        node: Any,
        lines: list[str],
        framework: str,
        classes: list[ParsedSymbol],
        functions: list[ParsedSymbol],
        routes: list[ParsedRoute],
        models: list[ParsedSymbol],
        parent_class: str | None = None,
    ) -> None:
        decorators: list[str] = []
        target_node = None

        for child in node.children:
            if child.type == "decorator":
                # Decorator text e.g. @router.get('/users')
                dec_text = child.text.decode("utf-8").strip()
                if dec_text.startswith("@"):
                    decorators.append(dec_text[1:])
                else:
                    decorators.append(dec_text)
            elif child.type in ("function_definition", "class_definition"):
                target_node = child

        if not target_node:
            return

        if target_node.type == "function_definition":
            self._handle_function_node(target_node, lines, framework, functions, routes, decorators, parent_class=parent_class)
        elif target_node.type == "class_definition":
            self._handle_class_node(target_node, lines, framework, classes, functions, routes, models, decorators)

    def _handle_class_node(
        self,
        node: Any,
        lines: list[str],
        framework: str,
        classes: list[ParsedSymbol],
        functions: list[ParsedSymbol],
        routes: list[ParsedRoute],
        models: list[ParsedSymbol],
        decorators: list[str],
    ) -> None:
        name_node = node.child_by_field_name("name")
        if not name_node:
            return
        name = name_node.text.decode("utf-8")

        line_num = node.start_point[0] + 1
        end_line = node.end_point[0] + 1

        # Superclasses/bases
        bases: list[str] = []
        superclasses_node = node.child_by_field_name("superclasses")
        if superclasses_node:
            for child in superclasses_node.children:
                if child.type in ("identifier", "attribute"):
                    bases.append(child.text.decode("utf-8"))

        docstring = self._extract_node_docstring(node)

        # Check methods in class body
        methods: list[str] = []
        body_node = node.child_by_field_name("body")
        fields: list[str] = []

        if body_node:
            for item in body_node.children:
                if item.type == "function_definition":
                    m_name_node = item.child_by_field_name("name")
                    if m_name_node:
                        m_name = m_name_node.text.decode("utf-8")
                        if not m_name.startswith("__") or m_name == "__init__":
                            methods.append(m_name)
                    # Also collect class methods as functions with parent
                    self._handle_function_node(item, lines, framework, functions, routes, decorators=[], parent_class=name)
                elif item.type == "decorated_definition":
                    for sub in item.children:
                        if sub.type == "function_definition":
                            m_name_node = sub.child_by_field_name("name")
                            if m_name_node:
                                m_name = m_name_node.text.decode("utf-8")
                                if not m_name.startswith("__") or m_name == "__init__":
                                    methods.append(m_name)
                    self._handle_decorated_node(item, lines, framework, classes, functions, routes, models, parent_class=name)
                elif item.type == "expression_statement":
                    # Check for ORM columns: e.g. name = Column(String)
                    stmt_text = item.text.decode("utf-8")
                    f_match = re.search(r"(\w+)\s*=\s*(?:db\.Column|Column|Mapped|Mapped\[)", stmt_text)
                    if f_match:
                        fields.append(f_match.group(1))

        is_service = any(
            d.split("(")[0] in ("service", "Service", "injectable", "component", "Component", "router", "Router", "APIRouter")
            for d in decorators
        )

        # Deep ORM metadata extraction
        body_slice = "\n".join(lines[line_num - 1:end_line])
        orm_meta = PythonORMParser.extract_model_metadata(name, bases, body_slice)

        is_model = orm_meta is not None or any(
            b in ("models.Model", "Model", "Base", "db.Model") or "model" in b.lower()
            for b in bases
        ) or bool(fields)

        if is_model:
            model_metadata = {
                "fields": orm_meta["fields"] if orm_meta else fields,
                "bases": bases,
            }
            if orm_meta:
                model_metadata["orm"] = orm_meta["orm"]
                model_metadata["primary_keys"] = orm_meta["primary_keys"]
                model_metadata["foreign_keys"] = orm_meta["foreign_keys"]
                model_metadata["relations"] = orm_meta["relations"]

            models.append(ParsedSymbol(
                name=name,
                kind="model",
                line=line_num,
                end_line=end_line,
                metadata=model_metadata,
            ))

        classes.append(ParsedSymbol(
            name=name,
            kind="class",
            line=line_num,
            end_line=end_line,
            docstring=docstring,
            is_exported=not name.startswith("_"),
            metadata={
                "bases": bases,
                "decorators": decorators,
                "methods": methods,
                "is_service": is_service,
            },
        ))

    def _check_expression_route(self, node: Any, framework: str, routes: list[ParsedRoute]) -> None:
        expr_text = node.text.decode("utf-8")
        match = re.search(r"path\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*(\w+)", expr_text)
        if match:
            routes.append(ParsedRoute(
                method="GET",
                path=match.group(1),
                handler=match.group(2),
                framework=framework,
                line=node.start_point[0] + 1,
            ))

    def _extract_node_docstring(self, node: Any) -> str | None:
        body = node.child_by_field_name("body")
        if not body or not body.children:
            return None
        first_stmt = body.children[0]
        if first_stmt.type == "expression_statement" and first_stmt.children:
            str_child = first_stmt.children[0]
            if str_child.type == "string":
                val = str_child.text.decode("utf-8")
                # Strip triple or single quotes
                val = re.sub(r'^(?:"""|\'\'\'|"|\')', "", val)
                val = re.sub(r'(?:"""|\'\'\'|"|\')$', "", val)
                return val.strip()
        return None

    # ----------------------------------------------------------------------
    # Regex Fallback Parser
    # ----------------------------------------------------------------------

    def _parse_regex(self, content: str, path: str) -> ParseResult:
        result = ParseResult(loc=self._count_loc(content))
        lines = content.splitlines()

        result.imports = self._extract_imports_regex(content)
        result.functions = self._extract_functions_regex(content, lines)
        result.classes = self._extract_classes_regex(content, lines)
        result.routes = self._extract_routes_regex(content, lines)
        result.models = self._extract_models_regex(content, lines)
        result.exports = [s.name for s in result.classes + result.functions if not s.name.startswith("_")]

        result.symbols = result.functions + result.classes + result.models

        return result

    def _extract_imports_regex(self, content: str) -> list[ParsedImport]:
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

    def _extract_functions_regex(self, content: str, lines: list[str]) -> list[ParsedSymbol]:
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

    def _extract_classes_regex(self, content: str, lines: list[str]) -> list[ParsedSymbol]:
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

    def _extract_routes_regex(self, content: str, lines: list[str]) -> list[ParsedRoute]:
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

    def _extract_models_regex(self, content: str, lines: list[str]) -> list[ParsedSymbol]:
        models = []
        for pattern in MODEL_PATTERNS:
            for match in pattern.finditer(content):
                name = match.group(1)
                line_num = content[:match.start()].count("\n") + 1
                end_line = self._find_class_end(lines, line_num - 1)
                block = "\n".join(lines[line_num - 1:end_line])

                orm_meta = PythonORMParser.extract_model_metadata(name, [], block)

                fields = []
                for f in re.finditer(r"(\w+)\s*=\s*(?:db\.Column|Column|Mapped|Mapped\[)", block):
                    fields.append(f.group(1))

                model_metadata = {
                    "fields": orm_meta["fields"] if orm_meta else fields,
                }
                if orm_meta:
                    model_metadata["orm"] = orm_meta["orm"]
                    model_metadata["primary_keys"] = orm_meta["primary_keys"]
                    model_metadata["foreign_keys"] = orm_meta["foreign_keys"]
                    model_metadata["relations"] = orm_meta["relations"]

                models.append(ParsedSymbol(
                    name=name,
                    kind="model",
                    line=line_num,
                    end_line=end_line,
                    metadata=model_metadata,
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
