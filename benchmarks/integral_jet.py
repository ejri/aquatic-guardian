"""Independent integral model of a round buoyant jet in stagnant, unstratified ambient.

Formulation
-----------
Morton, Taylor and Turner (1956) entrainment hypothesis with **Gaussian**
self-similar profiles (Lee & Chu 2003 convention):

    Q = π u_c b²
    M = (π/2) u_c² b²
    B = [π λ² / (1+λ²)] u_c g'_c b²   (buoyancy flux; conserved if unstratified)

Evolution in stagnant, unstratified ambient:

    dQ/dz = 2 π α u_c b
    dM/dz = B / u_c
    dB/dz = 0

Variable entrainment (jet → plume), densimetric Froude form of Lee & Chu
(2003), consistent with Fischer et al. (1979) §9–10:

    α = α_j + (α_p − α_j) · min(1, (Fr_p / Fr_l)²)
    Fr_l = u_c / √(g'_c b)

Centreline dilution from conserved tracer (Lee & Chu profile factor):

    S_c = [λ² / (1+λ²)] · (Q / Q₀)

Entrainment coefficients (named sources)
----------------------------------------
- α_j = 0.057 — round jet, Lee & Chu (2003) *Turbulent Jets and Plumes*, §2.3
  (Gaussian half-width). Fischer et al. (1979) *Mixing in Inland and Coastal
  Waters* quote ≈ 0.053–0.057.
- α_p = 0.083 — round plume, Fischer et al. (1979); Lee & Chu (2003) also quote
  ≈ 0.083–0.088. Default uses Fischer's 0.083.

Parameters flagged for human confirmation
-----------------------------------------
- Fr_p (default 3.5): asymptotic plume densimetric Froude number. Literature
  values are typically 3.4–3.7 depending on profile and Fr definition (List
  1982; Lee & Chu 2003). Treated as a parameter, not a constant — **verify**
  that this Fr_p matches Fr_l = u_c/√(g'_c b) as coded here.
- lambda_conc (default 1.2): concentration-to-velocity width ratio λ = b_c/b_u.
  Lee & Chu (2003) use λ ≈ 1.2; **verify** if pairing with a specific UM3
  profile option.
- Zone of flow establishment and virtual origin are NOT modelled. Initial
  conditions match a top-hat round-port exit (Q₀, M₀ = Q₀ U₀) projected onto
  the Gaussian flux definitions above.

This module is a benchmark only. It does not change library coefficients in
``aquatic_guardian.plume``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy.integrate import solve_ivp


# Named-source defaults (see module docstring).
ALPHA_JET = 0.057       # Lee & Chu (2003); Fischer et al. (1979) ~0.053–0.057
ALPHA_PLUME = 0.083     # Fischer et al. (1979); Lee & Chu (2003) ~0.083–0.088
FR_PLUME = 3.5          # verify: literature range ~3.4–3.7 (List 1982; Lee & Chu 2003)
LAMBDA_CONC = 1.2       # verify: Lee & Chu (2003) typical λ = b_c / b_u


@dataclass(frozen=True)
class EntrainmentParams:
    """Entrainment and profile parameters for the integral model.

    Uncertain values are explicit fields so they are never invented silently.
    """
    alpha_jet: float = ALPHA_JET
    alpha_plume: float = ALPHA_PLUME
    fr_plume: float = FR_PLUME          # verify
    lambda_conc: float = LAMBDA_CONC    # verify


@dataclass
class IntegralResult:
    """Centreline dilution and fluxes versus height."""
    z_m: np.ndarray
    dilution_centreline: np.ndarray
    dilution_volume: np.ndarray
    Q_m3s: np.ndarray
    M_m4s2: np.ndarray
    B_m4s3: float
    l_M_m: float
    params: EntrainmentParams


def _local_state(Q: float, M: float, B: float, lam: float) -> tuple[float, float, float]:
    """Return u_c, b, g'_c from Gaussian fluxes."""
    Q = max(Q, 1e-30)
    M = max(M, 1e-30)
    u_c = 2.0 * M / Q
    b = Q / np.sqrt(2.0 * np.pi * M)
    lam2 = lam ** 2
    # B = [λ²/(1+λ²)] Q g'_c  →  g'_c = B (1+λ²)/(λ² Q)
    g_c = B * (1.0 + lam2) / (lam2 * Q) if B > 0 else 0.0
    return u_c, b, g_c


def entrainment_coefficient(Q: float, M: float, B: float, params: EntrainmentParams) -> float:
    """α(Fr) transitioning from jet to plume (Lee & Chu / Fischer form)."""
    if B <= 0:
        return params.alpha_jet
    u_c, b, g_c = _local_state(Q, M, B, params.lambda_conc)
    fr_l = u_c / np.sqrt(max(g_c * b, 1e-30))
    blend = min(1.0, (params.fr_plume / max(fr_l, 1e-12)) ** 2)
    return params.alpha_jet + (params.alpha_plume - params.alpha_jet) * blend


