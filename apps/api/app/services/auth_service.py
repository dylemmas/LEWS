"""Auth service: signup, login, refresh, logout."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RefreshToken, Tenant, User
from app.schemas.auth import AuthResponse, LoginRequest, SignupRequest, TenantDTO, UserDTO
from app.security import (
    create_access_token,
    hash_password,
    hash_refresh_token,
    new_refresh_token,
    verify_password,
)


async def _create_refresh_token(db: AsyncSession, user_id: UUID) -> tuple[str, datetime]:
    raw, digest, expires = new_refresh_token()
    db.add(RefreshToken(user_id=user_id, token_hash=digest, expires_at=expires))
    return raw, expires


def _build_session(user: User, tenant: Tenant, access: str, expires_in: int, refresh: str) -> AuthResponse:
    return AuthResponse(
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
        expires_in=expires_in,
        user=UserDTO.model_validate(user),
        tenant=TenantDTO.model_validate(tenant),
    )


async def signup(db: AsyncSession, req: SignupRequest) -> AuthResponse:
    # uniqueness checks
    slug_check = await db.execute(select(Tenant).where(Tenant.slug == req.tenant_slug))
    if slug_check.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="tenant slug already taken")

    tenant = Tenant(slug=req.tenant_slug, name=req.tenant_name, plan="free")
    db.add(tenant)
    await db.flush()

    user = User(
        tenant_id=tenant.id,
        email=req.email,
        full_name=req.full_name,
        password_hash=hash_password(req.password),
        role="admin",
    )
    db.add(user)
    await db.flush()

    access, ttl = create_access_token(user.id, tenant.id, "admin")
    refresh, _expires = await _create_refresh_token(db, user.id)
    await db.commit()
    return _build_session(user, tenant, access, ttl, refresh)


async def login(db: AsyncSession, req: LoginRequest, tenant_slug: str | None = None) -> AuthResponse:
    # We need to find the user. If multiple tenants share the same email we
    # disambiguate via the X-Tenant header. For MVP we assume one tenant.
    q = select(User).where(User.email == req.email, User.is_active.is_(True))
    res = await db.execute(q)
    user = res.scalar_one_or_none()
    if user is None or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")

    tenant = await db.get(Tenant, user.tenant_id)
    if tenant is None:
        raise HTTPException(status_code=401, detail="invalid credentials")

    access, ttl = create_access_token(user.id, tenant.id, user.role)
    refresh, _expires = await _create_refresh_token(db, user.id)
    await db.commit()
    return _build_session(user, tenant, access, ttl, refresh)


async def refresh(db: AsyncSession, raw_token: str) -> AuthResponse:
    digest = hash_refresh_token(raw_token)
    res = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == digest)
    )
    row = res.scalar_one_or_none()
    if row is None or row.revoked_at is not None or row.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="invalid or expired refresh token")

    user = await db.get(User, row.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="user disabled")
    tenant = await db.get(Tenant, user.tenant_id)
    if tenant is None:
        raise HTTPException(status_code=401, detail="tenant missing")

    # Rotate: revoke old, issue new
    row.revoked_at = datetime.now(timezone.utc)
    access, ttl = create_access_token(user.id, tenant.id, user.role)
    new_raw, _ = await _create_refresh_token(db, user.id)
    await db.commit()
    return _build_session(user, tenant, access, ttl, new_raw)


async def logout(db: AsyncSession, raw_token: str) -> None:
    digest = hash_refresh_token(raw_token)
    res = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == digest)
    )
    row = res.scalar_one_or_none()
    if row is not None and row.revoked_at is None:
        row.revoked_at = datetime.now(timezone.utc)
        await db.commit()
