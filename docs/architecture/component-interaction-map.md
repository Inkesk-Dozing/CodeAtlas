# Component Interaction Map

## System Component Overview

CodeAtlas is structured as an asynchronous micro-services architecture operating over a shared PostgreSQL (pgvector) datastore and Redis message broker.

```mermaid
sequenceDiagram
    autonumber
    actor Dev as Developer / GitHub User
    participant Web as Web Frontend (Next.js 14)
    participant API as API Gateway (FastAPI)
    participant Worker as Task Worker (Celery)
    participant DB as Postgres + pgvector
    participant Storage as MinIO Storage

    Dev->>Web: Select Repository for Ingestion
    Web->>API: POST /api/v1/repos/{id}/ingest
    API->>Worker: Enqueue Ingestion Task (Repository ID)
    API-->>Web: 202 Accepted (Task ID)
    Worker->>Storage: Clone Repository & Extract AST Nodes
    Worker->>Worker: Parse Code Symbols (Tree-Sitter)
    Worker->>Worker: Generate Node Vectors (Ollama Embeddings)
    Worker->>DB: Bulk Upsert CodeNodes, CodeEdges & Vector Index
    Worker-->>API: Notify Completion via Redis Pub/Sub
    API-->>Web: WebSocket Broadcast (Ingestion Complete)
    Web->>API: GET /api/v1/graph/neighborhood
    API->>DB: Query Subgraph Nodes & Edges
    DB-->>API: Return Graph Payload
    API-->>Web: Render Canvas Nodes (React Flow)
```

## Core Subsystem Workflows

### 1. Ingestion Subsystem
- **Input**: GitHub App Webhook event or manual repository submission.
- **Process**: Celery worker clones sparse repository, executes Tree-Sitter parsing across supported languages (`.ts`, `.tsx`, `.py`, `.js`), extracts entity symbols (functions, classes, routes, models), and generates node embeddings.
- **Output**: Batch upsert into `code_nodes` and `code_edges` tables.

### 2. Issue Mapping Engine
- **Input**: GitHub issue title, body text, and comments.
- **Process**: TF-IDF keyword extraction combined with pgvector cosine similarity search over `code_nodes.embedding`. Graph propagation expands candidates to adjacent neighbor nodes.
- **Output**: Confidence-scored array of affected AST file paths, classes, and functions.

### 3. RAG & Natural Language Chat
- **Input**: User natural language query (e.g., "Where is authentication handled?").
- **Process**: Vector similarity retrieval against pgvector HNSW index → Top-K AST node context formatting → Ollama LLM prompt execution.
- **Output**: Streaming markdown response containing file citations.
