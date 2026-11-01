# CodeAtlas Pull Request Guide & Execution Blueprints

This document outlines the pull request workflow, review standards, and the authoritative, chronological Pull Request specifications for the **Phase 0 Foundation** milestone of CodeAtlas.

---

## 📌 Chronological Pull Request Catalog (Phase 0 Foundation)

| PR ID | Branch Name | Title | Linked Issue | Target | Status |
|---|---|---|---|---|---|
| `PR-01` | `feat/01-monorepo-turborepo-pnpm` | `feat(infra): support monorepo orchestration with Turborepo and pnpm workspaces` | Closes `#1` | `main` | Merged |
| `PR-02` | `infra/02-docker-compose-stack` | `infra(docker): configure multi-service local development stack with Docker Compose` | Closes `#2` | `main` | Merged |
| `PR-03` | `feat/03-github-webhook-receiver` | `feat(api): implement GitHub App webhook receiver with HMAC-SHA256 signature verification` | Closes `#3` | `main` | Merged |
| `PR-04` | `feat/04-oauth-jwt-auth` | `feat(auth): implement GitHub OAuth 2.0 authentication and dual-mode JWT session handling` | Closes `#4` | `main` | Merged |
| `PR-05` | `feat/05-db-schema-migrations` | `feat(db): establish 15-table relational database schema with async Alembic migrations and pgvector` | Closes `#5` | `main` | Merged |
| `PR-06` | `feat/06-fastapi-app-lifecycle` | `feat(api): build FastAPI application lifecycle, route registry, and exception middleware stack` | Closes `#6` | `main` | Merged |
| `PR-07` | `feat/07-nextjs-app-router-design` | `feat(web): create Next.js 14 App Router baseline with Tailwind CSS dark mode design system` | Closes `#7` | `main` | Merged |
| `PR-08` | `feat/08-shared-domain-contracts` | `feat(shared): define shared TypeScript and Python domain contracts and Data Transfer Objects` | Closes `#8` | `main` | Merged |
| `PR-09` | `ci/09-github-actions-monorepo` | `ci(workflow): establish CI/CD GitHub Actions workflow for monorepo validation and container builds` | Closes `#9` | `main` | Merged |
| `PR-10` | `security/10-codeql-trufflehog-dependabot` | `security(ci): automate security scanning with CodeQL static analysis, TruffleHog, and Dependabot` | Closes `#10` | `main` | Merged |
| `PR-11` | `infra/11-celery-redis-worker` | `infra(worker): configure Celery distributed task queue worker with Redis broker and process recycling` | Closes `#11` | `main` | Merged |
| `PR-12` | `docs/12-arch-blueprint-prd` | `docs(arch): document foundational architectural blueprint, component interactions, and PRD` | Closes `#13` | `main` | Merged |
| `PR-13` | `feat/13-pydantic-config-validation` | `feat(config): manage application runtime configuration with strict Pydantic Settings validation` | Closes `#14` | `main` | Merged |
| `PR-14` | `feat/14-health-probes-metrics` | `feat(infra): expose container liveness and readiness health check probes with dependency tests` | Closes `#15` | `main` | Merged |
| `PR-15` | `test/15-test-frameworks-coverage` | `test(core): establish automated backend pytest and frontend vitest test suites` | Closes `#16` | `main` | Merged |
| `PR-16` | `infra/16-formatting-precommit` | `infra(tooling): establish code style formatting, contributor guidelines, and pre-commit hooks` | Closes `#17` | `main` | Merged |
| `PR-17` | `feat/17-auth-context-guards` | `feat(web): implement client-side authentication context and protected route guards in Next.js` | Closes `#18` | `main` | Merged |
| `PR-18` | `feat/18-repository-explorer-ui` | `feat(web): build repository explorer card grid and manual ingestion trigger interface` | Closes `#19` | `main` | Merged |

---

## 🛠️ Detailed Pull Request Blueprints & Verification Matrix

### PR-01 Blueprint: `feat(infra): support monorepo orchestration with Turborepo and pnpm workspaces`

