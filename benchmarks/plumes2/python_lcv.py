"""Python near-field plume for the P-3 cases — Lee & Chu integral model on Linux.

Why this exists
---------------
The public PLUMES 2.0 zip (``plumes2/PLUMES2.0-main.zip``) contains only a
Windows GUI binary (``plumes2.0v1.exe``). No Fortran sources are published on
``ssmc-uw/PLUMES2.0``, so the EPA code cannot be compiled or ported here.

This module runs the same 16 discharges using the repository's already-tested
Morton–Taylor–Turner / Lee & Chu integral jet (``benchmarks/integral_jet.py``),
extended with:

- multiport merging when the round-plume diameter reaches port spacing
  (switch to line-plume shear; EPA 600/B-24/339 Fig. 4 idea);
- a weak-current correction via forced entrainment on the round-jet ODE
  (aspiration default 0.1 = PLUMES 2.0 GUI default in the P-3 README).

**This is not EPA PLUMES 2.0 / UM3.** Results must not close verification item
P-3. Use real PLUMES 2.0 on Windows for that.

Density: UNESCO EOS-80 via ``aquatic_guardian.seawater``.
"""
from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
from scipy.integrate import solve_ivp

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from aquatic_guardian.seawater import reduced_gravity  # noqa: E402
from benchmarks.integral_jet import (  # noqa: E402
    EntrainmentParams,
    _local_state,
    centreline_dilution_factor,
    entrainment_coefficient,
    jet_momentum_length,
)

# verify: PLUMES 2.0 GUI default aspiration; peak-to-mean limits from EPA manual.
ASPIRATION = 0.1
RATIO_ROUND = 3.89
RATIO_LINE = 2.22


@dataclass(frozen=True)
class RunParams:
    entrainment: EntrainmentParams = EntrainmentParams()
    aspiration: float = ASPIRATION
    ratio_round: float = RATIO_ROUND
    ratio_line: float = RATIO_LINE


@dataclass
class CaseResult:
    case_id: str
    flux_avg_dilution: float
    centerline_dilution: float
    plume_diameter_m: float
    centerline_depth_at_termination_m: float
    termination: str
    merged: str
    rise_m: float
    notes: str


def _peak_ratio(s_vol: float, merged: bool, p: RunParams) -> float:
    limit = p.ratio_line if merged else p.ratio_round
    return 1.0 + (limit - 1.0) * (1.0 - 1.0 / max(s_vol, 1.0))


