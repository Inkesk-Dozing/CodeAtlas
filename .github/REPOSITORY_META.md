# GitHub Repository Profile & Discoverability Specification

This document provides the exact metadata, description, topics, and configuration required to maximize CodeAtlas discoverability, search indexing, and developer traffic across GitHub.

---

## 📌 Repository Description (About Field)

Paste the following into the GitHub repository **About** field (350 character maximum):

```text
AI-Augmented Monorepo Onboarding Engine — Turns any codebase into an interactive living architecture graph, answers engineering questions with RAG, and maps GitHub issues to exact code locations with a 5-signal ranking algorithm.
```

- **Website**: `https://github.com/Inkesk-Dozing/CodeAtlas#readme` (or `https://codeatlas.dev`)
- **Include in Home**: Checked ✅

---

## 🏷️ GitHub Topics (Tags)

GitHub allows up to **20 topics** per repository. Adding these elevates search rankings across the GitHub Explore directory and trending algorithms:

| # | Topic | Category | Search Volume / Intent |
|---|---|---|---|
| 1 | `codebase-visualization` | Core Functionality | Developers searching for architecture visualizers |
| 2 | `architecture-graph` | Core Functionality | Graph-based system modeling & topology |
| 3 | `monorepo` | Ecosystem | Monorepo navigation & cross-package analysis |
| 4 | `developer-tools` | Category | General software engineering tooling |
| 5 | `react-flow` | Technology | Interactive canvas visualization community |
| 6 | `ast-parser` | Technology | Tree-sitter & AST code analysis |
| 7 | `tree-sitter` | Technology | Fast multi-language syntax tree generation |
| 8 | `rag` | AI / LLM | Retrieval-Augmented Generation for code |
| 9 | `pgvector` | Database | Vector database indexing & embeddings in Postgres |
| 10 | `fastapi` | Technology | High-performance Python backend ecosystem |
| 11 | `nextjs` | Technology | Modern React frontend ecosystem |
| 12 | `turborepo` | Ecosystem | High-performance monorepo build system |
| 13 | `code-search` | Use Case | Semantic and structural source code search |
| 14 | `issue-mapping` | Use Case | Automated issue-to-code location mapping |
| 15 | `onboarding` | Use Case | Developer onboarding & codebase documentation |
| 16 | `knowledge-graph` | Data Model | Software relational graph networks |
| 17 | `software-architecture` | Domain | Software architecture mapping & design |
| 18 | `ollama` | Technology | Local air-gapped LLM code intelligence |
| 19 | `code-intelligence` | Domain | AI code understanding & static analysis |
| 20 | `celery` | Technology | Distributed background task processing |

---

## ⚡ Instant Configuration via GitHub CLI (`gh`)

Run the following command in terminal to update the repository's description, website, and all 20 topics immediately:

```bash
gh repo edit Inkesk-Dozing/CodeAtlas \
  --description "AI-Augmented Monorepo Onboarding Engine — Turns any codebase into an interactive living architecture graph, answers engineering questions with RAG, and maps GitHub issues to exact code locations with a 5-signal ranking algorithm." \
  --homepage "https://github.com/Inkesk-Dozing/CodeAtlas#readme" \
  --add-topic "codebase-visualization" \
  --add-topic "architecture-graph" \
  --add-topic "monorepo" \
  --add-topic "developer-tools" \
  --add-topic "react-flow" \
  --add-topic "ast-parser" \
  --add-topic "tree-sitter" \
  --add-topic "rag" \
  --add-topic "pgvector" \
  --add-topic "fastapi" \
  --add-topic "nextjs" \
  --add-topic "turborepo" \
  --add-topic "code-search" \
  --add-topic "issue-mapping" \
  --add-topic "onboarding" \
  --add-topic "knowledge-graph" \
  --add-topic "software-architecture" \
  --add-topic "ollama" \
  --add-topic "code-intelligence" \
  --add-topic "celery"
```

---

## 🖼️ Social Preview Image Guidelines

To achieve maximum CTR (Click-Through Rate) on social shares (Twitter/X, LinkedIn, Discord):
1. **Resolution**: `1280 x 640` px (2:1 aspect ratio).
2. **Foreground Content**:
   - Dark mode CodeAtlas React Flow canvas showing a live graph with glowing dependency edges.
   - Prominent badge: *"AI-Augmented Monorepo Onboarding Engine"*.
   - Key tech badges: `FastAPI` • `Next.js 14` • `React Flow` • `pgvector` • `Ollama`.
3. Upload via **Settings -> General -> Social preview -> Edit**.
