"""Alert engine: two-stage (hardware + ML) evaluation, state machine, dedup."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Alert, Node, ThresholdRule
from app.services.dedup import make_dedup_key
from app.services.ml_service import ml_service

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RuleOutcome:
    severity: int
    breached: list[str]


def _eval_thresholds(reading: dict[str, Any], rule: ThresholdRule) -> RuleOutcome:
    """Stage 1: hardware threshold evaluation."""
    s = 0
    breaches: list[str] = []

    if reading["rain_tips_15m"] >= rule.rain_critical:
        s = max(s, 3)
        breaches.append("rain_critical")
    elif reading["rain_tips_15m"] >= rule.rain_warning:
        s = max(s, 2)
        breaches.append("rain_warning")
    elif reading["rain_tips_15m"] >= rule.rain_watch:
        s = max(s, 1)
        breaches.append("rain_watch")

    if reading["accel_rms_mg"] >= rule.accel_critical:
        s = max(s, 3)
        breaches.append("accel_critical")
    elif reading["accel_rms_mg"] >= rule.accel_warning:
        s = max(s, 2)
        breaches.append("accel_warning")
    elif reading["accel_rms_mg"] >= rule.accel_watch:
        s = max(s, 1)
        breaches.append("accel_watch")

    if reading["tilt_delta_ddeg"] >= rule.tilt_critical:
        s = max(s, 3)
        breaches.append("tilt_critical")
    elif reading["tilt_delta_ddeg"] >= rule.tilt_warning:
        s = max(s, 2)
        breaches.append("tilt_warning")
    elif reading["tilt_delta_ddeg"] >= rule.tilt_watch:
        s = max(s, 1)
        breaches.append("tilt_watch")

    if reading["crack_delta_mm10"] >= rule.crack_critical:
        s = max(s, 3)
        breaches.append("crack_critical")
    elif reading["crack_delta_mm10"] >= rule.crack_warning:
        s = max(s, 2)
        breaches.append("crack_warning")
    elif reading["crack_delta_mm10"] >= rule.crack_watch:
        s = max(s, 1)
        breaches.append("crack_watch")

    return RuleOutcome(severity=s, breached=breaches)


async def evaluate(
    db: AsyncSession,
    reading: dict[str, Any],
    ml_prob: float | None,
) -> Alert | None:
    """Run two-stage evaluation; return a new Alert row if one should be created.

    1. Get the tenant's threshold rules (or defaults).
    2. Stage 1: hardware thresholds → hw_sev.
    3. Stage 2: ML probability → ml_sev (never demotes).
    4. Final sev = max(hw_sev, ml_sev).
    5. If sev > 0:
       - build dedup_key
       - check if an open/ack'd alert exists with same key
       - if not, create a new Alert
    """
    node_id = UUID(reading["node_id"])
    site_id = UUID(reading["site_id"])
    tenant_id = UUID(reading["tenant_id"])
    t = reading.get("time") or datetime.now(timezone.utc)

    node = await db.get(Node, node_id)
    if node is None:
        logger.warning("Node %s not found during alert evaluation", node_id)
        return None

    # Fetch tenant rules (site-specific if exists, else tenant-wide)
    rule_res = await db.execute(
        select(ThresholdRule)
        .where(
            (ThresholdRule.tenant_id == tenant_id) &
            ((ThresholdRule.site_id == site_id) | (ThresholdRule.site_id.is_(None)))
        )
        .order_by(ThresholdRule.site_id.desc().nullslast())
        .limit(1)
    )
    rule = rule_res.scalar_one_or_none()
    if rule is None:
        # Fallback defaults (in-memory)
        class _Default:
            rain_watch = 10.0
            rain_warning = 25.0
            rain_critical = 50.0
            accel_watch = 50.0
            accel_warning = 100.0
            accel_critical = 200.0
            tilt_watch = 100.0
            tilt_warning = 250.0
            tilt_critical = 500.0
            crack_watch = 20.0
            crack_warning = 60.0
            crack_critical = 120.0
            dedup_window_sec = 300

        rule = _Default()  # type: ignore

    hw_outcome = _eval_thresholds(reading, rule)
    hw_sev = hw_outcome.severity

    ml_sev = ml_service.severity_from_prob(ml_prob)
    final_sev = max(hw_sev, ml_sev)

    if final_sev == 0:
        return None

    # Check for duplicate open/ack'd alert
    dedup_key = make_dedup_key(node_id, final_sev, t, rule.dedup_window_sec)
    existing_res = await db.execute(
        select(Alert).where(
            (Alert.node_id == node_id) &
            (Alert.dedup_key == dedup_key) &
            (Alert.state.in_(["open", "acknowledged"]))
        )
    )
    existing = existing_res.scalar_one_or_none()
    if existing:
        # coalesce: update last_seen_at only
        existing.last_seen_at = t
        existing.ml_prob = existing.ml_prob or ml_prob
        return existing

    # New alert
    title, message = _alert_text(final_sev, hw_outcome.breached, ml_prob)
    alert = Alert(
        tenant_id=tenant_id,
        node_id=node_id,
        site_id=site_id,
        severity=final_sev,
        state="open",
        dedup_key=dedup_key,
        title=title,
        message=message,
        trigger_payload={
            "reading_time": t.isoformat(),
            "hw_breaches": hw_outcome.breached,
            "hw_sev": hw_sev,
            "ml_prob": ml_prob,
        },
        first_seen_at=t,
        last_seen_at=t,
        ml_prob=ml_prob,
        notification_log=[],
    )
    db.add(alert)
    logger.info(
        "New alert: node=%s severity=%d dedup=%s hw=%s ml=%s",
        node_id,
        final_sev,
        dedup_key,
        hw_sev,
        ml_sev,
    )
    return alert


def _alert_text(severity: int, breaches: list[str], ml_prob: float | None) -> tuple[str, str]:
    labels = {1: "Watch", 2: "Warning", 3: "Critical"}
    label = labels.get(severity, "Unknown")
    if breaches:
        reason = ", ".join(set(breaches))
        msg = f"Hardware threshold(s) breached: {reason}"
    else:
        msg = "ML-based escalation (no hardware breach)"
    if ml_prob is not None:
        msg += f" — ML probability: {ml_prob:.2%}"
    return f"{label} Condition Detected", msg
