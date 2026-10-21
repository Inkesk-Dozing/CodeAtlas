# Phase 3 Issues: AI Summaries, Living Documentation & RAG Chat Engine

This document details all Phase 3 issues for CodeAtlas covering local LLM inference via Ollama, directory and module summarization, code complexity analytics, living architectural documentation generation, and the Retrieval-Augmented Generation (RAG) conversational chat engine.

---

### Issue #059: `[FEAT]: Local LLM Client Integration with Ollama, Timeout & Model Fallback`
- **Labels**: `phase:phase-3-ai-docs`, `type:feature`, `priority:P0-critical`, `component:ai-rag`, `status:completed`
- **Milestone**: `M3: AI & Docs`
- **Component**: `apps/api/services/ai/client.py`
- **Existing Implementation**: [apps/api/services/ai/](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/services/ai/)
- **Problem Statement**:
  CodeAtlas requires privacy-first local LLM inference (`codellama`, `deepseek-coder`, `llama3`) running locally via Ollama without leaking sensitive code to cloud providers.
- **Technical Specification**:
  - Implement async client for Ollama HTTP API (`POST /api/generate`, `POST /api/chat`).
  - Configure connection pooling, exponential backoff retries, and configurable timeouts (default 30s).
  - Support model fallback: `deepseek-coder:6.7b` -> `codellama:7b` -> `llama3:8b`.
  - Stream tokens asynchronously using Python async generators.
- **Acceptance Criteria**:
  - [x] Successfully streams completion tokens over async HTTP client.
  - [x] Handles connection drops gracefully with descriptive error payloads.
  - [x] Zero external internet requests: strictly targets `OLLAMA_HOST`.

---

### Issue #060: `[FEAT]: Directory-Level Architectural Purpose Summarizer`
- **Labels**: `phase:phase-3-ai-docs`, `type:feature`, `priority:P1-high`, `component:ai-rag`, `status:completed`
- **Milestone**: `M3: AI & Docs`
- **Component**: `apps/api/services/ai/summarizer.py`
- **Existing Implementation**: [apps/api/services/ai/](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/services/ai/)
- **Problem Statement**:
  When engineers enter unfamiliar monorepo folders (e.g. `apps/api/middleware/` or `packages/shared/tokens/`), they need an immediate executive summary of the directory's purpose, exports, and dependencies.
- **Technical Specification**:
  - Aggregate file listing, top exported symbols, and inbound/outbound directory import edges.
  - Prompt template:
    ```text
    Summarize the architectural purpose of directory '{dir_path}' in 2-3 sentences.
    Focus on: primary responsibility, key exports, and how other packages depend on it.
    Files: {file_list}
    Exports: {export_list}
    ```
  - Store summary in `summaries` table keyed by directory path and git commit hash.
- **Acceptance Criteria**:
  - [x] Generates concise, professional 2-3 sentence summaries.
  - [x] Preserves summaries in database for $O(1)$ fast retrieval.
  - [x] Displayed in directory hover tooltips on the canvas.

---

### Issue #061: `[FEAT]: Module, Class & Function Behavioral Summarizer`
- **Labels**: `phase:phase-3-ai-docs`, `type:feature`, `priority:P1-high`, `component:ai-rag`, `status:completed`
- **Milestone**: `M3: AI & Docs`
- **Component**: `apps/api/services/ai/summarizer.py`
- **Existing Implementation**: [apps/api/services/ai/](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/services/ai/)
- **Problem Statement**:
  Legacy code often lacks docstrings or comments. Auto-generating high-signal behavioral explanations helps onboard engineers 10x faster.
- **Technical Specification**:
  - Extract function body, parameter types, return signature, and callers.
  - Generate explanation covering:
    - What it does (input -> transformation -> output).
    - Side effects (DB queries, API calls, state mutations).
    - Edge cases or exceptions raised.
  - Endpoint: `GET /api/v1/repos/{id}/nodes/{id}/summary`.
