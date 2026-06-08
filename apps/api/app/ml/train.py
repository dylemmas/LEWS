"""Train the landslide risk classifier on a synthetic dataset.

Run from the apps/api dir:
    python -m app.ml.train

Persists to ML_MODEL_PATH (default app/ml/model_v1.joblib).
"""

from __future__ import annotations

import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split

from app.config import get_settings
from app.ml.features import build_features

# ---- synthetic label rule (mirrors what the seeded stream looks like) ----
# Positive class: heavy rain + sustained tilt OR crack widening OR strong vibration,
# in the Bandung afternoon "landslide window" (14:00-18:00 local).

RAIN_CRIT = 40
TILT_CRIT = 200        # 2.00° change in 15 min
CRACK_CRIT = 100       # 10.0 mm change
ACCEL_CRIT = 150       # mg


def synth_label(rain: int, accel: int, tilt: int, crack: int, hour_utc: int) -> int:
    local_hour = (hour_utc + 7) % 24  # Bandung is UTC+7
    if rain >= RAIN_CRIT and (
        tilt >= TILT_CRIT or crack >= CRACK_CRIT or accel >= ACCEL_CRIT
    ) and 14 <= local_hour <= 18:
        return 1
    return 0


def make_dataset(n_samples: int = 200_000, seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)

    rain = rng.poisson(5, n_samples).astype(np.int32)
    rain += rng.integers(0, 5, n_samples)
    # inject heavy-rain streaks
    heavy = rng.random(n_samples) < 0.10
    rain[heavy] += rng.integers(30, 80, heavy.sum())

    # accel: roughly N(20, 12) with occasional spikes
    accel = np.clip(rng.normal(20, 12, n_samples), 0, 1000).astype(np.int32)
    spike = rng.random(n_samples) < 0.02
    accel[spike] += rng.integers(100, 300, spike.sum())

    # tilt: random-walk-ish, mostly small, occasional jumps
    tilt = np.clip(rng.normal(0, 40, n_samples), -500, 500).astype(np.int32)
    big = rng.random(n_samples) < 0.04
    tilt[big] += rng.integers(150, 400, big.sum())

    # crack: small drift, occasional jumps
    crack = np.clip(rng.normal(0, 12, n_samples), -200, 200).astype(np.int32)
    jump = rng.random(n_samples) < 0.03
    crack[jump] += rng.integers(50, 200, jump.sum())

    # hour uniform
    hours = rng.integers(0, 24, n_samples)

    feats = np.empty((n_samples, 6), dtype=np.float32)
    labels = np.empty(n_samples, dtype=np.int32)

    for i in range(n_samples):
        t = datetime(2026, 6, 6, int(hours[i]), 0, 0, tzinfo=timezone.utc)
        f = build_features(
            {
                "rain_tips_15m": int(rain[i]),
                "accel_rms_mg": int(accel[i]),
                "tilt_delta_ddeg": int(tilt[i]),
                "crack_delta_mm10": int(crack[i]),
            },
            t,
        )
        feats[i] = f
        labels[i] = synth_label(int(rain[i]), int(accel[i]), int(tilt[i]), int(crack[i]), int(hours[i]))

    return feats, labels


def main() -> int:
    settings = get_settings()
    print(f"Generating synthetic dataset (n=200,000)…")
    X, y = make_dataset(200_000)
    pos_rate = y.mean()
    print(f"  positive rate: {pos_rate:.3%}  ({y.sum()} positives)")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("Training RandomForestClassifier(n_estimators=200, max_depth=12)…")
    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        class_weight="balanced",
        n_jobs=-1,
        random_state=42,
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    y_proba = clf.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_proba)
    print(f"\nTest AUC: {auc:.4f}\n")
    print(classification_report(y_test, y_pred, digits=3))

    out_path = Path(settings.ml_model_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": clf,
            "feature_names": [
                "rain_tips_15m",
                "accel_rms_mg",
                "tilt_delta_ddeg",
                "crack_delta_mm10",
                "sin_hour",
                "cos_hour",
            ],
            "thresholds": {
                "watch": settings.ml_threshold_watch,
                "warning": settings.ml_threshold_warning,
                "critical": settings.ml_threshold_critical,
            },
            "trained_at": datetime.now(timezone.utc).isoformat(),
        },
        out_path,
    )
    print(f"Saved model → {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
