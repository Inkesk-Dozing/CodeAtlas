from services.ingestion.workspace_detector import (
    WorkspaceBoundaryDetector,
)


class TestWorkspaceBoundaryDetector:
    def setup_method(self):
        self.detector = WorkspaceBoundaryDetector()

    def test_detects_turborepo_pnpm_workspace(self):
        files = [
            "pnpm-workspace.yaml",
            "turbo.json",
            "package.json",
            "apps/web/package.json",
            "apps/api/package.json",
            "packages/shared/package.json",
        ]

        file_contents = {
            "package.json": '{"name": "root"}',
            "apps/web/package.json": '{"name": "@codeatlas/web", "dependencies": {"@codeatlas/shared": "workspace:*"}}',
            "apps/api/package.json": '{"name": "@codeatlas/api"}',
            "packages/shared/package.json": '{"name": "@codeatlas/shared"}',
        }

        result = self.detector.analyze_files(files, file_reader=lambda p: file_contents.get(p))
        assert result.is_monorepo is True
        assert result.manager == "pnpm"
        assert len(result.packages) == 4
        assert result.has_circular_dependencies is False

        # Dependency graph check
        assert "@codeatlas/shared" in result.dependency_graph["@codeatlas/web"]
        assert len(result.dependency_graph["@codeatlas/shared"]) == 0

    def test_detects_circular_dependencies_tarjan(self):
        # Package A -> Package B -> Package C -> Package A
        graph = {
            "pkg-a": ["pkg-b"],
            "pkg-b": ["pkg-c"],
            "pkg-c": ["pkg-a"],
            "pkg-d": ["pkg-a"],  # Dependent but not in cycle
        }

        cycles = self.detector.detect_circular_dependencies(graph)
        assert len(cycles) == 1
        cycle = cycles[0]
        assert cycle.length == 3
        assert set(cycle.cycle[:-1]) == {"pkg-a", "pkg-b", "pkg-c"}
        assert "Circular dependency cycle detected" in cycle.description

    def test_detects_multiple_independent_cycles(self):
        # Cycle 1: X <-> Y
        # Cycle 2: M <-> N
        graph = {
            "x": ["y"],
            "y": ["x"],
            "m": ["n"],
            "n": ["m"],
            "z": ["x", "m"],
        }

        cycles = self.detector.detect_circular_dependencies(graph)
        assert len(cycles) == 2
        lengths = [c.length for c in cycles]
        assert lengths == [2, 2]

    def test_no_cycle_in_dag(self):
        # Strict DAG: A -> B -> C
        graph = {
            "pkg-a": ["pkg-b", "pkg-c"],
            "pkg-b": ["pkg-c"],
            "pkg-c": [],
        }

        cycles = self.detector.detect_circular_dependencies(graph)
        assert len(cycles) == 0

    def test_detects_self_referential_cycle(self):
        graph = {
            "loop-pkg": ["loop-pkg"],
        }

        cycles = self.detector.detect_circular_dependencies(graph)
        assert len(cycles) == 1
        assert cycles[0].length == 1
        assert "Self-referential" in cycles[0].description

