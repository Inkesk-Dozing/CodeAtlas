# CodeAtlas - Testing Strategy

## Overview
Pytest (backend), Vitest (frontend), Playwright (E2E), plus specialized pipeline tests. Target: 80%+ coverage.

---

## Test Pyramid

```
                    ┌─────────────┐
                    │   E2E (10)  │  Playwright
                   ┌┴─────────────┴┐
                   │ Integration(30)│  Pytest + Testcontainers
                  ┌┴───────────────┴┐
                  │   Unit (60+)     │  Pytest / Vitest
                 └┴─────────────────┘
```

---

## Backend Tests (Pytest)

### Directory Structure
```
apps/api/tests/
├── conftest.py
├── unit/
│   ├── test_parsers/
│   │   ├── test_typescript.py
│   │   ├── test_python.py
│   │   ├── test_go.py
│   │   └── test_extracts.py
│   ├── test_issue_mapping/
│   │   ├── test_analyzer.py
│   │   ├── test_ranker.py
│   │   └── test_patterns.py
│   ├── test_embeddings/
│   │   └── test_builder.py
│   └── test_graph/
│       ├── test_clustering.py
│       └── test_layout.py
├── integration/
│   ├── test_ingestion_pipeline.py
│   ├── test_api_endpoints.py
│   ├── test_webhooks.py
│   └── test_semantic_search.py
├── performance/
│   ├── test_ingestion_perf.py
│   └── test_search_perf.py
└── fixtures/
    ├── repos/
    │   ├── typescript-monorepo/
    │   ├── python-fastapi/
    │   └── go-service/
    └── issues/
        ├── bug_fix.json
        └── feature_add.json
```

### conftest.py
```python
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

@pytest_asyncio.fixture
async def db_session(engine):
    """Test database session with transaction rollback."""
    async with AsyncSession(engine) as session:
        yield session
        await session.rollback()

@pytest_asyncio.fixture
async def client(app, db_session):
    """Test HTTP client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def sample_repo(fixture_repo_path):
    """Path to sample repository fixture."""
    return fixture_repo_path / "typescript-monorepo"

@pytest.fixture
def sample_issue():
    """Sample GitHub issue for mapping tests."""
    return {
        "number": 123,
        "title": "Fix authentication middleware not running",
        "body": "The auth middleware in src/middleware/auth.ts is not being called for /api/users routes.",
        "labels": ["bug"],
    }
```

### Parser Unit Tests
```python
# tests/unit/test_parsers/test_typescript.py
import pytest
from api.parsers.typescript import TypeScriptParser

class TestTypeScriptParser:
    @pytest.fixture
    def parser(self):
        return TypeScriptParser()

    def test_extract_imports(self, parser):
        code = """
        import { UserService } from './services/user';
        import defaultExport from './utils/helper';
        import * as utils from './lib/utils';
        """
        imports = parser.extract_imports(code)
        assert len(imports) == 3
        assert "UserService" in [i.name for i in imports]
        assert any(i.is_default for i in imports)
        assert any(i.is_namespace for i in imports)

    def test_extract_functions(self, parser):
        code = """
        export function authenticate(token: string): boolean {
            return verify(token);
        }
        const getUser = async (id: number) => {
            return db.find(id);
        };
        """
        functions = parser.extract_functions(code)
        assert len(functions) == 2
        assert functions[0].name == "authenticate"
        assert functions[0].is_async is False
        assert functions[1].is_async is True

    def test_extract_classes(self, parser):
        code = """
        export class UserService extends BaseService implements interface IUserService {
            private db: Database;
            
            async createUser(data: UserData): Promise<User> {
                return this.db.insert(data);
            }
        }
        """
        classes = parser.extract_classes(code)
        assert len(classes) == 1
        assert classes[0].name == "UserService"
        assert classes[0].extends == "BaseService"
        assert len(classes[0].methods) == 1

    def test_extract_routes_express(self, parser):
        code = """
        router.get('/api/users', authenticate, getUsers);
        router.post('/api/users', validateBody, createUser);
        app.delete('/api/users/:id', deleteUser);
        """
        routes = parser.extract_routes(code, framework="express")
        assert len(routes) == 3
        assert routes[0].method == "GET"
        assert routes[0].path == "/api/users"
        assert routes[0].middleware == ["authenticate"]

    def test_extract_react_components(self, parser):
        code = """
        export function UserProfile({ userId }: Props) {
            const [user, setUser] = useState(null);
            useEffect(() => { fetchUser(userId); }, [userId]);
            return <div>{user.name}</div>;
        }
        
        const Header = () => <nav>...</nav>;
        """
        components = parser.extract_components(code)
        assert len(components) == 2
        assert components[0].name == "UserProfile"
        assert "useState" in components[0].hooks

    def test_handle_syntax_errors(self, parser):
        """Parser should not crash on invalid code."""
        code = "function broken( { incomplete"
        result = parser.parse(code, "test.ts")
        # Should return partial results, not raise
        assert result is not None

    @pytest.mark.parametrize("code,expected", [
        ("const x = 1;", 1),        # Simple
        ("export default class Foo {}", 1),
        ("interface Bar { x: number }", 1),
        ("type Baz = string | number", 1),
    ])
    def test_various_constructs(self, parser, code, expected):
        result = parser.parse(code, "test.ts")
        assert result.node_count >= expected
```