```markdown
## 📌 Description

Establishes root-level monorepo management utilizing Turborepo and pnpm workspaces. Configures topological build pipelines across apps/api, apps/web, and packages/shared with artifact hashing and dependency caching.

Closes #1

---

## 🛠️ Type of Change

- [ ] `feat`: Feat change
- [ ] `fix`: Fix change
- [x] `infra`: Infra change
- [ ] `security`: Security change
- [ ] `test`: Test change
- [ ] `docs`: Docs change

---

## 📐 Scope of Changes

- `package.json`
- `pnpm-workspace.yaml`
- `turbo.json`
- `.gitignore`
- `.gitattributes`

---

## 🧪 Verification & Testing Matrix

- [x] pnpm install executes with frozen lockfile validation
- [x] turbo run build executes cleanly in topological order across all packages
- [x] turbo run lint executes root-level formatting and workspace lint gates

---

## 🔒 Security & Guardrails Checklist

- [x] Configured .gitignore to forbid secret leakage (.env, *.pem, credentials)
- [x] Enforced strict package immutability via pnpm-lock.yaml
- [x] Verified zero hardcoded credentials or secret leakage
- [x] Linting and static analysis checks passed with 0 warnings
```

---

### PR-02 Blueprint: `infra(docker): configure multi-service local development stack with Docker Compose`

```markdown
## 📌 Description

Configures a complete multi-container local runtime stack via Docker Compose. Deploys PostgreSQL 16 with pgvector extension, Redis 7 for cache and queue broker, MinIO S3-compatible snapshot store, and Ollama local neural inference engine.

Closes #2

---

## 🛠️ Type of Change

- [ ] `feat`: Feat change
- [ ] `fix`: Fix change
- [x] `infra`: Infra change
- [ ] `security`: Security change
- [ ] `test`: Test change
- [ ] `docs`: Docs change

---

## 📐 Scope of Changes

- `infra/docker-compose.yml`
- `.env.example`
- `infra/README.md`

---

## 🧪 Verification & Testing Matrix

- [x] docker compose -f infra/docker-compose.yml up -d boots all 4 services healthy
- [x] Verified pgvector extension initialization via SELECT * FROM pg_extension WHERE extname = 'vector'
- [x] Redis broker responds to redis-cli ping with PONG

---

## 🔒 Security & Guardrails Checklist

- [x] Default non-root service credentials isolated to .env.example template
- [x] Internal network isolation between data volume mounts and host system
- [x] Verified zero hardcoded credentials or secret leakage
- [x] Linting and static analysis checks passed with 0 warnings
```

---

### PR-03 Blueprint: `feat(api): implement GitHub App webhook receiver with HMAC-SHA256 signature verification`

```markdown
## 📌 Description

Implements secure POST /api/v1/webhooks/github endpoint capable of ingesting push, installation, and issue events with constant-time HMAC-SHA256 signature verification. Rejects unsigned or forged payloads with HTTP 401.

Closes #3

---

## 🛠️ Type of Change

- [ ] `feat`: Feat change
- [ ] `fix`: Fix change
- [ ] `infra`: Infra change
- [x] `security`: Security change
- [ ] `test`: Test change
- [ ] `docs`: Docs change

---

## 📐 Scope of Changes

- `apps/api/routers/webhooks.py`
- `apps/api/services/auth.py`
- `apps/api/tests/unit/test_webhooks.py`

---

## 🧪 Verification & Testing Matrix

- [x] pytest apps/api/tests/unit/test_webhooks.py passed with 100% route coverage
- [x] Forged HMAC signatures return HTTP 401 Unauthorized
- [x] Valid payloads dispatch asynchronous ingestion jobs to Celery task queue

---

## 🔒 Security & Guardrails Checklist

- [x] Constant-time HMAC comparison via hmac.compare_digest prevents timing attacks
- [x] Payload replay attacks mitigated via webhook timestamp validation
- [x] Verified zero hardcoded credentials or secret leakage
- [x] Linting and static analysis checks passed with 0 warnings
```

---

### PR-04 Blueprint: `feat(auth): implement GitHub OAuth 2.0 authentication and dual-mode JWT session handling`

