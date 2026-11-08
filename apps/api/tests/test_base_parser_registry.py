"""Unit tests for Base AST Parser Framework & Multi-Language Dispatch Registry (Issue #24)."""


from parsers import (
    BaseParser,
    FallbackParser,
    GoParser,
    JavaScriptParser,
    JavaSpringParser,
    ParsedFile,
    ParsedSymbol,
    ParseResult,
    ParserRegistry,
    PrismaParser,
    PythonParser,
    RustParser,
    SymbolKind,
    get_fallback_parser,
    get_parser,
    get_parser_for_file,
)


def test_standardized_symbol_kinds():
    assert SymbolKind.FUNCTION == "function"
    assert SymbolKind.CLASS == "class"
    assert SymbolKind.MODULE == "module"
    assert SymbolKind.ROUTE == "route"
    assert SymbolKind.COMPONENT == "component"
    assert SymbolKind.MODEL == "model"


def test_parse_result_to_nodes_and_edges():
    result = ParseResult(
        loc=42,
        path="src/services/user.py",
        symbols=[
            ParsedSymbol(name="UserService", kind=SymbolKind.CLASS, line=10, end_line=30),
            ParsedSymbol(name="get_user", kind=SymbolKind.FUNCTION, line=15, end_line=25, parent="UserService"),
        ],
    )
    # Check alias compatibility
    assert isinstance(result, ParsedFile)
    assert isinstance(result, ParseResult)

    nodes = result.nodes
    assert len(nodes) >= 3  # module node + class + function
    node_names = {n.name for n in nodes}
    assert "user.py" in node_names
    assert "UserService" in node_names
    assert "get_user" in node_names

    module_node = next(n for n in nodes if n.kind == SymbolKind.MODULE)
    assert module_node.path == "src/services/user.py"
    assert module_node.metadata["loc"] == 42


def test_base_parser_helper_methods():
    class DummyParser(BaseParser):
        def parse(self, content: str, path: str) -> ParseResult:
            return ParseResult(
                loc=self._count_loc(content),
                path=path,
                exports=["exported_fn"],
                symbols=[ParsedSymbol(name="exported_fn", kind=SymbolKind.FUNCTION, line=1, end_line=3)],
            )

    parser = DummyParser()
    content = "def exported_fn():\n    pass\n"
    nodes = parser.extract_nodes(content, "dummy.py")
    exports = parser.extract_exports(content, "dummy.py")
    imports = parser.extract_imports(content, "dummy.py")
    edges = parser.extract_edges(content, "dummy.py")

    assert any(n.name == "exported_fn" for n in nodes)
    assert "exported_fn" in exports
    assert imports == []
    assert isinstance(edges, list)


def test_parser_registry_o1_extension_routing():
    registry = ParserRegistry()

    # Python extensions
    assert isinstance(registry.get_parser_for_file("app/main.py"), PythonParser)
    assert isinstance(registry.get_parser_for_file("types.pyi"), PythonParser)

    # TypeScript and JavaScript
    assert isinstance(registry.get_parser_for_file("src/index.ts"), JavaScriptParser)
    assert isinstance(registry.get_parser_for_file("components/App.tsx"), JavaScriptParser)
    assert isinstance(registry.get_parser_for_file("server.js"), JavaScriptParser)
    assert isinstance(registry.get_parser_for_file("ui.jsx"), JavaScriptParser)
    assert isinstance(registry.get_parser_for_file("module.mjs"), JavaScriptParser)
    assert isinstance(registry.get_parser_for_file("bundle.cjs"), JavaScriptParser)

    # Go and Rust
    assert isinstance(registry.get_parser_for_file("cmd/server/main.go"), GoParser)
    assert isinstance(registry.get_parser_for_file("src/lib.rs"), RustParser)

    # Java / Spring and Prisma
    assert isinstance(registry.get_parser_for_file("src/main/UserController.java"), JavaSpringParser)
    assert isinstance(registry.get_parser_for_file("prisma/schema.prisma"), PrismaParser)


def test_graceful_fallback_for_unsupported_files():
    registry = ParserRegistry()

    # Unsupported languages should gracefully route to FallbackParser
    fallback_1 = registry.get_parser_for_file("report.txt")
    assert isinstance(fallback_1, FallbackParser)

    fallback_2 = registry.get_parser_for_file("legacy.cobol")
    assert isinstance(fallback_2, FallbackParser)

    fallback_3 = registry.get_parser_for_file("settings.env")
    assert isinstance(fallback_3, FallbackParser)

    # Fallback parser extracts LOC and key-value properties without errors
    env_content = """
# Configuration File
APP_NAME = CodeAtlas
PORT = 8080
DEBUG = true
"""
    result = fallback_3.parse(env_content, "settings.env")
    assert result.loc == 3
    var_names = [v.name for v in result.variables]
    assert "APP_NAME" in var_names
    assert "PORT" in var_names
    assert "DEBUG" in var_names


def test_global_helper_functions():
    # Backward-compatible get_parser
    assert isinstance(get_parser("python"), PythonParser)
    assert isinstance(get_parser("typescript"), JavaScriptParser)
    assert isinstance(get_parser("golang"), GoParser)
    assert isinstance(get_parser("rs"), RustParser)
    assert get_parser("unknown_lang") is None

    # Global get_parser_for_file
    assert isinstance(get_parser_for_file("test.py"), PythonParser)
    assert isinstance(get_parser_for_file("unknown.xyz"), FallbackParser)

    # Global get_fallback_parser
    assert isinstance(get_fallback_parser(), FallbackParser)


def test_registry_custom_registration():
    registry = ParserRegistry()

    class CustomCobolParser(BaseParser):
        def parse(self, content: str, path: str) -> ParseResult:
            return ParseResult(loc=10, path=path)

    custom_parser = CustomCobolParser()
    registry.register(".cbl", custom_parser)
    assert registry.get_parser_for_file("program.cbl") is custom_parser
    assert registry.get_parser(".cbl") is custom_parser
