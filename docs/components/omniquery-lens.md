# OmniQuery Database Lens Component Specification

## Purpose
OmniQuery serves as CodeAtlas's operational data intelligence engine and Database Time Machine. It bridges static ORM/database code models with conversational database interactions, verifying the blast radius of migrations across API routes and executing safe transactional queries with automated rollback plans.

## System Dependencies
- **CodeAtlas AST Parsers**: Extraction of Prisma (`schema.prisma`), SQLAlchemy, and Django ORM models into first-class graph nodes.
- **FastAPI (`routers/omniquery.py`)**: Endpoints for schema model cataloging, natural language prompt explanation, sandbox dry-run execution, and transaction rollbacks.
- **Zustand (`omniQueryStore.ts`)**: Client-side state machine managing the strict multi-stage safety pipeline.
- **Relational Connectors / Sandboxes**: Isolated SQLite/PostgreSQL transactional test runner for dry-run simulation and row previewing.

## Big-O Algorithmic Complexity

| Operation | Time Complexity | Space Complexity | Description |
|---|---|---|---|
| Schema Model AST Extraction | $O(F_{models} \cdot S_{lines})$ | $O(M \cdot \bar{F})$ | Parsing $F$ schema files for $M$ entities with average $\bar{F}$ fields |
| NL-to-SQL Translation & Safety Check | $O(L_{prompt} + M_{schema})$ | $O(T_{sql})$ | Semantic analysis and AST constraint validation against schema definitions |
| Code Dependency Impact Traversal | $O(V_{endpoints} + E_{calls})$ | $O(V_{impacted})$ | Cross-referencing modified tables/columns against API route call-sites |
| Sandboxed Dry-Run Simulation | $O(R_{preview})$ | $O(R_{preview})$ | Sandboxed transaction execution fetching up to $R$ preview records |

## Architectural Multi-Stage Safety Pipeline

To prevent accidental production data loss or breaking API contract changes, OmniQuery enforces a strict sequential gate:

```
[ User Plain-English Prompt ]
              │
              ▼
    ┌───────────────────┐
    │ 1. Understand     │ ──▶ Natural-language intent parsed into AST SQL statement
    └───────────────────┘
              │
              ▼
    ┌───────────────────┐
    │ 2. Preview        │ ──▶ SQL syntax inspection, risk classification, &
    └───────────────────┘     Cross-Engine CodeAtlas Breaking Route Analysis
              │
              ▼
    ┌───────────────────┐
    │ 3. Simulate       │ ──▶ Sandboxed execution, preview table rows, &
    └───────────────────┘     automated rollback script generation
              │
              ▼
    ┌───────────────────┐
    │ 4. Approve & Run  │ ──▶ Transactional execution with safety verification
    └───────────────────┘
              │
              ▼
    ┌───────────────────┐
    │ 5. Rollback Gate  │ ──▶ One-click emergency restoration to prior state
    └───────────────────┘
```

## Key Capabilities

### 1. Database Model Discovery & Schema Lens
- Extracts entity models, table names, field types, primary keys, and nullability flags from source code.
- Directly accessible from the graph canvas whenever a database model node is clicked.

### 2. Cross-Engine Code Dependency Validation
- When a developer proposes modifying a table (e.g., changing a column type or renaming a field), OmniQuery consults CodeAtlas's dependency graph.
- Surfaces every API endpoint (e.g., `GET /api/v1/users`, `POST /api/v1/billing`) and component that queries the model, flagging breaking vs. compatible changes before execution.

### 3. Safe Dry-Run Simulation & Rollback Automation
- Runs in an isolated test transaction to preview affected rows and compute exact execution time in milliseconds.
- Generates an inverse SQL rollback script (e.g., `UPDATE users SET plan_state = NULL WHERE plan_state = 'free';`) stored in audit history.