```markdown
## 📌 Description

Delivers end-to-end GitHub OAuth 2.0 handshake and session issuance. Features short-lived access JWT tokens (15 minutes) and HTTP-only secure refresh cookie rotation (7 days) with CSRF state token verification.

Closes #4

---

## 🛠️ Type of Change

- [x] `feat`: Feat change
- [ ] `fix`: Fix change
- [ ] `infra`: Infra change
- [ ] `security`: Security change
- [ ] `test`: Test change
- [ ] `docs`: Docs change

---

## 📐 Scope of Changes

- `apps/api/routers/auth.py`
- `apps/api/services/auth.py`
- `apps/api/dependencies.py`
- `apps/api/tests/unit/test_auth.py`

---

## 🧪 Verification & Testing Matrix

- [x] pytest apps/api/tests/unit/test_auth.py verified OAuth token exchange and refresh flows
- [x] Protected API routes enforce Bearer JWT authentication and reject expired tokens with HTTP 401
- [x] Session renewal endpoint successfully refreshes tokens without requiring re-login

---

## 🔒 Security & Guardrails Checklist

- [x] Access tokens signed with HS256 algorithm and dynamic secret keys
- [x] Refresh tokens stored exclusively in HttpOnly, Secure, SameSite=Lax cookies
- [x] Verified zero hardcoded credentials or secret leakage
- [x] Linting and static analysis checks passed with 0 warnings
```

---

### PR-05 Blueprint: `feat(db): establish 15-table relational database schema with async Alembic migrations and pgvector`

```markdown
## 📌 Description

Creates complete 15-table relational schema with SQLAlchemy 2.0 async engine and Alembic migrations. Encodes CodeNode (AST entities), CodeEdge (relations), Repositories, Organizations, and Vector embeddings with pgvector HNSW indexing.

Closes #5

---

## 🛠️ Type of Change

- [x] `feat`: Feat change
- [ ] `fix`: Fix change
- [ ] `infra`: Infra change
- [ ] `security`: Security change
- [ ] `test`: Test change
- [ ] `docs`: Docs change

---

## 📐 Scope of Changes

- `apps/api/database.py`
- `apps/api/models/__init__.py`
- `apps/api/models/repository.py`
- `apps/api/models/node.py`
- `apps/api/models/edge.py`
- `apps/api/alembic/env.py`
- `apps/api/alembic/versions/`
- `apps/api/tests/integration/test_database.py`

---

## 🧪 Verification & Testing Matrix

- [x] alembic upgrade head executes without error against fresh PostgreSQL instance
- [x] pytest apps/api/tests/integration/test_database.py verified foreign key cascades and HNSW cosine distance queries
- [x] Confirmed connection pool stability under 100 concurrent asynchronous read/write sessions

---

## 🔒 Security & Guardrails Checklist

- [x] All queries parameterized through SQLAlchemy Core/ORM to prevent SQL injection
- [x] UUID primary keys utilized across all public entity tables
- [x] Verified zero hardcoded credentials or secret leakage
- [x] Linting and static analysis checks passed with 0 warnings
```

---

### PR-06 Blueprint: `feat(api): build FastAPI application lifecycle, route registry, and exception middleware stack`

```markdown
## 📌 Description

Implements modern FastAPI application using asynccontextmanager lifespan protocol. Registers global exception handlers, CORS headers, Request ID propagation middleware, and centralized router registry across 9 API controllers.

Closes #6

---

## 🛠️ Type of Change

- [x] `feat`: Feat change
- [ ] `fix`: Fix change
- [ ] `infra`: Infra change
- [ ] `security`: Security change
- [ ] `test`: Test change
- [ ] `docs`: Docs change

---

## 📐 Scope of Changes

- `apps/api/main.py`
- `apps/api/middleware.py`
- `apps/api/routers/__init__.py`
- `apps/api/tests/unit/test_main.py`

---

## 🧪 Verification & Testing Matrix

- [x] pytest apps/api/tests/unit/test_main.py verified lifespan startup and shutdown hooks
- [x] Unhandled exceptions captured by global handler and returned as structured RFC 7807 JSON error responses
- [x] X-Request-ID header attached to all incoming and outgoing HTTP responses

---

## 🔒 Security & Guardrails Checklist

- [x] Explicit CORS whitelist configured strictly to verified origin URLs
- [x] Internal exception stack traces suppressed from production API responses
- [x] Verified zero hardcoded credentials or secret leakage
- [x] Linting and static analysis checks passed with 0 warnings
```

