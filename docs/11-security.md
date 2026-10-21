# CodeAtlas - Security Specification

## Overview
Defense-in-depth approach: network, application, data, and operational security.

---

## Authentication & Authorization

### GitHub OAuth Flow
```
┌─────────┐     ┌──────────┐     ┌─────────┐     ┌──────────┐
│  User   │────▶│ Next.js  │────▶│ GitHub  │────▶│ Callback │
│         │     │ /login   │     │ OAuth   │     │ /callback│
└─────────┘     └──────────┘     └─────────┘     └──────────┘
                     │                               │
                     │  1. Redirect to GitHub         │
                     │◀──────────────────────────────│
                     │                               │
                     │  2. User authorizes           │
                     │──────────────────────────────▶│
                     │                               │
                     │  3. Code exchange             │
                     │──────────────────────────────▶│
                     │                               │
                     │  4. Access token              │
                     │◀──────────────────────────────│
                     │                               │
                     │  5. JWT issued                │
                     │◀──────────────────────────────│
                     ▼                               ▼
               ┌──────────┐                   ┌──────────┐
               │ Dashboard│                   │ Set Cookie│
               └──────────┘                   └──────────┘
```

### JWT Configuration
```python
# Security settings
JWT_CONFIG = {
    "algorithm": "RS256",           # Asymmetric (not HS256)
    "access_token_expire_minutes": 30,
    "refresh_token_expire_days": 30,
    "issuer": "https://auth.codeatlas.dev",
    "audience": "codeatlas-api",
}

# Claims
{
    "sub": "user-uuid",
    "org_id": "org-uuid",
    "role": "admin",               # admin | member | viewer
    "github_id": 123456,
    "iat": 1699123456,
    "exp": 1699125256,
    "iss": "https://auth.codeatlas.dev",
    "aud": "codeatlas-api",
    "jti": "unique-token-id"       # For token revocation
}
```

### Refresh Token Rotation
```python
async def refresh_access_token(refresh_token: str) -> TokenResponse:
    # 1. Validate refresh token signature and expiry
    payload = verify_jwt(refresh_token, REFRESH_SECRET)
    
    # 2. Check token not already used (revoke if reused)
    if await is_token_revoked(payload["jti"]):
        await revoke_all_user_tokens(payload["sub"])  # Token theft detected
        raise SecurityException("Token reuse detected")
    
    # 3. Revoke old refresh token
    await revoke_token(payload["jti"])
    
    # 4. Issue new token pair
    new_access = create_access_token(payload["sub"])
    new_refresh = create_refresh_token(payload["sub"])
    
    return TokenResponse(access_token=new_access, refresh_token=new_refresh)
```

### Role-Based Access Control (RBAC)
```python
class Role(str, Enum):
    ADMIN = "admin"       # Full access: manage org, repos, billing
    MEMBER = "member"     # Can view graphs, trigger ingestion, submit feedback
    VIEWER = "viewer"     # Read-only: view graphs, search

# Permission matrix
PERMISSIONS = {
    "repos:read":      [Role.ADMIN, Role.MEMBER, Role.VIEWER],
    "repos:write":     [Role.ADMIN, Role.MEMBER],
    "repos:delete":    [Role.ADMIN],
    "graph:read":      [Role.ADMIN, Role.MEMBER, Role.VIEWER],
    "graph:write":     [Role.ADMIN, Role.MEMBER],
    "issues:read":     [Role.ADMIN, Role.MEMBER, Role.VIEWER],
    "issues:analyze":  [Role.ADMIN, Role.MEMBER],
    "search":          [Role.ADMIN, Role.MEMBER, Role.VIEWER],
    "chat":            [Role.ADMIN, Role.MEMBER],
    "settings:read":   [Role.ADMIN, Role.MEMBER],
    "settings:write":  [Role.ADMIN],
    "members:manage":  [Role.ADMIN],
    "billing:manage":  [Role.ADMIN],
    "audit:read":      [Role.ADMIN],
}

def require_permission(permission: str):
    async def dependency(current_user = Depends(get_current_user)):
        if permission not in PERMISSIONS:
            raise HTTPException(400, "Unknown permission")
        
        user_role = current_user["role"]
        if user_role not in PERMISSIONS[permission]:
            raise HTTPException(403, f"Missing permission: {permission}")
        
        return current_user
    return dependency

# Usage
@app.get("/repos/{repo_id}")
async def get_repo(
    repo_id: str,
    user = Depends(require_permission("repos:read"))
):
    ...
```

