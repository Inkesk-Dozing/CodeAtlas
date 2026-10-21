# CodeAtlas - API Specification (OpenAPI 3.1)

## Overview
RESTful API for CodeAtlas platform. All endpoints require authentication via JWT (access token) or GitHub Installation Token.

**Base URL**: `https://api.codeatlas.dev/v1` (production) / `http://localhost:8000/v1` (development)

**Authentication**: Bearer token in `Authorization` header

---

## Common Headers
```
Authorization: Bearer <access_token>
X-GitHub-Installation-ID: <installation_id>  # Required for repo-scoped endpoints
Content-Type: application/json
Accept: application/json
```

---

## Error Responses

### Standard Error Format
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description",
    "details": {},
    "request_id": "uuid"
  }
}
```

### HTTP Status Codes
| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 202 | Accepted (async operation) |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 422 | Validation Error |
| 429 | Rate Limited |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

---

## Rate Limiting
- **Authenticated**: 1000 requests/minute per installation
- **Graph queries**: 100 requests/minute
- **Ingestion triggers**: 10 requests/hour per repo
- **Search**: 60 requests/minute

Headers returned:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1699123456
```

---

## Pagination
All list endpoints support cursor-based pagination:

### Request
```
GET /api/v1/repos/{repo_id}/nodes?limit=50&cursor=eyJpZCI6MTIzfQ==
```

### Response
```json
{
  "data": [...],
  "pagination": {
    "next_cursor": "eyJpZCI6MTIzfQ==",
    "has_more": true,
    "total": 1523
  }
}
```

---

## Repositories

### List Repositories
```
GET /api/v1/repos
```

**Query Parameters**:
- `installation_id` (optional): Filter by GitHub App installation
- `status` (optional): `pending`, `analyzing`, `ready`, `error`
- `limit` (default: 20, max: 100)
- `cursor` (optional): Pagination cursor

**Response**:
```json
{
  "data": [
    {
      "id": "uuid",
      "github_id": 123456789,
      "name": "my-monorepo",
      "full_name": "org/my-monorepo",
      "owner": "org",
      "default_branch": "main",
      "private": true,
      "status": "ready",
      "last_analyzed_at": "2026-10-05T10:30:00Z",
      "node_count": 1247,
      "edge_count": 3891,
      "languages": ["typescript", "python", "go"],
      "created_at": "2026-09-01T00:00:00Z",
      "updated_at": "2026-10-05T10:30:00Z"
    }
  ],
  "pagination": {}
}
```

### Get Repository
```
GET /api/v1/repos/{repo_id}
```

**Response**: Same as list item with additional fields:
- `settings`: Repository analysis configuration
- `webhook_secret`: (masked) Webhook secret for verification

### Create Repository (Trigger Initial Analysis)
```
POST /api/v1/repos
```

**Request**:
```json
{
  "github_id": 123456789,
  "installation_id": 987654321,
  "settings": {
    "ignored_paths": ["node_modules/**", "dist/**", "*.lock"],
    "languages": ["typescript", "python"],
    "analysis_depth": "full",
    "generate_docs": true
  }
}
```

**Response**: 202 Accepted with `Location` header pointing to ingestion status

### Update Repository Settings
```
PATCH /api/v1/repos/{repo_id}
```

**Request**:
```json
{
  "settings": {
    "ignored_paths": ["node_modules/**", "dist/**", ".next/**"],
    "analysis_depth": "incremental"
  }
}
```

### Delete Repository
```
DELETE /api/v1/repos/{repo_id}
```

**Response**: 204 No Content

### Get Repository Stats
```
GET /api/v1/repos/{repo_id}/stats
```

**Response**:
```json
{
  "node_count": 1247,
  "edge_count": 3891,
  "by_type": {
    "file": 342,
    "directory": 89,
    "function": 456,
    "class": 123,
    "route": 67,
    "component": 89,
    "model": 34
  },
  "by_language": {
    "typescript": 890,
    "python": 234,
    "go": 123
  },
  "complexity": {
    "avg_cyclomatic": 4.2,
    "max_cyclomatic": 47,
    "hotspots": [
      {"node_id": "uuid", "name": "PaymentProcessor", "score": 47}
    ]
  },
  "last_ingestion": {
    "started_at": "2026-10-05T10:00:00Z",
    "completed_at": "2026-10-05T10:05:23Z",
    "duration_seconds": 323,
    "files_processed": 1247,
    "status": "completed"
  }
}
```

