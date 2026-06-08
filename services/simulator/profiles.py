"""5 per-node sensor profiles for the Bandung region.

Each profile defines a baseline coordinate, sensor noise, and an event
'personality' that occasionally spikes during a session to make the
dashboard feel alive.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Callable


@dataclass(slots=True)
class NodeProfile:
    name: str
    dev_eui: str
    lat: float
    lon: float
    # Sensor noise generators
    rain_baseline: float = 5.0
    rain_storm_chance: float = 0.05
    accel_baseline: float = 20.0
    tilt_baseline: float = 0.0
    crack_baseline: float = 0.0
    battery_mv: int = 3700

    # Internal state
    _tilt: float = 0.0
    _crack: float = 0.0
    _storm_active: bool = False
    _storm_remaining: int = 0

    def reset(self) -> None:
        self._tilt = self.tilt_baseline
        self._crack = self.crack_baseline
        self._storm_active = False
        self._storm_remaining = 0

    def tick(self, sim_minute: int) -> dict:
        """Advance one simulator step and return a reading dict."""
        # Rain: Poisson-ish, with storm bursts
        if not self._storm_active and random.random() < self.rain_storm_chance:
            self._storm_active = True
            self._storm_remaining = random.randint(8, 30)  # 2-7.5 sim-hours
        if self._storm_active:
            self._storm_remaining -= 1
            if self._storm_remaining <= 0:
                self._storm_active = False

        rain_lambda = self.rain_baseline * (4.0 if self._storm_active else 1.0)
        rain_tips = int(_poisson(rain_lambda))

        accel_rms = max(0, int(random.gauss(self.accel_baseline, 12)))
        if random.random() < 0.02:
            accel_rms += random.randint(100, 250)

        # Tilt: small random walk + occasional jumps (storm-tied)
        self._tilt += random.gauss(0, 5)
        if self._storm_active and random.random() < 0.10:
            self._tilt += random.choice([-1, 1]) * random.randint(80, 200)
        tilt = int(max(-500, min(500, self._tilt)))

        # Crack: slow drift, occasional jumps
        self._crack += random.gauss(0, 1.5)
        if self._storm_active and random.random() < 0.07:
            self._crack += random.choice([-1, 1]) * random.randint(20, 80)
        crack = int(max(-200, min(200, self._crack)))

        # Battery: slow decay during storms, slow recharge otherwise
        if self._storm_active:
            self.battery_mv = max(3300, self.battery_mv - random.randint(0, 1))
        else:
            self.battery_mv = min(4200, self.battery_mv + (1 if random.random() < 0.3 else 0))

        # Severity: rule of thumb (the backend will re-evaluate; this is for the wire)
        sev = 0
        if rain_tips >= 50 or tilt >= 500 or crack >= 200 or accel_rms >= 250:
            sev = 3
        elif rain_tips >= 25 or tilt >= 250 or crack >= 60 or accel_rms >= 100:
            sev = 2
        elif rain_tips >= 10 or tilt >= 100 or crack >= 20 or accel_rms >= 50:
            sev = 1

        return {
            "severity": sev,
            "sensor_mask": 0x3F,
            "rain_tips_15m": rain_tips,
            "accel_rms_mg": accel_rms,
            "tilt_delta_ddeg": tilt,
            "crack_delta_mm10": crack,
            "battery_mv": self.battery_mv,
        }


def _poisson(lam: float) -> int:
    """Knuth's algorithm."""
    import math
    L = math.exp(-lam)
    k = 0
    p = 1.0
    while p > L:
        k += 1
        p *= random.random()
    return k - 1


# Bandung-area coordinates + dev_euis
BANDUNG_PROFILES: list[NodeProfile] = [
    NodeProfile(
        name="Cimenyan-01",
        dev_eui="LEWS000000000001",
        lat=-7.0408,
        lon=107.6895,
        rain_baseline=4.0,
        rain_storm_chance=0.06,
        tilt_baseline=0,
    ),
    NodeProfile(
        name="Lembang-02",
        dev_eui="LEWS000000000002",
        lat=-6.8180,
        lon=107.6170,
        rain_baseline=5.0,
        rain_storm_chance=0.05,
    ),
    NodeProfile(
        name="Pangalengan-03",
        dev_eui="LEWS000000000003",
        lat=-7.1640,
        lon=107.5910,
        rain_baseline=6.0,
        rain_storm_chance=0.07,
    ),
    NodeProfile(
        name="Ciwidey-04",
        dev_eui="LEWS000000000004",
        lat=-7.1370,
        lon=107.4530,
        rain_baseline=5.0,
        rain_storm_chance=0.05,
    ),
    NodeProfile(
        name="Maribaya-05",
        dev_eui="LEWS000000000005",
        lat=-6.8260,
        lon=107.6390,
        rain_baseline=4.0,
        rain_storm_chance=0.04,
    ),
]
