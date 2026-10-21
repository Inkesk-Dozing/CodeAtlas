# CodeAtlas GitHub Issue Catalog & Backlog

This document maintains the complete catalog of production issues for CodeAtlas, mapped against product phases, components, priorities, and technical specifications.

---

## 📌 Issue Catalog Summary

| ID | Title | Component | Type | Priority | Milestone | Status |
|---|---|---|---|---|---|---|
| `#1` | Implement Tree-Sitter AST Parser Framework | Ingestion Engine | Feature | `P0` | M1: Ingestion | Ready |
| `#2` | Integrate pgvector HNSW Index & Embedding Pipeline | Vector DB | Feature | `P0` | M1: Ingestion | Ready |
| `#3` | Celery Ingestion Worker Memory Leak on Reparsing | Ingestion Engine | Bug | `P1` | M1: Ingestion | Investigating |
| `#4` | Hybrid Keyword-Vector Search for Issue Mapping | Issue Mapper | Feature | `P0` | M2: Issue Mapping | Ready |
| `#5` | React Flow Virtualization & Directory Clustering | Canvas UX | Feature | `P1` | M2: Issue Mapping | Ready |
| `#6` | RAG Context Assembly & Streaming Ollama Endpoint | AI & Docs | Feature | `P0` | M3: AI & Docs | Ready |
| `#7` | PostgreSQL Row-Level Security (RLS) Enforcer | Multi-Tenant DB | Security | `P0` | M4: Beta Launch | Ready |
| `#8` | Stripe Billing Integration & Quotas Metering | Billing | Feature | `P1` | M4: Beta Launch | Ready |
| `#9` | Async DB Connection Pool Contention on Batch Edge Upsert | API & DB | Bug | `P1` | M1: Ingestion | In Progress |
| `#10` | Webhook HMAC SHA-256 Verification & Replay Guard | Security / Auth | Security | `P0` | M0: Foundation | Ready |
| `#11` | Fix Error Swallowing in GitHub Actions Workflow | CI/CD | Bug | `P0` | M0: Foundation | Ready |
| `#12` | PR Docker Build Validation & Trivy Container Scan | CI/CD | Security | `P1` | M0: Foundation | Ready |
| `#13` | Playwright E2E Testing Automation Pipeline | CI/CD | Testing | `P1` | M4: Beta Launch | Ready |
| `#14` | CodeQL SAST & Secret Scanning Workflow | Security | Security | `P0` | M0: Foundation | Ready |
| `#15` | Turborepo & Pip Dependency Caching Layer | CI/CD | Performance | `P2` | M0: Foundation | Ready |
| `#16` | Resolve API Health Check Loopback & Add Metrics | API & Monitoring | Bug | `P1` | M4: Beta Launch | Ready |

---

## Detailed Issue Specifications

### Issue #1: `[FEAT]: Implement Tree-Sitter AST Parser Framework for Multi-Language Ingestion`
- **Labels**: `enhancement`, `ingestion-engine`, `priority:P0`, `phase-1`
- **Component**: `apps/api/parsers`
- **Description**:  
  Construct a extensible Tree-Sitter AST parsing engine capable of extracting entity nodes (functions, classes, decorators, routes, imports) from Python (`.py`), TypeScript (`.ts`), and JavaScript (`.js`) files during repository cloning.
- **Acceptance Criteria**:
  - [ ] Implement `BaseParser` abstract class in `apps/api/parsers/base.py`.
  - [ ] Concrete parsers for Python (`python.py`) and TypeScript/JavaScript (`javascript.py`).
  - [ ] Extract import references, export signatures, class inheritance hierarchy, and route annotations.
  - [ ] Unit test coverage >= 90% across sample monorepo fixtures in `apps/api/tests/unit`.

---

### Issue #2: `[FEAT]: Integrate pgvector HNSW Index & Embedding Pipeline`
- **Labels**: `enhancement`, `database`, `ai-engine`, `priority:P0`, `phase-1`
- **Component**: `apps/api/services/ingestion`
- **Description**:  
  Integrate pgvector vector extension into PostgreSQL and construct a batch embedding service utilizing Sentence-Transformers / Ollama (`nomic-embed-text`) to compute vectors for generated `CodeNode` records.
- **Acceptance Criteria**:
  - [ ] Alembic migration enabling `vector` extension and adding `embedding vector(768)` column to `code_nodes`.
  - [ ] Build HNSW vector index (`m=16`, `ef_construction=64`).
  - [ ] Asynchronous embedding batch processing service with Redis task throttling.
  - [ ] Cosine similarity query endpoint returning top-$K$ nearest AST node matches.

---

### Issue #3: `[BUG]: Celery Ingestion Worker Memory Leak on Large Repository Reparsing`
- **Labels**: `bug`, `ingestion-engine`, `performance`, `priority:P1`
- **Component**: `apps/api/tasks/ingestion_tasks.py`
- **Description**:  
  When re-ingesting monorepos containing > 2,000 source files, Celery worker memory consumption steadily climbs and triggers Linux OOM killer termination.
