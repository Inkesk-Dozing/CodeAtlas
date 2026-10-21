# CodeAtlas

<p align="center">
  <strong>AI-Augmented Monorepo Onboarding Engine</strong><br />
  <em>Turn any codebase into an interactive living architecture graph, query it with RAG, and map GitHub issues to exact source code locations.</em>
</p>

<p align="center">
  <a href="https://github.com/Inkesk-Dozing/CodeAtlas/actions/workflows/ci.yml"><img src="https://img.shields.io/badge/CI%2FCD-passing-success?style=flat-square&logo=githubactions" alt="CI/CD" /></a>
  <a href="https://opensource.org/licenses/Apache-2.0"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg?style=flat-square" alt="License: Apache 2.0" /></a>
  <a href="https://www.python.org/downloads/release/python-3110/"><img src="https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python&logoColor=white" alt="Python 3.11+" /></a>
  <a href="https://nextjs.org/"><img src="https://img.shields.io/badge/Next.js-14%20App%20Router-black?style=flat-square&logo=next.js" alt="Next.js 14" /></a>
  <a href="https://reactflow.dev/"><img src="https://img.shields.io/badge/React%20Flow-Interactive%20Canvas-ff0072?style=flat-square" alt="React Flow" /></a>
  <a href="https://github.com/pgvector/pgvector"><img src="https://img.shields.io/badge/Postgres-pgvector-336791?style=flat-square&logo=postgresql&logoColor=white" alt="pgvector" /></a>
  <a href="https://turbo.build/repo"><img src="https://img.shields.io/badge/Turborepo-Monorepo-000000?style=flat-square&logo=turborepo" alt="Turborepo" /></a>
  <a href="https://github.com/Inkesk-Dozing/CodeAtlas/blob/main/CONTRIBUTING.md"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square" alt="PRs Welcome" /></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff" /></a>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#core-features">Features</a> •
  <a href="#api-surface-29-routes">API Surface</a> •
  <a href="docs/README.md">Full Documentation</a> •
  <a href="docs/issues/README.md">Issue Backlog (Phases 0–5)</a> •
  <a href="docs/roadmap/unified-platform-roadmap.md">CodeAtlas Prime Roadmap</a>
</p>

---

## 🏷️ GitHub Discoverability & Topics

`codebase-visualization` • `architecture-graph` • `monorepo` • `developer-tools` • `react-flow` • `ast-parser` • `tree-sitter` • `rag` • `pgvector` • `fastapi` • `nextjs` • `turborepo` • `code-search` • `issue-mapping` • `onboarding` • `knowledge-graph` • `software-architecture` • `ollama` • `code-intelligence` • `celery`

---

```
┌──────────────┐   GitHub App    ┌──────────────────┐    pgvector    ┌───────────────┐
│   GitHub     │ ──────────────▶ │  Ingestion API   │ ─────────────▶ │  PostgreSQL   │
│  webhooks    │                 │  (FastAPI+Celery)│                │  + pgvector   │
└──────────────┘                 └────────┬─────────┘                └───────┬───────┘
                                          │ clone → parse → extract → embed   │
                                          ▼                                   │
                                 ┌──────────────────┐                         │
                                 │  Ollama (LLM +   │◀────────────────────────┘
                                 │  embeddings)     │        retrieval
                                 └────────┬─────────┘
                                          │
┌──────────────┐    REST/WebSocket  ┌─────▼───────────┐   React Flow   ┌──────────┐
│   Next.js    │ ◀───────────────── │   API Gateway   │ ◀───────────── │  Graph   │
│   Frontend   │                   │  rate-limited   │                │  Engine  │
└──────────────┘                   └─────────────────┘                └──────────┘
```

## Monorepo layout

```
CodeAtlas/
├── apps/
│   ├── api/                 FastAPI backend (Python 3.11)
│   │   ├── routers/         auth, repos, graph, search, ingestion,
│   │   │                    issues, summaries, chat, webhooks
│   │   ├── services/
│   │   │   ├── auth.py      JWT (RS256/HS256), GitHub OAuth
│   │   │   ├── mapping/     5-signal issue → code ranker
│   │   │   ├── ai/          LLM client, summaries, RAG chat
│   │   │   └── ingestion/   clone → parse → graph extraction
│   │   ├── parsers/         regex-based JS/TS + Python parsers
│   │   ├── tasks/           Celery app + ingestion pipeline
│   │   ├── migrations/      Alembic (0001_initial, 15 tables)
│   │   └── tests/           55 unit/integration tests
│   └── web/                 Next.js 14 + React Flow + Zustand
├── packages/shared/         shared TS types + design tokens
├── infra/docker-compose.yml postgres·pgvector, redis, minio, ollama
├── docs/                    full planning documentation (01–15)
└── .github/workflows/ci.yml lint → typecheck → test → build → push
```

