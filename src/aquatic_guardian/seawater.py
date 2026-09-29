"""Seawater properties at atmospheric pressure.

Density uses the UNESCO EOS-80 one-atmosphere equation (Millero & Poisson 1981;
UNESCO 1981, Technical Papers in Marine Science 36). It is superseded for
oceanographic research by TEOS-10, but is accurate to ~0.01 kg/m3 over the
coastal range (0-40 C, 0-42 psu) and has published check values, which the
test suite reproduces. Heat capacity is a screening constant.
"""
from __future__ import annotations

G = 9.81  # m s-2
CP_SEAWATER = 3990.0   # J kg-1 K-1, S~35, 10-20 C (screening constant)
CP_FRESHWATER = 4184.0


def density_eos80(t_c: float, s_psu: float) -> float:
    """Density (kg/m3) at p = 0 from UNESCO EOS-80."""
    t = t_c
    rho_w = (999.842594 + 6.793952e-2 * t - 9.095290e-3 * t**2 + 1.001685e-4 * t**3
             - 1.120083e-6 * t**4 + 6.536332e-9 * t**5)
    a = 8.24493e-1 - 4.0899e-3 * t + 7.6438e-5 * t**2 - 8.2467e-7 * t**3 + 5.3875e-9 * t**4
    b = -5.72466e-3 + 1.0227e-4 * t - 1.6546e-6 * t**2
    c = 4.8314e-4
    s = max(s_psu, 0.0)
    return rho_w + a * s + b * s**1.5 + c * s**2


def rho_cp(t_c: float, s_psu: float) -> float:
    """Volumetric heat capacity (J m-3 K-1)."""
    cp = CP_FRESHWATER + (CP_SEAWATER - CP_FRESHWATER) * min(max(s_psu, 0.0), 35.0) / 35.0
    return density_eos80(t_c, s_psu) * cp


def reduced_gravity(t_ambient_c: float, delta_t_k: float, s_psu: float) -> float:
    """g' = g (rho_a - rho_e)/rho_a for effluent warmer by delta_t_k at the same salinity.

    Heated seawater is only weakly buoyant: at 10 C a 10 K rise gives
    g' of roughly 0.02 m s-2, an order of magnitude less than a freshwater
    sewage plume in the sea (~0.25 m s-2).
    """
    rho_a = density_eos80(t_ambient_c, s_psu)
    rho_e = density_eos80(t_ambient_c + delta_t_k, s_psu)
    return G * (rho_a - rho_e) / rho_a
