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
    auth,
    chat,
    graph,
    ingestion,
    issues,
    repos,
    search,
    summaries,
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


@asynccontextmanager
async def lifespan(app: FastAPI):
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
    checks = {"api": "healthy"}

    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://localhost:8000/ready", timeout=2.0)
            checks.update(resp.json().get("checks", {}))
    except Exception:
        pass

    overall = "healthy" if all(v == "healthy" for v in checks.values()) else "degraded"

    from datetime import datetime
    return {
        "status": overall,
        "version": settings.version,
        "checks": checks,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.get("/ready")
async def readiness_check():
    try:
        from sqlalchemy import text

        from database import engine
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ready", "checks": {"database": "healthy"}}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "checks": {"database": str(e)}},
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
app.include_router(search.router, prefix=API_PREFIX)
app.include_router(ingestion.router, prefix=API_PREFIX)
app.include_router(issues.router, prefix=API_PREFIX)
app.include_router(summaries.router, prefix=API_PREFIX)
app.include_router(chat.router, prefix=API_PREFIX)
app.include_router(webhooks.router, prefix=API_PREFIX)
