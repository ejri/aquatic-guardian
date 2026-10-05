# Benchmark P-3: near-field screening against PLUMES 2.0 (UM3)

The library's near-field dilution uses asymptotic coefficients (0.089 point plume, 0.38 line plume, 5.6 jet decay) that have never been compared with an established model. This kit runs the same 16 discharges through EPA's PLUMES 2.0 so the comparison can be made and recorded.

## Why PLUMES 2.0 and not Visual Plumes

EPA now distributes the original Visual Plumes (version 1.0, 2001) as a legacy model with no support, and lists it as unsupported beyond Windows XP. PLUMES 2.0 is EPA's current, supported replacement. It was built by the University of Washington Salish Sea Modeling Center with PNNL, reimplements UM3 (the Visual Plumes near-field model) in Fortran, and matches the original UM3 within about 0.5 % across the manual's validation cases (EPA/600/B-24/339, Appendix B). It is open source under a BSD 2-clause licence.

It contains UM3 and the Brooks far-field model only. NRFIELD (the empirical multiport model) is not in PLUMES 2.0; if you want it too, the San Francisco Estuary Institute hosts a web port of Visual Plumes, which the PLUMES 2.0 manual also mentions.

### Linux / macOS note (no Fortran in the public zip)

The published `PLUMES2.0-main.zip` ships **only** `plumes2.0v1.exe` (Windows GUI). There is no Fortran source to compile. For a local Linux/macOS dry-run of the same 16 cases, use the Lee & Chu integral proxy:

```bash
python benchmarks/plumes2/run_python_lcv.py
# writes results_python_lcv.csv — labelled python-lcv-lee-chu-not-epa
python benchmarks/plumes2/compare.py benchmarks/plumes2/results_python_lcv.csv
```

That proxy is useful for engineering checks. It **does not** close register item P-3; only real PLUMES 2.0 centreline dilutions do.

## What you need

- A PC running Windows 10 or 11. Administrator rights help; see step 2.
- About an hour for all 16 cases (a few minutes each once the first is set up).
- This folder: `cases.csv` (inputs) and `results_template.csv` (what to record).

## Steps

1. **Download.** Get the zip from EPA's PLUMES 2.0 page (www.epa.gov/hydrowq/PLUMES2), or from GitHub at `ssmc-uw/PLUMES2.0` using the green Code button, then Download ZIP. Also download the PLUMES 2.0 User Manual PDF from the EPA page.
2. **Install.** Extract the zip to a folder such as your Desktop. Double-click the `plumes2.0` executable. Windows Defender may block it as unrecognised: choose "More info", then "Run anyway". On a managed work computer you may need your IT administrator.
3. **Create a project.** Project tab, New Project, make a folder called `aquatic-guardian-P3`, save the project file.
4. **Set model options once** (Model Run tab, Nearfield settings):
   - aspiration coefficient 0.1 and diffuser contraction coefficient 1.0 (the defaults);
   - keep "Stop the plume at bottom hit" and "Stop the plume at the surface hit" checked (the defaults);
   - set the nearfield output interval to **1** step;
   - under "Select Variables for Outputs", **add centerline dilution** (essential: the library predicts minimum, centreline dilution, not the flux-averaged default);
   - you may untick integrated far-field calculations; they are not needed here.
   - if centerline dilution is not in the variable list, read it from the Graphic Outputs "Plume (centerline dilution)" plot at the last near-field point and note that in `notes`.
5. **Enter each case from `cases.csv`.** One row per run.
   - **Diffuser tab:** port diameter, port elevation (0.5 m), vertical angle 90°, horizontal angle 0°, number of ports, port spacing (leave blank or 1 m for single-port cases), port depth, X and Y = 0.
   - **Effluent tab:** flow = `total_effluent_flow_m3s` (select units "cms"); temperature = `effluent_temperature_c`; **salinity = 30 psu**. The cooling water is seawater, so do not leave effluent salinity at 0, or UM3 will model a freshwater plume with far more buoyancy. Pollutant concentration: enter 100 (it only scales the output). Mixing zones: acute 10 m, chronic 100 m (not used in the comparison).
   - **Ambient tab:** two rows, depth 0 m and depth = `water_depth_m`, each with temperature 12 °C, salinity 30 psu and current = `current_ms` at direction 0°. Use the same values for the far-field velocity; leave α at the default.
   - Tip: after the first case, use the tabs' Save buttons to write `Diffuser`, `Effluent` and `Ambient` CSVs. Their format lets you (or Cursor) generate the other 15 cases instead of typing them.
   - Why 0.01 m/s rather than zero: UM3 assumes a crossflow, and the manual warns that stagnant water can cause re-entrainment problems. 0.01 m/s is effectively stagnant for these discharges.
6. **Run.** Click Model Run. You should see "Model run was completed successfully!".
7. **Record the result.** Open the text output. Take the **last near-field row**, the one where the run stopped (normally a surface hit). Copy these into a copy of `results_template.csv` named `results.csv`:

| Column | Take it from |
|---|---|
| `plumes2_version` | the zip's date, for example 12-22-2025 |
| `flux_avg_dilution` | the dilution column (flux-averaged, the default output) |
| `centerline_dilution` | the centerline dilution column you added in step 4 |
| `plume_diameter_m` | plume diameter |
| `centerline_depth_at_termination_m` | plume depth (the centreline depth below the surface when the run stopped) |
| `termination` | surface hit, trapped, or bottom hit |
| `merged` | yes or no for multiport cases, from any merging message in the text output, or from the plume graphic. Leave it blank if unclear |

8. **Compare.** Put `results.csv` in this folder and run `python benchmarks/plumes2/compare.py`. The script evaluates the library at the rise height UM3 actually reached, so the surface-hit geometry doesn't bias the comparison. It writes `comparison.csv`.

## What the results need to show

For the screening tool to keep its current coefficients, the comparison should show all four:

1. **Conservative in every near-stagnant case (A1–B6):** the library's dilution is at or below UM3's centreline dilution, so the ratio UM3 ÷ library is at least 1. A screening tool may overstate the rise but must not understate it.
2. **Not uselessly pessimistic:** UM3 ÷ library at most about 2. If screening is routinely 3 to 5 times too cautious, it will flag designs that are fine.
3. **Dilution grows with current (C1–C4 against A1 and B1):** this confirms that the slack-water case is the worst case, which is what the framework's "critical conditions" principle relies on.
4. **Merging matches the regime:** UM3 should report merging in B1, B2, B4 and B6 (line or transitional), and not in B3 (point).

## What happens with each outcome

- **All four hold:** register item P-3 moves from "Needs benchmark" to "Verified against PLUMES 2.0 (UM3)", citing the version and `comparison.csv`.
- **Any case is not conservative:** the coefficients are refitted to UM3 centreline results with a safety margin, and correction 8 is recorded in `docs/CORRECTIONS.md`. The browser engine, the parity tests and every page number change with them.
- **Too pessimistic in a regime:** only that regime's coefficient is recalibrated.

Please send `results.csv` and a screenshot of one case's input tabs, so the setup can be checked.
