# OpenSourceMapper & Contributor Blueprint Component Specification

## Purpose
The OpenSourceMapper component connects open-source issue discovery with deep codebase topological intelligence. It automatically triages GitHub issues by AST subgraph isolation, matching new contributors with mathematically safe "Good First Issues" where changes have low in-degree and minimal downstream blast radius. It synthesizes interactive, 3-step contributor execution blueprints and prerequisite mental model checklists to empower developers to make high-impact contributions quickly.

## System Dependencies
- **GitHub Issues Fetcher**: Periodic GraphQL ingestion of issues, triage labels, and maintainer comment discussions.
- **Tree-Sitter AST & Graph Engine**: Extraction of node in-degree, out-degree, cyclomatic complexity, and transitive caller reach.
- **FastAPI (`routers/issues.py`)**: Endpoints for contributor roadmaps, prerequisite concept generation, and beginner-friendly issue ranking.
- **Zustand (`issueStore.ts`) & React UI (`apps/web`)**: Contributor planner drawer, interactive checklist widget, and step-by-step contribution roadmap cards.

## Big-O Algorithmic Complexity

| Operation | Time Complexity | Space Complexity | Description |
|---|---|---|---|
| Contributor Isolation Scoring | $O(V + E)$ | $O(V)$ | Calculating in-degree centrality and blast radius for all candidate issue-associated nodes |
| Prerequisite Concept Graph Extraction| $O(K \cdot D)$ | $O(K)$ | Traversing $D$ dependency levels from target node $u$ to extract required conceptual dependencies |
| 3-Step Contributor Blueprint Synthesis| $O(1)$ | $O(1)$ | Formatting structured execution steps (Understand ➔ Modify ➔ Verify) based on node AST profile |
| Pre-Flight PR Safety Verification | $O(V_{\text{reach}})$ | $O(V_{\text{reach}})$ | Checking contributor PR diff against architectural boundary rules and test coverage requirements |

## Contributor Safety & Isolation Score Formulation

The Contributor Isolation Score ($\text{CIS}$) measures how safely a beginner can modify a target node $v$ without causing unintended regressions:

$$\text{CIS}(v) = \frac{1}{1 + \ln(1 + \text{InDegree}(v))} \cdot \frac{1}{1 + \ln(1 + \text{TransitiveDependents}(v))} \cdot \exp\left(-\frac{\text{Complexity}(v)}{25}\right)$$

Where:
- High $\text{CIS}(v) \in [0.7, 1.0]$ designates an ideal "Good First Issue" candidate (isolated utility, leaf component, documentation helper, or standalone route).
- Low $\text{CIS}(v) < 0.2$ indicates a high-risk core infrastructure node (session manager, database connection pool, global state dispatcher) unsuitable for first-time contributors.

## Contributor Execution Blueprint Workflow

```
┌─────────────────────────────────┐
│       Selected GitHub Issue     │
│   (e.g., #42: Add CSV Exporter) │
└─────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐      ┌─────────────────────────────┐
│ Contributor Isolation Scorer    │ ───▶ │ Prerequisite Checklist      │
│ (Evaluates In-Degree & Blast)   │      │ (e.g. Streams, CSV Schema)  │
└─────────────────────────────────┘      └─────────────────────────────┘
                 │                                      │
                 ▼                                      ▼
┌─────────────────────────────────┐      ┌─────────────────────────────┐
│ 3-Step Execution Roadmap        │ ───▶ │ Interactive Canvas Focus    │
│ (1. Read ➔ 2. Edit ➔ 3. Test)   │      │ (Highlights Target Subgraph)│
└─────────────────────────────────┘      └─────────────────────────────┘
                 │                                      │
                 ▼                                      ▼
┌─────────────────────────────────┐      ┌─────────────────────────────┐
│ Pre-Flight Safety Verification  │ ───▶ │ Verified PR Submission      │
│ (Linters, Boundaries, Tests)    │      │ (Unlocks Contributor Badge) │
└─────────────────────────────────┘      └─────────────────────────────┘
```

