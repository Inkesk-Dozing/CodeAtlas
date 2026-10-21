# Phase 1 Issues: Ingestion Engine, AST Parsers & Graph Persistence

This document details all Phase 1 issues for CodeAtlas covering repository cloning, multi-language Abstract Syntax Tree (AST) parsing, entity extraction, relational dependency graph construction, pgvector embedding generation, and incremental webhook updates.

---

### Issue #019: `[FEAT]: Shallow Repository Cloner with GitHub Installation Token & Sparse Checkout`
- **Labels**: `phase:phase-1-ingestion`, `type:feature`, `priority:P0-critical`, `component:ingestion-engine`, `status:completed`
- **Milestone**: `M1: Ingestion`
- **Component**: `apps/api/services/ingestion/cloner.py`
- **Existing Implementation**: [apps/api/services/ingestion/](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/services/ingestion/)
- **Problem Statement**:
  Cloning full git commit history for massive monorepos wastes disk space, exhausts bandwidth, and slows down ingestion pipelines.
- **Technical Specification**:
  - Implement shallow cloner using `git clone --depth 1 --single-branch`.
  - Use GitHub App installation tokens (`ghs_...`) for authenticated HTTPS access.
  - Implement sparse checkout to exclude build directories, lockfiles, and media files (`node_modules/`, `dist/`, `.next/`, `*.png`, `*.mp4`).
  - Isolate cloned repositories in ephemeral temporary directories with automatic cleanup handlers.
- **Acceptance Criteria**:
  - [x] Clones 10,000-file repository in under 20 seconds.
  - [x] Respects `.gitignore` and ignores binary assets.
  - [x] Temporary directories cleaned up even on unhandled parsing exceptions.

---

### Issue #020: `[FEAT]: Base AST Parser Framework & Multi-Language Dispatch Registry`
- **Labels**: `phase:phase-1-ingestion`, `type:feature`, `priority:P0-critical`, `component:parsers`, `status:completed`
- **Milestone**: `M1: Ingestion`
- **Component**: `apps/api/parsers/base.py`, `apps/api/parsers/__init__.py`
- **Existing Implementation**: [apps/api/parsers/base.py](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/parsers/base.py)
- **Problem Statement**:
  CodeAtlas must support multiple programming languages through a uniform interface, returning standardized `ParsedFile`, `CodeNode`, and `CodeEdge` objects.
- **Technical Specification**:
  - Create abstract base class `BaseParser` defining `parse(file_path: str, content: str) -> ParsedFile`.
  - Registry pattern mapping file extensions (`.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.go`, `.rs`) to concrete parsers.
  - Standardized entity definitions: `function`, `class`, `module`, `route`, `component`, `model`.
- **Acceptance Criteria**:
  - [x] Abstract methods enforce extraction of nodes, edges, imports, and exports.
  - [x] File extension dispatcher routes files to appropriate parser in $O(1)$ time.
  - [x] Graceful fallback to basic line/token parsing for unsupported file types.

---

### Issue #021: `[FEAT]: JavaScript & TypeScript AST Parser Engine`
- **Labels**: `phase:phase-1-ingestion`, `type:feature`, `priority:P0-critical`, `component:parsers`, `status:completed`
- **Milestone**: `M1: Ingestion`
- **Component**: `apps/api/parsers/javascript.py`
- **Existing Implementation**: [apps/api/parsers/javascript.py](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/parsers/javascript.py)
- **Problem Statement**:
  TypeScript/JavaScript monorepos contain diverse patterns (ESM/CJS imports, TS interfaces, React components, arrow functions, decorators).
- **Technical Specification**:
  - Parse ESM (`import { x } from 'y'`) and CommonJS (`require('y')`) import statements.
  - Extract named and default exports, re-exports (`export * from '...'`).
  - Extract class declarations, methods, properties, and inheritance hierarchy (`extends`, `implements`).
  - Extract standalone functions, async arrow functions, and exported constants.
- **Acceptance Criteria**:
  - [x] Extracts source line ranges (`start_line`, `end_line`) for every AST node.
  - [x] Correctly identifies internal monorepo package imports vs third-party `node_modules`.
  - [x] Handles modern syntax: JSX, TS generics, optional chaining, and decorators.

