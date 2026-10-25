"""Seawater properties at atmospheric pressure.

PLUMES2.0 (manual §3.3.1) computes plume and ambient density from the
UNESCO/Fofonoff (1985) equation of state as sigma-t, i.e. at p = 0. The same is
done here so that density differences, which drive buoyancy, match the EPA
model. Heat capacity (Millero et al. 1973, p = 0) and dissolved-oxygen
saturation (Garcia & Gordon 1992, Benson & Krause fit) support the extended
thermal and biological metrics that PLUMES2.0 does not report.
"""
from __future__ import annotations

import math

G = 9.80665  # m s^-2


def density(S: float, T: float) -> float:
    """Seawater density (kg/m^3), UNESCO EOS-80 at p = 0.

    Check values (UNESCO 1981): rho(0, 5) = 999.96675, rho(35, 5) = 1027.67547,
    rho(35, 25) = 1023.34306.
    """
    T2, T3, T4, T5 = T * T, T ** 3, T ** 4, T ** 5
    rw = (999.842594 + 6.793952e-2 * T - 9.095290e-3 * T2 + 1.001685e-4 * T3
          - 1.120083e-6 * T4 + 6.536332e-9 * T5)
    if S <= 0:
        return rw
    A = 0.824493 - 4.0899e-3 * T + 7.6438e-5 * T2 - 8.2467e-7 * T3 + 5.3875e-9 * T4
    B = -5.72466e-3 + 1.0227e-4 * T - 1.6546e-6 * T2
    C = 4.8314e-4
    return rw + A * S + B * S ** 1.5 + C * S * S


def sigma_t(S: float, T: float) -> float:
    return density(S, T) - 1000.0


def heat_capacity(S: float, T: float) -> float:
    """Specific heat of seawater at p = 0, J/(kg K) (Millero et al. 1973)."""
    T2, T3, T4 = T * T, T ** 3, T ** 4
    cp0 = 4217.4 - 3.720283 * T + 0.1412855 * T2 - 2.654387e-3 * T3 + 2.093236e-5 * T4
    if S <= 0:
        return cp0
    a = -7.6444 + 0.107276 * T - 1.3839e-3 * T2
    b = 0.17709 - 4.0772e-3 * T + 5.3539e-5 * T2
    return cp0 + a * S + b * S ** 1.5


def thermal_expansion(S: float, T: float, dT: float = 0.01) -> float:
    """Thermal expansion coefficient (1/K) by central difference."""
    r0 = density(S, T)
    return -(density(S, T + dT) - density(S, T - dT)) / (2 * dT * r0)


def oxygen_saturation_mg_l(S: float, T: float) -> float:
    """Dissolved-oxygen saturation (mg/L) at 1 atm, Garcia & Gordon (1992),
    Benson & Krause coefficients (combined fit, umol/kg), converted with the
    in-situ density. Check: ~9.09 mg/L at 20 C fresh, ~7.4 mg/L at 20 C, S=35.
    """
    Ts = math.log((298.15 - T) / (273.15 + T))
    A0, A1, A2, A3, A4, A5 = 5.80871, 3.20291, 4.17887, 5.10006, -9.86643e-2, 3.80369
    B0, B1, B2, B3 = -7.01577e-3, -7.70028e-3, -1.13864e-2, -9.51519e-3
    C0 = -2.75915e-7
    lnC = (A0 + A1 * Ts + A2 * Ts ** 2 + A3 * Ts ** 3 + A4 * Ts ** 4 + A5 * Ts ** 5
           + S * (B0 + B1 * Ts + B2 * Ts ** 2 + B3 * Ts ** 3) + C0 * S * S)
    umol_kg = math.exp(lnC)
    return umol_kg * density(S, T) * 31.9988e-6  # umol/kg * kg/m3 * mg/umol / 1000 L


MGD_TO_M3S = 0.0438126364  # 1 million US gallons per day in m^3/s
CFS_TO_M3S = 0.028316846592
FT_TO_M = 0.3048


def f_to_c_delta(dF: float) -> float:
    return dF * 5.0 / 9.0
