"""Heat budget of a data centre and the cooling-water flow it implies.

Essentially all electrical power delivered to a data centre leaves as heat, so
total heat rejected is IT load x PUE. What fraction goes to a water body
depends on the cooling design and is an input, not an assumption.
"""
from __future__ import annotations
from .seawater import rho_cp

COOLING_TYPES = {
    # default fraction of rejected heat that goes to the receiving water
    "once_through": 1.0,     # seawater/surface-water once-through or submerged hull
    "hybrid": 0.5,           # part water, part dry coolers or towers (placeholder)
    "closed_loop_air": 0.0,  # dry coolers; heat to air, negligible water discharge
}


def heat_rejected_MW(it_load_mw: float, pue: float) -> float:
    if it_load_mw < 0 or pue < 1.0:
        raise ValueError("IT load must be >= 0 and PUE >= 1.0")
    return it_load_mw * pue


def heat_to_water_MW(it_load_mw: float, pue: float, fraction_to_water: float = 1.0,
                     reuse_fraction: float = 0.0) -> float:
    """Heat discharged to the receiving water after beneficial reuse is subtracted.

    reuse_fraction is the energy reuse factor (ERF, ISO/IEC 30134-6) of heat
    captured *before* discharge. Heat reused after discharge does not count
    (see docs/CORRECTIONS.md, correction 6).
    """
    if not (0 <= fraction_to_water <= 1 and 0 <= reuse_fraction <= 1):
        raise ValueError("fractions must be in [0, 1]")
    return heat_rejected_MW(it_load_mw, pue) * fraction_to_water * (1.0 - reuse_fraction)


def cooling_flow_m3s(heat_mw: float, delta_t_k: float, t_ambient_c: float = 12.0,
                     s_psu: float = 32.0) -> float:
    """Once-through flow needed to carry heat_mw at a temperature rise delta_t_k.

    Q = P / (rho c_p dT). For seawater this is ~24 L/s per MW at dT = 10 K.
    """
    if delta_t_k <= 0:
        raise ValueError("delta_t_k must be > 0")
    return heat_mw * 1e6 / (rho_cp(t_ambient_c, s_psu) * delta_t_k)