---

### Issue #022: `[FEAT]: Python AST Parser Engine with Decorator & Type Hint Analysis`
- **Labels**: `phase:phase-1-ingestion`, `type:feature`, `priority:P0-critical`, `component:parsers`, `status:completed`
- **Milestone**: `M1: Ingestion`
- **Component**: `apps/api/parsers/python.py`
- **Existing Implementation**: [apps/api/parsers/python.py](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/parsers/python.py)
- **Problem Statement**:
  Python repositories heavily use decorators for routing, ORM models for database definitions, and type hints for function signatures that must be captured in the graph.
- **Technical Specification**:
  - Parse `import x`, `from x import y`, and relative imports (`from . import z`).
  - Extract classes, base classes, methods, docstrings, and class variables.
  - Extract functions, async definitions, return type annotations, and decorator chains (`@app.get`, `@router.post`).
  - Calculate cyclomatic complexity per function.
- **Acceptance Criteria**:
  - [x] Accurately captures multi-line docstrings and function signatures.
  - [x] Detects API route decorator patterns in FastAPI, Flask, and Django.
  - [x] Preserves parameter names and type annotations in node metadata.

---

### Issue #023: `[FEAT]: Go Language AST Parser Integration (Packages, Structs & Interfaces)`
- **Labels**: `phase:phase-1-ingestion`, `type:feature`, `priority:P2-medium`, `component:parsers`, `status:ready`
- **Milestone**: `M1: Ingestion`
- **Component**: `apps/api/parsers/golang.py`
- **Problem Statement**:
  Backend services written in Go (Gin, Echo, standard library) are common in monorepos but currently lack specialized AST parsing in CodeAtlas.
- **Technical Specification**:
  - Implement `GoParser` using Tree-sitter Go grammar.
  - Extract Go package names, import declarations, and module boundaries (`go.mod`).
  - Extract struct definitions, embedded structs, interface signatures, and receiver methods (`func (s *Service) Do(...)`).
  - Identify HTTP route bindings in Gin (`r.GET("/api/v1/...", handler)`).
- **Acceptance Criteria**:
  - [ ] Extracts package-level functions and receiver methods linked to their parent struct.
  - [ ] Maps intra-package calls and external module dependencies.
  - [ ] Passes unit test suite across sample Go monorepo fixtures.

---

### Issue #024: `[FEAT]: Rust Language AST Parser Integration (Crates, Traits & Implementations)`
- **Labels**: `phase:phase-1-ingestion`, `type:feature`, `priority:P2-medium`, `component:parsers`, `status:ready`
- **Milestone**: `M1: Ingestion`
- **Component**: `apps/api/parsers/rust.py`
- **Problem Statement**:
  High-performance systems frequently utilize Rust workspace crates (`Cargo.toml`) which require trait and macro-aware AST parsing.
- **Technical Specification**:
  - Implement `RustParser` using Tree-sitter Rust grammar.
  - Extract `mod`, `use` statements, `struct`, `enum`, `trait`, and `impl` blocks.
  - Link `impl Trait for Struct` relationships as `implements` edges.
  - Extract Actix/Axum web routes from attribute macros (`#[get("/path")]`).
- **Acceptance Criteria**:
  - [ ] Resolves multi-file module trees (`mod.rs` and standalone module files).
  - [ ] Captures public vs private visibility flags (`pub`, `pub(crate)`).
  - [ ] Creates code nodes for structs, traits, and associated functions.

---

### Issue #025: `[FEAT]: API Route Extraction Engine for Express, FastAPI, Next.js & Spring`
- **Labels**: `phase:phase-1-ingestion`, `type:feature`, `priority:P1-high`, `component:ingestion-engine`, `status:completed`
- **Milestone**: `M1: Ingestion`
- **Component**: `apps/api/services/ingestion/route_extractor.py`
- **Existing Implementation**: [apps/api/services/ingestion/](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/services/ingestion/)
- **Problem Statement**:
  Engineers exploring a monorepo want to know "What API endpoints exist and which handlers process them?".
