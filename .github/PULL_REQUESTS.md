# CodeAtlas Pull Request Guide & Execution Blueprints

This document outlines the pull request workflow, review standards, and active Pull Request specifications for the CodeAtlas engineering team.

---

## 📌 Active Pull Request Catalog

| PR ID | Branch Name | Title | Linked Issue | Target | Status |
|---|---|---|---|---|---|
| `PR-01` | `feat/1-tree-sitter-parser` | `feat(ingestion): implement tree-sitter AST parser pipeline and symbol extractor` | Closes `#1` | `main` | Open |
| `PR-02` | `fix/9-async-db-pool-leak` | `fix(api): resolve async database connection pool leak on batch edge upsert` | Fixes `#9` | `main` | In Review |
| `PR-03` | `feat/5-react-flow-virtualization` | `feat(web): add React Flow virtualized node renderer and directory cluster nodes` | Closes `#5` | `main` | Approved |
| `PR-04` | `security/10-webhook-hmac-verifier` | `security(auth): enforce strict webhook HMAC SHA-256 signature verification` | Fixes `#10` | `main` | Merged |
| `PR-05` | `fix/11-ci-error-gates` | `fix(ci): eliminate error suppressions and enforce strict test gates` | Fixes `#11` | `main` | Open |
| `PR-06` | `security/12-docker-trivy-scan` | `security(ci): integrate PR Docker build validation and Trivy vulnerability scanner` | Fixes `#12`, `#14` | `main` | Open |
| `PR-07` | `test/13-playwright-e2e-ci` | `test(e2e): automate Playwright browser testing pipeline in GitHub Actions` | Closes `#13` | `main` | Open |
| `PR-08` | `fix/16-health-metrics-exporter` | `fix(api): eliminate health check loopback recursion and add Prometheus metrics` | Fixes `#16` | `main` | Open |

---

## Detailed PR Blueprints & Specifications

### PR-01 Blueprint: `feat(ingestion): implement tree-sitter AST parser pipeline and symbol extractor`

```markdown
## 📌 Description

This PR implements the core Tree-Sitter AST parsing engine for Python, TypeScript, and JavaScript source files. It establishes the `BaseParser` abstract class and concrete parser sub-classes capable of extracting structural entity nodes (`CodeNode`) and relational import edges (`CodeEdge`).

Closes #1

---

## 🛠️ Type of Change

- [x] `feat`: New feature (non-breaking change adding functionality)
- [ ] `fix`: Bug fix
- [ ] `perf`: Performance optimization
- [ ] `refactor`: Code change

---

## 📐 Scope of Changes

- `apps/api/parsers/base.py`: Abstract AST parser interface
- `apps/api/parsers/python.py`: Tree-Sitter Python grammar parser
- `apps/api/parsers/javascript.py`: Tree-Sitter TS/JS grammar parser
- `apps/api/tests/unit/test_parsers.py`: Unit test suite for AST symbol extraction

---

## 🧪 Verification & Testing Matrix

- [x] `pnpm lint` passed with 0 warnings
- [x] `pnpm typecheck` passed cleanly
- [x] `pytest apps/api/tests/unit/test_parsers.py` passed with 94% coverage

```bash
# Executed unit tests locally
cd apps/api
pytest tests/unit/test_parsers.py -v --cov=parsers
```

---

## 🔒 Security Checklist

- [x] Sanitized file path inputs against path traversal attacks (`os.path.abspath`)
- [x] Memory bounded AST node traversal limits (Max depth: 100)
- [x] No credentials or secrets hardcoded in test fixtures
```

---

### PR-02 Blueprint: `fix(api): resolve async database connection pool leak on batch edge upsert`

```markdown
## 📌 Description

Resolves connection pool exhaustion during batch graph edge upserts by refactoring session lifecycle management to use `async with async_session_factory()` context managers and increasing default QueuePool limits to 50 connections with automatic overflow recycling.

Fixes #9

---

## 🛠️ Type of Change

- [ ] `feat`: New feature
- [x] `fix`: Bug fix (non-breaking change fixing an issue)
- [x] `perf`: Performance optimization

---

## 📐 Scope of Changes

- `apps/api/database.py`: Increased connection pool overflow and pool_recycle configuration
- `apps/api/services/mapping/graph_builder.py`: Wrapped bulk upserts in explicit context managers with statement retries

---

## 🧪 Verification & Testing Matrix

- [x] Executed high-concurrency load test (`100` parallel edge upsert batches)
- [x] Verified zero `TimeoutError: QueuePool limit overflowed` exceptions in FastAPI logs
- [x] `pytest apps/api/tests/integration/test_database.py` passed
```

---

### PR-03 Blueprint: `feat(web): add React Flow virtualized node renderer and directory cluster nodes`

```markdown
## 📌 Description

Introduces node virtualization and collapsible directory clustering within the React Flow architecture graph canvas. This optimization reduces DOM node rendering count from 2,000+ elements down to active viewport nodes (~150 elements), maintaining a steady 60 FPS frame rate.

Closes #5

---

## 🛠️ Type of Change

- [x] `feat`: New feature (non-breaking change adding functionality)
- [x] `perf`: Performance optimization

---

## 📐 Scope of Changes

- `apps/web/src/components/canvas/GraphCanvas.tsx`: Integrated viewport node virtualization
- `apps/web/src/components/canvas/DirectoryClusterNode.tsx`: Added collapsible directory cluster node component
- `apps/web/src/hooks/useGraphLayout.ts`: Offloaded Dagre layout math to Web Worker thread

---

## 🧪 Verification & Testing Matrix

- [x] `pnpm lint` and `pnpm typecheck` passed
- [x] Chrome DevTools performance profiling confirmed 60 FPS viewport panning on 2,500-node graph
```

