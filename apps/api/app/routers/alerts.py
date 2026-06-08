"""/v1/alerts/* — list, ack, resolve, dismiss, KPIs."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.deps import CurrentUser, get_current_user, require_role
from app.models import Alert, Node
from app.schemas.alert import (
    AlertAckRequest,
    AlertDismissRequest,
    AlertDTO,
    AlertResolveRequest,
    KPISummary,
)
from app.services.ws_manager import ws_manager

router = APIRouter(prefix="/v1/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertDTO])
async def list_alerts(
    state: Literal["open", "acknowledged", "resolved", "dismissed"] | None = Query(None),
    severity: int | None = Query(None, ge=0, le=3),
    node_id: UUID | None = Query(None),
    since: datetime | None = Query(None),
    limit: int = Query(200, ge=1, le=1000),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Alert]:
    q = select(Alert).where(Alert.tenant_id == cu.tenant.id)
    if state:
        q = q.where(Alert.state == state)
    if severity is not None:
        q = q.where(Alert.severity == severity)
    if node_id:
        q = q.where(Alert.node_id == node_id)
    if since:
        q = q.where(Alert.last_seen_at >= since)
    q = q.order_by(Alert.last_seen_at.desc()).limit(limit)
    res = await db.execute(q)
    return list(res.scalars().all())


@router.get("/kpi", response_model=KPISummary)
async def kpis(
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> KPISummary:
    # active alerts
    res = await db.execute(
        select(func.count(Alert.id), Alert.severity)
        .where(Alert.tenant_id == cu.tenant.id, Alert.state.in_(["open", "acknowledged"]))
        .group_by(Alert.severity)
    )
    sev_counts = {row[1]: row[0] for row in res.all()}
    active = sum(sev_counts.values())
    critical = sev_counts.get(3, 0)
    warning = sev_counts.get(2, 0)

    # node counts
    res = await db.execute(
        select(Node.status, func.count(Node.id)).where(Node.tenant_id == cu.tenant.id).group_by(Node.status)
    )
    node_counts = {row[0]: row[1] for row in res.all()}
    total_nodes = sum(node_counts.values())
    online_nodes = node_counts.get("online", 0)

    # average battery
    res = await db.execute(
        select(func.avg(Node.battery_mv)).where(
            Node.tenant_id == cu.tenant.id, Node.battery_mv.is_not(None)
        )
    )
    avg_battery = res.scalar() or None
    if avg_battery is not None:
        avg_battery = float(avg_battery)

    return KPISummary(
        active_alerts=active,
        critical_alerts=critical,
        warning_alerts=warning,
        online_nodes=online_nodes,
        total_nodes=total_nodes,
        avg_battery_mv=avg_battery,
        rainfall_24h_mm=0.0,  # computed by readings router; left as a placeholder
        last_updated=datetime.now(timezone.utc),
    )


@router.post("/{alert_id}/ack", response_model=AlertDTO)
async def ack_alert(
    alert_id: UUID,
    payload: AlertAckRequest,
    cu: CurrentUser = Depends(require_role("operator")),
    db: AsyncSession = Depends(get_db),
) -> Alert:
    a = await db.get(Alert, alert_id)
    if a is None or a.tenant_id != cu.tenant.id:
        raise HTTPException(status_code=404, detail="alert not found")
    if a.state not in ("open", "acknowledged"):
        raise HTTPException(status_code=409, detail=f"cannot ack alert in state {a.state}")
    a.state = "acknowledged"
    a.acknowledged_at = datetime.now(timezone.utc)
    a.acknowledged_by = cu.user.id
    await db.commit()
    await db.refresh(a)
    try:
        await ws_manager.emit_alert(a.tenant_id, a)
    except Exception:
        pass
    return a


@router.post("/{alert_id}/resolve", response_model=AlertDTO)
async def resolve_alert(
    alert_id: UUID,
    payload: AlertResolveRequest,
    cu: CurrentUser = Depends(require_role("operator")),
    db: AsyncSession = Depends(get_db),
) -> Alert:
    a = await db.get(Alert, alert_id)
    if a is None or a.tenant_id != cu.tenant.id:
        raise HTTPException(status_code=404, detail="alert not found")
    if a.state == "resolved":
        raise HTTPException(status_code=409, detail="alert already resolved")
    a.state = "resolved"
    a.resolved_at = datetime.now(timezone.utc)
    a.resolved_by = cu.user.id
    await db.commit()
    await db.refresh(a)
    try:
        await ws_manager.emit_alert(a.tenant_id, a)
    except Exception:
        pass
    return a


@router.post("/{alert_id}/dismiss", response_model=AlertDTO)
async def dismiss_alert(
    alert_id: UUID,
    payload: AlertDismissRequest,
    cu: CurrentUser = Depends(require_role("operator")),
    db: AsyncSession = Depends(get_db),
) -> Alert:
    a = await db.get(Alert, alert_id)
    if a is None or a.tenant_id != cu.tenant.id:
        raise HTTPException(status_code=404, detail="alert not found")
    if a.state == "resolved":
        raise HTTPException(status_code=409, detail="alert already resolved")
    a.state = "dismissed"
    a.dismissed_at = datetime.now(timezone.utc)
    a.dismissed_by = cu.user.id
    a.dismiss_reason = payload.reason
    await db.commit()
    await db.refresh(a)
    try:
        await ws_manager.emit_alert(a.tenant_id, a)
    except Exception:
        pass
    return a
