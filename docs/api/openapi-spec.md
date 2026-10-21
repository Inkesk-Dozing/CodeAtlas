# OpenAPI Specification (v1)

## Base URL
`https://api.codeatlas.dev/api/v1`

## Endpoints Summary

### Authentication

#### `POST /auth/login/github`
Authenticates a user via GitHub OAuth authorization code.
- **Request Body**: `{ "code": "string" }`
- **Response**: `200 OK`
  ```json
  {
    "access_token": "jwt_token_string",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
      "id": "uuid",
      "username": "octocat",
      "email": "octocat@github.com"
    }
  }
  ```

#### `POST /auth/refresh`
Rotates access token using HTTP-Only refresh cookie.
- **Response**: `200 OK` `{ "access_token": "new_jwt_string" }`

---

### Repository Management

#### `GET /repos`
Lists repositories accessible to the current user's organization.
- **Query Params**: `page=1`, `limit=20`
- **Response**: `200 OK` Array of `Repository` entities.

#### `POST /repos/{repo_id}/ingest`
Triggers an ingestion job for a repository.
- **Response**: `202 Accepted` `{ "task_id": "uuid", "status": "PENDING" }`

---

### Architecture Graph API

#### `GET /graph/neighborhood`
Retrieves a subgraph centered around a root node or directory cluster.
- **Query Params**:
  - `repo_id` (required): UUID of repository
  - `root_id` (optional): UUID of target node
  - `depth` (optional): Traversal depth (default: 2, max: 5)
- **Response**: `200 OK`
  ```json
  {
    "nodes": [
      {
        "id": "node_uuid",
        "name": "ValidationCore",
        "node_type": "class",
        "file_path": "apps/api/services/validation.py",
        "complexity": 14
      }
    ],
    "edges": [
      {
        "source": "node_uuid_1",
        "target": "node_uuid_2",
        "relation_type": "IMPORTS"
      }
    ]
  }
  ```

---

### Issue Mapping API

#### `POST /issues/map`
Analyzes a GitHub issue and returns mapped codebase components with confidence scores.
- **Request Body**:
  ```json
  {
    "repo_id": "uuid",
    "issue_number": 42,
    "title": "JWT refresh token failure on rotation",
    "body": "When token expires, refresh endpoint returns 500 server error."
  }
  ```
- **Response**: `200 OK`
  ```json
  {
    "issue_number": 42,
    "mapped_nodes": [
      {
        "node_id": "uuid",
        "file_path": "apps/api/routers/auth.py",
        "confidence": 0.92,
        "evidence": "Matched route path '/auth/refresh' and exception logs"
      }
    ]
  }
  ```