def _integrate_round_with_current(
    d: float,
    q0: float,
    g_prime: float,
    z_max: float,
    u_a: float,
    params: RunParams,
    n_points: int = 400,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    """Round buoyant jet; optional weak crossflow forced entrainment.

    Forced term (verify): dQ/dz += aspiration * U_a * 2 b, a projected-area
    form consistent with the PAE idea summarised in the PLUMES 2.0 manual.
    """
    area = math.pi * d * d / 4.0
    u0 = q0 / area
    m0 = q0 * u0
    b0 = max(g_prime, 0.0) * q0
    ep = params.entrainment
    l_m = jet_momentum_length(m0, b0)

    def rhs(_z: float, y: np.ndarray) -> list[float]:
        q, m = float(y[0]), float(y[1])
        u_c, b, _g = _local_state(q, m, b0, ep.lambda_conc)
        alpha = entrainment_coefficient(q, m, b0, ep)
        dq = 2.0 * math.pi * alpha * u_c * b
        if u_a > 0:
            dq += params.aspiration * u_a * (2.0 * b)
        dm = b0 / max(u_c, 1e-30) if b0 > 0 else 0.0
        return [dq, dm]

    z = np.linspace(0.0, z_max, n_points)
    sol = solve_ivp(rhs, (0.0, z_max), y0=[q0, m0], t_eval=z, method="RK45", rtol=1e-7, atol=1e-9)
    if not sol.success:
        raise RuntimeError(sol.message)
    q = np.maximum(sol.y[0], q0)
    m = np.maximum(sol.y[1], 1e-30)
    diam = np.empty_like(q)
    for i in range(len(q)):
        _u, b, _ = _local_state(q[i], m[i], b0, ep.lambda_conc)
        diam[i] = 2.0 * b
    s_vol = np.maximum(q / q0, 1.0)
    return sol.t, s_vol, diam, q, l_m


def _continue_as_line(
    z0: float,
    q0_port: float,
    q_at_merge: float,
    g_prime: float,
    spacing: float,
    z_max: float,
    u_a: float,
    params: RunParams,
    n_points: int = 200,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Line-plume segment after merge: fluxes per unit length, one port's spacing."""
    # Per-unit-length volume flux at merge.
    q_line0 = q_at_merge / spacing
    b_line = g_prime * (q0_port / spacing)  # buoyancy per unit length (conserved from port)
    # Top-hat line: q = 2 b_half u  → need momentum per length m = q u.
    # Initialise u from round state order-of-magnitude: u ~ q_line / d_char.
    u_init = max(q_line0 / max(0.5 * spacing, 1e-3), 1e-3)
    m_line0 = q_line0 * u_init
    ep = params.entrainment

    def rhs(_z: float, y: np.ndarray) -> list[float]:
        ql, ml = float(y[0]), float(y[1])
        u = max(ml / max(ql, 1e-30), 1e-30)
        # Half-width from ql = 2 b u.
        b_half = ql / max(2.0 * u, 1e-30)
        # Line shear: dql/dz = 2 α u; α → plume value for buoyant line.
        fr = u / math.sqrt(max(g_prime * b_half, 1e-30)) if g_prime > 0 else 1e9
        blend = min(1.0, (ep.fr_plume / max(fr, 1e-12)) ** 2)
        alpha = ep.alpha_jet + (ep.alpha_plume - ep.alpha_jet) * blend
        dql = 2.0 * alpha * u
        if u_a > 0:
            dql += params.aspiration * u_a  # per unit length
        dml = b_line / max(u, 1e-30) if b_line > 0 else 0.0
        return [dql, dml]

    if z_max <= z0:
        return np.array([z0]), np.array([q_at_merge / q0_port]), np.array([spacing])
    z = np.linspace(z0, z_max, max(20, n_points))
    sol = solve_ivp(
        rhs, (z0, z_max), y0=[q_line0, m_line0], t_eval=z, method="RK45", rtol=1e-7, atol=1e-9
    )
    if not sol.success:
        raise RuntimeError(sol.message)
    ql = np.maximum(sol.y[0], q_line0)
    # Dilution relative to port: (ql * spacing) / q0_port
    s_vol = np.maximum(ql * spacing / q0_port, 1.0)
    # Slot thickness ~ spacing once merged (diameter interpretation for CSV).
    diam = np.full_like(s_vol, spacing)
    return sol.t, s_vol, diam


def simulate_case(
    *,
    case_id: str = "",
    n_ports: int,
    port_diameter_m: float,
    port_spacing_m: float,
    port_depth_m: float,
    total_flow_m3s: float,
    effluent_temperature_c: float,
    ambient_temperature_c: float,
    salinity_psu: float,
    current_ms: float,
    params: Optional[RunParams] = None,
) -> CaseResult:
    p = params or RunParams()
    q0 = total_flow_m3s / n_ports
    delta_t = effluent_temperature_c - ambient_temperature_c
    gp = reduced_gravity(ambient_temperature_c, delta_t, salinity_psu)
    z_max = port_depth_m  # rise to free surface
    ua = float(current_ms)
    spacing = float(port_spacing_m) if n_ports > 1 and port_spacing_m else float("inf")

    z, s_vol, diam, q, _l_m = _integrate_round_with_current(
        port_diameter_m, q0, gp, z_max, ua, p
    )
    merged = False
    merge_i = None
    if n_ports > 1 and math.isfinite(spacing):
        hit = np.where(diam >= spacing)[0]
        if len(hit):
            merge_i = int(hit[0])
            merged = True

    if merged and merge_i is not None and merge_i < len(z) - 2:
        z0 = float(z[merge_i])
        q_m = float(q[merge_i])
        z2, s2, d2 = _continue_as_line(
            z0, q0, q_m, gp, spacing, z_max, ua, p
        )
        # Stitch: use line segment for z >= z0.
        s_end = float(s2[-1])
        d_end = float(d2[-1])
    else:
        s_end = float(s_vol[-1])
        d_end = float(diam[-1])

    # Flux-average ≈ volume dilution for top-hat / integral Q/Q0.
    # Centreline: apply peak-to-mean (manual §3.3.1) OR Lee–Chu Gaussian factor.
    # Prefer Lee–Chu Gaussian centreline factor for round; peak ratio for merged.
    if merged:
        s_cl = s_end / _peak_ratio(s_end, True, p)
        s_flux = s_end
    else:
        s_flux = s_end
        s_cl = centreline_dilution_factor(p.entrainment) * s_end
        # Near orifice the Gaussian conversion over-states; floor at 1.
        s_cl = max(s_cl, 1.0)

    notes = (
        "Python Lee–Chu integral (benchmarks/integral_jet) + merge/crossflow; "
        "NOT EPA PLUMES 2.0 — cannot close P-3."
    )
    return CaseResult(
        case_id=case_id,
        flux_avg_dilution=round(s_flux, 4),
        centerline_dilution=round(max(s_cl, 1.0), 4),
        plume_diameter_m=round(d_end, 4),
        centerline_depth_at_termination_m=0.0,
        termination="surface hit",
        merged=("yes" if merged else "no") if n_ports > 1 else "",
        rise_m=round(z_max, 4),
        notes=notes,
    )


def simulate_from_case_row(row: dict, params: Optional[RunParams] = None) -> CaseResult:
    spacing = row.get("port_spacing_m") or ""
    return simulate_case(
        case_id=row["case_id"],
        n_ports=int(row["number_of_ports"]),
        port_diameter_m=float(row["port_diameter_m"]),
        port_spacing_m=float(spacing) if str(spacing).strip() else 0.0,
        port_depth_m=float(row["port_depth_m"]),
        total_flow_m3s=float(row["total_effluent_flow_m3s"]),
        effluent_temperature_c=float(row["effluent_temperature_c"]),
        ambient_temperature_c=float(row["ambient_temperature_c"]),
        salinity_psu=float(row["ambient_salinity_psu"]),
        current_ms=float(row["current_ms"]),
        params=params,
    )
