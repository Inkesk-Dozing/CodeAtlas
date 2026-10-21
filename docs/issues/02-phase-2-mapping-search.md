# Phase 2 Issues: Interactive Canvas UX, Search & Issue-to-Code Mapping Engine

This document details all Phase 2 issues for CodeAtlas covering React Flow canvas rendering, graph virtualization, hybrid natural language search, GitHub issue ingestion, and the 5-signal issue-to-code ranking algorithm.

---

### Issue #039: `[FEAT]: React Flow Canvas Initialization with Custom AST Node Renderers`
- **Labels**: `phase:phase-2-mapping`, `type:frontend`, `priority:P0-critical`, `component:apps/web`, `status:completed`
- **Milestone**: `M2: Issue Mapping`
- **Component**: `apps/web/src/components/graph/`, `apps/web/src/components/graph/CustomNodes.tsx`
- **Existing Implementation**: [apps/web/src/components/graph/](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/web/src/components/graph/)
- **Problem Statement**:
  Default React Flow nodes look generic and fail to visually convey distinct code roles (e.g. database model vs API route vs React component).
- **Technical Specification**:
  - Implement specialized node components:
    - `FileNode`: Icon, path, line count badge, language tag.
    - `FunctionNode`: Parameter signature, return type, complexity pill.
    - `ClassNode`: Class name, methods list preview, inheritance indicator.
    - `RouteNode`: HTTP verb pill (`GET`, `POST`, `PUT`, `DELETE`), URL path.
    - `ComponentNode`: React/Vue component icon, props count, hook indicator.
  - Interactive handles on left/right for dependency connections.
  - Selection and hover states with neon glowing borders.
- **Acceptance Criteria**:
  - [x] Node colors and badges accurately reflect `node_type`.
  - [x] Clicking a node dispatches selection event to Zustand `useGraphStore`.
  - [x] Clean rendering without text overflow or clipped badges.

---

### Issue #040: `[FEAT]: Typed Edge Rendering with Animated Data Flow & Relationship Colors`
- **Labels**: `phase:phase-2-mapping`, `type:frontend`, `priority:P1-high`, `component:apps/web`, `status:completed`
- **Milestone**: `M2: Issue Mapping`
- **Component**: `apps/web/src/components/graph/CustomEdges.tsx`
- **Existing Implementation**: [apps/web/src/components/graph/](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/web/src/components/graph/)
- **Problem Statement**:
  Engineers need to differentiate between import dependencies, function calls, class inheritance, and route handling at a glance.
- **Technical Specification**:
  - Implement custom smooth step and bezier edges styled by `edge_type`:
    - `imports`: Subtle slate gray solid line.
    - `calls`: Electric blue directional arrow with subtle particle animation on active flow.
    - `extends`: Emerald green dashed line.
    - `handles_route`: Purple thick edge linking route to handler.
    - `renders`: Amber curved edge linking parent to child component.
- **Acceptance Criteria**:
  - [x] Highlighting an edge dims unrelated edges to reduce visual clutter.
  - [x] Smooth rendering during panning and zooming.
  - [x] Edge tooltips display caller/callee context on hover.

---

### Issue #041: `[FEAT]: Dagre Hierarchical Layered Layout & BFS Depth Calculation Engine`
- **Labels**: `phase:phase-2-mapping`, `type:frontend`, `priority:P0-critical`, `component:apps/web`, `status:completed`
- **Milestone**: `M2: Issue Mapping`
- **Component**: `apps/web/src/lib/layout.ts`
- **Existing Implementation**: [apps/web/src/lib/](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/web/src/lib/)
- **Problem Statement**:
  Random or raw physics layouts create unreadable tangled hairball graphs. Monorepos require structured architectural layering (entrypoints -> controllers -> services -> models).
- **Technical Specification**:
  - Implement layout engine utilizing `dagre` algorithm.
  - Support Top-to-Bottom (`TB`) and Left-to-Right (`LR`) orientations.
  - Compute node ranks using Breadth-First Search (BFS) starting from root entrypoints (`main.py`, `app/page.tsx`, `index.ts`).
  - Isolate layout calculations in a Web Worker thread to prevent freezing the main UI.
- **Acceptance Criteria**:
  - [x] Computes positions for 1,000 nodes in under 400ms.
  - [x] Prevents edge crossings and node overlaps through configurable separation margins.
  - [x] Animated transition between layout orientations.

