"""Similarity scaling checks for the independent MTT integral jet model.

Scaling source: Fischer et al. (1979) Mixing in Inland and Coastal Waters,
Ch. 9–10 — round pure jet centreline dilution ∝ z; round pure plume
centreline dilution ∝ z^{5/3}. Also Morton, Taylor & Turner (1956) for the
entrainment plume similarity structure.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmarks.integral_jet import EntrainmentParams, integrate_round_jet


# Relative tolerance on the local power-law exponent fitted over the far-field
# window. 15% allows for residual transition and discrete ODE error while still
# distinguishing z^1 from z^{5/3}.
SCALING_RTOL = 0.15


def _log_log_slope(z: np.ndarray, s: np.ndarray, z_lo: float, z_hi: float) -> float:
    mask = (z >= z_lo) & (z <= z_hi) & (s > 1.05)
    assert mask.sum() >= 8, (z_lo, z_hi, mask.sum())
    coef = np.polyfit(np.log(z[mask]), np.log(s[mask]), 1)
    return float(coef[0])


def test_pure_jet_dilution_scales_linearly_with_z():
    """Pure momentum jet: S_c ∝ z (Fischer et al. 1979, round jet)."""
    d, Q, gp, z_max = 0.25, 0.1, 0.0, 40.0
    res = integrate_round_jet(d, Q, gp, z_max, n_points=400)
    # Far field but well above the port: ~20–80 diameters
    slope = _log_log_slope(res.z_m, res.dilution_centreline, 5.0, 35.0)
    assert slope == pytest.approx(1.0, rel=SCALING_RTOL), slope


def test_pure_plume_dilution_scales_as_z_to_the_five_thirds():
    """Pure plume (large z/l_M): S_c ∝ z^{5/3} (Fischer et al. 1979, round plume)."""
    # Small momentum length: weak exit velocity relative to buoyancy.
    d, Q, gp, z_max = 0.5, 0.02, 0.05, 60.0
    res = integrate_round_jet(d, Q, gp, z_max, n_points=500)
    assert math.isfinite(res.l_M_m) and res.l_M_m > 0
    # Sample deep in the plume regime z/l_M ≫ 1 (Fischer: plume-like for z/l_M > 5)
    z_lo = max(5.0 * res.l_M_m, 10.0)
    z_hi = z_max * 0.95
    assert z_hi > z_lo * 1.5, (res.l_M_m, z_lo, z_hi)
    slope = _log_log_slope(res.z_m, res.dilution_centreline, z_lo, z_hi)
    assert slope == pytest.approx(5.0 / 3.0, rel=SCALING_RTOL), (slope, res.l_M_m)


def test_buoyant_jet_transitions_toward_plume_scaling():
    """Forced plume: far-field exponent approaches 5/3 once z ≫ l_M."""
    # Larger port / modest velocity → smaller l_M so z/l_M ≫ 1 fits in domain.
    d, Q, gp, z_max = 0.4, 0.04, 0.03, 100.0
    res = integrate_round_jet(d, Q, gp, z_max, n_points=500)
    z_lo = max(8.0 * res.l_M_m, 15.0)
    z_hi = z_max * 0.95
    assert z_hi > z_lo * 1.3, (res.l_M_m, z_lo, z_hi)
    slope = _log_log_slope(res.z_m, res.dilution_centreline, z_lo, z_hi)
    assert slope == pytest.approx(5.0 / 3.0, rel=SCALING_RTOL), (slope, res.l_M_m)


def test_entrainment_params_are_explicit():
    """Uncertain Fr_p / λ remain parameters (never hard-wired as silent invent)."""
    p = EntrainmentParams(fr_plume=3.4, lambda_conc=1.1)
    res = integrate_round_jet(0.3, 0.05, 0.02, 20.0, params=p, n_points=100)
    assert res.params.fr_plume == 3.4
    assert res.params.lambda_conc == 1.1
    assert res.dilution_centreline[-1] >= 1.0