## Quick start

```bash
# 1. Infrastructure
cp .env.example .env
docker compose -f infra/docker-compose.yml up -d

# 2. Backend
cd apps/api
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
alembic upgrade head
uvicorn main:app --reload                             # http://localhost:8000/docs

# 3. Frontend (new terminal)
pnpm install
pnpm dev                                                # or: pnpm --filter @codeatlas/web dev
```

> `pnpm dev` runs API + web together via Turborepo (backend deps must be
> installed in your active Python environment).

## Commands

| Command | Description |
| --- | --- |
| `pnpm install` | install all workspace dependencies |
| `pnpm dev` | start API (`:8000`) + web (`:3000`) together |
| `pnpm --filter @codeatlas/web dev` | start Next.js dev server only |
| `pnpm lint` / `pnpm typecheck` / `pnpm test` | run checks across the monorepo |
| `pnpm build` | production build of web + shared |
| `pnpm db:migrate` | apply database migrations |
| `python -m pytest tests/ -q` | backend test suite (in `apps/api`) |
| `alembic upgrade head` | apply database migrations |
| `alembic revision --autogenerate -m "msg"` | create a new migration |

## Core features

- **Architecture graph** — React Flow canvas with BFS layered layout, node/edge
  filtering, semantic search, subgraph exploration, and minimap.
- **5-signal issue mapping** — semantic (pgvector), structural (pg_trgm),
  topological (1-hop propagation), historical (reviewer feedback), hotspot
  (node degree) → weighted confidence with high/medium/low tiers and suggested
  actions.
- **RAG chat & summaries** — question answering grounded in retrieved code with
  `[path]` citations; node/repo/architecture summaries with hash-based caching.
- **Ingestion pipeline** — clone → parse → extract → embed → persist, with
  per-stage progress, timings, and incremental mode.
- **Production concerns** — request IDs, sliding-window rate limiting, HMAC
  webhook verification, CORS, health/ready probes, Prometheus metrics,
  structured logs, GitHub OAuth, RS256/HS256 JWT.

## API surface (29 routes)

All routes are under `/api/v1`; interactive docs at `/docs`.

| Area | Endpoints |
| --- | --- |
| Auth | `POST /auth/callback`, `POST /auth/refresh`, `GET /auth/me` |
| Repos | `GET/POST /repos`, `GET/PATCH/DELETE /repos/{id}`, `GET /repos/{id}/stats` |
| Graph | `GET /repos/{id}/graph`, `POST /repos/{id}/graph/subgraph`, `GET /repos/{id}/nodes/{id}` |
| Search | `POST /repos/{id}/search/{semantic,structural,hybrid}` |
| Ingestion | `POST /repos/{id}/ingest/trigger`, `GET /repos/{id}/ingest/status` |
| Issues | `GET /repos/{id}/issues`, `POST .../{n}/analyze`, `GET .../{n}/mapping`, `POST .../{n}/feedback` |
| Summaries | `GET /repos/{id}/summary`, `GET /repos/{id}/architecture`, `GET /repos/{id}/nodes/{id}/summary` |
| Chat | `POST /repos/{id}/chat`, `GET /repos/{id}/chat/sessions[/{id}]` |
| Webhooks | `POST /webhooks/github` (HMAC-verified) |

## Verification status

```
backend   55 tests passed (pytest, ~14s)
frontend  10 tests passed (vitest)
typecheck tsc --noEmit clean (web + shared)
lint      next lint clean (warnings only)
build     next build production build OK
openapi   29 paths / 33 schemas generated
```

## Documentation & Roadmap
 
Full planning and engineering docs live in [`docs/`](docs/README.md):
- [Master System Overview](docs/01-project-overview.md)
- [Complete Issue Backlog (Phases 0–5)](docs/issues/README.md) — 115+ granular specifications covering foundation through production and CodeAtlas Prime
- [Phase Implementation Plan](docs/03-phases.md)
- [Unified Platform Roadmap (CodeAtlas Prime)](docs/roadmap/unified-platform-roadmap.md)
- [Ingestion Pipeline Engine](docs/04-ingestion-pipeline.md)
- [5-Signal Issue-to-Code Mapping](docs/05-issue-mapping.md)
- [REST API Specification (29 Routes)](docs/06-api-spec.md)
- [Frontend Architecture & Canvas UX](docs/07-frontend-architecture.md)
- [Database Schema & Migrations](docs/08-database-schema.md)
- [Security Threat Model & Policies](docs/11-security.md)