---

### Issue #042: `[PERF]: Canvas Node Virtualization for 2,000+ Nodes at 60 FPS`
- **Labels**: `phase:phase-2-mapping`, `type:performance`, `priority:P1-high`, `component:apps/web`, `status:ready`
- **Milestone**: `M2: Issue Mapping`
- **Component**: `apps/web/src/components/graph/CanvasVirtualizer.tsx`
- **Problem Statement**:
  Rendering DOM nodes for thousands of off-screen elements overwhelms the browser's paint pipeline and causes severe frame drops during canvas panning.
- **Technical Specification**:
  - Intercept React Flow viewport bounds `[x, y, zoom]`.
  - Calculate intersection between node bounding boxes and visible viewport.
  - Unmount DOM contents of off-screen nodes while maintaining lightweight proxy bounding boxes.
  - Dynamically throttle edge render calculations when zoom level < 0.3.
- **Acceptance Criteria**:
  - [ ] Maintains >= 55 FPS during continuous panning on a 2,500-node graph.
  - [ ] DOM element count kept under 300 active nodes regardless of total graph size.
  - [ ] Seamless re-hydration without visual popping when zooming in.

---

### Issue #043: `[FEAT]: Collapsible Directory & Monorepo Package Clustering`
- **Labels**: `phase:phase-2-mapping`, `type:frontend`, `priority:P1-high`, `component:apps/web`, `status:ready`
- **Milestone**: `M2: Issue Mapping`
- **Component**: `apps/web/src/components/graph/ClusterGroup.tsx`
- **Problem Statement**:
  Monorepos contain distinct applications and libraries (`apps/api`, `apps/web`, `packages/shared`). Viewing all nodes flatly prevents high-level mental chunking.
- **Technical Specification**:
  - Group nodes by common directory prefix into compound/container nodes.
  - Render collapsible group boundaries with directory path header, file count pill, and collapse/expand toggle.
  - When collapsed: Aggregate intra-cluster edges into consolidated inter-cluster edges.
  - When expanded: Smoothly animate child nodes to their internal positions.
- **Acceptance Criteria**:
  - [ ] Double-clicking a directory cluster expands/collapses its contents.
  - [ ] External edge connections dynamically route to the cluster boundary when collapsed.
  - [ ] Preserves nested directory hierarchies up to 4 levels deep.

---

### Issue #044: `[FEAT]: Subgraph Exploration & Neighborhood Extraction API`
- **Labels**: `phase:phase-2-mapping`, `type:feature`, `priority:P0-critical`, `component:apps/api`, `status:completed`
- **Milestone**: `M2: Issue Mapping`
- **Component**: `apps/api/routers/graph.py`
- **Existing Implementation**: [apps/api/routers/graph.py](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/routers/graph.py)
- **Problem Statement**:
  Engineers investigating a specific service or bug want to isolate its immediate dependencies without loading the entire monorepo into memory.
- **Technical Specification**:
  - `POST /api/v1/repos/{id}/graph/subgraph`:
    - Parameters: `node_ids: list[str]`, `depth: int = 1`, `direction: "upstream" | "downstream" | "both"`.
    - Returns minimal subset of nodes and edges within $N$-hop neighborhood.
  - Recursive Common Table Expression (CTE) query in PostgreSQL for high-speed traversal.
- **Acceptance Criteria**:
  - [x] Subgraph queries execute in < 50ms for depth=2 on 100k edge graphs.
  - [x] Respects directional traversal (e.g. only finding callers vs only finding dependencies).
  - [x] Response payload adheres to shared `GraphData` TypeScript contract.

---

### Issue #045: `[FEAT]: Interactive Canvas Navigation Controls, Minimap & Center-on-Node`
- **Labels**: `phase:phase-2-mapping`, `type:frontend`, `priority:P1-high`, `component:apps/web`, `status:completed`
- **Milestone**: `M2: Issue Mapping`
- **Component**: `apps/web/src/components/graph/GraphControls.tsx`
- **Existing Implementation**: [apps/web/src/components/graph/](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/web/src/components/graph/)
- **Problem Statement**:
  Navigating large visual graphs requires fluid controls for zooming, panning, overview navigation, and instantly focusing on search hits.
