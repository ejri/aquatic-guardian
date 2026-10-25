import pytest
from plumes2py.seawater import density, oxygen_saturation_mg_l, heat_capacity

@pytest.mark.parametrize("S,T,rho", [(0, 5, 999.96675), (35, 5, 1027.67547), (35, 25, 1023.34306)])
def test_unesco_check_values(S, T, rho):
    assert density(S, T) == pytest.approx(rho, abs=2e-4)

def test_oxygen_saturation():
    assert oxygen_saturation_mg_l(0, 20) == pytest.approx(9.09, abs=0.03)
    assert 7.2 <= oxygen_saturation_mg_l(35, 20) <= 7.5
    assert 8.8 <= oxygen_saturation_mg_l(35, 10) <= 9.2

def test_heat_capacity_order():
    assert 3950 < heat_capacity(35, 15) < 4010
