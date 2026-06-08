"""FastAPI dependency providers."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import Tenant, User
from app.security import decode_access_token, require_role as _require_role

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(slots=True)
class CurrentUser:
    user: User
    tenant: Tenant


async def get_current_user(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    if creds is None or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )
    payload = decode_access_token(creds.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )

    try:
        user_id = UUID(payload["sub"])
        tenant_id = UUID(payload["tid"])
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token payload",
        ) from None

    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled",
        )
    if user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant mismatch",
        )

    tenant = await db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant not found",
        )

    # Stash for downstream consumers (e.g. WS handshake)
    request.state.tenant_id = tenant_id
    request.state.user_id = user_id
    request.state.role = user.role

    return CurrentUser(user=user, tenant=tenant)


def require_role(min_role: str):
    """Return a dependency that asserts the current user is at least `min_role`."""

    async def _checker(cu: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        try:
            _require_role(cu.user.role, min_role)
        except PermissionError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e),
            ) from e
        return cu

    return _checker


async def optional_user(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUser | None:
    """Like get_current_user but returns None on missing/invalid token.

    Used for endpoints that have public AND authenticated behaviour (e.g. /me).
    """
    if not creds or not creds.credentials:
        return None
    try:
        return await get_current_user(request, creds)
    except HTTPException:
        return None
