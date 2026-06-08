"""/v1/ws/stream — Socket.IO mount."""

from __future__ import annotations

import logging
from typing import Any

import socketio

from app.deps import get_current_user
from app.security import decode_access_token
from app.services.ws_manager import ws_manager

logger = logging.getLogger(__name__)


def register_socketio_handlers() -> None:
    sio = ws_manager.server

    @sio.event
    async def connect(sid: str, environ: dict, auth: dict | None = None) -> bool:
        """Authenticate the handshake using an access token in `auth.token`."""
        token: str | None = None
        if isinstance(auth, dict):
            token = auth.get("token")
        if not token:
            # Try query string (e.g. ?token=xxx) as a fallback
            query = environ.get("QUERY_STRING", "")
            for part in query.split("&"):
                if part.startswith("token="):
                    token = part.split("=", 1)[1]
                    break
        if not token:
            logger.warning("WS connect rejected: no token (sid=%s)", sid)
            return False

        payload = decode_access_token(token)
        if not payload or payload.get("type") != "access":
            logger.warning("WS connect rejected: bad token (sid=%s)", sid)
            return False
        tid = payload.get("tid")
        uid = payload.get("sub")
        await sio.save_session(sid, {"tenant_id": tid, "user_id": uid, "role": payload.get("role")})
        await sio.enter_room(sid, f"t:{tid}")
        await sio.enter_room(sid, f"u:{uid}")
        await sio.emit("connected", {"sid": sid}, to=sid)
        logger.info("WS connected sid=%s tenant=%s user=%s", sid, tid, uid)
        return True

    @sio.event
    async def disconnect(sid: str) -> None:
        logger.info("WS disconnected sid=%s", sid)

    @sio.event
    async def subscribe_node(sid: str, data: dict) -> None:
        sess = await sio.get_session(sid)
        if not sess:
            return
        node_id = (data or {}).get("node_id")
        if node_id:
            await sio.enter_room(sid, f"n:{node_id}")

    @sio.event
    async def unsubscribe_node(sid: str, data: dict) -> None:
        sess = await sio.get_session(sid)
        if not sess:
            return
        node_id = (data or {}).get("node_id")
        if node_id:
            await sio.leave_room(sid, f"n:{node_id}")
