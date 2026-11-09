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
from parsers.routes import extract_nextjs_app_routes, extract_route_params

logger = logging.getLogger(__name__)

# Try loading tree-sitter TypeScript and TSX grammars
_TREE_SITTER_AVAILABLE = False
_TS_LANGUAGE = None
_TSX_LANGUAGE = None

# Comprehensive set of primitive HTML and SVG tags to distinguish from custom React/Vue components
HTML_PRIMITIVE_TAGS: set[str] = {
    "a", "abbr", "address", "area", "article", "aside", "audio", "b", "base", "bdi", "bdo",
    "blockquote", "body", "br", "button", "canvas", "caption", "cite", "code", "col", "colgroup",
    "data", "datalist", "dd", "del", "details", "dfn", "dialog", "div", "dl", "dt", "em", "embed",
    "fieldset", "figcaption", "figure", "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6",
    "head", "header", "hgroup", "hr", "html", "i", "iframe", "img", "input", "ins", "kbd",
    "label", "legend", "li", "link", "main", "map", "mark", "menu", "meta", "meter", "nav",
    "noscript", "object", "ol", "optgroup", "option", "output", "p", "picture", "pre", "progress",
    "q", "rp", "rt", "ruby", "s", "samp", "script", "search", "section", "select", "slot",
    "small", "source", "span", "strong", "style", "sub", "summary", "sup", "table", "tbody",
    "td", "template", "textarea", "tfoot", "th", "thead", "time", "title", "tr", "track", "u",
    "ul", "var", "video", "wbr",
    # SVG tags
    "svg", "animate", "circle", "clippath", "defs", "ellipse", "g", "line", "lineargradient",
    "mask", "path", "pattern", "polygon", "polyline", "radialgradient", "rect", "stop", "text", "tspan",
}

try:
    import tree_sitter_typescript
    from tree_sitter import Language, Parser

    _TS_LANGUAGE = Language(tree_sitter_typescript.language_typescript())
    _TSX_LANGUAGE = Language(tree_sitter_typescript.language_tsx())
    _TREE_SITTER_AVAILABLE = True
except Exception as e:
    logger.debug(f"Tree-sitter TypeScript grammar unavailable, using regex fallback: {e}")
    _TREE_SITTER_AVAILABLE = False


