# CodeAtlas - Phase-wise Implementation Plan

## Phase 0: Foundation (Weeks 1-2)
**Goal**: Core infrastructure, auth, and repository ingestion skeleton

### Deliverables
- [ ] Monorepo setup (Turborepo + pnpm workspaces)
- [ ] Docker Compose for local dev (PostgreSQL+pgvector, Redis, MinIO, Ollama)
- [ ] GitHub App registration & OAuth flow
- [ ] FastAPI project with base models, migrations (Alembic)
- [ ] Next.js project with React Flow, Tailwind, auth context
- [ ] CI/CD pipeline (lint, typecheck, test, build)

### Tasks
| Task | Owner | Estimate |
|------|-------|----------|
| Initialize Turborepo with apps/api, apps/web, packages/shared | BE | 2d |
| Configure PostgreSQL + pgvector extension | BE | 1d |
| Implement GitHub OAuth (FastAPI + NextAuth.js) | Full-stack | 3d |
| Create Repository, Installation models + migrations | BE | 1d |
| Build GitHub App webhook receiver (signature verification) | BE | 2d |
| Set up Celery + Redis for background jobs | BE | 1d |
| Create shared TypeScript/Python types package | Shared | 2d |
| Basic React Flow canvas with node/edge types | FE | 3d |

### Exit Criteria
- User can install GitHub App, authenticate, see repository list
- Webhook receives push events
- Empty graph renders in frontend

---

## Phase 1: Repository Ingestion & Graph Building (Weeks 3-5)
**Goal**: Clone repos, parse code, build dependency graph, store in DB

### Deliverables
- [ ] Repository cloner (shallow clone, sparse checkout for monorepos)
- [ ] Multi-language AST parser (Tree-sitter: TS/JS, Python, Go, Rust, Java)
- [ ] Dependency extraction (imports, exports, function calls, routes)
- [ ] Graph persistence with pgvector embeddings
- [ ] Incremental update on push webhook
- [ ] Progress API for frontend polling

### Tasks
| Task | Owner | Estimate |
|------|-------|----------|
| Design CodeNode/CodeEdge schema + indexes | BE | 1d |
| Implement shallow cloner with GitHub installation token | BE | 2d |
| Tree-sitter parser framework + language plugins | BE | 5d |
| Extract: imports/exports, class/function definitions | BE | 3d |
| Extract: API routes (Express, FastAPI, Next.js, Spring) | BE | 3d |
| Extract: React/Vue/Svelte components, hooks | BE | 3d |
| Extract: Database models (Prisma, SQLAlchemy, Django ORM, GORM) | BE | 2d |
| Build dependency graph (internal + external deps) | BE | 3d |
| Generate embeddings for nodes (batched, cached) | BE | 2d |
| Incremental diff-based update on push | BE | 3d |
| Ingestion status API + WebSocket progress | Full-stack | 2d |

### Language Support Priority
1. **TypeScript/JavaScript** (React, Next.js, Express, NestJS)
2. **Python** (FastAPI, Django, Flask)
3. **Go** (Gin, Echo, stdlib)
4. **Rust** (Actix, Axum)
5. **Java/Kotlin** (Spring Boot)

### Exit Criteria
- Full graph generated for sample monorepo (turborepo starter)
- Graph renders in React Flow with 500+ nodes performantly
- Push to repo triggers incremental update < 60s
- Embeddings enable semantic search

---

## Phase 2: Interactive Graph & Issue Mapping (Weeks 6-8)
**Goal**: Rich graph UX, issue-to-code mapping, natural language search

### Deliverables
- [ ] React Flow graph with clustering, filtering, search
- [ ] Node detail panel (code preview, complexity, docs)
- [ ] GitHub Issue fetch + analysis pipeline
- [ ] Semantic issue-to-code mapping
- [ ] Natural language query endpoint
- [ ] User feedback loop for mapping validation

### Tasks
| Task | Owner | Estimate |
|------|-------|----------|
| Graph: clustering by directory/module | FE | 3d |
| Graph: filtering by type, language, complexity | FE | 2d |
| Graph: search highlight + center on node | FE | 2d |
| Graph: minimap, zoom-to-fit, layout options | FE | 2d |
| Node detail sidebar: code, metrics, relationships | FE | 3d |
| Issue fetcher (REST + GraphQL for comments) | BE | 1d |
| Issue analyzer: extract intent, keywords, file hints | BE | 3d |
| Mapper: semantic similarity (issue ↔ node embeddings) | BE | 2d |
| Mapper: structural heuristics (route names, model names) | BE | 2d |
| Mapper: combine scores + confidence calibration | BE | 2d |
| Semantic search API (vector + keyword hybrid) | BE | 2d |
| Search UI: natural language input, results list | FE | 2d |
| Feedback API: thumbs up/down on mappings | Full-stack | 1d |

