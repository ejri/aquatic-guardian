"""Brooks far field against the EPA manual (EPA/600/B-24/339)."""
import math
import pytest
from plumes2py.brooks import run_farfield, width_ratio, centerline_ratio, beta

# Manual Fig. 14 (independent far field): D0=100, w0=50 m, x0=0.001 m, u=0.05, alpha=3e-4, 4/3 law
FIG14 = [(8.001, 100.000, 52.137), (16.001, 100.004, 54.303), (40.001, 101.326, 60.977),
         (104.000, 119.816, 79.985), (200.000, 162.627, 111.544), (224.000, 174.550, 119.965)]

@pytest.mark.parametrize("dist,dil,width", FIG14)
def test_independent_farfield_matches_manual_fig14(dist, dil, width):
    r = run_farfield(0.001, 100.0, 50.0, 0.05, alpha=0.0003, interval=8.0, stop_distance=230)
    row = min(r.rows, key=lambda q: abs(q.distance - dist))
    assert row.dilution == pytest.approx(dil, abs=0.006)
    assert row.width == pytest.approx(width, abs=0.006)

# Manual Fig. 12 far field: start 7.32 m, D0 169.754, w0 109.59 m. The origin convention differs
# between PLUMES2.0 releases (the manual's table implies ~7.1-7.3 m, the shipped executable's
# ModelResults_TxtOutputs.dat ~4.4 m), so this is checked to 0.1 % (see VALIDATION.md).
FIG12 = [(10.0, 169.754, 110.556), (50.0, 169.999, 124.732), (100.0, 176.666, 143.099)]

@pytest.mark.parametrize("dist,dil,width", FIG12)
def test_integrated_farfield_matches_manual_fig12(dist, dil, width):
    r = run_farfield(7.32, 169.754, 109.59, 0.05, alpha=0.0003, interval=10, stop_distance=102)
    row = min(r.rows, key=lambda q: abs(q.distance - dist))
    assert row.dilution == pytest.approx(dil, rel=1e-3)
    assert row.width == pytest.approx(width, rel=1e-3)

def test_case2_uses_derivation_not_manual_eq11_typo():
    # L dL/dx = 12 eps0 L/(u w0)  =>  L/w0 = 1 + beta x / w0  (manual eq. 11 says 1 + 2 beta x/w0)
    assert width_ratio("linear", 0.5) == pytest.approx(1.5)
    # concentration law consistent with the width law in every case
    for case in ("constant", "linear", "four_thirds"):
        bx = 0.7
        assert centerline_ratio(case, bx) == pytest.approx(math.erf(math.sqrt(1.5 / (width_ratio(case, bx) ** 2 - 1))))

def test_exact_mixing_zone_row():
    r = run_farfield(7.32, 169.754, 109.59, 0.05, interval=10, chronic=102.0, acute=10.2)
    assert r.at_chronic is not None and r.at_chronic.distance == 102.0
    assert r.at_acute is not None and r.at_acute.distance == 10.2
    # manual: "approximately 177:1 with interpolation"
    assert r.at_chronic.dilution == pytest.approx(177.0, abs=0.6)

def test_decay_and_background():
    r = run_farfield(0.0, 10.0, 20.0, 0.1, decay_per_day=1.0, start_conc=10.0, background=1.0,
                     interval=100, stop_distance=1000)
    last = r.rows[-1]
    t = last.travel / 0.1
    assert last.concentration == pytest.approx(1 + 9 / last.farfield_factor * math.exp(-t / 86400), rel=1e-9)

def test_no_duplicate_rows_when_boundary_falls_on_interval():
    # regression: an acute boundary at 30 m with a 10 m interval produced two rows at 30 m
    r = run_farfield(26.4, 28.0, 30.0, 0.25, acute=30.0, chronic=300.0, interval=10, stop_distance=600)
    d = [q.distance for q in r.rows]
    assert len(d) == len(set(d))
    assert r.at_acute.note == "acute mixing zone" and r.at_chronic.note == "chronic mixing zone"
