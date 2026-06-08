"""JWT helpers — access + refresh token issue/verify."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

_settings = get_settings()

_pwd_ctx = CryptContext(schemes=["argon2"], deprecated="auto")


# --- password hashing ---

def hash_password(plain: str) -> str:
    return _pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _pwd_ctx.verify(plain, hashed)
    except Exception:
        return False


# --- access tokens ---

def create_access_token(user_id: UUID, tenant_id: UUID, role: str) -> tuple[str, int]:
    """Return (jwt, expires_in_seconds)."""
    ttl = timedelta(minutes=_settings.access_ttl_min)
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "tid": str(tenant_id),
        "role": role,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + ttl).timestamp()),
    }
    token = jwt.encode(payload, _settings.jwt_secret, algorithm=_settings.jwt_alg)
    return token, _settings.access_ttl_min * 60


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(
            token,
            _settings.jwt_secret,
            algorithms=[_settings.jwt_alg],
            options={"require": ["exp", "sub", "tid", "type"]},
        )
    except JWTError:
        return None


# --- refresh tokens ---

def new_refresh_token() -> tuple[str, str, datetime]:
    """Return (raw_token, sha256_hash, expires_at)."""
    raw = secrets.token_urlsafe(48)
    digest = hashlib.sha256(raw.encode()).hexdigest()
    expires = datetime.now(timezone.utc) + timedelta(days=_settings.refresh_ttl_days)
    return raw, digest, expires


def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


# --- helpers for tests / non-default cases ---

def make_jwt(
    sub: str,
    tid: str,
    role: str = "viewer",
    ttl_sec: int = 3600,
    typ: Literal["access", "refresh"] = "access",
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "tid": tid,
        "role": role,
        "type": typ,
        "iat": int(now.timestamp()),
        "exp": int(now.timestamp()) + ttl_sec,
    }
    return jwt.encode(payload, _settings.jwt_secret, algorithm=_settings.jwt_alg)
