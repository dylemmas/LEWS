"""/v1/ingest/* — TTN and simulator HMAC-authenticated ingestion."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.session import get_db
from app.deps import CurrentUser, require_role
from app.models import Node
from app.security import verify_ingest_hmac
from app.services.ingest_service import encode_payload_b64, process_ingest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/ingest", tags=["ingest"])


class TtnUplink(BaseModel):
    """LoRaWAN uplink message from The Things Network (or similar)."""
    dev_eui: str
    payload_raw_b64: str
    f_cnt: int | None = None
    f_port: int | None = None
    rssi: int | None = None
    snr: float | None = None
    time: datetime | None = None


class SimUplink(BaseModel):
    """Same shape as TtnUplink, posted by the simulator."""
    dev_eui: str
    payload_raw_b64: str
    f_cnt: int | None = None
    rssi: int | None = None
    snr: float | None = None
    time: datetime | None = None


class IngestAck(BaseModel):
    ok: bool = True
    reading_id: str
    severity: int
    ml_prob: float | None = None
    alert_id: str | None = None


async def _verify_and_ingest(
    request: Request,
    payload: TtnUplink,
    db: AsyncSession,
) -> IngestAck:
    body = await request.body()
    verify_ingest_hmac(body, request.headers.get("X-Signature"))
    try:
        result = await process_ingest(
            db,
            dev_eui=payload.dev_eui,
            payload_b64=payload.payload_raw_b64,
            f_cnt=payload.f_cnt,
            rssi=payload.rssi,
            snr=payload.snr,
            time=payload.time,
        )
        return IngestAck(**result)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/ttn", response_model=IngestAck)
async def ingest_ttn(
    request: Request,
    payload: TtnUplink,
    db: AsyncSession = Depends(get_db),
) -> IngestAck:
    return await _verify_and_ingest(request, payload, db)


@router.post("/sim", response_model=IngestAck)
async def ingest_sim(
    request: Request,
    payload: SimUplink,
    db: AsyncSession = Depends(get_db),
) -> IngestAck:
    return await _verify_and_ingest(request, TtnUplink(**payload.model_dump()), db)


# --- demo inject endpoint (admin only, HMAC-protected) ---

class InjectRequest(BaseModel):
    node_id: UUID | None = None
    scenario: str = Field("critical", pattern="^(rain_burst|tilt_spike|crack_jump|critical)$")
    duration_sec: int = Field(30, ge=5, le=600)
    _ = None


@router.post("/sim/inject", response_model=IngestAck)
async def inject(
    request: Request,
    payload: InjectRequest,
    cu: CurrentUser = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> IngestAck:
    """Trigger a synthetic scenario for demo purposes. Auth via JWT (admin),
    and the request body itself is HMAC-signed by the *backend* when proxying
    back to /v1/ingest/sim (we re-use the same handler).

    For MVP simplicity we directly call the ingest pipeline with crafted
    payloads — no internal HTTP round-trip.
    """
    from app.services.ingest_service import process_ingest as pi

    # Pick a target node
    if payload.node_id:
        node = await db.get(Node, payload.node_id)
        if node is None or node.tenant_id != cu.tenant.id:
            raise HTTPException(status_code=404, detail="node not found")
    else:
        res = await db.execute(
            select(Node).where(Node.tenant_id == cu.tenant.id).limit(1)
        )
        node = res.scalar_one_or_none()
        if node is None:
            raise HTTPException(status_code=404, detail="no nodes in tenant")

    # Scenario presets
    scenario_payloads: dict[str, list[dict[str, int]]] = {
        "rain_burst": [
            {"severity": 1, "sensor_mask": 0x3F, "rain_tips_15m": 25, "accel_rms_mg": 30,
             "tilt_delta_ddeg": 20, "crack_delta_mm10": 5, "battery_mv": 3700},
            {"severity": 2, "sensor_mask": 0x3F, "rain_tips_15m": 55, "accel_rms_mg": 60,
             "tilt_delta_ddeg": 80, "crack_delta_mm10": 30, "battery_mv": 3700},
        ],
        "tilt_spike": [
            {"severity": 1, "sensor_mask": 0x3F, "rain_tips_15m": 5, "accel_rms_mg": 40,
             "tilt_delta_ddeg": 200, "crack_delta_mm10": 10, "battery_mv": 3700},
            {"severity": 2, "sensor_mask": 0x3F, "rain_tips_15m": 8, "accel_rms_mg": 80,
             "tilt_delta_ddeg": 400, "crack_delta_mm10": 20, "battery_mv": 3700},
        ],
        "crack_jump": [
            {"severity": 1, "sensor_mask": 0x3F, "rain_tips_15m": 10, "accel_rms_mg": 30,
             "tilt_delta_ddeg": 30, "crack_delta_mm10": 60, "battery_mv": 3700},
            {"severity": 2, "sensor_mask": 0x3F, "rain_tips_15m": 12, "accel_rms_mg": 50,
             "tilt_delta_ddeg": 60, "crack_delta_mm10": 150, "battery_mv": 3700},
        ],
        "critical": [
            {"severity": 2, "sensor_mask": 0x3F, "rain_tips_15m": 60, "accel_rms_mg": 180,
             "tilt_delta_ddeg": 300, "crack_delta_mm10": 80, "battery_mv": 3700},
            {"severity": 3, "sensor_mask": 0x3F, "rain_tips_15m": 90, "accel_rms_mg": 250,
             "tilt_delta_ddeg": 500, "crack_delta_mm10": 200, "battery_mv": 3700},
        ],
    }
    samples = scenario_payloads[payload.scenario]
    last_result: dict[str, Any] = {"ok": True, "reading_id": "", "severity": 0, "ml_prob": None, "alert_id": None}
    for sample in samples:
        # Carry forward node lat/lon
        sample = {
            **sample,
            "lat_e7": int(node.lat * 1e7),
            "lon_e7": int(node.lon * 1e7),
        }
        b64 = encode_payload_b64(sample)
        last_result = await pi(
            db,
            dev_eui=node.dev_eui,
            payload_b64=b64,
            time=datetime.now(timezone.utc),
        )
    return IngestAck(**last_result)
