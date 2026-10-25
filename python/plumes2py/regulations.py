"""Thermal-discharge rules used for screening.

Each rule carries its source and a ``verify`` flag, following the Aquatic
Guardian convention that enacted law, proposed bills and guidance are never
conflated and that secondary transcriptions are marked. Results are screening
arithmetic, not a compliance determination.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

F_TO_C = 5.0 / 9.0
FT_TO_M = 0.3048

WA_CATEGORIES = {"extraordinary": 13.0, "excellent": 16.0, "good": 19.0, "fair": 22.0}


@dataclass
class Rule:
    id: str
    label: str
    source: str
    status: str                   # "rule" | "placeholder"
    verify: bool = False
    verify_note: str = ""
    notes: str = ""
    params: Dict = field(default_factory=dict)


RULES: Dict[str, Rule] = {
    "wa_marine": Rule(
        "wa_marine", "Washington marine waters", "WAC 173-201A-210(1)(c)", "rule",
        notes="1-DMax criterion by use category; point-source increase at the mixing-zone edge "
              "no more than 12/(T-2) C, limited by headroom to the criterion, and 0.3 C where the "
              "criterion is already exceeded naturally."),
    "ca_new_coastal": Rule(
        "ca_new_coastal", "California coastal waters, new discharge",
        "California Thermal Plan (SWRCB 1972, am. 1975) Sec. 3.B.(3)-(4)", "rule",
        notes="No more than 20 F (11.1 C) above natural at the discharge; no more than 4 F "
              "(2.22 C) at the shoreline, the ocean substrate, or the ocean surface beyond 1,000 ft "
              "(304.8 m) of the discharge, for at least 50 % of any tidal cycle."),
    "ca_enclosed_bay": Rule(
        "ca_enclosed_bay", "California enclosed bay (e.g. San Francisco Bay), new discharge",
        "California Thermal Plan, enclosed bays, new discharges", "rule",
        notes="New thermal waste discharges with a maximum temperature more than 4 F (2.22 C) "
              "above natural are prohibited."),
    "or_marine": Rule(
        "or_marine", "Oregon ocean and bay waters", "OAR 340-041-0028(7)", "rule", verify=True,
        verify_note="Transcribed from a secondary host (oregon.public.law); confirm against the "
                    "Oregon Secretary of State rule text before relying on it.",
        notes="Ocean and bay waters may not be warmed by more than 0.3 C above natural unless a "
              "greater increase would not reasonably be expected to adversely affect fish or other "
              "aquatic life."),
    "custom": Rule(
        "custom", "User-supplied increment", "Permit or standard entered by the user", "placeholder",
        verify=True, verify_note="No jurisdiction-specific rule is applied; the result is arithmetic only.",
        notes="Used for British Columbia (permit-specific under the Environmental Management Act), "
              "EU member states, and anywhere not transcribed."),
}

# Jurisdiction ids match the existing site's data/criteria.json
JURISDICTION_RULE = {
    "us-wa": "wa_marine", "us-ca": "ca_new_coastal", "us-ca-bay": "ca_enclosed_bay",
    "us-or": "or_marine", "us-other": "custom", "ca-bc": "custom", "eu": "custom", "other": "custom",
}


def wa_allowed_increment(t_background: float, category: str = "excellent") -> Dict:
    crit = WA_CATEGORIES[category]
    if t_background >= crit:
        return {"allowed_c": 0.3, "basis": "natural exceedance: 0.3 C cap", "criterion_c": crit}
    inc = 12.0 / (t_background - 2.0) if t_background > 2.0 else float("inf")
    head = crit - t_background
    if head < inc:
        return {"allowed_c": head, "basis": "headroom to criterion", "criterion_c": crit}
    return {"allowed_c": inc, "basis": "12/(T-2) at mixing-zone edge", "criterion_c": crit}


def guess_jurisdiction(lat: float, lon: float) -> str:
    """Rough coastal jurisdiction from coordinates (screening convenience only)."""
    if -170 < lon < -50 and lat > 24:
        if lon < -114 and 32.4 <= lat < 42.0:
            # San Francisco Bay box
            if 37.4 < lat < 38.2 and -122.6 < lon < -122.0:
                return "us-ca-bay"
            return "us-ca"
        if lon < -116 and 42.0 <= lat < 46.25:
            return "us-or"
        if lon < -116 and 46.25 <= lat < 48.4 and lon > -125.0:
            return "us-wa"
        if 48.3 <= lat < 60 and lon < -114 and lon > -140:
            # Salish Sea split at the border is ~49 N east of 123.3 W
            if lat < 49.0 and lon > -123.3:
                return "us-wa"
            return "ca-bc"
        if lat < 49 or lon > -95:
            return "us-other"
    if 34 < lat < 72 and -25 < lon < 35:
        return "eu"
    return "other"


def evaluate(rule_id: str, result: Dict, *, wa_category: str = "excellent",
             custom_increment: Optional[float] = None) -> Dict:
    """Screen a model result (from model.run) against a rule. Uses the
    conservative excess temperature (max of local and effluent-attributable)."""
    rule = RULES[rule_id]
    th = result["metrics"]["thermal"]
    checks: List[Dict] = []
    t_bg = th["ambient_at_port_c"]

    def add(name, value, limit, where, basis=""):
        ok = None if value is None or limit is None else value <= limit + 1e-12
        checks.append({"check": name, "value_c": value, "limit_c": limit, "where": where,
                       "pass": ok, "basis": basis})

    if rule_id == "wa_marine":
        a = wa_allowed_increment(t_bg, wa_category)
        add("Increase at chronic mixing-zone edge", th["dt_chronic_c"], a["allowed_c"],
            "chronic mixing-zone boundary", a["basis"])
    elif rule_id == "ca_new_coastal":
        add("Discharge temperature above natural", th["dt_discharge_c"], 20 * F_TO_C, "end of pipe")
        add("Surface beyond 1,000 ft", th["dt_surface_1000ft_c"], 4 * F_TO_C,
            "ocean surface 304.8 m from the discharge",
            "" if th["surfaced"] else "plume trapped below the surface; surface value is ambient")
        if th["bottom_contact"]:
            add("Ocean substrate", th["dt_end_nearfield_c"], 4 * F_TO_C, "seabed contact")
    elif rule_id == "ca_enclosed_bay":
        add("Discharge temperature above natural", th["dt_discharge_c"], 4 * F_TO_C, "end of pipe")
    elif rule_id == "or_marine":
        add("Warming above natural at mixing-zone edge", th["dt_chronic_c"], 0.3,
            "chronic mixing-zone boundary")
    else:
        add("Increase at chronic mixing-zone edge", th["dt_chronic_c"], custom_increment,
            "chronic mixing-zone boundary", "user-supplied")
    passes = [c["pass"] for c in checks if c["pass"] is not None]
    verdict = ("cannot show compliance" if rule.status == "placeholder" or rule.verify and not passes
               else ("within screening limits" if passes and all(passes) else "exceeds screening limit"))
    if rule.status == "placeholder":
        verdict = "cannot show compliance"
    return {"rule": rule.__dict__, "checks": checks, "verdict": verdict}
