"""20-byte payload encoder (mirror of backend decoder)."""

from __future__ import annotations

import base64
import struct


PAYLOAD_SIZE = 20


def encode(
    *,
    severity: int,
    sensor_mask: int,
    rain_tips_15m: int,
    accel_rms_mg: int,
    tilt_delta_ddeg: int,
    crack_delta_mm10: int,
    lat_e7: int,
    lon_e7: int,
    battery_mv: int,
) -> str:
    buf = bytearray(PAYLOAD_SIZE)
    buf[0] = severity & 0xFF
    buf[1] = sensor_mask & 0xFF
    struct.pack_into("<H", buf, 2, rain_tips_15m & 0xFFFF)
    struct.pack_into("<H", buf, 4, accel_rms_mg & 0xFFFF)
    struct.pack_into("<h", buf, 6, max(-32768, min(32767, tilt_delta_ddeg)))
    struct.pack_into("<h", buf, 8, max(-32768, min(32767, crack_delta_mm10)))
    struct.pack_into("<i", buf, 10, int(lat_e7) & 0xFFFFFFFF)
    struct.pack_into("<i", buf, 14, int(lon_e7) & 0xFFFFFFFF)
    struct.pack_into("<H", buf, 18, battery_mv & 0xFFFF)
    return base64.b64encode(bytes(buf)).decode()
