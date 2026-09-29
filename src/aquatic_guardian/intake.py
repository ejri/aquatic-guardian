"""Cooling-water intake screening against US CWA §316(b) (40 CFR Part 125).

Subpart I (new facilities, 40 CFR 125.80-125.89) and Subpart J (existing
facilities, 40 CFR 125.90-125.99) apply to point sources with a cooling water
intake structure whose design intake flow exceeds 2 MGD and where >= 25 % of
the water withdrawn is used for cooling. Applicability to any specific data
centre is a legal determination; these functions only flag likely triggers.
"""
from __future__ import annotations
import math

MGD_TO_M3S = 3.785411784e3 / 86400.0      # 1 million US gal/day in m3/s (0.0438)
THRESHOLD_MGD = 2.0
THROUGH_SCREEN_LIMIT_MS = 0.5 * 0.3048    # 0.5 ft/s = 0.1524 m/s
COOLING_FRACTION_TRIGGER = 0.25


def mgd(q_m3s: float) -> float:
    return q_m3s / MGD_TO_M3S


def cwa316b_screen(design_intake_m3s: float, cooling_fraction: float = 1.0) -> dict:
    flow_mgd = mgd(design_intake_m3s)
    likely = flow_mgd > THRESHOLD_MGD and cooling_fraction >= COOLING_FRACTION_TRIGGER
    return {
        "design_intake_mgd": flow_mgd,
        "exceeds_2_mgd": flow_mgd > THRESHOLD_MGD,
        "cooling_fraction": cooling_fraction,
        "likely_applicable": likely,
        "min_screen_open_area_m2": design_intake_m3s / THROUGH_SCREEN_LIMIT_MS,
        "note": "Screening flag only; applicability and subpart require legal determination.",
    }


def tidal_volume_check(design_intake_m3s: float, tidal_excursion_m: float, depth_m: float,
                       cycle_hours: float = 12.4206) -> dict:
    """New-facility proportional-flow test for estuaries and tidal rivers
    (40 CFR 125.84(b)(3)(iii)): intake over one ebb and one flood must be
    <= 1 % of the water-column volume in a circle, centred on the intake,
    whose diameter is one tidal excursion at mean low water.
    Verify the provision's current text before relying on it.
    """
    volume = math.pi * (tidal_excursion_m / 2.0) ** 2 * depth_m
    withdrawn = design_intake_m3s * cycle_hours * 3600.0
    frac = withdrawn / volume if volume > 0 else float("inf")
    return {"reference_volume_m3": volume, "withdrawn_per_cycle_m3": withdrawn,
            "fraction": frac, "within_1_percent": frac <= 0.01}
