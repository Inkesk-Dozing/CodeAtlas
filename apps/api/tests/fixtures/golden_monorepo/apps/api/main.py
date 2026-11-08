"""FastAPI application entrypoint."""

from apps.api.routers.health import router as health_router
from apps.api.routers.users import router as users_router
from fastapi import FastAPI, Request

app = FastAPI(title="Synthetic Backend API")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Simple logging middleware."""
    response = await call_next(request)
    return response


app.include_router(health_router)
app.include_router(users_router)

