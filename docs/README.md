# CodeAtlas Documentation

Complete planning and technical documentation for CodeAtlas — AI-Augmented Monorepo Onboarding Engine & Unified Engineering Intelligence Platform.

## Document Index

| # | Document | Purpose |
|---|----------|---------|
| 01 | [Project Overview](01-project-overview.md) | Vision, problem, solution, tri-engine architecture, success metrics |
| 02 | [Tech Stack & Architecture](02-tech-stack.md) | Technology choices, high-level architecture, data models, API contracts |
| 03 | [Phases](03-phases.md) | Phase-wise implementation plan with tasks, estimates, exit criteria |
| 04 | [Ingestion Pipeline](04-ingestion-pipeline.md) | Clone → Parse → Extract → Embed → Persist specification |
| 05 | [Issue Mapping](05-issue-mapping.md) | Issue-to-code mapping algorithm, 6-signal hybrid ranker, feedback loop |
| 06 | [API Specification](06-api-spec.md) | REST API endpoints, Chronos & OmniQuery endpoints, rate limiting |
| 07 | [Frontend Architecture](07-frontend-architecture.md) | React Flow canvas, timeline bar, OmniQuery drawer, Zustand stores |
| 08 | [Database Schema](08-database-schema.md) | PostgreSQL schema, migrations, indexes, RLS policies |
| 09 | [Infrastructure](09-infrastructure.md) | Docker Compose, Kubernetes, Terraform, CI/CD, scaling |
| 10 | [Testing Strategy](10-testing-strategy.md) | Unit, integration, E2E, performance, visual regression tests |
| 11 | [Security](11-security.md) | Auth, RBAC, encryption, webhook security, audit logging |
| 12 | [Monitoring](12-monitoring.md) | Metrics, alerts, dashboards, tracing, logging, runbooks |
| 13 | [Developer Guide](13-developer-guide.md) | Local setup, project structure, workflows, debugging |
| 14 | [PRD](14-prd.md) | Product requirements, user stories, personas, KPIs |
| 15 | [Roadmap](15-roadmap.md) | Week-by-week plan, milestones, team allocation, budget |
| 16 | [Master Convergence Roadmap (CodeAtlas Prime)](roadmap/unified-platform-roadmap.md) | CodeAtlas + GitWatcher fusion, competitive teardown, operational blueprint |
| 17 | [Component Interaction Map](architecture/component-interaction-map.md) | Asynchronous architecture, sequence diagrams, tri-engine interaction map |
| 18 | [Chronos Engine Specification](components/chronos-engine.md) | Software Time Machine, timeline scrubber, what-if AST mutation, archaeology |
| 19 | [OmniQuery Lens Specification](components/omniquery-lens.md) | Conversational Database Time Machine, NL-to-SQL, multi-stage safety, rollback plan |

## Reading Order

### For Product/Business Stakeholders
1. `01-project-overview.md` — What is CodeAtlas and why
2. `14-prd.md` — Detailed requirements and user stories
3. `15-roadmap.md` — Timeline, budget, milestones
4. `roadmap/unified-platform-roadmap.md` — Unified market convergence and ROI

### For Backend Engineers
1. `02-tech-stack.md` — Architecture overview
2. `06-api-spec.md` — API contracts (including Chronos & OmniQuery)
3. `04-ingestion-pipeline.md` — Pipeline internals
4. `components/chronos-engine.md` — Chronos timeline & AST mutation engine
5. `components/omniquery-lens.md` — OmniQuery database lens & safety pipeline
6. `05-issue-mapping.md` — Mapping algorithm
7. `08-database-schema.md` — Database design
8. `10-testing-strategy.md` — Testing approach

### For Frontend Engineers
1. `07-frontend-architecture.md` — Component structure, canvas, timeline, and drawers
2. `06-api-spec.md` — API endpoints
3. `03-phases.md` — Graph UX and temporal controls
4. `10-testing-strategy.md` — Frontend testing

### For DevOps/Platform
1. `09-infrastructure.md` — Deployment, K8s, CI/CD
2. `11-security.md` — Security hardening
3. `12-monitoring.md` — Observability stack
4. `08-database-schema.md` — Backup/recovery

### For New Team Members
1. `13-developer-guide.md` — Local setup and workflows
2. `01-project-overview.md` — Product context
3. `03-phases.md` — Current phase and goals

## Quick Reference

### Tech Stack
- **Frontend**: Next.js 14, React Flow, Zustand, Tailwind, shadcn/ui
- **Backend**: FastAPI (Python 3.11), Celery, Tree-sitter
- **Database**: PostgreSQL 16 + pgvector, Redis
- **AI**: sentence-transformers, Ollama (CodeLlama), spaCy
- **Infra**: Docker, Kubernetes, Terraform, GitHub Actions

### Key Metrics
- Graph render: 2000+ nodes at 60fps
- Semantic search: < 50ms p95
- Issue mapping: < 2s, > 75% accuracy
- Ingestion: 1000 files < 5 min
- Uptime: 99.9%