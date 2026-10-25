# Validating plumes2py against EPA PLUMES 2.0

PLUMES 2.0 (EPA/600/B-24/339, December 2024) is distributed as a Windows executable; its Fortran 90
source is not public (github.com/ssmc-uw/PLUMES2.0 ships `plumes2.0v1.exe`, the manual and an example
project). `plumes2py` rebuilds the model from the manual's equations and the papers it cites, and is
checked against the one public reference run: `Example_project`, whose inputs and text output
(`ModelResults_TxtOutputs.dat`) ship with the program and are copied into `python/plumes2py/data/`.

## What was rebuilt

| Component | Source | Notes |
|---|---|---|
| Lagrangian control volume, top-hat | Manual §3.3.1; Baumgartner, Frick & Roberts (1994); Lee & Cheung (1990) | eqs. 2-5 |
| Aspiration (Taylor) entrainment | Manual eq. 2, α = 0.1 | along-axis velocity difference |
| Forced entrainment | Frick (1984) projected-area hypothesis | side, growth and curvature terms |
| Merging | Manual Fig. 4 | circle clipped at the port spacing projected into the cross-section |
| Density | UNESCO EOS-80, p = 0 (sigma-t) | UNESCO check values to 2e-4 kg/m³ |
| Termination | Manual §3.3.1, §4.2.5 | trap, max rise/fall (0-3), surface, seabed, shoreline |
| Far field | Brooks (1960), manual Tables 1-2, eq. 17 | constant, linear, 4/3 laws |

## Identifying the closure from the reference output

The reference output prints every fifth step. Three facts in it pin down choices the manual leaves open:

1. **Time step.** Mass grows by exactly 2.00 % per step through the jet phase (volumetric dilution 1.101 at
   step 5, 1.213 at 10, 1.624 at 25, after correcting for the density change). The step is therefore set so
   that the *unmerged* entrainment adds 2 % of the element mass. After merging the actual entrainment is
   smaller, which reproduces the slowdown the reference shows after step ~250.
2. **Sum, not maximum.** Summing forced and aspiration entrainment (manual eq. 2) overshoots dilution at equal
   height by 12-22 %; taking the larger (Lee & Cheung's JETLAG) undershoots by 18-53 %. The truth is between.
3. **Surface contact.** The plume "surfaces" when its centre depth equals the vertical half-extent of an
   inclined cross-section, `b·cos(φ)` (2.50 m against 2.512 m at step 275).

A sweep of a single scale on Frick's forced-entrainment term, with the full three-term expression and the
step rule above, gives a minimum RMS dilution error at 0.81:

| Forced-entrainment scale | RMS log error along the path | Terminal dilution (ref 169.754) |
|---|---|---|
| 0.76 | 5.3 % | 161.7 |
| 0.80 | 3.2 % | 167.9 |
| **0.81** | **2.9 %** | **169.5** |
| 0.83 | 2.9 % | 172.6 |
| 1.00 (no scaling) | 15 % | 204.8 |

**This is a one-case calibration.** Run the 16-case benchmark kit through
`python scripts/compare_plumes2.py <case folders> --fit` before relying on 0.81 outside conditions like the
example (multiport, stratified, weak current, buoyant). The Monte Carlo in `scenarios.py` and on the site varies
this scale from 0.65 to 1.0 so model-form uncertainty is visible in every result.

## Results against the reference

| Quantity | PLUMES 2.0 | plumes2py | Difference |
|---|---|---|---|
| Dilution, steps 5 / 10 / 15 / 25 | 1.101 / 1.213 / 1.337 / 1.624 | same to ±0.002 | < 0.2 % |
| Dilution where the plume surfaces | 169.754 | 169.458 | −0.17 % |
| Plume diameter at surfacing | 6.481 m | 6.406 m | −1.16 % |
| Position x, y | 7.017, 2.082 m | 6.974, 2.080 m | −0.62 %, −0.09 % |
| Depth at surfacing | 2.512 m | 2.499 m | −0.53 % |
| Trap depth | 3.03 m | 3.31 m | +9 % |
| Events | trap 251-255, merge 256-260, surface 271-275 | trap 247, merge 257, surface 261 | same order |
| Far field at 100 m (manual Fig. 12) | 176.666 | 176.259 | −0.23 % |
| Far field at chronic boundary 102 m | "approximately 177" | 176.72 | — |
| Independent far field, manual Fig. 14 (6 rows) | — | every row to ±0.006 | exact |
| Step-size convergence (2 % → 0.5 %) | — | −0.5 % change | converged |

Trap depth is the weakest match: the trap event depends on the exact density crossing, which is sensitive
to the closure. It does not feed the far field when the plume surfaces.

## Discrepancies found in the EPA materials

1. **Example effluent temperature.** The manual (§4.2.3) describes the example effluent as 26.3 °C; the shipped
   `Effluent_example.csv`, `Example_project.prj` and the output table all carry 2.63 °C. The files produced the
   reference output, so 2.63 °C is used.
2. **Equation 11 (case 2, linear diffusivity).** The manual gives w/w0 = 1 + 2βx/w0. Integrating
   L dL/dx = 12 ε0 L/(u w0) gives 1 + βx/w0, which is also what the manual's own eq. 15 implies. plumes2py uses
   the derivation-consistent form.
3. **Far-field origin.** The manual's Fig. 12 table is reproduced with the far field starting at the end of the
   near field (≈ 7.1-7.3 m); the shipped program's `ModelResults_TxtOutputs.dat` implies ≈ 4.4 m, giving 177.326
   rather than 176.666 at 100 m. plumes2py starts at the radial end-of-near-field distance, as the manual describes.
4. **Wastefield width.** PLUMES 2.0 reports 109.59 m for the example; the rule is not published. plumes2py uses
   (N − 1)·spacing + end diameter = 110.11 m (+0.5 %).

These are worth sending to the EPA ORD and Salish Sea Modeling Center contacts listed in the manual.

## Beyond PLUMES 2.0

Extended metrics (thermal excess against local ambient and attributable to effluent heat, distances and
footprints to thresholds, organism dose, oxygen saturation loss, heat budget, flow regime from CORMIX length
scales, merging penalty, step convergence) and multi-run analyses (critical conditions, tidal cycle, Monte
Carlo, tornado) are new and are not validated against PLUMES 2.0, because PLUMES 2.0 does not compute them.
Each is tested for internal consistency in `python/tests/` (tracer conservation, per-port flow scaling,
merged ≤ isolated, heat budget, monotone dilution, slack-water caveat).

## Browser parity

`site/js/plumes2.js` mirrors the Python line for line. `tests/parity.test.mjs` runs nine scenarios (EPA example,
stop at trap, all three far-field laws, 24 MW outfall, passive pod, stratified single port, sinking brine, slack
water) and compares 1,500 values at relative tolerance 1e-7: 0 failures. CI regenerates the fixtures and fails if
Python results change without the fixtures being committed.