### Issue Mapping Tests
```python
# tests/unit/test_issue_mapping/test_analyzer.py
import pytest
from api.mapping.analyzer import IssueAnalyzer

class TestIssueAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return IssueAnalyzer()

    def test_extract_file_paths(self, analyzer):
        issue = {
            "title": "Bug in auth flow",
            "body": "The issue is in src/middleware/auth.ts and src/routes/login.ts"
        }
        result = analyzer.analyze(issue)
        assert "src/middleware/auth.ts" in result.mentioned_files
        assert "src/routes/login.ts" in result.mentioned_files

    def test_extract_routes(self, analyzer):
        issue = {
            "title": "POST /api/login returns 500",
            "body": "The POST /api/users endpoint also fails"
        }
        result = analyzer.analyze(issue)
        assert any("POST /api/login" in r for r in result.mentioned_routes)
        assert any("POST /api/users" in r for r in result.mentioned_routes)

    def test_classify_intent_bug(self, analyzer):
        issue = {
            "title": "NullPointerException when user not found",
            "body": "The application crashes with an error"
        }
        result = analyzer.analyze(issue)
        assert result.intent == "BUG"
        assert result.intent_confidence > 0.7

    def test_classify_intent_feature(self, analyzer):
        issue = {
            "title": "Add password reset functionality",
            "body": "We need a way for users to reset their password"
        }
        result = analyzer.analyze(issue)
        assert result.intent == "FEATURE"

    def test_extract_keywords(self, analyzer):
        issue = {
            "title": "Fix JWT token expiration handling",
            "body": "Tokens should refresh automatically before expiring"
        }
        result = analyzer.analyze(issue)
        assert "jwt" in [k.lower() for k in result.keywords]
        assert "token" in [k.lower() for k in result.keywords]
        assert "expiration" in [k.lower() for k in result.keywords]

class TestRanking:
    def test_direct_file_match_scores_high(self, analyzer):
        """Issue mentioning exact file should rank it highest."""
        issue = {
            "title": "Fix login validation",
            "body": "Update src/validators/login.ts to check email format"
        }
        # Simulate candidates
        candidates = [
            {"path": "src/validators/login.ts", "type": "file"},
            {"path": "src/validators/register.ts", "type": "file"},
            {"path": "src/routes/auth.ts", "type": "file"},
        ]
        ranked = analyzer.rank_candidates(issue, candidates)
        assert ranked[0]["path"] == "src/validators/login.ts"

    def test_confidence_tiers(self, analyzer):
        """Confidence should map to correct tier."""
        assert analyzer.confidence_tier(0.9) == "high"
        assert analyzer.confidence_tier(0.6) == "medium"
        assert analyzer.confidence_tier(0.4) == "low"
        assert analyzer.confidence_tier(0.1) == "low"
```