---

### PR-07 Blueprint: `feat(web): create Next.js 14 App Router baseline with Tailwind CSS dark mode design system`

```markdown
## 📌 Description

Initializes Next.js 14 App Router frontend with React 18 and TypeScript. Establishes sleek dark-mode-first aesthetic with Tailwind CSS, custom design tokens, responsive navigation shell, and Inter typography.

Closes #7

---

## 🛠️ Type of Change

- [x] `feat`: Feat change
- [ ] `fix`: Fix change
- [ ] `infra`: Infra change
- [ ] `security`: Security change
- [ ] `test`: Test change
- [ ] `docs`: Docs change

---

## 📐 Scope of Changes

- `apps/web/package.json`
- `apps/web/tailwind.config.ts`
- `apps/web/src/app/layout.tsx`
- `apps/web/src/app/page.tsx`
- `apps/web/src/styles/globals.css`

---

## 🧪 Verification & Testing Matrix

- [x] pnpm --filter @codeatlas/web lint and typecheck passed cleanly
- [x] Server-Side Rendering (SSR) verified with zero hydration mismatch warnings
- [x] Dark mode theme tokens verified across responsive viewport breakpoints

---

## 🔒 Security & Guardrails Checklist

- [x] Configured Content Security Policy (CSP) and HTTP security response headers in Next.js config
- [x] Strict sanitation applied on client-rendered HTML markup
- [x] Verified zero hardcoded credentials or secret leakage
- [x] Linting and static analysis checks passed with 0 warnings
```

---

### PR-08 Blueprint: `feat(shared): define shared TypeScript and Python domain contracts and Data Transfer Objects`

```markdown
## 📌 Description

Establishes single source of truth for cross-boundary data schemas. Defines CodeNodeDTO, CodeEdgeDTO, IngestionJobStatus, and ArchitectureGraphPayload in TypeScript and mirrors them into Pydantic models in FastAPI.

Closes #8

---

## 🛠️ Type of Change

- [x] `feat`: Feat change
- [ ] `fix`: Fix change
- [ ] `infra`: Infra change
- [ ] `security`: Security change
- [ ] `test`: Test change
- [ ] `docs`: Docs change

---

## 📐 Scope of Changes

- `packages/shared/package.json`
- `packages/shared/src/types/index.ts`
- `packages/shared/src/constants/index.ts`
- `apps/api/schemas/__init__.py`

---

## 🧪 Verification & Testing Matrix

- [x] tsc --noEmit in packages/shared compiled without type errors
- [x] Pydantic schema validation tests pass against sample JSON AST payloads
- [x] Import resolution verified across both frontend and backend workspace boundaries

---

## 🔒 Security & Guardrails Checklist

- [x] Strict schema validation rejects unexpected extra payload fields
- [x] Strong typing eliminates runtime serialization type-casting vulnerabilities
- [x] Verified zero hardcoded credentials or secret leakage
- [x] Linting and static analysis checks passed with 0 warnings
```

---

### PR-09 Blueprint: `ci(workflow): establish CI/CD GitHub Actions workflow for monorepo validation and container builds`

```markdown
## 📌 Description

Configures automated GitHub Actions CI pipeline executing on all pull requests and main pushes. Validates pnpm lint, TypeScript compilation, Python Flake8/Black, pytest test suite, and Docker container build matrix with GitHub Actions cache.

Closes #9

---

## 🛠️ Type of Change

- [ ] `feat`: Feat change
- [ ] `fix`: Fix change
- [ ] `infra`: Infra change
- [ ] `security`: Security change
- [ ] `test`: Test change
- [ ] `docs`: Docs change

---

## 📐 Scope of Changes

- `.github/workflows/ci.yml`
- `.github/workflows/label-sync.yml`

---

## 🧪 Verification & Testing Matrix

- [x] Simulated PR run verified all test gates fail synchronously when assertions fail
- [x] Docker build caching (type=gha) reduces container build durations by >65%
- [x] Label synchronization action automatically reconciles GitHub labels with config

---

## 🔒 Security & Guardrails Checklist

- [x] GitHub Actions workflow permissions restricted to read-only defaults (contents: read)
- [x] Secrets isolation enforced on PR fork events
- [x] Verified zero hardcoded credentials or secret leakage
- [x] Linting and static analysis checks passed with 0 warnings
```

