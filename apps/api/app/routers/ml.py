"""/v1/ml/predict — direct inference endpoint (used for testing)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.deps import CurrentUser, require_role
from app.services.ml_service import ml_service

router = APIRouter(prefix="/v1/ml", tags=["ml"])


class PredictRequest(BaseModel):
    rain_tips_15m: int = 0
    accel_rms_mg: int = 0
    tilt_delta_ddeg: int = 0
    crack_delta_mm10: int = 0
    time: datetime | None = None


class PredictResponse(BaseModel):
    prob: float | None
    severity: int
    thresholds: dict[str, float]


@router.post("/predict", response_model=PredictResponse)
async def predict(
    payload: PredictRequest,
    cu: CurrentUser = Depends(require_role("operator")),
) -> PredictResponse:
    reading: dict[str, Any] = payload.model_dump()
    if reading.get("time") is None:
        reading["time"] = datetime.now(timezone.utc)
    prob = await ml_service.predict(reading)
    sev = ml_service.severity_from_prob(prob)
    from app.config import get_settings
    s = get_settings()
    return PredictResponse(
        prob=prob,
        severity=sev,
        thresholds={
            "watch": s.ml_threshold_watch,
            "warning": s.ml_threshold_warning,
            "critical": s.ml_threshold_critical,
        },
    )
