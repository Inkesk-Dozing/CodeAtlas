import json
import os
from dataclasses import dataclass, field


@dataclass
class WorkspacePackage:
    name: str
    path: str
    version: str = "0.0.0"
    dependencies: list[str] = field(default_factory=list)
    dev_dependencies: list[str] = field(default_factory=list)
    peer_dependencies: list[str] = field(default_factory=list)


@dataclass
class CircularDependencyCycle:
    cycle: list[str]
    length: int
    severity: str = "warning"
    description: str = ""


@dataclass
class WorkspaceAnalysisResult:
    is_monorepo: bool
    manager: str | None = None
    packages: list[WorkspacePackage] = field(default_factory=list)
    dependency_graph: dict[str, list[str]] = field(default_factory=dict)
    cycles: list[CircularDependencyCycle] = field(default_factory=list)
    has_circular_dependencies: bool = False


class WorkspaceBoundaryDetector:
    """
    Detects monorepo workspace boundaries (pnpm workspaces, Turborepo, Nx, Lerna, Cargo, Go workspaces),
    resolves internal package dependency topologies, and runs Tarjan's Strongly Connected Components
    algorithm to identify circular package dependency cycles.
    """

    def analyze_files(self, file_paths: list[str], file_reader=None) -> WorkspaceAnalysisResult:
        """
        Analyzes a repository based on a list of relative file paths and optional reader function.
        """
        file_set = set(file_paths)
        is_monorepo = False
        manager = None

        if "pnpm-workspace.yaml" in file_set:
            is_monorepo = True
            manager = "pnpm"
        elif "turbo.json" in file_set:
            is_monorepo = True
            manager = "turborepo"
        elif "nx.json" in file_set:
            is_monorepo = True
            manager = "nx"
        elif "lerna.json" in file_set:
            is_monorepo = True
            manager = "lerna"
        elif "Cargo.toml" in file_set:
            # Check if root Cargo.toml declares [workspace]
            manager = "cargo"

        # Discover all package.json files across the workspace
        pkg_json_files = [p for p in file_paths if p.endswith("package.json") and "node_modules" not in p]
        if len(pkg_json_files) > 1:
            is_monorepo = True
            if not manager:
                manager = "npm/yarn"

        packages: list[WorkspacePackage] = []
        name_to_pkg: dict[str, WorkspacePackage] = {}

        for pkg_path in pkg_json_files:
            content = file_reader(pkg_path) if file_reader else None
            if not content:
                continue

            try:
                data = json.loads(content)
                name = data.get("name")
                if not name:
                    continue

                pkg_dir = os.path.dirname(pkg_path).replace("\\", "/") or "."
                deps = list(data.get("dependencies", {}).keys())
                dev_deps = list(data.get("devDependencies", {}).keys())
                peer_deps = list(data.get("peerDependencies", {}).keys())

                pkg = WorkspacePackage(
                    name=name,
                    path=pkg_dir,
                    version=data.get("version", "0.0.0"),
                    dependencies=deps,
                    dev_dependencies=dev_deps,
                    peer_dependencies=peer_deps,
                )
                packages.append(pkg)
                name_to_pkg[name] = pkg
            except Exception:
                continue

        # Build intra-workspace dependency graph
        workspace_names = set(name_to_pkg.keys())
        dependency_graph: dict[str, list[str]] = {name: [] for name in workspace_names}

        for name, pkg in name_to_pkg.items():
            all_deps = pkg.dependencies + pkg.dev_dependencies + pkg.peer_dependencies
            internal_deps = [d for d in all_deps if d in workspace_names and d != name]
            dependency_graph[name] = sorted(set(internal_deps))

        # Run Tarjan's SCC to detect circular dependencies
        cycles = self.detect_circular_dependencies(dependency_graph)

        return WorkspaceAnalysisResult(
            is_monorepo=is_monorepo,
            manager=manager,
            packages=packages,
            dependency_graph=dependency_graph,
            cycles=cycles,
            has_circular_dependencies=len(cycles) > 0,
        )

    @staticmethod
    def detect_circular_dependencies(graph: dict[str, list[str]]) -> list[CircularDependencyCycle]:
        """
        Tarjan's algorithm for finding strongly connected components (SCCs) of size >= 2
        representing circular dependency cycles, plus self-loops.
        """
        index = 0
        indices: dict[str, int] = {}
        lowlinks: dict[str, int] = {}
        on_stack: dict[str, bool] = {}
        stack: list[str] = []
        sccs: list[list[str]] = []

        def strongconnect(node: str):
            nonlocal index
            indices[node] = index
            lowlinks[node] = index
            index += 1
            stack.append(node)
            on_stack[node] = True

            for neighbor in graph.get(node, []):
                if neighbor not in indices:
                    strongconnect(neighbor)
                    lowlinks[node] = min(lowlinks[node], lowlinks[neighbor])
                elif on_stack.get(neighbor, False):
                    lowlinks[node] = min(lowlinks[node], indices[neighbor])

            if lowlinks[node] == indices[node]:
                scc = []
                while True:
                    w = stack.pop()
                    on_stack[w] = False
                    scc.append(w)
                    if w == node:
                        break
                sccs.append(scc)

        for node in graph:
            if node not in indices:
                strongconnect(node)

        # Filter SCCs with cycles (length >= 2, or self-loop)
        detected_cycles: list[CircularDependencyCycle] = []
        for scc in sccs:
            if len(scc) > 1:
                # Cycle with multiple nodes
                cycle_nodes = list(reversed(scc))
                cycle_nodes.append(cycle_nodes[0])  # Close the loop representation
                cycle_str = " -> ".join(cycle_nodes)
                detected_cycles.append(
                    CircularDependencyCycle(
                        cycle=cycle_nodes,
                        length=len(scc),
                        severity="error" if len(scc) <= 3 else "warning",
                        description=f"Circular dependency cycle detected: {cycle_str}",
                    )
                )
            elif len(scc) == 1:
                # Self-loop check
                node = scc[0]
                if node in graph.get(node, []):
                    detected_cycles.append(
                        CircularDependencyCycle(
                            cycle=[node, node],
                            length=1,
                            severity="error",
                            description=f"Self-referential circular dependency detected on package {node}",
                        )
                    )

        return detected_cycles