- **Technical Specification**:
  - Detect HTTP verbs (`GET`, `POST`, `PUT`, `DELETE`, `PATCH`) and route paths.
  - Detect Next.js 14 App Router endpoints (`app/**/route.ts`).
  - Detect FastAPI / Flask route decorators (`@router.get('/items/{id}')`).
  - Detect Express / NestJS route mappings (`app.use('/auth', authRouter)`).
  - Create specialized `RouteNode` with path, verb, middleware list, and handler reference.
- **Acceptance Criteria**:
  - [x] Extracts parameter templates (`/users/:id` or `/users/{id}`).
  - [x] Creates `handles_route` edges connecting Route nodes to controller functions.
  - [x] Renders distinct badge for API routes in graph explorer.

---

### Issue #026: `[FEAT]: React/Vue Component & Hook Hierarchy Extraction`
- **Labels**: `phase:phase-1-ingestion`, `type:feature`, `priority:P1-high`, `component:ingestion-engine`, `status:completed`
- **Milestone**: `M1: Ingestion`
- **Component**: `apps/api/services/ingestion/component_extractor.py`
- **Existing Implementation**: [apps/api/services/ingestion/](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/services/ingestion/)
- **Problem Statement**:
  Frontend codebases are structured around component render trees and state management hooks rather than procedural functions.
- **Technical Specification**:
  - Identify React functional components, props interfaces, and return JSX structures.
  - Detect custom hook invocations (`useAuth`, `useCart`, `useQuery`).
  - Create `renders` edges between parent components and child JSX elements.
  - Create `uses_hook` edges linking components to hook definitions.
- **Acceptance Criteria**:
  - [x] Distinguishes primitive HTML tags from custom React components.
  - [x] Captures component props definitions and default values.
  - [x] Accurately maps cross-file component render relationships.

---

### Issue #027: `[FEAT]: Database ORM Model Extraction (Prisma, SQLAlchemy, Django ORM)`
- **Labels**: `phase:phase-1-ingestion`, `type:feature`, `priority:P1-high`, `component:ingestion-engine`, `status:completed`
- **Milestone**: `M1: Ingestion`
- **Component**: `apps/api/services/ingestion/model_extractor.py`
- **Existing Implementation**: [apps/api/services/ingestion/](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/services/ingestion/)
- **Problem Statement**:
  Database entities represent the core domain model of an application and serve as primary anchors during codebase onboarding.
- **Technical Specification**:
  - Parse Prisma schema files (`schema.prisma`): models, fields, relations, enums.
  - Parse SQLAlchemy `DeclarativeBase` models: column types, foreign keys, relationships.
  - Parse Django `models.Model` subclasses: fields, foreign keys, many-to-many fields.
  - Create `ModelNode` entities and `references_model` foreign key edges.
- **Acceptance Criteria**:
  - [x] Identifies primary keys, foreign keys, and nullability flags.
  - [x] Connects API endpoints to the database models they query or mutate.
  - [x] Visualizes entity relationship diagrams directly on the graph canvas.

---

### Issue #028: `[FEAT]: Graph Persistence Layer with High-Speed PostgreSQL Batch Upsert`
- **Labels**: `phase:phase-1-ingestion`, `type:performance`, `priority:P0-critical`, `component:apps/api`, `status:completed`
- **Milestone**: `M1: Ingestion`
- **Component**: `apps/api/services/ingestion/graph_persister.py`
- **Existing Implementation**: [apps/api/services/ingestion/](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/services/ingestion/)
- **Problem Statement**:
  Inserting 50,000 nodes and 100,000 edges sequentially via standard ORM queries causes transaction timeouts and database connection exhaustion.
- **Technical Specification**:
  - Implement batched bulk insert using PostgreSQL `INSERT INTO ... ON CONFLICT DO UPDATE`.
  - Chunk node upserts in batches of 1,000 records.
  - Resolve foreign key IDs for edges in a single pass using temporary lookup tables in Redis.
  - Use asyncpg raw connection for high-throughput bulk binary copying where applicable.