---

## Graph Endpoints

### Get Full Graph (Paginated)
```
GET /api/v1/repos/{repo_id}/graph
```

**Query Parameters**:
- `limit` (default: 500, max: 2000)
- `cursor`
- `types` (comma-separated): Filter by node types
- `languages` (comma-separated)
- `min_complexity`, `max_complexity`

**Response**:
```json
{
  "nodes": [
    {
      "id": "uuid",
      "type": "function",
      "name": "authenticateUser",
      "path": "src/services/auth.ts",
      "language": "typescript",
      "metadata": {
        "loc": 45,
        "complexity": {"cyclomatic": 3, "cognitive": 8},
        "exports": ["authenticateUser"],
        "imports": ["jwt", "bcrypt"],
        "docstring": "Authenticates user via JWT token"
      },
      "embedding": null
    }
  ],
  "edges": [
    {
      "id": "uuid",
      "source_id": "uuid",
      "target_id": "uuid",
      "type": "calls",
      "weight": 1.0,
      "metadata": {}
    }
  ],
  "pagination": {}
}
```

### Get Subgraph (Filtered)
```
GET /api/v1/repos/{repo_id}/graph/subgraph
```

**Query Parameters**:
- `center_node_id` (required): Center node for subgraph
- `radius` (default: 2): Number of hops
- `edge_types` (comma-separated): Filter edge types
- `max_nodes` (default: 200, max: 500)

**Response**: Same as full graph but limited to subgraph

### Get Node Details
```
GET /api/v1/repos/{repo_id}/nodes/{node_id}
```

**Response**:
```json
{
  "id": "uuid",
  "type": "route",
  "name": "POST /api/auth/login",
  "path": "src/routes/auth.ts",
  "language": "typescript",
  "metadata": {
    "loc": 32,
    "complexity": {"cyclomatic": 2, "cognitive": 5},
    "http_method": "POST",
    "route_path": "/api/auth/login",
    "controller": "AuthController",
    "middleware": ["rateLimit", "validateBody"],
    "docstring": "User login endpoint"
  },
  "summary": "Handles user authentication via email/password, returns JWT tokens",
  "neighbors": {
    "incoming": [...],
    "outgoing": [...]
  },
  "code_preview": "export async function login(req, res) {\n  const { email, password } = req.body;\n  const user = await User.findByEmail(email);\n  ...\n}"
}
```

### Get Node Neighbors
```
GET /api/v1/repos/{repo_id}/nodes/{node_id}/neighbors
```

**Query Parameters**:
- `direction`: `incoming`, `outgoing`, `both` (default)
- `edge_types`: Comma-separated
- `limit` (default: 50)

---

## Search Endpoints

### Semantic Search (Natural Language)
```
POST /api/v1/repos/{repo_id}/search/semantic
```

**Request**:
```json
{
  "query": "Where is the authentication middleware located?",
  "limit": 10,
  "types": ["middleware", "function", "route"],
  "threshold": 0.6
}
```

**Response**:
```json
{
  "results": [
    {
      "node": { ... },
      "score": 0.92,
      "match_type": "semantic",
      "snippet": "Authenticates user via JWT token in Authorization header"
    }
  ],
  "query_embedding": [0.1, -0.3, ...],
  "took_ms": 45
}
```

### Structural Search (AST-based)
```
POST /api/v1/repos/{repo_id}/search/structural
```

**Request**:
```json
{
  "pattern": {
    "type": "function",
    "name": "authenticate*",
    "language": "typescript",
    "has_decorator": "Injectable"
  },
  "limit": 20
}
```

**Response**: Same as semantic search

### Hybrid Search
```
POST /api/v1/repos/{repo_id}/search/hybrid
```