### Issue Mapping Algorithm
```
1. Parse issue title/body → extract entities (routes, models, components)
2. Embed issue text → vector search against node embeddings (top-k)
3. Structural matching: regex on paths, route patterns, model names
4. Graph propagation: include neighbors of high-confidence nodes
5. Rank by combined score → return top-N with confidence %
6. Store mapping + allow user validation → retrain ranker
```

### Exit Criteria
- User clicks issue → sees highlighted subgraph in < 2s
- Semantic search returns relevant files for "auth middleware"
- Mapping accuracy > 75% on labeled test set
- Graph handles 2000+ nodes at 60fps

---

## Phase 3: AI Summarization & Documentation (Weeks 9-11)
**Goal**: Auto-generated explanations, complexity analysis, living docs

### Deliverables
- [ ] Directory/module purpose summarization
- [ ] Code complexity scoring (cyclomatic, cognitive, maintainability)
- [ ] Architecture overview generation (Markdown/Notion sync)
- [ ] Onboarding guide generation per repository
- [ ] Chat interface for codebase Q&A

### Tasks
| Task | Owner | Estimate |
|------|-------|----------|
| Summarizer: directory-level (README-style) | BE | 3d |
| Summarizer: module/class/function (docstring + context) | BE | 3d |
| Complexity analyzer: radon (Py) + custom (TS/JS/Go) | BE | 3d |
| Architecture doc generator (Mermaid + Markdown) | BE | 2d |
| Onboarding guide: "First 5 issues to pick up" | BE | 2d |
| Chat API: RAG over code embeddings + summaries | BE | 4d |
| Chat UI: streaming responses, citations, history | FE | 3d |
| Notion/Confluence sync (optional) | BE | 2d |
| Scheduled re-analysis (weekly cron) | BE | 1d |

### Summarization Prompts
```
Directory: "Summarize the purpose of this directory in 2-3 sentences. 
Focus on: responsibility, key exports, external dependencies."

Module: "Explain what this module does, its public API, and how it fits 
in the architecture. Include key classes/functions and data flow."
```

### Exit Criteria
- Every directory has auto-generated summary
- Complexity scores match manual review
- Chat answers "Where is user authentication?" with file links
- Docs update automatically on merge to main

---

## Phase 4: Multi-tenant SaaS & Polish (Weeks 12-16)
**Goal**: Production-ready multi-tenant platform

### Deliverables
- [ ] Organization/workspace model
- [ ] Role-based access (Admin, Member, Viewer)
- [ ] Billing integration (Stripe)
- [ ] Admin dashboard (usage, quotas, health)
- [ ] Public API for integrations
- [ ] Comprehensive test coverage
- [ ] Documentation site
- [ ] Landing page + waitlist

### Tasks
| Task | Owner | Estimate |
|------|-------|----------|
| Org/Workspace models + RLS policies | BE | 2d |
| Invite flow, role management | Full-stack | 3d |
| Stripe: subscriptions, usage-based billing | BE | 3d |
| Quota enforcement (repos, analyses, API calls) | BE | 2d |
| Admin dashboard: org list, repo health, errors | FE | 4d |
| Public API: tokens, rate limits, webhooks | BE | 3d |
| E2E tests (Playwright): auth, graph, search, chat | QA | 5d |
| Load test: 100 concurrent ingestions | BE | 2d |
| Docs site (Nextra/Docusaurus) | FE | 3d |
| Landing page + waitlist form | FE | 2d |
| Security audit + penetration test | Security | 3d |

### Exit Criteria
- Multi-tenant isolation verified
- 99.9% uptime SLA achievable
- SOC2 Type II ready
- 10 pilot organizations onboarded

---

## Phase 5: CodeAtlas Prime Convergence (Weeks 13-16)
**Goal**: Unified engineering intelligence merging topological AST analysis with temporal git churn, PR blast radius automation, and architectural governance.

