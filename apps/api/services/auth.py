from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from models import User

security = HTTPBearer(auto_error=False)


def _signing_key() -> tuple[str, str]:
    """Return (key, algorithm).

    Uses RS256 with a PEM private key when `jwt_private_key_path` points to an
    existing file; otherwise falls back to HS256 with the shared secret so the
    service works out of the box in development.
    """
    if settings.jwt_private_key_path:
        key_path = Path(settings.jwt_private_key_path)
        if key_path.exists():
            return key_path.read_text(), "RS256"
    return settings.jwt_secret, "HS256"


def create_access_token(user_id: str, role: str = "member", org_id: str | None = None) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "org_id": org_id,
        "role": role,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_access_expiry_minutes)).timestamp()),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
    }
    key, algorithm = _signing_key()
    return jwt.encode(payload, key, algorithm=algorithm)


def create_refresh_token(user_id: str, jti: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "jti": jti,
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=settings.jwt_refresh_expiry_days)).timestamp()),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
    }
    key, algorithm = _signing_key()
    return jwt.encode(payload, key, algorithm=algorithm)


def decode_token(token: str) -> dict[str, Any]:
    key, algorithm = _signing_key()
    try:
        return jwt.decode(
            token,
            key,
            algorithms=[algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e!s}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


def require_role(*roles: str):
    async def dependency(user: User = Depends(get_current_user)) -> User:
        return user

    return dependency


async def get_user_role(db: AsyncSession, user_id: str, org_id: str | None = None) -> str:
    from models import OrgMember

    query = select(OrgMember.role).where(OrgMember.user_id == user_id)
    if org_id:
        query = query.where(OrgMember.org_id == org_id)
    result = await db.execute(query.limit(1))
    role = result.scalar_one_or_none()
    return role or "member"


async def exchange_github_code(code: str) -> dict[str, Any]:
    timeout = httpx.Timeout(15.0, connect=5.0)
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
            token_resp = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": settings.github_client_id,
                    "client_secret": settings.github_client_secret,
                    "code": code,
                },
            )
            token_data = token_resp.json()
            if "access_token" not in token_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange GitHub code",
                )

            auth_headers = {
                "Authorization": f"Bearer {token_data['access_token']}",
                "Accept": "application/vnd.github+json",
            }
            user_resp = await client.get("https://api.github.com/user", headers=auth_headers)
            user_resp.raise_for_status()
            github_user = user_resp.json()

            email_resp = await client.get(
                "https://api.github.com/user/emails", headers=auth_headers
            )
            emails = email_resp.json() if email_resp.status_code == 200 else []
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="GitHub OAuth service unreachable",
        ) from exc

    primary_email = next(
        (e["email"] for e in emails if e.get("primary") and e.get("verified")),
        None,
    )

    return {
        "github_id": github_user["id"],
        "username": github_user["login"],
        "email": primary_email or github_user.get("email"),
        "avatar_url": github_user.get("avatar_url"),
        "name": github_user.get("name"),
        "access_token": token_data["access_token"],
    }
