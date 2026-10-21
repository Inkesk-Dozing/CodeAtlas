# CodeAtlas - Developer Guide

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Node.js | 20+ | `nvm install 20` |
| pnpm | 8+ | `npm i -g pnpm` |
| Python | 3.11+ | `pyenv install 3.11` |
| Docker | 24+ | [Docker Desktop](https://docker.com) |
| Git | 2.40+ | `apt install git` |
| PostgreSQL client | 16 | `apt install postgresql-client` |

Optional (for full local setup):
| Tool | Purpose |
|------|---------|
| NVIDIA drivers + CUDA | Local LLM inference via Ollama |
| kubectl + minikube | Local Kubernetes testing |
| Terraform | Infrastructure management |

---

## Initial Setup

### 1. Clone Repository
```bash
git clone https://github.com/codeatlas/codeatlas.git
cd codeatlas
```

### 2. Environment Configuration
```bash
# Copy example environment file
cp .env.example .env

# Generate secrets
python -c "import secrets; print('JWT_SECRET=' + secrets.token_urlsafe(64))" >> .env
python -c "import secrets; print('NEXTAUTH_SECRET=' + secrets.token_urlsafe(64))" >> .env
python -c "import secrets; print('GITHUB_WEBHOOK_SECRET=' + secrets.token_urlsafe(32))" >> .env
```

### 3. GitHub App Setup

1. Go to [GitHub Developer Settings](https://github.com/settings/apps)
2. Click **New GitHub App**
3. Configure:
   - **Name**: `CodeAtlas-Dev`
   - **Homepage URL**: `http://localhost:3000`
   - **Webhook URL**: `http://localhost:8000/v1/webhooks/github`
   - **Webhook Secret**: Use value from `.env`
   - **Repository Permissions**:
     - Contents: Read-only
     - Metadata: Read-only
     - Issues: Read-only
   - **Where can this app be installed?**: Only on this account
4. Generate **Private Key** → save as `apps/api/private-key.pem`
5. Copy **App ID** to `.env` as `GITHUB_APP_ID`
6. Create OAuth App (for user login):
   - Go to **OAuth Apps** → **New OAuth App**
   - Authorization callback URL: `http://localhost:3000/api/auth/callback/github`
   - Copy Client ID and Secret to `.env`

### 4. Install Dependencies
```bash
# Install all workspace dependencies
pnpm install

# Install Python dependencies
cd apps/api
pip install -r requirements.txt
cd ../..

# Install pre-commit hooks
pre-commit install
```

### 5. Start Infrastructure
```bash
# Start PostgreSQL, Redis, MinIO, Ollama
docker compose up -d postgres redis minio

# Verify services are healthy
docker compose ps

# Run database migrations
docker compose exec api alembic upgrade head

# Initialize Ollama models (if using local LLM)
docker compose exec ollama ollama pull nomic-embed-text
docker compose exec ollama ollama pull codellama:7b
```

### 6. Seed Development Data
```bash
# Create sample repository and test data
docker compose exec api python -m scripts.seed_dev

# This creates:
# - Test user with GitHub OAuth mock
# - Sample repository with parsed graph
# - Sample issues with pre-computed mappings
```

### 7. Start Development Servers
```bash
# Terminal 1: Backend API
cd apps/api
uvicorn main:app --reload --port 8000

# Terminal 2: Celery Worker
cd apps/api
celery -A tasks.celery worker --loglevel=info

# Terminal 3: Frontend
cd apps/web
pnpm dev

# Or start everything at once
pnpm dev  # Runs all via turbo
```

### 8. Verify Setup
```bash
# API health check
curl http://localhost:8000/health
# Expected: {"status": "healthy", ...}

# API docs
open http://localhost:8000/docs

# Frontend
open http://localhost:3000

# MinIO console
open http://localhost:9001
```

---

## Project Structure

```
codeatlas/
├── apps/
│   ├── api/                    # FastAPI backend
│   │   ├── main.py             # App entry point
│   │   ├── config.py           # Settings
│   │   ├── database.py         # DB connection
│   │   ├── models/             # SQLAlchemy models
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── routers/            # API routes
│   │   │   ├── repos.py
│   │   │   ├── graph.py
│   │   │   ├── search.py
│   │   │   ├── issues.py
│   │   │   ├── ingestion.py
│   │   │   └── webhooks.py
│   │   ├── services/           # Business logic
│   │   │   ├── ingestion/
│   │   │   │   ├── clone.py
│   │   │   │   ├── parser.py
│   │   │   │   ├── extractor.py
│   │   │   │   ├── embedder.py
│   │   │   │   └── persist.py
│   │   │   ├── mapping/
│   │   │   │   ├── analyzer.py
│   │   │   │   ├── candidates.py
│   │   │   │   ├── ranker.py
│   │   │   │   └── propagation.py
│   │   │   ├── summarizer.py
│   │   │   └── chat.py
│   │   ├── tasks/              # Celery tasks
│   │   │   ├── celery_app.py
│   │   │   ├── ingestion_tasks.py
│   │   │   └── scheduled_tasks.py
│   │   ├── parsers/            # Tree-sitter parsers
│   │   │   ├── base.py
│   │   │   ├── typescript.py
│   │   │   ├── python.py
│   │   │   └── go.py
│   │   ├── migrations/         # Alembic migrations
│   │   ├── tests/              # Pytest tests
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   └── web/                    # Next.js frontend
│       ├── src/
│       │   ├── app/            # App Router pages
│       │   ├── components/     # React components
│       │   │   ├── graph/      # React Flow components
│       │   │   ├── ui/         # shadcn/ui
│       │   │   └── layout/     # Layout components
│       │   ├── stores/         # Zustand stores
│       │   ├── hooks/          # React hooks
│       │   ├── lib/            # Utilities
│       │   └── types/          # TypeScript types
│       ├── e2e/                # Playwright tests
│       ├── package.json
│       └── Dockerfile
│
├── packages/
│   ├── shared/                 # Shared types & constants
│   │   ├── src/
│   │   │   ├── types/
│   │   │   │   ├── graph.ts
│   │   │   │   ├── api.ts
│   │   │   │   └── issues.ts
│   │   │   └── constants.ts
│   │   └── package.json
│   └── ui/                     # Shared UI components
│
├── infra/                      # Infrastructure
│   ├── k8s/                    # Kubernetes manifests
│   ├── terraform/              # Terraform configs
│   ├── monitoring/             # Prometheus, Grafana
│   └── docker-compose.yml
│
├── docs/                       # Documentation
│   ├── 01-project-overview.md
│   ├── 02-tech-stack.md
│   ├── ... (all docs)
│   └── README.md
│
├── turbo.json                  # Turborepo config
├── pnpm-workspace.yaml
├── package.json
└── .github/workflows/          # CI/CD
```

---

## Development Workflow

### Creating a Feature
```bash
# 1. Create branch
git checkout -b feature/issue-mapping-enhancements

# 2. Make changes
# ... code ...

# 3. Run tests
pnpm test                    # All tests
pnpm test:api                # Backend only
pnpm test:web                # Frontend only
pnpm test:e2e                # E2E tests

# 4. Lint and type check
pnpm lint
pnpm typecheck

# 5. Commit (conventional commits)
git add .
git commit -m "feat(mapping): add historical pattern candidate generation"

# 6. Push and create PR
git push origin feature/issue-mapping-enhancements
gh pr create --fill
```

### Commit Convention
```
<type>(<scope>): <subject>

Types:
  feat:     New feature
  fix:      Bug fix
  docs:     Documentation
  style:    Formatting (no code change)
  refactor: Code restructuring
  test:     Adding tests
  chore:    Build/tooling changes

Examples:
  feat(mapping): add graph propagation to issue mapping
  fix(parser): handle TypeScript decorators correctly
  docs(api): update semantic search endpoint docs
  perf(embed): batch embeddings for 2x speedup
```

### Database Migrations
```bash
# Create new migration
cd apps/api
alembic revision --autogenerate -m "add chat_sessions table"

# Review generated migration
cat migrations/versions/xxxx_add_chat_sessions.py

# Apply migration
alembic upgrade head

# Rollback (if needed)
alembic downgrade -1
```

### Adding a New API Endpoint
```python
# 1. Define schema (apps/api/schemas/search.py)
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(default=10, ge=1, le=100)

class SearchResult(BaseModel):
    node: CodeNode
    score: float
    snippet: str

# 2. Create service (apps/api/services/search.py)
class SearchService:
    async def semantic_search(self, repo_id: str, query: str, limit: int) -> list[SearchResult]:
        ...

# 3. Create router (apps/api/routers/search.py)
@router.post("/repos/{repo_id}/search/semantic")
async def semantic_search(
    repo_id: str,
    request: SearchRequest,
    user = Depends(require_permission("search")),
    search_service = Depends(get_search_service),
):
    results = await search_service.semantic_search(repo_id, request.query, request.limit)
    return {"results": results}

# 4. Register router (apps/api/main.py)
from routers.search import router as search_router
app.include_router(search_router, prefix="/api/v1")

# 5. Add tests (apps/api/tests/integration/test_search.py)
async def test_semantic_search(client, auth_headers, sample_repo_id):
    ...

# 6. Update API docs (docs/06-api-spec.md)
```

### Adding a New Graph Node Type
```typescript
// 1. Define type (packages/shared/src/types/graph.ts)
export interface ServiceNode extends BaseNode {
  type: 'service';
  metadata: {
    injectable: boolean;
    dependencies: string[];
  };
}

// 2. Create component (apps/web/src/components/graph/nodes/ServiceNode.tsx)
export function ServiceNode({ data }: NodeProps<ServiceNode>) {
  return (
    <div className="node service-node">
      <span className="icon">⚙️</span>
      <span className="name">{data.name}</span>
      <span className="badge">{data.metadata.dependencies.length} deps</span>
    </div>
  );
}

// 3. Register (apps/web/src/components/graph/nodes/index.ts)
export const nodeTypes = {
  service: ServiceNode,
  // ... other types
};

// 4. Add parser support (apps/api/parsers/base.py)
# Add extraction logic for services
```

---

## Testing

```bash
# Run all tests
pnpm test

# Backend tests
cd apps/api
pytest                              # All
pytest tests/unit/                  # Unit only
pytest tests/integration/           # Integration only
pytest -k "test_extract_routes"     # By name
pytest --cov=apps/api --cov-report=html  # Coverage

# Frontend tests
cd apps/web
pnpm test                           # All
pnpm test -- --watch                # Watch mode
pnpm test -- --coverage             # Coverage
pnpm test GraphCanvas               # By name

# E2E tests
cd apps/web
pnpm test:e2e                       # All
pnpm test:e2e -- --headed           # With browser UI
pnpm test:e2e graph.spec.ts         # Specific file

# Load tests
k6 run tests/load/graph-load.js
```

---

## Debugging

### Backend Debugging
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with debugger
python -m debugpy --listen 5678 --wait-for-client -m uvicorn main:app --reload

# VS Code: Attach to process (launch.json)
{
    "name": "Python: Attach",
    "type": "debugpy",
    "request": "attach",
    "connect": {"host": "localhost", "port": 5678}
}

# Inspect Celery tasks
celery -A tasks.celery inspect active
celery -A tasks.celery inspect reserved

# Check database
psql codeatlas -c "SELECT * FROM code_nodes LIMIT 10;"
```

### Frontend Debugging
```bash
# React DevTools
# Install browser extension

# Zustand DevTools
# Check browser console for state changes

# Network tab: Filter by /api/v1/

# React Flow debugging
# Enable in dev: localStorage.setItem('rf-debug', 'true')
```

### Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: tree_sitter` | `pip install tree-sitter tree-sitter-typescript` |
| WebSocket connection failed | Check CORS, ensure backend running on 8000 |
| GitHub OAuth redirect mismatch | Verify callback URL matches OAuth App config |
| pgvector extension missing | `docker compose exec postgres psql -U codeatlas -c "CREATE EXTENSION vector;"` |
| Ollama connection refused | `docker compose up -d ollama` + pull models |
| Celery tasks not running | Check worker process: `celery -A tasks.celery inspect active` |
| pnpm workspace errors | Delete `node_modules`, run `pnpm install` |
| Migration conflicts | `alembic downgrade base && alembic upgrade head` |

---

## Useful Commands

```bash
# Development
pnpm dev                    # Start all dev servers
pnpm build                  # Build all
pnpm lint                   # Lint all
pnpm typecheck              # Type check all
pnpm test                   # Test all

# Docker
docker compose up -d        # Start infrastructure
docker compose logs -f api  # Follow API logs
docker compose exec api bash  # Shell into API container
docker compose down -v      # Stop and remove volumes

# Database
alembic upgrade head        # Apply migrations
alembic current             # Current migration
alembic history             # Migration history

# Celery
celery -A tasks.celery flower  # Monitoring UI (port 5555)

# Git
git log --oneline -10       # Recent commits
git diff --stat             # Changed files
git branch -a               # All branches
```

---

## Code Style

### Python (ruff)
```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "SIM"]
ignore = ["E501"]  # Line length handled by formatter

[tool.ruff.format]
quote-style = "double"
```

### TypeScript (ESLint + Prettier)
```json
// .eslintrc.json
{
  "extends": [
    "next/core-web-vitals",
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended"
  ],
  "rules": {
    "react/jsx-max-props-per-line": ["error", { "maximum": 3 }],
    "@typescript-eslint/no-unused-vars": ["error", { "argsIgnorePattern": "^_" }]
  }
}
```

### General Rules
- **No comments** unless explaining complex logic
- **Meaningful names**: `authenticateUser` not `auth`
- **Small functions**: < 50 lines preferred
- **Type everything**: No `any` in TypeScript, full type hints in Python
- **Error handling**: Never silently swallow errors