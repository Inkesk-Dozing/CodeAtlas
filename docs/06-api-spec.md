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

## Chronos (Software Time Machine & Archaeology)

### Get Commit Timeline
```
GET /api/v1/repos/{repo_id}/chronos/timeline?limit=20
```

**Response**:
```json
{
  "commits": [
    {
      "hash": "a8f4c2e819b930d41029c",
      "short_hash": "a8f4c2e",
      "author": "Kush Bhardwaj",
      "author_avatar": "https://avatars.githubusercontent.com/u/12345",
      "date": "2026-10-25T14:30:00Z",
      "message": "refactor: decouple database ORM models and isolate schema layer",
      "tag": "v0.9.0",
      "churn_added": 340,
      "churn_deleted": 210,
      "hotspot_score": 0.42,
      "architectural_milestone": "PR #104: Database Decoupling"
    }
  ],
  "total": 54,
  "current_head": "HEAD"
}
```

### Get Architectural Diff Between Commits
```
GET /api/v1/repos/{repo_id}/chronos/diff?from_commit=7e2a91f&to_commit=HEAD
```

**Response**:
```json
{
  "from_commit": "7e2a91f",
  "to_commit": "HEAD",
  "added_nodes": ["apps/api/routers/chronos.py", "apps/api/routers/omniquery.py"],
  "removed_nodes": [],
  "modified_nodes": ["apps/api/main.py", "packages/shared/src/types.ts"],
  "dependency_changes": [
    {
      "source": "apps/api/main.py",
      "target": "apps/api/routers/chronos.py",
      "action": "added"
    }
  ],
  "summary": "Mounted Chronos and OmniQuery routers into FastAPI application."
}
```

### Simulate What-If AST Mutation
```
POST /api/v1/repos/{repo_id}/chronos/simulate
```

**Request**:
```json
{
  "target_node_id": "apps/api/auth/session.py",
  "proposed_change": "Deprecate legacy session tokens and enforce asymmetric RS256 JWT validation."
}
```

**Response**:
```json
{
  "target_node_id": "apps/api/auth/session.py",
  "target_path": "apps/api/auth/session.py",
  "proposed_change": "Deprecate legacy session tokens and enforce asymmetric RS256 JWT validation.",
  "risk_level": "high",
  "blast_radius_count": 8,
  "downstream_nodes": [
    {
      "id": "apps/api/routers/graph.py",
      "name": "get_graph",
      "path": "apps/api/routers/graph.py",
      "depth": 1,
      "relation": "imports"
    }
  ],
  "impacted_endpoints": ["GET /api/v1/graph", "POST /api/v1/search"],
  "recommended_reviewers": ["kush05bhardwaj", "inkeskdozing"],
  "remediation_suggestions": [
    "Run integration test suite against auth routers.",
    "Verify backward compatibility for unexpired bearer tokens."
  ]
}
```

### Get Architectural Archaeology
```
GET /api/v1/repos/{repo_id}/chronos/archaeology/{node_id}
```

**Response**:
```json
{
  "node_id": "apps/api/auth/session.py",
  "node_path": "apps/api/auth/session.py",
  "created_in_commit": "7e2a91f",
  "created_at": "2026-09-12T10:15:00Z",
  "original_author": "Kush Bhardwaj",
  "decision_context": "PR #89 introduced asymmetric RS256 JWT validation to support distributed micro-service verification without central DB lookups.",
  "linked_prs": [
    { "number": 89, "title": "feat(auth): migrate session tokens to asymmetric RS256 JWTs" }
  ],
  "evolution_summary": "Created in initial auth rewrite; modified 14 times with 3 hotfixes.",
  "hotspot_trend": "stable"
}
```

---

## OmniQuery (Database Time Machine & Schema Lens)

### List Schema Models
```
GET /api/v1/repos/{repo_id}/omniquery/models
```

