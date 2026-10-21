# CodeAtlas - Infrastructure & Deployment Specification

## Overview
Docker Compose for development, Kubernetes for production. GitHub Actions for CI/CD.

---

## Local Development (Docker Compose)

### docker-compose.yml
```yaml
version: "3.9"

services:
  # PostgreSQL + pgvector
  postgres:
    image: pgvector/pgvector:pg16
    container_name: codeatlas-postgres
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: codeatlas
      POSTGRES_PASSWORD: codeatlas_dev
      POSTGRES_DB: codeatlas
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./infra/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U codeatlas"]
      interval: 5s
      timeout: 5s
      retries: 5

  # Redis (cache + Celery broker)
  redis:
    image: redis:7-alpine
    container_name: codeatlas-redis
    ports:
      - "6379:6379"
    volumes:
      - redisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  # MinIO (S3-compatible object storage)
  minio:
    image: minio/minio:latest
    container_name: codeatlas-minio
    ports:
      - "9000:9000"
      - "9001:9001"   # Console
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - miniodata:/data
    command: server /data --console-address ":9001"

  # Ollama (local LLM)
  ollama:
    image: ollama/ollama:latest
    container_name: codeatlas-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollamadata:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  # FastAPI Backend
  api:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    container_name: codeatlas-api
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://codeatlas:codeatlas_dev@postgres:5432/codeatlas
      REDIS_URL: redis://redis:6379/0
      S3_ENDPOINT: http://minio:9000
      S3_ACCESS_KEY: minioadmin
      S3_SECRET_KEY: minioadmin
      OLLAMA_URL: http://ollama:11434
      GITHUB_APP_ID: ${GITHUB_APP_ID}
      GITHUB_APP_PRIVATE_KEY: ${GITHUB_APP_PRIVATE_KEY}
      GITHUB_WEBHOOK_SECRET: ${GITHUB_WEBHOOK_SECRET}
      JWT_SECRET: ${JWT_SECRET}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./apps/api:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  # Celery Worker (ingestion tasks)
  worker:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    container_name: codeatlas-worker
    environment:
      DATABASE_URL: postgresql+asyncpg://codeatlas:codeatlas_dev@postgres:5432/codeatlas
      REDIS_URL: redis://redis:6379/0
      S3_ENDPOINT: http://minio:9000
      OLLAMA_URL: http://ollama:11434
    depends_on:
      - api
      - redis
      - postgres
    command: celery -A tasks.celery worker --loglevel=info --concurrency=4

  # Celery Beat (scheduled tasks)
  beat:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    container_name: codeatlas-beat
    environment:
      DATABASE_URL: postgresql+asyncpg://codeatlas:codeatlas_dev@postgres:5432/codeatlas
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - api
    command: celery -A tasks.celery beat --loglevel=info

  # Next.js Frontend
  web:
    build:
      context: ./apps/web
      dockerfile: Dockerfile
    container_name: codeatlas-web
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
      NEXTAUTH_URL: http://localhost:3000
      NEXTAUTH_SECRET: ${NEXTAUTH_SECRET}
      GITHUB_CLIENT_ID: ${GITHUB_CLIENT_ID}
      GITHUB_CLIENT_SECRET: ${GITHUB_CLIENT_SECRET}
    volumes:
      - ./apps/web:/app
      - /app/node_modules
      - /app/.next
    command: npm run dev

volumes:
  pgdata:
  redisdata:
  miniodata:
  ollamadata:
```

### Quick Start
```bash
# Clone and setup
git clone https://github.com/codeatlas/codeatlas.git
cd codeatlas
cp .env.example .env  # Fill in GitHub App credentials

# Start all services
docker compose up -d

# Run migrations
docker compose exec api alembic upgrade head

# Seed development data
docker compose exec api python -m scripts.seed_dev

# Access:
# Frontend:  http://localhost:3000
# API:       http://localhost:8000/docs
# MinIO:     http://localhost:9001
# pgAdmin:   http://localhost:5050
```

---

## Production (Kubernetes)

### Directory Structure
```
infra/
├── k8s/
│   ├── namespaces/
│   │   └── codeatlas.yaml
│   ├── api/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── hpa.yaml
│   │   └── configmap.yaml
│   ├── web/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── ingress.yaml
│   ├── worker/
│   │   ├── deployment.yaml
│   │   └── hpa.yaml
│   ├── postgres/
│   │   ├── statefulset.yaml
│   │   ├── service.yaml
│   │   └── pvc.yaml
│   ├── redis/
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   └── monitoring/
│       ├── prometheus/
│       ├── grafana/
│       └── alertmanager/
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── eks.tf
│   ├── rds.tf
│   └── outputs.tf
├── helm/
│   └── codeatlas/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
├── docker-compose.yml
└── postgres/
    └── init.sql
```

