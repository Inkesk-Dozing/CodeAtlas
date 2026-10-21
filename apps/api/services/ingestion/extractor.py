import hashlib
import uuid
from typing import Any

from parsers.base import ParseResult


class GraphExtractor:
    def __init__(self, repo_id: str):
        self.repo_id = repo_id
        self.nodes: list[dict] = []
        self.edges: list[dict] = []
        self._path_map: dict[str, str] = {}

    def extract(self, parsed_files: list[dict[str, Any]]) -> tuple[list[dict], list[dict]]:
        self._create_directory_nodes(parsed_files)
        self._create_file_nodes(parsed_files)
        self._create_symbol_nodes(parsed_files)
        self._create_import_edges(parsed_files)
        self._create_class_hierarchy_edges(parsed_files)
        self._create_route_edges(parsed_files)
        self._create_component_edges(parsed_files)
        self._create_containment_edges(parsed_files)

        return self.nodes, self.edges

    def _node_id(self) -> str:
        return str(uuid.uuid4())

    def _add_node(self, node_type: str, name: str, path: str, **kwargs) -> str:
        node_id = self._node_id()
        key = f"{path}::{name}::{node_type}"
        self._path_map[key] = node_id

        self.nodes.append({
            "id": node_id,
            "type": node_type,
            "name": name,
            "path": path,
            "language": kwargs.pop("language", None),
            "metadata": kwargs.pop("metadata", {}),
            "summary": kwargs.pop("summary", None),
            "content_hash": kwargs.pop("content_hash", None),
            "embedding": None,
        })
        return node_id

    def _add_edge(self, source_key: str, target_key: str, edge_type: str, weight: float = 1.0, **metadata):
        self.edges.append({
            "id": str(uuid.uuid4()),
            "source_key": source_key,
            "target_key": target_key,
            "type": edge_type,
            "weight": weight,
            "metadata": metadata,
        })

    def _create_directory_nodes(self, files: list[dict]):
        dirs: set[str] = set()
        for f in files:
            parts = f["path"].split("/")
            for i in range(1, len(parts)):
                dirs.add("/".join(parts[:i]))

        for d in sorted(dirs):
            name = d.split("/")[-1]
            self._add_node("directory", name, d, language=None)

    def _create_file_nodes(self, files: list[dict]):
        for f in files:
            path = f["path"]
            name = path.split("/")[-1]
            content = f.get("content", "")
            content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

            self._add_node(
                "file", name, path,
                language=f.get("language"),
                metadata={"loc": len(content.splitlines()), "size": len(content)},
                content_hash=content_hash,
            )

    def _create_symbol_nodes(self, files: list[dict]):
        for f in files:
            parsed: ParseResult | None = f.get("parsed")
            if parsed is None:
                continue

            path = f["path"]
            language = f.get("language")

            for fn in parsed.functions:
                is_component = fn.name[0].isupper() if fn.name else False
                node_type = "function"
                if is_component:
                    node_type = "component"
                if fn.metadata.get("is_route"):
                    node_type = "controller"

                self._add_node(
                    node_type, fn.name, path,
                    language=language,
                    metadata={
                        "loc": max(0, (fn.end_line or fn.line) - fn.line + 1),
                        "signature": fn.signature,
                        "docstring": fn.docstring,
                        "is_async": fn.is_async,
                        "is_exported": fn.is_exported,
                        "line": fn.line,
                        **fn.metadata,
                    },
                )

            for cls in parsed.classes:
                self._add_node(
                    "class", cls.name, path,
                    language=language,
                    metadata={
                        "loc": max(0, (cls.end_line or cls.line) - cls.line + 1),
                        "docstring": cls.docstring,
                        "is_exported": cls.is_exported,
                        "line": cls.line,
                        **cls.metadata,
                    },
                )

            for iface in parsed.interfaces:
                self._add_node(
                    "interface", iface.name, path,
                    language=language,
                    metadata={"is_exported": iface.is_exported, "line": iface.line},
                )

            for comp in parsed.components:
                self._add_node(
                    "component", comp.name, path,
                    language=language,
                    metadata={
                        "loc": max(0, (comp.end_line or comp.line) - comp.line + 1),
                        "is_exported": comp.is_exported,
                        "line": comp.line,
                        **comp.metadata,
                    },
                )

            for hook in parsed.hooks:
                self._add_node(
                    "hook", hook.name, path,
                    language=language,
                    metadata={"is_exported": hook.is_exported, "line": hook.line},
                )

            for model in parsed.models:
                self._add_node(
                    "model", model.name, path,
                    language=language,
                    metadata={"line": model.line, **model.metadata},
                )

            for route in parsed.routes:
                self._add_node(
                    "route", f"{route.method} {route.path}", path,
                    language=language,
                    metadata={
                        "http_method": route.method,
                        "route_path": route.path,
                        "controller": route.handler,
                        "framework": route.framework,
                        "middleware": route.middleware,
                        "line": route.line,
                    },
                )

    def _create_import_edges(self, files: list[dict]):
        for f in files:
            parsed: ParseResult | None = f.get("parsed")
            if parsed is None:
                continue

            source_path = f["path"]
            source_dir = "/".join(source_path.split("/")[:-1])

            for imp in parsed.imports:
                resolved = self._resolve_import(source_dir, imp.source, files)
                if resolved and resolved != source_path:
                    source_key = f"{source_path}::{'/'.join(source_path.split('/')[-1])}::file"
                    target_key = f"{resolved}::{'/'.join(resolved.split('/')[-1])}::file"
                    self._add_edge(source_key, target_key, "imports", metadata={"symbols": imp.names})

    def _create_class_hierarchy_edges(self, files: list[dict]):
        for f in files:
            parsed: ParseResult | None = f.get("parsed")
            if parsed is None:
                continue

            path = f["path"]
            for cls in parsed.classes:
                source_key = f"{path}::{cls.name}::class"
                extends = cls.metadata.get("extends")
                if extends:
                    target_key = f"{path}::{extends}::class"
                    self._add_edge(source_key, target_key, "extends")

                for impl in cls.metadata.get("implements", []):
                    target_key = f"{path}::{impl}::interface"
                    self._add_edge(source_key, target_key, "implements")

    def _create_route_edges(self, files: list[dict]):
        for f in files:
            parsed: ParseResult | None = f.get("parsed")
            if parsed is None:
                continue

            path = f["path"]
            for route in parsed.routes:
                route_key = f"{path}::{route.method} {route.path}::route"
                if route.handler:
                    handler_key = f"{path}::{route.handler}::function"
                    self._add_edge(route_key, handler_key, "routes_to")

                for mw in route.middleware:
                    mw_key = f"{path}::{mw}::function"
                    self._add_edge(mw_key, route_key, "middleware_for")

    def _create_component_edges(self, files: list[dict]):
        for f in files:
            parsed: ParseResult | None = f.get("parsed")
            if parsed is None:
                continue

            path = f["path"]
            for comp in parsed.components:
                comp_key = f"{path}::{comp.name}::component"

                for child in comp.metadata.get("renders", []):
                    child_key = f"{path}::{child}::component"
                    self._add_edge(comp_key, child_key, "renders")

                for hook in comp.metadata.get("hooks_used", []):
                    hook_key = f"{path}::{hook}::hook"
                    self._add_edge(comp_key, hook_key, "uses_hook")

    def _create_containment_edges(self, files: list[dict]):
        dir_keys: dict[str, str] = {}
        for node in self.nodes:
            if node["type"] == "directory":
                dir_keys[node["path"]] = f"{node['path']}::{node['name']}::directory"

        for node in self.nodes:
            if node["type"] == "file":
                parent = "/".join(node["path"].split("/")[:-1])
                if parent and parent in dir_keys:
                    file_key = f"{node['path']}::{node['name']}::file"
                    self._add_edge(dir_keys[parent], file_key, "contains")

    @staticmethod
    def _resolve_import(source_dir: str, import_src: str, files: list[dict]) -> str | None:
        if not import_src.startswith("."):
            return None

        parts = source_dir.split("/") if source_dir else []
        import_parts = import_src.split("/")

        for p in import_parts:
            if p == "..":
                if parts:
                    parts.pop()
            elif p == ".":
                continue
            else:
                parts.append(p)

        base = "/".join(parts)
        file_set = {f["path"] for f in files}

        candidates = [
            f"{base}.ts", f"{base}.tsx", f"{base}.js", f"{base}.jsx",
            f"{base}.py", f"{base}/index.ts", f"{base}/index.tsx",
            f"{base}/index.js", f"{base}/__init__.py",
        ]
        for c in candidates:
            if c in file_set:
                return c
        return None
