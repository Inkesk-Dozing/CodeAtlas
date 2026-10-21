# CodeAtlas - Tech Stack & Architecture

## High-Level Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   GitHub App    │────▶│  Ingestion      │────▶│  Vector DB      │
│   (OAuth/Webhooks)│   │  Pipeline       │   │  (pgvector)     │
└─────────────────┘     └────────┬────────┘     └────────┬────────┘
                                 │                       │
                                 ▼                       ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │  Graph Builder  │     │  Embedding      │
                        │  (AST/Dependency)│    │  Service        │
                        └────────┬────────┘     └────────┬────────┘
                                 │                       │
                                 ▼                       ▼
                        ┌─────────────────────────────────────────┐
                        │           API Layer (FastAPI)           │
                        │  • Graph Query  • Semantic Search       │
                        │  • Issue Mapping • Summarization        │
                        └─────────────────────┬───────────────────┘
                                              │
                                              ▼
                        ┌─────────────────────────────────────────┐
                        │        Frontend (Next.js + React Flow)  │
                        │  • Interactive Graph  • Issue Viewer    │
                        │  • Search UI  • Settings/Integrations   │
                        └─────────────────────────────────────────┘
```

## Technology Choices

### Frontend
| Component | Technology | Rationale |
|-----------|------------|-----------|
| Framework | Next.js 14 (App Router) | Server components, streaming, optimal for dashboards |
| Graph Visualization | React Flow | Purpose-built for node/edge graphs, extensible, performant |
| State Management | Zustand + React Query | Lightweight, server-state optimized |
| Styling | Tailwind CSS + shadcn/ui | Rapid development, consistent design system |
| Real-time | Socket.io client | Live graph updates during ingestion |

### Backend
| Component | Technology | Rationale |
|-----------|------------|-----------|
| API Framework | FastAPI | Async, auto-docs, type-safe, high performance |
| Language | Python 3.11+ | Best ML/NLP ecosystem, fast development |
| Task Queue | Celery + Redis | Distributed ingestion jobs, retry logic |
| GitHub Integration | PyGithub + GitHub App | Official SDK, fine-grained permissions |

### Database & Storage
| Component | Technology | Rationale |
|-----------|------------|-----------|
| Primary DB | PostgreSQL 16 + pgvector | ACID, vector similarity search, mature |
| Cache | Redis 7 | Session cache, rate limiting, Celery broker |
| Object Storage | S3-compatible (MinIO/Tigris) | Repository clones, generated assets |
| Search | pgvector (HNSW index) | Native vector search, no extra infra |

### AI/ML
| Component | Technology | Rationale |
|-----------|------------|-----------|
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) | Fast, 384-dim, good code understanding |
| Summarization | Local LLM (Ollama: CodeLlama-7b) | Privacy, cost control, code-specialized |
| Code Analysis | Tree-sitter + custom visitors | Multi-language AST parsing, incremental |
| Complexity Metrics | radon (Python) / custom (TS/JS) | Cyclomatic, cognitive, maintainability |

### Infrastructure
| Component | Technology | Rationale |
|-----------|------------|-----------|
| Containerization | Docker + Docker Compose | Dev/prod parity, easy deployment |
| Orchestration | Kubernetes (prod) / Compose (dev) | Scaling, self-healing |
| CI/CD | GitHub Actions | Native GitHub integration |
| Monitoring | Prometheus + Grafana + Sentry | Observability stack |
| Secrets | 1Password CLI / Doppler | Secure secret management |

## Data Models

### Repository
```python
class Repository(Base):
    id: UUID
    github_id: int
    name: str
    full_name: str
    owner: str
    default_branch: str
    installation_id: int
    settings: JSONB  # analysis config, ignored paths, etc.
    status: Enum[pending, analyzing, ready, error]
    last_analyzed_at: DateTime
    created_at: DateTime
```

### CodeNode (Graph Node)
```python
class CodeNode(Base):
    id: UUID
    repo_id: UUID
    type: Enum[file, directory, module, class, function, route, component, model]
    name: str
    path: str  # relative to repo root
    language: str
    metadata: JSONB  # complexity, exports, imports, docstring, etc.
    embedding: Vector(384)  # pgvector
    created_at: DateTime
    updated_at: DateTime
```

### CodeEdge (Graph Edge)
```python
class CodeEdge(Base):
    id: UUID
    repo_id: UUID
    source_id: UUID  # CodeNode
    target_id: UUID  # CodeNode
    type: Enum[imports, extends, calls, routes_to, renders, depends_on]
    weight: float  # strength of relationship
    metadata: JSONB
```

### IssueMapping
```python
class IssueMapping(Base):
    id: UUID
    repo_id: UUID
    issue_number: int
    issue_title: str
    issue_body: str
    affected_nodes: UUID[]  # CodeNode IDs
    confidence_scores: float[]  # per node
    generated_at: DateTime
    validated: bool  # user feedback
```

## API Contracts

### Graph Endpoints
```
GET    /api/v1/repos/{repo_id}/graph              # Full graph (paginated)
GET    /api/v1/repos/{repo_id}/graph/subgraph     # Filtered subgraph
GET    /api/v1/repos/{repo_id}/nodes/{node_id}    # Node details
GET    /api/v1/repos/{repo_id}/nodes/{node_id}/neighbors
```

### Search Endpoints
```
POST   /api/v1/repos/{repo_id}/search/semantic    # Natural language query
POST   /api/v1/repos/{repo_id}/search/structural  # AST-based query
```

### Issue Mapping
```
POST   /api/v1/repos/{repo_id}/issues/{number}/analyze
GET    /api/v1/repos/{repo_id}/issues/{number}/mapping
POST   /api/v1/repos/{repo_id}/issues/{number}/feedback
```

### Ingestion
```
POST   /api/v1/repos/{repo_id}/ingest/trigger     # Manual trigger
GET    /api/v1/repos/{repo_id}/ingest/status      # Progress polling
POST   /api/v1/webhooks/github                    # GitHub webhook receiver
```

## Security Considerations
- GitHub App with minimal permissions (Contents: Read, Metadata: Read, Issues: Read)
- Short-lived installation tokens, never stored
- Repository data encrypted at rest (pgcrypto)
- Row-level security on multi-tenant tables
- Rate limiting per installation
- Audit logging for all data access