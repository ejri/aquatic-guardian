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