- **Acceptance Criteria**:
  - [x] Persists 50,000 nodes and 80,000 edges in < 15 seconds.
  - [x] Zero foreign key constraint violation errors during concurrent batch execution.
  - [x] Idempotent execution: re-running ingestion does not duplicate nodes.

---

### Issue #029: `[FEAT]: Vector Embeddings Generation Pipeline with Local Ollama Inference`
- **Labels**: `phase:phase-1-ingestion`, `type:feature`, `priority:P0-critical`, `component:ai-rag`, `status:completed`
- **Milestone**: `M1: Ingestion`
- **Component**: `apps/api/services/ai/embedder.py`
- **Existing Implementation**: [apps/api/services/ai/](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/services/ai/)
- **Problem Statement**:
  Semantic search, RAG, and issue-to-code mapping require vector embeddings of AST nodes generated efficiently without leaking code to third-party APIs.
- **Technical Specification**:
  - Construct semantic embedding context string per node: `type: {node_type} | name: {name} | path: {path} | signature: {signature} | docstring: {docstring} | callers: {callers}`.
  - Call local Ollama embeddings endpoint (`nomic-embed-text` or `all-minilm`) in batched HTTP requests.
  - Fallback to local HuggingFace `sentence-transformers` when Ollama is unavailable.
  - Cache node text hashes to skip embeddings for unchanged files.
- **Acceptance Criteria**:
  - [x] Generates 768-dimensional normalized embedding vectors.
  - [x] Batches requests (32 items per call) to maximize CPU/GPU throughput.
  - [x] 100% air-gapped: zero external cloud API requests.

---

### Issue #030: `[FEAT]: pgvector HNSW Index Configuration & Fast Cosine Distance Queries`
- **Labels**: `phase:phase-1-ingestion`, `type:performance`, `priority:P0-critical`, `component:vector-db`, `status:completed`
- **Milestone**: `M1: Ingestion`
- **Component**: `apps/api/migrations/0001_initial.py`, `apps/api/services/mapping/`
- **Existing Implementation**: [apps/api/migrations/](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/migrations/)
- **Problem Statement**:
  Sequential vector scanning (exact KNN) scales poorly as repository code nodes exceed 100,000. Approximate Nearest Neighbor (ANN) indexing is essential.
- **Technical Specification**:
  - Create HNSW index on `code_nodes(embedding vector_cosine_ops)`.
  - Configure tuning parameters: `m=16` (bi-directional links) and `ef_construction=64`.
  - Implement parameterized nearest-neighbor query returning top-$K$ nodes filtered by `repository_id`.
- **Acceptance Criteria**:
  - [x] Query latency < 25ms for top-10 nearest neighbor search across 100k vectors.
  - [x] Index build completes during database migration without table locking.
  - [x] Scoped queries enforce strict `repository_id` filtering.

---

### Issue #031: `[FEAT]: Incremental Git Diff Parser for Push Webhook Re-Indexing`
- **Labels**: `phase:phase-1-ingestion`, `type:feature`, `priority:P1-high`, `component:ingestion-engine`, `status:completed`
- **Milestone**: `M1: Ingestion`
- **Component**: `apps/api/services/ingestion/incremental.py`
- **Existing Implementation**: [apps/api/services/ingestion/](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/services/ingestion/)
- **Problem Statement**:
  Re-parsing an entire 5,000-file repository on every commit push wastes computational resources and delays updated graph availability.
- **Technical Specification**:
  - Parse `git diff --name-status before_sha..after_sha` payload from GitHub push webhook.
  - Classify changed files: `Added`, `Modified`, `Deleted`, `Renamed`.
  - For `Deleted`: Cascade delete code nodes and connected edges.
  - For `Modified`: Re-parse file AST, diff existing nodes, update modified signatures, and re-embed.
  - For `Added`: Parse and insert new nodes and edges.
- **Acceptance Criteria**:
  - [x] Incremental updates for a 5-file commit complete in < 5 seconds.
  - [x] Orphaned edges correctly purged when dependencies are removed.
  - [x] Graph version bumped and clients notified via WebSocket.

---