- **Technical Specification**:
  - Mount React Flow `MiniMap` with node color-coding in bottom-right corner.
  - Floating control toolbar: Zoom In, Zoom Out, Zoom to Fit, Lock Canvas, Toggle Minimap.
  - Animated camera centering: `centerOnNode(nodeId, { duration: 800, zoom: 1.2 })`.
  - Keyboard shortcuts: `Space` (pan), `F` (focus), `Esc` (clear selection).
- **Acceptance Criteria**:
  - [x] "Zoom to Fit" frames all active nodes with comfortable 50px padding.
  - [x] Selecting a search result smoothly pans the camera and triggers a pulse animation on the target node.
  - [x] Minimap correctly reflects active viewport boundaries.

---

### Issue #046: `[FEAT]: GitHub Issues Fetcher Service with GraphQL Pagination & Comment Threads`
- **Labels**: `phase:phase-2-mapping`, `type:feature`, `priority:P0-critical`, `component:apps/api`, `status:completed`
- **Milestone**: `M2: Issue Mapping`
- **Component**: `apps/api/routers/issues.py`, `apps/api/services/mapping/`
- **Existing Implementation**: [apps/api/routers/issues.py](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/routers/issues.py)
- **Problem Statement**:
  Issue mapping requires full issue context (title, body, labels, author, and reviewer comments) fetched via GitHub API with rate limit awareness.
- **Technical Specification**:
  - Sync open and recently closed issues via GitHub REST API with conditional `If-None-Match` ETag caching.
  - For issues with discussion, use GraphQL to fetch up to 20 top comments.
  - Store records in PostgreSQL `issues` table with foreign key to `repository_id`.
  - Handle GitHub secondary rate limits with exponential backoff.
- **Acceptance Criteria**:
  - [x] Synchronizes 100 issues with comments in < 10 seconds.
  - [x] Respects GitHub API rate limits using installation token quotas.
  - [x] Updates existing issue records on subsequent syncs without duplicate keys.

---

### Issue #047: `[FEAT]: Issue Text Preprocessor (Code Block Extraction, Stack Traces & Symbols)`
- **Labels**: `phase:phase-2-mapping`, `type:feature`, `priority:P1-high`, `component:mapping-engine`, `status:completed`
- **Milestone**: `M2: Issue Mapping`
- **Component**: `apps/api/services/mapping/preprocessor.py`
- **Existing Implementation**: [apps/api/services/mapping/](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/services/mapping/)
- **Problem Statement**:
  Raw issue markdown contains conversational noise ("Hey team", "Steps to reproduce") that dilutes semantic search. Critical signals (stack traces, file paths, backticked code) must be extracted and prioritized.
- **Technical Specification**:
  - Regex parser extracting:
    - File path mentions (`apps/api/auth.py`, `src/components/Button.tsx`).
    - Backticked symbols (`` `validate_token` ``, `` `UserSession` ``).
    - URL endpoints (`/api/v1/auth/callback`).
    - Python/Node.js stack traces (extracting frame filenames and line numbers).
  - Cleaned text output for embedding generation.
- **Acceptance Criteria**:
  - [x] Extracts mentioned file paths with 100% precision.
  - [x] Isolates error messages and exception class names from stack traces.
  - [x] Weights extracted code symbols higher than surrounding prose.

---

### Issue #048: `[FEAT]: Issue Intent Classifier (Bug, Feature, Refactor, Security, Docs)`
- **Labels**: `phase:phase-2-mapping`, `type:feature`, `priority:P1-high`, `component:mapping-engine`, `status:completed`
- **Milestone**: `M2: Issue Mapping`
- **Component**: `apps/api/services/mapping/classifier.py`
- **Existing Implementation**: [apps/api/services/mapping/](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/services/mapping/)
- **Problem Statement**:
  Different issue types map to different code areas. A bug report usually maps to existing handlers and logic, while a feature request may map to interfaces, routers, or extension points.
- **Technical Specification**:
  - Classify issue into `BUG`, `FEATURE`, `REFACTOR`, `SECURITY`, `DOCS`.
  - Multi-feature heuristic using:
    - GitHub labels (`bug`, `enhancement`, `documentation`, `security`).
    - Title keywords (`fix`, `crash`, `error`, `add`, `support`, `upgrade`).
    - Structural presence of stack traces or reproducible steps.