### API Integration Tests
```python
# tests/integration/test_api_endpoints.py
import pytest

class TestGraphEndpoints:
    async def test_get_full_graph(self, client, auth_headers, sample_repo_id):
        resp = await client.get(
            f"/api/v1/repos/{sample_repo_id}/graph",
            headers=auth_headers,
            params={"limit": 100}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) <= 100

    async def test_get_node_details(self, client, auth_headers, sample_repo_id, sample_node_id):
        resp = await client.get(
            f"/api/v1/repos/{sample_repo_id}/nodes/{sample_node_id}",
            headers=auth_headers
        )
        assert resp.status_code == 200
        node = resp.json()
        assert node["id"] == sample_node_id
        assert "metadata" in node

    async def test_semantic_search(self, client, auth_headers, sample_repo_id):
        resp = await client.post(
            f"/api/v1/repos/{sample_repo_id}/search/semantic",
            headers=auth_headers,
            json={"query": "authentication middleware", "limit": 5}
        )
        assert resp.status_code == 200
        results = resp.json()["results"]
        assert len(results) <= 5
        assert all("score" in r for r in results)

    async def test_issue_mapping(self, client, auth_headers, sample_repo_id):
        # Trigger analysis
        resp = await client.post(
            f"/api/v1/repos/{sample_repo_id}/issues/123/analyze",
            headers=auth_headers
        )
        assert resp.status_code == 202
        task_id = resp.json()["task_id"]

        # Poll for completion (in tests, use synchronous execution)
        # ... assertion logic

class TestAuthentication:
    async def test_requires_auth(self, client, sample_repo_id):
        resp = await client.get(f"/api/v1/repos/{sample_repo_id}")
        assert resp.status_code == 401

    async def test_invalid_token(self, client, sample_repo_id):
        resp = await client.get(
            f"/api/v1/repos/{sample_repo_id}",
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert resp.status_code == 401

    async def test_cross_tenant_access_denied(self, client, user_a_headers, repo_owned_by_b):
        """User A cannot access User B's repository."""
        resp = await client.get(
            f"/api/v1/repos/{repo_owned_by_b}",
            headers=user_a_headers
        )
        assert resp.status_code in [403, 404]

class TestRateLimiting:
    async def test_rate_limit_headers(self, client, auth_headers, sample_repo_id):
        resp = await client.get(
            f"/api/v1/repos/{sample_repo_id}",
            headers=auth_headers
        )
        assert "X-RateLimit-Limit" in resp.headers
        assert "X-RateLimit-Remaining" in resp.headers

    async def test_rate_limit_exceeded(self, client, auth_headers, sample_repo_id):
        """Exceeding rate limit returns 429."""
        for _ in range(1001):
            resp = await client.get(
                f"/api/v1/repos/{sample_repo_id}",
                headers=auth_headers
            )
        assert resp.status_code == 429
```

