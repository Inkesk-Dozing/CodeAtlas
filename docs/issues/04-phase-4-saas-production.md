# Phase 4 Issues: Multi-Tenant SaaS, Security & Production Polish

This document details all Phase 4 issues for CodeAtlas covering multi-tenant organization isolation, PostgreSQL Row-Level Security (RLS), Stripe subscription billing, quota enforcement, developer API keys, audit logging, Playwright E2E testing, and production deployment orchestration.

---

### Issue #079: `[FEAT]: Organization & Workspace Multi-Tenant Relational Data Model`
- **Labels**: `phase:phase-4-saas`, `type:feature`, `priority:P0-critical`, `component:apps/api`, `status:completed`
- **Milestone**: `M4: Beta Launch`
- **Component**: `apps/api/models/organization.py`, `apps/api/migrations/0001_initial.py`
- **Existing Implementation**: [apps/api/models/](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/models/)
- **Problem Statement**:
  CodeAtlas must support teams and enterprises with shared repository access, shared billing, and strict data isolation across accounts.
- **Technical Specification**:
  - Tables: `organizations`, `organization_members`, `workspaces`.
  - Organization fields: `id`, `name`, `slug`, `avatar_url`, `plan_tier`, `created_at`.
  - Member fields: `id`, `org_id`, `user_id`, `role` (`owner`, `admin`, `member`, `viewer`).
  - Foreign key relations linking `repositories` and `chat_sessions` to `organization_id`.
- **Acceptance Criteria**:
  - [x] Unique slug per organization with URL slug validation.
  - [x] Cascade delete rules prevent orphaned repositories when organization is deleted.
  - [x] Database indexes on `(org_id, user_id)` for high-speed permission lookups.

---

### Issue #080: `[SEC]: PostgreSQL Row-Level Security (RLS) Tenant Isolation Policies`
- **Labels**: `phase:phase-4-saas`, `type:security`, `priority:P0-critical`, `component:apps/api`, `status:ready`
- **Milestone**: `M4: Beta Launch`
- **Component**: `apps/api/migrations/0002_row_level_security.py`
- **Problem Statement**:
  Application-level tenant filtering (`WHERE org_id = ...`) is susceptible to developer oversights that could leak confidential proprietary source code between organizations.
- **Technical Specification**:
  - Enable PostgreSQL Row-Level Security on `repositories`, `code_nodes`, `code_edges`, `issues`, `chat_sessions`.
  - Set current tenant context on every async database session checkout:
    `SET LOCAL app.current_org_id = :org_id`.
  - Define RLS policy:
    `CREATE POLICY tenant_isolation_policy ON repositories USING (org_id = NULLIF(current_setting('app.current_org_id', true), '')::uuid)`.
- **Acceptance Criteria**:
  - [ ] Queries without valid `app.current_org_id` return zero rows.
  - [ ] Cross-tenant data leakage physically blocked at the database engine level.
  - [ ] Automated security tests verify cross-tenant access attempts fail.

---

### Issue #081: `[FEAT]: Role-Based Access Control (RBAC) Permission Middleware`
- **Labels**: `phase:phase-4-saas`, `type:security`, `priority:P0-critical`, `component:apps/api`, `status:ready`
- **Milestone**: `M4: Beta Launch`
- **Component**: `apps/api/middleware/rbac.py`
- **Problem Statement**:
  Organizations require granular permission enforcement: viewers should not trigger re-ingestions, members should not alter billing, and admins should manage users.
- **Technical Specification**:
  - Permission matrix:
    - `Viewer`: Read graph, run searches, view issues, chat with codebase.
    - `Member`: Trigger re-ingestions, submit mapping feedback, manage personal API keys.
    - `Admin`: Add/remove members, configure webhooks, change repo settings.
    - `Owner`: Manage Stripe subscription, delete organization, transfer ownership.
  - FastAPI dependency decorator: `@require_permission("repo:ingest")`.
- **Acceptance Criteria**:
  - [ ] Unauthorized actions reject with HTTP 403 Forbidden and descriptive error code.
  - [ ] Role hierarchy verified across all 29 API routes.
  - [ ] Role transitions take effect immediately across all active user sessions.

