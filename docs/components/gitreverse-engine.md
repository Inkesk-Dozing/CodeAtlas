# GitReverse & AI Context Packager Component Specification

## Purpose
The GitReverse & AI Context Packager component automates the extraction and packaging of codebase architecture, git evolution, and AST dependency hierarchies into optimized prompt bundles for AI coding assistants and autonomous agents. It generates standardized project-level agent instructions (`AGENTS.md`), editor rules (`.cursorrules`), LLM context indexes (`llms.txt`), and subgraph prompt packs for targeted refactoring tasks.

## System Dependencies
- **Tree-Sitter AST & Graph Engine**: Extraction of public symbols, type signatures, interfaces, and cross-package call boundaries.
- **Git Analytics Subsystem**: Summarization of recent PR decisions, architectural drift, and design conventions.
- **FastAPI (`routers/prompts.py`)**: Endpoints for token-budgeted prompt generation, file exports, and format conversions.
- **Token Estimation Utility**: Accurate BPE token calculation (using `tiktoken` or HuggingFace tokenizers) to fit LLM context limits ($8\text{k}$, $32\text{k}$, $128\text{k}$, $1\text{M}$ tokens).
- **React UI (`apps/web`)**: Interactive prompt packaging drawer, token budget slider, AST subtree selector, and one-click copy/download modal.

## Big-O Algorithmic Complexity

| Operation | Time Complexity | Space Complexity | Description |
|---|---|---|---|
| Hierarchical AST Context Assembly | $O(V_{\text{sub}} + E_{\text{sub}})$ | $O(V_{\text{sub}})$ | Traversing selected subgraph to extract class/function signatures and relationships |
| Token Budget Pruning | $O(K \log K)$ | $O(K)$ | Priority-queue pruning of $K$ candidate AST nodes based on centrality and relevance score |
| `AGENTS.md` Synthesis | $O(P)$ | $O(P)$ | Compiling project overview, architectural boundaries, and guidelines across $P$ packages |
| Subgraph Interface Contract Synthesis| $O(E_{\text{cut}})$ | $O(E_{\text{cut}})$ | Extracting typed interface contracts crossing the boundary edges $E_{\text{cut}}$ of a selected module |

## Export Formats & Generation Targets

### 1. `AGENTS.md` (Standardized Autonomous Agent Guidelines)
- Documents repository layout, monorepo boundaries, testing conventions, and prohibited architectural anti-patterns.
- Formatted specifically for consumption by autonomous multi-agent systems and coding agents.

### 2. `.cursorrules` (Targeted Cursor & IDE Assistant Rules)
- Generates precise, project-specific context instructions for Cursor, Windsurf, Copilot, and Claude Dev.
- Injects exact package boundary rules and import prohibitions extracted from `codeatlas.config.json`.

### 3. `llms.txt` (Standardized LLM Documentation Index)
- Generates a lightweight, structured markdown sitemap of the codebase adhering to the `llms.txt` standard.
- Enables external AI systems to selectively fetch modular documentation without indexing the entire raw repository.

### 4. Subgraph Prompt-to-Reconstruct
- Packages a selected component node, its immediate 1-hop dependencies, and caller interface contracts into a self-contained prompt.
- Allows developers to ask an external LLM to safely refactor or migrate a component with zero out-of-context hallucinations.

