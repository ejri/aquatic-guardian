"""School-level metrics for multi-object fish tracking.

Polarisation P = |mean of unit heading vectors| (Vicsek et al. 1995; Couzin
et al. 2002). For N independent random headings in 2-D, E[P^2] = 1/N and
E[P] ~ sqrt(pi)/(2 sqrt(N)); always report this null baseline.

Frame-differenced velocity noise is sqrt(2) sigma_x / dt. A Kalman filter
helps when localisation noise sigma_x is comparable to or larger than the
per-frame displacement u dt (ratio r = sigma_x / (u dt)).
"""
from __future__ import annotations
import math
import numpy as np


def polarisation(vx, vy) -> float:
    v = np.column_stack([vx, vy]).astype(float)
    norm = np.linalg.norm(v, axis=1)
    v = v[norm > 0] / norm[norm > 0, None]
    return float(np.linalg.norm(v.mean(axis=0))) if len(v) else float("nan")


def null_polarisation(n: int) -> dict:
    return {"rms": 1.0 / math.sqrt(n), "mean": math.sqrt(math.pi) / (2.0 * math.sqrt(n))}


def fd_velocity_noise(sigma_x: float, dt: float) -> float:
    return math.sqrt(2.0) * sigma_x / dt


def kalman_benefit_ratio(sigma_x: float, speed: float, dt: float) -> float:
    return sigma_x / (speed * dt)
