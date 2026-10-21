# Phase 5 Issues: CodeAtlas Prime Convergence & Advanced Enterprise Capabilities

This document details all Phase 5 issues for CodeAtlas Prime covering the convergence of spatial codebase topology and temporal developer telemetry, PR blast radius automation, architectural boundary linting, bus factor risk alerts, dynamic README badges, IDE extensions, and enterprise integrations.

---

### Issue #099: `[FEAT]: PR "Blast Radius" GitHub App Bot with Automated Architectural Impact Comment`
- **Labels**: `phase:phase-5-prime`, `type:feature`, `priority:P0-critical`, `component:apps/api`, `status:ready`
- **Milestone**: `M6: V2.0 / CodeAtlas Prime`
- **Component**: `apps/api/services/bot/blast_radius.py`, `apps/api/routers/webhooks.py`
- **Problem Statement**:
  When engineers open pull requests, reviewers lack immediate visibility into downstream breaking changes, affected API routes, and hidden dependency blast radiuses.
- **Technical Specification**:
  - Intercept GitHub `pull_request.opened` and `synchronize` webhook events.
  - Extract changed file paths from PR git diff.
  - Project changed files onto the dependency graph; traverse downstream 1-hop and 2-hop dependent nodes.
  - Compute:
    - **Blast Radius Count**: Total number of downstream files, functions, and routes affected.
    - **Hotspot Risk**: Cross-reference with commit frequency and open regression issues.
    - **Recommended Reviewers**: Identify top code contributors using git blame ownership across the affected call chain.
  - Post formatted GitHub PR markdown comment with impact summary and link to live isolated subgraph.
- **Acceptance Criteria**:
  - [ ] Posts comprehensive blast radius comment within 15 seconds of PR creation.
  - [ ] Automatically updates comment on subsequent pushes to the PR branch.
  - [ ] Gracefully skips non-code files (e.g. markdown docs, image assets).

---

### Issue #100: `[FEAT]: Architectural Boundary Enforcement Engine ("The Architecture Linter")`
- **Labels**: `phase:phase-5-prime`, `type:feature`, `priority:P0-critical`, `component:apps/api`, `status:ready`
- **Milestone**: `M6: V2.0 / CodeAtlas Prime`
- **Component**: `apps/api/services/linter/boundary_checker.py`
- **Problem Statement**:
  Monorepos degrade into tangled spaghetti architecture when developers introduce illegal imports (e.g. frontend importing backend code, or domain packages bypassing shared abstractions).
- **Technical Specification**:
  - Define configuration schema in `codeatlas.config.json`:
    ```json
    {
      "boundaries": [
        { "from": "apps/web/**", "disallow": "apps/api/**" },
        { "from": "packages/ui/**", "disallow": "packages/database/**" },
        { "from": "modules/billing/**", "allowOnly": ["modules/auth/**", "packages/shared/**"] }
      ]
    }
    ```
  - Parse changed import edges during PR analysis.
  - If an edge violates configured boundary rules:
    - Post an inline PR review comment pointing to the offending line number.
    - Set GitHub commit status check to `failure` with diagnostic: *"Illegal architectural import detected"*.
- **Acceptance Criteria**:
  - [ ] Evaluates glob-based import boundary patterns in < 2 seconds.
  - [ ] Blocks PR merges via GitHub branch protection checks when violations occur.
  - [ ] Supports CLI execution via `npx @codeatlas/cli lint-boundaries`.

---

### Issue #101: `[FEAT]: "Bus Factor" & Single-Maintainer Knowledge Silo Risk Analysis`
- **Labels**: `phase:phase-5-prime`, `type:feature`, `priority:P1-high`, `component:apps/api`, `status:ready`
- **Milestone**: `M6: V2.0 / CodeAtlas Prime`
- **Component**: `apps/api/services/telemetry/bus_factor.py`
- **Problem Statement**:
  Organizations face severe operational risks when critical core modules (e.g. billing reconciliation or token verification) are understood and modified by only a single engineer.