---

### Issue #082: `[FEAT]: Organization Member Invitation Flow with Cryptographic Signed Tokens`
- **Labels**: `phase:phase-4-saas`, `type:feature`, `priority:P1-high`, `component:apps/api`, `status:ready`
- **Milestone**: `M4: Beta Launch`
- **Component**: `apps/api/routers/invites.py`
- **Problem Statement**:
  Team administrators need a secure, friction-free way to invite colleagues to their CodeAtlas organization via email.
- **Technical Specification**:
  - `POST /api/v1/orgs/{id}/invites`: Generates HMAC-signed invite token with 7-day expiration.
  - Sends branded email invite via SendGrid / Resend with direct join link.
  - `POST /api/v1/invites/{token}/accept`: Validates signature, verifies user identity via GitHub OAuth, and adds member to organization.
- **Acceptance Criteria**:
  - [ ] Expired or tampered invite tokens reject with clear user feedback.
  - [ ] Prevents inviting users who are already active members.
  - [ ] Pending invites can be revoked or resent by organization admins.

---

### Issue #083: `[FEAT]: Stripe Subscription Billing Integration (Free, Pro & Enterprise Tiers)`
- **Labels**: `phase:phase-4-saas`, `type:feature`, `priority:P0-critical`, `component:apps/api`, `status:ready`
- **Milestone**: `M4: Beta Launch`
- **Component**: `apps/api/routers/billing.py`, `apps/api/services/billing/stripe_service.py`
- **Problem Statement**:
  Monetizing CodeAtlas requires self-serve subscription checkouts, pricing tier enforcement, customer portals, and automated billing.
- **Technical Specification**:
  - Pricing tiers:
    - **Community / Free**: 3 public repos, 50k nodes/repo, 100 AI chat queries/month.
    - **Pro ($29/mo)**: 15 private repos, 250k nodes/repo, unlimited chat, issue mapping.
    - **Enterprise (Custom)**: Unlimited repos, self-hosted Ollama runner, SSO, SLA.
  - Create Stripe Checkout sessions via `POST /api/v1/billing/checkout`.
  - Stripe Customer Portal redirect for payment method and invoice management.
- **Acceptance Criteria**:
  - [ ] Seamless redirect to Stripe hosted checkout and return handling.
  - [ ] Subscribed organizations updated immediately upon payment success.
  - [ ] Customers can download PDF invoices directly from the web portal.

---

### Issue #084: `[FEAT]: Usage Quota Enforcement & Real-Time Metering Service`
- **Labels**: `phase:phase-4-saas`, `type:feature`, `priority:P1-high`, `component:apps/api`, `status:ready`
- **Milestone**: `M4: Beta Launch`
- **Component**: `apps/api/services/billing/quotas.py`
- **Problem Statement**:
  Prevent users on Free or Pro tiers from exceeding their allotted repository count, graph node storage, or daily AI query limits.
- **Technical Specification**:
  - Track usage metrics in Redis counters with atomic increments (`INCRBY`).
  - Metrics tracked:
    - `org:{id}:repos:count` (hard limit).
    - `org:{id}:nodes:total` (storage limit).
    - `org:{id}:chat:daily` (rate quota, reset at midnight UTC).
  - Intercept ingestion and chat endpoints; return `402 Payment Required` with upgrade CTA if quota exceeded.
- **Acceptance Criteria**:
  - [ ] Enforces plan quotas with zero race conditions during concurrent requests.
  - [ ] Warning banner displayed in UI when organization reaches 80% of quota.
  - [ ] Upgrading plan instantly removes quota blocks without restart.

---

### Issue #085: `[FEAT]: Stripe Webhook Receiver & Subscription Lifecycle State Machine`
- **Labels**: `phase:phase-4-saas`, `type:security`, `priority:P0-critical`, `component:apps/api`, `status:ready`
- **Milestone**: `M4: Beta Launch`
- **Component**: `apps/api/routers/billing.py`
- **Problem Statement**:
  Subscription renewals, upgrades, cancellations, and payment failures occur asynchronously via Stripe webhooks and must be synchronized reliably.
