# Visual Plumes UM3 outputs for Aquatic Guardian P-3

EPA Visual Plumes is a **Windows** desktop application. This folder holds input
decks a person prepares on Windows, and (once available) CSV outputs that the
Python comparison merges automatically.

## What to install

1. Obtain EPA Visual Plumes (VP) from the US EPA mixing-zone tools distribution
   used by your organisation (historically distributed as a Windows installer;
   check the current EPA site for "Visual Plumes" / PLUMES).
2. Install on a Windows machine. UM3 is the recommended model for a single
   round buoyant jet in stagnant ambient; NRFIELD is for multiport diffusers.

## Generate decks (any OS)

From the repository root, with the project venv active:

```bash
python benchmarks/visual_plumes/write_um3_decks.py
```

This writes one JSON card and one plain-text entry sheet per case under
`benchmarks/visual_plumes/decks/`, matching the sweep in
`benchmarks/compare_near_field.py` (port diameter, flow, g′, depth).

## Run each case in Visual Plumes

For each `decks/<case_id>.txt`:

1. Open Visual Plumes → new UM3 simulation.
2. Set **ambient** to stagnant (current = 0) and **unstratified**, water depth =
   case depth H.
3. Set **one vertical round port** with diameter D and flow Q from the sheet.
4. Set ambient and effluent temperature/salinity. The sheet gives a starting
   effluent temperature so that reduced gravity is near the case g′. Adjust
   until VP reports a discharge g′ matching the case (within a few percent).
5. Run UM3.
6. Export centreline dilution versus height (or tabulate manually).

## Save outputs

Write a CSV to:

```text
benchmarks/visual_plumes/outputs/<case_id>.csv
```

with header and at least a row at the case depth:

```text
z_m,dilution_centreline
0.0,1.0
...
25.0,42.3
```

`case_id` must match the deck stem, e.g. `d0p3_Q0p05_gp0p015_z25.csv`.

## Merge into the comparison

Re-run:

```bash
python benchmarks/compare_near_field.py
```

If CSVs are present, `near_field_comparison.csv` gains `dilution_visual_plumes`
and `ratio_library_over_vp` columns. Until then those columns stay empty and
verification item **P-3 remains "Needs benchmark"**.