### Issue #032: `[FEAT]: Real-Time Ingestion Pipeline Progress Tracking via WebSocket & REST API`
- **Labels**: `phase:phase-1-ingestion`, `type:feature`, `priority:P1-high`, `component:apps/api`, `status:completed`
- **Milestone**: `M1: Ingestion`
- **Component**: `apps/api/routers/ingestion.py`
- **Existing Implementation**: [apps/api/routers/ingestion.py](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/routers/ingestion.py)
- **Problem Statement**:
  Users initiating repository ingestion need granular, transparent feedback across all 5 pipeline stages (`clone`, `parse`, `extract`, `embed`, `persist`).
- **Technical Specification**:
  - REST endpoint: `GET /api/v1/repos/{id}/ingest/status` returning current stage, percentage, processed files count, and stage timings.
  - WebSocket channel: `WS /api/v1/repos/{id}/ingest/ws` broadcasting stage transitions and real-time progress events.
  - Publish stage updates to Redis pub/sub for multi-worker synchronization.
- **Acceptance Criteria**:
  - [x] Progress percentage monotonically increases from 0% to 100%.
  - [x] Frontend receives progress updates at minimum 2 Hz rate.
  - [x] Failure events broadcast exact error message and diagnostic log.

---

### Issue #033: `[PERF]: Celery Ingestion Worker Memory Leak Remediation & Process Recycling`
- **Labels**: `phase:phase-1-ingestion`, `type:performance`, `priority:P1-high`, `component:ingestion-engine`, `status:completed`
- **Milestone**: `M1: Ingestion`
- **Component**: `apps/api/tasks/ingestion_tasks.py`
- **Existing Implementation**: [apps/api/tasks/](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/tasks/)
- **Problem Statement**:
  Tree-sitter C bindings and large AST allocations in Python can lead to memory fragmentation and eventual OOM termination during successive large repository ingestion runs.
- **Technical Specification**:
  - Configure Celery worker concurrency with explicit process recycling: `--max-tasks-per-child=10`.
  - Set hard memory limit per child worker using `worker_max_memory_per_child = 500000` (500 MB).
  - Explicitly trigger `gc.collect()` after parsing phase completion.
- **Acceptance Criteria**:
  - [x] Worker memory stabilizes under 600 MB resident memory across 20 consecutive ingestions.
  - [x] Child workers recycle cleanly without dropping in-flight queue jobs.
  - [x] Zero SIGKILL / OOM terminations in worker container logs.

---

### Issue #034: `[FEAT]: Monorepo Workspace Package Boundary & Circular Dependency Detector`
- **Labels**: `phase:phase-1-ingestion`, `type:feature`, `priority:P1-high`, `component:ingestion-engine`, `status:ready`
- **Milestone**: `M1: Ingestion`
- **Component**: `apps/api/services/ingestion/monorepo_analyzer.py`
- **Problem Statement**:
  In large monorepos (Turborepo, Nx, Lerna), circular package imports and boundary violations degrade build caching and create hidden deployment couplings.
- **Technical Specification**:
  - Detect monorepo configuration files (`pnpm-workspace.yaml`, `turbo.json`, `nx.json`, `package.json`).
  - Map intra-monorepo workspace dependencies (`apps/web` -> `packages/shared`).
  - Run Tarjan's strongly connected components algorithm on package dependency graph to detect circular dependencies.
  - Flag circular cycles with severity warning and affected package paths.
- **Acceptance Criteria**:
  - [ ] Accurately identifies all monorepo package roots and scopes.
  - [ ] Returns list of circular dependency chains if present.
  - [ ] Displays package dependency matrix in repository summary view.

---

### Issue #035: `[FEAT]: Tree-sitter Native Parser Integration (Upgrading from Regex)`
- **Labels**: `phase:phase-1-ingestion`, `type:feature`, `priority:P1-high`, `component:parsers`, `status:ready`
- **Milestone**: `M1: Ingestion`
- **Component**: `apps/api/parsers/treesitter/`
- **Problem Statement**:
  Regex-based parsers struggle with nested templates, multi-line nested JSX, and complex type annotations. Direct Tree-sitter C/Wasm bindings provide 100% grammar accuracy.