- **Acceptance Criteria**:
  - [x] Generates technical, accurate summaries without boilerplate filler words.
  - [x] Response time < 2s with warm Ollama model.
  - [x] Cached in `summaries` table to eliminate duplicate inference.

---

### Issue #062: `[PERF]: Content-Hash Summary Cache to Prevent Redundant LLM Inference`
- **Labels**: `phase:phase-3-ai-docs`, `type:performance`, `priority:P1-high`, `component:ai-rag`, `status:completed`
- **Milestone**: `M3: AI & Docs`
- **Component**: `apps/api/services/ai/cache.py`
- **Existing Implementation**: [apps/api/services/ai/](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/services/ai/)
- **Problem Statement**:
  Running LLM summarization on thousands of files across every git push is computationally prohibitive. Unchanged code must reuse existing summaries.
- **Technical Specification**:
  - Compute SHA-256 hash of node content, signature, and dependency list.
  - Check `summaries` table for matching `content_hash`.
  - If match exists, return cached summary immediately with zero LLM inference.
  - Only dispatch Ollama generation for new or modified content hashes.
- **Acceptance Criteria**:
  - [x] Cache hit rate > 95% on routine pull request re-ingestions.
  - [x] Cache lookup time < 5ms.
  - [x] Automatic stale cache invalidation when function implementation changes.

---

### Issue #063: `[FEAT]: Code Complexity Analyzer (Cyclomatic, Cognitive & Halstead Metrics)`
- **Labels**: `phase:phase-3-ai-docs`, `type:feature`, `priority:P1-high`, `component:apps/api`, `status:completed`
- **Milestone**: `M3: AI & Docs`
- **Component**: `apps/api/parsers/base.py`, `apps/api/models/`
- **Existing Implementation**: [apps/api/parsers/base.py](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/parsers/base.py)
- **Problem Statement**:
  Identifying brittle code hotspots requires automated code complexity scoring across all functions and classes in the monorepo.
- **Technical Specification**:
  - Compute cyclomatic complexity: $M = E - N + 2P$ (decision points: `if`, `elif`, `for`, `while`, `catch`, `&&`, `||`).
  - Compute cognitive complexity (nesting depth penalty).
  - Store score in `code_nodes.complexity` integer column.
  - Classify risk:
    - **Low**: $1 - 5$ (Simple, robust).
    - **Moderate**: $6 - 10$ (Standard complexity).
    - **High**: $11 - 20$ (Refactoring candidate).
    - **Critical**: $> 20$ (High defect probability hotspot).
- **Acceptance Criteria**:
  - [x] Accurately calculates cyclomatic complexity for Python and TypeScript files.
  - [x] Exposes complexity metric via node detail API.
  - [x] Hotspots queryable via `GET /repos/{id}/stats`.

---

### Issue #064: `[FEAT]: Visual Complexity Heatmap Overlay on React Flow Canvas`
- **Labels**: `phase:phase-3-ai-docs`, `type:frontend`, `priority:P1-high`, `component:apps/web`, `status:ready`
- **Milestone**: `M3: AI & Docs`
- **Component**: `apps/web/src/components/graph/ComplexityHeatmap.tsx`
- **Problem Statement**:
  Architects need an immediate bird's-eye view of technical debt and brittle complexity across the entire system topology.
- **Technical Specification**:
  - Add "Heatmap View" toggle in canvas control bar.
  - When enabled, interpolate node background color based on complexity score:
    - Score $1 - 5$: Muted emerald dark green.
    - Score $6 - 10$: Neutral slate.
    - Score $11 - 20$: Amber orange glow.
    - Score $> 20$: Pulsing crimson red border with flame badge.
  - Hotspot list drawer sorting top-10 most complex nodes in the repo.
- **Acceptance Criteria**:
  - [ ] Smooth color transition when toggling heatmap mode on/off.
  - [ ] Clicking a hotspot in the list instantly focuses that node on canvas.
  - [ ] Heatmap color legend displayed in bottom corner.

---

