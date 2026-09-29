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
| P-3 | Dilution coefficients 0.089 (point) and 0.38 (line) | Fischer et al. (1979) asymptotic minimum dilution; MTT integral similarity (∝ z, ∝ z^{5/3}); library vs integral sweep in `docs/BENCHMARK_P3.md`; 8 integral *proxy* CSVs under `benchmarks/visual_plumes/outputs/` (not UM3) | **Needs benchmark** against real Visual Plumes UM3 / NRFIELD (and ideally a lab set). Integral proxy exercises the merge path only — see `outputs/PROVENANCE.json` | `test_pure_jet_dilution_scales_linearly_with_z`, `test_pure_plume_dilution_scales_as_z_to_the_five_thirds` |
| P-4 | Stratified trapping, crossflow and bottom attachment | Not modelled | **Out of scope**; use UM3/CORMIX | none |
| T-1 | M2 excursion 2U/ω (Correction 2) | 10.7 km ↔ 0.75 m/s | Published value | `test_tidal_excursion` |
| N-1 | Okubo (1971) diffusivity | 0.58 m²/s at 1 km; crossover ~3 km for 2.1 m²/s | Published value | `test_okubo_values` |
| N-2 | Upwind numerical diffusion formula (Correction 3) | Measured from variance growth, within 5 % | Simulation | `test_upwind_numerical_diffusion_matches_formula` |
| N-3 | Flux-limited (MC) scheme | < 20 % of upwind diffusion; mass conserved; no negatives | Simulation | `test_tvd_scheme_removes_most_numerical_diffusion_and_conserves_mass` |
| N-4 | Physical diffusion recovered with TVD | Within 20 % | Simulation | `test_physical_diffusion_recovered_by_tvd` |
| W-1 | DO saturation (Garcia & Gordon 1992, Benson & Krause) | 9.09 mg/L at 20 °C fresh; 14.62 at 0 °C | Published value | `test_do_freshwater_20c`, `test_do_freshwater_0c` |
| W-2 | DO in seawater | 20 °C/35: 7.2 to 7.5; 10 °C/35: 8.8 to 9.2 mg/L | Published value (range) | `test_do_seawater_ranges` |
| W-3 | Un-ionised ammonia, freshwater (Emerson et al. 1975) | Table values at 20 °C pH 7 and 25 °C pH 8 | Published value | `test_emerson_table` |
| W-4 | Salinity correction (Khoo et al. 1977) vs Bower & Bidwell (1978) seawater % NH₃ | LaMotte seawater table at S=34‰ / ionic strength 0.701 m, attributed to Bower & Bidwell (1978) pp. 1012–1016: e.g. 2.98% at 20 °C pH 8.0, 4.28% at 25 °C pH 8.0 | **Published value** — confirmed LaMotte reprint of B&B; see `data/checks/BOWER_BIDWELL_PROVENANCE.md` | `test_unionised_fraction_vs_bower_bidwell`, `test_salinity_lowers_unionised_fraction` |
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
| J-1 | Browser engine | 200 randomised scenarios spread over every jurisdiction, 17 outputs, rel. tol. 1e-9, identical flag ids and flag text | Parity | `test_js_engine_matches_python` |
| J-2 | Jurisdiction tables in `app/engine.js` | The mirrored `JURISDICTIONS` and `INTAKE_RULES` tables equal the `jurisdictions` and `intake_rules` sections of `data/criteria.json` field for field, and the resolved lookup matches Python for every jurisdiction | Parity | `test_js_jurisdiction_tables_match_criteria_json`, `test_js_jurisdiction_lookup_matches_python` |
| J-3 | Lab simulation kernels (`app/sims.js`) | 1-D transport both directions, imaging, bioenergetics and Kalman match the Python library to 1e-12 (Kalman 1e-9); 2-D tidal upwind spreading matches the numerical-diffusion formula within 5 % | Parity | `test_sims_parity.py` |
| R-3 | Jurisdiction rule mapping | Washington and California carry a cited rule; British Columbia, the EU, Oregon, other US states and "other" map to a user-supplied increment, are marked `placeholder` with `verify: true`, and raise a flag saying the result cannot show compliance | **Placeholder for five of seven jurisdictions** — BC, EU and Oregon values are permit-specific or not yet transcribed | `test_jurisdictions_never_assert_an_untranscribed_rule` |
| R-4 | Flags cite only law that applies | §316(b) and 40 CFR 125.84 flags appear only where the jurisdiction's intake rule is `us_cwa_316b`; the Fisheries Act note only where it is `ca_fisheries_act`; neither appears for the EU or "other" | Property test over every jurisdiction | `test_intake_rule_only_cites_law_that_applies_there`, `test_screening_flags_only_cite_the_selected_jurisdictions_law`, `test_no_flag_cites_a_law_that_does_not_apply_there` (browser) |
| G-1 | Policy briefs quote clauses exactly | Every clause id in `policy/model-language/` appears in exactly one brief, byte for byte, in the brief for its own file; the committed `briefs/*.md` match a fresh generation; every instrument and recommendation reaches its brief; `verify` entries carry their warning into print | Simulation | `test_briefs.py` |
| X-1 | Tracker data shape | `data/instruments.json` validates against `schemas/instruments.schema.json` (JSON Schema 2020-12): ids unique, stage from a closed list, dates ISO, `doc` names a file that exists, sources are absolute http(s) URLs, and an entry with no source cannot be marked verified | Simulation | `test_tracker.py` |
| X-2 | Tracker review report | `scripts/tracker_report.py` finds entries older than `stale_after_days`, entries marked `verify`, and dates that have passed while the status still reads as forthcoming; each finding is reported once | Simulation with synthetic entries | `test_the_report_finds_a_stale_entry`, `test_the_report_catches_a_past_date_still_described_as_future`, `test_the_report_reports_each_finding_once` |
| A-1 | Site accessibility and behaviour | `site/index.html` in Chromium: audience routes (public, officials, lab, industry), no console errors beyond blocked fonts, no horizontal scroll at 390 px, every input labelled, officials and industry screening tools, Lab notebook results and sims, model-language tabs respond to arrow keys, dark mode renders, no request other than Google Fonts, and no serious or critical axe-core violation under the WCAG 2.2 AA tag set | Simulation (browser) | `test_site.py` (marker `site`) |
| L-1 | Lab notebook results | Fixed-seed recomputation of thermal / monitoring / aquaculture notebook outputs for the Lab page; Colab-only findings stay in `reported` | Simulation | `app/notebook_results.py` (consumed by build; covered by Lab content in `test_site.py`) |

## Before any result leaves the team

1. P-3 benchmark completed and the coefficient source recorded.
2. W-4 confirmed via LaMotte's attributed Bower & Bidwell (1978) seawater table (pp. 1012–1016); R-2 checked against the SWRCB Thermal Plan primary text.
3. All placeholder species parameters replaced and reviewed.
4. Site tidal currents taken from a NOAA CO-OPS or DFO/CHS station, not assumed.
5. The conditional-finding template in each notebook completed.
6. A primary-source URL recorded for every entry in `data/instruments.json`. All 16 entries currently have an empty `sources` array and `verify: true`; `scripts/tracker_report.py` lists them. Nobody can check a status or a date in the tracker without searching for the source again.
7. Oregon's, British Columbia's and the member-state EU temperature rules transcribed from primary text, so those jurisdictions stop relying on a user-supplied increment (register item R-3).
8. The site's headline count of automated checks confirmed against the suite before release; it is written by hand in `web/parts/2_body.html`.