- **Technical Specification**:
  - `POST /api/v1/webhooks/stripe`: Validates Stripe webhook signature using `STRIPE_WEBHOOK_SECRET`.
  - Handled events:
    - `customer.subscription.created` & `updated`: Update plan tier and billing cycle.
    - `customer.subscription.deleted`: Downgrade organization to Free tier.
    - `invoice.payment_failed`: Trigger dunning email sequence and mark account as past-due.
- **Acceptance Criteria**:
  - [ ] Idempotent processing using Stripe event IDs.
  - [ ] Returns HTTP 200 within 500ms to satisfy Stripe delivery constraints.
  - [ ] Grace period (3 days) before restricting features on payment failure.

---

### Issue #086: `[FEAT]: Organization Admin Dashboard & System Observability Portal`
- **Labels**: `phase:phase-4-saas`, `type:frontend`, `priority:P1-high`, `component:apps/web`, `status:ready`
- **Milestone**: `M4: Beta Launch`
- **Component**: `apps/web/src/app/admin/`, `apps/web/src/components/admin/`
- **Problem Statement**:
  Organization admins need visibility into team activity, repository health, ingestion queues, billing status, and error logs.
- **Technical Specification**:
  - Overview cards: Active Repositories, Total Nodes Mapped, Monthly Chat Queries, Current Plan.
  - Repository Health Table: Name, Ingestion Status, Last Sync, Edge Density, Error Rate.
  - Team Member Manager: Role dropdowns, remove member button, pending invites table.
  - Billing Tab: Current subscription, card on file, usage progress bars, upgrade buttons.
- **Acceptance Criteria**:
  - [ ] Responsive dashboard layout restricted to `Admin` and `Owner` roles.
  - [ ] Real-time updates reflecting new members and repository status changes.
  - [ ] Clean metric visualizations using Tailwind and SVG chart components.

---

### Issue #087: `[FEAT]: Ingestion Error Log Viewer & Dead-Letter Queue Management`
- **Labels**: `phase:phase-4-saas`, `type:frontend`, `priority:P1-high`, `component:apps/web`, `status:ready`
- **Milestone**: `M4: Beta Launch`
- **Component**: `apps/web/src/components/admin/ErrorLogs.tsx`
- **Problem Statement**:
  When ingestion fails on complex syntax or network timeouts, admins and engineers need access to sanitized tracebacks to resolve the issue.
- **Technical Specification**:
  - Log viewer displaying failed tasks with timestamp, repository name, failed file path, and exception trace.
  - Filter by error severity (`CRITICAL`, `ERROR`, `WARNING`) and error category (`PARSER`, `NETWORK`, `EMBEDDING`, `DATABASE`).
  - "Retry Ingestion" and "Dismiss" buttons per error record.
- **Acceptance Criteria**:
  - [ ] Scrub sensitive tokens, passwords, or personal data from error tracebacks before display.
  - [ ] Supports searching error logs by filename or error message substring.
  - [ ] One-click retry triggers Celery task restart.

---

### Issue #088: `[FEAT]: Public Developer API: Key Generation, SHA-256 Hashing & Revocation`
- **Labels**: `phase:phase-4-saas`, `type:security`, `priority:P0-critical`, `component:apps/api`, `status:ready`
- **Milestone**: `M4: Beta Launch`
- **Component**: `apps/api/routers/api_keys.py`, `apps/api/models/api_key.py`
- **Problem Statement**:
  Teams want to integrate CodeAtlas into external CI/CD workflows, custom bots, and IDE plugins using persistent developer API tokens (`ca_live_...`).
- **Technical Specification**:
  - `POST /api/v1/api-keys`: Generates high-entropy token (`ca_live_` prefix + 32 random bytes).
  - Display raw token *once* to user; store only salt and SHA-256 hash in `api_keys` table.
  - Support scoped permissions (`read:graph`, `read:issues`, `write:ingest`).
  - `DELETE /api/v1/api-keys/{id}`: Instantly revokes token and clears Redis auth cache.