- **Acceptance Criteria**:
  - [x] Classification accuracy > 88% on sample issue corpus.
  - [x] Assigns confidence score to predicted intent.
  - [x] Adjusts search strategy based on detected intent.

---

### Issue #049: `[FEAT]: Signal 1 — Semantic Issue Candidate Retrieval via pgvector Cosine Distance`
- **Labels**: `phase:phase-2-mapping`, `type:feature`, `priority:P0-critical`, `component:mapping-engine`, `status:completed`
- **Milestone**: `M2: Issue Mapping`
- **Component**: `apps/api/services/mapping/semantic_ranker.py`
- **Existing Implementation**: [apps/api/services/mapping/](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/services/mapping/)
- **Problem Statement**:
  Users frequently describe problems using high-level concepts ("user session expires immediately") without explicitly naming code symbols.
- **Technical Specification**:
  - Generate embedding for cleaned issue text using Ollama / Sentence-Transformers.
  - Execute cosine similarity query against `code_nodes` table:
    `1 - (embedding <=> issue_embedding) AS semantic_score`.
  - Filter by `repository_id` and limit to top-50 candidate nodes.
- **Acceptance Criteria**:
  - [x] Retrieves conceptually related files even when variable names differ.
  - [x] Query executes in < 30ms via pgvector HNSW index.
  - [x] Normalized semantic similarity score bounded between `[0.0, 1.0]`.

---

### Issue #050: `[FEAT]: Signal 2 — Structural Heuristic Matcher via Trigram & Exact Symbol Match`
- **Labels**: `phase:phase-2-mapping`, `type:feature`, `priority:P0-critical`, `component:mapping-engine`, `status:completed`
- **Milestone**: `M2: Issue Mapping`
- **Component**: `apps/api/services/mapping/structural_ranker.py`
- **Existing Implementation**: [apps/api/services/mapping/](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/services/mapping/)
- **Problem Statement**:
  When an issue explicitly mentions a filename (`auth.py`) or class name (`TokenVerifier`), semantic vectors alone may not score it high enough compared to exact string matches.
- **Technical Specification**:
  - Match extracted symbols and paths against `code_nodes.name` and `code_nodes.path`.
  - Compute trigram similarity score using PostgreSQL `similarity(code_nodes.name, query_symbol)`.
  - Exact filename match receives 1.0 structural score; partial path match receives 0.7; symbol substring match receives 0.5.
- **Acceptance Criteria**:
  - [x] Explicit file mentions guaranteed to appear in top candidates.
  - [x] Case-insensitive matching across camelCase, snake_case, and kebab-case.
  - [x] Structural score bounded between `[0.0, 1.0]`.

---

### Issue #051: `[FEAT]: Signal 3 — Topological 1-Hop Graph Neighbor Propagation Algorithm`
- **Labels**: `phase:phase-2-mapping`, `type:feature`, `priority:P0-critical`, `component:mapping-engine`, `status:completed`
- **Milestone**: `M2: Issue Mapping`
- **Component**: `apps/api/services/mapping/topological_ranker.py`
- **Existing Implementation**: [apps/api/services/mapping/](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/services/mapping/)
- **Problem Statement**:
  Bug fixes rarely modify a single isolated function; changes usually ripple to immediate callers, callees, or imported models.
- **Technical Specification**:
  - For top candidates identified by semantic and structural signals, traverse connected edges in `code_edges`.
  - Propagate confidence score to 1-hop neighbors discounted by attenuation factor $\gamma = 0.5$.
  - Boost nodes that have multiple incoming edges from high-confidence candidates.
- **Acceptance Criteria**:
  - [x] Surfaces dependent service and model files that were not mentioned in the issue text.
  - [x] Bounded graph traversal prevents runaway score inflation.
  - [x] Execution time < 20ms using indexed edge joins.

---

### Issue #052: `[FEAT]: Signal 4 — Historical Reviewer Feedback Weighting`
- **Labels**: `phase:phase-2-mapping`, `type:feature`, `priority:P1-high`, `component:mapping-engine`, `status:completed`
- **Milestone**: `M2: Issue Mapping`
- **Component**: `apps/api/services/mapping/historical_ranker.py`
- **Existing Implementation**: [apps/api/services/mapping/](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/services/mapping/)
- **Problem Statement**:
  The ranking algorithm must learn from engineer feedback over time, penalizing false positives and boosting validated mappings.
