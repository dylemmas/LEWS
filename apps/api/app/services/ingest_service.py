"""Ingest service: decode the 20-byte binary payload, persist, enqueue worker."""

from __future__ import annotations

import base64
import logging
import struct
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Node, SensorReading
from app.services.ml_service import ml_service
from app.services.ws_manager import ws_manager

logger = logging.getLogger(__name__)


# --- payload codec (mirror of packages/shared-types/src/payload.ts) ---

PAYLOAD_SIZE = 20


def decode_payload_b64(b64: str) -> dict[str, Any]:
    raw = base64.b64decode(b64)
    if len(raw) < PAYLOAD_SIZE:
        raise ValueError(f"payload too short: {len(raw)} bytes (expected {PAYLOAD_SIZE})")
    severity = raw[0]
    sensor_mask = raw[1]
    rain_tips = struct.unpack_from("<H", raw, 2)[0]
    accel_rms = struct.unpack_from("<H", raw, 4)[0]
    tilt = struct.unpack_from("<h", raw, 6)[0]
    crack = struct.unpack_from("<h", raw, 8)[0]
    lat_e7 = struct.unpack_from("<i", raw, 10)[0]
    lon_e7 = struct.unpack_from("<i", raw, 14)[0]
    battery_mv = struct.unpack_from("<H", raw, 18)[0]
    return {
        "severity": severity,
        "sensor_mask": sensor_mask,
        "rain_tips_15m": rain_tips,
        "accel_rms_mg": accel_rms,
        "tilt_delta_ddeg": tilt,
        "crack_delta_mm10": crack,
        "lat_e7": lat_e7,
        "lon_e7": lon_e7,
        "battery_mv": battery_mv,
    }


def encode_payload_b64(d: dict[str, Any]) -> str:
    buf = bytearray(PAYLOAD_SIZE)
    buf[0] = d["severity"] & 0xFF
    buf[1] = d["sensor_mask"] & 0xFF
    struct.pack_into("<H", buf, 2, d["rain_tips_15m"] & 0xFFFF)
    struct.pack_into("<H", buf, 4, d["accel_rms_mg"] & 0xFFFF)
    struct.pack_into("<h", buf, 6, max(-32768, min(32767, d["tilt_delta_ddeg"])))
    struct.pack_into("<h", buf, 8, max(-32768, min(32767, d["crack_delta_mm10"])))
    struct.pack_into("<i", buf, 10, int(d["lat_e7"]) & 0xFFFFFFFF)
    struct.pack_into("<i", buf, 14, int(d["lon_e7"]) & 0xFFFFFFFF)
    struct.pack_into("<H", buf, 18, d["battery_mv"] & 0xFFFF)
    return base64.b64encode(bytes(buf)).decode()


# --- ingest path ---

async def _resolve_node(db: AsyncSession, dev_eui: str) -> Node | None:
    res = await db.execute(select(Node).where(Node.dev_eui == dev_eui))
    return res.scalar_one_or_none()


async def process_ingest(
    db: AsyncSession,
    *,
    dev_eui: str,
    payload_b64: str,
    f_cnt: int | None = None,
    rssi: int | None = None,
    snr: float | None = None,
    time: datetime | None = None,
) -> dict[str, Any]:
    """Decode, persist, and enqueue the worker for ML + alert evaluation.

    Returns: {ok, reading_id, severity, ml_prob, alert_id}
    """
    decoded = decode_payload_b64(payload_b64)
    if time is None:
        time = datetime.now(timezone.utc)

    node = await _resolve_node(db, dev_eui)
    if node is None:
        raise LookupError(f"Unknown dev_eui: {dev_eui}")

    reading = SensorReading(
        time=time,
        tenant_id=node.tenant_id,
        node_id=node.id,
        site_id=node.site_id,
        severity=decoded["severity"],
        sensor_mask=decoded["sensor_mask"],
        rain_tips_15m=decoded["rain_tips_15m"],
        accel_rms_mg=decoded["accel_rms_mg"],
        tilt_delta_ddeg=decoded["tilt_delta_ddeg"],
        crack_delta_mm10=decoded["crack_delta_mm10"],
        battery_mv=decoded["battery_mv"],
        f_cnt=f_cnt,
        rssi=rssi,
        snr=snr,
        raw_payload_b64=payload_b64,
    )
    db.add(reading)

    # Update node status (online, last_seen, battery, location)
    node.status = "online"
    node.last_seen_at = time
    node.battery_mv = decoded["battery_mv"]
    if decoded["lat_e7"] != 0 and decoded["lon_e7"] != 0:
        node.lat = decoded["lat_e7"] / 1e7
        node.lon = decoded["lon_e7"] / 1e7

    await db.flush()  # surface FK errors before we commit
    await db.commit()

    # Push the reading to WS immediately (low latency, before ML)
    reading_payload = {
        "type": "reading",
        "tenant_id": str(reading.tenant_id),
        "node_id": str(reading.node_id),
        "site_id": str(reading.site_id),
        "time": reading.time.isoformat(),
        "severity": reading.severity,
        "sensor_mask": reading.sensor_mask,
        "rain_tips_15m": reading.rain_tips_15m,
        "accel_rms_mg": reading.accel_rms_mg,
        "tilt_delta_ddeg": reading.tilt_delta_ddeg,
        "crack_delta_mm10": reading.crack_delta_mm10,
        "battery_mv": reading.battery_mv,
        "ml_prob": None,
        "lat": node.lat,
        "lon": node.lon,
    }
    try:
        await ws_manager.emit_reading(reading.tenant_id, reading_payload)
    except Exception as e:
        logger.warning("Failed to emit reading WS event: %s", e)

    # Enqueue worker for ML inference + alert evaluation
    await _enqueue_worker(
        {
            "reading_id": str(reading.time) + "|" + str(reading.node_id),
            "tenant_id": str(reading.tenant_id),
            "node_id": str(reading.node_id),
            "site_id": str(reading.site_id),
            "time": reading.time.isoformat(),
            "severity": reading.severity,
            "rain_tips_15m": reading.rain_tips_15m,
            "accel_rms_mg": reading.accel_rms_mg,
            "tilt_delta_ddeg": reading.tilt_delta_ddeg,
            "crack_delta_mm10": reading.crack_delta_mm10,
        }
    )

    return {
        "ok": True,
        "reading_id": f"{reading.time.isoformat()}|{reading.node_id}",
        "severity": reading.severity,
        "ml_prob": None,
        "alert_id": None,
    }


# --- arq worker pool ---

_arq_pool: ArqRedis | None = None


async def _enqueue_worker(payload: dict[str, Any]) -> None:
    """Enqueue a process_reading task to the arq worker pool."""
    global _arq_pool
    settings = get_settings()
    if _arq_pool is None:
        try:
            _arq_pool = await create_pool(
                RedisSettings.from_dsn(settings.redis_url)
            )
        except Exception as e:
            logger.warning("arq enqueue failed (no redis?): %s", e)
            return
    try:
        await _arq_pool.enqueue_job("process_reading", payload)
    except Exception as e:
        logger.warning("arq enqueue error: %s", e)


async def close_arq() -> None:
    global _arq_pool
    if _arq_pool is not None:
        await _arq_pool.aclose()
        _arq_pool = None
