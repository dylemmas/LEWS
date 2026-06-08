"""Simulator entrypoint — async loop that posts HMAC-signed 20B payloads."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging
import time
from datetime import datetime, timezone

import httpx

from config import get_settings
from payload import encode as encode_payload
from profiles import BANDUNG_PROFILES, NodeProfile

logger = logging.getLogger(__name__)


def _hmac_header(secret: str, body: bytes, t: int) -> str:
    payload = f"{t}.".encode() + body
    digest = hmac.new(secret.encode(), payload, "sha256").hexdigest()
    return f"t={t},v1={digest}"


async def _post_ingest(
    client: httpx.AsyncClient,
    url: str,
    secret: str,
    dev_eui: str,
    payload_b64: str,
) -> None:
    body_dict = {
        "dev_eui": dev_eui,
        "payload_raw_b64": payload_b64,
        "time": datetime.now(timezone.utc).isoformat(),
    }
    # FastAPI expects JSON; httpx will serialize, but we also need the raw
    # bytes for HMAC. Easiest: pre-encode the JSON ourselves.
    import json
    body_bytes = json.dumps(body_dict, separators=(",", ":")).encode()
    sig = _hmac_header(secret, body_bytes, int(time.time()))
    try:
        r = await client.post(
            url,
            content=body_bytes,
            headers={"Content-Type": "application/json", "X-Signature": sig},
        )
        if r.status_code >= 400:
            logger.warning("Ingest %s -> %d: %s", dev_eui, r.status_code, r.text[:200])
        else:
            logger.debug("Ingest %s -> %d OK", dev_eui, r.status_code)
    except Exception as e:
        logger.warning("Ingest %s failed: %s", dev_eui, e)


async def run() -> None:
    s = get_settings()
    logging.basicConfig(level=s.log_level, format="%(asctime)s %(levelname)-5s %(name)s :: %(message)s")
    logger.info("Simulator booting (api=%s, speedup=%dx, interval=%ds)", s.api_url, s.speedup, s.interval_sec)

    profiles: list[NodeProfile] = BANDUNG_PROFILES[: s.seed_nodes]
    sim_minute = 0

    async with httpx.AsyncClient(timeout=15) as client:
        while True:
            for p in profiles:
                reading = p.tick(sim_minute)
                b64 = encode_payload(
                    severity=reading["severity"],
                    sensor_mask=reading["sensor_mask"],
                    rain_tips_15m=reading["rain_tips_15m"],
                    accel_rms_mg=reading["accel_rms_mg"],
                    tilt_delta_ddeg=reading["tilt_delta_ddeg"],
                    crack_delta_mm10=reading["crack_delta_mm10"],
                    lat_e7=int(p.lat * 1e7),
                    lon_e7=int(p.lon * 1e7),
                    battery_mv=reading["battery_mv"],
                )
                await _post_ingest(client, s.api_url, s.hmac_secret, p.dev_eui, b64)
            sim_minute += 15
            await asyncio.sleep(s.interval_sec)


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("Simulator stopped")
