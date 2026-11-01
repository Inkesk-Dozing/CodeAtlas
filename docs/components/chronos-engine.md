# Chronos Engine Component Specification

## Purpose
The Chronos Engine provides temporal codebase intelligence, tracking how architectural topology, AST symbols, author ownership, and technical debt evolve over time. It transforms CodeAtlas from a static HEAD visualizer into an interactive temporal simulator capable of architectural archaeology and what-if refactor blast radius prediction.

## System Dependencies
- **Git Binary / Git CLI Hook**: Subprocess streaming (`git log --stat --follow`, git blame, and tag histories).
- **Tree-Sitter AST Parsers**: Incremental syntax tree diffing between historical commit checkpoints.
- **PostgreSQL + pgvector**: Vector and relational persistence of historical commits, pull requests, and author churn telemetry.
- **FastAPI (`routers/chronos.py`)**: API endpoints for timeline progression, commit diffs, mutation simulations, and node archaeology.
- **Zustand (`chronosStore.ts`) & React Flow (Frontend)**: Real-time scrubbing, timeline playback ribbon, and dynamic blast radius graph overlays.

## Big-O Algorithmic Complexity

| Operation | Time Complexity | Space Complexity | Description |
|---|---|---|---|
| Commit Timeline Synthesis | $O(C \cdot \log C)$ | $O(C)$ | Ingesting and sorting $C$ commit logs with churn velocity and milestone flags |
| AST Checkpoint Diffing | $O(N_1 + N_2)$ | $O(N_1 + N_2)$ | Computing node/edge topological deltas between commit $C_1$ and $C_2$ |
| What-If Mutation Blast Radius | $O(V_{reach} + E_{reach})$ | $O(V_{reach})$ | Directed graph transitive closure from target node $u$ up to maximum depth $D$ |
| Architectural Archaeology Retrieval | $O(\log N_{nodes} + P)$ | $O(P)$ | Relational index lookup linking node $u$ to original commit, PR metadata ($P$), and blame history |

## Architectural Modules & Execution Flows

```
[ Git History / Commits ]
            │
            ▼
┌───────────────────────────┐      ┌───────────────────────────┐
│   Chronos Timeline Engine │ ───▶ │  Interactive Scrubber Bar │
│ (Commit Velocity & Churn) │      │  (Past ➔ Milestones ➔ NOW)│
└───────────────────────────┘      └───────────────────────────┘
            │                                    │
            ▼                                    ▼
┌───────────────────────────┐      ┌───────────────────────────┐
│  AST Mutation Simulator   │ ───▶ │ What-If Blast Radius Modal│
│ (Downstream Caller Graph) │      │ (Downstream Breaking APIs)│
└───────────────────────────┘      └───────────────────────────┘
            │                                    │
            ▼                                    ▼
┌───────────────────────────┐      ┌───────────────────────────┐
│  Architectural Archaeology│ ───▶ │ Origin & PR Decision View │
│ (Blame, PRs, & Debt Trend)│      │ ("Why did this change?")  │
└───────────────────────────┘      └───────────────────────────┘
```

### 1. Interactive Timeline Scrubber
- Renders an interactive ribbon of commits across the bottom of the canvas with author identity, relative timestamps, release milestones (e.g., `v0.8.0 Release`, `PR #104: Database Decoupling`), and churn metrics (`+added / -deleted`).
- Supports automated playback, stepping backward/forward, and instant fast-forward to latest HEAD.

### 2. What-If AST Mutation Simulator
- Accepts a target symbol/node and a proposed refactoring description.
- Evaluates outgoing and incoming dependency edges to calculate downstream blast radius count, affected API endpoints with breaking risk assessments, recommended peer reviewers, and remediation steps.
- Automatically highlights the entire blast radius subgraph on the canvas in amber/crimson.

### 3. Architectural Archaeology
- Retrieves deep historical provenance for any selected node: original author, commit hash, timestamp, linked pull requests, historical hotspot trends, and decision context explaining why the architectural boundary was created.