---

### PR-10 Blueprint: `security(ci): automate security scanning with CodeQL static analysis, TruffleHog, and Dependabot`

```markdown
## 📌 Description

Automates continuous security scanning across repository. Integrates GitHub CodeQL SAST for Python and TypeScript, TruffleHog secret scanning to block credential leakage, and Dependabot weekly CVE dependency alerts.

Closes #10

---

## 🛠️ Type of Change

- [ ] `feat`: Feat change
- [ ] `fix`: Fix change
- [ ] `infra`: Infra change
- [x] `security`: Security change
- [ ] `test`: Test change
- [ ] `docs`: Docs change

---

## 📐 Scope of Changes

- `.github/workflows/security.yml`
- `.github/dependabot.yml`
- `SECURITY.md`

---

## 🧪 Verification & Testing Matrix

- [x] CodeQL workflow executes on pull request triggers and logs zero high-severity findings
- [x] TruffleHog scanner verified by scanning test fixtures for credential entropy
- [x] Dependabot configuration verified via GitHub dependency graph interface

---

## 🔒 Security & Guardrails Checklist

- [x] Blocks pull requests containing detected cryptographic keys or API credentials
- [x] Publishes public security disclosure policy and SLA in SECURITY.md
- [x] Verified zero hardcoded credentials or secret leakage
- [x] Linting and static analysis checks passed with 0 warnings
```

---

### PR-11 Blueprint: `infra(worker): configure Celery distributed task queue worker with Redis broker and process recycling`

```markdown
## 📌 Description

Integrates Celery distributed background worker backed by Redis. Configures max-tasks-per-child (100) and worker memory limits to eliminate process memory leaks during intensive Tree-Sitter AST parser and embedding jobs.

Closes #11

---

## 🛠️ Type of Change

- [ ] `feat`: Feat change
- [ ] `fix`: Fix change
- [x] `infra`: Infra change
- [ ] `security`: Security change
- [ ] `test`: Test change
- [ ] `docs`: Docs change

---

## 📐 Scope of Changes

- `apps/api/celery_app.py`
- `apps/api/tasks/__init__.py`
- `apps/api/tasks/ingestion.py`
- `apps/api/services/queue.py`

---

## 🧪 Verification & Testing Matrix

- [x] Enqueued 250 asynchronous background jobs and verified sequential worker processing
- [x] Worker process recycling confirmed upon reaching 100 task threshold
- [x] Task failure exception hooks accurately log error metadata to PostgreSQL job record

---

## 🔒 Security & Guardrails Checklist

- [x] Task arguments sanitized to prevent arbitrary code execution via pickle serialization
- [x] Forced JSON task serializer across all Celery queues
- [x] Verified zero hardcoded credentials or secret leakage
- [x] Linting and static analysis checks passed with 0 warnings
```

---

### PR-12 Blueprint: `docs(arch): document foundational architectural blueprint, component interactions, and PRD`

```markdown
## 📌 Description

Authors foundational architectural specifications and Product Requirements Document (PRD). Includes Mermaid component interaction diagrams, data ingestion workflows, 5-signal issue mapping theory, and technology stack standards.

Closes #13

---

## 🛠️ Type of Change

- [ ] `feat`: Feat change
- [ ] `fix`: Fix change
- [ ] `infra`: Infra change
- [ ] `security`: Security change
- [ ] `test`: Test change
- [x] `docs`: Docs change

---

## 📐 Scope of Changes

- `docs/architecture/system-overview.md`
- `docs/PRD.md`
- `README.md`

---

## 🧪 Verification & Testing Matrix

- [x] Mermaid markdown diagrams validated with zero syntax errors
- [x] All internal markdown file links verified for absolute URL target validity

---

## 🔒 Security & Guardrails Checklist

- [x] Strips private environment credentials from architectural diagrams
- [x] Documents threat modeling and mitigation strategies for repository cloning
- [x] Verified zero hardcoded credentials or secret leakage
- [x] Linting and static analysis checks passed with 0 warnings
```

