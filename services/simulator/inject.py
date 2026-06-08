"""Standalone /inject handler — same scenarios as backend, callable via CLI."""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from datetime import datetime, timezone

import httpx

from config import get_settings
from payload import encode as encode_payload
from profiles import BANDUNG_PROFILES


SCENARIOS = {
    "rain_burst": [
        {"severity": 1, "sensor_mask": 0x3F, "rain_tips_15m": 25, "accel_rms_mg": 30,
         "tilt_delta_ddeg": 20, "crack_delta_mm10": 5, "battery_mv": 3700},
        {"severity": 2, "sensor_mask": 0x3F, "rain_tips_15m": 55, "accel_rms_mg": 60,
         "tilt_delta_ddeg": 80, "crack_delta_mm10": 30, "battery_mv": 3700},
        {"severity": 2, "sensor_mask": 0x3F, "rain_tips_15m": 65, "accel_rms_mg": 70,
         "tilt_delta_ddeg": 120, "crack_delta_mm10": 50, "battery_mv": 3700},
        {"severity": 3, "sensor_mask": 0x3F, "rain_tips_15m": 90, "accel_rms_mg": 180,
         "tilt_delta_ddeg": 250, "crack_delta_mm10": 100, "battery_mv": 3700},
        {"severity": 3, "sensor_mask": 0x3F, "rain_tips_15m": 110, "accel_rms_mg": 220,
         "tilt_delta_ddeg": 400, "crack_delta_mm10": 180, "battery_mv": 3700},
        {"severity": 3, "sensor_mask": 0x3F, "rain_tips_15m": 130, "accel_rms_mg": 260,
         "tilt_delta_ddeg": 520, "crack_delta_mm10": 220, "battery_mv": 3700},
    ],
    "tilt_spike": [
        {"severity": 1, "sensor_mask": 0x3F, "rain_tips_15m": 5, "accel_rms_mg": 40,
         "tilt_delta_ddeg": 200, "crack_delta_mm10": 10, "battery_mv": 3700},
        {"severity": 2, "sensor_mask": 0x3F, "rain_tips_15m": 8, "accel_rms_mg": 80,
         "tilt_delta_ddeg": 400, "crack_delta_mm10": 20, "battery_mv": 3700},
        {"severity": 3, "sensor_mask": 0x3F, "rain_tips_15m": 10, "accel_rms_mg": 130,
         "tilt_delta_ddeg": 550, "crack_delta_mm10": 40, "battery_mv": 3700},
        {"severity": 3, "sensor_mask": 0x3F, "rain_tips_15m": 12, "accel_rms_mg": 180,
         "tilt_delta_ddeg": 600, "crack_delta_mm10": 70, "battery_mv": 3700},
        {"severity": 3, "sensor_mask": 0x3F, "rain_tips_15m": 14, "accel_rms_mg": 200,
         "tilt_delta_ddeg": 620, "crack_delta_mm10": 90, "battery_mv": 3700},
        {"severity": 2, "sensor_mask": 0x3F, "rain_tips_15m": 10, "accel_rms_mg": 120,
         "tilt_delta_ddeg": 400, "crack_delta_mm10": 60, "battery_mv": 3700},
    ],
    "crack_jump": [
        {"severity": 1, "sensor_mask": 0x3F, "rain_tips_15m": 10, "accel_rms_mg": 30,
         "tilt_delta_ddeg": 30, "crack_delta_mm10": 60, "battery_mv": 3700},
        {"severity": 2, "sensor_mask": 0x3F, "rain_tips_15m": 12, "accel_rms_mg": 50,
         "tilt_delta_ddeg": 60, "crack_delta_mm10": 150, "battery_mv": 3700},
        {"severity": 2, "sensor_mask": 0x3F, "rain_tips_15m": 14, "accel_rms_mg": 70,
         "tilt_delta_ddeg": 100, "crack_delta_mm10": 200, "battery_mv": 3700},
        {"severity": 3, "sensor_mask": 0x3F, "rain_tips_15m": 16, "accel_rms_mg": 90,
         "tilt_delta_ddeg": 150, "crack_delta_mm10": 250, "battery_mv": 3700},
        {"severity": 3, "sensor_mask": 0x3F, "rain_tips_15m": 18, "accel_rms_mg": 100,
         "tilt_delta_ddeg": 180, "crack_delta_mm10": 280, "battery_mv": 3700},
        {"severity": 2, "sensor_mask": 0x3F, "rain_tips_15m": 14, "accel_rms_mg": 60,
         "tilt_delta_ddeg": 120, "crack_delta_mm10": 200, "battery_mv": 3700},
    ],
    "critical": [
        {"severity": 2, "sensor_mask": 0x3F, "rain_tips_15m": 60, "accel_rms_mg": 180,
         "tilt_delta_ddeg": 300, "crack_delta_mm10": 80, "battery_mv": 3700},
        {"severity": 3, "sensor_mask": 0x3F, "rain_tips_15m": 90, "accel_rms_mg": 250,
         "tilt_delta_ddeg": 500, "crack_delta_mm10": 200, "battery_mv": 3700},
        {"severity": 3, "sensor_mask": 0x3F, "rain_tips_15m": 110, "accel_rms_mg": 280,
         "tilt_delta_ddeg": 600, "crack_delta_mm10": 280, "battery_mv": 3700},
        {"severity": 3, "sensor_mask": 0x3F, "rain_tips_15m": 130, "accel_rms_mg": 320,
         "tilt_delta_ddeg": 700, "crack_delta_mm10": 320, "battery_mv": 3700},
        {"severity": 3, "sensor_mask": 0x3F, "rain_tips_15m": 150, "accel_rms_mg": 350,
         "tilt_delta_ddeg": 750, "crack_delta_mm10": 350, "battery_mv": 3700},
        {"severity": 3, "sensor_mask": 0x3F, "rain_tips_15m": 160, "accel_rms_mg": 380,
         "tilt_delta_ddeg": 800, "crack_delta_mm10": 380, "battery_mv": 3700},
    ],
}


def _hmac(secret: str, body: bytes, t: int) -> str:
    import hmac
    import hashlib
    payload = f"{t}.".encode() + body
    digest = hmac.new(secret.encode(), payload, "sha256").hexdigest()
    return f"t={t},v1={digest}"


async def inject(scenario: str, node_index: int = 0, interval_sec: float = 1.0) -> None:
    s = get_settings()
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown scenario: {scenario}")
    profile = BANDUNG_PROFILES[node_index % len(BANDUNG_PROFILES)]
    samples = SCENARIOS[scenario]
    async with httpx.AsyncClient(timeout=15) as client:
        for sample in samples:
            payload = {
                **sample,
                "lat_e7": int(profile.lat * 1e7),
                "lon_e7": int(profile.lon * 1e7),
            }
            b64 = encode_payload(**payload)
            body_dict = {
                "dev_eui": profile.dev_eui,
                "payload_raw_b64": b64,
                "time": datetime.now(timezone.utc).isoformat(),
            }
            body_bytes = json.dumps(body_dict, separators=(",", ":")).encode()
            sig = _hmac(s.hmac_secret, body_bytes, int(time.time()))
            r = await client.post(
                s.api_url,
                content=body_bytes,
                headers={"Content-Type": "application/json", "X-Signature": sig},
            )
            print(f"{scenario} -> {profile.name} ({profile.dev_eui}): {r.status_code}")
            await asyncio.sleep(interval_sec)


if __name__ == "__main__":
    import sys
    sc = sys.argv[1] if len(sys.argv) > 1 else "critical"
    idx = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    asyncio.run(inject(sc, idx))