**Request**:
```json
{
  "query": "auth middleware",
  "structural_filters": {
    "type": "middleware",
    "language": "typescript"
  },
  "semantic_weight": 0.7,
  "keyword_weight": 0.3,
  "limit": 15
}
```

---

## Issue Mapping Endpoints

### Analyze Issue
```
POST /api/v1/repos/{repo_id}/issues/{issue_number}/analyze
```

**Request**:
```json
{
  "include_comments": true,
  "max_comments": 10,
  "force_refresh": false
}
```

**Response**: 202 Accepted
```json
{
  "task_id": "uuid",
  "status": "processing",
  "poll_url": "/api/v1/repos/{repo_id}/issues/{issue_number}/mapping"
}
```

### Get Issue Mapping
```
GET /api/v1/repos/{repo_id}/issues/{issue_number}/mapping
```

**Query Parameters**:
- `task_id` (optional): Specific task ID to poll

**Response**:
```json
{
  "issue_number": 1234,
  "status": "completed",
  "mappings": [
    {
      "node": { ... },
      "confidence": 0.92,
      "confidence_tier": "high",
      "evidence": {
        "semantic_match": true,
        "structural_match": true,
        "historical_match": false,
        "propagation_match": true,
        "matched_keywords": ["auth", "login", "jwt", "token"],
        "matched_patterns": ["route: POST /api/auth/login"]
      },
      "suggested_actions": [
        "Modify login route handler in src/routes/auth.ts",
        "Update JWT token generation in src/services/auth.ts",
        "Add rate limiting middleware"
      ]
    }
  ],
  "generated_at": "2026-10-05T10:30:00Z",
  "model_version": "v1.2.0"
}
```

### Submit Feedback on Mapping
```
POST /api/v1/repos/{repo_id}/issues/{issue_number}/feedback
```

**Request**:
```json
{
  "node_id": "uuid",
  "rating": "relevant",
  "comment": "This is exactly the file that needs modification"
}
```

**Rating values**: `relevant`, `partially_relevant`, `irrelevant`

---

## Ingestion Endpoints

### Trigger Ingestion
```
POST /api/v1/repos/{repo_id}/ingest/trigger
```

**Request**:
```json
{
  "mode": "full",
  "branch": "main",
  "force": false
}
```

**Mode values**: `full`, `incremental`

**Response**: 202 Accepted
```json
{
  "task_id": "uuid",
  "status": "queued",
  "poll_url": "/api/v1/repos/{repo_id}/ingest/status"
}
```

### Get Ingestion Status
```
GET /api/v1/repos/{repo_id}/ingest/status
```

**Query Parameters**:
- `task_id` (optional)

**Response**:
```json
{
  "task_id": "uuid",
  "status": "processing",
  "stage": "embedding",
  "progress": {
    "current": 847,
    "total": 1247,
    "percentage": 67.9
  },
  "started_at": "2026-10-05T10:00:00Z",
  "estimated_completion": "2026-10-05T10:05:00Z",
  "stages": {
    "clone": {"status": "completed", "duration_ms": 12000},
    "parse": {"status": "completed", "duration_ms": 45000},
    "extract": {"status": "completed", "duration_ms": 23000},
    "embed": {"status": "processing", "duration_ms": 180000},
    "persist": {"status": "pending", "duration_ms": 0}
  },
  "errors": []
}
```

### GitHub Webhook Receiver
```
POST /api/v1/webhooks/github
```

**Headers**:
```
X-GitHub-Event: push
X-GitHub-Delivery: uuid
X-Hub-Signature-256: sha256=...
```

**Payload**: Standard GitHub push webhook payload

**Response**: 200 OK (processed asynchronously)

---

## Summarization Endpoints

### Get Directory Summary
```
GET /api/v1/repos/{repo_id}/summaries/directory
```

**Query Parameters**:
- `path` (required): Directory path

**Response**:
```json
{
  "path": "src/services",
  "summary": "Contains core business logic services including authentication, payment processing, and user management. Key exports: AuthService, PaymentService, UserService. Dependencies: database models, external APIs (Stripe, SendGrid).",
  "key_files": [
    {"path": "src/services/auth.ts", "type": "service"},
    {"path": "src/services/payment.ts", "type": "service"}
  ],
  "complexity": {"avg": 4.2, "max": 12},
  "generated_at": "2026-10-05T10:30:00Z"
}
```