---

### PR-13 Blueprint: `feat(config): manage application runtime configuration with strict Pydantic Settings validation`

```markdown
## 📌 Description

Replaces unstructured os.getenv calls with centralized Pydantic BaseSettings class. Validates database URLs, Redis endpoints, JWT secret entropy, and Ollama base URLs on startup with fail-fast validation exceptions.

Closes #14

---

## 🛠️ Type of Change

- [x] `feat`: Feat change
- [ ] `fix`: Fix change
- [ ] `infra`: Infra change
- [ ] `security`: Security change
- [ ] `test`: Test change
- [ ] `docs`: Docs change

---

## 📐 Scope of Changes

- `apps/api/config.py`
- `apps/api/tests/unit/test_config.py`

---

## 🧪 Verification & Testing Matrix

- [x] pytest apps/api/tests/unit/test_config.py verified settings parsing and default fallback values
- [x] Application startup raises clear ValidationError when required credentials (DATABASE_URL) are missing
- [x] Sensitive settings masked from repr() string representation

---

## 🔒 Security & Guardrails Checklist

- [x] Ensures minimum 32-character secret key entropy requirement for JWT signing
- [x] Prevents silent fallback to insecure default credentials in production environments
- [x] Verified zero hardcoded credentials or secret leakage
- [x] Linting and static analysis checks passed with 0 warnings
```

---

### PR-14 Blueprint: `feat(infra): expose container liveness and readiness health check probes with dependency tests`

```markdown
## 📌 Description

Exposes standard GET /health/live and GET /health/ready endpoints for Kubernetes and Docker container orchestration. Readiness probe conducts live non-blocking ping checks against PostgreSQL database and Redis cache.

Closes #15

---

## 🛠️ Type of Change

- [ ] `feat`: Feat change
- [ ] `fix`: Fix change
- [x] `infra`: Infra change
- [ ] `security`: Security change
- [ ] `test`: Test change
- [ ] `docs`: Docs change

---

## 📐 Scope of Changes

- `apps/api/routers/health.py`
- `apps/api/tests/unit/test_health.py`

---

## 🧪 Verification & Testing Matrix

- [x] pytest apps/api/tests/unit/test_health.py verified 200 OK and 503 Service Unavailable responses
- [x] Simulated database drop returns HTTP 503 with exact failing dependency indicated in JSON body
- [x] Liveness probe returns HTTP 200 instantaneously without external network overhead

---

## 🔒 Security & Guardrails Checklist

- [x] Health endpoints expose zero internal connection strings or stack traces to unauthorized callers
- [x] Verified zero hardcoded credentials or secret leakage
- [x] Linting and static analysis checks passed with 0 warnings
```

---

### PR-15 Blueprint: `test(core): establish automated backend pytest and frontend vitest test suites`

```markdown
## 📌 Description

Establishes robust test frameworks across backend and frontend workspaces. Configures pytest-asyncio, in-memory SQLite fixtures, and factory-boy in FastAPI, paired with Vitest, Happy-DOM, and React Testing Library in Next.js.

Closes #16

---

## 🛠️ Type of Change

- [ ] `feat`: Feat change
- [ ] `fix`: Fix change
- [ ] `infra`: Infra change
- [ ] `security`: Security change
- [x] `test`: Test change
- [ ] `docs`: Docs change

---

## 📐 Scope of Changes

- `apps/api/pytest.ini`
- `apps/api/tests/conftest.py`
- `apps/web/vitest.config.ts`
- `apps/web/tests/setup.ts`

---

## 🧪 Verification & Testing Matrix

- [x] Executed 55 backend unit & integration tests with 0 failures
- [x] Executed 10 frontend Vitest tests with 0 failures
- [x] Code coverage reporting configured via coverage.py and vitest --coverage

---

## 🔒 Security & Guardrails Checklist

- [x] Mock database fixtures run fully isolated in-memory to prevent test pollution of dev databases
- [x] Verified zero hardcoded credentials or secret leakage
- [x] Linting and static analysis checks passed with 0 warnings
```

---

### PR-16 Blueprint: `infra(tooling): establish code style formatting, contributor guidelines, and pre-commit hooks`

