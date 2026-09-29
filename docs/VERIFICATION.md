# Verification register

What each part of the toolkit has been checked against, and what still needs outside review. Run `pytest` to reproduce every "verified" row; the test named in the last column fails if the check stops holding.

Status key: **Published value**, reproduces a number printed in the cited source; **Simulation**, the property is demonstrated on synthetic data with known truth; **Parity**, the browser engine matches the Python reference; **Needs benchmark**, implemented and internally consistent but must be compared with an established model or field data before regulatory use; **Placeholder**, not to be used for decisions.

| ID | Item | Check | Status | Test |
|---|---|---|---|---|
| S-1 | Seawater density (UNESCO EOS-80, p = 0) | Four UNESCO (1981) check values to 2e-4 kg/m³ | Published value | `test_eos80_check_values` |
| S-2 | Reduced gravity of heated seawater | 10 K at 10 °C gives 0.01 to 0.03 m/s² | Published value (order) | `test_heated_seawater_is_weakly_buoyant` |
| C-1 | Cooling flow per MW | ~24 L/s per MW at 10 K | Published value | `test_cooling_flow_per_mw` |
| C-2 | Reuse counted only before discharge | Arithmetic | Simulation | `test_heat_reuse_only_before_discharge` |
| I-1 | §316(b) 2 MGD trigger and 25 % cooling test | Unit conversion; 2 MGD ≈ 3.6 MW heat at 10 K | Published value | `test_316b_threshold_conversion` |
| I-2 | Estuary 1 % tidal-volume test (40 CFR 125.84) | Implemented as written | Needs legal check of current text | none |
| P-1 | Port-spacing regime (Tian, Roberts & Daviero 2004) | s/H ≤ 0.3 line, ≥ 1.0 point | Published value | `test_regime_boundaries` |
| P-2 | Per-port versus total flow (Correction 1) | Error factor exactly N^(2/3) | Simulation | `test_total_flow_substitution_error_is_n_two_thirds` |
| P-3 | Dilution coefficients 0.089 (point) and 0.38 (line) | Fischer et al. (1979) asymptotic minimum dilution; MTT integral similarity (∝ z, ∝ z^{5/3}); library vs integral sweep in `docs/BENCHMARK_P3.md` | **Needs benchmark** against Visual Plumes UM3 / NRFIELD and a lab data set (integral infrastructure in place; VP outputs not yet present) | `test_pure_jet_dilution_scales_linearly_with_z`, `test_pure_plume_dilution_scales_as_z_to_the_five_thirds` |
| P-4 | Stratified trapping, crossflow and bottom attachment | Not modelled | **Out of scope**; use UM3/CORMIX | none |
| T-1 | M2 excursion 2U/ω (Correction 2) | 10.7 km ↔ 0.75 m/s | Published value | `test_tidal_excursion` |
| N-1 | Okubo (1971) diffusivity | 0.58 m²/s at 1 km; crossover ~3 km for 2.1 m²/s | Published value | `test_okubo_values` |
| N-2 | Upwind numerical diffusion formula (Correction 3) | Measured from variance growth, within 5 % | Simulation | `test_upwind_numerical_diffusion_matches_formula` |
| N-3 | Flux-limited (MC) scheme | < 20 % of upwind diffusion; mass conserved; no negatives | Simulation | `test_tvd_scheme_removes_most_numerical_diffusion_and_conserves_mass` |
| N-4 | Physical diffusion recovered with TVD | Within 20 % | Simulation | `test_physical_diffusion_recovered_by_tvd` |
| W-1 | DO saturation (Garcia & Gordon 1992, Benson & Krause) | 9.09 mg/L at 20 °C fresh; 14.62 at 0 °C | Published value | `test_do_freshwater_20c`, `test_do_freshwater_0c` |
| W-2 | DO in seawater | 20 °C/35: 7.2 to 7.5; 10 °C/35: 8.8 to 9.2 mg/L | Published value (range) | `test_do_seawater_ranges` |
| W-3 | Un-ionised ammonia, freshwater (Emerson et al. 1975) | Table values at 20 °C pH 7 and 25 °C pH 8 | Published value | `test_emerson_table` |
| W-4 | Salinity correction (Khoo et al. 1977) | Lowers fraction; order of magnitude of Bower & Bidwell (1978) | **Needs table check** — CSV scaffold in `data/checks/bower_bidwell_1978.csv` (rows still TRANSCRIBE); secondary sources cite ~4.2% NH₃ at 25 °C, pH 8, S≈35 but primary pages 1012–1016 not yet transcribed | `test_salinity_lowers_unionised_fraction`, `test_unionised_fraction_vs_bower_bidwell` (skips until transcribed) |
| W-5 | EPA 2013 freshwater ammonia criteria | 17 and 1.9 mg TAN/L at pH 7, 20 °C | Published value | `test_epa2013_criteria_at_reference_conditions` |
| R-1 | WA marine increment rule, WAC 173-201A-210 | 12/(T−2), headroom and 0.3 °C cases | Published rule text | `test_wa_increment_rule` |
| R-2 | CA Thermal Plan, new coastal discharges | 4 °F and 20 °F at/ beyond 1,000 ft; unit conversion | **Published value** — SWRCB Thermal Plan §3.B.(3)–(4) transcribed in `data/checks/ca_thermal_plan.md` (PDF accessed 2026-09-29) | `test_ca_thermal_plan_units`, `test_ca_thermal_plan_text_matches_criteria` |
| O-1 | Occupancy with detection correction (MacKenzie et al. 2002) | Naive analysis shows a 17-point false impact; pooled model finds no zone effect and recovers the turbidity slope | Simulation | `test_turbidity_masquerades_as_impact_without_detection_model` |
| V-1 | Image formation inversion (Akkaynak & Treibitz) | Exact round trip where t ≥ 0.1; low-transmittance frames flagged | Simulation | `test_image_inversion_round_trip_and_flagging` |
| K-1 | Null polarisation baseline | RMS 1/√N and mean √π/(2√N) | Simulation | `test_null_polarisation` |
| K-2 | Frame-difference velocity noise | √2 σx/Δt | Simulation | `test_fd_velocity_noise` |
| B-1 | Yield optimum below growth optimum | Holds for the placeholder parameter set | Simulation, **placeholder parameters** | `test_yield_optimum_below_growth_optimum_with_placeholders` |
| B-2 | Species parameters (TGC, T_opt, MO₂, welfare density) | None reviewed | **Placeholder** | none |
| E-1 | Sentience tiers | UK 2022 Act, Birch et al. 2021, NY Declaration 2024 | Literature mapping; **needs welfare-scientist review** | `test_sentience_table_never_merges_life_stages` |
| D-1 | Disclosure and handoff records | Validate against JSON Schema 2020-12 | Simulation | `test_records.py` |
| D-2 | Notebook library integration + handoffs | Three mentee notebooks execute headlessly (CPU, synthetic); `thermal` / `monitoring` / `aquaculture` handoffs validate | Simulation | `test_notebooks.py` (marker `slow`) |
| J-1 | Browser engine | 200 randomised scenarios, 17 outputs, rel. tol. 1e-9, identical flags | Parity | `test_js_engine_matches_python` |

## Before any result leaves the team

1. P-3 benchmark completed and the coefficient source recorded.
2. W-4 and R-2 checked against the primary text.
3. All placeholder species parameters replaced and reviewed.
4. Site tidal currents taken from a NOAA CO-OPS or DFO/CHS station, not assumed.
5. The conditional-finding template in each notebook completed.
