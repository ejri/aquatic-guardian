"""Growth and carrying capacity for contained aquaculture using reused heat.

ALL species parameters here are PLACEHOLDERS (see SpeciesParams.placeholder).
They must be replaced with species-specific literature values and reviewed by a
fish-health veterinarian before any result is used.

Growth: thermal-unit growth coefficient (Iwama & Tautz 1981; Cho 1992),
W_f^(1/3) = W_i^(1/3) + (TGC/1000) * sum(T * days), valid only up to the
thermal optimum. Above T_opt growth declines linearly to zero at T_max.

Carrying capacity is the minimum of three limits:
  DO supply   (inflow oxygen above the welfare floor / oxygen demand),
  ammonia     (TAN production P_TAN = feed * protein * 0.092, Timmons & Ebeling),
  welfare     (maximum stocking density from a named welfare standard).
Because DO saturation falls and un-ionised ammonia rises with temperature while
oxygen demand rises, the yield-optimal temperature sits below the growth
optimum.
"""
from __future__ import annotations
from dataclasses import dataclass
from .water_quality import do_saturation_mg_l, unionised_fraction


@dataclass
class SpeciesParams:
    name: str = "generic salmonid (PLACEHOLDER)"
    tgc: float = 2.5                  # TGC x 1000 units, placeholder
    t_opt: float = 15.0               # C, placeholder
    t_max: float = 22.0               # C, placeholder
    mo2_mg_kg_h_at_tref: float = 250  # mg O2 per kg fish per h at t_ref, placeholder
    t_ref: float = 12.0
    q10: float = 2.3
    do_floor_mg_l: float = 7.0        # welfare floor at outflow, placeholder
    feed_rate_frac_bw_day: float = 0.012
    feed_protein_frac: float = 0.45
    nh3_limit_mg_l: float = 0.0125    # un-ionised NH3 limit, placeholder
    max_density_kg_m3: float = 30.0   # welfare stocking cap, placeholder
    placeholder: bool = True


def growth_factor(t_c: float, sp: SpeciesParams) -> float:
    if t_c <= sp.t_opt:
        return 1.0
    if t_c >= sp.t_max:
        return 0.0
    return (sp.t_max - t_c) / (sp.t_max - sp.t_opt)


def tgc_growth(w0_g: float, t_c: float, days: float, sp: SpeciesParams) -> float:
    t_eff = min(t_c, sp.t_opt) * growth_factor(t_c, sp)
    return (w0_g ** (1 / 3) + sp.tgc / 1000.0 * t_eff * days) ** 3


def oxygen_demand_mg_kg_h(t_c: float, sp: SpeciesParams) -> float:
    return sp.mo2_mg_kg_h_at_tref * sp.q10 ** ((t_c - sp.t_ref) / 10.0)


def carrying_capacity_kg(t_c: float, s_psu: float, ph: float, flow_m3_h: float,
                         tank_volume_m3: float, sp: SpeciesParams,
                         inflow_do_fraction_sat: float = 1.0) -> dict:
    do_in = do_saturation_mg_l(t_c, s_psu) * inflow_do_fraction_sat
    do_budget = max(do_in - sp.do_floor_mg_l, 0.0) * flow_m3_h * 1000.0      # mg O2/h
    b_do = do_budget / oxygen_demand_mg_kg_h(t_c, sp)
    tan_per_kg_day = sp.feed_rate_frac_bw_day * sp.feed_protein_frac * 0.092 * 1e6  # mg TAN/kg/day
    tan_limit = sp.nh3_limit_mg_l / unionised_fraction(t_c, ph, s_psu)          # mg TAN/L allowed
    b_nh3 = tan_limit * flow_m3_h * 24 * 1000.0 / tan_per_kg_day
    b_welfare = sp.max_density_kg_m3 * tank_volume_m3
    limits = {"do": b_do, "ammonia": b_nh3, "welfare": b_welfare}
    binding = min(limits, key=limits.get)
    return {"limits_kg": limits, "capacity_kg": limits[binding], "binding": binding,
            "do_in_mg_l": do_in}


def yield_index(t_c: float, s_psu: float, ph: float, flow_m3_h: float, tank_volume_m3: float,
                sp: SpeciesParams) -> float:
    """Relative production rate: capacity x specific growth (cube-root TGC gain)."""
    cap = carrying_capacity_kg(t_c, s_psu, ph, flow_m3_h, tank_volume_m3, sp)["capacity_kg"]
    return cap * min(t_c, sp.t_opt) * growth_factor(t_c, sp)
