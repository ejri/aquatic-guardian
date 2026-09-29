"""Physics checks against published values. Each test names its source."""
import math
import numpy as np
import pytest
from aquatic_guardian import seawater, cooling, intake, plume, tidal, numerics


@pytest.mark.parametrize("t,s,rho", [(5, 0, 999.96675), (5, 35, 1027.67547),
                                     (25, 0, 997.04796), (25, 35, 1023.34306)])
def test_eos80_check_values(t, s, rho):
    # UNESCO (1981) Technical Papers in Marine Science 36, check values at p = 0
    assert seawater.density_eos80(t, s) == pytest.approx(rho, abs=2e-4)


def test_heated_seawater_is_weakly_buoyant():
    gp = seawater.reduced_gravity(10, 10, 35)
    assert 0.01 < gp < 0.03


def test_cooling_flow_per_mw():
    # Q = P/(rho cp dT): ~24 L/s per MW at dT = 10 K in seawater
    q = cooling.cooling_flow_m3s(1.0, 10.0, 12.0, 32.0)
    assert q * 1000 == pytest.approx(24.4, abs=0.4)


def test_heat_reuse_only_before_discharge():
    assert cooling.heat_to_water_MW(10, 1.2, 1.0, 0.25) == pytest.approx(9.0)


def test_316b_threshold_conversion():
    assert intake.MGD_TO_M3S == pytest.approx(0.043813, rel=1e-4)
    # 2 MGD at 10 K carries ~3.6 MW of heat
    q2 = 2 * intake.MGD_TO_M3S
    heat = q2 * seawater.rho_cp(12, 32) * 10 / 1e6
    assert heat == pytest.approx(3.6, abs=0.1)
    assert intake.cwa316b_screen(q2 * 1.01)["likely_applicable"]
    assert not intake.cwa316b_screen(q2 * 1.01, cooling_fraction=0.2)["likely_applicable"]


def test_regime_boundaries():
    # Tian, Roberts & Daviero (2004)
    assert plume.regime(3, 10) == "line"
    assert plume.regime(10, 10) == "point"
    assert plume.regime(5, 10) == "transitional"
    assert plume.regime(3, 10, n_ports=1) == "point"   # single port is never a line plume


def test_total_flow_substitution_error_is_n_two_thirds():
    """Correction 1: feeding Q_T into a point-plume law under-predicts dilution by N^(2/3)."""
    n, qt, gp, z = 12, 1.2, 0.02, 25.0
    d = plume.Diffuser(qt, n, 0.3, 30.0)
    f_port = plume.fluxes(d, gp)
    s_true = plume.dilution_point(f_port, z)
    wrong = {"Q": qt, "B": gp * qt}
    s_wrong = plume.dilution_point(wrong, z)
    assert s_true / s_wrong == pytest.approx(plume.total_flow_error_factor(n), rel=1e-12)


def test_line_plume_uses_flux_per_length():
    d = plume.Diffuser(1.0, 20, 0.2, 2.0)
    f = plume.fluxes(d, 0.02)
    assert f["q"] == pytest.approx(1.0 / 40.0)
    assert f["b"] == pytest.approx(0.02 / 40.0)


def test_tidal_excursion():
    # Correction 2: 10.7 km per half-cycle implies ~0.75 m/s peak current
    assert tidal.implied_peak_current(10_700) == pytest.approx(0.752, abs=0.005)
    assert tidal.excursion_half_cycle(0.3) == pytest.approx(4270, abs=10)


def test_okubo_values():
    assert numerics.okubo_kh(1000) == pytest.approx(0.58, abs=0.01)
    assert numerics.okubo_kh(25) == pytest.approx(0.0083, abs=0.0003)
    # 2.1 m2/s numerical diffusion exceeds physical mixing below ~3 km
    assert numerics.okubo_crossover_scale(2.1) == pytest.approx(3070, rel=0.03)


def _pulse(nx=800, dx=25.0, width=6):
    x = np.arange(nx) * dx
    c = np.exp(-0.5 * ((np.arange(nx) - nx // 4) / width) ** 2)
    return x, c


def test_upwind_numerical_diffusion_matches_formula():
    """Correction 3, measured: variance growth of a pulse under pure advection."""
    x, c0 = _pulse()
    u, dx, dt, steps = 0.3, 25.0, 25.0, 600       # C = 0.3
    c1 = numerics.advect_diffuse_1d(c0, u, 0.0, dx, dt, steps, "upwind")
    k_eff = numerics.effective_diffusivity(c0, c1, x, dt * steps)
    assert k_eff == pytest.approx(numerics.k_num_upwind(u, dx, dt), rel=0.05)


def test_tvd_scheme_removes_most_numerical_diffusion_and_conserves_mass():
    x, c0 = _pulse()
    u, dx, dt, steps = 0.3, 25.0, 25.0, 600
    up = numerics.advect_diffuse_1d(c0, u, 0.0, dx, dt, steps, "upwind")
    tvd = numerics.advect_diffuse_1d(c0, u, 0.0, dx, dt, steps, "tvd")
    k_up = numerics.effective_diffusivity(c0, up, x, dt * steps)
    k_tvd = numerics.effective_diffusivity(c0, tvd, x, dt * steps)
    assert k_tvd < 0.2 * k_up
    assert tvd.sum() == pytest.approx(c0.sum(), rel=1e-10)
    assert tvd.min() > -1e-10          # monotone: no negative concentrations


def test_physical_diffusion_recovered_by_tvd():
    x, c0 = _pulse()
    u, dx, dt, steps, k = 0.3, 25.0, 25.0, 600, 1.0
    tvd = numerics.advect_diffuse_1d(c0, u, k, dx, dt, steps, "tvd")
    k_eff = numerics.effective_diffusivity(c0, tvd, x, dt * steps)
    assert k_eff == pytest.approx(k, rel=0.2)