- **Technical Specification**:
  - Parse git commit history and blame line ownership across all repository files.
  - For each AST code node and module, compute:
    - **Contributor Entropy**: Distribution of authored lines across developers.
    - **Primary Maintainer Dominance**: Percentage of lines authored by the top contributor.
  - Flag high-risk "Silos": Nodes with high in-degree centrality ($> 10$) where a single contributor owns $> 85\%$ of commits and no other active contributor has modified the file in 180 days.
  - Display "Bus Factor Alert" pill on canvas nodes.
- **Acceptance Criteria**:
  - [ ] Accurately identifies single-maintainer critical path modules.
  - [ ] Ranks architectural components by knowledge silo severity.
  - [ ] Recommends pairing partners to distribute codebase ownership.

---

### Issue #102: `[FEAT]: Dynamic README SVG Architecture Badge Generator`
- **Labels**: `phase:phase-5-prime`, `type:feature`, `priority:P1-high`, `component:apps/api`, `status:ready`
- **Milestone**: `M6: V2.0 / CodeAtlas Prime`
- **Component**: `apps/api/routers/badges.py`
- **Problem Statement**:
  Open-source and enterprise repositories need dynamic visual badges in their root README displaying live architectural health, node counts, and complexity metrics.
- **Technical Specification**:
  - Endpoint: `GET /api/v1/repos/{id}/badge.svg?metric=nodes|health|complexity|routes`:
    - Generates dynamic, pixel-perfect SVG card.
    - Visualizes: Active node count, total edges, architecture health grade (A/B/C/F), and last analyzed timestamp.
  - Support dark and light theme parameters (`?theme=dark|light`).
  - Cache responses with HTTP headers (`Cache-Control: public, max-age=3600, s-maxage=3600`) and ETag validation.
- **Acceptance Criteria**:
  - [ ] Generates valid SVG image rendering cleanly in GitHub READMEs.
  - [ ] Response time < 20ms using Redis SVG template cache.
  - [ ] Clicking badge redirects user to the live interactive canvas on CodeAtlas.

---

### Issue #103: `[FEAT]: Temporal Commit Churn Heatmap Overlay on Spatial React Flow Nodes`
- **Labels**: `phase:phase-5-prime`, `type:frontend`, `priority:P1-high`, `component:apps/web`, `status:ready`
- **Milestone**: `M6: V2.0 / CodeAtlas Prime`
- **Component**: `apps/web/src/components/graph/TemporalChurnHeatmap.tsx`
- **Problem Statement**:
  Code quality cannot be understood through static code alone. The most dangerous files are those that have both high static complexity AND high commit churn (modified 40+ times a month).
- **Technical Specification**:
  - Ingest git commit frequency per file over 30, 60, and 90-day rolling windows.
  - Add "Temporal Churn" filter in canvas display modes.
  - Compute Risk Index: $Risk = Complexity \times Churn$.
  - Render pulsing flame markers and color intensity overlays on high-risk hotspot nodes.
- **Acceptance Criteria**:
  - [ ] Visualizes commit frequency directly on the architecture topology.
  - [ ] Identifies the "top 5% code hotspots" causing 80% of repository churn.
  - [ ] Slider control to adjust time window (30 days vs 1 year).

---

### Issue #104: `[FEAT]: GitWatcher (GitPulse) Developer Telemetry Convergence`
- **Labels**: `phase:phase-5-prime`, `type:feature`, `priority:P1-high`, `component:apps/api`, `status:ready`
- **Milestone**: `M6: V2.0 / CodeAtlas Prime`
- **Component**: `apps/api/services/telemetry/gitpulse_sync.py`
- **Problem Statement**:
  Fusing GitWatcher's engineering velocity metrics (PR review latency, DORA deployment frequency, review cycle time) with CodeAtlas's AST topology creates an unprecedented holistic developer observability platform.
- **Technical Specification**:
  - Ingest PR lifecycle telemetry: Time to First Review, Review Depth (comments per PR), Merge Latency.
  - Map velocity metrics to specific codebase architectural domains (e.g. "Why are PRs in `modules/billing` taking 4x longer to review than `apps/web`?").
  - Reveal architectural bottlenecks slowing down team velocity.
- **Acceptance Criteria**:
  - [ ] Dashboard correlates review latency with code complexity and node degree.
  - [ ] Highlights architectural areas requiring excessive review cycles.
  - [ ] Unified database schema linking commit SHAs to AST graph nodes.

