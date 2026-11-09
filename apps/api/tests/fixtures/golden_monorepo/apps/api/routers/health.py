"""FastAPI health check router."""

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
def health_check():
    """Service liveness probe."""
    return {"status": "healthy"}