### Deliverables
- [ ] PR "Blast Radius" GitHub App Bot with automated architectural impact comments
- [ ] Architectural boundary enforcement engine ("The Architecture Linter" via `codeatlas.config.json`)
- [ ] "Bus Factor" and single-maintainer knowledge silo risk analysis
- [ ] Dynamic README SVG architecture badge generator
- [ ] Temporal commit churn heatmap overlay on spatial React Flow nodes
- [ ] GitWatcher / GitPulse telemetry convergence
- [ ] Cross-branch architectural drift tracking
- [ ] CodeAtlas VS Code and JetBrains IDE extensions

### Tasks
| Task | Owner | Estimate |
|------|-------|----------|
| PR Blast Radius GitHub App webhook and comment generator | Backend | 4d |
| Architecture boundary linter and CI exit code checker | Backend | 3d |
| Bus factor calculation and knowledge silo alert shader | Full-stack | 3d |
| Dynamic README architecture SVG generator | Backend | 2d |
| Commit churn heatmap overlay on React Flow canvas | Frontend | 4d |
| VS Code extension with graph preview and hover insights | Frontend | 5d |
| Architectural drift engine comparing branches and tags | Backend | 4d |

### Exit Criteria
- PR Bot posts automated blast radius reports on incoming pull requests
- Architecture linter blocks CI on illegal cross-module imports
- Canvas dynamically colors nodes by 30-day commit churn velocity
- IDE extension enables graph navigation directly inside editor

---

## Phase 6: Developer Flight Simulator, Active Telemetry & Verifiable Credential Ecosystem (Weeks 17-20)
**Goal**: Interactive git flight simulator, verifiable Ed25519 developer credentials, WakaTime-compatible cognitive telemetry, and AST-driven agent prompt generation.

### Deliverables
- [x] **Chronos Engine**: Timeline commit scrubber, what-if AST refactor mutation simulator, and architectural archaeology provenance modal
- [x] **OmniQuery Schema Lens**: Conversational database workbench, ORM discovery, code dependency checks, and sandboxed rollback dry-runs
- [ ] **OpenSourceMapper**: AST-driven "Good First Issue" triage, 3-step contributor blueprints, and prerequisite knowledge checklists
- [ ] **Active Editor Telemetry**: Local WakaTime-compatible heartbeat stream, AST focus time mapping, and Cognitive Friction Index (CFI) alerts
- [ ] **GitReverse Engine**: Hierarchical AST token budget optimizer, automated `AGENTS.md`, `.cursorrules`, and `llms.txt` generation
- [ ] **CodeAtlas Flight Simulator**: In-browser virtual Git shell, simulated pull request bot reviews, and merge conflict resolution challenges
- [ ] **Holopin-Style Verifiable Badges**: Dynamic vector SVG badges, Ed25519 cryptographic digital signatures, public verification portal, and viral collectible badge board

### Tasks
| Task | Owner | Estimate |
|------|-------|----------|
| Chronos timeline scrubber, diff engine & simulation modal | Full-stack | Completed |
| OmniQuery conversational SQL lens & sandbox rollback engine | Full-stack | Completed |
| OpenSourceMapper AST isolation scorer & 3-step blueprint UI | Full-stack | 4d |
| Telemetry heartbeat receiver & Cognitive Friction Index engine | Backend | 3d |
| React Flow focus time heatmap shader & pulse dashboard | Frontend | 3d |
| GitReverse prompt packager (`AGENTS.md`, `.cursorrules`) | Backend | 3d |
| In-browser virtual Git shell & PR bot reviewer | Full-stack | 5d |
| Dynamic SVG badge generator & Ed25519 digital signature service | Backend | 3d |
| Public verification portal & Holopin-style hexagonal badge board | Frontend | 4d |

### Exit Criteria
- New contributors can complete virtual Git missions in the Flight Simulator without installing local software
- Learners receive mathematically verifiable, tamper-proof Ed25519-signed SVG badges for their GitHub READMEs
- Active editor focus time is mapped to AST nodes without logging keystrokes or source code
- Developers can export complete `AGENTS.md` and `.cursorrules` optimized for LLM token limits in one click


---

## Phase 7: IDE Extensions, Micro-Workspaces & Cross-Monorepo Federation (Weeks 21–24)
**Goal**: Native developer environment integration, zero-cloud desktop sidecars, offline local caching, and cross-repository microservice federation.

