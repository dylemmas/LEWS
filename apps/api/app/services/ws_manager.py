"""Socket.IO manager — single-instance bridge between Python services and clients."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

import socketio
from socketio import AsyncRedisManager

from app.config import get_settings

logger = logging.getLogger(__name__)
_settings = get_settings()


class WSManager:
    """Wrapper around python-socketio ASGI server + Redis adapter.

    Usage:
        sio, manager = build_socketio_app()
        # in main: sio_asgi_app = socketio.ASGIApp(sio)
        # in routers: await ws_manager.emit_alert(tenant_id, alert)
    """

    def __init__(self) -> None:
        self.sio: socketio.AsyncServer | None = None
        self._redis_mgr: AsyncRedisManager | None = None
        self._settings = get_settings()

    def init(self, redis_url: str | None = None) -> socketio.AsyncServer:
        if self.sio is not None:
            return self.sio
        # Redis adapter for horizontal scale (works in single-pod dev too)
        url = redis_url or self._settings.redis_url
        try:
            self._redis_mgr = AsyncRedisManager(url)
            self.sio = socketio.AsyncServer(
                async_mode="asgi",
                cors_allowed_origins="*",
                client_manager=self._redis_mgr,
                logger=False,
                engineio_logger=False,
            )
        except Exception as e:
            logger.warning("Failed to init redis manager (%s); falling back to in-memory", e)
            self.sio = socketio.AsyncServer(
                async_mode="asgi",
                cors_allowed_origins="*",
                logger=False,
                engineio_logger=False,
            )
        return self.sio

    @property
    def server(self) -> socketio.AsyncServer:
        if self.sio is None:
            raise RuntimeError("WSManager not initialised. Call .init() first.")
        return self.sio

    async def emit_reading(self, tenant_id: UUID, payload: dict[str, Any]) -> None:
        await self.server.emit("reading", payload, room=f"t:{tenant_id}", namespace="/ws")
        node_id = payload.get("node_id")
        if node_id:
            await self.server.emit("reading", payload, room=f"n:{node_id}", namespace="/ws")

    async def emit_alert(self, tenant_id: UUID, alert: Any) -> None:
        payload = _alert_to_dict(alert)
        await self.server.emit("alert", payload, room=f"t:{tenant_id}", namespace="/ws")
        if getattr(alert, "node_id", None):
            await self.server.emit("alert", payload, room=f"n:{alert.node_id}", namespace="/ws")

    async def emit_node_status(self, tenant_id: UUID, node_id: UUID, payload: dict[str, Any]) -> None:
        await self.server.emit("node_status", payload, room=f"t:{tenant_id}", namespace="/ws")
        await self.server.emit("node_status", payload, room=f"n:{node_id}", namespace="/ws")


def _alert_to_dict(a: Any) -> dict[str, Any]:
    return {
        "type": "alert",
        "tenant_id": str(a.tenant_id),
        "alert_id": str(a.id),
        "node_id": str(a.node_id),
        "site_id": str(a.site_id),
        "severity": int(a.severity),
        "state": a.state,
        "title": a.title,
        "message": a.message,
        "first_seen_at": a.first_seen_at.isoformat() if a.first_seen_at else None,
        "last_seen_at": a.last_seen_at.isoformat() if a.last_seen_at else None,
        "acknowledged_at": a.acknowledged_at.isoformat() if a.acknowledged_at else None,
        "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
        "ml_prob": float(a.ml_prob) if a.ml_prob is not None else None,
    }


ws_manager = WSManager()
ws_manager.init()
