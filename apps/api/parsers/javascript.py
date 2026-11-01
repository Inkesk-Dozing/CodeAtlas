"""Tree-sitter native JavaScript/TypeScript AST parser with fallback to regex extraction."""

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

logger = logging.getLogger(__name__)

# Try loading tree-sitter TypeScript and TSX grammars
_TREE_SITTER_AVAILABLE = False
_TS_LANGUAGE = None
_TSX_LANGUAGE = None

try:
    import tree_sitter_typescript
    from tree_sitter import Language, Parser

    _TS_LANGUAGE = Language(tree_sitter_typescript.language_typescript())
    _TSX_LANGUAGE = Language(tree_sitter_typescript.language_tsx())
    _TREE_SITTER_AVAILABLE = True
except Exception as e:
    logger.debug(f"Tree-sitter TypeScript grammar unavailable, using regex fallback: {e}")
    _TREE_SITTER_AVAILABLE = False


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


class JavaScriptParser(BaseParser):
    def __init__(self, language: str = "typescript") -> None:
        self.language = language
        self.use_native = _TREE_SITTER_AVAILABLE
        self._ts_parser: Any = None
        self._tsx_parser: Any = None

        if self.use_native and _TS_LANGUAGE is not None and _TSX_LANGUAGE is not None:
            try:
                self._ts_parser = Parser(_TS_LANGUAGE)
                self._tsx_parser = Parser(_TSX_LANGUAGE)
            except Exception:
                self.use_native = False

    def parse(self, content: str, path: str) -> ParseResult:
        if self.use_native and (self._tsx_parser is not None or self._ts_parser is not None):
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

        # Select TSX parser for jsx/tsx files or general JS/TS (TSX grammar parses TS as superset)
        parser = self._tsx_parser if self._tsx_parser is not None else self._ts_parser
        content_bytes = content.encode("utf-8")
        tree = parser.parse(content_bytes)
        root = tree.root_node

        framework = self._detect_framework(content)
        imports: list[ParsedImport] = []
        exports: set[str] = set()
        functions: list[ParsedSymbol] = []
        classes: list[ParsedSymbol] = []
        interfaces: list[ParsedSymbol] = []
        routes: list[ParsedRoute] = []
        components: list[ParsedSymbol] = []
        hooks: list[ParsedSymbol] = []
        models: list[ParsedSymbol] = []

        self._traverse_tree(
            root,
            lines,
            content,
            framework,
            imports,
            exports,
            functions,
            classes,
            interfaces,
            routes,
            components,
            hooks,
            models,
        )

        result.imports = imports
        result.exports = list(exports)
        result.functions = functions
        result.classes = classes
        result.interfaces = interfaces
        result.routes = routes
        result.components = components
        result.hooks = hooks
        result.models = models

        result.symbols = (
            result.functions + result.classes + result.interfaces
            + result.components + result.hooks + result.models
        )

        return result

    def _traverse_tree(
        self,
        node: Any,
        lines: list[str],
        content: str,
        framework: str,
        imports: list[ParsedImport],
        exports: set[str],
        functions: list[ParsedSymbol],
        classes: list[ParsedSymbol],
        interfaces: list[ParsedSymbol],
        routes: list[ParsedRoute],
        components: list[ParsedSymbol],
        hooks: list[ParsedSymbol],
        models: list[ParsedSymbol],
    ) -> None:
        def walk(n: Any, is_exported_ctx: bool = False, decorators_ctx: list[str] | None = None) -> None:
            decs = decorators_ctx or []
            ntype = n.type

            if ntype == "import_statement":
                self._handle_import_node(n, imports)
                return

            elif ntype == "export_statement":
                # e.g. export const api = ...; export function foo() ...; export default LoginPage;
                for child in n.children:
                    if child.type == "export_clause":
                        for spec in child.children:
                            if spec.type == "export_specifier":
                                name_node = spec.child_by_field_name("name")
                                if name_node:
                                    exports.add(name_node.text.decode("utf-8"))
                    elif child.type in ("function_declaration", "class_declaration", "lexical_declaration", "variable_declaration", "interface_declaration", "type_alias_declaration"):
                        walk(child, is_exported_ctx=True, decorators_ctx=decs)
                    elif child.type == "identifier":
                        exports.add(child.text.decode("utf-8"))
                    elif child.type == "default":
                        # Look for following identifier or expression
                        pass
                return

            elif ntype == "function_declaration":
                name_node = n.child_by_field_name("name")
                if name_node:
                    name = name_node.text.decode("utf-8")
                    line_num = n.start_point[0] + 1
                    end_line = n.end_point[0] + 1
                    is_async = any(c.type == "async" for c in n.children)
                    sig = self._extract_sig(n, name)

                    if is_exported_ctx:
                        exports.add(name)

                    if self._is_component_name(name):
                        comp = self._create_component_symbol(n, name, line_num, end_line, is_exported_ctx)
                        components.append(comp)

                    if self._is_hook_name(name):
                        hooks.append(ParsedSymbol(
                            name=name,
                            kind="hook",
                            line=line_num,
                            end_line=end_line,
                            is_exported=is_exported_ctx,
                        ))

                    functions.append(ParsedSymbol(
                        name=name,
                        kind="function",
                        line=line_num,
                        end_line=end_line,
                        signature=sig,
                        is_async=is_async,
                        is_exported=is_exported_ctx,
                    ))
                return

            elif ntype in ("lexical_declaration", "variable_declaration"):
                # const foo = () => {}, api = { ... }
                for decl in n.children:
                    if decl.type == "variable_declarator":
                        name_node = decl.child_by_field_name("name")
                        val_node = decl.child_by_field_name("value")
                        if not name_node:
                            continue
                        name = name_node.text.decode("utf-8")
                        line_num = decl.start_point[0] + 1
                        end_line = decl.end_point[0] + 1

                        if is_exported_ctx:
                            exports.add(name)

                        # Check require imports: const x = require('pkg')
                        if val_node and val_node.type == "call_expression":
                            fn_call = val_node.child_by_field_name("function")
                            if fn_call and fn_call.text.decode("utf-8") == "require":
                                args = val_node.child_by_field_name("arguments")
                                if args and len(args.children) >= 2:
                                    src = args.children[1].text.decode("utf-8").strip("'\"")
                                    imports.append(ParsedImport(source=src, names=[name], line=line_num))

                        # Check arrow functions or function expressions
                        if val_node and val_node.type in ("arrow_function", "function_expression"):
                            is_async = any(c.type == "async" for c in val_node.children)
                            sig = self._extract_sig(val_node, name)

                            if self._is_component_name(name):
                                comp = self._create_component_symbol(val_node, name, line_num, end_line, is_exported_ctx)
                                components.append(comp)

                            if self._is_hook_name(name):
                                hooks.append(ParsedSymbol(
                                    name=name,
                                    kind="hook",
                                    line=line_num,
                                    end_line=end_line,
                                    is_exported=is_exported_ctx,
                                ))

                            functions.append(ParsedSymbol(
                                name=name,
                                kind="function",
                                line=line_num,
                                end_line=end_line,
                                signature=sig,
                                is_async=is_async,
                                is_exported=is_exported_ctx,
                            ))
                return

            elif ntype == "class_declaration":
                self._handle_class_node(n, is_exported_ctx, decs, framework, classes, components, routes)
                return

            elif ntype == "interface_declaration" or ntype == "type_alias_declaration":
                name_node = n.child_by_field_name("name")
                if name_node:
                    name = name_node.text.decode("utf-8")
                    line_num = n.start_point[0] + 1
                    if is_exported_ctx:
                        exports.add(name)
                    interfaces.append(ParsedSymbol(
                        name=name,
                        kind="interface",
                        line=line_num,
                        is_exported=is_exported_ctx,
                    ))
                return

            elif ntype == "expression_statement":
                # Check for express / fastify routes e.g. app.get('/users', handler)
                for child in n.children:
                    if child.type == "call_expression":
                        self._check_route_call(child, framework, content, routes)

            # Check Prisma or custom models
            # Recurse for decorators or top-level blocks
            for child in n.children:
                if child.type == "decorator":
                    decs.append(child.text.decode("utf-8").strip())
                elif child.type in ("program", "statement_block"):
                    walk(child, is_exported_ctx=is_exported_ctx, decorators_ctx=decs)

        walk(node)

        # Check for Prisma or ORM model blocks if present in content
        prisma_match = re.finditer(r"model\s+(\w+)\s*\{", content)
        for match in prisma_match:
            name = match.group(1)
            line_num = content[:match.start()].count("\n") + 1
            models.append(ParsedSymbol(name=name, kind="model", line=line_num, metadata={"orm": "prisma"}))

    def _handle_import_node(self, node: Any, imports: list[ParsedImport]) -> None:
        line_num = node.start_point[0] + 1
        source_node = node.child_by_field_name("source")
        source = source_node.text.decode("utf-8").strip("'\"") if source_node else ""

        names: list[str] = []
        is_default = False
        is_namespace = False

        for child in node.children:
            if child.type == "import_clause":
                for c in child.children:
                    if c.type == "identifier":
                        names.append(c.text.decode("utf-8"))
                        is_default = True
                    elif c.type == "namespace_import":
                        is_namespace = True
                        for id_node in c.children:
                            if id_node.type == "identifier":
                                names.append(id_node.text.decode("utf-8"))
                    elif c.type == "named_imports":
                        for spec in c.children:
                            if spec.type == "import_specifier":
                                n_node = spec.child_by_field_name("name")
                                if n_node:
                                    names.append(n_node.text.decode("utf-8"))

        if source:
            imports.append(ParsedImport(
                source=source,
                names=names,
                line=line_num,
                is_default=is_default,
                is_namespace=is_namespace,
            ))

    def _handle_class_node(
        self,
        node: Any,
        is_exported: bool,
        decorators: list[str],
        framework: str,
        classes: list[ParsedSymbol],
        components: list[ParsedSymbol],
        routes: list[ParsedRoute],
    ) -> None:
        name_node = node.child_by_field_name("name")
        if not name_node:
            return
        name = name_node.text.decode("utf-8")
        line_num = node.start_point[0] + 1
        end_line = node.end_point[0] + 1

        # Check decorators attached to class node
        for child in node.children:
            if child.type == "decorator":
                decorators.append(child.text.decode("utf-8").strip())

        extends_val = None
        implements_list: list[str] = []

        for child in node.children:
            if child.type == "class_heritage":
                for hc in child.children:
                    if hc.type == "extends_clause":
                        for sub in hc.children:
                            if sub.type in ("identifier", "type_identifier"):
                                extends_val = sub.text.decode("utf-8")
                    elif hc.type == "implements_clause":
                        for sub in hc.children:
                            if sub.type in ("identifier", "type_identifier"):
                                implements_list.append(sub.text.decode("utf-8"))

        # Methods and class body decorators
        methods: list[str] = []
        body_node = node.child_by_field_name("body")
        if body_node:
            for item in body_node.children:
                if item.type == "method_definition":
                    m_name_node = item.child_by_field_name("name")
                    if m_name_node:
                        methods.append(m_name_node.text.decode("utf-8"))

        clean_decorators = [d.lstrip("@").split("(")[0].strip() for d in decorators]
        is_service = any(d in ("Injectable", "Service", "Component") for d in clean_decorators)

        # Check React class component
        if extends_val and ("Component" in extends_val or "PureComponent" in extends_val):
            components.append(ParsedSymbol(
                name=name,
                kind="component",
                line=line_num,
                end_line=end_line,
                is_exported=is_exported,
                metadata={"renders": [], "props": [], "hooks_used": []},
            ))

        classes.append(ParsedSymbol(
            name=name,
            kind="class",
            line=line_num,
            end_line=end_line,
            is_exported=is_exported,
            metadata={
                "extends": extends_val,
                "implements": implements_list,
                "decorators": clean_decorators,
                "methods": methods,
                "is_service": is_service,
            },
        ))

    def _create_component_symbol(
        self,
        node: Any,
        name: str,
        line_num: int,
        end_line: int,
        is_exported: bool,
    ) -> ParsedSymbol:
        hooks_used: set[str] = set()
        renders: set[str] = set()
        props: list[str] = []

        # Walk children of node to extract JSX and hooks
        def walk_comp(n: Any) -> None:
            if n.type == "call_expression":
                fn_node = n.child_by_field_name("function")
                if fn_node:
                    fn_name = fn_node.text.decode("utf-8")
                    if self._is_hook_name(fn_name):
                        hooks_used.add(fn_name)
            elif n.type in ("jsx_opening_element", "jsx_self_closing_element"):
                name_node = n.child_by_field_name("name")
                if name_node:
                    renders.add(name_node.text.decode("utf-8"))
            for c in n.children:
                walk_comp(c)

        walk_comp(node)

        # Extract props destructuring if present
        param_node = node.child_by_field_name("parameters")
        if param_node:
            for p in param_node.children:
                if p.type in ("required_parameter", "optional_parameter"):
                    pattern = p.child_by_field_name("pattern")
                    if pattern and pattern.type == "object_pattern":
                        for oc in pattern.children:
                            if oc.type == "shorthand_property_identifier_pattern":
                                props.append(oc.text.decode("utf-8"))
                            elif oc.type == "object_assignment_pattern":
                                left = oc.child_by_field_name("left")
                                if left:
                                    props.append(left.text.decode("utf-8"))

        return ParsedSymbol(
            name=name,
            kind="component",
            line=line_num,
            end_line=end_line,
            is_exported=is_exported,
            metadata={
                "hooks_used": list(hooks_used),
                "props": props,
                "renders": list(renders)[:10],
            },
        )

    def _check_route_call(
        self,
        call_node: Any,
        framework: str,
        content: str,
        routes: list[ParsedRoute],
    ) -> None:
        fn_node = call_node.child_by_field_name("function")
        if not fn_node or fn_node.type != "member_expression":
            return

        obj_node = fn_node.child_by_field_name("object")
        prop_node = fn_node.child_by_field_name("property")

        if not obj_node or not prop_node:
            return

        obj_name = obj_node.text.decode("utf-8")
        method_name = prop_node.text.decode("utf-8").lower()

        if obj_name in ("app", "router") and method_name in ("get", "post", "put", "delete", "patch", "all"):
            args_node = call_node.child_by_field_name("arguments")
            if not args_node:
                return

            args = [c for c in args_node.children if c.type not in ("(", ")", ",")]
            if not args:
                return

            path = args[0].text.decode("utf-8").strip("'\"")
            handler = args[-1].text.decode("utf-8") if len(args) > 1 else ""

            line_num = call_node.start_point[0] + 1
            node_text = call_node.text.decode("utf-8")

            middleware = []
            for mw in ("authenticate", "authorize", "validate", "rateLimit", "cors"):
                if mw in node_text:
                    middleware.append(mw)

            routes.append(ParsedRoute(
                method=method_name.upper(),
                path=path,
                handler=handler,
                middleware=middleware,
                framework=framework,
                line=line_num,
            ))

    def _extract_sig(self, node: Any, name: str) -> str:
        param_node = node.child_by_field_name("parameters")
        params_text = ""
        if param_node:
            # Strip outer parens
            params_text = param_node.text.decode("utf-8").strip("()")
        return f"{name}({params_text})"

    @staticmethod
    def _is_component_name(name: str) -> bool:
        return bool(name and name[0].isupper() and not name.isupper())

    @staticmethod
    def _is_hook_name(name: str) -> bool:
        return bool(name and name.startswith("use") and len(name) > 3 and name[3].isupper())

    # ----------------------------------------------------------------------
    # Regex Fallback Parser
    # ----------------------------------------------------------------------

    def _parse_regex(self, content: str, path: str) -> ParseResult:
        result = ParseResult(loc=self._count_loc(content))
        lines = content.splitlines()

        result.imports = self._extract_imports_regex(content, lines)
        result.exports = self._extract_exports_regex(content)
        result.functions = self._extract_functions_regex(content, lines)
        result.classes = self._extract_classes_regex(content, lines)
        result.interfaces = self._extract_interfaces_regex(content, lines)
        result.routes = self._extract_routes_regex(content, lines)
        result.components = self._extract_components_regex(content, lines)
        result.hooks = self._extract_hooks_regex(content)
        result.models = self._extract_models_regex(content, lines)

        result.symbols = (
            result.functions + result.classes + result.interfaces
            + result.components + result.hooks + result.models
        )

        return result

    def _extract_imports_regex(self, content: str, lines: list[str]) -> list[ParsedImport]:
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

    def _extract_exports_regex(self, content: str) -> list[str]:
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

    def _extract_functions_regex(self, content: str, lines: list[str]) -> list[ParsedSymbol]:
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

    def _extract_classes_regex(self, content: str, lines: list[str]) -> list[ParsedSymbol]:
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

    def _extract_interfaces_regex(self, content: str, lines: list[str]) -> list[ParsedSymbol]:
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

    def _extract_routes_regex(self, content: str, lines: list[str]) -> list[ParsedRoute]:
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

    def _extract_components_regex(self, content: str, lines: list[str]) -> list[ParsedSymbol]:
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

    def _extract_hooks_regex(self, content: str) -> list[ParsedSymbol]:
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

    def _extract_models_regex(self, content: str, lines: list[str]) -> list[ParsedSymbol]:
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