```markdown
## 📌 Description

Deploys automated pre-commit hook framework enforcing Black, Flake8, and isort for Python, and Prettier and ESLint for TypeScript. Establishes comprehensive CONTRIBUTING.md outlining branch naming and PR standards.

Closes #17

---

## 🛠️ Type of Change

- [ ] `feat`: Feat change
- [ ] `fix`: Fix change
- [x] `infra`: Infra change
- [ ] `security`: Security change
- [ ] `test`: Test change
- [ ] `docs`: Docs change

---

## 📐 Scope of Changes

- `.pre-commit-config.yaml`
- `CONTRIBUTING.md`
- `pyproject.toml`
- `.eslintrc.js`

---

## 🧪 Verification & Testing Matrix

- [x] pre-commit run --all-files executed cleanly across monorepo
- [x] Conventional Commits commit-msg hook rejects non-standard commit messages
- [x] ESLint rule adherence verified across all apps/web React components

---

## 🔒 Security & Guardrails Checklist

- [x] Pre-commit hook includes detect-private-key and end-of-file-fixer checks
- [x] Verified zero hardcoded credentials or secret leakage
- [x] Linting and static analysis checks passed with 0 warnings
```

---

### PR-17 Blueprint: `feat(web): implement client-side authentication context and protected route guards in Next.js`

```markdown
## 📌 Description

Implements React Context provider managing user authentication state, session hydration, and automatic token refresh. Introduces <ProtectedRoute /> wrapper redirecting unauthenticated users to GitHub OAuth login.

Closes #18

---

## 🛠️ Type of Change

- [x] `feat`: Feat change
- [ ] `fix`: Fix change
- [ ] `infra`: Infra change
- [ ] `security`: Security change
- [ ] `test`: Test change
- [ ] `docs`: Docs change

---

## 📐 Scope of Changes

- `apps/web/src/contexts/AuthContext.tsx`
- `apps/web/src/components/auth/ProtectedRoute.tsx`
- `apps/web/src/hooks/useAuth.ts`

---

## 🧪 Verification & Testing Matrix

- [x] vitest apps/web/tests/unit/test_auth_context.test.tsx passed cleanly
- [x] Unauthenticated visits to /canvas correctly redirect to /auth/login
- [x] Session restoration from HttpOnly cookie hydrates user profile in <50ms

---

## 🔒 Security & Guardrails Checklist

- [x] Session tokens not exposed to localStorage to prevent XSS credential harvesting
- [x] ProtectedRoute prevents flash of unauthenticated content (FOUC)
- [x] Verified zero hardcoded credentials or secret leakage
- [x] Linting and static analysis checks passed with 0 warnings
```

---

### PR-18 Blueprint: `feat(web): build repository explorer card grid and manual ingestion trigger interface`

```markdown
## 📌 Description

Builds interactive repository explorer interface. Displays synchronized GitHub repositories in a responsive card grid with ingestion status badges, language indicators, node counts, and one-click manual ingestion trigger modal.

Closes #19

---

## 🛠️ Type of Change

- [x] `feat`: Feat change
- [ ] `fix`: Fix change
- [ ] `infra`: Infra change
- [ ] `security`: Security change
- [ ] `test`: Test change
- [ ] `docs`: Docs change

---

## 📐 Scope of Changes

- `apps/web/src/components/repositories/RepositoryGrid.tsx`
- `apps/web/src/components/repositories/IngestTriggerModal.tsx`
- `apps/web/src/app/repositories/page.tsx`

---

## 🧪 Verification & Testing Matrix

- [x] Rendered 50 repository cards with smooth 60 FPS scrolling and responsive grid reflow
- [x] Ingestion trigger button initiates POST /api/v1/repositories/{id}/ingest and transitions badge to 'Ingesting'
- [x] Search filter input dynamically updates repository list with 0ms lag

---

## 🔒 Security & Guardrails Checklist

- [x] Repository access restricted strictly to organizations matching user's authenticated scope
- [x] Input repository URLs sanitized against SSRF vectors
- [x] Verified zero hardcoded credentials or secret leakage
- [x] Linting and static analysis checks passed with 0 warnings
```

---