### Deliverables
- [ ] VS Code Extension Language Server Protocol (LSP) AST bridge
- [ ] JetBrains IntelliJ IDEA / PyCharm JCEF canvas sidepane
- [ ] Neovim Lua & Tree-Sitter live telemetry and quickfix blast radius inspector
- [ ] Tauri & Rust bare-metal desktop sidecar with multi-threaded parser
- [ ] Local SQLite edge cache for offline monorepo navigation
- [ ] Multi-repository cross-dependency graph federation via OpenAPI / Protobuf
- [ ] Package boundary firewall and circular dependency cycle preventer
- [ ] Custom CodeAtlasQL query engine for automated architectural rule checking
- [ ] GitHub App PR review bot with interactive SVG diff embeds
- [ ] Slack & Discord conversational bots with `/codeatlas` slash commands

### Tasks
| Task | Owner | Estimate |
|------|-------|----------|
| VS Code LSP server and AST hover provider | Frontend | 5d |
| JetBrains JCEF tool window and Kotlin PSI listener | Frontend | 5d |
| Neovim Lua autocommands and IPC socket client | Backend | 3d |
| Tauri Rust multi-threaded parser with Rayon | Systems | 8d |
| SQLite edge cache and timestamp-based delta sync | Full-stack | 5d |
| Multi-repo federation engine and OpenAPI/Protobuf parser | Backend | 8d |
| CodeAtlasQL query lexer, parser, and traversal engine | Backend | 8d |
| GitHub PR bot with SVG diff generator | Backend | 5d |
| Slack / Discord bot with Block Kit / Embed cards | Backend | 3d |

### Exit Criteria
- Developers can hover over any symbol in VS Code / JetBrains to view blast radiuses without leaving the editor
- Complete graph exploration and AST search function offline via local SQLite cache
- Multi-repository microservice dependencies are traced end-to-end on the canvas
- CodeAtlasQL queries execute in $< 100	ext{ms}$ across 50,000 nodes

---

## Phase 8: Autonomous SWE Agents, Code Repair & Benchmark Evaluation (Weeks 25–28)
**Goal**: Autonomous software engineering agents, automated bug repair, SWE-bench evaluation harnesses, multi-agent collaboration, and formal patch verification.

### Deliverables
- [ ] Autonomous SWE-bench Lite & Full benchmark evaluation harness
- [ ] AST-guided spectrum-based fault localization (SBFL via Ochiai / Tarantula)
- [ ] Multi-agent collaboration protocol (Planner, Coder, Reviewer, Verifier)
- [ ] Ephemeral rootless Docker container isolation sandbox with `--network none`
- [ ] Formal AST import and interface verification engine preventing hallucinations
- [ ] Auto-scaffolding PR patch generator for verified issues
- [ ] Token budget cost optimizer and prompt caching pipeline
- [ ] Self-healing test failure reflection loop (up to 3 automated retry attempts)
- [ ] Human-in-the-loop approval workflow for agent-generated pull requests

### Tasks
| Task | Owner | Estimate |
|------|-------|----------|
| SWE-bench benchmark container harness and evaluator | ML / QA | 8d |
| Spectrum-based fault localizer (SBFL) with Ochiai formula | Backend | 5d |
| Multi-agent orchestrator with Planner, Coder, Reviewer personas | AI / ML | 8d |
| Ephemeral rootless Docker sandbox runner with tmpfs | DevOps | 5d |
| Formal AST import validator and boundary contract checker | Backend | 5d |
| PR patch generator with automated branch creation and tests | Full-stack | 5d |
| Reflection loop ingesting compiler/test diagnostics for retry | AI / ML | 8d |
| Web UI for human-in-the-loop review and AST diff preview | Frontend | 5d |

### Exit Criteria
- Autonomous agent achieves $> 25\%$ resolution rate on SWE-bench Lite benchmark
- Fault localization isolates root-cause files within Top-5 candidates in $> 80\%$ of tasks
- Generated patches contain zero hallucinated imports or illegal cross-package dependencies
- All agent code execution is strictly sandboxed without host filesystem or network access

---

## Phase 9: Enterprise Governance, Security Compliance & Air-Gapped High Availability (Weeks 29–32)
**Goal**: 100% air-gapped on-premise Kubernetes deployments, SOC 2 Type II compliance audit logging, enterprise SAML 2.0 / OIDC SSO, granular RBAC, and disaster recovery.

