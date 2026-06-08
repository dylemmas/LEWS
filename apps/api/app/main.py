"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

import socketio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.routers import alerts, auth, ingest, ml, nodes, readings, sites
from app.routers import ws as ws_router
from app.services import ml_service, ws_manager

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    logging.basicConfig(
        level=s.log_level,
        format="%(asctime)s %(levelname)-5s %(name)s :: %(message)s",
    )
    logger.info("LEWS API booting (env=%s)", s.app_env)
    # Load ML model
    try:
        ml_service.load_sync()
    except Exception as e:
        logger.exception("Failed to load ML model: %s", e)
    # Init socketio
    ws_manager.init()
    ws_router.register_socketio_handlers()
    yield
    # Shutdown: close arq pool, etc.
    try:
        from app.services.ingest_service import close_arq
        await close_arq()
    except Exception:
        pass
    logger.info("LEWS API shutdown complete")


def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(
        title="LEWS API",
        version="0.1.0",
        lifespan=lifespan,
        default_response_class=JSONResponse,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=s.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(auth.router)
    app.include_router(sites.router)
    app.include_router(nodes.router)
    app.include_router(readings.router)
    app.include_router(alerts.router)
    app.include_router(ml.router)
    app.include_router(ingest.router)

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {
            "ok": True,
            "env": s.app_env,
            "ml_loaded": ml_service.is_loaded,
        }

    @app.get("/")
    async def root() -> dict[str, Any]:
        return {"name": "lews-api", "version": "0.1.0", "docs": "/docs"}

    return app


# Create the FastAPI app (consumed by uvicorn)
app = create_app()


# Mount Socket.IO under /v1/ws (we build an ASGI sub-app)
def build_socketio_asgi():
    sio = ws_manager.server
    return socketio.ASGIApp(sio, socketio_path="stream")


sio_app = build_socketio_asgi()


# Composite ASGI app: dispatch /v1/ws/* to sio, rest to FastAPI
class MountedApp:
    def __init__(self, fastapi_app, sio_asgi):
        self.fastapi_app = fastapi_app
        self.sio_asgi = sio_asgi

    async def __call__(self, scope, receive, send):
        if scope["type"] in ("http", "websocket"):
            path = scope.get("path", "")
            if path.startswith("/v1/ws"):
                # Strip prefix so sio sees /stream
                scope = dict(scope)
                scope["path"] = path[len("/v1/ws"):] or "/"
                scope["raw_path"] = scope["path"].encode()
                await self.sio_asgi(scope, receive, send)
                return
        await self.fastapi_app(scope, receive, send)


application = MountedApp(app, sio_app)