- **Technical Specification**:
  - Query `mapping_feedbacks` table for previous user thumbs up/down ratings on identical or similar node paths.
  - Calculate historical adjustment score:
    $S_{hist} = \frac{positive - negative}{positive + negative + 2}$.
  - Apply additive bonus/penalty to candidate score.
- **Acceptance Criteria**:
  - [x] Downvoted incorrect files drop out of top-5 recommendations.
  - [x] Validated files gain confidence boost on future similar issues.
  - [x] Default prior neutral (0.0) when no historical data exists.

---

### Issue #053: `[FEAT]: Signal 5 — Hotspot Degree Centrality Prioritization`
- **Labels**: `phase:phase-2-mapping`, `type:feature`, `priority:P1-high`, `component:mapping-engine`, `status:completed`
- **Milestone**: `M2: Issue Mapping`
- **Component**: `apps/api/services/mapping/hotspot_ranker.py`
- **Existing Implementation**: [apps/api/services/mapping/](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/services/mapping/)
- **Problem Statement**:
  Critical architectural bottlenecks and frequently imported utility modules have high in-degree centrality and are disproportionately involved in system bugs.
- **Technical Specification**:
  - Calculate normalized degree centrality per node:
    $C_d(v) = \frac{in\_degree(v) + out\_degree(v)}{max\_degree}$.
  - Weight centrality score into final ranking to prioritize architectural hub nodes.
- **Acceptance Criteria**:
  - [x] Highly interconnected nodes receive proportional priority bonus.
  - [x] Prevents obscure dead-end leaf nodes from outranking critical controllers.
  - [x] Degree values precomputed and cached during ingestion.

---

### Issue #054: `[FEAT]: 5-Signal Combined Confidence Calibration & Tier Assignment (High/Med/Low)`
- **Labels**: `phase:phase-2-mapping`, `type:feature`, `priority:P0-critical`, `component:mapping-engine`, `status:completed`
- **Milestone**: `M2: Issue Mapping`
- **Component**: `apps/api/services/mapping/calibrator.py`
- **Existing Implementation**: [apps/api/services/mapping/](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/services/mapping/)
- **Problem Statement**:
  Raw combined scores must be calibrated into an intuitive percentage confidence (`0%` to `100%`) and classified into actionable tiers for the UI.
- **Technical Specification**:
  - Weighted linear combination:
    $Score = 0.35 \cdot S_{sem} + 0.30 \cdot S_{struct} + 0.15 \cdot S_{topo} + 0.10 \cdot S_{hist} + 0.10 \cdot S_{hot}$.
  - Sigmoid calibration mapping raw score to calibrated confidence percentage.
  - Categorize into tiers:
    - **High**: $\ge 75\%$ (Green badge — primary files to edit).
    - **Medium**: $50\% - 74\%$ (Yellow badge — secondary dependencies or context).
    - **Low**: $< 50\%$ (Gray badge — exploratory reference).
- **Acceptance Criteria**:
  - [x] Generates top-10 ranked files with confidence percentage and tier tag.
  - [x] Returns explanatory evidence bullets explaining why each file was mapped.
  - [x] Precision@5 exceeds 75% on validated golden test dataset.

---

### Issue #055: `[FEAT]: Issue Detail Sidebar with Highlighting & Suggested Action Reasoning`
- **Labels**: `phase:phase-2-mapping`, `type:frontend`, `priority:P0-critical`, `component:apps/web`, `status:completed`
- **Milestone**: `M2: Issue Mapping`
- **Component**: `apps/web/src/components/panels/IssueMappingPanel.tsx`
- **Existing Implementation**: [apps/web/src/components/panels/](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/web/src/components/panels/)
- **Problem Statement**:
  Developers clicking an issue need to see which files to change, why they were selected, and what actions to take, accompanied by canvas highlighting.
- **Technical Specification**:
  - Slide-out drawer displaying issue title, author, GitHub link, and intent pill.
  - Ranked list of mapped files with confidence badges (`92% High`).
  - Expanding a file displays:
    - Evidence tags (`Semantic: 0.88`, `Exact Match: auth.py`, `Topological: 1-hop from route`).
    - Suggested actions: *"Inspect JWT expiration logic in line 42-65"*.
    - Thumbs up / Thumbs down feedback buttons.
  - Clicking a file centers the canvas and highlights its node and connecting edges with a glowing green stroke.
