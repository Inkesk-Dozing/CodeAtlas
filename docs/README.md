# CodeAtlas Documentation

Complete planning and technical documentation for CodeAtlas â€” AI-Augmented Monorepo Onboarding Engine.

## Document Index

| # | Document | Purpose |
|---|----------|---------|
| 01 | [Project Overview](01-project-overview.md) | Vision, problem, solution, target users, success metrics |
| 02 | [Tech Stack & Architecture](02-tech-stack.md) | Technology choices, high-level architecture, data models, API contracts |
| 03 | [Phases](03-phases.md) | Phase-wise implementation plan with tasks, estimates, exit criteria |
| 04 | [Ingestion Pipeline](04-ingestion-pipeline.md) | Clone â†’ Parse â†’ Extract â†’ Embed â†’ Persist specification |
| 05 | [Issue Mapping](05-issue-mapping.md) | Issue-to-code mapping algorithm, ranking, feedback loop |
| 06 | [API Specification](06-api-spec.md) | REST API endpoints, request/response formats, rate limiting |
| 07 | [Frontend Architecture](07-frontend-architecture.md) | React Flow components, state management, graph algorithms |
| 08 | [Database Schema](08-database-schema.md) | PostgreSQL schema, migrations, indexes, RLS policies |
| 09 | [Infrastructure](09-infrastructure.md) | Docker Compose, Kubernetes, Terraform, CI/CD, scaling |
| 10 | [Testing Strategy](10-testing-strategy.md) | Unit, integration, E2E, performance, visual regression tests |
| 11 | [Security](11-security.md) | Auth, RBAC, encryption, webhook security, audit logging |
| 12 | [Monitoring](12-monitoring.md) | Metrics, alerts, dashboards, tracing, logging, runbooks |
| 13 | [Developer Guide](13-developer-guide.md) | Local setup, project structure, workflows, debugging |
| 14 | [PRD](14-prd.md) | Product requirements, user stories, personas, KPIs |
| 15 | [Roadmap](15-roadmap.md) | Week-by-week plan, milestones, team allocation, budget |
| 16 | [Master Convergence Roadmap (CodeAtlas Prime)](roadmap/unified-platform-roadmap.md) | CodeAtlas + GitWatcher fusion, competitive teardown,  cost blueprint |

## Reading Order

### For Product/Business Stakeholders
1. `01-project-overview.md` â€” What is CodeAtlas and why
2. `14-prd.md` â€” Detailed requirements and user stories
3. `15-roadmap.md` â€” Timeline, budget, milestones

### For Backend Engineers
1. `02-tech-stack.md` â€” Architecture overview
2. `06-api-spec.md` â€” API contracts
3. `04-ingestion-pipeline.md` â€” Pipeline internals
4. `05-issue-mapping.md` â€” Mapping algorithm
5. `08-database-schema.md` â€” Database design
6. `10-testing-strategy.md` â€” Testing approach

### For Frontend Engineers
1. `07-frontend-architecture.md` â€” Component structure
2. `06-api-spec.md` â€” API endpoints
3. `03-phases.md` â€” Phase 2 graph UX requirements
4. `10-testing-strategy.md` â€” Frontend testing

### For DevOps/Platform
1. `09-infrastructure.md` â€” Deployment, K8s, CI/CD
2. `11-security.md` â€” Security hardening
3. `12-monitoring.md` â€” Observability stack
4. `08-database-schema.md` â€” Backup/recovery

### For New Team Members
1. `13-developer-guide.md` â€” Local setup and workflows
2. `01-project-overview.md` â€” Product context
3. `03-phases.md` â€” Current phase and goals

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

### Timeline
- Phase 0 (Foundation): Weeks 1-2
- Phase 1 (Ingestion & Graph): Weeks 3-5
- Phase 2 (Issue Mapping): Weeks 6-8
- Phase 3 (AI & Docs): Weeks 9-11
- Phase 4 (SaaS): Weeks 12-16
- Phase 5 (Advanced): Post-launch