### Ingestion Pipeline Integration Test
```python
# tests/integration/test_ingestion_pipeline.py
import pytest

class TestIngestionPipeline:
    @pytest.fixture
    def sample_repo_fixture(self, tmp_path):
        """Create a small sample repository on disk."""
        repo = tmp_path / "sample"
        repo.mkdir()
        (repo / "src").mkdir()
        (repo / "src" / "index.ts").write_text("""
            import { UserService } from './services/user';
            export function main() {
                const service = new UserService();
                service.start();
            }
        """)
        (repo / "src" / "services").mkdir()
        (repo / "src" / "services" / "user.ts").write_text("""
            export class UserService {
                async getUser(id: string) {
                    return db.query(id);
                }
            }
        """)
        (repo / "package.json").write_text('{"name": "test"}')
        return repo

    async def test_full_pipeline(self, db_session, sample_repo_fixture):
        """Full pipeline: parse → extract → embed → persist → query."""
        from api.pipeline import IngestionPipeline

        pipeline = IngestionPipeline(db_session)
        result = await pipeline.run(
            repo_path=sample_repo_fixture,
            repo_id="test-repo-id"
        )

        # Verify nodes created
        assert result.nodes_created >= 3  # index.ts, user.ts, UserService class

        # Verify edges created
        assert result.edges_created >= 1  # import edge

        # Verify embeddings generated
        nodes = await db_session.query(CodeNode).filter(
            CodeNode.repo_id == "test-repo-id"
        ).all()
        assert all(n.embedding is not None for n in nodes)

    async def test_incremental_update(self, db_session, sample_repo_fixture, completed_pipeline):
        """Modify a file → incremental update only processes changes."""
        # Initial ingestion
        await completed_pipeline.run(repo_path=sample_repo_fixture)

        # Modify a file
        (sample_repo_fixture / "src" / "index.ts").write_text("""
            import { UserService } from './services/user';
            import { AuthService } from './services/auth';  // NEW
            export function main() {
                const service = new UserService();
                service.start();
            }
        """)

        # Run incremental
        result = await completed_pipeline.run(
            repo_path=sample_repo_fixture,
            mode="incremental"
        )

        # Only changed file should be re-processed
        assert result.files_processed == 1

    async def test_error_handling(self, db_session, tmp_path):
        """Pipeline should handle syntax errors gracefully."""
        repo = tmp_path / "broken"
        repo.mkdir()
        (repo / "broken.ts").write_text("function broken( { incomplete !!")

        pipeline = IngestionPipeline(db_session)
        result = await pipeline.run(repo_path=repo, repo_id="broken-repo")

        # Should complete with warnings, not fail
        assert result.status == "completed"
        assert len(result.warnings) > 0

    async def test_performance_10k_files(self, db_session, large_repo_fixture):
        """10k file monorepo should complete in < 10 minutes."""
        import time
        pipeline = IngestionPipeline(db_session)
        start = time.time()
        result = await pipeline.run(repo_path=large_repo_fixture)
        duration = time.time() - start

        assert result.status == "completed"
        assert duration < 600  # 10 minutes
```

---

## Frontend Tests (Vitest + React Testing Library)

### Directory Structure
```
apps/web/src/__tests__/
├── components/
│   ├── graph/
│   │   ├── GraphCanvas.test.tsx
│   │   ├── nodes/
│   │   │   ├── FileNode.test.tsx
│   │   │   ├── RouteNode.test.tsx
│   │   │   └── ComponentNode.test.tsx
│   │   └── panels/
│   │       ├── NodeDetailPanel.test.tsx
│   │       └── SearchResultsPanel.test.tsx
│   └── layout/
│       └── Sidebar.test.tsx
├── stores/
│   ├── graphStore.test.ts
│   └── uiStore.test.ts
├── hooks/
│   ├── useGraph.test.ts
│   └── useSearch.test.ts
└── lib/
    ├── graph/
    │   ├── layout.test.ts
    │   └── clustering.test.ts
    └── utils/
        └── format.test.ts
```

### Graph Component Tests
```typescript
// components/graph/nodes/FileNode.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { FileNode } from '@/components/graph/nodes/FileNode';

const mockNode = {
  id: 'node-1',
  type: 'file',
  name: 'auth.ts',
  path: 'src/middleware/auth.ts',
  language: 'typescript',
  metadata: {
    loc: 45,
    complexity: { cyclomatic: 3, cognitive: 8 },
    exports: ['authenticate', 'authorize'],
  },
};

describe('FileNode', () => {
  it('renders file name', () => {
    render(<FileNode data={{ node: mockNode, isSelected: false, isHighlighted: false }} />);
    expect(screen.getByText('auth.ts')).toBeInTheDocument();
  });

  it('shows language badge', () => {
    render(<FileNode data={{ node: mockNode, isSelected: false, isHighlighted: false }} />);
    expect(screen.getByText('TypeScript')).toBeInTheDocument();
  });

  it('shows LOC count', () => {
    render(<FileNode data={{ node: mockNode, isSelected: false, isHighlighted: false }} />);
    expect(screen.getByText('45 LOC')).toBeInTheDocument();
  });

  it('highlights when selected', () => {
    const { container } = render(
      <FileNode data={{ node: mockNode, isSelected: true, isHighlighted: false }} />
    );
    expect(container.firstChild).toHaveClass('ring-2');
  });

  it('calls onClick when clicked', () => {
    const onClick = vi.fn();
    render(
      <FileNode
        data={{ node: mockNode, isSelected: false, isHighlighted: false }}
        onClick={onClick}
      />
    );
    fireEvent.click(screen.getByText('auth.ts'));
    expect(onClick).toHaveBeenCalledWith('node-1');
  });
});
```