### API Deployment
```yaml
# infra/k8s/api/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: codeatlas-api
  namespace: codeatlas
  labels:
    app: codeatlas-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: codeatlas-api
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: codeatlas-api
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: codeatlas-api
      containers:
        - name: api
          image: ghcr.io/codeatlas/api:${VERSION}
          ports:
            - containerPort: 8000
              name: http
          envFrom:
            - configMapRef:
                name: codeatlas-api-config
            - secretRef:
                name: codeatlas-api-secrets
          resources:
            requests:
              cpu: 250m
              memory: 512Mi
            limits:
              cpu: 1000m
              memory: 1Gi
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /ready
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
          lifecycle:
            preStop:
              exec:
                command: ["sleep", "10"]
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: topology.kubernetes.io/zone
          whenUnsatisfiable: DoNotSchedule
          labelSelector:
            matchLabels:
              app: codeatlas-api
```

### Horizontal Pod Autoscaler
```yaml
# infra/k8s/api/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: codeatlas-api-hpa
  namespace: codeatlas
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: codeatlas-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
    - type: Pods
      pods:
        metric:
          name: http_requests_per_second
        target:
          type: AverageValue
          averageValue: "100"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Percent
          value: 100
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
```

### Ingress (NGINX)
```yaml
# infra/k8s/web/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: codeatlas-ingress
  namespace: codeatlas
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - app.codeatlas.dev
        - api.codeatlas.dev
      secretName: codeatlas-tls
  rules:
    - host: app.codeatlas.dev
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: codeatlas-web
                port:
                  number: 3000
    - host: api.codeatlas.dev
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: codeatlas-api
                port:
                  number: 8000
```

### Worker Deployment (Ingestion)
```yaml
# infra/k8s/worker/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: codeatlas-worker
  namespace: codeatlas
spec:
  replicas: 4
  selector:
    matchLabels:
      app: codeatlas-worker
  template:
    metadata:
      labels:
        app: codeatlas-worker
    spec:
      containers:
        - name: worker
          image: ghcr.io/codeatlas/api:${VERSION}
          command: ["celery", "-A", "tasks.celery", "worker"]
          args:
            - "--loglevel=info"
            - "--concurrency=8"
            - "-Q"
            - "ingestion,embedding,summarization"
          resources:
            requests:
              cpu: 500m
              memory: 1Gi
            limits:
              cpu: 2000m
              memory: 4Gi
          envFrom:
            - secretRef:
                name: codeatlas-api-secrets
          volumeMounts:
            - name: tmp
              mountPath: /tmp
      volumes:
        - name: tmp
          emptyDir:
            sizeLimit: 10Gi
```

---

## Terraform (AWS)

### EKS Cluster
```hcl
# infra/terraform/eks.tf
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = "codeatlas-prod"
  cluster_version = "1.28"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  eks_managed_node_groups = {
    general = {
      desired_size = 3
      min_size     = 3
      max_size     = 10

      instance_types = ["m6i.xlarge"]
      capacity_type  = "ON_DEMAND"
    }
    compute = {
      desired_size = 2
      min_size     = 1
      max_size     = 5

      instance_types = ["c6i.2xlarge"]
      capacity_type  = "ON_DEMAND"
    }
  }

  # Enable cluster autoscaler
  cluster_autoscaler_enabled = true
}
```

### RDS (PostgreSQL)
```hcl
# infra/terraform/rds.tf
module "rds" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 6.0"

  identifier = "codeatlas-db"

  engine               = "postgres"
  engine_version       = "16.1"
  family               = "postgres16"
  major_engine_version = "16"
  instance_class       = "db.r6g.xlarge"

  allocated_storage     = 100
  max_allocated_storage = 1000

  db_name  = "codeatlas"
  username = "codeatlas_admin"
  password = var.db_password

  vpc_security_group_ids = [module.security_group.security_group_id]
  subnet_ids             = module.vpc.database_subnets

  backup_retention_period = 30
  multi_az               = true
  storage_encrypted      = true

  performance_insights_enabled = true
  monitoring_interval          = 60

  # Enable pgvector via parameter group
  create_db_parameter_group = true
  parameter_group_name      = "codeatlas-pgvector"
  parameters = [
    {
      name  = "shared_preload_libraries"
      value = "pg_stat_statements"
    }
  ]
}
```

---

## CI/CD (GitHub Actions)

### Main Pipeline
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_PREFIX: ghcr.io/${{ github.repository }}