---

### PR-04 Blueprint: `security(auth): enforce strict webhook HMAC SHA-256 signature verification`

```markdown
## 📌 Description

Implements constant-time HMAC SHA-256 signature verification (`X-Hub-Signature-256`) and replay protection timestamp checks on GitHub webhook endpoints. Unsigned or corrupted payloads are immediately rejected with HTTP 401.

Fixes #10

---

## 🛠️ Type of Change

- [ ] `feat`: New feature
- [ ] `fix`: Bug fix
- [x] `security`: Security patch / hardening

---

## 📐 Scope of Changes

- `apps/api/routers/webhooks.py`: Added `verify_github_signature` dependency middleware
- `apps/api/services/auth.py`: Constant-time string comparator (`hmac.compare_digest`)
- `apps/api/tests/unit/test_webhooks.py`: Unit tests verifying valid, invalid, and forged webhook signatures

---

## 🔒 Security Checklist

- [x] Mitigated timing attacks using `hmac.compare_digest`
- [x] Enforced secret key rotation handling via environment variable `GITHUB_WEBHOOK_SECRET`
- [x] Verified 100% test coverage on authentication middleware
```

---

### PR-05 Blueprint: `fix(ci): eliminate error suppressions and enforce strict test gates`

```markdown
## 📌 Description

Removes `|| true` error suppressions across `lint-python` and `test` jobs in `.github/workflows/ci.yml`. Enforces strict MyPy type checking, pytest assertion gates, and JUnit XML test reporting.

Fixes #11

---

## 🛠️ Type of Change

- [ ] `feat`: New feature
- [x] `fix`: Bug fix
- [x] `chore`: CI/CD automation update

---

## 📐 Scope of Changes

- `.github/workflows/ci.yml`: Removed `|| true` flags, configured strict MyPy checks and pytest JUnit output
- `apps/api/main.py`: Fixed type annotations and missing return types

---

## 🧪 Verification & Testing Matrix

- [x] `pnpm lint` and `pnpm typecheck` passed
- [x] Verified GitHub Actions CI pipeline fails synchronously when a failing assertion is committed
```

---

### PR-06 Blueprint: `security(ci): integrate PR Docker build validation and Trivy vulnerability scanner`

```markdown
## 📌 Description

Extends Docker build matrix validation to pull request events and integrates `aquasecurity/trivy-action` container image security scanning to block critical CVE vulnerabilities before code merge.

Fixes #12, #14

---

## 🛠️ Type of Change

- [x] `security`: Security patch / hardening
- [x] `chore`: CI/CD automation update

---

## 📐 Scope of Changes

- `.github/workflows/ci.yml`: Enabled PR Docker build matrix with `push: false`
- `.github/workflows/security.yml`: Added Trivy container scanner step and CodeQL SAST workflow

---

## 🔒 Security Checklist

- [x] Configured Trivy scanner to fail build on Critical and High severity CVEs
- [x] Cached Docker build layers using GitHub Actions cache backend (`type=gha`)
```

---

### PR-07 Blueprint: `test(e2e): automate Playwright browser testing pipeline in GitHub Actions`

```markdown
## 📌 Description

Adds an automated Playwright end-to-end testing job (`test-e2e`) within `.github/workflows/ci.yml` backed by PostgreSQL + pgvector and Redis GitHub Actions service containers.

Closes #13

---

## 🛠️ Type of Change

- [x] `test`: E2E test additions
- [x] `chore`: CI/CD automation update

---

## 📐 Scope of Changes

- `.github/workflows/ci.yml`: Added `test-e2e` job with Chromium dependencies and service containers
- `apps/web/playwright.config.ts`: Configured trace mode, screenshot capture on failure, and HTML reporter

---

## 🧪 Verification & Testing Matrix

- [x] Executed `pnpm test:e2e` locally against dev containers
- [x] Verified Playwright HTML test report artifacts upload cleanly on GitHub Actions failure
```

---

### PR-08 Blueprint: `fix(api): eliminate health check loopback recursion and add Prometheus metrics`

```markdown
## 📌 Description

Refactors `/health` endpoint in `apps/api/main.py` to eliminate loopback HTTP requests to `/ready`, avoiding event loop socket exhaustion under heavy request throughput. Adds Prometheus metrics middleware exposing request histograms on `/metrics`.

Fixes #16

---

## 🛠️ Type of Change

- [x] `fix`: Bug fix
- [x] `perf`: Performance optimization

---

## 📐 Scope of Changes

- `apps/api/main.py`: Replaced `httpx.AsyncClient` call in `/health` with direct internal function call
- `apps/api/middleware.py`: Added Prometheus request duration and status counter metrics middleware

---

## 🧪 Verification & Testing Matrix

- [x] Loaded `/health` with `1,000` concurrent requests; verified zero socket timeouts
- [x] Verified `/metrics` returns OpenMetrics formatted counters and duration buckets
```