def classify_js_import(source: str) -> dict[str, bool]:
    """Classify an import source as internal relative, internal monorepo package, or third-party."""
    if source.startswith((".", "/")):
        return {"is_internal": True, "is_monorepo": False, "is_third_party": False}
    if source.startswith(("@/", "~/")):
        return {"is_internal": True, "is_monorepo": True, "is_third_party": False}
    if any(
        source.startswith(prefix)
        for prefix in ("@repo/", "@workspace/", "@shared/", "@core/", "@packages/", "@codeatlas/", "@apps/")
    ):
        return {"is_internal": True, "is_monorepo": True, "is_third_party": False}
    return {"is_internal": False, "is_monorepo": False, "is_third_party": True}


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

    @staticmethod
    def _calculate_complexity(node: Any) -> int:
        """McCabe cyclomatic complexity for JavaScript / TypeScript functions."""
        complexity = 1

        def walk(n: Any) -> None:
            nonlocal complexity
            ntype = n.type
            if ntype in (
                "if_statement",
                "for_statement",
                "for_in_statement",
                "while_statement",
                "do_statement",
                "catch_clause",
                "ternary_expression",
                "switch_case",
            ):
                complexity += 1
            elif ntype == "binary_expression":
                op = n.child_by_field_name("operator")
                if op and op.text.decode("utf-8") in ("&&", "||", "??"):
                    complexity += 1
            for child in n.children:
                walk(child)

        walk(node)
        return complexity

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
        variables: list[ParsedSymbol] = []

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
            variables,
        )

        # Detect Next.js 14 App Router endpoints (e.g. app/**/route.ts)
        nextjs_routes = extract_nextjs_app_routes(path, content)
        for nr in nextjs_routes:
            if not any(r.method == nr.method and r.path == nr.path for r in routes):
                routes.append(nr)

        result.imports = imports
        result.exports = list(exports)
        result.functions = functions
        result.classes = classes
        result.interfaces = interfaces
        result.routes = routes
        result.components = components
        result.hooks = hooks
        result.models = models
        result.variables = variables

        result.symbols = (
            result.functions + result.classes + result.interfaces
            + result.components + result.hooks + result.models
            + result.variables
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
        variables: list[ParsedSymbol],
    ) -> None:
        def walk(n: Any, is_exported_ctx: bool = False, decorators_ctx: list[str] | None = None) -> None:
            decs = decorators_ctx or []
            ntype = n.type

            if ntype == "import_statement":
                self._handle_import_node(n, imports)
                return

            elif ntype == "export_statement":
                # Collect any decorators attached directly to export_statement (e.g. @Component() export class ...)
                export_decs = list(decs)
                for child in n.children:
                    if child.type == "decorator":
                        export_decs.append(child.text.decode("utf-8").strip())

                source_node = n.child_by_field_name("source")
                if source_node:
                    # Re-export statement: export * from '...', export { a } from '...'
                    reexport_source = source_node.text.decode("utf-8").strip("'\"")
                    c_info = classify_js_import(reexport_source)
                    reexport_names: list[str] = []
                    is_ns = False
                    for child in n.children:
                        if child.type == "*":
                            exports.add("*")
                            reexport_names.append("*")
                            is_ns = True
                        elif child.type == "namespace_export":
                            is_ns = True
                            for sc in child.children:
                                if sc.type == "identifier":
                                    ns_name = sc.text.decode("utf-8")
                                    exports.add(ns_name)
                                    reexport_names.append(ns_name)
                        elif child.type == "export_clause":
                            for spec in child.children:
                                if spec.type == "export_specifier":
                                    n_node = spec.child_by_field_name("name")
                                    a_node = spec.child_by_field_name("alias")
                                    name_val = a_node.text.decode("utf-8") if a_node else (n_node.text.decode("utf-8") if n_node else "")
                                    if name_val:
                                        exports.add(name_val)
                                        reexport_names.append(name_val)
                    imports.append(ParsedImport(
                        source=reexport_source,
                        names=reexport_names,
                        line=n.start_point[0] + 1,
                        is_namespace=is_ns,
                        is_internal=c_info["is_internal"],
                        is_monorepo=c_info["is_monorepo"],
                        is_third_party=c_info["is_third_party"],
                    ))
                    return

                # Regular export statement
                for child in n.children:
                    if child.type == "export_clause":
                        for spec in child.children:
                            if spec.type == "export_specifier":
                                name_node = spec.child_by_field_name("name")
                                a_node = spec.child_by_field_name("alias")
                                name_val = a_node.text.decode("utf-8") if a_node else (name_node.text.decode("utf-8") if name_node else "")
                                if name_val:
                                    exports.add(name_val)
                    elif child.type in (
                        "function_declaration",
                        "class_declaration",
                        "lexical_declaration",
                        "variable_declaration",
                        "interface_declaration",
                        "type_alias_declaration",
                    ):
                        walk(child, is_exported_ctx=True, decorators_ctx=export_decs)
                    elif child.type == "identifier":
                        exports.add(child.text.decode("utf-8"))
                    elif child.type == "default":
                        exports.add("default")
                        for next_child in n.children:
                            if next_child.type == "identifier":
                                exports.add(next_child.text.decode("utf-8"))
                return

            elif ntype == "function_declaration":
                name_node = n.child_by_field_name("name")
                if name_node:
                    name = name_node.text.decode("utf-8")
                    line_num = n.start_point[0] + 1
                    end_line = n.end_point[0] + 1
                    is_async = any(c.type == "async" for c in n.children)
                    sig = self._extract_sig(n, name)
                    complexity = self._calculate_complexity(n)

                    tp_node = n.child_by_field_name("type_parameters")
                    type_params = tp_node.text.decode("utf-8") if tp_node else None

                    ret_node = n.child_by_field_name("return_type")
                    ret_type = ret_node.text.decode("utf-8").lstrip(":").strip() if ret_node else None

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
                            metadata={"start_line": line_num, "end_line": end_line},
                        ))

                    functions.append(ParsedSymbol(
                        name=name,
                        kind="function",
                        line=line_num,
                        end_line=end_line,
                        signature=sig,
                        is_async=is_async,
                        is_exported=is_exported_ctx,
                        metadata={
                            "type_parameters": type_params,
                            "return_type": ret_type,
                            "complexity": {"cyclomatic": complexity},
                            "start_line": line_num,
                            "end_line": end_line,
                        },
                    ))
                return

            elif ntype in ("lexical_declaration", "variable_declaration"):
                # const foo = () => {}, api = { ... }
                is_const = any(c.type == "const" for c in n.children)
                for decl in n.children:
                    if decl.type == "variable_declarator":
                        name_node = decl.child_by_field_name("name")
                        val_node = decl.child_by_field_name("value")
                        if not name_node:
                            continue
                        line_num = decl.start_point[0] + 1
                        end_line = decl.end_point[0] + 1

                        # Check require imports:
                        # 1) const x = require('pkg')
                        # 2) const { a, b } = require('pkg')
                        # 3) const x = require('pkg').foo
                        require_call = None
                        if val_node:
                            if val_node.type == "call_expression":
                                fn_call = val_node.child_by_field_name("function")
                                if fn_call and fn_call.text.decode("utf-8") == "require":
                                    require_call = val_node
                            elif val_node.type == "member_expression":
                                obj = val_node.child_by_field_name("object")
                                if obj and obj.type == "call_expression":
                                    fn_call = obj.child_by_field_name("function")
                                    if fn_call and fn_call.text.decode("utf-8") == "require":
                                        require_call = obj

                        if require_call:
                            args = require_call.child_by_field_name("arguments")
                            if args and len(args.children) >= 2:
                                src = args.children[1].text.decode("utf-8").strip("'\"")
                                req_names: list[str] = []
                                if name_node.type == "identifier":
                                    req_names.append(name_node.text.decode("utf-8"))
                                elif name_node.type == "object_pattern":
                                    for oc in name_node.children:
                                        if oc.type == "shorthand_property_identifier_pattern":
                                            req_names.append(oc.text.decode("utf-8"))
                                        elif oc.type == "pair_pattern":
                                            val_id = oc.child_by_field_name("value")
                                            if val_id:
                                                req_names.append(val_id.text.decode("utf-8"))
                                c_info = classify_js_import(src)
                                imports.append(ParsedImport(
                                    source=src,
                                    names=req_names,
                                    line=line_num,
                                    is_default=bool(name_node.type == "identifier"),
                                    is_internal=c_info["is_internal"],
                                    is_monorepo=c_info["is_monorepo"],
                                    is_third_party=c_info["is_third_party"],
                                ))
                                continue

                        if name_node.type != "identifier":
                            continue

                        name = name_node.text.decode("utf-8")
                        if is_exported_ctx:
                            exports.add(name)

                        # Check arrow functions or function expressions
                        if val_node and val_node.type in ("arrow_function", "function_expression"):
                            is_async = any(c.type == "async" for c in val_node.children)
                            sig = self._extract_sig(val_node, name)
                            complexity = self._calculate_complexity(val_node)

                            tp_node = val_node.child_by_field_name("type_parameters")
                            type_params = tp_node.text.decode("utf-8") if tp_node else None

                            ret_node = val_node.child_by_field_name("return_type")
                            ret_type = ret_node.text.decode("utf-8").lstrip(":").strip() if ret_node else None

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
                                    metadata={"start_line": line_num, "end_line": end_line},
                                ))

                            functions.append(ParsedSymbol(
                                name=name,
                                kind="function",
                                line=line_num,
                                end_line=end_line,
                                signature=sig,
                                is_async=is_async,
                                is_exported=is_exported_ctx,
                                metadata={
                                    "type_parameters": type_params,
                                    "return_type": ret_type,
                                    "complexity": {"cyclomatic": complexity},
                                    "start_line": line_num,
                                    "end_line": end_line,
                                },
                            ))
                        else:
                            # Standalone constant or variable
                            variables.append(ParsedSymbol(
                                name=name,
                                kind="constant" if is_const else "variable",
                                line=line_num,
                                end_line=end_line,
                                is_exported=is_exported_ctx,
                                metadata={
                                    "is_const": is_const,
                                    "start_line": line_num,
                                    "end_line": end_line,
                                },
                            ))
                return

            elif ntype == "class_declaration":
                self._handle_class_node(n, is_exported_ctx, decs, framework, classes, components, routes)
                return

            elif ntype in ("interface_declaration", "type_alias_declaration"):
                name_node = n.child_by_field_name("name")
                if name_node:
                    name = name_node.text.decode("utf-8")
                    line_num = n.start_point[0] + 1
                    end_line = n.end_point[0] + 1
                    tp_node = n.child_by_field_name("type_parameters")
                    type_params = tp_node.text.decode("utf-8") if tp_node else None
                    if is_exported_ctx:
                        exports.add(name)
                    interfaces.append(ParsedSymbol(
                        name=name,
                        kind="interface" if ntype == "interface_declaration" else "type",
                        line=line_num,
                        end_line=end_line,
                        is_exported=is_exported_ctx,
                        metadata={
                            "type_parameters": type_params,
                            "start_line": line_num,
                            "end_line": end_line,
                        },
                    ))
                return

            elif ntype == "expression_statement":
                # Check for express / fastify routes e.g. app.get('/users', handler)
                for child in n.children:
                    if child.type == "call_expression":
                        self._check_route_call(child, framework, content, routes)

            # Recurse for decorators or child nodes
            for child in n.children:
                if child.type == "decorator":
                    decs.append(child.text.decode("utf-8").strip())
                else:
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
                                a_node = spec.child_by_field_name("alias")
                                name_val = a_node.text.decode("utf-8") if a_node else (n_node.text.decode("utf-8") if n_node else "")
                                if name_val:
                                    names.append(name_val)

        if source:
            c_info = classify_js_import(source)
            imports.append(ParsedImport(
                source=source,
                names=names,
                line=line_num,
                is_default=is_default,
                is_namespace=is_namespace,
                is_internal=c_info["is_internal"],
                is_monorepo=c_info["is_monorepo"],
                is_third_party=c_info["is_third_party"],
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

        tp_node = node.child_by_field_name("type_parameters")
        type_params = tp_node.text.decode("utf-8") if tp_node else None

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
        method_details: list[dict[str, Any]] = []
        properties: list[dict[str, Any]] = []
        body_node = node.child_by_field_name("body")
        if body_node:
            for item in body_node.children:
                if item.type == "method_definition":
                    m_name_node = item.child_by_field_name("name")
                    if m_name_node:
                        m_name = m_name_node.text.decode("utf-8")
                        methods.append(m_name)
                        m_is_async = any(c.type == "async" for c in item.children)
                        m_is_static = any(c.type == "static" for c in item.children)
                        m_visibility = "public"
                        for c in item.children:
                            if c.type == "accessibility_modifier":
                                m_visibility = c.text.decode("utf-8")
                        m_ret_node = item.child_by_field_name("return_type")
                        m_ret = m_ret_node.text.decode("utf-8").lstrip(":").strip() if m_ret_node else None
                        m_tp_node = item.child_by_field_name("type_parameters")
                        m_tp = m_tp_node.text.decode("utf-8") if m_tp_node else None
                        method_details.append({
                            "name": m_name,
                            "visibility": m_visibility,
                            "is_static": m_is_static,
                            "is_async": m_is_async,
                            "return_type": m_ret,
                            "type_parameters": m_tp,
                            "line": item.start_point[0] + 1,
                            "end_line": item.end_point[0] + 1,
                            "complexity": self._calculate_complexity(item),
                        })
                elif item.type in ("public_field_definition", "field_definition", "property_definition"):
                    p_name_node = item.child_by_field_name("name")
                    p_type_node = item.child_by_field_name("type")
                    p_val_node = item.child_by_field_name("value")
                    if p_name_node:
                        p_name = p_name_node.text.decode("utf-8")
                        p_type = p_type_node.text.decode("utf-8").lstrip(":").strip() if p_type_node else None
                        p_val = p_val_node.text.decode("utf-8") if p_val_node else None
                        p_static = any(c.type == "static" for c in item.children)
                        p_readonly = any(c.type == "readonly" for c in item.children)
                        p_vis = "public"
                        for c in item.children:
                            if c.type == "accessibility_modifier":
                                p_vis = c.text.decode("utf-8")
                        properties.append({
                            "name": p_name,
                            "type": p_type,
                            "value": p_val,
                            "visibility": p_vis,
                            "is_static": p_static,
                            "is_readonly": p_readonly,
                            "line": item.start_point[0] + 1,
                            "end_line": item.end_point[0] + 1,
                        })

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
                metadata={"renders": [], "props": [], "hooks_used": [], "start_line": line_num, "end_line": end_line},
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
                "type_parameters": type_params,
                "decorators": clean_decorators,
                "methods": methods,
                "method_details": method_details,
                "properties": properties,
                "is_service": is_service,
                "start_line": line_num,
                "end_line": end_line,
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
        prop_defaults: dict[str, str] = {}
        props_interface: str | None = None

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
                    raw_tag = name_node.text.decode("utf-8")
                    # Distinguish primitive HTML/SVG tags from custom React/Vue components
                    tag_base = raw_tag.split(".")[0]
                    if tag_base not in HTML_PRIMITIVE_TAGS and tag_base[0].isupper():
                        renders.add(raw_tag)
            for c in n.children:
                walk_comp(c)

        walk_comp(node)

        # Extract props destructuring, default values, and interface annotation if present
        param_node = node.child_by_field_name("parameters")
        if param_node:
            for p in param_node.children:
                if p.type in ("required_parameter", "optional_parameter"):
                    # Check props type annotation, e.g. ({ title }: Props) or (props: UserCardProps)
                    type_ann = p.child_by_field_name("type")
                    if type_ann:
                        raw_type = type_ann.text.decode("utf-8").lstrip(":").strip()
                        props_interface = raw_type

                    pattern = p.child_by_field_name("pattern")
                    if pattern and pattern.type == "object_pattern":
                        for oc in pattern.children:
                            if oc.type == "shorthand_property_identifier_pattern":
                                props.append(oc.text.decode("utf-8"))
                            elif oc.type == "object_assignment_pattern":
                                left = oc.child_by_field_name("left")
                                right = oc.child_by_field_name("right")
                                if left:
                                    p_name = left.text.decode("utf-8")
                                    props.append(p_name)
                                    if right:
                                        prop_defaults[p_name] = right.text.decode("utf-8")
                    elif pattern and pattern.type == "identifier":
                        # Plain identifier (e.g. `props`)
                        p_name = pattern.text.decode("utf-8")
                        if p_name not in props:
                            props.append(p_name)

        return ParsedSymbol(
            name=name,
            kind="component",
            line=line_num,
            end_line=end_line,
            is_exported=is_exported,
            metadata={
                "hooks_used": list(hooks_used),
                "props": props,
                "prop_defaults": prop_defaults,
                "props_interface": props_interface,
                "renders": list(renders)[:20],
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
                params=extract_route_params(path),
            ))

    def _extract_sig(self, node: Any, name: str) -> str:
        param_node = node.child_by_field_name("parameters")
        params_text = ""
        if param_node:
            params_text = param_node.text.decode("utf-8").strip("()")
        tp_node = node.child_by_field_name("type_parameters")
        tp_text = tp_node.text.decode("utf-8") if tp_node else ""
        ret_node = node.child_by_field_name("return_type")
        ret_text = f": {ret_node.text.decode('utf-8').lstrip(':').strip()}" if ret_node else ""
        return f"{name}{tp_text}({params_text}){ret_text}"

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

        # Detect Next.js 14 App Router endpoints
        nextjs_routes = extract_nextjs_app_routes(path, content)
        for nr in nextjs_routes:
            if not any(r.method == nr.method and r.path == nr.path for r in result.routes):
                result.routes.append(nr)

        result.components = self._extract_components_regex(content, lines)
        result.hooks = self._extract_hooks_regex(content)
        result.models = self._extract_models_regex(content, lines)
        result.variables = self._extract_variables_regex(content, lines)

        result.symbols = (
            result.functions + result.classes + result.interfaces
            + result.components + result.hooks + result.models
            + result.variables
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
                        c_info = classify_js_import(groups[4])
                        imports.append(ParsedImport(
                            source=groups[4],
                            names=names,
                            line=i + 1,
                            is_default=bool(groups[0] or groups[3]),
                            is_namespace=bool(groups[2]),
                            is_internal=c_info["is_internal"],
                            is_monorepo=c_info["is_monorepo"],
                            is_third_party=c_info["is_third_party"],
                        ))
                    elif groups and groups[0]:
                        c_info = classify_js_import(groups[0])
                        imports.append(ParsedImport(
                            source=groups[0],
                            line=i + 1,
                            is_internal=c_info["is_internal"],
                            is_monorepo=c_info["is_monorepo"],
                            is_third_party=c_info["is_third_party"],
                        ))
                    break

        for match in re.finditer(r"(?:const|let|var)\s+(?:(\w+)|\{([^}]+)\})\s*=\s*require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)", content):
            names = []
            if match.group(1):
                names.append(match.group(1))
            elif match.group(2):
                names.extend([n.strip() for n in match.group(2).split(",") if n.strip()])
            src = match.group(3)
            line = content[:match.start()].count("\n") + 1
            c_info = classify_js_import(src)
            imports.append(ParsedImport(
                source=src,
                names=names,
                line=line,
                is_internal=c_info["is_internal"],
                is_monorepo=c_info["is_monorepo"],
                is_third_party=c_info["is_third_party"],
            ))

        return imports

    def _extract_variables_regex(self, content: str, lines: list[str]) -> list[ParsedSymbol]:
        variables = []
        for match in re.finditer(r"(?:export\s+)?(const|let|var)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)(?:\s*:\s*([^=\n;]+))?\s*=\s*([^;\n]+)", content):
            is_const = match.group(1) == "const"
            name = match.group(2)
            val = match.group(4).strip()
            if "=>" in val or val.startswith("function") or val.startswith("async"):
                continue
            line_num = content[:match.start()].count("\n") + 1
            is_exported = "export" in content[max(0, match.start() - 20):match.start()]
            variables.append(ParsedSymbol(
                name=name,
                kind="constant" if is_const else "variable",
                line=line_num,
                end_line=line_num,
                is_exported=is_exported,
                metadata={
                    "is_const": is_const,
                    "type": match.group(3).strip() if match.group(3) else None,
                    "start_line": line_num,
                    "end_line": line_num,
                },
            ))
        return variables

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
        for m in re.finditer(r"export\s+\*\s+(?:as\s+(\w+)\s+)?from\s+['\"]([^'\"]+)['\"]", content):
            if m.group(1):
                exports.append(m.group(1))
            else:
                exports.append("*")
        for m in re.finditer(r"export\s+default\s+(?:(?:async\s+)?(?:function|class)\s+)?(\w+)?", content):
            if m.group(1):
                exports.append(m.group(1))
            exports.append("default")
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
                        params=extract_route_params(path),
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
                props_match = re.search(r"\(\s*\{([^}]*)\}(?:\s*:\s*(\w+))?", block)
                props = []
                prop_defaults = {}
                props_interface = props_match.group(2) if props_match and props_match.group(2) else None
                if props_match:
                    raw_props = [p.strip() for p in props_match.group(1).split(",") if p.strip()]
                    for p in raw_props:
                        if "=" in p:
                            p_name, p_def = p.split("=", 1)
                            p_clean = p_name.strip().split(":")[0].strip()
                            props.append(p_clean)
                            prop_defaults[p_clean] = p_def.strip()
                        else:
                            p_clean = p.split(":")[0].strip()
                            props.append(p_clean)

                raw_renders = re.findall(r"<([A-Za-z0-9_.]+)", block)
                renders = [
                    r for r in raw_renders
                    if r.split(".")[0] not in HTML_PRIMITIVE_TAGS and r.split(".")[0][0].isupper()
                ]

                components.append(ParsedSymbol(
                    name=name,
                    kind="component",
                    line=line_num,
                    end_line=end_line,
                    is_exported="export" in content[max(0, match.start()-30):match.start()],
                    metadata={
                        "hooks_used": list(set(hooks)),
                        "props": props,
                        "prop_defaults": prop_defaults,
                        "props_interface": props_interface,
                        "renders": list(set(renders))[:20],
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
