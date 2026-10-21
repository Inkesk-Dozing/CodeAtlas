# CodeAtlas - Product Requirements Document (PRD)

## Document Information
| Field | Value |
|-------|-------|
| Version | 1.0 |
| Status | Draft |
| Last Updated | 2026-10-05 |
| Owner | Product Team |

---

## 1. Executive Summary

### Problem Statement
New developers joining engineering teams or open-source projects take **weeks** to become productive. Existing documentation (READMEs, wikis, architecture docs) becomes stale within days of creation. There is no automated way to:
- Visualize the architecture of a complex monorepo
- Map GitHub Issues to the exact files/components that need modification
- Query a codebase in natural language

### Solution
CodeAtlas is a GitHub-integrated platform that automatically:
1. **Maps** repository architecture into an interactive visual graph
2. **Explains** what each module/directory/component does using AI
3. **Connects** GitHub Issues to affected code areas with confidence scores
4. **Answers** natural language questions about the codebase

### Value Proposition
> "Reduce onboarding time from weeks to hours with an AI-powered architecture map that stays in sync with your codebase."

---

## 2. Target Users & Personas

### Persona 1: New Developer (Primary)
```
Name: Alex
Role: Junior/Mid-level developer, 1-3 years experience
Context: Just joined a company or open-source project
Goals:
  - Understand the codebase structure quickly
  - Find where to make changes for assigned issues
  - Learn architectural patterns and conventions
Pain Points:
  - Documentation is outdated or missing
  - Asking senior developers for every question feels bad
  - Monorepo structure is confusing (packages, apps, libs)
Success: Makes first meaningful contribution within 1-2 days
```

### Persona 2: Tech Lead / Onboarding Manager
```
Name: Sarah
Role: Tech lead, team of 5-10 engineers
Context: Onboarding 2-4 new hires per quarter
Goals:
  - Reduce time spent answering "where is X?" questions
  - Ensure new hires understand architecture before making changes
  - Maintain living documentation
Pain Points:
  - Repetitive onboarding questions
  - No single source of truth for architecture
  - Documentation goes stale immediately
Success: 80% reduction in onboarding questions
```

### Persona 3: Open Source Contributor
```
Name: Priya
Role: Student / hobbyist contributor
Context: Wants to contribute to a large OSS project
Goals:
  - Find "good first issues"
  - Understand project structure before contributing
  - Get oriented without reading entire codebase
Pain Points:
  - Large codebases are intimidating
  - No visual overview of the project
  - Unclear how components relate to each other
Success: Successfully submits first PR within hours
```

### Persona 4: Consultant / Auditor
```
Name: Marcus
Role: Engineering consultant
Context: Needs to audit unfamiliar codebases quickly
Goals:
  - Rapidly understand architecture of client codebases
  - Identify complexity hotspots
  - Generate architecture documentation
Pain Points:
  - Limited time with each codebase
  - Manual architecture diagramming is slow
  - Need to produce deliverables quickly
Success: Generates architecture review in 1 day vs 1 week
```

---

## 3. User Stories & Requirements

### Epic 1: Authentication & Repository Selection

| ID | Story | Priority | Acceptance Criteria |
|----|-------|----------|---------------------|
| AUTH-01 | As a user, I can log in with GitHub OAuth | P0 | Redirect to GitHub → callback → dashboard. Session persists 30 days. |
| AUTH-02 | As a user, I can install the GitHub App on my repositories | P0 | GitHub App installation flow → webhook received → repos listed. |
| AUTH-03 | As a user, I can see a list of my accessible repositories | P0 | Paginated list showing name, language, analysis status. |
| AUTH-04 | As a user, I can select a repository to analyze | P0 | Click repo → triggers ingestion → shows progress. |
| AUTH-05 | As a user, I can see which org I belong to | P1 | Org name displayed in header, with role (admin/member/viewer). |
| AUTH-06 | As an admin, I can invite team members | P2 | Email invite → accept → joined with role. |

### Epic 2: Repository Ingestion

| ID | Story | Priority | Acceptance Criteria |
|----|-------|----------|---------------------|
| ING-01 | As a user, I can trigger a full repository analysis | P0 | Click "Analyze" → progress bar shows 5 stages → completes < 10 min for 1k files. |
| ING-02 | As a user, I can see ingestion progress in real-time | P0 | Live progress: clone → parse → extract → embed → persist. WebSocket updates. |
| ING-03 | As a user, I receive automatic updates when code changes | P0 | Push to main → webhook triggers incremental update < 60s. |
| ING-04 | As a user, I can see ingestion history | P1 | List of past analyses with status, duration, node count. |
| ING-05 | As a user, I can configure ignored paths | P1 | Edit `ignored_paths` in settings → next ingestion skips them. |
| ING-06 | As a user, I can see ingestion errors | P1 | Failed files listed with error messages, retry button. |
| ING-07 | As a user, I can cancel a running ingestion | P2 | Cancel button → graceful stop → status = cancelled. |