- **Acceptance Criteria**:
  - [x] Smooth drawer slide-in animation without layout shift.
  - [x] Canvas highlights mapped subgraph in < 100ms.
  - [x] Thumbs up/down sends feedback payload to `POST /issues/{n}/feedback`.

---

### Issue #056: `[FEAT]: Node Detail Inspector Drawer (Source Preview, Relationships & Complexity)`
- **Labels**: `phase:phase-2-mapping`, `type:frontend`, `priority:P1-high`, `component:apps/web`, `status:completed`
- **Milestone**: `M2: Issue Mapping`
- **Component**: `apps/web/src/components/panels/NodeDetailPanel.tsx`
- **Existing Implementation**: [apps/web/src/components/panels/](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/web/src/components/panels/)
- **Problem Statement**:
  Engineers need quick access to a node's source code, incoming callers, outgoing dependencies, and cyclomatic complexity without switching back and forth to their IDE.
- **Technical Specification**:
  - Sidebar showing:
    - Node name, qualified path, language, line range (`lines 45-88`).
    - Syntax-highlighted code snippet preview with line numbers.
    - Cyclomatic complexity score with risk indicator (Low/Moderate/High).
    - Tabs: "Callers (Incoming)", "Dependencies (Outgoing)", "Summary".
  - One-click "Copy path" and "Open in GitHub" buttons.
- **Acceptance Criteria**:
  - [x] Code preview fetches node source via `GET /repos/{id}/nodes/{id}`.
  - [x] Clicking a caller/callee in the list navigates to that node on canvas.
  - [x] Clean dark theme syntax highlighting.

---

### Issue #057: `[FEAT]: Hybrid Natural Language Search API & Real-Time Query UI`
- **Labels**: `phase:phase-2-mapping`, `type:feature`, `priority:P0-critical`, `component:apps/api`, `status:completed`
- **Milestone**: `M2: Issue Mapping`
- **Component**: `apps/api/routers/search.py`, `apps/web/src/components/panels/SearchPanel.tsx`
- **Existing Implementation**: [apps/api/routers/search.py](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/routers/search.py)
- **Problem Statement**:
  Users want to search for both technical symbols (`useAuthStore`, `/api/v1/repos`) and conceptual questions (`where is rate limiting implemented?`).
- **Technical Specification**:
  - Endpoints:
    - `POST /search/semantic`: Vector cosine search against node embeddings.
    - `POST /search/structural`: Trigram fuzzy search on names and paths.
    - `POST /search/hybrid`: Reciprocal Rank Fusion (RRF) combining semantic and structural results.
  - Frontend search input with auto-complete dropdown, debounce (250ms), and keyboard shortcut (`Cmd+K` / `Ctrl+K`).
- **Acceptance Criteria**:
  - [x] Reciprocal Rank Fusion returns top matches across both exact symbol and semantic intent.
  - [x] Search execution time < 80ms.
  - [x] Pressing `Enter` centers canvas on the top result.

---

### Issue #058: `[TEST]: Issue Mapping Golden Set Accuracy Evaluation Suite`
- **Labels**: `phase:phase-2-mapping`, `type:test`, `priority:P1-high`, `component:mapping-engine`, `status:ready`
- **Milestone**: `M2: Issue Mapping`
- **Component**: `apps/api/tests/eval/issue_mapping_eval.py`
- **Problem Statement**:
  Algorithmic updates to ranking weights must be automatically evaluated against ground truth pull request diffs to avoid regression in mapping precision.
- **Technical Specification**:
  - Curate golden evaluation dataset of 100 closed GitHub issues paired with their merged PR file diffs.
  - Automated benchmark script computing:
    - **Precision@1**, **Precision@3**, **Precision@5**.
    - **Mean Reciprocal Rank (MRR)**.
    - **Hit Rate**: Percentage of issues where the true fix file was in top-5 recommendations.
- **Acceptance Criteria**:
  - [ ] Benchmark asserts Precision@5 >= 75% on evaluation dataset.
  - [ ] Generates comparative accuracy report between model weight versions.
  - [ ] Can run in CI pipeline on pull requests touching `apps/api/services/mapping/`.
