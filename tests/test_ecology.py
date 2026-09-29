"""Ecology, monitoring and aquaculture checks, including the confounds the
notebooks were rebuilt to expose."""
import math
import numpy as np
import pytest
from scipy.special import expit
from aquatic_guardian import occupancy, imaging, tracking, bioenergetics, sentience


def _simulate(n_sites, n_surveys, psi, a0, a1, turb_mean, rng):
    z = rng.random(n_sites) < psi
    turb = rng.normal(turb_mean, 0.3, (n_sites, n_surveys))
    p = expit(a0 + a1 * turb)
    y = (rng.random((n_sites, n_surveys)) < p) & z[:, None]
    return y.astype(float), turb


def test_turbidity_masquerades_as_impact_without_detection_model():
    """Same true occupancy in both zones; the impact zone is only more turbid.

    Correct design: one model over all sites, zone as an occupancy covariate,
    turbidity as a detection covariate shared across zones (MacKenzie et al. 2006).
    Fitting each zone separately with low detection gives imprecise psi; that
    imprecision is real and is why the pooled model and its CI are reported.
    """
    rng = np.random.default_rng(7)
    y_ref, t_ref = _simulate(300, 4, 0.6, 1.0, -1.5, 0.0, rng)
    y_imp, t_imp = _simulate(300, 4, 0.6, 1.0, -1.5, 1.5, rng)
    naive_gap = occupancy.fit(y_ref)["naive_occupancy"] - occupancy.fit(y_imp)["naive_occupancy"]
    assert naive_gap > 0.1                       # naive analysis reports an "impact"

    y = np.vstack([y_ref, y_imp])
    turb = np.vstack([t_ref, t_imp])
    zone = np.r_[np.zeros(300), np.ones(300)]
    fit = occupancy.fit(y, psi_covariates=zone, detection_covariates=turb)
    b_zone, se_zone = fit["beta_psi"][1], fit["se"][1]
    assert abs(b_zone) < 1.96 * se_zone          # no detectable zone effect on occupancy
    assert fit["alpha_p"][1] == pytest.approx(-1.5, abs=0.4)   # turbidity recovered in detection
    assert expit(fit["beta_psi"][0]) == pytest.approx(0.6, abs=0.08)


def test_image_inversion_round_trip_and_flagging():
    J = np.array([0.2, 0.5, 0.8])
    z = np.array([1.0, 3.0, 12.0])
    I = imaging.forward(J, z, beta_d=0.3, beta_b=0.25, b_inf=0.4)
    r = imaging.invert(I, z, 0.3, 0.25, 0.4)
    assert r["recoverable"].tolist() == [True, True, False]   # t(12 m) = 0.027 < 0.1
    np.testing.assert_allclose(r["J"][:2], J[:2], rtol=1e-12)
    assert r["noise_gain"][2] == pytest.approx(math.exp(0.3 * 12))


def test_null_polarisation():
    rng = np.random.default_rng(1)
    n, trials = 12, 20000
    th = rng.uniform(0, 2 * np.pi, (trials, n))
    P = np.hypot(np.cos(th).mean(1), np.sin(th).mean(1))
    nb = tracking.null_polarisation(n)
    assert np.sqrt((P ** 2).mean()) == pytest.approx(nb["rms"], rel=0.02)
    assert P.mean() == pytest.approx(nb["mean"], rel=0.05)


def test_fd_velocity_noise():
    rng = np.random.default_rng(2)
    sx, dt = 0.004, 1 / 30
    x = rng.normal(0, sx, 200000)
    v = np.diff(x) / dt
    assert v.std() == pytest.approx(tracking.fd_velocity_noise(sx, dt), rel=0.02)


def test_yield_optimum_below_growth_optimum_with_placeholders():
    sp = bioenergetics.SpeciesParams()
    temps = np.arange(8.0, 21.0, 0.25)
    y = [bioenergetics.yield_index(t, 30, 7.6, 60, 100, sp) for t in temps]
    t_best = temps[int(np.argmax(y))]
    assert t_best < sp.t_opt
    cap_warm = bioenergetics.carrying_capacity_kg(18, 30, 7.6, 60, 100, sp)
    assert cap_warm["binding"] in {"do", "ammonia"}


def test_tgc_growth_monotone_and_capped():
    sp = bioenergetics.SpeciesParams()
    w_opt = bioenergetics.tgc_growth(100, sp.t_opt, 30, sp)
    w_hot = bioenergetics.tgc_growth(100, sp.t_opt + 4, 30, sp)
    assert w_opt > w_hot > 100
    assert bioenergetics.tgc_growth(100, sp.t_max + 1, 30, sp) == pytest.approx(100)


def test_sentience_table_never_merges_life_stages():
    rows = sentience.impact_table([
        {"taxon": "fish", "life_stage": "larva", "pathway": "entrainment", "n": 1000},
        {"taxon": "fish", "life_stage": "juvenile", "pathway": "impingement", "n": 40},
        {"taxon": "decapod", "life_stage": "adult", "pathway": "impingement", "n": 5},
        {"taxon": "fish", "life_stage": "larva", "pathway": "entrainment", "n": 200},
    ])
    assert len(rows) == 3
    assert {r["tier"] for r in rows} == {1}
    assert [r["n"] for r in rows if r["life_stage"] == "larva"] == [1200]