### Store Tests
```typescript
// stores/graphStore.test.ts
import { describe, it, expect, beforeEach } from 'vitest';
import { useGraphStore } from '@/stores/graphStore';

describe('graphStore', () => {
  beforeEach(() => {
    useGraphStore.setState({
      nodes: new Map(),
      edges: new Map(),
      selectedNodeId: null,
      highlightedNodeIds: new Set(),
    });
  });

  it('sets graph data', () => {
    const nodes = [
      { id: '1', type: 'file', name: 'a.ts', path: 'src/a.ts' },
      { id: '2', type: 'file', name: 'b.ts', path: 'src/b.ts' },
    ];
    const edges = [
      { id: 'e1', source_id: '1', target_id: '2', type: 'imports' },
    ];

    useGraphStore.getState().setGraph(nodes, edges);

    expect(useGraphStore.getState().nodes.size).toBe(2);
    expect(useGraphStore.getState().edges.size).toBe(1);
  });

  it('selects and deselects node', () => {
    useGraphStore.getState().selectNode('node-1');
    expect(useGraphStore.getState().selectedNodeId).toBe('node-1');

    useGraphStore.getState().selectNode(null);
    expect(useGraphStore.getState().selectedNodeId).toBeNull();
  });

  it('adds and clears highlights', () => {
    useGraphStore.getState().addHighlight(['a', 'b', 'c']);
    expect(useGraphStore.getState().highlightedNodeIds.size).toBe(3);

    useGraphStore.getState().clearHighlight();
    expect(useGraphStore.getState().highlightedNodeIds.size).toBe(0);
  });

  it('filters nodes by type', () => {
    // Setup nodes
    useGraphStore.getState().setGraph(mockNodes, []);
    useGraphStore.getState().setFilter({ types: ['route'] });

    const visible = useGraphStore.getState().filteredNodeIds;
    const visibleNodes = mockNodes.filter(n => visible.has(n.id));
    expect(visibleNodes.every(n => n.type === 'route')).toBe(true);
  });
});
```

---

## E2E Tests (Playwright)

### Directory Structure
```
apps/web/e2e/
├── auth.spec.ts
├── graph.spec.ts
├── issue-mapping.spec.ts
├── search.spec.ts
├── chat.spec.ts
└── fixtures/
```

