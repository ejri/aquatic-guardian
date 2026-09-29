"""Run the key experiments of the three Colab notebooks with the verified library
and write data/notebook_results.json for the website's Lab.

Everything here is recomputed from src/aquatic_guardian with fixed seeds, so the
numbers on the site are reproducible with `python app/notebook_results.py`.
Findings reported from the Colab runs themselves (not recomputed here) are kept
in a separate `reported` block and labelled as such on the site.
"""
from __future__ import annotations
import datetime as dt
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.special import expit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import aquatic_guardian as ag  # noqa: E402
from aquatic_guardian import (screening, plume, tidal, numerics, criteria, occupancy,  # noqa: E402
                              imaging, tracking, bioenergetics, water_quality, handoff)

R = lambda x, n=4: float(round(float(x), n))  # noqa: E731


def thermal() -> dict:
    base = screening.screen()
    f = base["inputs"]
    d = plume.Diffuser(base["flow_m3s"], f["n_ports"], f["port_diameter_m"], 12.0)
    gp = base["near_field"]["g_prime"]
    port = plume.fluxes(d, gp)
    s_port = plume.dilution_point(port, f["depth_m"])
    s_total = plume.dilution_point({"Q": d.total_flow_m3s, "B": gp * d.total_flow_m3s}, f["depth_m"])
    per_port = {"n_ports": d.n_ports, "spacing_m": 12.0, "depth_m": f["depth_m"],
                "dilution_per_port": R(s_port, 2), "dilution_total_flow_bug": R(s_total, 2),
                "factor": R(s_port / s_total, 3), "theory_factor": R(plume.total_flow_error_factor(d.n_ports), 3)}

    exc = [{"u_ms": u, "km": R(tidal.excursion_half_cycle(u) / 1000, 2)} for u in (0.1, 0.2, 0.3, 0.5, 0.75, 1.0)]

    nx, dx, u, dts, steps = 800, 25.0, 0.3, 25.0, 600
    x = np.arange(nx) * dx
    c0 = np.exp(-0.5 * ((np.arange(nx) - nx // 4) / 6) ** 2)
    up = numerics.advect_diffuse_1d(c0, u, 0.0, dx, dts, steps, "upwind")
    tv = numerics.advect_diffuse_1d(c0, u, 0.0, dx, dts, steps, "tvd")
    shift = int(round(u * dts * steps / dx))
    exact = np.roll(c0, shift)
    win = slice(nx // 4 + shift - 60, nx // 4 + shift + 60)
    pulse = {"x_km": [R(v / 1000, 3) for v in x[win]], "initial_shifted": [R(v) for v in exact[win]],
             "upwind": [R(v) for v in up[win]], "tvd": [R(v) for v in tv[win]],
             "k_eff_upwind": R(numerics.effective_diffusivity(c0, up, x, dts * steps), 3),
             "k_eff_tvd": R(numerics.effective_diffusivity(c0, tv, x, dts * steps), 3),
             "k_formula": R(numerics.k_num_upwind(u, dx, dts), 3), "u_ms": u, "dx_m": dx, "dt_s": dts,
             "hours": R(dts * steps / 3600, 2)}
    scales = np.logspace(1, 4.3, 40)
    kcurve = {"scale_m": [R(s, 1) for s in scales], "okubo": [R(numerics.okubo_kh(s), 5) for s in scales],
              "k_num": {str(int(g)): R(numerics.k_num_upwind(0.3, g, 10.0), 3) for g in (10, 25, 50, 100)},
              "crossover_m_for_2_1": R(numerics.okubo_crossover_scale(2.1), 0)}

    margin = []
    for t in np.arange(6.0, 18.01, 0.5):
        r = screening.screen({"t_ambient_c": float(t)})
        margin.append({"t_c": R(t, 1), "allowed_k": R(r["temperature_rule"]["allowed_increment_k"], 3),
                       "near_field_k": R(r["near_field"]["delta_t_near_field_k"], 3),
                       "basis": r["temperature_rule"]["basis"],
                       "do_drop_pct": R(100 * r["water_quality"]["do_sat_drop_frac"], 1)})

    rec = handoff.make("thermal_tidal", "default-screening", ["slack-water near field", "WA excellent marine"],
                       ["species thermal thresholds", "site tidal current"],
                       loop_inlet_temperature_c=R(f["t_ambient_c"] + f["delta_t_k"], 2),
                       receiving_water={"ambient_t_c": f["t_ambient_c"], "salinity_psu": f["s_psu"], "ph": f["ph"],
                                        "do_mg_l": R(base["water_quality"]["do_sat_ambient_mg_l"], 2),
                                        "unionised_ammonia_fraction": R(base["water_quality"]["nh3_frac_ambient"], 4)},
                       plume={"delta_t_mixing_zone_edge_k": R(base["near_field"]["delta_t_near_field_k"], 3),
                              "regime": base["near_field"]["regime"],
                              "near_field_dilution": R(base["near_field"]["dilution"], 2),
                              "design_condition": "slack water, ambient 12 C",
                              "grid": {"dx_m": 25, "k_num_m2s": R(base["numerics"]["k_num_upwind_m2s"], 3),
                                       "k_phys_m2s": R(numerics.okubo_kh(1000), 3), "scheme": "tvd"}})
    rec["created"] = "2026-09-29T00:00:00+00:00"
    return {"per_port": per_port, "excursion": exc, "pulse": pulse, "k_curve": kcurve,
            "margin": margin, "handoff_example": rec}


def monitoring() -> dict:
    shifts, declines, reps, n_sites, n_surv = (0.0, 0.5, 1.0, 1.5, 2.0), (0.0, 0.1, 0.2, 0.3), 12, 150, 4
    grid = []
    for sh in shifts:
        for dec in declines:
            rng = np.random.default_rng(int(1000 * sh + 100 * dec) + 17)
            rows, sample = [], None
            for rep in range(reps):
                psi = np.r_[np.full(n_sites, 0.6), np.full(n_sites, 0.6 - dec)]
                z = rng.random(2 * n_sites) < psi
                turb = np.vstack([rng.normal(0, 0.3, (n_sites, n_surv)), rng.normal(sh, 0.3, (n_sites, n_surv))])
                y = ((rng.random((2 * n_sites, n_surv)) < expit(1.0 - 1.5 * turb)) & z[:, None]).astype(float)
                zone = np.r_[np.zeros(n_sites), np.ones(n_sites)]
                fit = occupancy.fit(y, psi_covariates=zone, detection_covariates=turb)
                b0, b1 = fit["beta_psi"]
                se1 = fit["se"][1]
                rows.append([y[:n_sites].max(1).mean(), y[n_sites:].max(1).mean(), expit(b0), expit(b0 + b1),
                             float(abs(b1) > 1.96 * se1)])
                if rep == 0:
                    sample = {"occupied": "".join("1" if v else "0" for v in z),
                              "detections": "".join(str(int(v)) for v in y.sum(1))}
            a = np.array(rows)
            grid.append({"shift": sh, "decline": dec, "naive_ref": R(a[:, 0].mean(), 3), "naive_imp": R(a[:, 1].mean(), 3),
                         "psi_ref": R(a[:, 2].mean(), 3), "psi_imp": R(a[:, 3].mean(), 3),
                         "psi_imp_sd": R(a[:, 3].std(), 3), "detect_rate": R(a[:, 4].mean(), 3), "sample": sample})
    betas = {"clear oceanic": 0.05, "coastal": 0.2, "turbid coastal": 0.5, "very turbid": 0.85}
    table = [{"water": k, "beta_d": b, "rows": [{"z_m": z, "t": float(f"{math.exp(-b * z):.3g}"),
                                                  "gain": float(f"{math.exp(b * z):.3g}"),
                                                  "recoverable": math.exp(-b * z) >= imaging.T_MIN_DEFAULT}
                                                 for z in (1, 2, 5, 10, 15, 20)]} for k, b in betas.items()]
    turb = np.linspace(-0.5, 3.0, 36)
    p = expit(1.0 - 1.5 * turb)
    det = {"turbidity": [R(v, 2) for v in turb], "p_single": [R(v, 3) for v in p],
           "p_any_of_4": [R(1 - (1 - v) ** 4, 3) for v in p]}
    return {"grid": grid, "settings": {"sites_per_zone": n_sites, "surveys": n_surv, "reps": reps, "psi_ref": 0.6,
                                        "detection_model": "logit p = 1.0 - 1.5 x turbidity (standardised)"},
            "conditioning": table, "detection_curve": det}


def aquaculture() -> dict:
    ratios = np.logspace(-2, 1, 13)
    sweep = []
    for r in ratios:
        e_fd, e_kf = [], []
        for seed in range(3):
            sc = tracking.simulate_school(n=12, steps=300, align=0.9, heading_noise=0.6, seed=seed)
            pos, vel, dts = sc["pos"], sc["vel"], sc["dt"]
            p_true = tracking.polarisation_series(vel)[6:].mean()
            sx = r * 0.3 * dts
            obs = pos + np.random.default_rng(100 + seed).normal(0, sx, pos.shape)
            fd = np.diff(obs, axis=0) / dts
            kf = tracking.kalman_cv(obs, dts, sx, q=0.5)
            e_fd.append(abs(tracking.polarisation_series(fd)[5:].mean() - p_true))
            e_kf.append(abs(tracking.polarisation_series(kf)[6:].mean() - p_true))
        sweep.append({"ratio": R(r, 4), "err_fd": R(np.mean(e_fd), 4), "err_kf": R(np.mean(e_kf), 4)})
    sp = bioenergetics.SpeciesParams()
    temps = np.arange(6.0, 22.01, 0.25)
    curve = []
    for t in temps:
        c = bioenergetics.carrying_capacity_kg(float(t), 30, 7.6, 400, 100, sp)
        curve.append({"t_c": R(t, 2), "do_kg": R(c["limits_kg"]["do"], 1), "nh3_kg": R(c["limits_kg"]["ammonia"], 1),
                      "welfare_kg": R(c["limits_kg"]["welfare"], 1), "binding": c["binding"],
                      "yield": R(bioenergetics.yield_index(float(t), 30, 7.6, 400, 100, sp), 1)})
    best = max(curve, key=lambda c: c["yield"])
    return {"kalman_sweep": sweep, "bio_curve": curve,
            "bio_settings": {"salinity_psu": 30, "ph": 7.6, "flow_m3_h": 400, "tank_m3": 100,
                             "species": sp.name, "t_opt": sp.t_opt, "t_max": sp.t_max, "placeholder": True},
            "ceiling_c": best["t_c"], "ceiling_binding": best["binding"]}


REPORTED = {
    "source": "Findings reported from the Colab runs of the rebuilt notebooks (not recomputed on this page).",
    "thermal": [
        {"title": "Per-port asymptote bug", "text": "The near-field cell used total diffuser flow where the law needs per-port flow. Two algebraic forms of the same law disagreed by 84% while the cell printed that the constants agreed. Fixed; the library now enforces per-port and per-length fluxes."},
        {"title": "Domain narrower than the tide", "text": "About 26% of the heat was being lost because the plume advected out of a domain narrower than the tidal excursion (about 10.7 km over two M2 cycles). Rather than patch it, the analysis was reframed as a steady design-current mixing-zone study, matching §316(a) practice."},
        {"title": "Silent numerical diffusion", "text": "First-order upwind added about 2.1 m²/s of numerical diffusion at 25 m resolution, around 20% of the dispersion the model used, with no warning. Against scale-dependent ocean mixing it is larger than the real thing below about 3 km."}],
    "monitoring": [
        {"title": "Turbidity masquerading as impact", "text": "Detection failure that rose with turbidity looked exactly like animals leaving. Only the detection-corrected occupancy model separated the two."},
        {"title": "Conditioning, not tolerance", "text": "At long range in turbid water, transmittance fell to about 5×10⁻⁸, amplifying rounding error about 20 million-fold in the image round-trip test. The loosened tolerance was replaced with a conditioning table that flags unrecoverable frames."}],
    "aquaculture": [
        {"title": "205 tracks for 12 fish", "text": "The tracker fell apart because of camera siting: fish moved 34 pixels per frame across a 37 cm field of view. Correcting the geometry and arena size brought track purity to 0.998, 0.935 and 0.678 for calm, moderate and erratic schools."},
        {"title": "A hypothesis that didn't survive", "text": "Kalman-filtered velocities were expected to recover school polarisation better than raw frame differencing. The sweep showed filtering only wins when localisation noise is large relative to per-frame motion. The notebook reports the trade-off instead of the original claim."},
        {"title": "Yield optimum below growth optimum", "text": "Because the oxygen- and ammonia-limited stocking ceiling falls as water warms, the economically best loop temperature is cooler than the temperature at which fish grow fastest."}],
    "purity": [{"school": "Calm", "purity": 0.998}, {"school": "Moderate", "purity": 0.935}, {"school": "Erratic", "purity": 0.678}],
}


def main() -> None:
    out = {"generated": "2026-09-29", "library_version": ag.__version__,
           "note": "Recomputed with fixed seeds by app/notebook_results.py.",
           "thermal": thermal(), "monitoring": monitoring(), "aquaculture": aquaculture(), "reported": REPORTED}
    p = ROOT / "data" / "notebook_results.json"
    p.write_text(json.dumps(out, separators=(",", ":"), ensure_ascii=False))
    print(f"wrote {p} ({p.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