### Epic 3: Interactive Architecture Graph

| ID | Story | Priority | Acceptance Criteria |
|----|-------|----------|---------------------|
| GRP-01 | As a user, I can see a visual graph of the repository structure | P0 | Nodes for files/dirs/functions/classes/routes/components/models. Edges for dependencies. |
| GRP-02 | As a user, I can click a node to see details | P0 | Sidebar shows: name, path, complexity, docstring, imports/exports, code preview. |
| GRP-03 | As a user, I can filter nodes by type | P0 | Filter panel: show/hide by type (routes, components, models, etc.). |
| GRP-04 | As a user, I can filter by language | P1 | Toggle TypeScript, Python, Go, etc. |
| GRP-05 | As a user, I can search within the graph | P0 | Search box → highlights matching nodes → centers viewport. |
| GRP-06 | As a user, I can zoom and pan the graph | P0 | Mouse wheel zoom, drag pan, minimap, zoom-to-fit. |
| GRP-07 | As a user, I can switch layout algorithms | P1 | Dropdown: hierarchical, force-directed, circular. |
| GRP-08 | As a user, I can see node clusters (directories) | P1 | Directories shown as collapsible clusters. Double-click to expand. |
| GRP-09 | As a user, I can see edge labels | P1 | Hover edge → shows type (imports, calls, renders). |
| GRP-10 | As a user, I can see the graph at 60fps with 2000+ nodes | P0 | Virtualized rendering, no lag on pan/zoom. |
| GRP-11 | As a user, I can share a link to a specific node | P2 | Copy link → opens graph centered on that node. |
| GRP-12 | As a user, I can export the graph as PNG/SVG | P2 | Download button → image export. |

### Epic 4: Issue-to-Code Mapping

| ID | Story | Priority | Acceptance Criteria |
|----|-------|----------|---------------------|
| ISS-01 | As a user, I can see a list of GitHub issues | P0 | Issues fetched from GitHub, showing number, title, labels, state. |
| ISS-02 | As a user, I can click an issue to see affected code | P0 | Click issue → analysis runs → graph highlights mapped nodes with confidence scores. |
| ISS-03 | As a user, I can see confidence scores for each mapping | P0 | High (≥0.8), Medium (0.5-0.8), Low (0.3-0.5) tiers shown. |
| ISS-04 | As a user, I can see why a file was mapped | P1 | Evidence shown: semantic match, structural match, matched keywords. |
| ISS-05 | As a user, I can submit feedback on mappings | P1 | Thumbs up/down on each mapping → stored for retraining. |
| ISS-06 | As a user, I can see suggested actions | P1 | "Modify this route handler", "Update this model", etc. |
| ISS-07 | As a user, I can force re-analysis of an issue | P1 | Refresh button → re-runs mapping with latest code. |
| ISS-08 | As a user, I can see mapping accuracy improves over time | P2 | Accuracy metric displayed, improves with feedback. |

**Acceptance for ISS-02:**
- Analysis completes in < 2 seconds
- At least 1 high-confidence mapping for issues with explicit file references
- Graph highlights affected nodes with color-coded confidence

### Epic 5: Semantic Search

| ID | Story | Priority | Acceptance Criteria |
|----|-------|----------|---------------------|
| SRC-01 | As a user, I can ask natural language questions | P0 | Input: "Where is auth middleware?" → Returns relevant files with context. |
| SRC-02 | As a user, I can filter search results by type | P1 | Toggle: only show routes, only show components, etc. |
| SRC-03 | As a user, I can see search results on the graph | P0 | Search → matching nodes highlighted, others dimmed. |
| SRC-04 | As a user, I can combine semantic and keyword search | P1 | Hybrid results with relevance scores. |
| SRC-05 | As a user, I can see a snippet of why a result matched | P1 | Show relevant code/docstring excerpt. |

### Epic 6: AI Summarization & Documentation