### Deliverables
- [ ] 100% air-gapped production Kubernetes Helm charts (`charts/codeatlas`)
- [ ] SOC 2 Type II immutable cryptographic audit logging with SHA-256 Merkle chaining
- [ ] Enterprise SAML 2.0 and OIDC Single Sign-On (Okta, Azure AD, Keycloak)
- [ ] PostgreSQL Row-Level Security (RLS) multi-tenant data isolation policies
- [ ] Open-source software (OSS) license compliance and CVE vulnerability graph mapping
- [ ] Disaster recovery automated cross-region PostgreSQL streaming replication
- [ ] Granular Path-Based Access Control (PBAC) for sensitive monorepo subtrees
- [ ] Distributed Celery worker Horizontal Pod Autoscaler (HPA) via Redis queue metrics
- [ ] High-availability Redis 7 Sentinel cluster with automatic failover
- [ ] MinIO multi-tenant distributed object storage cluster

### Tasks
| Task | Owner | Estimate |
|------|-------|----------|
| Air-gapped Helm chart with pre-packaged images and model weights | DevOps | 8d |
| Immutable Merkle-tree audit logging service | Security | 5d |
| SAML 2.0 SP and OIDC client with JIT user provisioning | Security | 8d |
| PostgreSQL Row-Level Security migrations and tenant context | Database | 5d |
| SPDX license scanner and CycloneDX SBOM generator | Backend | 5d |
| PostgreSQL streaming replication and failover controller | Database | 8d |
| Subtree path-based access control middleware | Security | 5d |
| Celery HPA autoscaler and Prometheus metrics exporter | DevOps | 5d |
| Redis Sentinel HA cluster deployment | DevOps | 5d |
| Chaos engineering tests (Chaos Mesh pod kill simulations) | QA | 5d |

### Exit Criteria
- System deploys and operates with 100% functionality in an air-gapped VPC with zero internet egress
- Database Row-Level Security blocks cross-tenant reads even if application filters are bypassed
- Enterprise SAML SSO authenticates corporate users and maps directory groups to RBAC
- RTO $< 5$ minutes and RPO $< 1$ minute under simulated primary database failure
---

## Phase 10: Hyperscale Observability, Distributed Resilience & Stream Ingestion (Weeks 33–36)

### Goal
Establish enterprise-grade hyperscale observability, distributed lock managers, high-throughput stream ingestion (100k events/sec), zero-copy memory-mapped AST parsers, eBPF kernel sandboxing, automated chaos engineering, and multi-region high availability.

### Key Deliverables
- **OpenTelemetry Distributed Tracing**: Full W3C `traceparent` context propagation across API gateway, Celery workers, and background tree-sitter parsers.
- **Distributed Concurrency & Rate Limiting**: Redis Cluster distributed token-bucket rate limiter with Lua atomic execution and SingleFlight request coalescing.
- **Zero-Copy Memory-Mapped Streaming Parser**: Apache Arrow columnar buffers and POSIX `mmap` parsing multi-gigabyte source files with zero RAM duplication.
- **Kafka High-Throughput Webhook Ingestion**: 32-partition topic with partition key hashing and idempotent consumer groups with Exactly-Once Semantics (EOS).
- **eBPF & Landlock Kernel Sandboxing**: Linux kernel syscall filtering (`sys_enter_execve`, `sys_enter_connect`) isolating unprivileged AST subprocesses.
- **Kubernetes Resilience**: KEDA `ScaledObject` autoscaling worker pools up to 64 pods, Pod Disruption Budgets (PDB), and dynamic CFS thread-pool tuning.
- **Active-Active High Availability**: PostgreSQL 16 logical replication across multi-region clusters, WAL-G continuous archiving (RPO < 60s, RTO < 20m).

### Phase 10 Tasks (`Issue 301 – Issue 350`)
| Task | Track | Est. |
|------|-------|------|
| OpenTelemetry W3C trace context injector and tail-based span sampler | Observability | 5d |
| Redis Cluster token-bucket limiter and SingleFlight request coalescer | Performance | 5d |
| Zero-copy mmap Tree-sitter parser with Apache Arrow buffers | Parser | 8d |
| Kafka 3.6+ webhook ingestion topic with partition hashing and idempotent consumers | Streaming | 8d |
| eBPF Linux kernel syscall auditor and Landlock LSM sandbox enforcer | Security | 8d |
| KEDA Celery worker autoscaler and Kubernetes Pod Disruption Budgets | DevOps | 5d |
| Dynamic adaptive circuit breaker with exponential backoff and decorrelated jitter | Resilience | 5d |
| Prometheus high-frequency metric exporter and Grafana SRE dashboard templates | Observability | 5d |
| Multi-region active-active PostgreSQL logical replication and WAL-G archiving | Database | 8d |
| Automated chaos engineering suite (Toxiproxy and Chaos Mesh experiments) | QA | 5d |