---

## GitHub App Security

### App Configuration
```
GitHub App Settings:
├── Webhook URL: https://api.codeatlas.dev/v1/webhooks/github
├── Webhook Secret: <random-64-chars>
├── Private Key: <RSA-2048-key>
├── Request OAuth during installation: ✅
└── Permissions:
    ├── Repository permissions:
    │   ├── Contents: Read-only        # Clone repo files
    │   ├── Metadata: Read-only        # Repo info
    │   ├── Issues: Read-only          # Read issues for mapping
    │   └── Pull requests: Read-only   # (Phase 5) PR analysis
    └── Account permissions:
        └── None
```

### Installation Token Management
```python
class GitHubTokenManager:
    def __init__(self, app_id: int, private_key: str):
        self.app_id = app_id
        self.private_key = private_key
        self._cache: dict[int, tuple[str, datetime]] = {}  # installation_id -> (token, expiry)

    async def get_installation_token(self, installation_id: int) -> str:
        # Check cache (tokens valid for 1 hour)
        if installation_id in self._cache:
            token, expiry = self._cache[installation_id]
            if datetime.utcnow() < expiry - timedelta(minutes=5):  # 5-min buffer
                return token
        
        # Generate JWT for app authentication
        app_jwt = self._create_app_jwt()
        
        # Exchange for installation token
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"https://api.github.com/app/installations/{installation_id}/access_tokens",
                headers={
                    "Authorization": f"Bearer {app_jwt}",
                    "Accept": "application/vnd.github+json",
                },
            )
            resp.raise_for_status()
            data = resp.json()
        
        token = data["token"]
        expiry = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))
        
        # Cache (never log or persist this token)
        self._cache[installation_id] = (token, expiry)
        return token

    def _create_app_jwt(self) -> str:
        now = int(time.time())
        payload = {
            "iat": now - 60,
            "exp": now + 540,  # 9 minutes max
            "iss": str(self.app_id),
        }
        return jwt.encode(payload, self.private_key, algorithm="RS256")
```

### Webhook Signature Verification
```python
from hmac import HMAC, compare_digest

async def verify_webhook_signature(
    payload: bytes,
    signature_header: str,
    secret: str,
) -> bool:
    """Verify X-Hub-Signature-256 header."""
    if not signature_header.startswith("sha256="):
        return False
    
    expected = "sha256=" + HMAC(secret.encode(), payload, "sha256").hexdigest()
    
    # Constant-time comparison (prevents timing attacks)
    return compare_digest(expected, signature_header)

# FastAPI dependency
@app.post("/webhooks/github")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(...),
    x_hub_signature_256: str = Header(...),
    x_github_delivery: str = Header(...),
):
    body = await request.body()
    
    if not await verify_webhook_signature(body, x_hub_signature_256, WEBHOOK_SECRET):
        raise HTTPException(401, "Invalid webhook signature")
    
    # Process event...
```

---

## Data Security

### Encryption at Rest
```sql
-- Sensitive columns encrypted via pgcrypto
ALTER TABLE users 
    ADD COLUMN github_token_encrypted BYTEA;

-- Encrypt on write
UPDATE users SET github_token_encrypted = pgp_sym_encrypt(
    'ghp_xxx', 
    current_setting('app.encryption_key')
);

-- Decrypt on read (only in application layer)
SELECT pgp_sym_decrypt(
    github_token_encrypted, 
    current_setting('app.encryption_key')
) FROM users WHERE id = $1;
```

### Encryption in Transit
```
All connections use TLS 1.3:
- Client → Load Balancer: TLS 1.3 (HSTS enforced)
- Load Balancer → Pods: TLS 1.3 (mTLS via Istio)
- Pod → PostgreSQL: TLS 1.3 (require)
- Pod → Redis: TLS 1.3 (require)
- Pod → GitHub API: TLS 1.3 (enforced by HTTP client)
```

