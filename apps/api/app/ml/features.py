"""Feature engineering for the ML model.

Features: [rain_tips_15m, accel_rms_mg, tilt_delta_ddeg, crack_delta_mm10, sin(hour), cos(hour)]
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any


def build_features(reading: dict[str, Any], t: datetime | None = None) -> list[float]:
    """Build a 6-dim feature vector from a reading dict.

    The reading dict can come straight from the sensor_readings row or from
    a Pydantic schema; we only read the keys we need.
    """
    if t is None:
        t = reading.get("time") or datetime.now(timezone.utc)
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    hour_frac = (t.hour * 3600 + t.minute * 60 + t.second) / 86400.0  # 0..1
    return [
        float(reading.get("rain_tips_15m", 0)),
        float(reading.get("accel_rms_mg", 0)),
        float(reading.get("tilt_delta_ddeg", 0)),
        float(reading.get("crack_delta_mm10", 0)),
        math.sin(2 * math.pi * hour_frac),
        math.cos(2 * math.pi * hour_frac),
    ]


FEATURE_NAMES = [
    "rain_tips_15m",
    "accel_rms_mg",
    "tilt_delta_ddeg",
    "crack_delta_mm10",
    "sin_hour",
    "cos_hour",
]
