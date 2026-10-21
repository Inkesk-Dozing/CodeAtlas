# CodeAtlas - Monitoring & Observability

## Overview
Prometheus + Grafana for metrics, Loki for logs, Sentry for errors, OpenTelemetry for tracing.

---

## Metrics Stack

### Prometheus Configuration
```yaml
# infra/monitoring/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets: ["alertmanager:9093"]

scrape_configs:
  - job_name: "codeatlas-api"
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names: [codeatlas]
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)

  - job_name: "codeatlas-postgres"
    static_configs:
      - targets: ["postgres-exporter:9187"]

  - job_name: "codeatlas-redis"
    static_configs:
      - targets: ["redis-exporter:9121"]
```

### Custom Metrics (FastAPI)
```python
from prometheus_client import Counter, Histogram, Gauge, Info
from starlette.middleware.base import BaseHTTPMiddleware

# Counters
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

ERROR_COUNT = Counter(
    "http_errors_total",
    "Total HTTP errors",
    ["method", "endpoint", "error_type"]
)

# Histograms
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

# Gauges
ACTIVE_CONNECTIONS = Gauge(
    "active_db_connections",
    "Current active database connections"
)

QUEUE_DEPTH = Gauge(
    "celery_queue_depth",
    "Number of tasks in Celery queue",
    ["queue"]
)

INGESTION_PROGRESS = Gauge(
    "ingestion_progress_percent",
    "Ingestion progress percentage",
    ["repo_id", "stage"]
)

# Info
BUILD_INFO = Info("codeatlas_build", "Build information")
BUILD_INFO.info({
    "version": "1.2.0",
    "commit": git_commit_sha,
    "python_version": sys.version,
})

# Domain-specific metrics
EMBEDDING_BATCH_SIZE = Histogram(
    "embedding_batch_size",
    "Embedding batch sizes",
    buckets=[1, 8, 16, 32, 64, 128]
)

EMBEDDING_LATENCY = Histogram(
    "embedding_generation_seconds",
    "Time to generate embeddings",
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0]
)

GRAPH_QUERY_NODES = Histogram(
    "graph_query_node_count",
    "Number of nodes returned in graph queries",
    buckets=[10, 50, 100, 500, 1000, 2000]
)

SEARCH_RESULTS_COUNT = Histogram(
    "search_results_count",
    "Number of search results returned",
    buckets=[1, 5, 10, 20, 50]
)

ISSUE_MAPPING_CONFIDENCE = Histogram(
    "issue_mapping_confidence",
    "Confidence scores of issue mappings",
    buckets=[0.1, 0.3, 0.5, 0.7, 0.9]
)

# Middleware
class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        
        endpoint = request.url.path
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status=response.status_code
        ).inc()
        
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(duration)
        
        return response
```

---

## Key Metrics & SLOs

### Service Level Objectives
| Service | SLO | Measurement |
|---------|-----|-------------|
| API availability | 99.9% | Successful responses / total |
| API latency (p95) | < 200ms | Request duration |
| Graph query latency (p95) | < 100ms | Query duration |
| Search latency (p95) | < 50ms | Search duration |
| Ingestion success rate | 99% | Successful / total |
| Ingestion duration (p95) | < 10 min | Full repo analysis |
| Issue mapping latency (p95) | < 2s | Analysis duration |
| Webhook processing delay | < 5s | Event received → processed |

### Business Metrics
```python
# Track product usage
ACTIVE_REPOSITORIES = Gauge("active_repositories", "Repos analyzed in last 7 days")
ACTIVE_USERS = Gauge("active_users", "Users active in last 7 days")
QUERIES_PER_DAY = Counter("queries_per_day", "Total searches/queries")
ISSUES_MAPPED = Counter("issues_mapped_total", "Issues with generated mappings")
MAPPING_ACCURACY = Gauge("mapping_accuracy_avg", "Average mapping confidence")

# Onboarding impact
TIME_TO_FIRST_QUERY = Histogram(
    "time_to_first_query_seconds",
    "Time from signup to first code query",
    buckets=[60, 300, 900, 3600, 86400]
)
```