def centreline_dilution_factor(params: EntrainmentParams) -> float:
    """S_c / (Q/Q₀) = λ²/(1+λ²) for Gaussian velocity and concentration profiles.

    For λ = 1.2 this is ≈ 0.590, matching the Fischer et al. (1979) ratio of
    centreline coefficient ≈ 0.089 to volume-flux coefficient ≈ 0.15.
    """
    lam2 = params.lambda_conc ** 2
    return lam2 / (1.0 + lam2)


def jet_momentum_length(M: float, B: float) -> float:
    """Fischer et al. (1979) jet/plume transition length l_M = M^{3/4} / B^{1/2}."""
    if B <= 0:
        return float("inf")
    return M ** 0.75 / np.sqrt(B)


def integrate_round_jet(
    port_diameter_m: float,
    port_flow_m3s: float,
    g_prime_m_s2: float,
    z_max_m: float,
    *,
    n_points: int = 200,
    params: Optional[EntrainmentParams] = None,
    rtol: float = 1e-7,
    atol: float = 1e-9,
) -> IntegralResult:
    """Integrate a round buoyant jet; return centreline dilution versus height.

    Parameters
    ----------
    port_diameter_m, port_flow_m3s
        Exit diameter and volume flux of one round port.
    g_prime_m_s2
        Reduced gravity of the discharge relative to ambient (m/s²). Use 0 for
        a pure momentum jet.
    z_max_m
        Maximum height above the port to integrate to (m).
    """
    if port_diameter_m <= 0 or port_flow_m3s <= 0 or z_max_m <= 0:
        raise ValueError("diameter, flow and z_max must be positive")
    params = params or EntrainmentParams()

    area = np.pi * port_diameter_m ** 2 / 4.0
    u0 = port_flow_m3s / area
    Q0 = port_flow_m3s
    # Top-hat exit momentum; Gaussian state uses M = (π/2) u_c² b² with the same
    # integrated momentum as the port (M₀ = Q₀ U₀).
    M0 = Q0 * u0
    B0 = max(g_prime_m_s2, 0.0) * Q0
    l_M = jet_momentum_length(M0, B0)

    def rhs(_z: float, y: np.ndarray) -> list[float]:
        Q, M = float(y[0]), float(y[1])
        u_c, b, _g = _local_state(Q, M, B0, params.lambda_conc)
        alpha = entrainment_coefficient(Q, M, B0, params)
        dQ = 2.0 * np.pi * alpha * u_c * b
        dM = B0 / max(u_c, 1e-30) if B0 > 0 else 0.0
        return [dQ, dM]

    z_eval = np.linspace(0.0, z_max_m, n_points)
    sol = solve_ivp(
        rhs,
        (0.0, z_max_m),
        y0=[Q0, M0],
        t_eval=z_eval,
        method="RK45",
        rtol=rtol,
        atol=atol,
        dense_output=False,
    )
    if not sol.success:
        raise RuntimeError(f"Integral jet ODE failed: {sol.message}")

    Q = np.maximum(sol.y[0], Q0)
    M = np.maximum(sol.y[1], 1e-30)
    s_vol = Q / Q0
    s_cl = centreline_dilution_factor(params) * s_vol
    # At the orifice the Gaussian conversion is not physical; pin S >= 1.
    s_cl = np.maximum(s_cl, 1.0)
    s_vol = np.maximum(s_vol, 1.0)

    return IntegralResult(
        z_m=sol.t,
        dilution_centreline=s_cl,
        dilution_volume=s_vol,
        Q_m3s=Q,
        M_m4s2=M,
        B_m4s3=B0,
        l_M_m=l_M,
        params=params,
    )


def dilution_at_height(
    port_diameter_m: float,
    port_flow_m3s: float,
    g_prime_m_s2: float,
    z_m: float,
    *,
    params: Optional[EntrainmentParams] = None,
) -> dict:
    """Convenience wrapper: centreline dilution and length scales at one height."""
    res = integrate_round_jet(
        port_diameter_m, port_flow_m3s, g_prime_m_s2, z_m,
        n_points=max(50, int(z_m * 20)),
        params=params,
    )
    return {
        "z_m": float(res.z_m[-1]),
        "dilution_centreline": float(res.dilution_centreline[-1]),
        "dilution_volume": float(res.dilution_volume[-1]),
        "l_M_m": float(res.l_M_m),
        "z_over_l_M": float(res.z_m[-1] / res.l_M_m) if np.isfinite(res.l_M_m) else float("inf"),
        "Q_m3s": float(res.Q_m3s[-1]),
        "B_m4s3": float(res.B_m4s3),
    }