### Secrets Management
```python
# Never store secrets in code or env vars directly
# Use Kubernetes Secrets + External Secrets Operator

# infra/k8s/external-secrets.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: codeatlas-secrets
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: ClusterSecretStore
  target:
    name: codeatlas-api-secrets
    creationPolicy: Owner
  data:
    - secretKey: DATABASE_URL
      remoteRef:
        key: codeatlas/prod
        property: database_url
    - secretKey: JWT_SECRET
      remoteRef:
        key: codeatlas/prod
        property: jwt_secret
    - secretKey: GITHUB_APP_PRIVATE_KEY
      remoteRef:
        key: codeatlas/prod
        property: github_private_key
```

### PII Handling
| Data | Storage | Retention | Anonymization |
|------|---------|-----------|---------------|
| User email | PostgreSQL | Account lifetime | On deletion |
| GitHub username | PostgreSQL | Account lifetime | On deletion |
| User tokens | Encrypted column | Session + refresh | On logout |
| Repo code | Temporary (S3) | Ingestion only | Deleted after parse |
| Repo metadata | PostgreSQL | Account lifetime | On repo deletion |
| Chat history | PostgreSQL | 90 days | Auto-purge |
| Audit logs | PostgreSQL | 1 year | Aggregate after 90 days |

### Data Deletion (GDPR)
```python
async def delete_user_data(user_id: str):
    """Complete user data deletion (GDPR Right to Erasure)."""
    async with db.transaction():
        # 1. Delete chat history
        await db.execute(
            "DELETE FROM chat_messages WHERE session_id IN "
            "(SELECT id FROM chat_sessions WHERE user_id = $1)", user_id
        )
        await db.execute("DELETE FROM chat_sessions WHERE user_id = $1", user_id)
        
        # 2. Delete mapping feedback
        await db.execute("DELETE FROM mapping_feedback WHERE user_id = $1", user_id)
        
        # 3. Anonymize audit logs (keep for compliance)
        await db.execute(
            "UPDATE audit_logs SET user_id = NULL, ip_address = NULL "
            "WHERE user_id = $1", user_id
        )
        
        # 4. Delete user record
        await db.execute("DELETE FROM org_members WHERE user_id = $1", user_id)
        await db.execute("DELETE FROM users WHERE id = $1", user_id)
        
        # 5. Revoke all tokens
        await revoke_all_tokens(user_id)
```

---

## API Security

### Rate Limiting (Redis-based)
```python
import redis.asyncio as redis

class RateLimiter:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def check_limit(
        self, 
        key: str, 
        limit: int, 
        window_seconds: int
    ) -> tuple[bool, int, int]:
        """Returns (allowed, remaining, reset_timestamp)."""
        now = int(time.time())
        window_start = now - window_seconds
        
        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, window_seconds)
        results = await pipe.execute()
        
        request_count = results[2]
        remaining = max(0, limit - request_count)
        reset = now + window_seconds
        
        return (request_count <= limit, remaining, reset)

# Middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Get identifier (user ID or IP)
    client_id = await get_client_id(request)
    
    # Different limits per endpoint type
    limit, window = get_rate_limit(request.url.path)
    
    allowed, remaining, reset = await rate_limiter.check_limit(
        f"ratelimit:{client_id}", limit, window
    )
    
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded"},
            headers={
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset),
                "Retry-After": str(reset - int(time.time())),
            },
        )
    
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(reset)
    return response
```

### Input Validation (Pydantic)
```python
from pydantic import BaseModel, Field, validator
import re

class RepositoryCreate(BaseModel):
    github_id: int = Field(..., gt=0)
    installation_id: int = Field(..., gt=0)
    settings: RepositorySettings = Field(default_factory=RepositorySettings)
    
    @validator("github_id")
    def validate_github_id(cls, v):
        if v > 9_999_999_999:  # GitHub IDs are < 10 billion
            raise ValueError("Invalid GitHub ID")
        return v

class SearchQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(default=10, ge=1, le=100)
    types: list[str] = Field(default_factory=list)
    threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    
    @validator("query")
    def sanitize_query(cls, v):
        # Remove potential injection patterns
        v = re.sub(r'[<>{}\\]', '', v)
        return v.strip()

class IssueFeedback(BaseModel):
    node_id: UUID
    rating: Literal["relevant", "partially_relevant", "irrelevant"]
    comment: Optional[str] = Field(None, max_length=1000)
```

