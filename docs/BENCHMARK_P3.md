# P-3 near-field benchmark (Phase 3)

Status of verification item **P-3**: still **Needs benchmark**. The library
coefficients (`C_POINT = 0.089`, `C_LINE = 0.38`, `JET_DECAY = 5.6`) are
unchanged. This document records the independent integral comparison and the
Visual Plumes path that remains to be completed by a person on Windows.

## What was built

| Artefact | Role |
|---|---|
| `benchmarks/integral_jet.py` | Morton–Taylor–Turner integral round jet/plume (Gaussian profiles, variable α) |
| `benchmarks/compare_near_field.py` | Sweep vs library point-source envelope; CSV + SVG |
| `benchmarks/results/near_field_comparison.csv` | 320 cases |
| `benchmarks/results/near_field_ratio_vs_z_lM.svg` | Ratio plot |
| `benchmarks/visual_plumes/` | UM3 decks, README, CSV loader |
| `tests/test_benchmark_integral.py` | Pure-jet ∝ z and pure-plume ∝ z^{5/3} scaling |

## Integral model (independent of the library)

- Entrainment: Morton, Taylor and Turner (1956) with α(Fr) jet→plume transition
  as in Lee & Chu (2003) / Fischer et al. (1979).
- Coefficients cited in the module docstring: **α_j = 0.057** (Lee & Chu 2003;
  Fischer ≈ 0.053–0.057), **α_p = 0.083** (Fischer et al. 1979).
- Parameters left explicit for confirmation: **Fr_p = 3.5** (literature ~3.4–3.7),
  **λ = 1.2** (Lee & Chu concentration/velocity width). Zone of flow
  establishment is not modelled.
- Similarity tests (Fischer et al. 1979 scaling): log–log slope within 15% of
  1.0 (pure jet) and 5/3 (pure plume / far-field forced plume).

## Sweep design

Ranges aligned with `tests/test_engine_parity.py`:

- port diameter 0.1–1.0 m
- per-port flow 0.02–0.4 m³/s
- reduced gravity 0.005–0.04 m/s² (heated-seawater order, item S-2)
- depth 4–80 m

Library side: stagnant **point-source envelope** `max(jet, plume)` using the
unchanged coefficients (single round port). Line-plume coefficient 0.38 is out
of scope for this round-jet integral model.

## Headline agreement (integral vs library)

From `benchmarks/results/near_field_comparison.csv` (320 cases):

| Metric | Value |
|---|---|
| Median S_library / S_integral | **0.92** |
| 10th–90th percentile | 0.68–1.24 |
| Min–max | 0.49–1.30 |
| Cases with library **less conservative** (S_lib > S_int) | **127 / 320 (40%)** |

By Fischer length-scale regime:

| Regime | n | Median ratio | Library less conservative |
|---|---|---|---|
| Jet-like (z/l_M < 0.5) | 40 | 0.87 | 0 / 40 |
| Transition (0.5–5) | 110 | 0.82 | 0 / 110 |
| Plume-like (z/l_M > 5) | 170 | 1.14 | 127 / 170 |

Interpretation:

- In jet and transition regimes the library envelope is **always at or below**
  the integral centreline dilution in this sweep (conservative for thermal
  impact).
- In the deep plume regime the library **often predicts higher dilution** than
  the integral model (up to ~30%). That is where `C_POINT = 0.089` sits slightly
  above this MTT realisation with α_p = 0.083 and λ = 1.2. Absolute levels still
  depend on Fr_p, λ, and the missing zone-of-flow-establishment — hence P-3 is
  not closed.

Worst library/integral ratios in the sweep are deep plumes (large z/l_M), e.g.
d = 1.0 m, Q = 0.02 m³/s, g′ = 0.04 m/s², z = 80 m → ratio ≈ 1.30.

## Visual Plumes

Decks: `python benchmarks/visual_plumes/write_um3_decks.py`  
Instructions: `benchmarks/visual_plumes/README.md`

**Proxy (not UM3):** `python benchmarks/visual_plumes/write_integral_proxy_outputs.py`
writes eight MTT integral centreline profiles into `outputs/` with
`PROVENANCE.json` stating `not_visual_plumes: true`. They exercise the CSV
loader and merge columns. **They do not close P-3.**

When true Visual Plumes CSVs exist, replace the proxy files and re-run
`python benchmarks/compare_near_field.py` to fill `dilution_visual_plumes`
columns. **P-3 stays Needs benchmark until UM3/NRFIELD outputs (and ideally a
lab data set) are in and reviewed.**

## What a human expert still has to check

1. Run EPA Visual Plumes (Windows) for the deck set; confirm g′ matching.
2. Confirm Fr_p and λ against the profile convention used in UM3.
3. Decide whether `C_POINT = 0.089` should stay, be lowered for conservatism, or
   wait for UM3 before any coefficient change.
4. Line-plume coefficient 0.38 needs a separate multiport / NRFIELD comparison.
