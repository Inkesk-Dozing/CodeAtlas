import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import OrgMember, User
from schemas import AuthCallbackRequest, TokenResponse, UserResponse
from services.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    exchange_github_code,
    get_current_user,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/callback", response_model=TokenResponse)
async def auth_callback(
    payload: AuthCallbackRequest,
    db: AsyncSession = Depends(get_db),
):
    github_data = await exchange_github_code(payload.code)

    result = await db.execute(select(User).where(User.github_id == github_data["github_id"]))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            id=str(uuid.uuid4()),
            github_id=github_data["github_id"],
            username=github_data["username"],
            email=github_data["email"],
            avatar_url=github_data["avatar_url"],
            name=github_data["name"],
            last_login_at=datetime.now(UTC),
        )
        db.add(user)
        await db.flush()
    else:
        user.username = github_data["username"]
        user.email = github_data["email"]
        user.avatar_url = github_data["avatar_url"]
        user.name = github_data["name"]
        user.last_login_at = datetime.now(UTC)
        await db.flush()

    role = "member"
    membership = await db.execute(
        select(OrgMember).where(OrgMember.user_id == user.id).limit(1)
    )
    member = membership.scalar_one_or_none()
    org_id = member.org_id if member else None

    access_token = create_access_token(str(user.id), role=role, org_id=org_id)
    refresh_token = create_refresh_token(str(user.id), jti=str(uuid.uuid4()))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=1800,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    user: User = Depends(get_current_user),
):
    return user


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db),
):
    payload = decode_token(refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    new_access = create_access_token(str(user.id))
    new_refresh = create_refresh_token(str(user.id), jti=str(uuid.uuid4()))

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        expires_in=1800,
    )