### Exit Criteria
- Ingestion pipeline sustains 100,000 webhook events/sec with $< 20\text{ms}$ publish latency
- Memory consumption for 500MB source files drops from 3.2GB to $< 60\text{MB}$ via zero-copy mmap
- System demonstrates 100% availability during simulated regional failovers and pod evictions
- OpenTelemetry traces correlate 100% of distributed transactions across API and background workers
---

## Phase 11: WebGPU High-Performance Canvas & Real-Time CRDT Multi-User Collaboration (Weeks 37–40)

### Goal
Deliver a hardware-accelerated WebGPU/WebGL canvas engine capable of rendering 1,000,000+ nodes and edges at 60–120 FPS, multi-threaded Wasm Barnes-Hut physics, Louvain community clustering, Hierarchical Edge Bundling (HEB), real-time Yjs CRDT multi-user collaboration, and Chronos 4D vertex interpolation.

### Key Deliverables
- **WebGPU Compute & Instanced Rendering**: WGSL compute shaders simulating 1,000,000+ nodes in GPU VRAM and single-pass instanced draw calls (`drawIndexedIndirect`).
- **Rust/Wasm Physics Engines**: Multi-threaded Barnes-Hut $O(N \log N)$ and Fast Multipole Method (FMM) $O(N)$ spatial force solvers compiled to WebAssembly.
- **Spatial Quadtree Frustum Culling**: Viewport matrix frustum culling discarding $> 95\%$ of off-screen nodes before GPU submission.
- **Topological Community Detection**: Client-side Louvain modularity clustering and Markov Cluster Algorithm (MCL) discovering microservice boundaries.
- **Hierarchical Edge Bundling (HEB)**: Dynamic cubic B-spline curves eliminating visual hairballs on dense dependency graphs.
- **Real-Time Multi-User CRDT Co-Editing**: Yjs `Y.Map` and `Y.Array` state matrices synchronizing canvas edits over WebSockets with zero conflict divergence.
- **Collaborative Presence & Awareness**: Live cursor tracking, spotlight presenter follow mode, and spatial proximity audio/text pings.
- **Semantic Level-of-Detail (LoD0-LoD3)**: Smooth cross-fading zoom from macro galaxy domain bubbles down to function-level AST syntax trees.
- **Chronos 4D Temporal Shaders**: WebGL vertex shader interpolation morphing node coordinates and edge connections smoothly across Git commit timelines.

### Phase 11 Tasks (`Issue 351 – Issue 400`)
| Task | Track | Est. |
|------|-------|------|
| WebGPU compute shader pipeline and instanced vertex buffer renderer | Canvas/GPU | 10d |
| WebAssembly Rust Barnes-Hut and FMM physics engine | Algorithms | 8d |
| Spatial Quadtree frustum culling and WebGL 2.0 fallback renderer | Canvas/GPU | 6d |
| Client-side Louvain modularity clustering and Markov Cluster Algorithm | Algorithms | 6d |
| Hierarchical Edge Bundling (HEB) with cubic B-spline curve shaders | Rendering | 6d |
| Yjs CRDT multi-user spatial co-editing matrix and binary state vector sync | Frontend | 8d |
| Ephemeral cursor tracking, spotlight presenter follow mode, and spatial audio | Collab | 5d |
| 4-tier Level-of-Detail (LoD) semantic zoom controller and hardware minimap | Canvas | 5d |
| Chronos 4D temporal vertex shader interpolation and bidirectional scrubber | Chronos | 6d |
| GPU bloom and heat-distortion post-processing shaders for CFI hotspots | Shaders | 5d |

### Exit Criteria
- Canvas maintains locked 60-120 FPS on 1,000,000 nodes on modern discrete GPUs
- Draw call count reduced from 50,000+ down to $< 10$ draw calls per frame via instancing
- Multi-user concurrent co-editing verified with zero state divergence across 20 simultaneous collaborators
- Chronos timeline scrubbing operates with butter-smooth 60 FPS transitions between any two Git commits
---

## Phase 12: Domain-Specific AI, Contrastive AST Embeddings & Local Neural Model Quantization (Weeks 41–44)

### Goal
Train and deploy domain-specific Graph Neural Networks (GNNs) on AST syntax subtrees, establish self-supervised contrastive learning (InfoNCE), compile local GGUF/ONNX quantized models with hardware acceleration (Metal, CUDA, WebGPU), provide multi-modal whiteboard diagram parsing, and build autonomous AST refactoring engines.