### Get Module/Class Summary
```
GET /api/v1/repos/{repo_id}/summaries/node/{node_id}
```

### Get Architecture Overview
```
GET /api/v1/repos/{repo_id}/architecture
```

**Query Parameters**:
- `format`: `markdown`, `mermaid`, `json` (default)

**Response** (format=markdown):
```markdown
# Architecture Overview: my-monorepo

## Modules
- **auth**: Authentication & authorization (12 files, 45 functions)
- **payments**: Payment processing with Stripe (8 files, 23 functions)
- **users**: User management (15 files, 67 functions)

## Key Dependencies
```
auth --> users
payments --> users, auth
```

## Entry Points
- `src/main.ts` - Application bootstrap
- `src/routes/*.ts` - API route handlers
```

---

## Chat/QA Endpoints

### Ask Question
```
POST /api/v1/repos/{repo_id}/chat
```

**Request**:
```json
{
  "question": "How does password reset work?",
  "history": [
    {"role": "user", "content": "Where is auth middleware?"},
    {"role": "assistant", "content": "Auth middleware is in src/middleware/auth.ts..."}
  ],
  "stream": true
}
```

**Response** (streaming):
```
data: {"type": "thinking", "content": "Searching for password reset..."}
data: {"type": "citation", "node_id": "uuid", "path": "src/routes/auth.ts"}
data: {"type": "answer", "content": "Password reset is implemented in..."}
data: {"type": "done", "citations": [...]}
```

---

## Onboarding Endpoints

### Get Onboarding Guide
```
GET /api/v1/repos/{repo_id}/onboarding
```

**Response**:
```json
{
  "overview": "Welcome to my-monorepo! This guide will help you...",
  "architecture_summary": "...",
  "key_areas": [
    {"name": "Authentication", "path": "src/auth", "description": "..."},
    {"name": "API Routes", "path": "src/routes", "description": "..."}
  ],
  "starter_issues": [
    {
      "number": 123,
      "title": "Add input validation to login endpoint",
      "labels": ["good-first-issue", "backend"],
      "estimated_hours": 2,
      "affected_files": ["src/routes/auth.ts", "src/validators/auth.ts"]
    }
  ],
  "generated_at": "2026-10-05T10:30:00Z"
}
```

---

## WebSocket Endpoints

### Graph Updates (Real-time)
```
WS /api/v1/repos/{repo_id}/ws/graph
```

**Messages**:
```json
// Client -> Server
{"type": "subscribe", "node_ids": ["uuid1", "uuid2"]}

// Server -> Client
{"type": "node_updated", "node": {...}}
{"type": "edge_added", "edge": {...}}
{"type": "ingestion_progress", "progress": {...}}
```

### Ingestion Progress
```
WS /api/v1/repos/{repo_id}/ws/ingest/{task_id}
```

---

## Health & Monitoring

### Health Check
```
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "version": "1.2.0",
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "vector_db": "healthy",
    "embedding_service": "healthy",
    "github_api": "healthy"
  }
}
```

### Readiness Check
```
GET /ready
```

### Metrics (Prometheus)
```
GET /metrics
```

---

## Versioning
- API version in URL: `/v1/`
- Breaking changes = new version (`/v2/`)
- Deprecation notice: 3 months via `Deprecation` header
- Sunset header: `Sunset: Sat, 01 Jan 2027 00:00:00 GMT`

---

## SDKs
- **TypeScript**: `@codeatlas/sdk` (auto-generated from OpenAPI)
- **Python**: `codeatlas-python` (auto-generated)
- **Go**: `github.com/codeatlas/go-sdk` (auto-generated)

---

## Changelog
| Version | Date | Changes |
|---------|------|---------|
| v1.0 | 2026-10-01 | Initial release |
| v1.1 | 2026-10-15 | Added hybrid search, chat endpoint |
| v1.2 | 2026-11-01 | Added onboarding, architecture endpoints |