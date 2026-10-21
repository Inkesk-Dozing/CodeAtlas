# Threat Modeling & Security Mitigation Strategy

## System Threat Surface Map

CodeAtlas handles sensitive source code data, repository access credentials, and user access tokens. Threat modeling follows the STRIDE methodology (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege).

---

## Threat Matrix & Mitigation Controls

| Threat Category | Target Subsystem | Vulnerability Risk | Impact | Mitigation Strategy | Risk Level |
|---|---|---|---|---|---|
| **Spoofing** | GitHub Webhook Endpoint | Injected forged push webhook payloads | Unauthorized repository ingestion trigger | Enforce HMAC SHA-256 signature verification (`X-Hub-Signature-256`) using `GITHUB_WEBHOOK_SECRET` | **High** |
| **Tampering** | MinIO Object Storage | Unauthenticated access to stored code AST snapshots | Arbitrary code analysis modification | Enforce MinIO private bucket policy with AWS Signature Version 4 authentication | **High** |
| **Repudiation** | User / Admin Actions | Lack of audit logs for repository deletion or role modification | Inability to trace malicious admin activity | Enforce mandatory structured audit log streaming for all mutation operations | **Medium** |
| **Information Disclosure** | Multi-Tenant Database | Cross-tenant data leakage via SQL queries | Unauthorized exposure of private repository ASTs | Enforce PostgreSQL Row-Level Security (RLS) policies scoped strictly to `organization_id` | **Critical** |
| **Denial of Service** | Celery Worker Queue | Submission of massive monorepos causing worker OOM crash | Ingestion queue starvation for other tenants | Impose repository file size limits, shallow cloning, and per-tenant concurrency quotas | **High** |
| **Elevation of Privilege** | JWT Authentication | Stale access token abuse or stolen JWT tokens | Unauthorized API execution as admin | Short-lived access tokens (30 min) coupled with token family refresh rotation and IP binding | **High** |

---

## Security Verification Controls

1. **Pre-Commit Checks**: Secret scanning with TruffleHog.
2. **SAST Execution**: GitHub Actions CodeQL analysis scanning Python and TypeScript code paths.
3. **Dependency Auditing**: Snyk automated PR checks blocking known CVEs in pnpm and pip packages.