### Ingestion Metrics
```python
INGESTION_DURATION = Histogram(
    "ingestion_duration_seconds",
    "Total ingestion duration",
    ["mode", "repo_size"],  # mode: full/incremental, repo_size: small/medium/large
    buckets=[10, 30, 60, 120, 300, 600, 1800]
)

INGESTION_STAGE_DURATION = Histogram(
    "ingestion_stage_duration_seconds",
    "Duration per ingestion stage",
    ["stage"],  # clone, parse, extract, embed, persist
    buckets=[1, 5, 10, 30, 60, 120, 300]
)

INGESTION_FILES_PROCESSED = Counter(
    "ingestion_files_processed_total",
    "Total files processed",
    ["language", "status"]  # status: success, error, skipped
)

INGESTION_FAILURES = Counter(
    "ingestion_failures_total",
    "Ingestion failures by stage",
    ["stage", "error_type"]
)
```

---

## Alert Rules

```yaml
# infra/monitoring/prometheus/alert_rules.yml
groups:
  - name: codeatlas_api
    rules:
      # High error rate
      - alert: APIHighErrorRate
        expr: |
          rate(http_errors_total[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
          team: backend
        annotations:
          summary: "API error rate above 5%"
          description: "Error rate is {{ $value | humanizePercentage }}"

      # High latency
      - alert: APIHighLatency
        expr: |
          histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
        for: 5m
        labels:
          severity: warning
          team: backend
        annotations:
          summary: "API p95 latency above 500ms"

      # Ingestion failures
      - alert: IngestionHighFailureRate
        expr: |
          rate(ingestion_failures_total[1h]) > 5
        for: 15m
        labels:
          severity: warning
          team: backend
        annotations:
          summary: "High ingestion failure rate"

      # Ingestion taking too long
      - alert: IngestionTimeout
        expr: |
          ingestion_duration_seconds{mode="full"} > 1800
        labels:
          severity: warning
        annotations:
          summary: "Ingestion taking > 30 minutes"

  - name: codeatlas_database
    rules:
      # High connection usage
      - alert: DatabaseHighConnections
        expr: |
          pg_stat_activity_count / pg_settings_max_connections > 0.8
        for: 5m
        labels:
          severity: warning

      # Slow queries
      - alert: DatabaseSlowQueries
        expr: |
          rate(pg_stat_statements_mean_time_seconds[5m]) > 1.0
        for: 10m
        labels:
          severity: warning

      # Replication lag
      - alert: DatabaseReplicationLag
        expr: |
          pg_replication_lag > 30
        for: 5m
        labels:
          severity: critical

      # Disk space
      - alert: DatabaseDiskSpace
        expr: |
          (pg_database_size_bytes / node_filesystem_size_bytes) > 0.85
        for: 10m
        labels:
          severity: warning

  - name: codeatlas_infrastructure
    rules:
      # Pod restarts
      - alert: PodFrequentRestarts
        expr: |
          increase(kube_pod_container_status_restarts_total[1h]) > 3
        labels:
          severity: warning

      # Memory pressure
      - alert: PodMemoryPressure
        expr: |
          container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
        for: 5m
        labels:
          severity: warning

      # Queue backlog
      - alert: CeleryQueueBacklog
        expr: |
          celery_queue_depth{queue="ingestion"} > 100
        for: 10m
        labels:
          severity: warning

  - name: codeatlas_security
    rules:
      # Auth failure spike
      - alert: AuthFailureSpike
        expr: |
          rate(auth_failures_total[5m]) > 10
        for: 5m
        labels:
          severity: high

      # Webhook signature failures
      - alert: WebhookSignatureFailures
        expr: |
          rate(webhook_signature_failures_total[10m]) > 5
        labels:
          severity: high
```

---

## Grafana Dashboards

### Dashboard 1: Service Overview
```
Panels:
├── Row: API Health
│   ├── Stat: Uptime (99.9% target)
│   ├── Timeseries: Request rate (req/s)
│   ├── Timeseries: Error rate (%)
│   └── Gauge: p95 latency
├── Row: Ingestion
│   ├── Stat: Active ingestions
│   ├── Timeseries: Ingestion duration
│   ├── Bar chart: Success/failure by stage
│   └── Table: Recent ingestion tasks
├── Row: Search & Query
│   ├── Timeseries: Search QPS
│   ├── Histogram: Search latency distribution
│   └── Stat: avg result count
└── Row: Business
    ├── Stat: Active repos (7d)
    ├── Stat: Active users (7d)
    ├── Timeseries: Issues mapped
    └── Gauge: Mapping accuracy
```