### Key E2E Scenarios
```typescript
// e2e/graph.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Graph Visualization', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/repos/test-repo/graph');
    await page.waitForSelector('[data-testid="graph-canvas"]');
  });

  test('renders graph with nodes', async ({ page }) => {
    const nodes = page.locator('.react-flow__node');
    expect(await nodes.count()).toBeGreaterThan(0);
  });

  test('click node opens detail panel', async ({ page }) => {
    await page.locator('.react-flow__node').first().click();
    await expect(page.locator('[data-testid="node-detail-panel"]')).toBeVisible();
    await expect(page.locator('[data-testid="node-name"]')).toBeVisible();
  });

  test('filter by node type', async ({ page }) => {
    await page.click('[data-testid="filter-button"]');
    await page.check('input[value="route"]');
    await page.click('[data-testid="apply-filter"]');

    // Only route nodes should be visible
    const visibleNodes = page.locator('.react-flow__node:not(.filtered-out)');
    // Assert all visible nodes are of type route
  });

  test('search highlights matching nodes', async ({ page }) => {
    await page.fill('[data-testid="graph-search"]', 'auth');
    await page.press('[data-testid="graph-search"]', 'Enter');

    await expect(page.locator('.react-flow__node.highlighted')).toHaveCount.greaterThan(0);
  });

  test('zoom controls work', async ({ page }) => {
    const zoomIn = page.locator('[data-testid="zoom-in"]');
    await zoomIn.click();
    // Verify zoom level changed
  });

  test('cluster expands on double click', async ({ page }) => {
    const cluster = page.locator('.react-flow__node.cluster').first();
    await cluster.dblclick();
    // Verify child nodes appear
  });
});

test.describe('Issue Mapping Flow', () => {
  test('click issue shows highlighted subgraph', async ({ page }) => {
    await page.goto('/repos/test-repo/issues');

    // Click an issue
    await page.locator('[data-testid="issue-123"]').click();

    // Wait for mapping to load
    await page.waitForSelector('[data-testid="issue-mapping-panel"]');

    // Verify highlighted nodes
    const highlighted = page.locator('.react-flow__node.highlighted');
    expect(await highlighted.count()).toBeGreaterThan(0);

    // Verify confidence scores shown
    await expect(page.locator('[data-testid="confidence-score"]').first()).toBeVisible();
  });

  test('submit feedback on mapping', async ({ page }) => {
    await page.goto('/repos/test-repo/issues/123');
    await page.click('[data-testid="thumbs-up"]');
    await expect(page.locator('[data-testid="feedback-success"]')).toBeVisible();
  });
});

test.describe('Authentication', () => {
  test('redirects to login when unauthenticated', async ({ page }) => {
    await page.goto('/repos');
    await expect(page).toHaveURL(/.*login/);
  });

  test('login with GitHub OAuth', async ({ page }) => {
    // Mock OAuth flow in tests
    await page.goto('/login');
    await page.click('[data-testid="github-login"]');
    // Assert redirect to dashboard
  });
});
```

### Playwright Config
```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 4 : undefined,
  reporter: [
    ['html', { open: 'never' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
  ],
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'mobile',
      use: { ...devices['iPhone 14'] },
    },
  ],
  webServer: {
    command: 'docker compose up -d',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
```

---

## Performance Tests

### Ingestion Performance
```python
# tests/performance/test_ingestion_perf.py
import pytest
import time

@pytest.mark.performance
class TestIngestionPerformance:
    async def test_small_repo_under_30s(self, db_session, small_repo_fixture):
        """Repo with <100 files: complete in <30s."""
        start = time.time()
        pipeline = IngestionPipeline(db_session)
        result = await pipeline.run(repo_path=small_repo_fixture)
        assert time.time() - start < 30

    async def test_medium_repo_under_5min(self, db_session, medium_repo_fixture):
        """Repo with ~1000 files: complete in <5min."""
        start = time.time()
        pipeline = IngestionPipeline(db_session)
        result = await pipeline.run(repo_path=medium_repo_fixture)
        assert time.time() - start < 300

    async def test_incremental_under_30s(self, db_session, changed_repo_fixture):
        """100 file change: incremental update in <30s."""
        start = time.time()
        pipeline = IngestionPipeline(db_session)
        result = await pipeline.run(repo_path=changed_repo_fixture, mode="incremental")
        assert time.time() - start < 30

    async def test_memory_usage_under_2gb(self, db_session, large_repo_fixture):
        """Peak memory usage < 2GB."""
        import tracemalloc
        tracemalloc.start()
        
        pipeline = IngestionPipeline(db_session)
        await pipeline.run(repo_path=large_repo_fixture)
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        assert peak < 2 * 1024 * 1024 * 1024  # 2GB
```