### SQL Injection Prevention
```python
# NEVER use string formatting for SQL
# BAD:
# query = f"SELECT * FROM nodes WHERE name = '{name}'"

# GOOD: Parameterized queries
async def get_nodes_by_name(name: str):
    return await db.fetch(
        "SELECT * FROM code_nodes WHERE name = $1",
        name
    )

# GOOD: ORM (SQLAlchemy)
async def get_nodes_by_name_orm(name: str):
    stmt = select(CodeNode).where(CodeNode.name == name)
    return await db.execute(stmt)
```

### CORS Configuration
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.codeatlas.dev",
        "http://localhost:3000",  # Dev only
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-GitHub-Installation-ID"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],
    max_age=86400,
)
```

### Security Headers (Next.js)
```javascript
// next.config.js
const securityHeaders = [
  {
    key: 'Strict-Transport-Security',
    value: 'max-age=63072000; includeSubDomains; preload',
  },
  {
    key: 'X-Content-Type-Options',
    value: 'nosniff',
  },
  {
    key: 'X-Frame-Options',
    value: 'DENY',
  },
  {
    key: 'X-XSS-Protection',
    value: '1; mode=block',
  },
  {
    key: 'Referrer-Policy',
    value: 'strict-origin-when-cross-origin',
  },
  {
    key: 'Permissions-Policy',
    value: 'camera=(), microphone=(), geolocation=()',
  },
  {
    key: 'Content-Security-Policy',
    value: [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net",
      "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
      "font-src 'self' https://fonts.gstatic.com",
      "img-src 'self' data: https://avatars.githubusercontent.com",
      "connect-src 'self' https://api.codeatlas.dev wss://api.codeatlas.dev",
      "frame-ancestors 'none'",
    ].join('; '),
  },
];

module.exports = {
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: securityHeaders,
      },
    ];
  },
};
```

---

## Repository Analysis Security

### Path Traversal Prevention
```python
def validate_repo_path(base_path: Path, file_path: str) -> Path:
    """Prevent path traversal attacks during repo cloning."""
    resolved = (base_path / file_path).resolve()
    
    # Ensure resolved path is within base_path
    if not str(resolved).startswith(str(base_path.resolve())):
        raise SecurityException(f"Path traversal attempt: {file_path}")
    
    return resolved

# Also filter these during ingestion:
BLOCKED_PATH_PATTERNS = [
    "../*",
    "/etc/*",
    "/proc/*",
    "/sys/*",
    "~/*",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "id_rsa*",
    "id_ed25519*",
    ".env",
    ".env.*",
    "credentials",
    "*.secret",
]
```

### Symlink Attack Prevention
```python
def safe_scan_directory(base_path: Path):
    """Scan directory following symlinks safely."""
    for entry in os.scandir(base_path):
        # Skip symlinks (could point outside repo)
        if entry.is_symlink():
            logger.warning(f"Skipping symlink: {entry.path}")
            continue
        
        if entry.is_dir(follow_symlinks=False):
            yield from safe_scan_directory(Path(entry.path))
        elif entry.is_file(follow_symlinks=False):
            yield Path(entry.path)
```

### Secret Detection (Before Embedding)
```python
SECRET_PATTERNS = [
    # AWS
    r"AKIA[0-9A-Z]{16}",
    r"aws_secret_access_key\s*[=:]\s*['\"]?[A-Za-z0-9/+=]{40}",
    # GitHub
    r"gh[pousr]_[A-Za-z0-9]{36,}",
    r"github_pat_[A-Za-z0-9_]{22,}",
    # Stripe
    r"sk_live_[0-9a-zA-Z]{24,}",
    # Generic
    r"(?:api[_-]?key|secret|password|token)\s*[=:]\s*['\"][^'\"]{8,}['\"]",
    # Private keys
    r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
]

def detect_secrets(content: str) -> list[str]:
    """Detect potential secrets before storing/embedding."""
    findings = []
    for pattern in SECRET_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        findings.extend(matches)
    return findings

# During ingestion: redact secrets before embedding
def redact_secrets(content: str) -> str:
    for pattern in SECRET_PATTERNS:
        content = re.sub(pattern, "[REDACTED]", content, flags=re.IGNORECASE)
    return content
```

---

## Network Security

### Kubernetes Network Policies
```yaml
# infra/k8s/network-policies.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-network-policy
  namespace: codeatlas
