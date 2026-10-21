# CodeAtlas - Database Schema & Migrations

## Overview
PostgreSQL 16 + pgvector. All migrations managed via Alembic. UUID primary keys throughout.

---

## Extension Setup

```sql
-- migrations/0001_extensions.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";      -- Fuzzy text search
CREATE EXTENSION IF NOT EXISTS "hstore";
```

---

## Core Tables

### Organizations
```sql
CREATE TABLE organizations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) NOT NULL,
    slug            VARCHAR(255) NOT NULL UNIQUE,
    github_org_id   BIGINT UNIQUE,
    plan            VARCHAR(50) NOT NULL DEFAULT 'free',
    -- free | pro | enterprise
    settings        JSONB NOT NULL DEFAULT '{}',
    quota           JSONB NOT NULL DEFAULT '{
        "max_repos": 5,
        "max_ingestions_per_month": 100,
        "max_api_calls_per_day": 1000
    }',
    stripe_customer_id  VARCHAR(255),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_organizations_slug ON organizations(slug);
CREATE INDEX idx_organizations_github ON organizations(github_org_id);
```

### Users
```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    github_id       BIGINT NOT NULL UNIQUE,
    username        VARCHAR(255) NOT NULL,
    email           VARCHAR(255),
    avatar_url      TEXT,
    name            VARCHAR(255),
    -- Encrypted at rest via pgcrypto
    github_token_encrypted  BYTEA,
    token_expires_at        TIMESTAMPTZ,
    settings        JSONB NOT NULL DEFAULT '{}',
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_github ON users(github_id);
CREATE INDEX idx_users_email ON users(email);
```

### User-Org Membership (RBAC)
```sql
CREATE TABLE org_members (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id      UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role        VARCHAR(50) NOT NULL DEFAULT 'member',
    -- admin | member | viewer
    invited_by  UUID REFERENCES users(id),
    joined_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(org_id, user_id)
);

CREATE INDEX idx_org_members_org ON org_members(org_id);
CREATE INDEX idx_org_members_user ON org_members(user_id);
```

### GitHub App Installations
```sql
CREATE TABLE github_installations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    installation_id     BIGINT NOT NULL UNIQUE,
    org_id              UUID REFERENCES organizations(id),
    github_account_name VARCHAR(255) NOT NULL,
    github_account_type VARCHAR(50) NOT NULL,  -- User | Organization
    permissions         JSONB NOT NULL DEFAULT '{}',
    suspended           BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_installations_org ON github_installations(org_id);
```

---

## Repository Tables

### Repositories
```sql
CREATE TABLE repositories (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    github_id       BIGINT NOT NULL UNIQUE,
    installation_id BIGINT NOT NULL,
    org_id          UUID REFERENCES organizations(id),
    name            VARCHAR(255) NOT NULL,
    full_name       VARCHAR(255) NOT NULL,  -- owner/repo
    owner           VARCHAR(255) NOT NULL,
    default_branch  VARCHAR(255) NOT NULL DEFAULT 'main',
    private         BOOLEAN NOT NULL DEFAULT TRUE,
    language        VARCHAR(50),
    description     TEXT,
    clone_url       TEXT NOT NULL,
    settings        JSONB NOT NULL DEFAULT '{
        "ignored_paths": ["node_modules/**", "dist/**", ".git/**", "*.lock"],
        "analysis_depth": "full",
        "generate_docs": true,
        "embedding_model": "all-MiniLM-L6-v2"
    }',
    status          VARCHAR(50) NOT NULL DEFAULT 'pending',
    -- pending | analyzing | ready | error | disabled
    error_message   TEXT,
    last_analyzed_at    TIMESTAMPTZ,
    last_analyzed_sha   VARCHAR(40),
    node_count      INTEGER NOT NULL DEFAULT 0,
    edge_count      INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_repos_installation ON repositories(installation_id);
CREATE INDEX idx_repos_org ON repositories(org_id);
CREATE INDEX idx_repos_status ON repositories(status);
CREATE INDEX idx_repos_full_name ON repositories(full_name);
```

