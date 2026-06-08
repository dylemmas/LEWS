"""Notification dispatch — Twilio SMS, SendGrid email, Socket.IO fanout."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Alert, User
from app.services.ws_manager import ws_manager

logger = logging.getLogger(__name__)
_settings = get_settings()


async def _send_email(to: str, subject: str, body: str) -> tuple[bool, str | None]:
    """Send via SendGrid if API key set, else fall back to dev SMTP/MailHog."""
    if _settings.sendgrid_api_key:
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    headers={"Authorization": f"Bearer {_settings.sendgrid_api_key}"},
                    json={
                        "personalizations": [{"to": [{"email": to}]}],
                        "from": {"email": _settings.sendgrid_from},
                        "subject": subject,
                        "content": [{"type": "text/plain", "value": body}],
                    },
                )
            if r.status_code in (200, 201, 202):
                return True, None
            return False, f"sendgrid {r.status_code}: {r.text[:200]}"
        except Exception as e:
            return False, f"sendgrid exc: {e}"
    else:
        # Dev fallback: log only
        logger.info("[DEV-EMAIL] to=%s subject=%s body=%s", to, subject, body[:120])
        return True, None


async def _send_sms(to: str, body: str) -> tuple[bool, str | None]:
    """Send via Twilio if creds set, else log only."""
    if not (_settings.twilio_account_sid and _settings.twilio_auth_token and _settings.twilio_from):
        logger.info("[DEV-SMS] to=%s body=%s", to, body[:120])
        return True, None
    try:
        from twilio.rest import Client

        client = Client(_settings.twilio_account_sid, _settings.twilio_auth_token)
        # Twilio SDK is sync — run in thread
        def _do() -> str:
            msg = client.messages.create(body=body, from_=_settings.twilio_from, to=to)
            return msg.sid

        sid = await asyncio.get_running_loop().run_in_executor(None, _do)
        return True, None
    except Exception as e:
        return False, f"twilio exc: {e}"


async def dispatch_alert(db: AsyncSession, alert: Alert) -> None:
    """Send notifications according to severity dispatch matrix."""
    tenant_id = alert.tenant_id
    sev = alert.severity

    # Find the target operators/admins
    users_res = await db.execute(
        select(User).where(
            (User.tenant_id == tenant_id) & (User.is_active.is_(True))
        )
    )
    users = list(users_res.scalars().all())

    title = f"[{['Normal','Watch','Warning','Critical'][sev]}] LEWS Alert"
    subject = title
    body = f"{alert.message}\nNode: {alert.node_id}\nFirst seen: {alert.first_seen_at.isoformat()}"
    sms_body = f"LEWS {['Normal','Watch','Warning','Critical'][sev]}: {alert.title} (node {str(alert.node_id)[:8]})"

    log: list[dict[str, Any]] = []

    # WebSocket fanout — always
    try:
        await ws_manager.emit_alert(tenant_id, alert)
        log.append(
            {
                "channel": "ws",
                "target": f"t:{tenant_id}",
                "sent_at": datetime.now(timezone.utc).isoformat(),
                "ok": True,
            }
        )
    except Exception as e:
        log.append(
            {
                "channel": "ws",
                "target": f"t:{tenant_id}",
                "sent_at": datetime.now(timezone.utc).isoformat(),
                "ok": False,
                "error": str(e),
            }
        )

    # Email + SMS per severity
    if sev >= 1:
        for u in users:
            if u.role in ("admin", "operator") and u.email:
                ok, err = await _send_email(u.email, subject, body)
                log.append(
                    {
                        "channel": "email",
                        "target": u.email,
                        "sent_at": datetime.now(timezone.utc).isoformat(),
                        "ok": ok,
                        "error": err,
                    }
                )

    if sev >= 2:
        for u in users:
            if u.role in ("admin", "operator") and u.phone_e164:
                ok, err = await _send_sms(u.phone_e164, sms_body)
                log.append(
                    {
                        "channel": "sms",
                        "target": u.phone_e164,
                        "sent_at": datetime.now(timezone.utc).isoformat(),
                        "ok": ok,
                        "error": err,
                    }
                )

    if sev >= 3:
        # Critical: also SMS all admins
        for u in users:
            if u.role == "admin" and u.phone_e164:
                ok, err = await _send_sms(u.phone_e164, sms_body)
                log.append(
                    {
                        "channel": "sms",
                        "target": u.phone_e164,
                        "sent_at": datetime.now(timezone.utc).isoformat(),
                        "ok": ok,
                        "error": err,
                    }
                )

    alert.notification_log = (alert.notification_log or []) + log
    await db.commit()
