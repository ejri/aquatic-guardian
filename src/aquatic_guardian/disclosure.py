"""Build and validate Aquatic Disclosure Records (schemas/aquatic-disclosure.schema.json)."""
from __future__ import annotations
import json
from pathlib import Path

from ._resources import path as _res
SCHEMA = _res("schemas", "aquatic-disclosure.schema.json")


def validate(record: dict) -> list[str]:
    try:
        import jsonschema
    except ImportError:
        req = json.loads(SCHEMA.read_text())["required"]
        return [f"missing {k}" for k in req if k not in record]
    v = jsonschema.Draft202012Validator(json.loads(SCHEMA.read_text()))
    return [f"{'/'.join(map(str, e.path))}: {e.message}" for e in v.iter_errors(record)]


def from_screening(result: dict, facility_id: str, jurisdictions: list[str], siting: str,
                   period: tuple[str, str], hours: float = 8760.0) -> dict:
    """Pre-fill a disclosure record from a screening result (design values, not measurements)."""
    from . import __version__
    inp = result["inputs"]
    rec = {
        "schema_version": "0.1.0",
        "facility": {"id": facility_id, "jurisdictions": jurisdictions, "siting": siting,
                     "it_capacity_mw": inp["it_load_mw"], "pue": inp["pue"],
                     "cooling_type": inp["cooling_type"],
                     "location": {"water_type": inp["water_type"]}},
        "reporting_period": {"start": period[0], "end": period[1]},
        "thermal": {"heat_rejected_mwh": result["heat_rejected_mw"] * hours,
                    "heat_to_water_mwh": result["heat_to_water_mw"] * hours,
                    "heat_reused_mwh": result["heat_reused_mw"] * hours,
                    "erf": inp["reuse_fraction"],
                    "discharge_delta_t_k": {"max": inp["delta_t_k"]},
                    "mixing_zone": {"criterion_c": result["temperature_rule"]["criterion_c"],
                                    "criterion_basis": result["temperature_rule"]["basis"],
                                    "model": f"aquatic_guardian {__version__} screening"}},
        "intake": {"design_intake_m3s": result["flow_m3s"], "cooling_fraction": inp["cooling_fraction"]},
        "provenance": {"prepared_by": "UNSET", "method": "design-value screening",
                       "tool_versions": [f"aquatic_guardian {__version__}"],
                       "independently_verified": False, "screening_only": True},
    }
    return rec
