"""Dedup key generation for alert coalescing."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID


def make_dedup_key(node_id: UUID, severity: int, t: datetime, window_sec: int = 300) -> str:
    """Bucket time into N-second windows so repeated readings coalesce.

    Format: f"{node_id}|{severity}|{bucket}"
    """
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    bucket = int(t.timestamp()) // window_sec
    return f"{node_id}|{severity}|{bucket}"