### Dashboard 2: Ingestion Deep Dive
```
Panels:
├── Row: Pipeline Stages
│   ├── Timeseries: Clone duration
│   ├── Timeseries: Parse duration
│   ├── Timeseries: Extract duration
│   ├── Timeseries: Embed duration
│   └── Timeseries: Persist duration
├── Row: File Processing
│   ├── Pie chart: Files by language
│   ├── Timeseries: Files/sec throughput
│   └── Stat: Total files processed
├── Row: Errors
│   ├── Table: Recent failures
│   └── Timeseries: Failure rate by stage
└── Row: Embeddings
    ├── Histogram: Batch size distribution
    ├── Timeseries: Embedding latency
    └── Stat: Vectors generated
```

### Dashboard 3: Database Performance
```
Panels:
├── Row: Connections
│   ├── Gauge: Active connections
│   └── Timeseries: Connection rate
├── Row: Queries
│   ├── Timeseries: Query rate
│   ├── Table: Slow queries (> 100ms)
│   └── Histogram: Query latency
├── Row: pgvector
│   ├── Timeseries: HNSW search latency
│   ├── Stat: Index size
│   └── Timeseries: Vector count
└── Row: Storage
    ├── Stat: Database size
    ├── Timeseries: Disk IOPS
    └── Timeseries: Replication lag
```

---

## Distributed Tracing (OpenTelemetry)

```python
# apps/api/tracing.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor

def setup_tracing(app):
    provider = TracerProvider()
    provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(endpoint="http://otel-collector:4317")
        )
    )
    trace.set_tracer_provider(provider)
    
    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument()
    RedisInstrumentor().instrument()

# Custom spans for domain operations
tracer = trace.get_tracer(__name__)

async def ingest_repository(repo_id: str):
    with tracer.start_as_current_span("ingest_repository") as span:
        span.set_attribute("repo.id", repo_id)
        
        with tracer.start_as_current_span("clone"):
            # Clone logic...
            pass
        
        with tracer.start_as_current_span("parse") as parse_span:
            parse_span.set_attribute("files.count", file_count)
            # Parse logic...
            pass
        
        with tracer.start_as_current_span("embed") as embed_span:
            embed_span.set_attribute("vectors.count", vector_count)
            # Embed logic...
            pass
```

---

## Logging Strategy

### Structured Logging (Python)
```python
import structlog

logger = structlog.get_logger()

# Configure
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    wrapper_class=structlog.BoundLogger,
    cache_logger_on_first_use=True,
)

# Usage
async def analyze_issue(repo_id: str, issue_number: int):
    log = logger.bind(
        repo_id=repo_id,
        issue_number=issue_number,
        trace_id=trace.get_current_span().get_span_context().trace_id,
    )
    
    log.info("issue_analysis_started")
    
    try:
        result = await mapping_service.analyze(issue)
        log.info(
            "issue_analysis_completed",
            duration_ms=result.duration,
            mappings_count=len(result.mappings),
            avg_confidence=result.avg_confidence,
        )
    except Exception as e:
        log.error(
            "issue_analysis_failed",
            error=str(e),
            error_type=type(e).__name__,
        )
        raise
```

### Log Levels & Usage
| Level | Usage | Examples |
|-------|-------|---------|
| DEBUG | Development debugging | Variable values, SQL queries |
| INFO | Normal operations | Request completed, task started |
| WARNING | Unexpected but handled | Rate limit approaching, slow query |
| ERROR | Operation failed | Ingestion failed, API error |
| CRITICAL | System-level failure | Database down, auth bypass attempt |

### Log Aggregation (Loki)
```yaml
# Promtail config
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: codeatlas
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: codeatlas-.*
      - source_labels: [__meta_kubernetes_pod_container_name]
        target_label: container
      - source_labels: [__meta_kubernetes_namespace]
        target_label: namespace

# LogQL queries
# Error rate
{namespace="codeatlas"} |= "error" | json | rate([5m])

# Ingestion failures
{namespace="codeatlas", container="codeatlas-worker"} 
  |= "ingestion_failed" 
  | json

# Slow requests
{namespace="codeatlas"} 
  | json 
  | duration > 1s
```

