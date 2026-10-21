# CodeAtlas Engineering Issue Backlog & Architecture Matrix

This directory maintains the complete, professional backlog of **118 technical specifications and engineering issues** for **CodeAtlas** and **CodeAtlas Prime**, systematically mapped across all development phases from initialization to enterprise scale.

---

## 🧭 Backlog Overview & Phase Navigation

The issues are organized into six distinct modular phase documents:

| Phase Document | Phase Title | Issue Range | Focus Areas | Status |
|---|---|---|---|---|
| **[00-phase-0-foundation.md](./00-phase-0-foundation.md)** | **Phase 0: Foundation & Core Skeleton** | `#001` – `#018` | Turborepo, Docker Compose, OAuth, FastAPI lifespan, Alembic, Next.js, CI/CD | `100% Completed` |
| **[01-phase-1-ingestion-graph.md](./01-phase-1-ingestion-graph.md)** | **Phase 1: Ingestion & Graph Building** | `#019` – `#038` | Shallow cloner, AST parsers, route/ORM extraction, pgvector HNSW, Celery | `90% Completed` |
| **[02-phase-2-mapping-search.md](./02-phase-2-mapping-search.md)** | **Phase 2: Canvas UX & Issue Mapping** | `#039` – `#058` | React Flow custom nodes, Dagre layout, 5-signal issue ranker, hybrid search | `85% Completed` |
| **[03-phase-3-ai-docs-rag.md](./03-phase-3-ai-docs-rag.md)** | **Phase 3: AI Summaries & RAG Q&A** | `#059` – `#078` | Ollama inference, living docs, complexity metrics, streaming SSE, citations | `80% Completed` |
| **[04-phase-4-saas-production.md](./04-phase-4-saas-production.md)** | **Phase 4: Multi-Tenant SaaS & Polish** | `#079` – `#098` | RLS isolation, Stripe billing, API keys, Playwright E2E, Kubernetes Helm | `40% Ready / Active` |
| **[05-phase-5-prime-advanced.md](./05-phase-5-prime-advanced.md)** | **Phase 5: CodeAtlas Prime Convergence** | `#099` – `#118` | PR blast radius bot, architecture linter, bus factor, churn heatmap, IDE extensions | `Planned / Roadmap` |

---

## 📊 Current Verification & Implementation State

The core architecture for Phases 0, 1, 2, and 3 has already been coded and verified in the active codebase:

```text
Backend:    55 unit & integration tests passing (pytest in apps/api)
Frontend:   10 unit tests passing (vitest in apps/web)
Typecheck:  tsc --noEmit clean across apps/web and packages/shared
Routes:     29 FastAPI routes implemented across 9 core controllers
Database:   15 relational tables with Alembic async migrations + pgvector HNSW
Canvas:     React Flow canvas with custom nodes, BFS layout & minimap
```

---

## 📋 Complete Master Issue Catalog (118 Issues)

### Phase 0: Foundation, Infrastructure & Core Skeleton (`#001` - `#018`)