### Key Deliverables
- **Relational GCN & Tree-LSTM**: Neural architecture modeling AST nodes and syntax relations (parent, child, data-flow, control-flow) into 768-d dense embeddings.
- **Self-Supervised Contrastive Training**: InfoNCE and Triplet Margin Loss pipelines trained on semantic code mutations (variable rename, loop unroll, statement reorder).
- **Fast Semantic Code Clone Detection**: Subtree cosine vector indexing in pgvector detecting Type 1–4 semantic clones with $> 89\%$ recall.
- **GGUF 4-Bit & 8-Bit Quantization**: Post-training quantization compiling PyTorch models into standalone $< 1.8\text{GB}$ binaries running locally.
- **Multi-Platform Hardware Acceleration**: Apple Silicon Metal (MPS), NVIDIA CUDA/TensorRT, and WebGPU compute shaders with CPU INT4 fallback.
- **Multi-Modal Vision Architecture Parser**: Fine-tuned Vision Transformer (ViT) parsing whiteboard sketches and architecture diagrams into live CodeAtlas graph nodes.
- **Topological Code Smell Detectors**: Automated detection of God Classes ($WMC > 45$, $LCOM4 > 1$), Shotgun Surgery, and Tarjan SCC circular dependencies.
- **Autonomous AST Refactoring Engines**: Safe, comment-preserving formal AST rewriting via LibCST (Python), TS-Morph (TypeScript), and Syn/Quote (Rust).
- **Graph-Augmented LLM Prompts**: Synthesizer injecting 2-hop caller/callee AST context and enforcing caller contract verification.

### Phase 12 Tasks (`Issue 401 – Issue 450`)
| Task | Track | Est. |
|------|-------|------|
| PyTorch Relational GCN and Tree-LSTM model architecture for AST subtrees | AI/ML | 8d |
| InfoNCE and Triplet Margin Loss contrastive training pipeline on AST mutations | AI/ML | 8d |
| Type 1-4 semantic code clone detection via pgvector HNSW cosine similarity | Search | 5d |
| GGUF quantization compiler (Q4_K_M and Q8_0) and ONNX runtime integration | Inference | 6d |
| Apple Silicon Metal (MPS) and NVIDIA CUDA hardware acceleration modules | Inference | 6d |
| Multi-modal Vision Transformer (ViT) for whiteboard diagram extraction | Vision | 8d |
| Topological anti-pattern detectors (God Class, Shotgun Surgery, Tarjan SCC) | Analysis | 6d |
| Autonomous formal AST refactoring engines (LibCST, TS-Morph, Syn/Quote) | Refactoring | 8d |
| Graph-augmented prompt synthesizer with caller/callee contract verifier | RAG | 6d |
| 100% air-gapped model key management and cryptographic weight loader | Security | 5d |

### Exit Criteria
- GNN achieves $> 94\%$ accuracy on downstream code algorithm classification benchmarks
- GGUF 4-bit model runs within 4GB host RAM with $< 1.2\%$ degradation in retrieval accuracy
- Whiteboard photos converted into structured architecture graphs with $> 92\%$ OCR accuracy
- Autonomous AST refactorings pass type-checking and unit tests with 100% comment and whitespace preservation
---

## Phase 13: SCM Ecosystem Federation, CI/CD Native Quality Gates & Developer Platform API (Weeks 45–48)

### Goal
Complete the 500-issue engineering platform with official CI/CD quality gates (GitHub Actions, GitLab CI, Bitbucket Pipelines), multi-SCM federation (GitLab Self-Managed, Bitbucket Data Center, Perforce, Gerrit, Azure DevOps), Public GraphQL and REST v2 Developer APIs, auto-generated SDKs, OPA Rego policy compliance, native CLI (`codeatlas`), and production golden master release verification.

