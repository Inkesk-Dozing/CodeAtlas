import logging
import sys
import time
from contextlib import asynccontextmanager
from datetime import UTC

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from config import settings
from middleware import install_middleware
from routers import (
    achievements,
    auth,
    badges,
    chat,
    chronos,
    flight_simulator,
    graph,
    ingestion,
    issues,
    omniquery,
    prompts,
    repos,
    search,
    summaries,
    telemetry,
    webhooks,
)

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
    stream=sys.stdout,
)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start

        if not request.url.path.startswith("/metrics"):
            logger.debug(
                "%s %s -> %d (%.3fs)",
                request.method,
                request.url.path,
                response.status_code,
                duration,
            )
        return response


_app_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _app_start_time
    _app_start_time = time.time()
    logger.info("CodeAtlas API starting up (env=%s)", settings.environment)
    yield
    logger.info("CodeAtlas API shutting down")


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="AI-Augmented Monorepo Onboarding Engine",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
)

app.add_middleware(MetricsMiddleware)
install_middleware(app)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred",
                "request_id": str(request.headers.get("x-request-id", "")),
            }
        },
    )


@app.get("/health")
async def health_check():
    """Liveness probe: returns HTTP 200 with server status, uptime, and version without external calls."""
    from datetime import datetime

    now = time.time()
    uptime_seconds = round(now - _app_start_time, 3)

    return {
        "status": "healthy",
        "version": settings.version,
        "uptime_seconds": uptime_seconds,
        "checks": {"api": "healthy"},
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.get("/ready")
async def readiness_check():
    """Readiness probe: validates database, redis, and optional ollama connectivity."""
    checks: dict[str, str] = {}
    is_ready = True

    # 1. Database check
    try:
        from sqlalchemy import text

        from database import engine

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {e}"
        is_ready = False

    # 2. Redis check
    try:
        import redis.asyncio as aioredis

        redis_client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_timeout=1.0,
            socket_connect_timeout=1.0,
        )
        await redis_client.ping()
        await redis_client.aclose()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {e}"
        is_ready = False

    # 3. Ollama check (dependency check)
    try:
        import httpx

        async with httpx.AsyncClient(timeout=1.0) as client:
            resp = await client.get(f"{settings.ollama_url.rstrip('/')}/api/tags")
            checks["ollama"] = "healthy" if resp.status_code == 200 else f"degraded: status {resp.status_code}"
    except Exception:
        checks["ollama"] = "unavailable"

    status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE
    response_status = "ready" if is_ready else "not_ready"

    return JSONResponse(
        status_code=status_code,
        content={"status": response_status, "checks": checks},
    )


@app.get("/metrics")
async def metrics():
    try:
        from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
    except ImportError:
        return JSONResponse(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            content={"detail": "prometheus_client not installed"},
        )
    from starlette.responses import Response
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


API_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(repos.router, prefix=API_PREFIX)
app.include_router(graph.router, prefix=API_PREFIX)
app.include_router(chronos.router, prefix=API_PREFIX)
app.include_router(omniquery.router, prefix=API_PREFIX)
app.include_router(search.router, prefix=API_PREFIX)
app.include_router(ingestion.router, prefix=API_PREFIX)
app.include_router(issues.router, prefix=API_PREFIX)
app.include_router(summaries.router, prefix=API_PREFIX)
app.include_router(chat.router, prefix=API_PREFIX)
app.include_router(webhooks.router, prefix=API_PREFIX)
app.include_router(badges.router, prefix=API_PREFIX)
app.include_router(telemetry.router, prefix=API_PREFIX)
app.include_router(flight_simulator.router, prefix=API_PREFIX)
app.include_router(prompts.router, prefix=API_PREFIX)
app.include_router(achievements.router, prefix=API_PREFIX)