**Response**:
```json
{
  "models": [
    {
      "name": "User",
      "table_name": "users",
      "file_path": "apps/api/models/user.py",
      "fields": [
        { "name": "id", "type": "UUID", "is_primary": true, "is_nullable": false },
        { "name": "email", "type": "String", "is_primary": false, "is_nullable": false },
        { "name": "status", "type": "String", "is_primary": false, "is_nullable": true }
      ],
      "connected_endpoints": [
        "GET /api/v1/users",
        "POST /api/v1/users",
        "DELETE /api/v1/users/{id}"
      ]
    }
  ]
}
```

### Explain & Preview Natural Language Query
```
POST /api/v1/repos/{repo_id}/omniquery/explain
```

**Request**:
```json
{
  "prompt": "Find all inactive users from last year and set their status to archived",
  "model_name": "User"
}
```

**Response**:
```json
{
  "intent": "Find all inactive users from last year and set their status to archived",
  "operation_type": "UPDATE",
  "translated_sql": "UPDATE users SET status = 'archived' WHERE last_login < NOW() - INTERVAL '1 year' AND status = 'inactive';",
  "explanation": "Scans users table for records where last_login exceeds 365 days and updates status to archived.",
  "risk_level": "medium",
  "estimated_affected_rows": 42,
  "safety_check_passed": true,
  "code_dependencies": [
    {
      "endpoint": "GET /api/v1/users",
      "method": "GET",
      "path": "apps/api/routers/users.py",
      "impact": "compatible"
    }
  ]
}
```

### Simulate Query in Sandbox
```
POST /api/v1/repos/{repo_id}/omniquery/simulate
```

**Request**:
```json
{
  "sql": "UPDATE users SET status = 'archived' WHERE last_login < NOW() - INTERVAL '1 year';",
  "model_name": "User"
}
```

**Response**:
```json
{
  "success": true,
  "preview_rows": [
    { "id": "1111-2222", "email": "inactive_test@example.com", "status": "archived" }
  ],
  "rollback_plan": "UPDATE users SET status = 'inactive' WHERE id IN ('1111-2222');",
  "execution_time_ms": 14.2,
  "warnings": []
}
```

### Approve & Execute Transaction
```
POST /api/v1/repos/{repo_id}/omniquery/execute
```

**Request**:
```json
{
  "sql": "UPDATE users SET status = 'archived' WHERE last_login < NOW() - INTERVAL '1 year';",
  "model_name": "User",
  "rollback_plan": "UPDATE users SET status = 'inactive' WHERE id IN ('1111-2222');"
}
```

**Response**:
```json
{
  "id": "exec_8f91a0c",
  "timestamp": "2026-10-27T16:45:00Z",
  "status": "executed",
  "affected_rows": 1,
  "message": "Transaction committed successfully with rollback point registered."
}
```

---

## Developer Telemetry (WakaTime-Compatible)

### Ingest Active Editor Heartbeat
```
POST /api/v1/telemetry/heartbeat
```
Maps active developer editor coding time to an AST node without transmitting code text.

**Request**:
```json
{
  "entity": "apps/api/routers/auth.py",
  "type": "file",
  "time": 1730225400.0,
  "project": "CodeAtlas",
  "branch": "main",
  "language": "python",
  "is_write": true,
  "cursorpos": { "line": 42, "column": 10 }
}
```

**Response**:
```json
{
  "status": "recorded",
  "node_id": "b7e2898a-1a87-4b7f-8e42-1e9a3cf34b92",
  "active_minutes_total": 42.5,
  "cognitive_friction_index": 0.38
}
```

### Get Telemetry & Friction Index
```
GET /api/v1/repos/{repo_id}/telemetry/stats?window=7d
```

**Response**:
```json
{
  "repo_id": "uuid",
  "total_focus_hours": 38.4,
  "hotspots": [
    {
      "node_id": "uuid",
      "file_path": "apps/api/routers/graph.py",
      "active_minutes": 185.0,
      "loc_churn": 42,
      "cognitive_friction_index": 0.84,
      "friction_tier": "critical"
    }
  ]
}
```