### Key Deliverables
- **Official GitHub Action Runner**: TypeScript action (`codeatlas/action@v1`) with native SARIF 2.1.0 report generation and PR check run blocking.
- **GitLab CI & Bitbucket Pipelines Integrations**: Official GitLab CI/CD component and Bitbucket Pipe with Code Insights reports and MR decorations.
- **Multi-SCM Depot Ingestion**: Connectors for GitLab Self-Managed, Bitbucket Data Center, Perforce Helix Core, Gerrit, and Azure DevOps Repos.
- **Public Developer GraphQL & REST APIs**: Apollo Federation v2 schema with DataLoader batching and REST API v2 with complete OpenAPI 3.1 specifications.
- **Client SDK Ecosystem**: Auto-generated strongly typed SDKs for TypeScript/Node.js, Python (asyncio), Go, and Rust.
- **Cryptographic Webhook Security**: HMAC-SHA256 signature verification and timestamp/nonce replay attack mitigation.
- **Architectural Policy Engine (OPA Rego)**: Embedded Open Policy Agent evaluating `codeatlas.policy.rego` rules against AST mutation graphs in CI.
- **Enterprise Project Tracking Sync**: Bi-directional issue and milestone synchronization with Jira, Linear, and Asana.
- **Standalone Static Docs Exporter**: Zero-server HTML/Wasm offline bundle containing complete architecture graph and WebGPU viewer.
- **Native CodeAtlas CLI**: Standalone binary in Go/Rust with interactive terminal TUI, graph visualizer, blast radius analyzer, and GitReverse prompt packager.
- **Golden Master Verification**: Final release script verifying all 500 engineering backlog issues and generating cryptographically signed release binaries.

### Phase 13 Tasks (`Issue 451 – Issue 500`)
| Task | Track | Est. |
|------|-------|------|
| Official GitHub Action with SARIF 2.1.0 output and PR check run gate | CI/CD | 6d |
| GitLab CI/CD component and Bitbucket Pipelines pipe with PR decorations | CI/CD | 6d |
| Perforce Helix Core depot connector and Gerrit review voting bot | SCM | 8d |
| Azure DevOps native marketplace extension and PR status policy | SCM | 6d |
| Public Developer GraphQL API with Apollo Federation v2 and DataLoader | API | 6d |
| Public REST API v2 with OpenAPI 3.1 specification and Swagger UI portal | API | 5d |
| Auto-generated client SDKs for TypeScript, Python, Go, and Rust | SDK | 6d |
| Webhook HMAC-SHA256 security gateway and nonce replay defense | Security | 5d |
| Open Policy Agent (OPA) Rego rule engine for architectural compliance | Policy | 6d |
| Standalone offline static documentation exporter (HTML/Wasm bundle) | Export | 6d |
| Native CodeAtlas CLI (Go/Rust binary) with terminal TUI and GitReverse exports | CLI | 8d |
| Golden Master production readiness release verification script | Release | 5d |

### Exit Criteria
- GitHub Action, GitLab CI, and Bitbucket Pipe verify PRs and block merges on architectural drift in $< 20\text{seconds}$
- Public GraphQL and REST v2 APIs pass 100% compliance test suite with $< 18\text{ms}$ query latency
- Auto-generated SDKs (TS, Python, Go, Rust) published with 100% passing test suites and strict typings
- All 500 backlog issues verified complete and certified ready for planetary-scale enterprise deployment
---

## Resource Estimation

### Team Composition (Minimum Viable)
| Role | Phase 0-1 | Phase 2-3 | Phase 4 |
|------|-----------|-----------|---------|
| Backend Engineer | 2 | 2 | 2 |
| Frontend Engineer | 1 | 2 | 2 |
| ML/AI Engineer | 0.5 | 1 | 1 |
| DevOps/Platform | 0.5 | 0.5 | 1 |
| Designer | 0.25 | 0.5 | 0.5 |
| QA | 0 | 0.5 | 1 |

### Infrastructure Costs (Monthly, at Scale)
| Component | Estimate |
|-----------|----------|
| Kubernetes (EKS/GKE) | $2,000-5,000 |
| PostgreSQL (managed) | $500-1,500 |
| Redis (managed) | $200-500 |
| Object Storage | $100-300 |
| GPU Inference (Ollama/A10G) | $1,000-3,000 |
| GitHub API (included) | $0 |
| Monitoring/Sentry | $200-500 |
| **Total** | **$4,000-10,800** |

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| GitHub API rate limits | High | Medium | Installation tokens, caching, exponential backoff |
| Large repo ingestion timeout | High | High | Chunked processing, streaming, progress checkpoints |
| Embedding quality for code | Medium | High | Fine-tune on code corpus, hybrid search fallback |
| React Flow performance >2k nodes | Medium | High | Virtualization, clustering, WebGL renderer |
| Multi-tenant data leakage | Low | Critical | RLS, penetration testing, audit logs |
| LLM hallucination in chat | Medium | High | Citations, confidence scores, human feedback loop |
| Competitor launches first | Medium | Medium | Focus on monorepo + issue mapping differentiation |