### Issue #065: `[FEAT]: Living Architecture Documentation Generator (Markdown + Mermaid)`
- **Labels**: `phase:phase-3-ai-docs`, `type:feature`, `priority:P0-critical`, `component:apps/api`, `status:completed`
- **Milestone**: `M3: AI & Docs`
- **Component**: `apps/api/routers/summaries.py`, `apps/api/services/ai/architecture_generator.py`
- **Existing Implementation**: [apps/api/routers/summaries.py](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/routers/summaries.py)
- **Problem Statement**:
  Architecture documentation written manually in Notion or Google Docs goes stale within weeks of active development.
- **Technical Specification**:
  - Generate comprehensive architecture documentation:
    - System overview & topology breakdown.
    - Entrypoints and API route contracts.
    - Database entity relationship model.
    - Auto-generated Mermaid diagram representing high-level component dependencies.
  - Endpoint: `GET /api/v1/repos/{id}/architecture`.
- **Acceptance Criteria**:
  - [x] Generates syntactically valid Mermaid diagrams representing module relationships.
  - [x] Updates automatically whenever repository code is re-ingested.
  - [x] Exportable as raw Markdown or rendered HTML.

---

### Issue #066: `[FEAT]: Automated "New Contributor Onboarding Guide" Generator`
- **Labels**: `phase:phase-3-ai-docs`, `type:feature`, `priority:P1-high`, `component:apps/api`, `status:ready`
- **Milestone**: `M3: AI & Docs`
- **Component**: `apps/api/services/ai/onboarding_generator.py`
- **Problem Statement**:
  New developers take an average of 3-4 weeks to understand where to start, what setup steps to run, and how core modules communicate.
- **Technical Specification**:
  - Synthesize repository AST data into a custom Onboarding Guide:
    - "Core Architectural Mental Model" (5 key abstractions).
    - "Data Flow Walkthrough" (from incoming HTTP request to DB persist).
    - "Development Workflow" (how to run tests, add a route, run migrations).
    - "Recommended First 5 Issues to Pick Up".
  - Endpoint: `GET /api/v1/repos/{id}/onboarding-guide`.
- **Acceptance Criteria**:
  - [ ] Guide renders in a dedicated "Onboarding" tab in the web UI.
  - [ ] Interactive checklist allowing new developers to mark completed milestones.
  - [ ] Downloadable as a standalone `ONBOARDING.md` file.

---

### Issue #067: `[FEAT]: "Good First Issue" Matcher Based on AST Isolation & Low In-Degree`
- **Labels**: `phase:phase-3-ai-docs`, `type:feature`, `priority:P1-high`, `component:mapping-engine`, `status:ready`
- **Milestone**: `M3: AI & Docs`
- **Component**: `apps/api/services/mapping/good_first_issue.py`
- **Problem Statement**:
  New contributors often pick up issues that seem simple in text but actually require altering high-risk architectural hubs, leading to abandoned PRs.
- **Technical Specification**:
  - Map open GitHub issues to code candidates using the 5-signal engine.
  - Evaluate mapped files for architectural risk:
    - Low in-degree centrality ($< 3$ dependents).
    - Low cyclomatic complexity ($< 8$).
    - Well-covered by existing unit tests ($> 80\%$ file coverage).
  - Score issues by contributor accessibility and tag with "Good First Issue" badge.
- **Acceptance Criteria**:
  - [ ] Recommends safe, isolated tasks that minimize breaking changes.
  - [ ] Explains why the issue is suitable for a beginner.
  - [ ] Filters out issues that touch core authentication or database schemas.

---

### Issue #068: `[FEAT]: RAG Context Assembly Pipeline with Strict Token Budgeting`
- **Labels**: `phase:phase-3-ai-docs`, `type:feature`, `priority:P0-critical`, `component:ai-rag`, `status:completed`
- **Milestone**: `M3: AI & Docs`
- **Component**: `apps/api/services/ai/rag.py`
- **Existing Implementation**: [apps/api/services/ai/](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/services/ai/)
- **Problem Statement**:
  Feeding full repository files into local LLM context windows (4k - 8k tokens) causes prompt truncation and model confusion. Context must be selectively assembled.