spec:
  podSelector:
    matchLabels:
      app: codeatlas-api
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - protocol: TCP
          port: 8000
  egress:
    # Allow database access
    - to:
        - podSelector:
            matchLabels:
              app: postgres
      ports:
        - protocol: TCP
          port: 5432
    # Allow Redis access
    - to:
        - podSelector:
            matchLabels:
              app: redis
      ports:
        - protocol: TCP
          port: 6379
    # Allow GitHub API (HTTPS only)
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
            except:
              - 10.0.0.0/8
              - 172.16.0.0/12
              - 192.168.0.0/16
      ports:
        - protocol: TCP
          port: 443
    # DNS
    - to:
        - namespaceSelector: {}
      ports:
        - protocol: UDP
          port: 53
---
# Deny all other traffic by default
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
  namespace: codeatlas
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
```

### Pod Security Standards
```yaml
# Enforce restricted pod security
apiVersion: v1
kind: Namespace
metadata:
  name: codeatlas
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

---

## Audit Logging

```python
class AuditAction(str, Enum):
    # Auth
    USER_LOGIN = "auth.login"
    USER_LOGOUT = "auth.logout"
    TOKEN_REFRESH = "auth.token_refresh"
    
    # Repository
    REPO_CREATED = "repo.create"
    REPO_UPDATED = "repo.update"
    REPO_DELETED = "repo.delete"
    
    # Ingestion
    INGESTION_TRIGGERED = "ingest.trigger"
    INGESTION_COMPLETED = "ingest.complete"
    INGESTION_FAILED = "ingest.fail"
    
    # Data access
    GRAPH_ACCESSED = "data.graph_read"
    NODE_ACCESSED = "data.node_read"
    SEARCH_PERFORMED = "data.search"
    
    # Issue mapping
    ISSUE_ANALYZED = "issue.analyze"
    FEEDBACK_SUBMITTED = "issue.feedback"
    
    # Settings
    SETTINGS_UPDATED = "settings.update"
    MEMBER_INVITED = "member.invite"
    MEMBER_REMOVED = "member.remove"

async def audit_log(
    action: AuditAction,
    user_id: str | None,
    org_id: str | None,
    resource_type: str,
    resource_id: str | None,
    details: dict = None,
    request: Request = None,
):
    """Write audit log entry."""
    await db.execute(
        """
        INSERT INTO audit_logs 
            (user_id, org_id, action, resource_type, resource_id, details, ip_address, user_agent)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """,
        user_id, org_id, action.value, resource_type, resource_id,
        details or {},
        request.client.host if request else None,
        request.headers.get("user-agent") if request else None,
    )
```

---

## Incident Response

### Security Event Triage
| Severity | Examples | Response Time |
|----------|----------|---------------|
| Critical | Data breach, RCE, auth bypass | Immediate (15 min) |
| High | Token leak, privilege escalation | 1 hour |
| Medium | Rate limit bypass, XSS | 4 hours |
| Low | Information disclosure | 24 hours |

### Automated Alerts
```yaml
# Prometheus alert rules
groups:
  - name: security
    rules:
      - alert: HighFailedAuthAttempts
        expr: rate(auth_failures_total[5m]) > 10
        for: 5m
        labels:
          severity: high
        annotations:
          summary: "High authentication failure rate"
          
      - alert: RateLimitAbuse
        expr: rate(rate_limited_requests_total[5m]) > 50
        for: 5m
        labels:
          severity: medium
          
      - alert: WebhookSignatureFailure
        expr: rate(webhook_signature_failures_total[10m]) > 5
        labels:
          severity: high
          
      - alert: UnusualDataAccess
        expr: rate(graph_queries_total[5m]) > 1000
        for: 10m
        labels:
          severity: medium
```

---

## Security Checklist (Pre-Launch)

- [ ] HTTPS enforced on all endpoints (HSTS)
- [ ] JWT uses RS256 with key rotation
- [ ] Refresh token rotation with reuse detection
- [ ] Webhook signature verification
- [ ] Rate limiting on all public endpoints
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (CSP headers, output encoding)
- [ ] Path traversal prevention (repo cloning)
- [ ] Secret detection before embedding
- [ ] Encryption at rest for tokens
- [ ] RLS enabled on multi-tenant tables
- [ ] Audit logging for all sensitive operations
- [ ] Network policies (deny-by-default)
- [ ] Pod security standards (restricted)
- [ ] Dependency scanning (Snyk/Dependabot)
- [ ] Container image scanning (Trivy)
- [ ] Penetration test completed
- [ ] GDPR data deletion implemented
- [ ] Incident response plan documented