- **Steps to Reproduce**:
  1. Trigger ingestion on a 2,500 file monorepo.
  2. Perform sequential push re-ingestion triggers 5 times.
  3. Observe Celery worker process resident set size (RSS) exceeding 2.5 GB.
- **Expected Behavior**: Worker memory should be garbage collected after task completion or isolated via worker child process recycling (`max_tasks_per_child=10`).

---

### Issue #4: `[FEAT]: Construct Hybrid Keyword-Vector Search Engine for GitHub Issue Mapping`
- **Labels**: `enhancement`, `issue-mapping`, `priority:P0`, `phase-2`
- **Component**: `apps/api/routers/issues.py` & `apps/api/services/mapping`
- **Description**:  
  Combine TF-IDF keyword regex extraction with pgvector semantic vector search to rank source files relevant to an incoming GitHub issue with confidence scores.
- **Acceptance Criteria**:
  - [ ] Extract file names, route paths, error stack traces, and class names from issue text.
  - [ ] Weighted scoring algorithm combining exact symbol match (40%), vector cosine similarity (40%), and 1-hop graph neighbor weight (20%).
  - [ ] Precision@5 evaluation score > 75% across test golden set.

---

### Issue #5: `[FEAT]: React Flow Subgraph Virtualization & Directory Clustering Renderer`
- **Labels**: `frontend`, `canvas-ux`, `priority:P1`, `phase-2`
- **Component**: `apps/web/src/components/canvas`
- **Description**:  
  Implement canvas node virtualization and directory clustering in React Flow to maintain 60 FPS rendering performance on graphs exceeding 2,000 nodes.
- **Acceptance Criteria**:
  - [ ] Group AST nodes into collapsible directory clusters.
  - [ ] Viewport node virtualization (only render visible nodes in screen viewport).
  - [ ] Dagre hierarchical layout calculation executed in Web Worker thread.

---

### Issue #6: `[FEAT]: RAG Context Assembly & Streaming Ollama Endpoint`
- **Labels**: `enhancement`, `ai-engine`, `rag`, `priority:P0`, `phase-3`
- **Component**: `apps/api/routers/graph.py` & `apps/api/services/rag.py`
- **Description**:  
  Build Retrieval-Augmented Generation (RAG) context assembly pipeline connecting pgvector node matches with local Ollama (`codellama:7b`) inference, returning streaming SSE responses to the frontend.
- **Acceptance Criteria**:
  - [ ] Context window retriever fetching top-5 node code snippets.
  - [ ] Server-Sent Events (SSE) streaming API endpoint `/api/v1/chat/stream`.
  - [ ] Markdown file path citation generation.

---

### Issue #7: `[SECURITY]: PostgreSQL Row-Level Security (RLS) Policy Enforcement for Multi-Tenancy`
- **Labels**: `security`, `database`, `multi-tenant`, `priority:P0`, `phase-4`
- **Component**: `apps/api/migrations` & `apps/api/models`
- **Description**:  
  Implement strict Row-Level Security (RLS) policies across PostgreSQL tables (`repositories`, `code_nodes`, `code_edges`, `issues`) to guarantee tenant sandbox isolation.
- **Acceptance Criteria**:
  - [ ] Alembic migration enabling `ROW LEVEL SECURITY` on tenant tables.
  - [ ] RLS policy evaluating `current_setting('app.current_org_id')`.
  - [ ] Automated integration test proving cross-tenant query attempts return zero rows.

---

### Issue #8: `[FEAT]: Stripe Billing Lifecycle Integration and Tier Quotas Metering`
- **Labels**: `enhancement`, `billing`, `saas`, `priority:P1`, `phase-4`
- **Component**: `apps/api/routers/billing.py`
- **Description**:  
  Integrate Stripe SDK for customer subscription management, invoice webhooks, and tier quota enforcement (Free vs Pro vs Enterprise).
- **Acceptance Criteria**:
  - [ ] Stripe Checkout session creation for tier upgrades.
  - [ ] Stripe Webhook signature verification and event handler (`customer.subscription.updated`, `invoice.payment_failed`).
  - [ ] Middleware enforcing monthly ingestion & repository quotas per organization.

---

### Issue #9: `[FIX]: Async Database Connection Pool Contention on Batch Edge Upsert`
- **Labels**: `bug`, `database`, `performance`, `priority:P1`
- **Component**: `apps/api/database.py` & `apps/api/services/graph_builder.py`
- **Description**:  
  Concurrent batch graph edge upserts cause asyncpg connection pool starvation under heavy worker load, throwing `TimeoutError: QueuePool limit of size 20 overflowed`.
- **Expected Behavior**: Connection pool should gracefully queue or expand to max capacity (50 connections) with statement retries.

---

### Issue #10: `[SECURITY]: Enforce Webhook HMAC SHA-256 Signature Verification & Replay Guard`
- **Labels**: `security`, `auth`, `priority:P0`, `phase-0`
- **Component**: `apps/api/routers/webhooks.py`
- **Description**:  
  Implement robust HMAC SHA-256 signature verification (`X-Hub-Signature-256`) and timestamp replay guards on all GitHub webhook endpoints.
