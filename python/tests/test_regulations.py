import pytest
from plumes2py.regulations import wa_allowed_increment, guess_jurisdiction, F_TO_C, evaluate
from plumes2py.datacenter import DataCentreDesign, build
from plumes2py import run

@pytest.mark.parametrize("t,allowed,basis", [(10, 1.5, "12/(T-2)"), (15, 0.923, "12/(T-2)"),
                                             (15.5, 0.5, "headroom"), (16.5, 0.3, "natural")])
def test_wa_increment_matches_site_margin_table(t, allowed, basis):
    a = wa_allowed_increment(t, "excellent")
    assert a["allowed_c"] == pytest.approx(allowed, abs=1e-3) and basis in a["basis"]

def test_ca_units():
    assert 4 * F_TO_C == pytest.approx(2.2222, abs=1e-4)
    assert 20 * F_TO_C == pytest.approx(11.111, abs=1e-3)

@pytest.mark.parametrize("lat,lon,j", [(48.4, -123.4, "ca-bc"), (47.6, -122.4, "us-wa"),
                                       (36.6, -121.9, "us-ca"), (37.8, -122.4, "us-ca-bay"),
                                       (44.6, -124.1, "us-or"), (25.8, -80.2, "us-other"),
                                       (16.1, -86.9, "other")])
def test_jurisdiction_guess(lat, lon, j):
    assert guess_jurisdiction(lat, lon) == j

def test_placeholder_rule_never_claims_compliance():
    res = run(build(DataCentreDesign(), sst_c=10, salinity=30, current_ms=0.2))
    assert evaluate("custom", res, custom_increment=5.0)["verdict"] == "cannot show compliance"
