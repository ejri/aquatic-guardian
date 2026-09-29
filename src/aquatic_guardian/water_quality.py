"""Dissolved oxygen solubility and ammonia speciation.

DO: Garcia & Gordon (1992) fit to Benson & Krause (1984) data, cm3/dm3
coefficients, converted to mg/L with 1.42905 mg per cm3 O2.

Ammonia (Correction 5): Emerson et al. (1975) pKa, as used in EPA's 2013
freshwater criteria; seawater ionic-strength correction of Khoo et al.
(1977) in the form used by Florida DEP; check against Bower & Bidwell (1978).
EPA 2013 freshwater criteria are evaluated with the equations in EPA
822-R-13-001. EPA saltwater ammonia criteria (1989, EPA 440/5-88-004) were
not revised in 2013.
"""
from __future__ import annotations
import math

_A = (2.00907, 3.22014, 4.05010, 4.94457, -2.56847e-1, 3.88767)
_B = (-6.24523e-3, -7.37614e-3, -1.03410e-2, -8.17083e-3)
_C0 = -4.88682e-7
ML_TO_MG_O2 = 1.42905


def do_saturation_mg_l(t_c: float, s_psu: float) -> float:
    ts = math.log((298.15 - t_c) / (273.15 + t_c))
    ln_c = (_A[0] + _A[1] * ts + _A[2] * ts ** 2 + _A[3] * ts ** 3 + _A[4] * ts ** 4
            + _A[5] * ts ** 5
            + s_psu * (_B[0] + _B[1] * ts + _B[2] * ts ** 2 + _B[3] * ts ** 3)
            + _C0 * s_psu ** 2)
    return math.exp(ln_c) * ML_TO_MG_O2


def pka_nh4(t_c: float, s_psu: float = 0.0) -> float:
    pka = 0.09018 + 2729.92 / (t_c + 273.2)
    if s_psu > 0:
        ionic = 19.9273 * s_psu / (1000.0 - 1.005109 * s_psu)
        pka += (0.1552 - 0.0003142 * t_c) * ionic
    return pka


def unionised_fraction(t_c: float, ph: float, s_psu: float = 0.0) -> float:
    return 1.0 / (1.0 + 10 ** (pka_nh4(t_c, s_psu) - ph))


def epa2013_ccc_mg_tan_l(ph: float, t_c: float) -> float:
    """Chronic criterion (30-day rolling average), mg TAN/L, unionid mussels present
    (the national default). Site-specific variants (EPA 2013 Appendix N) are not
    implemented; use EPA's own recalculation procedure for those.
    """
    base = 0.8876 * (0.0278 / (1 + 10 ** (7.688 - ph)) + 1.1994 / (1 + 10 ** (ph - 7.688)))
    return base * 2.126 * 10 ** (0.028 * (20 - max(t_c, 7.0)))


def epa2013_cmc_mg_tan_l(ph: float, t_c: float, oncorhynchus_present: bool = True) -> float:
    """Acute criterion (1-hour average), mg TAN/L."""
    salmonid = 0.275 / (1 + 10 ** (7.204 - ph)) + 39.0 / (1 + 10 ** (ph - 7.204))
    invert = 0.7249 * (0.0114 / (1 + 10 ** (7.204 - ph)) + 1.6181 / (1 + 10 ** (ph - 7.204)))
    temp = 23.12 * 10 ** (0.036 * (20 - t_c))
    if oncorhynchus_present:
        return min(salmonid, invert * temp)
    return invert * min(51.93, temp)


EPA1989_SALTWATER_NH3 = {"cmc_mg_nh3_l": 0.233, "ccc_mg_nh3_l": 0.035,
                         "status": "verify against EPA 440/5-88-004 and state adoption"}
CCME_FRESHWATER_NH3_MG_L = 0.019   # long-term, un-ionised NH3; CCME has no marine guideline