- **Acceptance Criteria**:
  - [ ] Raw API keys never persisted in plain-text in database or server logs.
  - [ ] Authentication via `Authorization: Bearer ca_live_...` executes in < 5ms via Redis hash cache.
  - [ ] Token prefix allows instant detection by GitHub Secret Scanning.

---

### Issue #089: `[FEAT]: Tiered API Rate Limiting with Redis Sliding Window Counter`
- **Labels**: `phase:phase-4-saas`, `type:performance`, `priority:P1-high`, `component:apps/api`, `status:completed`
- **Milestone**: `M4: Beta Launch`
- **Component**: `apps/api/middleware.py`
- **Existing Implementation**: [apps/api/middleware.py](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/apps/api/middleware.py)
- **Problem Statement**:
  Prevent denial-of-service and fair-use violations by throttling API requests based on user identity, API key, and subscription tier.
- **Technical Specification**:
  - Redis sliding window log algorithm:
    - Free tier: 60 requests/minute.
    - Pro tier: 600 requests/minute.
    - Enterprise tier: 3,000 requests/minute.
  - Return standardized rate limit headers:
    `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.
  - HTTP 429 response when limit exceeded with `Retry-After` seconds header.
- **Acceptance Criteria**:
  - [x] Sliding window prevents burst attacks at boundary boundaries.
  - [x] Rate limit check executes in < 2ms using Redis pipeline.
  - [x] Internal health checks bypass rate limiting.

---

### Issue #090: `[SEC]: Enterprise Audit Logging Service for Compliance (SOC 2 Type II)`
- **Labels**: `phase:phase-4-saas`, `type:security`, `priority:P1-high`, `component:apps/api`, `status:ready`
- **Milestone**: `M4: Beta Launch`
- **Component**: `apps/api/services/audit.py`
- **Problem Statement**:
  Enterprise customers require immutable audit logs recording all authentication events, permission modifications, repository deletions, and API token generations.
- **Technical Specification**:
  - Table: `audit_logs` (append-only, immutable).
  - Record fields: `id`, `org_id`, `actor_user_id`, `action`, `resource_type`, `resource_id`, `ip_address`, `user_agent`, `payload_diff`, `timestamp`.
  - Export audit logs to S3 / MinIO in encrypted JSONL format for cold storage retention.
- **Acceptance Criteria**:
  - [ ] All administrative actions generate an immutable audit log entry.
  - [ ] Audit logs cannot be updated or deleted through the API.
  - [ ] Searchable audit trail accessible via organization admin portal.

---

### Issue #091: `[TEST]: Playwright End-to-End Test Suite: Authentication & Canvas Workflows`
- **Labels**: `phase:phase-4-saas`, `type:test`, `priority:P0-critical`, `component:apps/web`, `status:ready`
- **Milestone**: `M4: Beta Launch`
- **Component**: `apps/web/e2e/canvas.spec.ts`
- **Problem Statement**:
  Ensure user-facing critical paths (OAuth sign-in, repo selection, canvas rendering, node inspection) are verified against regressions before any production release.
- **Technical Specification**:
  - Implement Playwright test suite running against staging environment:
    - Test 1: GitHub OAuth login -> redirect to dashboard -> repo list rendered.
    - Test 2: Select repository -> canvas renders nodes -> minimap visible.
    - Test 3: Click node -> node detail sidebar opens with syntax-highlighted code.
    - Test 4: Drag canvas -> verify smooth viewport pan and zoom-to-fit behavior.
- **Acceptance Criteria**:
  - [ ] All tests run headless in CI GitHub Actions pipeline.
  - [ ] Automatic screenshot and video capture on test failure.
  - [ ] Zero flaky test failures across 10 consecutive test runs.

---

### Issue #092: `[TEST]: Playwright End-to-End Test Suite: Issue Mapping & Streaming Chat`
- **Labels**: `phase:phase-4-saas`, `type:test`, `priority:P0-critical`, `component:apps/web`, `status:ready`
- **Milestone**: `M4: Beta Launch`
- **Component**: `apps/web/e2e/mapping_chat.spec.ts`
- **Problem Statement**:
  Verify complex interactive workflows (clicking an issue, observing highlighted subgraph, asking a RAG question, receiving streamed citations) function seamlessly end-to-end.
- **Technical Specification**:
  - Test 1: Open issues drawer -> click issue -> assert green glowing nodes highlighted on canvas.
  - Test 2: Click "Thumbs Up" on mapping -> assert positive feedback toast and DB record.
  - Test 3: Type "Where is auth handled?" in chat -> assert streaming tokens render -> verify clickable citation links.
  - Test 4: Click citation pill -> assert canvas centers on cited file node.
- **Acceptance Criteria**:
  - [ ] Validates SSE streaming handling and UI token rendering in real browser.
  - [ ] Asserts DOM updates without race conditions or uncaught console errors.
  - [ ] Completes suite in < 45 seconds.

---

### Issue #093: `[PERF]: High-Concurrency Load Testing with Locust (100 Concurrent Ingestions)`
- **Labels**: `phase:phase-4-saas`, `type:performance`, `priority:P1-high`, `component:apps/api`, `status:ready`
- **Milestone**: `M4: Beta Launch`
- **Component**: `tests/load/locustfile.py`
- **Problem Statement**:
  Validate system throughput and stability under peak multi-tenant load (100 concurrent webhook push ingestions and 500 simultaneous search queries).
- **Technical Specification**:
  - Write Locust load test script simulating:
    - 100 concurrent Celery ingestion tasks.
    - 500 concurrent hybrid search requests.
    - 50 simultaneous streaming chat connections.
  - Measure response latencies (p50, p95, p99), CPU utilization, and PostgreSQL connection pool saturation.
- **Acceptance Criteria**:
  - [ ] p95 search latency remains < 150ms under sustained load.
  - [ ] Zero database connection timeout errors (`pool_size` tuned appropriately).
  - [ ] Celery task queue processes backlog without message drops or worker crashes.

---

### Issue #094: `[SEC]: OWASP Top 10 Security Audit, Penetration Test & Dependency Remediation`
- **Labels**: `phase:phase-4-saas`, `type:security`, `priority:P0-critical`, `component:apps/api`, `status:ready`
- **Milestone**: `M4: Beta Launch`
- **Component**: `docs/11-security.md`, `SECURITY.md`
- **Existing Implementation**: [docs/11-security.md](file:///C:/Users/USER/Desktop/Extras/pending-projects/CodeAtlas/docs/11-security.md)
- **Problem Statement**:
  Before public beta launch, the platform must be thoroughly audited against injection, broken access control, SSRF in webhook cloner, and XSS in markdown renderers.
- **Technical Specification**:
  - Audit checklist:
    - SQL injection: Verify all SQLAlchemy queries use parameterized statements.
    - SSRF: Restrict git clone URLs to verified `github.com` endpoints; block `localhost`/internal private IP ranges (`10.0.0.0/8`, `192.168.0.0/16`).
    - XSS: Sanitize rendered markdown in chat and node preview using `DOMPurify`.
    - CSRF: Enforce strict SameSite cookie policies.
- **Acceptance Criteria**:
  - [ ] Zero High or Critical CVEs in production dependency trees.
  - [ ] Git cloner rejects loopback or private network URLs.
  - [ ] Comprehensive penetration test report signed off and archived.

---

### Issue #095: `[DOCS]: Public Documentation Site Deployment (Nextra / Mintlify)`
- **Labels**: `phase:phase-4-saas`, `type:documentation`, `priority:P1-high`, `component:documentation`, `status:ready`
- **Milestone**: `M4: Beta Launch`
- **Component**: `docs/`, `apps/docs/`
- **Problem Statement**:
  Users, open-source contributors, and enterprise architects need a searchable, modern documentation website at `docs.codeatlas.dev`.
- **Technical Specification**:
  - Setup documentation portal using Nextra or Mintlify.
  - Synchronize planning markdown files from `docs/`:
    - Quickstart & Docker deployment.
    - Interactive OpenAPI specification viewer.
    - Issue mapping algorithmic breakdown.
    - Self-hosting guide for private Ollama clusters.
  - Search powered by Algolia / Pagefind with keyboard navigation.
- **Acceptance Criteria**:
  - [ ] Documentation site deploys automatically on push to `main`.
  - [ ] Full text search returns results in < 50ms.
  - [ ] Mobile-responsive layout with dark/light mode toggle.

---

### Issue #096: `[FEAT]: Marketing Landing Page with Interactive Canvas Demo & Waitlist`
- **Labels**: `phase:phase-4-saas`, `type:frontend`, `priority:P1-high`, `component:apps/web`, `status:ready`
- **Milestone**: `M4: Beta Launch`
- **Component**: `apps/web/src/app/landing/`
- **Problem Statement**:
  Attracting developers and converting visitors into active users requires an engaging landing page with an interactive embedded demo.
- **Technical Specification**:
  - Hero section: Bold value proposition, GitHub star count button, live interactive React Flow canvas preview.
  - Features grid: Interactive Graph, 5-Signal Issue Mapping, RAG Living Docs, 100% Privacy/Self-Hosted.
  - Interactive playground: Let users explore pre-indexed public monorepo (e.g. Next.js or FastAPI sample).
  - Waitlist / sign-up form integrated with PostgreSQL and email notification.
- **Acceptance Criteria**:
  - [ ] Lighthouse performance score > 95 on mobile and desktop.
  - [ ] Interactive demo canvas loads instantly without authentication.
  - [ ] Responsive across all screen sizes.

---

### Issue #097: `[INFRA]: Production Kubernetes Deployment Architecture (EKS/GKE Helm Charts)`
- **Labels**: `phase:phase-4-saas`, `type:infra`, `priority:P0-critical`, `component:infra`, `status:ready`
- **Milestone**: `M4: Beta Launch`
- **Component**: `infra/k8s/`, `infra/helm/`
- **Problem Statement**:
  Transitioning from single-host Docker Compose to production requires Kubernetes orchestration with Horizontal Pod Autoscaling (HPA) and automated SSL.
- **Technical Specification**:
  - Create Helm chart `codeatlas-platform`:
    - Deployments: `api` (FastAPI), `web` (Next.js), `worker` (Celery).
    - StatefulSets / Managed Services: PostgreSQL with pgvector, Redis Cluster.
    - Ingress: NGINX Ingress Controller with cert-manager Let's Encrypt TLS.
    - HPA: Scale API pods based on CPU/Memory and Celery workers based on Redis queue depth.
- **Acceptance Criteria**:
  - [ ] `helm install codeatlas infra/helm/codeatlas-platform` deploys complete stack cleanly.
  - [ ] Zero-downtime rolling updates verified.
  - [ ] Automatic SSL certificate issuance and renewal via Let's Encrypt.

---

### Issue #098: `[FEAT]: Automated Incident Response Runbooks & Disaster Recovery Protocols`
- **Labels**: `phase:phase-4-saas`, `type:infra`, `priority:P1-high`, `component:documentation`, `status:ready`
- **Milestone**: `M4: Beta Launch`
- **Component**: `docs/runbooks/`
- **Problem Statement**:
  Production uptime SLA (99.9%) requires battle-tested operational runbooks for database failovers, worker queue backups, and corrupted index rebuilds.
- **Technical Specification**:
  - Runbooks:
    - `database-failover.md`: Restoring PostgreSQL from pgvector point-in-time recovery (PITR) snapshots.
    - `celery-queue-backlog.md`: Scaling worker nodes and draining dead-letter queues.
    - `ollama-gpu-crash.md`: Diagnosing Ollama OOM issues and failing over to CPU inference.
    - `webhook-replay.md`: Reprocessing dropped GitHub webhook deliveries.
- **Acceptance Criteria**:
  - [ ] Step-by-step CLI commands tested against staging failure simulations.
  - [ ] RTO (Recovery Time Objective) < 30 minutes; RPO (Recovery Point Objective) < 5 minutes.
  - [ ] Runbooks linked directly to Prometheus alerting rules.