---

## GitReverse & AI Context Packager

### Export AGENTS.md Agent Guidelines
```
GET /api/v1/repos/{repo_id}/prompts/agents-md
```

**Response**:
```markdown
# Autonomous Agent Context: CodeAtlas Monorepo
## Architectural Boundaries
- apps/web MUST NOT import apps/api directly.
- packages/shared contains domain contracts only.
...
```

### Export .cursorrules IDE Rules
```
GET /api/v1/repos/{repo_id}/prompts/cursorrules
```

### Export llms.txt Documentation Sitemap
```
GET /api/v1/repos/{repo_id}/prompts/llms-txt
```

### Package Targeted Subgraph Prompt
```
POST /api/v1/repos/{repo_id}/prompts/subgraph
```

**Request**:
```json
{
  "node_id": "uuid",
  "depth": 1,
  "token_budget": 8192
}
```

**Response**:
```json
{
  "prompt_token_count": 3420,
  "system_prompt": "You are refactoring a subcomponent in CodeAtlas...",
  "interface_contracts": "interface GraphNodeProps { ... }",
  "caller_context": ["apps/web/src/components/graph/Canvas.tsx"]
}
```

---

## CodeAtlas Flight Simulator

### List Available Missions
```
GET /api/v1/flight-simulator/missions
```

**Response**:
```json
[
  {
    "id": "mission_git_01",
    "title": "Branching & First Pull Request",
    "track": "beginner",
    "difficulty": "introductory",
    "reward_badge_tier": "Git Flight Certified"
  },
  {
    "id": "mission_git_02",
    "title": "Upstream Merge Conflict Resolution",
    "track": "intermediate",
    "difficulty": "moderate",
    "reward_badge_tier": "Conflict Master"
  }
]
```

### Execute Virtual Git Command in Session
```
POST /api/v1/flight-simulator/sessions/{session_id}/command
```

**Request**:
```json
{
  "command": "git checkout -b feat/add-readme-badge"
}
```

**Response**:
```json
{
  "stdout": "Switched to a new branch 'feat/add-readme-badge'",
  "current_branch": "feat/add-readme-badge",
  "dag_state": { "head": "commit_1a", "branches": ["main", "feat/add-readme-badge"] }
}
```

### Submit Simulated Pull Request for Bot Review
```
POST /api/v1/flight-simulator/sessions/{session_id}/pr-review
```

**Response**:
```json
{
  "pr_number": 42,
  "status": "changes_requested",
  "ci_checks": {
    "linter": "passed",
    "typecheck": "passed",
    "unit_tests": "failed"
  },
  "bot_comments": [
    {
      "file": "README.md",
      "line": 12,
      "message": "Great work on the badge syntax! Remember to add alt text for accessibility."
    }
  ]
}
```

---

## Verifiable Badges & Credential Network

### Get Dynamic Contributor SVG Badge
```
GET /api/v1/badges/contributor/{username}.svg?theme=dark&style=hexagon
```
Returns a pixel-perfect, cache-optimized dynamic SVG badge for GitHub READMEs.

### Get Collectible Badge Board SVG
```
GET /api/v1/badges/board/{username}.svg
```
Returns an aggregated Holopin-style hexagonal badge board SVG for developer profile READMEs.

### Verify Digital Credential (Ed25519)
```
GET /api/v1/badges/verify/{cert_id}
```

**Response**:
```json
{
  "cert_id": "ca_cert_8f91a0c",
  "recipient": "kush05bhardwaj",
  "tier": "Git Flight Certified",
  "repository": "CodeAtlas",
  "issued_at": 1730225400,
  "signature_valid": true,
  "algorithm": "Ed25519",
  "signer_public_key": "ed25519_pk_9a102b...",
  "proof_replay_url": "https://codeatlas.dev/repos/codeatlas/graph?replay=cert_8f91a0c"
}
```