- **Technical Specification**:
  - Integrate `tree-sitter` Python library with precompiled grammars for Python, TypeScript, and TSX.
  - Construct AST query s-expressions (`(function_declaration name: (identifier) @func.name)`) to extract symbols.
  - Replace regex extraction in `javascript.py` and `python.py` with native Tree-sitter cursor traversals.
- **Acceptance Criteria**:
  - [ ] 100% syntax compliance even on minified or syntactically irregular code files.
  - [ ] Parsing speed improvements: > 2,000 lines/second per thread.
  - [ ] Zero false positive symbol extractions on comments or string literals.

---

### Issue #036: `[FEAT]: CodeNode & CodeEdge Composite Index Optimization for Subgraph Traversal`
- **Labels**: `phase:phase-1-ingestion`, `type:performance`, `priority:P1-high`, `component:apps/api`, `status:completed`
- **Milestone**: `M1: Ingestion`
- **Component**: `apps/api/migrations/`
- **Existing Implementation**: [apps/api/migrations/](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/migrations/)
- **Problem Statement**:
  Recursive graph traversal queries (`GET /subgraph`) scanning millions of edges must execute in under 100ms.
- **Technical Specification**:
  - Composite B-tree index on `code_edges(source_id, target_id)`.
  - Composite B-tree index on `code_edges(target_id, source_id)`.
  - Trigram GIN index (`pg_trgm`) on `code_nodes(name, path)` for fast symbol prefix search.
  - Filter index on `code_nodes(repository_id, node_type)`.
- **Acceptance Criteria**:
  - [x] 1-hop and 2-hop neighborhood traversals execute in < 40ms on 200,000 edges.
  - [x] Symbol substring search (`LIKE '%service%'`) utilizes GIN trigram index.
  - [x] Query execution plans verified via `EXPLAIN ANALYZE`.

---

### Issue #037: `[FEAT]: Repository Health Check & Ingestion Failure Rollback Mechanism`
- **Labels**: `phase:phase-1-ingestion`, `type:feature`, `priority:P2-medium`, `component:ingestion-engine`, `status:ready`
- **Milestone**: `M1: Ingestion`
- **Component**: `apps/api/services/ingestion/pipeline.py`
- **Problem Statement**:
  If an ingestion job crashes halfway through (e.g. out of memory or network timeout during embedding), the repository remains in a broken, half-populated state.
- **Technical Specification**:
  - Implement two-phase commit or shadow staging graph for new ingestions.
  - Maintain previous active graph version until new graph generation is 100% verified.
  - On unhandled failure: Roll back staging records, set repository status to `Failed`, and preserve previous valid graph.
  - Log root-cause error trace to `ingestion_errors` table.
- **Acceptance Criteria**:
  - [ ] Zero partial/corrupted graphs visible to users during failed ingestions.
  - [ ] Users can view detailed error diagnostics and trigger clean retry.
  - [ ] Automated cleanup of dangling temporary clones.

---

### Issue #038: `[TEST]: Synthetic Golden Monorepo Fixture & Parser Test Suite`
- **Labels**: `phase:phase-1-ingestion`, `type:test`, `priority:P1-high`, `component:parsers`, `status:completed`
- **Milestone**: `M1: Ingestion`
- **Component**: `apps/api/tests/fixtures/`, `apps/api/tests/test_parsers.py`
- **Existing Implementation**: [apps/api/tests/](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/tests/)
- **Problem Statement**:
  Parser changes must be continuously validated against known fixtures to prevent regressions in entity extraction accuracy.
- **Technical Specification**:
  - Create synthetic test monorepo fixture containing:
    - Next.js 14 frontend with React hooks, components, and API routes.
    - FastAPI backend with routers, middleware, Pydantic models, and SQLAlchemy ORM.
    - Shared TypeScript package.
  - Automated assertions verifying exact node counts, edge counts, and symbol names.
- **Acceptance Criteria**:
  - [x] Pytest suite validates all extracted nodes and edges against ground truth.
  - [x] Tests run in < 5 seconds in CI pipeline.
  - [x] Coverage >= 90% across `apps/api/parsers/`.