### Ingestion Tasks
```sql
CREATE TABLE ingestion_tasks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id         UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    triggered_by    UUID REFERENCES users(id),
    mode            VARCHAR(50) NOT NULL DEFAULT 'full',
    -- full | incremental | webhook
    status          VARCHAR(50) NOT NULL DEFAULT 'queued',
    -- queued | running | completed | failed | cancelled
    current_stage   VARCHAR(50),
    -- clone | parse | extract | embed | persist
    progress        INTEGER NOT NULL DEFAULT 0,  -- 0-100
    branch          VARCHAR(255),
    commit_sha      VARCHAR(40),
    files_total     INTEGER DEFAULT 0,
    files_processed INTEGER DEFAULT 0,
    nodes_created   INTEGER DEFAULT 0,
    edges_created   INTEGER DEFAULT 0,
    error           TEXT,
    error_stage     VARCHAR(50),
    stage_timings   JSONB NOT NULL DEFAULT '{}',
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ingestion_repo ON ingestion_tasks(repo_id);
CREATE INDEX idx_ingestion_status ON ingestion_tasks(status);
CREATE INDEX idx_ingestion_created ON ingestion_tasks(created_at DESC);
```

### Ingestion Failures (Dead Letter)
```sql
CREATE TABLE ingestion_failures (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id     UUID NOT NULL REFERENCES ingestion_tasks(id) ON DELETE CASCADE,
    file_path   TEXT NOT NULL,
    error_type  VARCHAR(100) NOT NULL,
    error_msg   TEXT NOT NULL,
    stack_trace TEXT,
    retried     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_failures_task ON ingestion_failures(task_id);
CREATE INDEX idx_failures_unretried ON ingestion_failures(retried) WHERE retried = FALSE;
```

---

## Graph Tables

### Code Nodes
```sql
CREATE TABLE code_nodes (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id     UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    type        VARCHAR(50) NOT NULL,
    -- directory | file | module | class | function | interface | type
    -- | variable | route | component | hook | model | service
    -- | middleware | controller | utility | config | migration | test
    name        VARCHAR(500) NOT NULL,
    path        TEXT NOT NULL,
    language    VARCHAR(50),
    metadata    JSONB NOT NULL DEFAULT '{}',
    summary     TEXT,
    search_vector   TSVECTOR,
    embedding       VECTOR(384),
    -- Content hash for incremental updates
    content_hash    VARCHAR(64),
    -- Git blame info
    last_modified_by    VARCHAR(255),
    last_modified_at    TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Unique constraint: same entity not duplicated
CREATE UNIQUE INDEX idx_nodes_unique 
    ON code_nodes(repo_id, path, name, type);

-- Query indexes
CREATE INDEX idx_nodes_repo ON code_nodes(repo_id);
CREATE INDEX idx_nodes_type ON code_nodes(repo_id, type);
CREATE INDEX idx_nodes_path ON code_nodes(repo_id, path);
CREATE INDEX idx_nodes_language ON code_nodes(repo_id, language);

-- Full-text search index
CREATE INDEX idx_nodes_search ON code_nodes USING GIN(search_vector);

-- Vector similarity index (HNSW for better recall)
CREATE INDEX idx_nodes_embedding ON code_nodes 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Trigram index for fuzzy path search
CREATE INDEX idx_nodes_path_trgm ON code_nodes USING GIN (path gin_trgm_ops);
CREATE INDEX idx_nodes_name_trgm ON code_nodes USING GIN (name gin_trgm_ops);

-- Auto-update search_vector on insert/update
CREATE OR REPLACE FUNCTION nodes_search_vector_update() RETURNS trigger AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', COALESCE(NEW.name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.path, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.summary, '')), 'C') ||
        setweight(to_tsvector('english', 
            COALESCE(NEW.metadata->>'docstring', '')), 'D');
    RETURN NEW;
END
$$ LANGUAGE plpgsql;

CREATE TRIGGER nodes_search_update 
    BEFORE INSERT OR UPDATE ON code_nodes
    FOR EACH ROW EXECUTE FUNCTION nodes_search_vector_update();
```

### Code Edges
```sql
CREATE TABLE code_edges (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id     UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    source_id   UUID NOT NULL REFERENCES code_nodes(id) ON DELETE CASCADE,
    target_id   UUID NOT NULL REFERENCES code_nodes(id) ON DELETE CASCADE,
    type        VARCHAR(50) NOT NULL,
    -- contains | exports | imports | re_exports | extends | implements
    -- | calls | instantiates | routes_to | renders | uses_hook
    -- | has_model | middleware_for | reads | writes | emits | listens
    weight      FLOAT NOT NULL DEFAULT 1.0,
    metadata    JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_edges_unique 
    ON code_edges(repo_id, source_id, target_id, type);
CREATE INDEX idx_edges_repo ON code_edges(repo_id);
CREATE INDEX idx_edges_source ON code_edges(source_id);
CREATE INDEX idx_edges_target ON code_edges(target_id);
CREATE INDEX idx_edges_type ON code_edges(repo_id, type);
```

---

