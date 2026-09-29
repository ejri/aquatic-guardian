"""Tidal kinematics for screening.

For u(t) = U sin(omega t) the displacement over one flood (or one ebb) is
2U/omega. Over whole cycles the oscillatory displacement cancels and only the
residual drift remains (Correction 2, docs/CORRECTIONS.md).
"""
from __future__ import annotations
import math

M2_PERIOD_S = 12.4206012 * 3600.0
OMEGA_M2 = 2.0 * math.pi / M2_PERIOD_S     # 1.4052e-4 s-1


def excursion_half_cycle(u_peak_ms: float, omega: float = OMEGA_M2) -> float:
    return 2.0 * u_peak_ms / omega


def implied_peak_current(excursion_m: float, omega: float = OMEGA_M2) -> float:
    return excursion_m * omega / 2.0


def residual_drift(u_residual_ms: float, n_cycles: float = 1.0) -> float:
    return u_residual_ms * n_cycles * M2_PERIOD_S