| ID | Title | Component | Type | Priority | Status |
|---|---|---|---|---|---|
| `#001` | [Monorepo Orchestration with Turborepo & pnpm Workspaces](./00-phase-0-foundation.md#issue-001-feat-monorepo-orchestration-with-turborepo--pnpm-workspaces) | `infra` | Feature | `P0` | `Completed` |
| `#002` | [Multi-Container Local Development Stack with Docker Compose](./00-phase-0-foundation.md#issue-002-infra-multi-container-local-development-stack-with-docker-compose) | `infra` | Infra | `P0` | `Completed` |
| `#003` | [GitHub App Registration & Webhook Receiver with HMAC-SHA256](./00-phase-0-foundation.md#issue-003-feat-github-app-registration--webhook-receiver-with-hmac-sha256-verification) | `apps/api` | Security | `P0` | `Completed` |
| `#004` | [GitHub OAuth 2.0 Flow & Dual-Mode JWT Authentication Service](./00-phase-0-foundation.md#issue-004-feat-github-oauth-20-flow--dual-mode-jwt-authentication-service) | `apps/api` | Feature | `P0` | `Completed` |
| `#005` | [Alembic Database Migration Framework & 15-Table Relational Schema](./00-phase-0-foundation.md#issue-005-feat-alembic-database-migration-framework--15-table-relational-schema) | `apps/api` | Feature | `P0` | `Completed` |
| `#006` | [FastAPI Lifecycle, Router Registry & Exception Middleware Stack](./00-phase-0-foundation.md#issue-006-feat-fastapi-application-lifecycle-router-registry--exception-middleware-stack) | `apps/api` | Feature | `P0` | `Completed` |
| `#007` | [Next.js 14 App Router Baseline & Modern Dark Mode Design System](./00-phase-0-foundation.md#issue-007-feat-nextjs-14-app-router-baseline--modern-dark-mode-design-system) | `apps/web` | Frontend | `P0` | `Completed` |
| `#008` | [Shared TypeScript Domain Contracts & Data Transfer Objects](./00-phase-0-foundation.md#issue-008-feat-shared-typescript-domain-contracts--data-transfer-objects) | `packages/shared` | Feature | `P1` | `Completed` |
| `#009` | [CI/CD GitHub Actions Pipeline for Monorepo Validation & Docker Builds](./00-phase-0-foundation.md#issue-009-test-cicd-github-actions-pipeline-for-monorepo-validation--docker-builds) | `ci-cd` | Test | `P0` | `Completed` |
| `#010` | [Automated Security Scanning with CodeQL, TruffleHog & Dependabot](./00-phase-0-foundation.md#issue-010-sec-automated-security-scanning-with-codeql-trufflehog--dependabot) | `ci-cd` | Security | `P0` | `Completed` |
| `#011` | [Celery Asynchronous Task Worker & Redis Broker Integration](./00-phase-0-foundation.md#issue-011-feat-celery-asynchronous-task-worker--redis-broker-integration) | `apps/api` | Infra | `P0` | `Completed` |
| `#012` | [Foundation Architectural Specifications & Technical System Blueprint](./00-phase-0-foundation.md#issue-012-docs-foundation-architectural-specifications--technical-system-blueprint) | `docs` | Docs | `P1` | `Completed` |
| `#013` | [Configuration Management with Pydantic Settings & Strict Validation](./00-phase-0-foundation.md#issue-013-feat-configuration-management-with-pydantic-settings--strict-validation) | `apps/api` | Feature | `P1` | `Completed` |
| `#014` | [Health, Liveness & Readiness Probes for Container Orchestration](./00-phase-0-foundation.md#issue-014-feat-health-liveness--readiness-probes-for-container-orchestration) | `apps/api` | Infra | `P1` | `Completed` |
| `#015` | [Comprehensive Backend & Frontend Unit Test Baseline](./00-phase-0-foundation.md#issue-015-test-comprehensive-backend--frontend-unit-test-baseline) | `apps/api` | Test | `P1` | `Completed` |
| `#016` | [Contributor Guidelines, Code Style & Pre-Commit Hook Baseline](./00-phase-0-foundation.md#issue-016-infra-contributor-guidelines-code-style--pre-commit-hook-baseline) | `infra` | Docs | `P2` | `Completed` |
| `#017` | [Next.js Authentication Context & Protected Route Guards](./00-phase-0-foundation.md#issue-017-feat-nextjs-authentication-context--protected-route-guards) | `apps/web` | Frontend | `P1` | `Completed` |
| `#018` | [Repository Explorer & Ingestion Trigger UI](./00-phase-0-foundation.md#issue-018-feat-repository-explorer--ingestion-trigger-ui) | `apps/web` | Frontend | `P1` | `Completed` |

---

### Phase 1: Ingestion Engine, AST Parsers & Graph Persistence (`#019` - `#038`)

| ID | Title | Component | Type | Priority | Status |
|---|---|---|---|---|---|
| `#019` | [Shallow Cloner with GitHub Installation Token & Sparse Checkout](./01-phase-1-ingestion-graph.md#issue-019-feat-shallow-repository-cloner-with-github-installation-token--sparse-checkout) | `ingestion` | Feature | `P0` | `Completed` |
| `#020` | [Base AST Parser Framework & Multi-Language Dispatch Registry](./01-phase-1-ingestion-graph.md#issue-020-feat-base-ast-parser-framework--multi-language-dispatch-registry) | `parsers` | Feature | `P0` | `Completed` |
| `#021` | [JavaScript & TypeScript AST Parser Engine](./01-phase-1-ingestion-graph.md#issue-021-feat-javascript--typescript-ast-parser-engine) | `parsers` | Feature | `P0` | `Completed` |
| `#022` | [Python AST Parser Engine with Decorator & Type Hint Analysis](./01-phase-1-ingestion-graph.md#issue-022-feat-python-ast-parser-engine-with-decorator--type-hint-analysis) | `parsers` | Feature | `P0` | `Completed` |
| `#023` | [Go Language AST Parser Integration (Packages, Structs & Interfaces)](./01-phase-1-ingestion-graph.md#issue-023-feat-go-language-ast-parser-integration-packages-structs--interfaces) | `parsers` | Feature | `P2` | `Ready` |
| `#024` | [Rust Language AST Parser Integration (Crates, Traits & Impls)](./01-phase-1-ingestion-graph.md#issue-024-feat-rust-language-ast-parser-integration-crates-traits--implementations) | `parsers` | Feature | `P2` | `Ready` |
| `#025` | [API Route Extraction Engine for Express, FastAPI, Next.js & Spring](./01-phase-1-ingestion-graph.md#issue-025-feat-api-route-extraction-engine-for-express-fastapi-nextjs--spring) | `ingestion` | Feature | `P1` | `Completed` |
| `#026` | [React/Vue Component & Hook Hierarchy Extraction](./01-phase-1-ingestion-graph.md#issue-026-feat-reactvue-component--hook-hierarchy-extraction) | `ingestion` | Feature | `P1` | `Completed` |
| `#027` | [Database ORM Model Extraction (Prisma, SQLAlchemy, Django ORM)](./01-phase-1-ingestion-graph.md#issue-027-feat-database-orm-model-extraction-prisma-sqlalchemy-django-orm) | `ingestion` | Feature | `P1` | `Completed` |
| `#028` | [Graph Persistence Layer with PostgreSQL Batch Upsert](./01-phase-1-ingestion-graph.md#issue-028-feat-graph-persistence-layer-with-high-speed-postgresql-batch-upsert) | `apps/api` | Perf | `P0` | `Completed` |
| `#029` | [Vector Embeddings Generation Pipeline with Local Ollama Inference](./01-phase-1-ingestion-graph.md#issue-029-feat-vector-embeddings-generation-pipeline-with-local-ollama-inference) | `ai-rag` | Feature | `P0` | `Completed` |
| `#030` | [pgvector HNSW Index Configuration & Fast Cosine Distance Queries](./01-phase-1-ingestion-graph.md#issue-030-feat-pgvector-hnsw-index-configuration--fast-cosine-distance-queries) | `vector-db` | Perf | `P0` | `Completed` |
| `#031` | [Incremental Git Diff Parser for Push Webhook Re-Indexing](./01-phase-1-ingestion-graph.md#issue-031-feat-incremental-git-diff-parser-for-push-webhook-re-indexing) | `ingestion` | Feature | `P1` | `Completed` |
| `#032` | [Real-Time Ingestion Progress Tracking via WebSocket & REST API](./01-phase-1-ingestion-graph.md#issue-032-feat-real-time-ingestion-pipeline-progress-tracking-via-websocket--rest-api) | `apps/api` | Feature | `P1` | `Completed` |
| `#033` | [Celery Worker Memory Leak Remediation & Process Recycling](./01-phase-1-ingestion-graph.md#issue-033-perf-celery-ingestion-worker-memory-leak-remediation--process-recycling) | `ingestion` | Perf | `P1` | `Completed` |
| `#034` | [Monorepo Package Boundary & Circular Dependency Detector](./01-phase-1-ingestion-graph.md#issue-034-feat-monorepo-workspace-package-boundary--circular-dependency-detector) | `ingestion` | Feature | `P1` | `Ready` |
| `#035` | [Tree-sitter Native Parser Integration (Upgrading from Regex)](./01-phase-1-ingestion-graph.md#issue-035-feat-tree-sitter-native-parser-integration-upgrading-from-regex) | `parsers` | Feature | `P1` | `Ready` |
| `#036` | [CodeNode & CodeEdge Composite Index Optimization for Subgraphs](./01-phase-1-ingestion-graph.md#issue-036-feat-codenode--codeedge-composite-index-optimization-for-subgraph-traversal) | `apps/api` | Perf | `P1` | `Completed` |
| `#037` | [Repository Health Check & Ingestion Failure Rollback Mechanism](./01-phase-1-ingestion-graph.md#issue-037-feat-repository-health-check--ingestion-failure-rollback-mechanism) | `ingestion` | Feature | `P2` | `Ready` |
| `#038` | [Synthetic Golden Monorepo Fixture & Parser Test Suite](./01-phase-1-ingestion-graph.md#issue-038-test-synthetic-golden-monorepo-fixture--parser-test-suite) | `parsers` | Test | `P1` | `Completed` |

---

### Phase 2: Interactive Canvas UX, Search & Issue Mapping (`#039` - `#058`)

| ID | Title | Component | Type | Priority | Status |
|---|---|---|---|---|---|
| `#039` | [React Flow Canvas with Custom AST Node Renderers](./02-phase-2-mapping-search.md#issue-039-feat-react-flow-canvas-initialization-with-custom-ast-node-renderers) | `apps/web` | Frontend | `P0` | `Completed` |
| `#040` | [Typed Edge Rendering with Animated Data Flow & Relationship Colors](./02-phase-2-mapping-search.md#issue-040-feat-typed-edge-rendering-with-animated-data-flow--relationship-colors) | `apps/web` | Frontend | `P1` | `Completed` |
| `#041` | [Dagre Hierarchical Layered Layout & BFS Depth Calculation Engine](./02-phase-2-mapping-search.md#issue-041-feat-dagre-hierarchical-layered-layout--bfs-depth-calculation-engine) | `apps/web` | Frontend | `P0` | `Completed` |
| `#042` | [Canvas Node Virtualization for 2,000+ Nodes at 60 FPS](./02-phase-2-mapping-search.md#issue-042-perf-canvas-node-virtualization-for-2000-nodes-at-60-fps) | `apps/web` | Perf | `P1` | `Ready` |
| `#043` | [Collapsible Directory & Monorepo Package Clustering](./02-phase-2-mapping-search.md#issue-043-feat-collapsible-directory--monorepo-package-clustering) | `apps/web` | Frontend | `P1` | `Ready` |
| `#044` | [Subgraph Exploration & Neighborhood Extraction API](./02-phase-2-mapping-search.md#issue-044-feat-subgraph-exploration--neighborhood-extraction-api) | `apps/api` | Feature | `P0` | `Completed` |
| `#045` | [Interactive Canvas Controls, Minimap & Center-on-Node Navigation](./02-phase-2-mapping-search.md#issue-045-feat-interactive-canvas-navigation-controls-minimap--center-on-node) | `apps/web` | Frontend | `P1` | `Completed` |
| `#046` | [GitHub Issues Fetcher with GraphQL Pagination & Comment Threads](./02-phase-2-mapping-search.md#issue-046-feat-github-issues-fetcher-service-with-graphql-pagination--comment-threads) | `apps/api` | Feature | `P0` | `Completed` |
| `#047` | [Issue Text Preprocessor (Code Blocks, Stack Traces & Symbols)](./02-phase-2-mapping-search.md#issue-047-feat-issue-text-preprocessor-code-block-extraction-stack-traces--symbols) | `mapping` | Feature | `P1` | `Completed` |
| `#048` | [Issue Intent Classifier (Bug, Feature, Refactor, Security, Docs)](./02-phase-2-mapping-search.md#issue-048-feat-issue-intent-classifier-bug-feature-refactor-security-docs) | `mapping` | Feature | `P1` | `Completed` |
| `#049` | [Signal 1: Semantic Candidate Retrieval via pgvector Cosine Distance](./02-phase-2-mapping-search.md#issue-049-feat-signal-1--semantic-issue-candidate-retrieval-via-pgvector-cosine-distance) | `mapping` | Feature | `P0` | `Completed` |
| `#050` | [Signal 2: Structural Heuristic Matcher via Trigram & Exact Symbol Match](./02-phase-2-mapping-search.md#issue-050-feat-signal-2--structural-heuristic-matcher-via-trigram--exact-symbol-match) | `mapping` | Feature | `P0` | `Completed` |
| `#051` | [Signal 3: Topological 1-Hop Graph Neighbor Propagation](./02-phase-2-mapping-search.md#issue-051-feat-signal-3--topological-1-hop-graph-neighbor-propagation-algorithm) | `mapping` | Feature | `P0` | `Completed` |
| `#052` | [Signal 4: Historical Reviewer Feedback Weighting](./02-phase-2-mapping-search.md#issue-052-feat-signal-4--historical-reviewer-feedback-weighting) | `mapping` | Feature | `P1` | `Completed` |
| `#053` | [Signal 5: Hotspot Degree Centrality Prioritization](./02-phase-2-mapping-search.md#issue-053-feat-signal-5--hotspot-degree-centrality-prioritization) | `mapping` | Feature | `P1` | `Completed` |
| `#054` | [5-Signal Combined Confidence Calibration & Tier Assignment](./02-phase-2-mapping-search.md#issue-054-feat-5-signal-combined-confidence-calibration--tier-assignment-highmedlow) | `mapping` | Feature | `P0` | `Completed` |
| `#055` | [Issue Detail Sidebar with Highlighting & Action Reasoning](./02-phase-2-mapping-search.md#issue-055-feat-issue-detail-sidebar-with-highlighting--suggested-action-reasoning) | `apps/web` | Frontend | `P0` | `Completed` |
| `#056` | [Node Detail Inspector Drawer (Code, Dependencies & Complexity)](./02-phase-2-mapping-search.md#issue-056-feat-node-detail-inspector-drawer-source-preview-relationships--complexity) | `apps/web` | Frontend | `P1` | `Completed` |
| `#057` | [Hybrid Natural Language Search API & Real-Time Query UI](./02-phase-2-mapping-search.md#issue-057-feat-hybrid-natural-language-search-api--real-time-query-ui) | `apps/api` | Feature | `P0` | `Completed` |
| `#058` | [Issue Mapping Golden Set Accuracy Evaluation Suite](./02-phase-2-mapping-search.md#issue-058-test-issue-mapping-golden-set-accuracy-evaluation-suite) | `mapping` | Test | `P1` | `Ready` |

---

### Phase 3: AI Summaries, Living Documentation & RAG Chat (`#059` - `#078`)

| ID | Title | Component | Type | Priority | Status |
|---|---|---|---|---|---|
| `#059` | [Local LLM Client Integration with Ollama & Model Fallback](./03-phase-3-ai-docs-rag.md#issue-059-feat-local-llm-client-integration-with-ollama-timeout--model-fallback) | `ai-rag` | Feature | `P0` | `Completed` |
| `#060` | [Directory-Level Architectural Purpose Summarizer](./03-phase-3-ai-docs-rag.md#issue-060-feat-directory-level-architectural-purpose-summarizer) | `ai-rag` | Feature | `P1` | `Completed` |
| `#061` | [Module, Class & Function Behavioral Summarizer](./03-phase-3-ai-docs-rag.md#issue-061-feat-module-class--function-behavioral-summarizer) | `ai-rag` | Feature | `P1` | `Completed` |
| `#062` | [Content-Hash Summary Cache to Prevent Redundant Inference](./03-phase-3-ai-docs-rag.md#issue-062-perf-content-hash-summary-cache-to-prevent-redundant-llm-inference) | `ai-rag` | Perf | `P1` | `Completed` |
| `#063` | [Code Complexity Analyzer (Cyclomatic & Cognitive Metrics)](./03-phase-3-ai-docs-rag.md#issue-063-feat-code-complexity-analyzer-cyclomatic-cognitive--halstead-metrics) | `apps/api` | Feature | `P1` | `Completed` |
| `#064` | [Visual Complexity Heatmap Overlay on React Flow Canvas](./03-phase-3-ai-docs-rag.md#issue-064-feat-visual-complexity-heatmap-overlay-on-react-flow-canvas) | `apps/web` | Frontend | `P1` | `Ready` |
| `#065` | [Living Architecture Documentation Generator (Markdown + Mermaid)](./03-phase-3-ai-docs-rag.md#issue-065-feat-living-architecture-documentation-generator-markdown--mermaid) | `apps/api` | Feature | `P0` | `Completed` |
| `#066` | [Automated "New Contributor Onboarding Guide" Generator](./03-phase-3-ai-docs-rag.md#issue-066-feat-automated-new-contributor-onboarding-guide-generator) | `apps/api` | Feature | `P1` | `Ready` |
| `#067` | ["Good First Issue" Matcher Based on AST Isolation & Low In-Degree](./03-phase-3-ai-docs-rag.md#issue-067-feat-good-first-issue-matcher-based-on-ast-isolation--low-in-degree) | `mapping` | Feature | `P1` | `Ready` |
| `#068` | [RAG Context Assembly Pipeline with Strict Token Budgeting](./03-phase-3-ai-docs-rag.md#issue-068-feat-rag-context-assembly-pipeline-with-strict-token-budgeting) | `ai-rag` | Feature | `P0` | `Completed` |
| `#069` | [Streaming Server-Sent Events (SSE) Chat API Endpoint](./03-phase-3-ai-docs-rag.md#issue-069-feat-streaming-server-sent-events-sse-chat-api-endpoint) | `apps/api` | Feature | `P0` | `Completed` |
| `#070` | [Grounded Code Citation Linking with Exact [file:line] References](./03-phase-3-ai-docs-rag.md#issue-070-feat-grounded-code-citation-linking-with-exact-fileline-references) | `ai-rag` | Feature | `P0` | `Completed` |
| `#071` | [Conversational Chat Session Persistence & Multi-Turn Cache](./03-phase-3-ai-docs-rag.md#issue-071-feat-conversational-chat-session-persistence--multi-turn-history-cache) | `apps/api` | Feature | `P1` | `Completed` |
| `#072` | [Hallucination Guardrails & Refusal Protocol for Out-of-Domain Queries](./03-phase-3-ai-docs-rag.md#issue-072-feat-hallucination-guardrails--refusal-protocol-for-out-of-domain-queries) | `ai-rag` | Security | `P1` | `Ready` |
| `#073` | [Automated Architectural Drift Detection on Git Push Webhook](./03-phase-3-ai-docs-rag.md#issue-073-feat-automated-architectural-drift-detection-on-git-push-webhook) | `apps/api` | Feature | `P1` | `Ready` |
| `#074` | [Scheduled Weekly Repository Full Re-Analysis Celery Beat Task](./03-phase-3-ai-docs-rag.md#issue-074-feat-scheduled-weekly-repository-full-re-analysis-celery-beat-task) | `apps/api` | Infra | `P2` | `Ready` |
| `#075` | [Markdown & PDF Living Architecture Documentation Export Service](./03-phase-3-ai-docs-rag.md#issue-075-feat-markdown--pdf-living-architecture-documentation-export-service) | `apps/api` | Feature | `P2` | `Ready` |
| `#076` | [Architectural Changelog Generator Between Git Releases & Tags](./03-phase-3-ai-docs-rag.md#issue-076-feat-architectural-changelog-generator-between-git-releases--tags) | `apps/api` | Feature | `P2` | `Ready` |
| `#077` | [Contextual Chat Suggestion Chips Based on Canvas Selection](./03-phase-3-ai-docs-rag.md#issue-077-feat-contextual-chat-suggestion-chips-based-on-canvas-selection) | `apps/web` | Frontend | `P2` | `Ready` |
| `#078` | [User Feedback Collector for AI Answer Quality & Citation Precision](./03-phase-3-ai-docs-rag.md#issue-078-feat-user-feedback-collector-for-ai-answer-quality--citation-accuracy) | `apps/api` | Feature | `P2` | `Ready` |

---

### Phase 4: Multi-Tenant SaaS, Security & Production Polish (`#079` - `#098`)

| ID | Title | Component | Type | Priority | Status |
|---|---|---|---|---|---|
| `#079` | [Organization & Workspace Multi-Tenant Relational Data Model](./04-phase-4-saas-production.md#issue-079-feat-organization--workspace-multi-tenant-relational-data-model) | `apps/api` | Feature | `P0` | `Completed` |
| `#080` | [PostgreSQL Row-Level Security (RLS) Tenant Isolation Policies](./04-phase-4-saas-production.md#issue-080-sec-postgresql-row-level-security-rls-tenant-isolation-policies) | `apps/api` | Security | `P0` | `Ready` |
| `#081` | [Role-Based Access Control (RBAC) Permission Middleware](./04-phase-4-saas-production.md#issue-081-feat-role-based-access-control-rbac-permission-middleware) | `apps/api` | Security | `P0` | `Ready` |
| `#082` | [Organization Member Invitation Flow with Cryptographic Signed Tokens](./04-phase-4-saas-production.md#issue-082-feat-organization-member-invitation-flow-with-cryptographic-signed-tokens) | `apps/api` | Feature | `P1` | `Ready` |
| `#083` | [Stripe Subscription Billing Integration (Free, Pro & Enterprise)](./04-phase-4-saas-production.md#issue-083-feat-stripe-subscription-billing-integration-free-pro--enterprise-tiers) | `apps/api` | Feature | `P0` | `Ready` |
| `#084` | [Usage Quota Enforcement & Real-Time Metering Service](./04-phase-4-saas-production.md#issue-084-feat-usage-quota-enforcement--real-time-metering-service) | `apps/api` | Feature | `P1` | `Ready` |
| `#085` | [Stripe Webhook Receiver & Subscription Lifecycle State Machine](./04-phase-4-saas-production.md#issue-085-feat-stripe-webhook-receiver--subscription-lifecycle-state-machine) | `apps/api` | Security | `P0` | `Ready` |
| `#086` | [Organization Admin Dashboard & System Observability Portal](./04-phase-4-saas-production.md#issue-086-feat-organization-admin-dashboard--system-observability-portal) | `apps/web` | Frontend | `P1` | `Ready` |
| `#087` | [Ingestion Error Log Viewer & Dead-Letter Queue Management](./04-phase-4-saas-production.md#issue-087-feat-ingestion-error-log-viewer--dead-letter-queue-management) | `apps/web` | Frontend | `P1` | `Ready` |
| `#088` | [Public Developer API: Key Generation, SHA-256 Hashing & Revocation](./04-phase-4-saas-production.md#issue-088-feat-public-developer-api-key-generation-sha-256-hashing--revocation) | `apps/api` | Security | `P0` | `Ready` |
| `#089` | [Tiered API Rate Limiting with Redis Sliding Window Counter](./04-phase-4-saas-production.md#issue-089-feat-tiered-api-rate-limiting-with-redis-sliding-window-counter) | `apps/api` | Perf | `P1` | `Completed` |
| `#090` | [Enterprise Audit Logging Service for Compliance (SOC 2 Type II)](./04-phase-4-saas-production.md#issue-090-sec-enterprise-audit-logging-service-for-compliance-soc-2-type-ii) | `apps/api` | Security | `P1` | `Ready` |
| `#091` | [Playwright E2E Test Suite: Authentication & Canvas Workflows](./04-phase-4-saas-production.md#issue-091-test-playwright-end-to-end-test-suite-authentication--canvas-workflows) | `apps/web` | Test | `P0` | `Ready` |
| `#092` | [Playwright E2E Test Suite: Issue Mapping & Streaming Chat](./04-phase-4-saas-production.md#issue-092-test-playwright-end-to-end-test-suite-issue-mapping--streaming-chat) | `apps/web` | Test | `P0` | `Ready` |
| `#093` | [High-Concurrency Load Testing with Locust (100 Concurrent Ingestions)](./04-phase-4-saas-production.md#issue-093-perf-high-concurrency-load-testing-with-locust-100-concurrent-ingestions) | `apps/api` | Perf | `P1` | `Ready` |
| `#094` | [OWASP Top 10 Security Audit, Penetration Test & Dependency Scan](./04-phase-4-saas-production.md#issue-094-sec-owasp-top-10-security-audit-penetration-test--dependency-remediation) | `apps/api` | Security | `P0` | `Ready` |
| `#095` | [Public Documentation Site Deployment (Nextra / Mintlify)](./04-phase-4-saas-production.md#issue-095-docs-public-documentation-site-deployment-nextra--mintlify) | `docs` | Docs | `P1` | `Ready` |
| `#096` | [Marketing Landing Page with Interactive Canvas Demo & Waitlist](./04-phase-4-saas-production.md#issue-096-feat-marketing-landing-page-with-interactive-canvas-demo--waitlist) | `apps/web` | Frontend | `P1` | `Ready` |
| `#097` | [Production Kubernetes Deployment Architecture (EKS/GKE Helm Charts)](./04-phase-4-saas-production.md#issue-097-infra-production-kubernetes-deployment-architecture-eksgke-helm-charts) | `infra` | Infra | `P0` | `Ready` |
| `#098` | [Automated Incident Response Runbooks & Disaster Recovery Protocols](./04-phase-4-saas-production.md#issue-098-feat-automated-incident-response-runbooks--disaster-recovery-protocols) | `docs` | Infra | `P1` | `Ready` |

---

### Phase 5: CodeAtlas Prime Convergence & Advanced Enterprise (`#099` - `#118`)

| ID | Title | Component | Type | Priority | Status |
|---|---|---|---|---|---|
| `#099` | [PR "Blast Radius" GitHub App Bot with Architectural Impact Comment](./05-phase-5-prime-advanced.md#issue-099-feat-pr-blast-radius-github-app-bot-with-automated-architectural-impact-comment) | `apps/api` | Feature | `P0` | `Ready` |
| `#100` | [Architectural Boundary Enforcement Engine ("The Architecture Linter")](./05-phase-5-prime-advanced.md#issue-100-feat-architectural-boundary-enforcement-engine-the-architecture-linter) | `apps/api` | Feature | `P0` | `Ready` |
| `#101` | ["Bus Factor" & Single-Maintainer Knowledge Silo Risk Analysis](./05-phase-5-prime-advanced.md#issue-101-feat-bus-factor--single-maintainer-knowledge-silo-risk-analysis) | `apps/api` | Feature | `P1` | `Ready` |
| `#102` | [Dynamic README SVG Architecture Badge Generator](./05-phase-5-prime-advanced.md#issue-102-feat-dynamic-readme-svg-architecture-badge-generator) | `apps/api` | Feature | `P1` | `Ready` |
| `#103` | [Temporal Commit Churn Heatmap Overlay on Spatial React Flow Nodes](./05-phase-5-prime-advanced.md#issue-103-feat-temporal-commit-churn-heatmap-overlay-on-spatial-react-flow-nodes) | `apps/web` | Frontend | `P1` | `Ready` |
| `#104` | [GitWatcher (GitPulse) Developer Telemetry Convergence](./05-phase-5-prime-advanced.md#issue-104-feat-gitwatcher-gitpulse-developer-telemetry-convergence) | `apps/api` | Feature | `P1` | `Ready` |
| `#105` | [Architectural Drift Tracking Between Git Branches & Release Tags](./05-phase-5-prime-advanced.md#issue-105-feat-architectural-drift-tracking-between-git-branches--release-tags) | `apps/api` | Feature | `P1` | `Ready` |
| `#106` | [VS Code Extension: In-Editor Graph Navigation & Hover AST Insights](./05-phase-5-prime-advanced.md#issue-106-feat-codeatlas-vs-code-extension-in-editor-graph-navigation--hover-ast-insights) | `extensions` | Frontend | `P1` | `Ready` |
| `#107` | [JetBrains IDE Plugin for CodeAtlas Graph & Subgraph Exploration](./05-phase-5-prime-advanced.md#issue-107-feat-jetbrains-ide-plugin-for-codeatlas-graph--subgraph-exploration) | `extensions` | Frontend | `P2` | `Ready` |
| `#108` | [Slack & Discord Bot: Conversational Codebase Q&A ("/codeatlas <query>")](./05-phase-5-prime-advanced.md#issue-108-feat-slack--discord-bot-conversational-codebase-qa-codeatlas-query) | `apps/api` | Feature | `P2` | `Ready` |
| `#109` | [Auto-Scaffolding PR Patch Generator for Mapped GitHub Issues](./05-phase-5-prime-advanced.md#issue-109-feat-auto-scaffolding-pr-patch-generator-for-mapped-github-issues) | `ai-rag` | Feature | `P2` | `Ready` |
| `#110` | [Open-Source License Compliance & Vulnerability Dependency Mapper](./05-phase-5-prime-advanced.md#issue-110-feat-open-source-license-compliance--vulnerability-dependency-mapper) | `ingestion` | Security | `P1` | `Ready` |
| `#111` | [Notion & Confluence Living Architecture Documentation Sync Engine](./05-phase-5-prime-advanced.md#issue-111-feat-notion--confluence-living-architecture-documentation-sync-engine) | `apps/api` | Feature | `P2` | `Ready` |
| `#112` | [Multi-Repository Cross-Dependency Graph Mapping for Microservices](./05-phase-5-prime-advanced.md#issue-112-feat-multi-repository-cross-dependency-graph-mapping-for-microservices) | `apps/api` | Feature | `P1` | `Ready` |
| `#113` | [100% Air-Gapped Local Enterprise Distribution & Self-Hosted Package](./05-phase-5-prime-advanced.md#issue-113-feat-100-air-gapped-local-enterprise-distribution--self-hosted-package) | `infra` | Infra | `P1` | `Ready` |
| `#114` | [3D WebGL / Force-Directed AST Diff Visualizer](./05-phase-5-prime-advanced.md#issue-114-feat-3d-webgl--force-directed-ast-diff-visualizer) | `apps/web` | Frontend | `P2` | `Ready` |
| `#115` | [Custom Architectural Rules Engine with AST Query Language (CodeAtlasQL)](./05-phase-5-prime-advanced.md#issue-115-feat-custom-architectural-rules-engine-with-ast-query-language-codeatlasql) | `apps/api` | Feature | `P1` | `Ready` |
| `#116` | [Codebase Technical Debt Prioritization Matrix (Churn vs Complexity)](./05-phase-5-prime-advanced.md#issue-116-feat-codebase-technical-debt-prioritization-matrix-churn-vs-complexity) | `apps/api` | Feature | `P1` | `Ready` |
| `#117` | [Enterprise Single Sign-On (SSO) with SAML 2.0 & OIDC (Okta, Azure AD)](./05-phase-5-prime-advanced.md#issue-117-sec-enterprise-single-sign-on-sso-with-saml-20--oidc-okta-azure-ad) | `apps/api` | Security | `P0` | `Ready` |
| `#118` | [Domain-Specific AST Embedding Model Fine-Tuning Pipeline](./05-phase-5-prime-advanced.md#issue-118-feat-domain-specific-ast-embedding-model-fine-tuning-pipeline) | `ai-rag` | Feature | `P2` | `Ready` |

---

## 🛠️ Contribution Workflow & Issue Templates

When picking up an issue from this backlog:

1. **Branch Naming**:
   Create branch following the pattern: `<type>/<issue-id>-<short-description>`:
   ```bash
   git checkout -b feat/023-go-ast-parser
   git checkout -b perf/042-canvas-virtualization
   ```
2. **Issue Linking**:
   Ensure PR body includes `Closes #<id>` to link and close the issue automatically on merge.
3. **Labels & Metadata**:
   Reference [.github/labels.yml](../.github/labels.yml) for label naming taxonomy.
4. **Issue Templates**:
   Use GitHub Issue forms located in [.github/ISSUE_TEMPLATE/](../.github/ISSUE_TEMPLATE/) for bug reports, feature requests, and security disclosures.