jobs:
  # ---------- Lint & Type Check ----------
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
        with:
          version: 8
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: pnpm
      - run: pnpm install --frozen-lockfile
      - run: pnpm lint
      - run: pnpm typecheck

  lint-python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip
      - run: pip install ruff mypy
      - run: ruff check apps/api/
      - run: mypy apps/api/ --ignore-missing-imports

  # ---------- Test ----------
  test:
    runs-on: ubuntu-latest
    needs: [lint, lint-python]
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: codeatlas_test
        ports: ["5432:5432"]
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports: ["6379:6379"]
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
        with:
          version: 8
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: pnpm
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip
      - run: pnpm install --frozen-lockfile
      - run: pip install -r apps/api/requirements.txt
      - run: pnpm test          # Frontend unit tests
      - run: pytest apps/api/ -v --cov=apps/api
      - run: pnpm test:e2e      # Playwright (if not too slow)

  # ---------- Build & Push ----------
  build:
    runs-on: ubuntu-latest
    needs: [test]
    if: github.ref == 'refs/heads/main'
    strategy:
      matrix:
        app: [api, web]
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          context: ./apps/${{ matrix.app }}
          push: true
          tags: |
            ${{ env.IMAGE_PREFIX }}-${{ matrix.app }}:${{ github.sha }}
            ${{ env.IMAGE_PREFIX }}-${{ matrix.app }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # ---------- Deploy ----------
  deploy:
    runs-on: ubuntu-latest
    needs: [build]
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - uses: actions/checkout@v4
      - uses: azure/k8s-set-context@v3
        with:
          method: kubeconfig
          kubeconfig: ${{ secrets.KUBE_CONFIG }}
      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/codeatlas-api \
            api=${{ env.IMAGE_PREFIX }}-api:${{ github.sha }} \
            -n codeatlas
          kubectl set image deployment/codeatlas-web \
            web=${{ env.IMAGE_PREFIX }}-web:${{ github.sha }} \
            -n codeatlas
          kubectl rollout status deployment/codeatlas-api -n codeatlas --timeout=300s
          kubectl rollout status deployment/codeatlas-web -n codeatlas --timeout=300s
```

---

## Environment Configuration

### Development
```env
# .env
DATABASE_URL=postgresql+asyncpg://codeatlas:codeatlas_dev@localhost:5432/codeatlas
REDIS_URL=redis://localhost:6379/0
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
OLLAMA_URL=http://localhost:11434

GITHUB_APP_ID=123456
GITHUB_APP_PRIVATE_KEY_PATH=./private-key.pem
GITHUB_WEBHOOK_SECRET=dev-secret

JWT_SECRET=dev-jwt-secret-change-in-prod
NEXTAUTH_SECRET=dev-nextauth-secret
NEXTAUTH_URL=http://localhost:3000
GITHUB_CLIENT_ID=Iv1.example
GITHUB_CLIENT_SECRET=example

LOG_LEVEL=DEBUG
```

### Production (Kubernetes Secrets)
```yaml
# kubectl create secret generic codeatlas-api-secrets
apiVersion: v1
kind: Secret
metadata:
  name: codeatlas-api-secrets
  namespace: codeatlas
type: Opaque
stringData:
  DATABASE_URL: postgresql+asyncpg://user:pass@rds-endpoint:5432/codeatlas
  REDIS_URL: redis://elasticache-endpoint:6379/0
  JWT_SECRET: <generated>
  GITHUB_APP_PRIVATE_KEY: <base64-encoded-key>
  GITHUB_WEBHOOK_SECRET: <generated>
  S3_ACCESS_KEY: <iam-access-key>
  S3_SECRET_KEY: <iam-secret-key>
  SENTRY_DSN: <sentry-dsn>
```

---

## Scaling Strategy

### Horizontal Scaling
| Component | Trigger | Scale Range | Method |
|-----------|---------|-------------|--------|
| API | CPU > 70% or RPS > 100/pod | 3-20 pods | HPA |
| Worker | Queue depth > 50 | 2-10 pods | KEDA |
| Web | CPU > 70% | 2-10 pods | HPA |

### Vertical Scaling
| Component | Current | Upgrade Path |
|-----------|---------|--------------|
| RDS | db.r6g.xlarge | db.r6g.4xlarge (16 vCPU, 128GB) |
| ElastiCache | cache.r6g.large | cache.r6g.xlarge |
| Node groups | m6i.xlarge | m6i.2xlarge |

### Database Scaling
1. **Read replicas**: Route read queries to replicas
2. **Connection pooling**: PgBouncer (transaction mode)
3. **Partitioning**: Partition `code_nodes` by `repo_id` for large instances
4. **Archival**: Move old repos to cold storage after 90 days

---

## Cost Estimation (Monthly, Production)

| Component | Specification | Cost |
|-----------|--------------|------|
| EKS cluster | 3x m6i.xlarge nodes | $450 |
| RDS PostgreSQL | db.r6g.xlarge, multi-AZ | $550 |
| ElastiCache Redis | cache.r6g.large | $150 |
| S3 storage | 500GB | $12 |
| CloudFront CDN | 1TB transfer | $90 |
| Application Load Balancer | - | $25 |
| ECR (container registry) | 20GB | $2 |
| Route 53 DNS | - | $1 |
| Secrets Manager | - | $5 |
| CloudWatch/monitoring | - | $50 |
| Sentry (errors) | Team plan | $26 |
| **Total** | | **~$1,361/mo** |

### Cost Optimization
- Reserved instances (1-year): ~30% savings
- Spot instances for workers: ~60% savings
- S3 Intelligent-Tiering for old repos
- Auto-suspend dev/staging clusters outside business hours