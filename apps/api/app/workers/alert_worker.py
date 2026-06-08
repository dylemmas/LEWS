"""arq task: process a single reading → ML → alert evaluation → notify."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select, update

from app.db.session import session_scope
from app.models import SensorReading
from app.services import dispatch_alert, evaluate, ml_service, ws_manager

logger = logging.getLogger(__name__)


async def process_reading(ctx: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """Run ML inference, then evaluate against thresholds, then notify.

    Payload (from ingest_service):
        reading_id, tenant_id, node_id, site_id, time,
        severity, rain_tips_15m, accel_rms_mg, tilt_delta_ddeg, crack_delta_mm10
    """
    log_extra = {"node_id": payload.get("node_id")}
    try:
        # 1) ML inference
        prob = await ml_service.predict(payload)
        ml_sev = ml_service.severity_from_prob(prob)

        # 2) Persist ml_prob back to the reading row
        time = datetime.fromisoformat(payload["time"])
        node_id = UUID(payload["node_id"])
        async with session_scope() as db:
            await db.execute(
                update(SensorReading)
                .where(SensorReading.node_id == node_id, SensorReading.time == time)
                .values(ml_prob=prob)
            )
            # Re-fetch for any downstream FK access
            res = await db.execute(
                select(SensorReading).where(
                    SensorReading.node_id == node_id, SensorReading.time == time
                )
            )
            reading = res.scalar_one_or_none()
            if reading is None:
                logger.warning("Reading disappeared: %s|%s", time, node_id, extra=log_extra)
                return {"ok": False, "reason": "reading_not_found"}

            # 3) Two-stage evaluation
            reading_dict = {
                **payload,
                "time": time,
                "tenant_id": UUID(payload["tenant_id"]),
                "node_id": node_id,
                "site_id": UUID(payload["site_id"]),
            }
            alert = await evaluate(db, reading_dict, prob)

            # 4) Fanout
            if alert is not None and alert.id is None:
                await db.flush()
            if alert is not None:
                # Push WS update for the reading with ml_prob
                try:
                    await ws_manager.emit_reading(
                        alert.tenant_id,
                        {
                            "type": "reading",
                            "tenant_id": str(alert.tenant_id),
                            "node_id": str(alert.node_id),
                            "site_id": str(alert.site_id),
                            "time": time.isoformat(),
                            "severity": max(int(payload.get("severity", 0)), ml_sev),
                            "ml_prob": prob,
                        },
                    )
                except Exception as e:
                    logger.warning("WS emit failed: %s", e)

            # 5) Dispatch notifications for new alerts
            if alert is not None and (alert.notification_log is None or len(alert.notification_log) == 0):
                # Newly created → needs notification
                await dispatch_alert(db, alert)
            elif alert is not None and alert.id is not None and len(alert.notification_log) > 0:
                # Coalesced update — re-emit alert so banner refreshes
                try:
                    await ws_manager.emit_alert(alert.tenant_id, alert)
                except Exception as e:
                    logger.warning("WS re-emit failed: %s", e)

        return {
            "ok": True,
            "ml_prob": prob,
            "ml_sev": ml_sev,
            "alert_id": str(alert.id) if alert and alert.id else None,
            "alert_severity": alert.severity if alert else None,
        }
    except Exception as e:
        logger.exception("process_reading failed: %s", e)
        return {"ok": False, "error": str(e)}