### API Performance
```python
# tests/performance/test_api_perf.py
import pytest
import asyncio

@pytest.mark.performance
class TestAPIPerformance:
    async def test_graph_load_under_100ms(self, client, auth_headers, sample_repo_id):
        """Graph endpoint with 500 nodes: <100ms."""
        times = []
        for _ in range(10):
            start = time.time()
            resp = await client.get(
                f"/api/v1/repos/{sample_repo_id}/graph",
                headers=auth_headers,
                params={"limit": 500}
            )
            times.append(time.time() - start)
        avg = sum(times) / len(times)
        assert avg < 0.1  # 100ms

    async def test_semantic_search_under_50ms(self, client, auth_headers, sample_repo_id):
        """Semantic search: <50ms."""
        times = []
        for _ in range(10):
            start = time.time()
            resp = await client.post(
                f"/api/v1/repos/{sample_repo_id}/search/semantic",
                headers=auth_headers,
                json={"query": "auth middleware", "limit": 10}
            )
            times.append(time.time() - start)
        avg = sum(times) / len(times)
        assert avg < 0.05  # 50ms
```

### Load Test (k6)
```javascript
// tests/load/graph-load.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '2m', target: 50 },   // Ramp up
    { duration: '5m', target: 50 },   // Steady state
    { duration: '2m', target: 100 },  // Ramp up more
    { duration: '5m', target: 100 },  // Peak
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<200'],  // 95% under 200ms
    errors: ['rate<0.01'],             // <1% error rate
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const TOKEN = __ENV.TOKEN;

export default function () {
  const headers = {
    'Authorization': `Bearer ${TOKEN}`,
    'Content-Type': 'application/json',
  };

  // Test scenario mix
  const scenario = Math.random();

  if (scenario < 0.4) {
    // 40% graph queries
    const resp = http.get(
      `${BASE_URL}/api/v1/repos/test-repo/graph?limit=500`,
      { headers }
    );
    check(resp, {
      'graph status 200': (r) => r.status === 200,
      'graph time < 200ms': (r) => r.timings.duration < 200,
    });
    errorRate.add(resp.status !== 200);
  } else if (scenario < 0.7) {
    // 30% semantic searches
    const resp = http.post(
      `${BASE_URL}/api/v1/repos/test-repo/search/semantic`,
      JSON.stringify({ query: 'auth middleware', limit: 10 }),
      { headers }
    );
    check(resp, { 'search status 200': (r) => r.status === 200 });
    errorRate.add(resp.status !== 200);
  } else if (scenario < 0.9) {
    // 20% node details
    const resp = http.get(
      `${BASE_URL}/api/v1/repos/test-repo/nodes/some-node-id`,
      { headers }
    );
    check(resp, { 'node status 200': (r) => r.status === 200 });
    errorRate.add(resp.status !== 200);
  } else {
    // 10% issue mapping
    const resp = http.post(
      `${BASE_URL}/api/v1/repos/test-repo/issues/123/analyze`,
      JSON.stringify({}),
      { headers }
    );
    check(resp, { 'issue status 202': (r) => r.status === 202 });
    errorRate.add(resp.status !== 202);
  }

  sleep(1);
}
```

---

## Visual Regression (Chromatic)

```typescript
// .storybook/preview.tsx
export const parameters = {
  chromatic: {
    pauseAnimationAtEnd: true,
    diffThreshold: 0.1,
  },
};

// stories/NodeTypes.stories.tsx
export const FileNodeLight: Story = {
  parameters: {
    chromatic: { preferredTheme: 'light' },
  },
};

export const FileNodeDark: Story = {
  parameters: {
    chromatic: { preferredTheme: 'dark' },
  },
};
```

---

## Coverage Requirements

| Layer | Minimum | Tool |
|-------|---------|------|
| Unit (Python) | 80% | pytest-cov |
| Unit (TypeScript) | 80% | vitest |
| Integration | 70% | pytest |
| E2E critical paths | 100% | Playwright |

### Coverage Report
```bash
# Backend
pytest --cov=apps/api --cov-report=html --cov-report=term-missing

# Frontend
pnpm test --coverage

# Combined report
pnpm coverage:merge
```

---

## CI Test Gates

| Gate | Condition | Action |
|------|-----------|--------|
| Unit tests | Must pass | Block merge |
| Integration tests | Must pass | Block merge |
| Coverage | > 80% | Block merge |
| E2E tests | Must pass | Block merge |
| Performance | Within targets | Warning |
| Visual regression | No unexpected diffs | Block merge |