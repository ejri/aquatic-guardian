import json
import pytest
from aquatic_guardian import screening, disclosure, handoff


def test_disclosure_from_screening_is_schema_valid():
    r = screening.screen()
    rec = disclosure.from_screening(r, "demo-1", ["US-WA"], "nearshore_submerged",
                                    ("2026-01-01", "2026-12-31"))
    assert disclosure.validate(rec) == []


def test_disclosure_rejects_bad_cooling_type():
    r = screening.screen()
    rec = disclosure.from_screening(r, "demo-1", ["US-WA"], "nearshore_submerged",
                                    ("2026-01-01", "2026-12-31"))
    rec["facility"]["cooling_type"] = "magic"
    assert disclosure.validate(rec)


def test_handoff_round_trip(tmp_path):
    rec = handoff.make("thermal_tidal", "summer-p90", ["slack water design condition"],
                       ["species thermal thresholds"], loop_inlet_temperature_c=14.2,
                       receiving_water={"ambient_t_c": 12.0, "salinity_psu": 30, "ph": 8.0,
                                        "do_mg_l": 8.9, "unionised_ammonia_fraction": 0.017})
    p = handoff.write(rec, tmp_path / "thermal.json")
    assert handoff.read(p)["loop_inlet_temperature_c"] == 14.2


def test_handoff_rejects_missing_placeholders():
    with pytest.raises(ValueError):
        handoff.write({"handoff_version": "0.1.0", "producer": "thermal_tidal"}, "/tmp/x.json")


def test_screening_flags_known_cases():
    hot = screening.screen({"delta_t_k": 15, "n_ports": 1, "port_diameter_m": 0.5, "depth_m": 8,
                            "t_ambient_c": 15.5})
    ids = {f["id"] for f in hot["flags"]}
    assert "temperature" in ids and "intake_316b" in ids
    closed = screening.screen({"cooling_type": "closed_loop_air"})
    assert closed["flow_m3s"] == 0 and closed["near_field"] is None
    assert not closed["intake_316b"]["likely_applicable"]
