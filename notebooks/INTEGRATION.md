# Connecting the Colab notebooks

The three rebuilt notebooks (Thermal-Tidal, Aquatic Monitoring, Aquaculture Vision) keep their teaching narrative and figures, and import their physics from this library so that every notebook, the web app and the policy text use the same verified functions.

## 1. First cell of every notebook

Detect Colab vs local. Pin the tag on Colab; locally install the editable repo (parent of `notebooks/`). Print the version. Handoffs write to `notebooks/_handoffs/` (optional Colab Drive path in a comment).

```python
import sys, subprocess
from pathlib import Path
IN_COLAB = "google.colab" in sys.modules
if IN_COLAB:
    subprocess.check_call([sys.executable, "-m", "pip", "-q", "install",
                           "git+https://github.com/ejri/aquatic-guardian.git@v0.1.0"])
else:
    subprocess.check_call([sys.executable, "-m", "pip", "-q", "install", "-e", str(Path("..").resolve())])
import aquatic_guardian as ag
print("aquatic_guardian", ag.__version__)
```

A notebook that reports results must state the library version it ran with.

## 2. Replace in-notebook implementations

| Notebook | Replace | With |
|---|---|---|
| Thermal-Tidal | near-field plume dilution cells | `ag.plume.near_field(ag.plume.Diffuser(Q, N, d, s), H, T, dT, S, U)` |
| Thermal-Tidal | tidal excursion over two cycles | `ag.tidal.excursion_half_cycle(U)` plus `ag.tidal.residual_drift(u_res, n)` |
| Thermal-Tidal | first-order upwind transport | `ag.numerics.advect_diffuse_1d(..., scheme="tvd")`, and print `ag.numerics.k_num_upwind(u, dx, dt)` beside `ag.numerics.okubo_kh(L)` |
| Thermal-Tidal | DO and ammonia exports | `ag.water_quality.do_saturation_mg_l(T, S)`, `ag.water_quality.unionised_fraction(T, pH, S)` |
| Thermal-Tidal | mixing-zone test | `ag.criteria.temperature_rule(rule, T_background)` at critical design conditions |
| Aquatic Monitoring | occupancy fit | `ag.occupancy.fit(y, psi_covariates=zone, detection_covariates=turbidity)`; report `psi_hat`, `se` and `naive_occupancy` together |
| Aquatic Monitoring | image formation round trip | `ag.imaging.invert(I, z, beta_d, beta_b, b_inf)`; pass `recoverable` into detection covariates |
| Aquaculture Vision | polarisation | `ag.tracking.polarisation(vx, vy)` with `ag.tracking.null_polarisation(N)` |
| Aquaculture Vision | Kalman versus differencing discussion | `ag.tracking.kalman_benefit_ratio(sigma_x, speed, dt)` |
| Aquaculture Vision | TGC growth and carrying capacity | `ag.bioenergetics.carrying_capacity_kg(...)`, `ag.bioenergetics.yield_index(...)` with a filled `SpeciesParams` |

## 3. JSON handoff

Replace ad-hoc JSON with validated records (`schemas/notebook-handoff.schema.json`):

```python
# Thermal-Tidal, last cell
rec = ag.handoff.make(
    "thermal_tidal", scenario_id="august-p10-current",
    assumptions=["slack-water near field", "TVD far field, dx = 25 m"],
    placeholders=["kelp and eelgrass thresholds"],
    loop_inlet_temperature_c=T_loop,
    receiving_water={"ambient_t_c": T, "salinity_psu": S, "ph": pH,
                     "do_mg_l": ag.water_quality.do_saturation_mg_l(T, S),
                     "unionised_ammonia_fraction": ag.water_quality.unionised_fraction(T, pH, S)},
    plume={"delta_t_mixing_zone_edge_k": dT_edge, "regime": nf["regime"],
           "near_field_dilution": nf["dilution"],
           "grid": {"dx_m": 25, "k_num_m2s": K_num, "k_phys_m2s": K_phys, "scheme": "tvd"}})
ag.handoff.write(rec, "notebooks/_handoffs/thermal_handoff.json")
# Optional Colab: ag.handoff.write(rec, "/content/drive/MyDrive/aquatic_guardian/thermal_handoff.json")
```

```python
# Aquaculture Vision, last cell: return the ceiling to Thermal-Tidal
rec = ag.handoff.make("aquaculture_vision", scenario_id="august-p10-current",
                      assumptions=[...], placeholders=sp_placeholders,
                      recommended_loop_inlet_ceiling_c=T_ceiling, binding_constraint="do")
ag.handoff.write(rec, "notebooks/_handoffs/aquaculture_handoff.json")
```
`ag.handoff.read()` rejects a file that does not validate. A non-empty `placeholders` list means the result is not ready to leave the team.

## 4. From notebook to disclosure record

```python
r = ag.screening.screen({...facility inputs...})
record = ag.disclosure.from_screening(r, "site-01", ["CA-BC"], "nearshore_submerged",
                                      ("2027-01-01", "2027-12-31"))
assert ag.disclosure.validate(record) == []
```

The web app produces the same record from the same engine.