---

### Issue #105: `[FEAT]: Architectural Drift Tracking Between Git Branches & Release Tags`
- **Labels**: `phase:phase-5-prime`, `type:feature`, `priority:P1-high`, `component:apps/api`, `status:ready`
- **Milestone**: `M6: V2.0 / CodeAtlas Prime`
- **Component**: `apps/api/services/graph/branch_comparator.py`
- **Problem Statement**:
  Feature branches often introduce architectural deviations that diverge from main. Engineers need to compare branch topologies before merging.
- **Technical Specification**:
  - Endpoint: `POST /api/v1/repos/{id}/graph/diff`:
    - Parameters: `base_branch`, `target_branch`.
    - Returns topological diff: added nodes, deleted nodes, added edges, deleted edges.
  - Canvas renders side-by-side or overlay diff view with color-coded additions (green) and deletions (red).
- **Acceptance Criteria**:
  - [ ] Computes structural graph diff between two git branches in < 3 seconds.
  - [ ] Canvas highlights newly introduced coupling edges.
  - [ ] Exportable as visual architectural change summary.

---

### Issue #106: `[FEAT]: CodeAtlas VS Code Extension: In-Editor Graph Navigation & Hover AST Insights`
- **Labels**: `phase:phase-5-prime`, `type:frontend`, `priority:P1-high`, `component:extensions`, `status:ready`
- **Milestone**: `M6: V2.0 / CodeAtlas Prime`
- **Component**: `apps/vscode-extension/`
- **Problem Statement**:
  Developers spend their working hours inside their IDE. Switching out to a browser tab disrupts flow state; codebase intelligence should be accessible directly in VS Code.
- **Technical Specification**:
  - Build VS Code extension using the VS Code Extension API.
  - Features:
    - Sidebar WebView rendering interactive CodeAtlas mini-canvas centered on the active editor file.
    - Hover provider: Hovering over a function displays callers count, complexity score, and linked GitHub issues.
    - Command Palette: `CodeAtlas: Map Active File to Open Issues`, `CodeAtlas: View Downstream Callers`.
- **Acceptance Criteria**:
  - [ ] Synchronizes active editor cursor with canvas node focus.
  - [ ] Connects to local or remote CodeAtlas instance via API token.
  - [ ] Published to VS Code Marketplace and Open VSX Registry.

---

### Issue #107: `[FEAT]: JetBrains IDE Plugin for CodeAtlas Graph & Subgraph Exploration`
- **Labels**: `phase:phase-5-prime`, `type:frontend`, `priority:P2-medium`, `component:extensions`, `status:ready`
- **Milestone**: `M6: V2.0 / CodeAtlas Prime`
- **Component**: `apps/jetbrains-plugin/`
- **Problem Statement**:
  Kotlin, Java, Python, and Go developers working in IntelliJ IDEA, PyCharm, and GoLand require native IDE integration.
- **Technical Specification**:
  - Kotlin-based JetBrains plugin with JCEF (Chromium Embedded Framework) tool window.
  - Embeds CodeAtlas canvas with bidirectional IDE file jumping (`Navigate -> Jump to Source`).
  - Right-click file in Project Explorer -> *"Explore Architecture Subgraph in CodeAtlas"*.
- **Acceptance Criteria**:
  - [ ] Works across all IntelliJ-based IDEs (v2023.2+).
  - [ ] Seamless communication between Java/Kotlin IDE backend and React canvas.
  - [ ] Memory footprint under 150 MB.

---

### Issue #108: `[FEAT]: Slack & Discord Bot: Conversational Codebase Q&A ("/codeatlas <query>")`
- **Labels**: `phase:phase-5-prime`, `type:feature`, `priority:P2-medium`, `component:apps/api`, `status:ready`
- **Milestone**: `M6: V2.0 / CodeAtlas Prime`
- **Component**: `apps/api/routers/slack_bot.py`
- **Problem Statement**:
  Engineers in Slack or Discord channels frequently ask questions like "Where is token verification defined?" or "Who owns the billing router?".