- **Technical Specification**:
  - Retrieve top-$K$ candidate nodes using vector cosine search.
  - Expand candidates to include their direct signatures, docstrings, and 1-hop caller paths.
  - Token budget manager: Limit retrieved context chunks to 3,000 tokens maximum.
  - Construct structured RAG prompt with numbered file reference snippets (`[Doc 1: apps/api/auth.py]`).
- **Acceptance Criteria**:
  - [x] Fits within configured token budget without dropping critical signatures.
  - [x] Formats context with clean code blocks and line numbers.
  - [x] Includes relevant directory summaries for high-level questions.

---

### Issue #069: `[FEAT]: Streaming Server-Sent Events (SSE) Chat API Endpoint`
- **Labels**: `phase:phase-3-ai-docs`, `type:feature`, `priority:P0-critical`, `component:apps/api`, `status:completed`
- **Milestone**: `M3: AI & Docs`
- **Component**: `apps/api/routers/chat.py`
- **Existing Implementation**: [apps/api/routers/chat.py](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/routers/chat.py)
- **Problem Statement**:
  Waiting 15 seconds for a complete LLM response causes perceived lag. Streaming tokens provides instant feedback to the user.
- **Technical Specification**:
  - Implement `POST /api/v1/repos/{id}/chat` returning `text/event-stream`.
  - Stream chunks formatted as SSE: `data: {"token": "...", "done": false}\n\n`.
  - Final chunk sends metadata: `{"done": true, "citations": [...], "session_id": "..."}`.
  - Client handles disconnects and aborts upstream Ollama stream cleanly.
- **Acceptance Criteria**:
  - [x] First token appears within 800ms of prompt submission.
  - [x] Connection properly closes when generation finishes.
  - [x] Frontend stream rendering handles markdown code blocks and syntax highlighting smoothly.

---

### Issue #070: `[FEAT]: Grounded Code Citation Linking with Exact [file:line] References`
- **Labels**: `phase:phase-3-ai-docs`, `type:feature`, `priority:P0-critical`, `component:ai-rag`, `status:completed`
- **Milestone**: `M3: AI & Docs`
- **Component**: `apps/api/services/ai/citations.py`, `apps/web/src/components/panels/ChatPanel.tsx`
- **Existing Implementation**: [apps/web/src/components/panels/](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/web/src/components/panels/)
- **Problem Statement**:
  AI chat answers that don't cite exact file locations cannot be trusted by engineers verifying codebase mechanics.
- **Technical Specification**:
  - Instruct LLM prompt to cite code locations using strict bracket notation: `[apps/api/auth.py#L45-L60]`.
  - Post-process LLM response text, verifying cited files actually exist in `code_nodes`.
  - Frontend renders citations as clickable pills:
    - Hovering displays quick code preview tooltip.
    - Clicking centers and highlights that file on the React Flow canvas.
- **Acceptance Criteria**:
  - [x] All claims in chat answers anchored to real file paths.
  - [x] Hallucinated/non-existent paths automatically scrubbed or flagged.
  - [x] Clicking citation navigates directly to source code location.

---

### Issue #071: `[FEAT]: Conversational Chat Session Persistence & Multi-Turn History Cache`
- **Labels**: `phase:phase-3-ai-docs`, `type:feature`, `priority:P1-high`, `component:apps/api`, `status:completed`
- **Milestone**: `M3: AI & Docs`
- **Component**: `apps/api/routers/chat.py`, `apps/api/models/`
- **Existing Implementation**: [apps/api/routers/chat.py](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/routers/chat.py)
- **Problem Statement**:
  Engineers ask follow-up questions ("What calls that?", "How do I test it?") that require full multi-turn conversational context.
- **Technical Specification**:
  - `GET /api/v1/repos/{id}/chat/sessions`: List past conversation threads.
  - `GET /api/v1/repos/{id}/chat/sessions/{id}`: Load thread message history.
  - Persist user queries, assistant responses, and citations in `chat_messages` table.
  - Cache active session in Redis with 24-hour sliding TTL.