## Issue Mapping Tables

### Issues (Cached)
```sql
CREATE TABLE issues (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id         UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    github_issue_id BIGINT NOT NULL,
    number          INTEGER NOT NULL,
    title           TEXT NOT NULL,
    body            TEXT,
    state           VARCHAR(20) NOT NULL DEFAULT 'open',
    -- open | closed
    labels          JSONB NOT NULL DEFAULT '[]',
    assignees       JSONB NOT NULL DEFAULT '[]',
    author          VARCHAR(255),
    url             TEXT,
    embedding       VECTOR(384),
    closed_at       TIMESTAMPTZ,
    fetched_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(repo_id, number)
);

CREATE INDEX idx_issues_repo ON issues(repo_id);
CREATE INDEX idx_issues_state ON issues(repo_id, state);
CREATE INDEX idx_issues_embedding ON issues 
    USING hnsw (embedding vector_cosine_ops);
```

### Issue Mappings
```sql
CREATE TABLE issue_mappings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issue_id        UUID NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    repo_id         UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    status          VARCHAR(50) NOT NULL DEFAULT 'pending',
    -- pending | processing | completed | failed
    mappings        JSONB NOT NULL DEFAULT '[]',
    -- Array of {node_id, confidence, tier, evidence, actions}
    model_version   VARCHAR(50) NOT NULL DEFAULT 'v1.0.0',
    generation_ms   INTEGER,
    validated       BOOLEAN,
    generated_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_mappings_issue ON issue_mappings(issue_id);
CREATE INDEX idx_mappings_repo ON issue_mappings(repo_id);
CREATE INDEX idx_mappings_status ON issue_mappings(status);
```

### Mapping Feedback (Training Data)
```sql
CREATE TABLE mapping_feedback (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mapping_id  UUID NOT NULL REFERENCES issue_mappings(id) ON DELETE CASCADE,
    node_id     UUID NOT NULL REFERENCES code_nodes(id) ON DELETE CASCADE,
    user_id     UUID NOT NULL REFERENCES users(id),
    rating      VARCHAR(30) NOT NULL,
    -- relevant | partially_relevant | irrelevant
    comment     TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_feedback_mapping ON mapping_feedback(mapping_id);
CREATE INDEX idx_feedback_rating ON mapping_feedback(rating);
```

---

## Summarization Tables

### Node Summaries
```sql
CREATE TABLE node_summaries (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_id         UUID NOT NULL REFERENCES code_nodes(id) ON DELETE CASCADE,
    summary_type    VARCHAR(50) NOT NULL,
    -- directory | module | class | function | architecture
    content         TEXT NOT NULL,
    model_used      VARCHAR(100) NOT NULL,
    input_tokens    INTEGER,
    output_tokens   INTEGER,
    source_hash     VARCHAR(64),  -- To detect staleness
    generated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(node_id, summary_type)
);

CREATE INDEX idx_summaries_node ON node_summaries(node_id);
```

---

## Chat Tables

### Chat Sessions
```sql
CREATE TABLE chat_sessions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id     UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    user_id     UUID NOT NULL REFERENCES users(id),
    title       VARCHAR(500),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_chat_sessions_repo ON chat_sessions(repo_id);
CREATE INDEX idx_chat_sessions_user ON chat_sessions(user_id);
```

### Chat Messages
```sql
CREATE TABLE chat_messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role            VARCHAR(20) NOT NULL,
    -- user | assistant | system
    content         TEXT NOT NULL,
    citations       JSONB NOT NULL DEFAULT '[]',
    -- Array of {node_id, path, snippet, relevance}
    tokens_used     INTEGER,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_chat_messages_session ON chat_messages(session_id, created_at);
```

---

## Audit & Logging

### Audit Log
```sql
CREATE TABLE audit_logs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID REFERENCES users(id),
    org_id      UUID REFERENCES organizations(id),
    action      VARCHAR(100) NOT NULL,
    -- repo.create, repo.delete, ingest.trigger, settings.update, etc.
    resource_type   VARCHAR(50) NOT NULL,
    resource_id     UUID,
    details     JSONB NOT NULL DEFAULT '{}',
    ip_address  INET,
    user_agent  TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_user ON audit_logs(user_id, created_at DESC);
CREATE INDEX idx_audit_org ON audit_logs(org_id, created_at DESC);
CREATE INDEX idx_audit_action ON audit_logs(action, created_at DESC);
```

---

## Row-Level Security (Multi-tenant)

