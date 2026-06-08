"""Role-based access control helpers."""

from __future__ import annotations

from typing import Iterable


ROLE_RANK: dict[str, int] = {
    "viewer": 1,
    "operator": 2,
    "admin": 3,
}


def role_at_least(actual: str, required: str) -> bool:
    """Return True if `actual` is at least as privileged as `required`."""
    return ROLE_RANK.get(actual, 0) >= ROLE_RANK.get(required, 0)


def require_role(actual: str | None, required: str) -> None:
    """Raise PermissionError if `actual` is below `required`."""
    if not actual or not role_at_least(actual, required):
        raise PermissionError(f"role '{actual}' < required '{required}'")


def in_scope(tenant_ids: Iterable[str], tenant_id: str) -> bool:
    return tenant_id in set(tenant_ids)
