# Benchmark P-3: near-field screening against PLUMES 2.0 (UM3)

**Use EPA PLUMES 2.0, not legacy Visual Plumes.** Visual Plumes 1.0 (2001) is distributed as unsupported beyond Windows XP. PLUMES 2.0 (December 2025 release) is EPA's maintained replacement; it reimplements UM3 and matched original UM3 within about 0.5 % in EPA's validation. Download: [EPA PLUMES 2.0](https://www.epa.gov/hydrowq/PLUMES2) or [ssmc-uw/PLUMES2.0](https://github.com/ssmc-uw/PLUMES2.0). Optional web port of Visual Plumes (includes NRFIELD): https://visualplumes.sfei.org.

All inputs, the run guide, the results template and the comparison script live in **`benchmarks/plumes2/`**. Start with that folder's README.

## Pass criteria (checked by `compare.py`)

1. **Never too optimistic** — in near-stagnant cases, library dilution ≤ UM3 centreline dilution.
2. **Not uselessly cautious** — UM3 ÷ library ≲ 2.
3. **Stronger currents mix more** — dilution rises with current.
4. **Merging where expected** — UM3 reports merging in closely spaced cases, not in the widely spaced one.

Send `benchmarks/plumes2/results.csv` and a screenshot of one case's input tabs. If every criterion holds, P-3 moves to verified; if any case is less cautious than UM3, coefficients are refitted (Correction 8) and every site number updates.

## Critical PLUMES 2.0 settings

- Effluent salinity **30 psu** (cooling water is seawater; 0 models a freshwater plume).
- Add **centerline dilution** to outputs (the library predicts the peak, not flux-averaged dilution).
