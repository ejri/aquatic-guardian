"""Numerical diffusion diagnostics and a reference 1-D transport solver.

Correction 3 (docs/CORRECTIONS.md): first-order upwind adds
K_num = |u| dx / 2 (1 - C), C = |u| dt / dx. Compare against physical
horizontal diffusivity from Okubo (1971): K = 0.0103 L^1.15 (cgs units).
The solver below lets the test suite measure K_num empirically and show that a
flux-limited (monotonised-central) scheme removes most of it.
"""
from __future__ import annotations
import math
import numpy as np


def k_num_upwind(u_ms: float, dx_m: float, dt_s: float | None = None) -> float:
    c = abs(u_ms) * dt_s / dx_m if dt_s else 0.0
    return abs(u_ms) * dx_m / 2.0 * (1.0 - c)


def okubo_kh(scale_m: float) -> float:
    """Apparent horizontal diffusivity (m2/s) at length scale L (Okubo 1971)."""
    return 0.0103 * (scale_m * 100.0) ** 1.15 * 1e-4


def okubo_crossover_scale(k_m2s: float) -> float:
    """Length scale (m) below which K exceeds Okubo's physical diffusivity."""
    return (k_m2s * 1e4 / 0.0103) ** (1 / 1.15) / 100.0


def _mc_limiter(r: np.ndarray) -> np.ndarray:
    return np.maximum(0.0, np.minimum(np.minimum(2 * r, 0.5 * (1 + r)), 2.0))


def advect_diffuse_1d(c0: np.ndarray, u: float, k: float, dx: float, dt: float,
                      n_steps: int, scheme: str = "upwind") -> np.ndarray:
    """Periodic 1-D advection-diffusion, u > 0. scheme = 'upwind' | 'tvd'."""
    c = c0.astype(float).copy()
    cfl = u * dt / dx
    if cfl > 1 or k * dt / dx ** 2 > 0.5:
        raise ValueError("unstable time step")
    for _ in range(n_steps):
        cm1 = np.roll(c, 1)
        cp1 = np.roll(c, -1)
        if scheme == "upwind":
            face = c  # value at face i+1/2 for u > 0
        elif scheme == "tvd":
            num = c - cm1
            den = cp1 - c
            with np.errstate(divide="ignore", invalid="ignore"):
                r = np.where(np.abs(den) > 1e-300, num / den, 0.0)
            face = c + 0.5 * _mc_limiter(r) * (1 - cfl) * (cp1 - c)
        else:
            raise ValueError(scheme)
        flux = u * face
        c = c - dt / dx * (flux - np.roll(flux, 1)) + k * dt / dx ** 2 * (cp1 - 2 * c + cm1)
    return c


def effective_diffusivity(c_start: np.ndarray, c_end: np.ndarray, x: np.ndarray,
                          elapsed_s: float) -> float:
    def var(c):
        m = c.sum()
        mu = (x * c).sum() / m
        return ((x - mu) ** 2 * c).sum() / m
    return (var(c_end) - var(c_start)) / (2.0 * elapsed_s)
