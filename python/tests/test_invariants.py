import copy
import math
import pytest
from plumes2py import (Ambient, AmbientRow, Diffuser, Effluent, MixingZone, Scenario, Settings,
                       reference_example, run, run_nearfield)
from plumes2py.datacenter import DataCentreDesign, build, heat_to_water_mw

def simple(n=1, q=0.1, spacing=5.0, speed=0.1, t0=25.0, s0=31.0):
    amb = Ambient([AmbientRow(depth=0, speed=speed, salinity=31, temperature=12, far_speed=speed),
                   AmbientRow(depth=30, speed=speed, salinity=31, temperature=12, far_speed=speed)])
    return Scenario(Diffuser(0.2, 0.5, 15, 0, n_ports=n, spacing=spacing, port_depth=20),
                    Effluent(q, salinity=s0, temperature=t0, concentration=100),
                    amb, MixingZone(10, 100), Settings())

def test_per_port_flow_not_total():
    """N widely spaced ports carrying Q behave like one port carrying Q/N (correction 1)."""
    many = run_nearfield(simple(n=8, q=0.8, spacing=1e6)).end
    one = run_nearfield(simple(n=1, q=0.1)).end
    assert many.dilution == pytest.approx(one.dilution, rel=1e-9)

def test_merged_cannot_outdilute_isolated():
    for spacing in (0.5, 1, 2, 4, 8):
        merged = run_nearfield(simple(n=10, q=1.0, spacing=spacing)).end.dilution
        iso = run_nearfield(simple(n=10, q=1.0, spacing=1e6)).end.dilution
        assert merged <= iso * 1.02

def test_tracer_conservation_zero_background():
    r = run_nearfield(simple())
    for s in r.steps[::20]:
        assert s.concentration * s.dilution == pytest.approx(100.0, rel=1e-6)

def test_step_size_convergence():
    sc = reference_example()
    a = run_nearfield(sc).end.dilution
    sc.settings.step_mass_fraction = 0.005
    b = run_nearfield(sc).end.dilution
    assert abs(b / a - 1) < 0.02

def test_heat_budget_and_salinity_for_data_centre():
    d = DataCentreDesign(it_mw=10, pue=1.2, delta_t_k=10)
    sc = build(d, sst_c=12, salinity=31, current_ms=0.1)
    assert sc.effluent.salinity == 31                      # not 0 psu
    res = run(sc)
    assert res["metrics"]["heat"]["heat_to_water_mw"] == pytest.approx(heat_to_water_mw(d), rel=0.01)
    assert res["metrics"]["heat"]["flow_m3s"] == pytest.approx(12e6 / (1023 * 3990 * 10), rel=0.02)

def test_buoyant_warm_plume_rises_and_dilutes_monotonically():
    r = run_nearfield(simple(t0=30))
    dils = [s.dilution for s in r.steps]
    assert all(b >= a - 1e-12 for a, b in zip(dils, dils[1:]))
    assert r.end.depth < 20

def test_negatively_buoyant_brine_sinks():
    sc = simple(t0=12, s0=60)
    sc.diffuser.vertical_angle = 60
    r = run_nearfield(sc)
    assert r.termination in ("bottom", "max fall", "second trap level", "trap level")

def test_slack_water_caveat():
    res = run(simple(speed=0.01))
    assert any("slack" in c for c in res["caveats"])

def test_validation_errors():
    sc = simple(); sc.diffuser.port_depth = 0
    with pytest.raises(ValueError):
        run_nearfield(sc)

def test_coflowing_ports_give_monotonic_horizontal_distance():
    # regression: ports aimed upstream folded back, so the far field started behind the near field
    from plumes2py.datacenter import DataCentreDesign, build
    sc = build(DataCentreDesign(it_mw=120, port_depth=13), sst_c=29.4, salinity=36, current_ms=0.25)
    r = run_nearfield(sc)
    d = [s.distance for s in r.steps]
    assert all(b >= a - 1e-9 for a, b in zip(d, d[1:]))
