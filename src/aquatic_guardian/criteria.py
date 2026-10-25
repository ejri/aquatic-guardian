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


def _data(path: str | Path | None = None) -> dict:
    if path is None:
        from ._resources import path as _res
        path = _res("data", "criteria.json")
    return json.loads(Path(path).read_text())


def load_criteria(path: str | Path | None = None) -> list[dict]:
    return _data(path)["criteria"]


def load_jurisdictions(path: str | Path | None = None) -> dict:
    """Jurisdiction records from data/criteria.json, keyed by id.

    Each record names the temperature rule that applies, its legal status and
    source, and which intake rule applies. Jurisdictions whose numeric rule is
    permit-specific or not yet transcribed map to the 'custom' temperature rule
    with `verify: true`; they never assert a numeric threshold of their own.
    Mirrored in app/engine.js (JURISDICTIONS); tests/test_engine_parity.py
    checks the two copies against this file.
    """
    return {j["id"]: j for j in _data(path)["jurisdictions"]}


def jurisdiction(jurisdiction_id: str, path: str | Path | None = None) -> dict:
    """Resolve one jurisdiction, with its intake rule's status and source attached."""
    js = load_jurisdictions(path)
    if jurisdiction_id not in js:
        raise ValueError(jurisdiction_id)
    j = js[jurisdiction_id]
    intake = _data(path)["intake_rules"][j["intake_rule"]]
    return {"id": j["id"], "label": j["label"], "country": j["country"],
            "temperature_rule": j["temperature_rule"],
            "temperature_status": j["temperature_status"],
            "temperature_source": j["temperature_source"],
            "status_as_of": j["status_as_of"], "note": j["note"],
            "verify": j["verify"], "verify_note": j.get("verify_note"),
            "intake_rule": j["intake_rule"], "intake_label": intake["label"],
            "intake_status": intake["status"], "intake_source": intake["source"]}


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
    """California Thermal Plan, coastal waters, new discharges.

    Source: SWRCB Water Quality Control Plan for Control of Temperature in the
    Coastal and Interstate Waters and Enclosed Bays and Estuaries of California,
    Specific Water Quality Objectives §3.B.(3)–(4). Exact text:
    data/checks/ca_thermal_plan.md. Discharge ≤ 20 °F above natural; receiving-
    water rise ≤ 4 °F at shoreline, ocean substrate, or ocean surface beyond
    1,000 ft from the discharge system.
    """
    return {"criterion_c": None, "allowed_increment_k": 4.0 * F_TO_K,
            "max_discharge_delta_k": 20.0 * F_TO_K,
            "basis": "CA Thermal Plan (new coastal): 4 F at surface beyond 1,000 ft"}


def custom_increment(allowed_increment_k: float, label: str = "permit-specific increment") -> dict:
    return {"criterion_c": None, "allowed_increment_k": float(allowed_increment_k), "basis": label}


def or_marine_increment() -> dict:
    """OAR 340-041-0028(7): ocean and bay waters, 0.3 °C above natural.

    Transcribed from a secondary host (oregon.public.law); confirm against the
    Oregon Secretary of State rule text before relying on it (verify=True on
    the jurisdiction row in data/criteria.json).
    """
    return {
        "criterion_c": None,
        "allowed_increment_k": 0.3,
        "basis": "OAR 340-041-0028(7): 0.3 C above natural (verify)",
    }


def temperature_rule(rule: str, t_background_c: float, wa_category: str = "excellent",
                     custom_increment_k: float = 1.0) -> dict:
    if rule == "wa_marine":
        return wa_marine_allowed_increment(t_background_c, wa_category)
    if rule == "ca_new_coastal":
        return ca_thermal_plan_new_coastal()
    if rule == "or_marine":
        return or_marine_increment()
    if rule == "custom":
        return custom_increment(custom_increment_k)
    raise ValueError(rule)
