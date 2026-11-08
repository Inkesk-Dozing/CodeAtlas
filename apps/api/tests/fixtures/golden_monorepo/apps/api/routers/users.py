"""FastAPI router for user management."""

from apps.api.models.user import UserCreate, UserResponse
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(prefix="/users", tags=["users"])


def verify_auth_token(token: str = "default_token") -> bool:
    """Mock authentication dependency."""
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return True


@router.get("/", response_model=list[UserResponse])
async def list_users(limit: int = 50, is_auth: bool = Depends(verify_auth_token)):
    """Retrieve active user list."""
    return []


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, is_auth: bool = Depends(verify_auth_token)):
    """Create a new user account."""
    return {"id": "new_1", "name": payload.name, "email": payload.email, "is_active": True, "created_at": "2026-01-01T00:00:00"}


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: str):
    """Retrieve a single user by ID."""
    return {"id": user_id, "name": "User", "email": "user@example.com", "is_active": True, "created_at": "2026-01-01T00:00:00"}

