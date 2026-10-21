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

## Phase 5: Advanced Features (Post-Launch)
**Goal**: Differentiation and enterprise features

### Ideas
- [ ] **Diff Visualization**: Show architectural changes between branches/PRs
- [ ] **Impact Analysis**: "If I change this model, what breaks?"
- [ ] **Team Knowledge Graph**: Who owns what, tribal knowledge capture
- [ ] **Auto-PR Generation**: Scaffold fixes for common issue patterns
- [ ] **IDE Extension**: VS Code / JetBrains integration
- [ ] **Slack/Discord Bot**: "/codeatlas where is payment processing?"
- [ ] **Compliance Reports**: License scanning, security hotspots
- [ ] **Custom Rules**: Organization-specific architecture patterns

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