- **Acceptance Criteria**:
  - [x] Multi-turn dialog retains context of previously mentioned functions and files.
  - [x] Users can revisit past chat sessions from sidebar.
  - [x] Deleting a session cascades cleanly through related messages.

---

### Issue #072: `[FEAT]: Hallucination Guardrails & Refusal Protocol for Out-of-Domain Queries`
- **Labels**: `phase:phase-3-ai-docs`, `type:security`, `priority:P1-high`, `component:ai-rag`, `status:ready`
- **Milestone**: `M3: AI & Docs`
- **Component**: `apps/api/services/ai/guardrails.py`
- **Problem Statement**:
  When users ask questions about functionality that does not exist in the codebase, the LLM must not invent non-existent APIs or files.
- **Technical Specification**:
  - Check semantic similarity distance of top retrieved code chunks.
  - If top cosine distance $< 0.45$: Trigger refusal protocol:
    *"I could not find any code related to '{query}' in this repository. Here are the closest architectural areas..."*
  - Guardrail prompt instructing model to never fabricate filenames or functions not present in the provided context.
- **Acceptance Criteria**:
  - [ ] Confidently admits when a concept or feature is absent from the repo.
  - [ ] Zero fabricated file paths in chat output.
  - [ ] Suggests related search terms when query has low similarity.

---

### Issue #073: `[FEAT]: Automated Architectural Drift Detection on Git Push Webhook`
- **Labels**: `phase:phase-3-ai-docs`, `type:feature`, `priority:P1-high`, `component:apps/api`, `status:ready`
- **Milestone**: `M3: AI & Docs`
- **Component**: `apps/api/services/ingestion/drift_detector.py`
- **Problem Statement**:
  As code changes, architectural documentation and summaries drift out of sync with actual implementations.
- **Technical Specification**:
  - During incremental push webhook processing, identify nodes whose AST signatures or call hierarchies changed.
  - Flag corresponding `summaries` records as `is_stale = true`.
  - Background Celery task re-generates summaries asynchronously for stale nodes.
  - Log architectural changes: added routes, deleted models, new cross-package dependencies.
- **Acceptance Criteria**:
  - [ ] Automatically detects when an existing documentation summary is outdated.
  - [ ] Re-summarizes modified components without requiring full repository re-ingestion.
  - [ ] Emits drift notification to repository maintainers.

---

### Issue #074: `[FEAT]: Scheduled Weekly Repository Full Re-Analysis Celery Beat Task`
- **Labels**: `phase:phase-3-ai-docs`, `type:infra`, `priority:P2-medium`, `component:apps/api`, `status:ready`
- **Milestone**: `M3: AI & Docs`
- **Component**: `apps/api/tasks/scheduled_tasks.py`
- **Problem Statement**:
  Over time, edge-case incremental sync misses or database drift can accumulate. Periodic full reconciliation ensures graph integrity.
- **Technical Specification**:
  - Configure Celery Beat scheduler with weekly cron trigger (`0 2 * * 0` — Sunday at 2 AM).
  - Query all active repositories and enqueue background full re-analysis jobs with low priority.
  - Re-compute complexity scores, degree centralities, and refresh vector index embeddings.
- **Acceptance Criteria**:
  - [ ] Scheduled tasks execute reliably without manual intervention.
  - [ ] Throttled to 1 concurrent re-analysis to avoid saturating server CPU/GPU.
  - [ ] Emits telemetry log upon completion.

---

### Issue #075: `[FEAT]: Markdown & PDF Living Architecture Documentation Export Service`
- **Labels**: `phase:phase-3-ai-docs`, `type:feature`, `priority:P2-medium`, `component:apps/api`, `status:ready`
- **Milestone**: `M3: AI & Docs`
- **Component**: `apps/api/routers/export.py`
- **Problem Statement**:
  Engineering teams preparing for architectural reviews, client audits, or compliance certifications need offline documentation packages.