| ID | Story | Priority | Acceptance Criteria |
|----|-------|----------|---------------------|
| SUM-01 | As a user, I can see auto-generated directory summaries | P0 | Click directory → 2-3 sentence summary of purpose, key exports. |
| SUM-02 | As a user, I can see architecture overview | P1 | Generated Markdown: modules, dependencies, entry points. |
| SUM-03 | As a user, I can see code complexity metrics | P1 | Cyclomatic complexity, cognitive complexity, maintainability score. |
| SUM-04 | As a user, I can see complexity hotspots | P1 | Top 10 most complex functions/classes highlighted. |
| SUM-05 | As a user, I can chat with the codebase | P1 | Q&A interface: "How does payment processing work?" → Answer with citations. |
| SUM-06 | As a user, I can see an onboarding guide | P1 | Auto-generated: key areas, first issues to pick up, architecture tour. |
| SUM-07 | As a user, I can export documentation to Markdown | P2 | Download button → .md file. |
| SUM-08 | As a user, I can sync docs to Notion/Confluence | P3 | Integration setup → auto-sync on analysis complete. |

### Epic 7: Multi-tenancy & Administration

| ID | Story | Priority | Acceptance Criteria |
|----|-------|----------|---------------------|
| ADM-01 | As an admin, I can create an organization | P1 | Create org → invite members. |
| ADM-02 | As an admin, I can manage member roles | P1 | Change role: admin/member/viewer. |
| ADM-03 | As an admin, I can see usage dashboard | P1 | Repos analyzed, API calls, storage used. |
| ADM-04 | As an admin, I can set quotas | P2 | Max repos, max analyses/month, max API calls/day. |
| ADM-05 | As an admin, I can manage billing | P2 | Stripe integration → view invoices, upgrade plan. |
| ADM-06 | As an admin, I can view audit logs | P2 | All actions logged with timestamp, user, resource. |

---

## 4. Non-Functional Requirements

### Performance
| Metric | Target | Priority |
|--------|--------|----------|
| Graph render (500 nodes) | < 1 second | P0 |
| Graph render (2000 nodes) | < 2 seconds, 60fps | P0 |
| Graph query API | < 100ms p95 | P0 |
| Semantic search | < 50ms p95 | P0 |
| Issue mapping analysis | < 2 seconds | P0 |
| Full ingestion (1000 files) | < 5 minutes | P0 |
| Incremental ingestion | < 60 seconds | P0 |
| Page load (dashboard) | < 2 seconds | P1 |

### Scalability
| Dimension | Target |
|-----------|--------|
| Concurrent users | 1000+ |
| Repos per organization | 100+ |
| Nodes per graph | 5000+ |
| Files per repository | 50,000+ |
| API requests/second | 1000+ |

### Reliability
| Metric | Target |
|--------|--------|
| API uptime | 99.9% |
| Data durability | 99.999999999% (11 nines) |
| Ingestion success rate | 99% |
| Recovery Time Objective (RTO) | < 1 hour |
| Recovery Point Objective (RPO) | < 5 minutes |

### Security
- SOC 2 Type II compliance (Phase 4)
- GDPR compliant (data deletion, export)
- OWASP Top 10 addressed
- Penetration test before launch
- Encryption at rest and in transit

### Usability
- Time to first graph: < 5 minutes from signup
- Onboarding flow: < 3 steps
- Accessibility: WCAG 2.1 AA
- Browser support: Chrome, Firefox, Safari, Edge (latest 2 versions)
- Responsive: Desktop-first, tablet-optimized

---

## 5. Success Metrics (KPIs)

### Product Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| Onboarding time reduction | 80%+ | Time from signup to first contribution (survey) |
| Issue resolution time | 40% reduction | Time from issue assignment to PR |
| User activation rate | 60% | Users who analyze a repo within 24h of signup |
| Weekly active users | 1000+ | WAU within 6 months of launch |
| NPS score | 50+ | Quarterly survey |

### Engagement Metrics
| Metric | Target |
|--------|--------|
| Repos analyzed/week | 500+ |
| Issues mapped/week | 2000+ |
| Search queries/day | 5000+ |
| Chat sessions/week | 500+ |
| Mapping feedback rate | 30% of mappings rated |
| Mapping accuracy | > 75% (Precision@5) |

### Business Metrics (Phase 4+)
| Metric | Target |
|--------|--------|
| Free → paid conversion | 5% |
| Monthly recurring revenue | $10K by month 6 |
| Churn rate | < 5% monthly |
| Customer acquisition cost | < $200 |

---

## 6. Competitive Analysis

