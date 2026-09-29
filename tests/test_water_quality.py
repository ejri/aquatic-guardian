import pytest
from aquatic_guardian import water_quality as wq, criteria


def test_do_freshwater_20c():
    # Benson & Krause (1984) / USGS tables: 9.09 mg/L at 20 C, S = 0
    assert wq.do_saturation_mg_l(20, 0) == pytest.approx(9.09, abs=0.02)


def test_do_freshwater_0c():
    assert wq.do_saturation_mg_l(0, 0) == pytest.approx(14.62, abs=0.05)


def test_do_seawater_ranges():
    assert 7.2 < wq.do_saturation_mg_l(20, 35) < 7.5
    assert 8.8 < wq.do_saturation_mg_l(10, 35) < 9.2


def test_do_falls_with_temperature_and_salinity():
    assert wq.do_saturation_mg_l(18, 30) < wq.do_saturation_mg_l(10, 30)
    assert wq.do_saturation_mg_l(10, 35) < wq.do_saturation_mg_l(10, 0)


@pytest.mark.parametrize("t,ph,pct", [(20, 7.0, 0.397), (25, 8.0, 5.38)])
def test_emerson_table(t, ph, pct):
    # Emerson et al. (1975) Table 1
    assert 100 * wq.unionised_fraction(t, ph) == pytest.approx(pct, rel=0.02)


def test_salinity_lowers_unionised_fraction():
    fresh = wq.unionised_fraction(25, 8.0, 0)
    sea = wq.unionised_fraction(25, 8.0, 34)
    assert sea < fresh
    assert 0.035 < sea < 0.05   # Bower & Bidwell (1978) order of magnitude; compare to table before citing


def test_epa2013_criteria_at_reference_conditions():
    # EPA 822-R-13-001: CMC 17 mg TAN/L, CCC 1.9 mg TAN/L at pH 7, 20 C
    assert round(wq.epa2013_cmc_mg_tan_l(7.0, 20.0)) == 17
    assert round(wq.epa2013_ccc_mg_tan_l(7.0, 20.0), 1) == 1.9


def test_wa_increment_rule():
    r = criteria.wa_marine_allowed_increment(12.0, "excellent")
    assert r["allowed_increment_k"] == pytest.approx(1.2)
    r = criteria.wa_marine_allowed_increment(15.5, "excellent")
    assert r["allowed_increment_k"] == pytest.approx(0.5)      # headroom binds
    r = criteria.wa_marine_allowed_increment(16.5, "excellent")
    assert r["allowed_increment_k"] == pytest.approx(0.3)      # natural exceedance


def test_ca_thermal_plan_units():
    r = criteria.ca_thermal_plan_new_coastal()
    assert r["allowed_increment_k"] == pytest.approx(2.222, abs=1e-3)
    assert r["max_discharge_delta_k"] == pytest.approx(11.11, abs=1e-2)


def test_criteria_file_has_provenance():
    for c in criteria.load_criteria():
        assert c["status"] in {"rule", "guidance", "placeholder"}
        assert c["source"]


def test_jurisdictions_never_assert_an_untranscribed_rule():
    """A jurisdiction may only name a numeric temperature rule if it cites a source.

    Where the numeric value is permit-specific or not yet transcribed, the entry
    must fall back to the 'custom' rule (user-supplied increment), be marked
    'placeholder', and carry verify=true with a note saying what is missing.
    """
    for jid, j in criteria.load_jurisdictions().items():
        assert j["temperature_status"] in {"rule", "guidance", "placeholder"}, jid
        if j["temperature_status"] == "placeholder":
            assert j["temperature_rule"] == "custom", jid
            assert j["verify"] is True and j.get("verify_note"), jid
            assert j["temperature_source"] is None, jid
        else:
            assert j["temperature_source"], jid
            assert j["temperature_rule"] in {"wa_marine", "ca_new_coastal"}, jid
        assert j["note"] and j["status_as_of"], jid


def test_intake_rule_only_cites_law_that_applies_there():
    """§316(b) is US-only and the Fisheries Act is Canada-only."""
    for jid, j in criteria.load_jurisdictions().items():
        r = criteria.jurisdiction(jid)
        assert r["intake_rule"] in {"us_cwa_316b", "ca_fisheries_act", "none"}, jid
        if r["intake_rule"] == "us_cwa_316b":
            assert r["country"] == "US", jid
        if r["intake_rule"] == "ca_fisheries_act":
            assert r["country"] == "CA", jid
        if r["country"] not in {"US", "CA"}:
            assert r["intake_rule"] == "none", jid


@pytest.mark.parametrize("jid", sorted(criteria.load_jurisdictions()))
def test_screening_flags_only_cite_the_selected_jurisdictions_law(jid):
    from aquatic_guardian import screening
    # A large estuarine facility in a weak current: both US intake tests are tripped,
    # so the flags differ only because of the jurisdiction.
    r = screening.screen({"jurisdiction": jid, "it_load_mw": 600.0, "water_type": "estuarine",
                          "u_peak_ms": 0.05, "depth_m": 5.0})
    assert r["intake_316b"]["likely_applicable"]
    assert not r["tidal_volume_check"]["within_1_percent"]
    ids = {f["id"] for f in r["flags"]}
    text = " ".join(f["text"] for f in r["flags"])
    us = criteria.jurisdiction(jid)["intake_rule"] == "us_cwa_316b"
    assert ("intake_316b" in ids) == us
    assert ("tidal_volume" in ids) == us
    assert ("316(b)" in text) == us
    assert ("125.84" in text) == us
    assert ("fisheries_act" in ids) == (criteria.jurisdiction(jid)["intake_rule"] == "ca_fisheries_act")
