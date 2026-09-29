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


def simulate_school(n: int = 12, steps: int = 300, dt: float = 1 / 30, speed: float = 0.3,
                    align: float = 0.9, heading_noise: float = 0.35, seed: int = 0) -> dict:
    """Vicsek-style school: each fish turns toward the mean heading with weight
    `align` and adds Gaussian heading noise (rad per sqrt(s)). Returns true
    positions (steps x n x 2) and velocities. Synthetic truth for tracker tests.
    """
    rng = np.random.default_rng(seed)
    th = rng.uniform(-np.pi, np.pi, n) * (1 - align) + rng.normal(0, 0.2, n)
    pos = np.zeros((steps, n, 2))
    vel = np.zeros((steps, n, 2))
    pos[0] = rng.uniform(0, 1.0, (n, 2))
    for t in range(steps):
        mean = np.arctan2(np.sin(th).mean(), np.cos(th).mean())
        d = np.angle(np.exp(1j * (mean - th)))
        th = th + align * d * dt * 5 + rng.normal(0, heading_noise * math.sqrt(dt), n)
        vel[t] = speed * np.column_stack([np.cos(th), np.sin(th)])
        if t + 1 < steps:
            pos[t + 1] = pos[t] + vel[t] * dt
    return {"pos": pos, "vel": vel, "dt": dt}


def kalman_cv(obs: np.ndarray, dt: float, sigma_x: float, q: float) -> np.ndarray:
    """Constant-velocity Kalman filter per track, 2-D. obs: steps x n x 2 noisy
    positions with known identity (association solved). q: white-acceleration
    spectral density (m2 s-3). Returns filtered velocities (steps x n x 2).
    """
    steps, n, _ = obs.shape
    F = np.array([[1, dt], [0, 1]])
    Q = q * np.array([[dt ** 3 / 3, dt ** 2 / 2], [dt ** 2 / 2, dt]])
    H = np.array([[1.0, 0.0]])
    R = sigma_x ** 2
    out = np.zeros_like(obs)
    for k in range(n):
        for ax in range(2):
            x = np.array([obs[0, k, ax], 0.0])
            P = np.diag([R, 1.0])
            for t in range(steps):
                if t:
                    x = F @ x
                    P = F @ P @ F.T + Q
                S = (H @ P @ H.T)[0, 0] + R
                K = (P @ H.T)[:, 0] / S
                x = x + K * (obs[t, k, ax] - x[0])
                P = P - np.outer(K, H @ P)
                out[t, k, ax] = x[1]
    return out


def polarisation_series(vel: np.ndarray) -> np.ndarray:
    return np.array([polarisation(v[:, 0], v[:, 1]) for v in vel])