- **Technical Specification**:
  - Slack Bolt / Discord API integration for slash command `/codeatlas <query>`.
  - Routes query to RAG Q&A pipeline.
  - Responds in thread with:
    - Grounded explanation.
    - Clickable file citations.
    - Primary file maintainer mention.
    - Deep-link button to open highlighted subgraph on CodeAtlas web.
- **Acceptance Criteria**:
  - [ ] Responds in Slack thread within 3 seconds.
  - [ ] Ephemeral preview with "Post to channel" option.
  - [ ] Verified signatures preventing unauthorized webhook triggers.

---

### Issue #109: `[FEAT]: Auto-Scaffolding PR Patch Generator for Mapped GitHub Issues`
- **Labels**: `phase:phase-5-prime`, `type:feature`, `priority:P2-medium`, `component:ai-rag`, `status:ready`
- **Milestone**: `M6: V2.0 / CodeAtlas Prime`
- **Component**: `apps/api/services/ai/patch_generator.py`
- **Problem Statement**:
  For well-defined bug reports where the 5-signal ranker achieves $> 85\%$ confidence on a specific function, engineers want a scaffolded fix draft to accelerate remediation.
- **Technical Specification**:
  - Assemble issue description, stack trace, and target AST node implementation into prompt.
  - Prompt Ollama to generate a git unified diff patch (`git diff` format).
  - Validate patch syntax and verify that target line numbers match the active file.
  - Render "Create Draft Fix Branch" button in the web UI.
- **Acceptance Criteria**:
  - [ ] Generates clean unified diffs with exact line offsets.
  - [ ] Does not modify unrelated lines or invent non-existent APIs.
  - [ ] One-click action creates a new git branch with the proposed patch applied.

---

### Issue #110: `[FEAT]: Open-Source License Compliance & Vulnerability Dependency Mapper`
- **Labels**: `phase:phase-5-prime`, `type:security`, `priority:P1-high`, `component:ingestion-engine`, `status:ready`
- **Milestone**: `M6: V2.0 / CodeAtlas Prime`
- **Component**: `apps/api/services/ingestion/license_scanner.py`
- **Problem Statement**:
  Enterprises must avoid infectious copyleft licenses (GPL, AGPL) in proprietary products and identify transitive CVE vulnerabilities.
- **Technical Specification**:
  - Parse lockfiles (`pnpm-lock.yaml`, `package-lock.json`, `poetry.lock`, `Cargo.lock`, `go.sum`).
  - Extract external dependency packages and map their declared SPDX licenses.
  - Check dependencies against OSV (Open Source Vulnerability) database.
  - Highlight vulnerable third-party nodes on the canvas with CVSS severity badges.
- **Acceptance Criteria**:
  - [ ] Flags AGPL/GPL dependencies in commercial repositories.
  - [ ] Highlights critical CVEs on canvas nodes and lists remediation upgrade paths.
  - [ ] Generates Software Bill of Materials (SBOM) in SPDX and CycloneDX formats.

---

### Issue #111: `[FEAT]: Notion & Confluence Living Architecture Documentation Sync Engine`
- **Labels**: `phase:phase-5-prime`, `type:feature`, `priority:P2-medium`, `component:apps/api`, `status:ready`
- **Milestone**: `M6: V2.0 / CodeAtlas Prime`
- **Component**: `apps/api/services/integrations/notion_sync.py`
- **Problem Statement**:
  Product and engineering organizations maintain their knowledge bases in Notion or Confluence. Keeping these documents manually aligned with code changes is impossible.
- **Technical Specification**:
  - Integrate Notion API and Atlassian Confluence REST API.
  - Setup scheduled or webhook-driven sync:
    - Export repository architecture overview, module summaries, and Mermaid diagrams to designated Notion page or Confluence space.
    - Synchronize only changed sections to prevent destroying manual user notes.
- **Acceptance Criteria**:
  - [ ] Automatically updates Notion/Confluence pages on merge to `main`.
  - [ ] Preserves custom user sections using demarcated comment tags (`<!-- codeatlas:start -->`).
  - [ ] OAuth integration allowing simple workspace connection.

---

