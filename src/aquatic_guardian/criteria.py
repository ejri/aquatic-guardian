"""Temperature criteria with provenance.

All thresholds live in data/criteria.json with source, legal status
(enacted rule / guidance / placeholder), and a retrieval date. Nothing here is
species-expert-reviewed; entries flagged 'placeholder' must not be used for
decisions.
"""
from __future__ import annotations
import json
from importlib import resources
from pathlib import Path

WA_MARINE_1DMAX_C = {"extraordinary": 13.0, "excellent": 16.0, "good": 19.0, "fair": 22.0}


def load_criteria(path: str | Path | None = None) -> list[dict]:
    if path is None:
        from ._resources import path as _res
        path = _res("data", "criteria.json")
    return json.loads(Path(path).read_text())["criteria"]


def wa_marine_allowed_increment(t_background_c: float, category: str = "excellent") -> dict:
    """WAC 173-201A-210(1)(c): marine temperature, point sources.

    If background T is cooler than the criterion, the point-source increment at
    the mixing-zone edge may not exceed 12/(T-2), nor raise T above the
    criterion. If background already exceeds the criterion (natural
    conditions), human actions may add no more than 0.3 C.
    Note: the older 8/(T-4) formula belongs to repealed WAC 173-201A-030.
    """
    crit = WA_MARINE_1DMAX_C[category]
    if t_background_c >= crit:
        return {"criterion_c": crit, "allowed_increment_k": 0.3, "basis": "natural exceedance: 0.3 C cap"}
    formula = 12.0 / (t_background_c - 2.0) if t_background_c > 2.0 else float("inf")
    headroom = crit - t_background_c
    if formula <= headroom:
        return {"criterion_c": crit, "allowed_increment_k": formula, "basis": "12/(T-2) at mixing-zone edge"}
    return {"criterion_c": crit, "allowed_increment_k": headroom, "basis": "headroom to criterion"}


F_TO_K = 5.0 / 9.0


def ca_thermal_plan_new_coastal() -> dict:
    """California Thermal Plan, coastal waters, new discharges (SWRCB 1972, as amended):
    discharge no more than 20 F above natural; no increase above 4 F at the
    shoreline, the ocean substrate, or the ocean surface beyond 1,000 ft from
    the discharge system. Verify against the current Plan text before use.
    """
    return {"criterion_c": None, "allowed_increment_k": 4.0 * F_TO_K,
            "max_discharge_delta_k": 20.0 * F_TO_K,
            "basis": "CA Thermal Plan (new coastal): 4 F at surface beyond 1,000 ft"}


def custom_increment(allowed_increment_k: float, label: str = "permit-specific increment") -> dict:
    return {"criterion_c": None, "allowed_increment_k": float(allowed_increment_k), "basis": label}


def temperature_rule(rule: str, t_background_c: float, wa_category: str = "excellent",
                     custom_increment_k: float = 1.0) -> dict:
    if rule == "wa_marine":
        return wa_marine_allowed_increment(t_background_c, wa_category)
    if rule == "ca_new_coastal":
        return ca_thermal_plan_new_coastal()
    if rule == "custom":
        return custom_increment(custom_increment_k)
    raise ValueError(rule)