---

## GitHub Achievements Tracker & AI Context Endpoints

### Get Canonical Achievements Catalog
```
GET /api/v1/achievements/catalog
```
Returns all 9 supported GitHub achievements, tiers (Base, Bronze, Silver, Gold), unlock thresholds, and practical optimization tips (mirroring `gitbadgecheck.vercel.app`).

**Response**:
```json
{
  "catalog_version": "2026.1",
  "provider": "CodeAtlas GitBadgeCheck Engine",
  "total_available": 9,
  "achievements": {
    "pull-shark": {
      "id": "pull-shark",
      "name": "Pull Shark",
      "category": "active",
      "description": "Merged pull requests into repositories.",
      "icon": "🦈",
      "metric_name": "merged_prs",
      "tiers": [
        {"tier": "Base", "threshold": 2, "multiplier": "x1"},
        {"tier": "Bronze", "threshold": 16, "multiplier": "x2"},
        {"tier": "Silver", "threshold": 128, "multiplier": "x3"},
        {"tier": "Gold", "threshold": 1024, "multiplier": "x4"}
      ]
    }
  }
}
```

### Track User GitHub Achievements & Live Progress
```
GET /api/v1/achievements/user/{username}
```
Inspects a public profile's achievements, current unlocked tiers, progress percentages toward the next tier, remaining contributions needed, and estimated developer XP.

**Query Parameters** (Optional overrides):
- `merged_prs`: Override merged PR count
- `max_stars`: Override top repository stars
- `coauthored_commits`: Override co-authored commits
- `accepted_answers`: Override accepted discussion answers

**Response**:
```json
{
  "username": "octocat",
  "total_unlocked": 7,
  "total_achievements": 9,
  "completion_rate": 77.8,
  "active_badges": 6,
  "legacy_badges": 1,
  "highest_rank_badge": "Pull Shark (Silver)",
  "estimated_xp": 2650,
  "achievements": [
    {
      "id": "pull-shark",
      "name": "Pull Shark",
      "category": "active",
      "icon": "🦈",
      "unlocked": true,
      "current_tier": "Silver",
      "current_multiplier": "x3",
      "current_count": 130,
      "next_tier": "Gold",
      "next_threshold": 1024,
      "remaining_for_next_tier": 894,
      "progress_percentage": 0.2,
      "tips": "Submit and merge PRs across public repositories. Squash or rebase merges count."
    }
  ]
}
```

### AI-Optimized Achievement Context for External Agents
```
GET /api/v1/achievements/ai-context/{username}
```
Generates token-budgeted prompt contexts, actionable next steps, and markdown cards ready to inject directly into LLM / AI assistant prompts.

**Query Parameters**:
- `target_badge` (optional): Badge ID to prioritize (e.g. `pull-shark`)

**Response**:
```json
{
  "prompt_context": "<github_achievements user="octocat" unlocked="7/9" xp="2650">\n  <status highest_rank="Pull Shark (Silver)" completion_rate="77.8%">\n  <unlocked_badges>\n    <badge id="pull-shark" name="Pull Shark" tier="Silver" count="130" progress="0.2%" />\n  </unlocked_badges>\n  <recommended_next_actions>\n    <action priority="1">Advance Pair Extraordinaire to Silver: Needs 12 more co-authored commits.</action>\n  </recommended_next_actions>\n</github_achievements>",
  "markdown_card": "### 🏆 GitHub Achievement Profile: @octocat\n- **Completion**: 7/9 badges (77.8%) | **XP**: 2650\n...",
  "raw_stats": {
    "username": "octocat",
    "total_unlocked": 7,
    "total_achievements": 9,
    "estimated_xp": 2650,
    "completion_rate": 77.8
  },
  "actionable_next_steps": [
    "Advance Pair Extraordinaire to Silver: Needs 12 more co-authored commits.",
    "Unlock Galaxy Brain: Needs 2 accepted discussion answers."
  ]
}
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