### Issue #112: `[FEAT]: Multi-Repository Cross-Dependency Graph Mapping for Microservices`
- **Labels**: `phase:phase-5-prime`, `type:feature`, `priority:P1-high`, `component:apps/api`, `status:ready`
- **Milestone**: `M6: V2.0 / CodeAtlas Prime`
- **Component**: `apps/api/services/graph/multi_repo.py`
- **Problem Statement**:
  Organizations with polyrepo microservice architectures cannot view end-to-end data flows that span across multiple independent GitHub repositories.
- **Technical Specification**:
  - Link independent repositories within an Organization into a "System Canvas".
  - Detect cross-repository communication:
    - HTTP REST client calls matching route nodes in another repository.
    - gRPC protobuf definitions and RPC client calls.
    - Kafka / RabbitMQ event publishing and message consumer bindings.
  - Render unified inter-service dependency graph in React Flow.
- **Acceptance Criteria**:
  - [ ] Visualizes call flows across multiple separate git repositories.
  - [ ] Tracks cross-service blast radius when a shared API route is changed.
  - [ ] Filters view by individual microservice or overall system topology.

---

### Issue #113: `[FEAT]: 100% Air-Gapped Local Enterprise Distribution & Self-Hosted Package`
- **Labels**: `phase:phase-5-prime`, `type:infra`, `priority:P1-high`, `component:infra`, `status:ready`
- **Milestone**: `M6: V2.0 / CodeAtlas Prime`
- **Component**: `infra/airgap/`
- **Problem Statement**:
  Defense, healthcare, and financial institutions cannot connect their source code to any external internet service or cloud Docker registry.
- **Technical Specification**:
  - Build self-contained air-gapped bundle:
    - Pre-pulled Docker images (`postgres-pgvector`, `redis`, `ollama` with pre-cached `deepseek-coder` and `nomic-embed-text` weights).
    - Offline installer script verifying system prerequisites (NVIDIA drivers, RAM, disk space).
    - Complete zero-network startup verification.
- **Acceptance Criteria**:
  - [ ] Runs with network interfaces completely disabled (`--net=none` test pass).
  - [ ] Model weights bundled locally without downloading during initialization.
  - [ ] Comprehensive offline installation guide provided.

---

### Issue #114: `[FEAT]: 3D WebGL / Force-Directed AST Diff Visualizer`
- **Labels**: `phase:phase-5-prime`, `type:frontend`, `priority:P2-medium`, `component:apps/web`, `status:ready`
- **Milestone**: `M6: V2.0 / CodeAtlas Prime`
- **Component**: `apps/web/src/components/graph/Graph3D.tsx`
- **Problem Statement**:
  For massive systems with $> 10,000$ files, 2D planar layouts encounter overlapping planes. A 3D spatial view provides superior depth perception for cluster hierarchies.
- **Technical Specification**:
  - Implement 3D canvas option using Three.js / React Force Graph 3D.
  - Render nodes as glowing 3D spheres positioned by directory sphere clusters.
  - Dependency edges rendered as glowing curved splines with traveling particle photons.
  - Orbit controls, mousewheel fly-through navigation, and VR headset support (WebXR).
- **Acceptance Criteria**:
  - [ ] Smooth 60 FPS rendering on 10,000 nodes using instanced mesh rendering.
  - [ ] Click-to-focus camera animation flying directly to selected node.
  - [ ] Toggle seamlessly between 2D React Flow and 3D WebGL modes.

---

### Issue #115: `[FEAT]: Custom Architectural Rules Engine with AST Query Language (CodeAtlasQL)`
- **Labels**: `phase:phase-5-prime`, `type:feature`, `priority:P1-high`, `component:apps/api`, `status:ready`
- **Milestone**: `M6: V2.0 / CodeAtlas Prime`
- **Component**: `apps/api/services/rules/query_engine.py`
- **Problem Statement**:
  Enterprise architects need to define bespoke structural assertions (e.g. "Every Route handler must call a Service class", "No model may import an HTTP controller").
- **Technical Specification**:
  - Create declarative AST graph query engine:
    ```sql
    MATCH (r:Route)-[:handles_route]->(h:Function)
    WHERE NOT (h)-[:calls]->(:Service)
    RETURN r, h
    ```
  - Pre-packaged rule library for clean architecture, hexagonal architecture, and MVC patterns.
  - Run rule assertions on schedule and in pull requests.
