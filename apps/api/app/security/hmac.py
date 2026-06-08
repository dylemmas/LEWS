"""HMAC signature verification for /v1/ingest/* endpoints."""

from __future__ import annotations

import hmac
from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.config import get_settings

_settings = get_settings()


def verify_ingest_hmac(body: bytes, header: str | None, secret: str | None = None) -> None:
    """Raise HTTPException if HMAC signature is missing or invalid.

    Header format: X-Signature: t=<unix>,v1=<hex(hmac-sha256(secret, "<t>." + body))>
    Reject if `t` is > 5min skewed (configurable via INGEST_MAX_SKEW_SEC).

    Args:
        body: raw request body as bytes
        header: value of X-Signature header (or None)
        secret: secret key (defaults to INGEST_HMAC_SECRET from env)
    """
    if secret is None:
        secret = _settings.ingest_hmac_secret

    if not header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Signature header",
        )

    try:
        parts = dict(p.split("=", 1) for p in header.split(","))
        t = int(parts["t"])
        v1 = parts["v1"]
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid X-Signature format",
        ) from None

    now = int(datetime.now(timezone.utc).timestamp())
    if abs(now - t) > _settings.ingest_max_skew_sec:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Signature timestamp skew too large ({abs(now - t)}s > {_settings.ingest_max_skew_sec}s)",
        )

    # build expected payload: "<t>." + body
    payload = f"{t}.".encode() + body
    expected = hmac.new(secret.encode(), payload, "sha256").hexdigest()

    if not hmac.compare_digest(expected, v1):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="HMAC signature mismatch",
        )


def build_ingest_hmac(body: bytes, t: int | None = None, secret: str | None = None) -> str:
    """Generate an X-Signature header value. Used by the simulator."""
    if secret is None:
        secret = _settings.ingest_hmac_secret
    if t is None:
        t = int(datetime.now(timezone.utc).timestamp())
    payload = f"{t}.".encode() + body
    v1 = hmac.new(secret.encode(), payload, "sha256").hexdigest()
    return f"t={t},v1={v1}"