---

## Error Tracking (Sentry)

```python
# apps/api/sentry.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

sentry_sdk.init(
    dsn=os.environ["SENTRY_DSN"],
    environment=os.environ.get("ENVIRONMENT", "development"),
    release=f"codeatlas@{VERSION}",
    integrations=[
        FastApiIntegration(),
        SqlalchemyIntegration(),
        CeleryIntegration(),
    ],
    traces_sample_rate=0.1,  # 10% of transactions
    profiles_sample_rate=0.1,
    before_send=filter_sensitive_data,
    before_send_transaction=sample_transactions,
)

def filter_sensitive_data(event, hint):
    """Remove sensitive data before sending to Sentry."""
    if "request" in event:
        # Remove auth headers
        headers = event["request"].get("headers", {})
        headers.pop("Authorization", None)
        headers.pop("Cookie", None)
    
    # Scrub URLs with sensitive params
    if "url" in event:
        event["url"] = re.sub(r"token=[^&]+", "token=REDACTED", event["url"])
    
    return event
```

### Frontend Sentry
```typescript
// apps/web/sentry.client.config.ts
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NODE_ENV,
  tracesSampleRate: 0.1,
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
  integrations: [
    new Sentry.Replay({
      maskAllText: true,
      blockAllMedia: true,
    }),
  ],
  beforeSend(event) {
    // Scrub sensitive data
    if (event.user) {
      delete event.user.email;
      delete event.user.ip_address;
    }
    return event;
  },
});
```

---

## Runbooks

### Ingestion Failures Spike
```
1. Check ingestion dashboard → which stage is failing?
2. If CLONE: Check GitHub API rate limits, installation token validity
3. If PARSE: Check worker logs for syntax errors, OOM kills
4. If EMBED: Check Ollama service health, GPU memory
5. If PERSIST: Check database connections, disk space
6. Check Celery queue depth → scale workers if needed
7. If >10 failures: Check ingestion_failures table for patterns
```

### High API Latency
```
1. Check API dashboard → which endpoint is slow?
2. Check database → slow queries, connection pool exhaustion
3. Check Redis → cache hit rate, memory
4. Check pod resource usage → scale if needed
5. Check external dependencies → GitHub API, Ollama
6. If consistent: Enable query profiling, optimize slow queries
```

### Database Storage Filling Up
```
1. Check database size growth rate
2. Check table sizes: SELECT * FROM pg_total_relation_size(...)
3. Old repos: Archive repos not analyzed in 90+ days
4. Embeddings: Consider reducing precision (float32 → float16)
5. Logs: Check if audit logs need rotation
6. Scale: Increase RDS storage or enable auto-scaling
```

---

## Health Checks

```python
# apps/api/health.py
@app.get("/health")
async def health_check():
    checks = {}
    
    # Database
    try:
        await db.execute("SELECT 1")
        checks["database"] = "healthy"
    except Exception:
        checks["database"] = "unhealthy"
    
    # Redis
    try:
        await redis.ping()
        checks["redis"] = "healthy"
    except Exception:
        checks["redis"] = "unhealthy"
    
    # Ollama
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{OLLAMA_URL}/api/tags", timeout=2.0)
            checks["ollama"] = "healthy" if resp.status_code == 200 else "degraded"
    except Exception:
        checks["ollama"] = "unhealthy"
    
    # GitHub API
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://api.github.com/zen", timeout=2.0)
            checks["github"] = "healthy" if resp.status_code == 200 else "degraded"
    except Exception:
        checks["github"] = "unhealthy"
    
    # Celery workers
    try:
        inspect = celery.control.inspect()
        active = inspect.active()
        checks["celery"] = "healthy" if active else "unhealthy"
    except Exception:
        checks["celery"] = "unhealthy"
    
    overall = "healthy" if all(v == "healthy" for v in checks.values()) else "degraded"
    
    return {
        "status": overall,
        "version": VERSION,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat(),
    }

@app.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe."""
    # Only ready if critical dependencies are healthy
    health = await health_check()
    if health["checks"]["database"] == "healthy" and health["checks"]["redis"] == "healthy":
        return {"status": "ready"}
    raise HTTPException(503, "Not ready")
```