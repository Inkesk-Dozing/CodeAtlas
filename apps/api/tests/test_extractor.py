from services.ingestion.extractor import GraphExtractor


def _files_fixture() -> list[dict]:
    from parsers.javascript import JavaScriptParser

    parser = JavaScriptParser()

    app_code = """
    import { LoginPage } from './LoginPage';
    export function App() { return <LoginPage />; }
    """
    login_code = """
    export function LoginPage() { return <form />; }
    """

    return [
        {"path": "src/App.tsx", "language": "typescript", "content": app_code,
         "parsed": parser.parse(app_code, "src/App.tsx")},
        {"path": "src/LoginPage.tsx", "language": "typescript", "content": login_code,
         "parsed": parser.parse(login_code, "src/LoginPage.tsx")},
    ]


class TestGraphExtractor:
    def test_extract_produces_nodes_and_edges(self):
        ex = GraphExtractor(repo_id="r1")
        nodes, edges = ex.extract(_files_fixture())
        assert len(nodes) > 0
        assert len(edges) > 0
        assert nodes is ex.nodes and edges is ex.edges

    def test_creates_directory_and_file_nodes(self):
        ex = GraphExtractor(repo_id="r1")
        nodes, _ = ex.extract(_files_fixture())
        types = [n["type"] for n in nodes]
        assert "directory" in types
        assert "file" in types
        assert "function" in types or "component" in types

    def test_file_node_metadata(self):
        ex = GraphExtractor(repo_id="r1")
        nodes, _ = ex.extract(_files_fixture())
        file_node = next(n for n in nodes if n["type"] == "file" and n["path"] == "src/App.tsx")
        assert file_node["metadata"]["loc"] > 0
        assert file_node["content_hash"]
        assert file_node["language"] == "typescript"

    def test_contains_edges_link_dir_to_file(self):
        ex = GraphExtractor(repo_id="r1")
        _, edges = ex.extract(_files_fixture())
        assert any(e["type"] == "contains" for e in edges)

    def test_relative_import_edge_created(self):
        ex = GraphExtractor(repo_id="r1")
        _, edges = ex.extract(_files_fixture())
        assert any(e["type"] == "imports" for e in edges)

    def test_edges_carry_keys(self):
        ex = GraphExtractor(repo_id="r1")
        _, edges = ex.extract(_files_fixture())
        for e in edges:
            assert "::" in e["source_key"]
            assert "::" in e["target_key"]
            assert e["id"]


class TestResolveImport:
    def test_relative_import_resolves(self):
        files = [
            {"path": "src/components/Button.tsx"},
            {"path": "src/components/index.ts"},
        ]
        resolved = GraphExtractor._resolve_import("src/components", "./Button", files)
        assert resolved == "src/components/Button.tsx"

    def test_parent_import_resolves(self):
        files = [{"path": "src/utils.ts"}]
        resolved = GraphExtractor._resolve_import("src/components", "../utils", files)
        assert resolved == "src/utils.ts"

    def test_package_import_ignored(self):
        assert GraphExtractor._resolve_import("src", "react", [{"path": "src/a.ts"}]) is None

    def test_unresolved_import(self):
        assert GraphExtractor._resolve_import("src", "./missing", [{"path": "src/a.ts"}]) is None