| Feature | CodeAtlas | Sourcegraph | GitKraken | CodeSee | Traditional Docs |
|---------|-----------|-------------|-----------|--------|------------------|
| Interactive graph | ✅ | ❌ | ❌ | ✅ | ❌ |
| Issue → code mapping | ✅ | ❌ | ❌ | ❌ | ❌ |
| Semantic search | ✅ | ✅ | ❌ | ❌ | ❌ |
| AI summaries | ✅ | ✅ | ❌ | ❌ | ❌ |
| Monorepo support | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| Auto-updating | ✅ | ✅ | ✅ | ✅ | ❌ |
| Natural language Q&A | ✅ | ✅ | ❌ | ❌ | ❌ |
| Open source | Planned | ❌ | ❌ | ❌ | ✅ |
| Free tier | ✅ | ✅ | ✅ | ✅ | ✅ |
| Price (team) | $29/mo | $29/user/mo | $14/user/mo | Custom | Free |

### Differentiation
1. **Issue-to-code mapping** — No competitor offers this with confidence scores
2. **Monorepo-first** — Purpose-built for Turborepo/pnpm workspaces
3. **Interactive graph** — Visual, explorable architecture map
4. **Feedback loop** — Mapping accuracy improves with usage
5. **Free tier** — Generous for students and OSS contributors

---

## 7. Phased Delivery

### MVP (Phase 0-1, Weeks 1-5)
**Goal**: Working ingestion pipeline and basic graph

Must-have:
- GitHub OAuth + App installation
- Repository cloning and parsing (TS/JS, Python)
- Basic graph with file/directory/function/class nodes
- React Flow canvas with zoom/pan/click
- Node detail panel

Nice-to-have:
- Incremental updates via webhook
- Progress indicators during ingestion

### Beta (Phase 2, Weeks 6-8)
**Goal**: Issue mapping and search work end-to-end

Must-have:
- Issue fetch and analysis pipeline
- Semantic issue-to-code mapping with confidence scores
- Graph highlighting for mapped nodes
- Natural language search
- Feedback collection (thumbs up/down)

### V1.0 (Phase 3, Weeks 9-11)
**Goal**: AI features and documentation generation

Must-have:
- Directory/module summaries
- Complexity analysis
- Architecture overview generation
- Chat interface (codebase Q&A)
- Onboarding guide generation

### V2.0 (Phase 4, Weeks 12-16)
**Goal**: Production-ready SaaS

Must-have:
- Multi-tenant organizations
- RBAC (admin/member/viewer)
- Billing (Stripe)
- Admin dashboard
- E2E test coverage
- Security audit
- Documentation site

### Future (Phase 5+)
- Diff visualization (branch/PR comparison)
- Impact analysis ("what breaks if I change this?")
- IDE extension (VS Code)
- Slack/Discord bot
- Team knowledge graph (ownership)
- Compliance reporting (licenses, security)

---

## 8. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| GitHub API rate limits | High | Medium | Installation tokens, caching, backoff |
| Large repo ingestion timeout | High | High | Chunked processing, checkpoints, streaming |
| Embedding quality insufficient | Medium | High | Fine-tune, hybrid search, human feedback |
| React Flow performance at scale | Medium | High | Virtualization, clustering, WebGL fallback |
| Multi-tenant data leakage | Low | Critical | RLS, penetration testing, audit logs |
| LLM hallucination in summaries | Medium | Medium | Citations, confidence scores, human review |
| Competitor launches first | Medium | Medium | Focus on monorepo + issue mapping niche |
| Low user activation | Medium | High | In-app guidance, templates, quick wins |
| Cost overrun (LLM inference) | Medium | Medium | Local models, caching, usage-based pricing |

---

## 9. Open Questions

| # | Question | Owner | Deadline |
|---|----------|-------|----------|
| 1 | PostgreSQL+pgvector vs Supabase? | Backend | Week 1 |
| 2 | Local LLM (Ollama) vs API (OpenAI)? | ML | Week 2 |
| 3 | Free tier limits? | Product | Week 3 |
| 4 | Self-hosted offering? | Product | Phase 4 |
| 5 | Pricing model: per-seat vs per-repo? | Product | Phase 4 |

---

## 10. Appendices

### Glossary
| Term | Definition |
|------|------------|
| Monorepo | Single repository containing multiple projects/packages |
| AST | Abstract Syntax Tree — structural representation of code |
| pgvector | PostgreSQL extension for vector similarity search |
| Embedding | Numeric vector representation of text for similarity comparison |
| HNSW | Hierarchical Navigable Small World — efficient vector index |
| RLS | Row-Level Security — database-level multi-tenant isolation |
| RAG | Retrieval-Augmented Generation — LLM pattern using search results |

### References
- [React Flow Documentation](https://reactflow.dev)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [Tree-sitter Documentation](https://tree-sitter.github.io)
- [GitHub Apps Documentation](https://docs.github.com/en/apps)
- [Turborepo Documentation](https://turbo.build)