- **Technical Specification**:
  - `GET /api/v1/repos/{id}/export?format=markdown|pdf`:
    - Compiles full architecture summary, module descriptions, route catalogs, and Mermaid diagrams into a cohesive document.
    - PDF conversion using headless Chrome / WeasyPrint with dark-mode formatting.
  - Return downloadable file attachment with appropriate MIME type.
- **Acceptance Criteria**:
  - [ ] Generates clean, publication-ready PDF with table of contents and page numbers.
  - [ ] Markdown format renders cleanly on GitHub and Notion.
  - [ ] Includes generated timestamp, repository commit SHA, and author credits.

---

### Issue #076: `[FEAT]: Architectural Changelog Generator Between Git Releases & Tags`
- **Labels**: `phase:phase-3-ai-docs`, `type:feature`, `priority:P2-medium`, `component:apps/api`, `status:ready`
- **Milestone**: `M3: AI & Docs`
- **Component**: `apps/api/services/ai/changelog_generator.py`
- **Problem Statement**:
  Standard git changelogs only list commit messages ("fix typo", "update styles"). Architects need to know what *structural* capabilities were added, removed, or refactored.
- **Technical Specification**:
  - Compare AST graphs between tag $v1.0.0$ and tag $v1.1.0$.
  - Categorize architectural diffs:
    - New API endpoints & controllers.
    - New or modified database models & migrations.
    - Deprecated functions & removed classes.
    - New package dependencies.
  - Summarize changes using Ollama into high-level release notes.
- **Acceptance Criteria**:
  - [ ] Generates structural release notes highlighting high-level functional changes.
  - [ ] Links directly to changed AST nodes in the graph.
  - [ ] Can be published automatically to GitHub Releases via webhook.

---

### Issue #077: `[FEAT]: Contextual Chat Suggestion Chips Based on Canvas Selection`
- **Labels**: `phase:phase-3-ai-docs`, `type:frontend`, `priority:P2-medium`, `component:apps/web`, `status:ready`
- **Milestone**: `M3: AI & Docs`
- **Component**: `apps/web/src/components/panels/ChatPanel.tsx`
- **Problem Statement**:
  Users opening the chat panel often do not know what questions to ask. Dynamic suggestions lower cognitive barrier.
- **Technical Specification**:
  - When user selects a node on canvas, generate 3 contextual quick-prompt chips:
    - For Route node: *"What middleware protects this endpoint?"*, *"Show request/response schema"*.
    - For Model node: *"What services query this table?"*, *"Are there cascade delete risks?"*.
    - For Function node: *"How do I write a unit test for this?"*, *"Explain error handling"*.
  - Clicking a chip immediately submits the query to the chat stream.
- **Acceptance Criteria**:
  - [ ] Chips update dynamically based on the active node type.
  - [ ] Clicking a chip triggers streaming chat without manual typing.
  - [ ] Smooth horizontal scroll layout for chips above chat input.

---

### Issue #078: `[FEAT]: User Feedback Collector for AI Answer Quality & Citation Accuracy`
- **Labels**: `phase:phase-3-ai-docs`, `type:feature`, `priority:P2-medium`, `component:apps/api`, `status:ready`
- **Milestone**: `M3: AI & Docs`
- **Component**: `apps/api/routers/chat.py`
- **Problem Statement**:
  Continuously improving RAG retrieval accuracy and citation relevance requires telemetry on user satisfaction and hallucination reports.
- **Technical Specification**:
  - Thumbs up / Thumbs down buttons below every assistant chat message.
  - Optional modal on thumbs down: *"What was wrong?"* (Incorrect file citation, Hallucinated code, Outdated answer, Too vague).
  - Store rating and feedback tag in `chat_message_feedbacks` table.
  - Dashboard analytics metric tracking Chat Quality Score (CSAT).
- **Acceptance Criteria**:
  - [ ] User feedback recorded with message ID and timestamp.
  - [ ] Downvoted citations flagged for RAG retrieval algorithm fine-tuning.
  - [ ] Unobtrusive UI that does not disrupt conversational flow.
