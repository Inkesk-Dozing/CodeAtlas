"""Request ID propagation and per-client sliding-window rate limiting."""
from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict, deque

from fastapi import FastAPI, Request, Response

logger = logging.getLogger("codeatlas.http")

RATE_LIMIT_WINDOW = 60.0
RATE_LIMIT_MAX_DEFAULT = 120
RATE_LIMIT_MAX_HEAVY = 20  # per window, for search/chat/analyze endpoints

HEAVY_PATH_MARKERS = ("/search", "/chat", "/analyze", "/summary", "/architecture")

_rate_buckets: dict[str, deque[float]] = defaultdict(deque)
_last_prune = 0.0


def _client_key(request: Request) -> str:
    auth = request.headers.get("authorization", "")
    if auth:
        return auth[-24:]
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _prune(now: float) -> None:
    global _last_prune
    if now - _last_prune < RATE_LIMIT_WINDOW:
        return
    _last_prune = now
    cutoff = now - RATE_LIMIT_WINDOW
    for key in list(_rate_buckets):
        bucket = _rate_buckets[key]
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if not bucket:
            del _rate_buckets[key]


def install_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        request.state.request_id = request_id

        heavy = any(marker in request.url.path for marker in HEAVY_PATH_MARKERS)
        limit = RATE_LIMIT_MAX_HEAVY if heavy else RATE_LIMIT_MAX_DEFAULT

        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            now = time.time()
            _prune(now)
            bucket = _rate_buckets[_client_key(request)]
            while bucket and bucket[0] < now - RATE_LIMIT_WINDOW:
                bucket.popleft()
            if len(bucket) >= limit:
                reset = int(bucket[0] + RATE_LIMIT_WINDOW - now)
                return Response(
                    content='{"error":{"code":"RATE_LIMITED","message":"Too many requests"}}',
                    status_code=429,
                    media_type="application/json",
                    headers={
                        "X-Request-ID": request_id,
                        "Retry-After": str(max(1, reset)),
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                    },
                )
            bucket.append(now)
            remaining = limit - len(bucket)
        else:
            remaining = limit

        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "unhandled error request_id=%s path=%s", request_id, request.url.path
            )
            raise

        response.headers["X-Request-ID"] = request_id
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        return response
