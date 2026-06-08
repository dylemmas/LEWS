"""Alert schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class NotificationLogEntry(BaseModel):
    channel: Literal["sms", "email", "ws"]
    target: str
    sent_at: datetime
    ok: bool
    error: str | None = None


class AlertDTO(BaseModel):
    id: UUID
    tenant_id: UUID
    node_id: UUID
    site_id: UUID
    severity: int
    state: Literal["open", "acknowledged", "resolved", "dismissed"]
    dedup_key: str
    title: str
    message: str
    trigger_payload: dict[str, Any] | None
    first_seen_at: datetime
    last_seen_at: datetime
    acknowledged_at: datetime | None
    acknowledged_by: UUID | None
    resolved_at: datetime | None
    resolved_by: UUID | None
    dismissed_at: datetime | None
    dismissed_by: UUID | None
    dismiss_reason: str | None
    ml_prob: float | None
    notification_log: list[NotificationLogEntry]

    model_config = {"from_attributes": True}


class AlertAckRequest(BaseModel):
    note: str | None = Field(None, max_length=500)


class AlertResolveRequest(BaseModel):
    note: str | None = Field(None, max_length=500)


class AlertDismissRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)


class KPISummary(BaseModel):
    active_alerts: int
    critical_alerts: int
    warning_alerts: int
    online_nodes: int
    total_nodes: int
    avg_battery_mv: float | None
    rainfall_24h_mm: float
    last_updated: datetime