- **Acceptance Criteria**:
  - [ ] Reject requests missing valid `X-Hub-Signature-256` header with 401 Unauthorized.
  - [ ] Constant-time signature comparison (`hmac.compare_digest`) preventing timing attacks.
  - [ ] Replay attack window validation (timestamp within 300 seconds).

---

### Issue #11: `[CI/CD]: Fix Error Swallowing in GitHub Actions Workflow and Enforce Strict Test Gates`
- **Labels**: `ci-cd`, `bug`, `priority:P0`, `phase-0`
- **Component**: `.github/workflows/ci.yml`
- **Description**:  
  In `.github/workflows/ci.yml`, steps `lint-python` and `test` append `|| true` to execution commands (`mypy`, `pnpm test`, `pytest`). This swallows test and type checking failures, allowing broken builds to report green status and merge into `main`.
- **Acceptance Criteria**:
  - [ ] Remove all `|| true` error suppressions from `.github/workflows/ci.yml`.
  - [ ] Fix underlying lint/type failures in Python and TypeScript workspaces so CI passes natively.
  - [ ] Configure `pytest` with JUnit XML report artifact generation for GitHub Actions step summaries.

---

### Issue #12: `[CI/CD]: Add Pull Request Docker Build Validation & Container Vulnerability Scanning`
- **Labels**: `ci-cd`, `security`, `priority:P1`, `phase-0`
- **Component**: `.github/workflows/ci.yml`
- **Description**:  
  Docker container builds currently run only on push triggers to `main`. Pull Requests targeting `main` fail to validate container builds or catch unvetted container CVE vulnerabilities before merge.
- **Acceptance Criteria**:
  - [ ] Enable Docker build matrix validation on `pull_request` triggers (setting `push: false`).
  - [ ] Integrate `aquasecurity/trivy-action` step to scan built `api` and `web` images for Critical and High severity vulnerabilities.
  - [ ] Configure layer caching using GitHub Actions cache backend (`type=gha`).

---

### Issue #13: `[CI/CD]: Implement Automated Playwright E2E Testing Pipeline in GitHub Actions`
- **Labels**: `ci-cd`, `testing`, `frontend`, `priority:P1`, `phase-4`
- **Component**: `.github/workflows/ci.yml` & `apps/web/playwright.config.ts`
- **Description**:  
  The workspace defines `pnpm test:e2e` in `package.json`, but lacks automated execution in GitHub Actions CI.
- **Acceptance Criteria**:
  - [ ] Add `test-e2e` job in `ci.yml` with headless Chromium browser installation.
  - [ ] Provision PostgreSQL + pgvector and Redis GitHub Actions service containers for E2E runs.
  - [ ] Upload Playwright HTML test reports and trace zip artifacts on build failures.

---

### Issue #14: `[SECURITY]: Integrate CodeQL Static Analysis (SAST) and Secret Scanning Pipeline`
- **Labels**: `security`, `ci-cd`, `priority:P0`, `phase-0`
- **Component**: `.github/workflows/security.yml`
- **Description**:  
  Automate static application security testing (SAST) and hardcoded secret scanning across all PRs and default branch commits.
- **Acceptance Criteria**:
  - [ ] Create `.github/workflows/security.yml` executing CodeQL for Python and JavaScript/TypeScript.
  - [ ] Integrate Gitleaks / TruffleHog action to detect hardcoded API keys, JWT secrets, and AWS credentials.
  - [ ] Upload SARIF report results to the GitHub Security tab.

---

### Issue #15: `[CI/CD]: Enable Turborepo & Pip Dependency Caching Layer for Accelerated Builds`
- **Labels**: `ci-cd`, `performance`, `priority:P2`, `phase-0`
- **Component**: `.github/workflows/ci.yml`
- **Description**:  
  CI workflow executions re-download pip wheels and re-execute Turbo tasks without caching `.turbo` outputs, causing inflated workflow run times.
- **Acceptance Criteria**:
  - [ ] Add `actions/cache` step targeting `.turbo` build outputs directory.
  - [ ] Add `actions/cache` step targeting `~/.cache/pip` wheel cache directory.
  - [ ] Reduce total CI execution time by >= 40%.

---

### Issue #16: `[FIX]: Resolve API Health Check Loopback Contention and Implement Prometheus Exporter`
- **Labels**: `bug`, `api`, `monitoring`, `priority:P1`, `phase-4`
- **Component**: `apps/api/main.py`
- **Description**:  
  In `apps/api/main.py` lines 101-106, `/health` makes an asynchronous HTTP request back to `http://localhost:8000/ready` via `httpx.AsyncClient()`. Under high load, this causes socket loopback contention and false health probe failures.
- **Acceptance Criteria**:
  - [ ] Refactor `/health` to execute direct internal function call to readiness logic without loopback HTTP calls.
  - [ ] Add Prometheus metrics middleware tracking request duration histograms and status code counters.
  - [ ] Expose `/metrics` returning standard OpenMetrics formatted data.

