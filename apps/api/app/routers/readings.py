"""/v1/nodes/{id}/readings — time-series queries."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.deps import CurrentUser, get_current_user
from app.models import Node, SensorReading
from app.schemas.reading import ReadingDTO, ReadingSeries

router = APIRouter(prefix="/v1", tags=["readings"])


def _to_tenant_id(cu: CurrentUser) -> UUID:
    return cu.tenant.id


@router.get("/nodes/{node_id}/readings", response_model=list[ReadingDTO])
async def list_node_readings(
    node_id: UUID,
    start: datetime | None = Query(None),
    end: datetime | None = Query(None),
    limit: int = Query(1000, ge=1, le=10_000),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SensorReading]:
    node = await db.get(Node, node_id)
    if node is None or node.tenant_id != cu.tenant.id:
        raise HTTPException(status_code=404, detail="node not found")

    end = end or datetime.now(timezone.utc)
    start = start or (end - timedelta(hours=24))

    q = (
        select(SensorReading)
        .where(
            SensorReading.node_id == node_id,
            SensorReading.time >= start,
            SensorReading.time <= end,
        )
        .order_by(SensorReading.time.asc())
        .limit(limit)
    )
    res = await db.execute(q)
    return list(res.scalars().all())


@router.get("/nodes/{node_id}/readings/latest", response_model=ReadingDTO | None)
async def latest_reading(
    node_id: UUID,
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SensorReading | None:
    node = await db.get(Node, node_id)
    if node is None or node.tenant_id != cu.tenant.id:
        raise HTTPException(status_code=404, detail="node not found")
    res = await db.execute(
        select(SensorReading)
        .where(SensorReading.node_id == node_id)
        .order_by(SensorReading.time.desc())
        .limit(1)
    )
    return res.scalar_one_or_none()


@router.get("/sites/{site_id}/readings", response_model=list[ReadingDTO])
async def list_site_readings(
    site_id: UUID,
    start: datetime | None = Query(None),
    end: datetime | None = Query(None),
    limit: int = Query(2000, ge=1, le=20_000),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SensorReading]:
    end = end or datetime.now(timezone.utc)
    start = start or (end - timedelta(hours=24))

    q = (
        select(SensorReading)
        .where(
            SensorReading.tenant_id == cu.tenant.id,
            SensorReading.site_id == site_id,
            SensorReading.time >= start,
            SensorReading.time <= end,
        )
        .order_by(SensorReading.time.asc())
        .limit(limit)
    )
    res = await db.execute(q)
    return list(res.scalars().all())


@router.get("/nodes/{node_id}/readings/series", response_model=list[ReadingSeries])
async def node_series(
    node_id: UUID,
    agg: Literal["15m", "1h"] = "1h",
    hours: int = Query(24, ge=1, le=720),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ReadingSeries]:
    """Time-bucketed aggregates for chart rendering. Pulls from
    the sensor_readings_hourly continuous aggregate when possible."""
    node = await db.get(Node, node_id)
    if node is None or node.tenant_id != cu.tenant.id:
        raise HTTPException(status_code=404, detail="node not found")

    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=hours)

    bucket = "15 minutes" if agg == "15m" else "1 hour"
    sql = f"""
        SELECT
            time_bucket('{bucket}', time) AS bucket,
            AVG(severity)::float AS avg_severity,
            SUM(rain_tips_15m)::float AS sum_rain,
            AVG(accel_rms_mg)::float AS avg_accel,
            AVG(tilt_delta_ddeg)::float AS avg_tilt,
            AVG(crack_delta_mm10)::float AS avg_crack,
            AVG(battery_mv)::float AS avg_battery,
            COUNT(*)::int AS count
        FROM sensor_readings
        WHERE node_id = :node_id AND time >= :start AND time <= :end
        GROUP BY bucket
        ORDER BY bucket ASC
    """
    from sqlalchemy import text

    res = await db.execute(text(sql), {"node_id": str(node_id), "start": start, "end": end})
    rows = res.mappings().all()
    return [
        ReadingSeries(
            bucket=r["bucket"],
            avg_severity=r["avg_severity"] or 0.0,
            sum_rain=r["sum_rain"] or 0.0,
            avg_accel=r["avg_accel"] or 0.0,
            avg_tilt=r["avg_tilt"] or 0.0,
            avg_crack=r["avg_crack"] or 0.0,
            avg_battery=r["avg_battery"],
            count=r["count"] or 0,
        )
        for r in rows
    ]
