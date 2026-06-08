"""ML inference service — loads model at startup, predicts on demand."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from app.config import get_settings
from app.ml.features import build_features

logger = logging.getLogger(__name__)


class MLService:
    """Wraps a joblib-loaded RandomForestClassifier and exposes .predict()."""

    def __init__(self) -> None:
        self._model: Any = None
        self._meta: dict[str, Any] = {}
        self._lock = asyncio.Lock()

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def load_sync(self, path: Path | None = None) -> None:
        """Load the model from disk. Call once at app startup."""
        if path is None:
            path = get_settings().ml_model_path
        if not Path(path).exists():
            logger.warning("ML model not found at %s; predictions will return None", path)
            self._model = None
            return
        blob = joblib.load(path)
        self._model = blob["model"]
        self._meta = {k: v for k, v in blob.items() if k != "model"}
        logger.info(
            "ML model loaded: trained_at=%s, thresholds=%s",
            self._meta.get("trained_at"),
            self._meta.get("thresholds"),
        )

    async def predict(self, reading: dict[str, Any]) -> float | None:
        """Return probability of "landslide risk" in [0, 1] or None if no model."""
        if self._model is None:
            return None
        t = reading.get("time")
        if isinstance(t, str):
            try:
                t = datetime.fromisoformat(t.replace("Z", "+00:00"))
            except ValueError:
                t = None
        feats = build_features(reading, t)
        arr = np.array([feats], dtype=np.float32)
        # joblib is sync — run in a thread to keep the event loop unblocked
        loop = asyncio.get_running_loop()
        proba = await loop.run_in_executor(None, lambda: self._model.predict_proba(arr)[0, 1])
        return float(proba)

    def severity_from_prob(self, prob: float | None) -> int:
        """Map probability to severity 0..3 using configured thresholds."""
        s = get_settings()
        if prob is None:
            return 0
        if prob >= s.ml_threshold_critical:
            return 3
        if prob >= s.ml_threshold_warning:
            return 2
        if prob >= s.ml_threshold_watch:
            return 1
        return 0


ml_service = MLService()
