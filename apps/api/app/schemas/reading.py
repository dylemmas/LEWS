"""Reading schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ReadingDTO(BaseModel):
    time: datetime
    tenant_id: UUID
    node_id: UUID
    site_id: UUID
    severity: int
    sensor_mask: int
    rain_tips_15m: int
    accel_rms_mg: int
    tilt_delta_ddeg: int
    crack_delta_mm10: int
    battery_mv: int
    ml_prob: float | None
    lat: float
    lon: float

    model_config = {"from_attributes": True}


class ReadingSeries(BaseModel):
    """Time-bucketed series for chart rendering."""
    bucket: datetime
    avg_severity: float
    sum_rain: float
    avg_accel: float
    avg_tilt: float
    avg_crack: float
    avg_battery: float | None
    count: int