- **Acceptance Criteria**:
  - [ ] Evaluates custom graph patterns with sub-second execution times.
  - [ ] Emits detailed rule violation reports with node links.
  - [ ] Web UI for writing and testing custom queries interactively.

---

### Issue #116: `[FEAT]: Codebase Technical Debt Prioritization Matrix (Churn vs Complexity)`
- **Labels**: `phase:phase-5-prime`, `type:feature`, `priority:P1-high`, `component:apps/api`, `status:ready`
- **Milestone**: `M6: V2.0 / CodeAtlas Prime`
- **Component**: `apps/api/routers/debt_matrix.py`
- **Problem Statement**:
  Engineering leaders struggle to justify refactoring work to product managers because technical debt is rarely quantified with empirical risk data.
- **Technical Specification**:
  - Compute 4-quadrant Technical Debt Matrix:
    - **Quadrant 1 (Critical Danger - High Churn, High Complexity)**: Fix immediately; primary source of bugs.
    - **Quadrant 2 (Latent Risk - Low Churn, High Complexity)**: Leave alone until modification is required.
    - **Quadrant 3 (Active Churn - High Churn, Low Complexity)**: Well-designed, frequently modified modules.
    - **Quadrant 4 (Stable Foundation - Low Churn, Low Complexity)**: Reliable utility code.
  - Render interactive scatter plot with refactoring ROI scores.
- **Acceptance Criteria**:
  - [ ] Automatically categorizes all repository files into the 4 quadrants.
  - [ ] Generates prioritized "Refactoring Backlog" backed by defect probability.
  - [ ] Exportable executive report for engineering leadership.

---

### Issue #117: `[SEC]: Enterprise Single Sign-On (SSO) with SAML 2.0 & OIDC (Okta, Azure AD)`
- **Labels**: `phase:phase-5-prime`, `type:security`, `priority:P0-critical`, `component:apps/api`, `status:ready`
- **Milestone**: `M6: V2.0 / CodeAtlas Prime`
- **Component**: `apps/api/routers/sso.py`
- **Problem Statement**:
  Enterprise organizations require centralized identity management with SAML 2.0 / OIDC integrations and automated employee deprovisioning.
- **Technical Specification**:
  - Support SAML 2.0 identity providers: Okta, Azure Active Directory, Google Workspace, OneLogin.
  - Just-in-Time (JIT) user provisioning and organization assignment based on SAML assertions.
  - SCIM 2.0 endpoint for automated user lifecycle provisioning and deprovisioning.
- **Acceptance Criteria**:
  - [ ] Passwords and credentials never handled directly by CodeAtlas.
  - [ ] Deprovisioning user in IdP immediately terminates all active CodeAtlas sessions.
  - [ ] Verified against official Okta and Azure AD test harnesses.

---

### Issue #118: `[FEAT]: Domain-Specific AST Embedding Model Fine-Tuning Pipeline`
- **Labels**: `phase:phase-5-prime`, `type:feature`, `priority:P2-medium`, `component:ai-rag`, `status:ready`
- **Milestone**: `M6: V2.0 / CodeAtlas Prime`
- **Component**: `apps/api/services/ai/fine_tuner.py`
- **Problem Statement**:
  Generic natural language embedding models do not fully capture programming language semantics (e.g. inheritance, method overrides, and variable scope).
- **Technical Specification**:
  - Construct contrastive learning dataset from repository AST nodes:
    - Positive pairs: Function signature + implementation, Caller + Callee, Interface + Implementation.
    - Hard negative pairs: Functions with identical names in different packages, unrelated classes.
  - Fine-tune base embedding model (`nomic-embed-text`) using MultipleNegativesRankingLoss.
  - Quantize fine-tuned model to GGUF format for high-speed local inference in Ollama.
- **Acceptance Criteria**:
  - [ ] Precision@5 on code retrieval tasks improves by $> 15\%$ over base model.
  - [ ] Quantized GGUF runs smoothly on CPU/GPU via Ollama.
  - [ ] Automated training pipeline callable on custom private code corpuses.