```sql
-- Enable RLS on all tenant-scoped tables
ALTER TABLE repositories ENABLE ROW LEVEL SECURITY;
ALTER TABLE code_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE code_edges ENABLE ROW LEVEL SECURITY;
ALTER TABLE issues ENABLE ROW LEVEL SECURITY;
ALTER TABLE issue_mappings ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access repos in their org
CREATE POLICY repo_access_policy ON repositories
    FOR ALL
    USING (
        org_id IN (
            SELECT org_id FROM org_members 
            WHERE user_id = current_setting('app.current_user_id')::UUID
        )
    );

-- Policy: Node/edge access follows repo access
CREATE POLICY node_access_policy ON code_nodes
    FOR ALL
    USING (
        repo_id IN (
            SELECT id FROM repositories 
            WHERE org_id IN (
                SELECT org_id FROM org_members 
                WHERE user_id = current_setting('app.current_user_id')::UUID
            )
        )
    );

-- Same pattern for code_edges, issues, etc.
```

---

## Materialized Views

### Repository Stats
```sql
CREATE MATERIALIZED VIEW repo_node_stats AS
SELECT 
    r.id AS repo_id,
    COUNT(DISTINCT n.id) AS total_nodes,
    COUNT(DISTINCT e.id) AS total_edges,
    COUNT(DISTINCT n.id) FILTER (WHERE n.type = 'file') AS file_count,
    COUNT(DISTINCT n.id) FILTER (WHERE n.type = 'function') AS function_count,
    COUNT(DISTINCT n.id) FILTER (WHERE n.type = 'class') AS class_count,
    COUNT(DISTINCT n.id) FILTER (WHERE n.type = 'route') AS route_count,
    COUNT(DISTINCT n.id) FILTER (WHERE n.type = 'component') AS component_count,
    COUNT(DISTINCT n.id) FILTER (WHERE n.type = 'model') AS model_count,
    jsonb_object_agg(
        n.language, 
        COUNT(*) 
    ) FILTER (WHERE n.language IS NOT NULL) AS language_distribution,
    AVG((n.metadata->>'cyclomatic_complexity')::FLOAT) AS avg_complexity
FROM repositories r
LEFT JOIN code_nodes n ON n.repo_id = r.id
LEFT JOIN code_edges e ON e.repo_id = r.id
GROUP BY r.id;

CREATE UNIQUE INDEX idx_repo_stats ON repo_node_stats(repo_id);

-- Refresh after ingestion
REFRESH MATERIALIZED VIEW CONCURRENTLY repo_node_stats;
```

### Graph Centrality (for ranking)
```sql
CREATE MATERIALIZED VIEW node_centrality AS
SELECT 
    source_id AS node_id,
    COUNT(*) AS out_degree,
    SUM(weight) AS weighted_out_degree
FROM code_edges
GROUP BY source_id;

CREATE UNIQUE INDEX idx_centrality ON node_centrality(node_id);
```

---

## Migration Strategy

### Alembic Configuration
```ini
# alembic.ini
[alembic]
script_location = migrations
sqlalchemy.url = postgresql+asyncpg://user:pass@localhost:5432/codeatlas

[loggers]
keys = root,sqlalchemy,alembic
```

### Naming Convention
```
migrations/
├── 0001_extensions.sql
├── 0002_core_tables.sql
├── 0003_graph_tables.sql
├── 0004_issue_tables.sql
├── 0005_chat_tables.sql
├── 0006_rls_policies.sql
├── 0007_materialized_views.sql
└── versions/
    ├── a1b2c3d4_add_repo_settings.py
    └── e5f6g7h8_add_chat_tables.py
```

### Rollback Strategy
- Every migration has `downgrade()` function
- Test rollback in CI before merge
- Never modify applied migrations — create new ones

---

## Backup & Recovery

| Strategy | Frequency | Retention | Method |
|----------|-----------|-----------|--------|
| Full backup | Daily | 30 days | pg_dump + S3 |
| WAL archiving | Continuous | 7 days | pgBackRest |
| Point-in-time recovery | On-demand | 30 days | WAL + base backup |
| Schema-only | Weekly | 90 days | pg_dump --schema-only |

---

## Performance Targets

| Operation | Target | Index Used |
|-----------|--------|------------|
| Node lookup by ID | < 5ms | Primary key |
| Graph fetch (500 nodes) | < 100ms | idx_nodes_repo |
| Semantic search (top-10) | < 50ms | HNSW index |
| Full-text search | < 30ms | GIN index |
| Issue mapping lookup | < 50ms | idx_mappings_issue |
| Stats aggregation | < 200ms | Materialized view |
| Incremental upsert (100 files) | < 2s | Unique indexes |