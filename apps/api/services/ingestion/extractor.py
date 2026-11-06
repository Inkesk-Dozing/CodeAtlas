import hashlib
import re
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
        self._create_orm_model_edges(parsed_files)
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
                        "params": route.params,
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
            # Link methods to their parent struct or class
            for fn in parsed.functions:
                parent_struct = fn.metadata.get("receiver") or (fn.parent if fn.kind == "method" else None)
                if parent_struct:
                    method_key = f"{path}::{fn.name}::function"
                    struct_key = f"{path}::{parent_struct}::class"
                    self._add_edge(struct_key, method_key, "declares_method")

            for cls in parsed.classes:
                source_key = f"{path}::{cls.name}::class"
                extends = cls.metadata.get("extends")
                if extends:
                    target_key = f"{path}::{extends}::class"
                    self._add_edge(source_key, target_key, "extends")

                for embedded in cls.metadata.get("embedded", []):
                    target_key = f"{path}::{embedded}::class"
                    self._add_edge(source_key, target_key, "embeds")

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
                    # Add primary routes_to edge
                    self._add_edge(route_key, handler_key, "routes_to")
                    # Also add handles_route edge from controller function to route per specification
                    self._add_edge(handler_key, route_key, "handles_route")

                for mw in route.middleware:
                    mw_key = f"{path}::{mw}::function"
                    self._add_edge(mw_key, route_key, "middleware_for")

    def _create_component_edges(self, files: list[dict]):
        # Index components and hooks across all files
        # Map: name -> list of node_keys (to support local file matches and cross-file matches)
        component_nodes: dict[str, list[str]] = {}
        hook_nodes: dict[str, list[str]] = {}

        for f in files:
            parsed: ParseResult | None = f.get("parsed")
            if parsed is None:
                continue
            path = f["path"]
            for comp in parsed.components:
                c_key = f"{path}::{comp.name}::component"
                component_nodes.setdefault(comp.name, []).append(c_key)
            for hk in parsed.hooks:
                h_key = f"{path}::{hk.name}::hook"
                hook_nodes.setdefault(hk.name, []).append(h_key)

        for f in files:
            parsed: ParseResult | None = f.get("parsed")
            if parsed is None:
                continue

            path = f["path"]
            source_dir = "/".join(path.split("/")[:-1])
            # Check imports in this file to prioritize cross-file imported targets
            imported_symbols: dict[str, str] = {}
            for imp in parsed.imports:
                resolved_path = self._resolve_import(source_dir, imp.source, files)
                if resolved_path:
                    for name in imp.names:
                        imported_symbols[name] = resolved_path

            for comp in parsed.components:
                comp_key = f"{path}::{comp.name}::component"

                for child in comp.metadata.get("renders", []):
                    # Handle namespaced components (e.g. CustomModal.Header -> CustomModal)
                    child_base = child.split(".")[0]
                    target_key = None

                    # 1. Match from explicit import
                    if child_base in imported_symbols:
                        target_path = imported_symbols[child_base]
                        target_key = f"{target_path}::{child_base}::component"
                    # 2. Match from same file
                    elif any(k.startswith(f"{path}::") for k in component_nodes.get(child_base, [])):
                        target_key = f"{path}::{child_base}::component"
                    # 3. Match globally across repo
                    elif component_nodes.get(child_base):
                        target_key = component_nodes[child_base][0]
                    else:
                        # Fallback key in current file scope
                        target_key = f"{path}::{child}::component"

                    if target_key and target_key != comp_key:
                        self._add_edge(comp_key, target_key, "renders")

                for hook in comp.metadata.get("hooks_used", []):
                    target_key = None
                    # 1. Match from explicit import
                    if hook in imported_symbols:
                        target_path = imported_symbols[hook]
                        target_key = f"{target_path}::{hook}::hook"
                    # 2. Match from same file
                    elif any(k.startswith(f"{path}::") for k in hook_nodes.get(hook, [])):
                        target_key = f"{path}::{hook}::hook"
                    # 3. Match globally across repo
                    elif hook_nodes.get(hook):
                        target_key = hook_nodes[hook][0]
                    else:
                        # Fallback key in current file scope
                        target_key = f"{path}::{hook}::hook"

                    if target_key:
                        self._add_edge(comp_key, target_key, "uses_hook")

    def _create_orm_model_edges(self, files: list[dict]):
        # Index all models across files by name
        model_map: dict[str, str] = {}
        for f in files:
            parsed: ParseResult | None = f.get("parsed")
            if not parsed:
                continue
            path = f["path"]
            for m in parsed.models:
                # Key by model name (case-insensitive and exact)
                model_key = f"{path}::{m.name}::model"
                model_map[m.name] = model_key
                model_map[m.name.lower()] = model_key
                # Also plural/singular forms if applicable
                if m.name.endswith("s"):
                    model_map[m.name[:-1].lower()] = model_key
                else:
                    model_map[f"{m.name.lower()}s"] = model_key

        # 1. Connect model-to-model foreign keys & relations
        for f in files:
            parsed: ParseResult | None = f.get("parsed")
            if not parsed:
                continue
            path = f["path"]
            for m in parsed.models:
                source_key = f"{path}::{m.name}::model"
                foreign_keys = m.metadata.get("foreign_keys", [])
                for fk in foreign_keys:
                    target_model = fk.get("target_model")
                    if target_model and target_model in model_map:
                        target_key = model_map[target_model]
                        if source_key != target_key:
                            self._add_edge(
                                source_key,
                                target_key,
                                "references_model",
                                weight=1.0,
                                foreign_key=fk.get("column"),
                                target_column=fk.get("target_column", "id"),
                            )

                relations = m.metadata.get("relations", [])
                for rel in relations:
                    target_model = rel.get("target_model")
                    if target_model and target_model in model_map:
                        target_key = model_map[target_model]
                        if source_key != target_key:
                            # Avoid duplicate edge if already added by foreign_keys
                            exists = any(
                                e["source_key"] == source_key
                                and e["target_key"] == target_key
                                and e["type"] == "references_model"
                                for e in self.edges
                            )
                            if not exists:
                                self._add_edge(
                                    source_key,
                                    target_key,
                                    "references_model",
                                    weight=1.0,
                                    relation_field=rel.get("field"),
                                    relation_type=rel.get("type", "relation"),
                                )

        # 2. Connect API endpoints / routes to the database models they query or mutate
        for f in files:
            parsed: ParseResult | None = f.get("parsed")
            if not parsed:
                continue
            path = f["path"]
            content = f.get("content", "")

            for route in parsed.routes:
                route_key = f"{path}::{route.method} {route.path}::route"
                handler_name = route.handler
                route_path_tokens = set(re.findall(r"\w+", route.path.lower()))

                for model_name, target_key in model_map.items():
                    # Only check primary canonical model names (avoid case variants duplicate checking)
                    if not model_name[0].isupper():
                        continue

                    model_lower = model_name.lower()
                    # Determine if route or handler queries or mutates model
                    is_related = (
                        model_lower in route_path_tokens
                        or (handler_name and model_lower in handler_name.lower())
                    )

                    if not is_related and content and re.search(rf"\b{model_name}\b", content):
                        # Scoped occurrence
                        is_related = True

                    if is_related:
                        edge_type = "mutates_model" if route.method.upper() in ("POST", "PUT", "PATCH", "DELETE") else "queries_model"
                        # Verify we haven't already linked this route to this model
                        exists = any(
                            e["source_key"] == route_key
                            and e["target_key"] == target_key
                            for e in self.edges
                        )
                        if not exists:
                            self._add_edge(
                                route_key,
                                target_key,
                                edge_type,
                                weight=1.0,
                                method=route.method,
                            )

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
