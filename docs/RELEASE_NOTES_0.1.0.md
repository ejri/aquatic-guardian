# Aquatic Guardian 0.1.0 — release notes (draft)

**A Sentient Futures project.** Plug-in aquatic, ecological and animal-welfare module for data-centre regulation: policy language, a verified screening library, disclosure schemas, and a public screening website.

Builds on *Governing the Ocean Server Farm* (Elchami, Kaplan and Daher, Sentient Futures, April 2026).

## Four deliverables

1. **Policy** — framework, recommendations, and model clauses for US federal and state instruments, permits, the EU, Canada, BBNJ / ISO and the UK (`policy/`).
2. **Verified library** — heat budget, intake, near-field plume, tidal excursion, numerical diffusion, DO, ammonia, temperature rules, occupancy, imaging, tracking, bioenergetics, sentience reporting, disclosure and notebook handoffs (`src/aquatic_guardian/`).
3. **Open packaging** — 119 automated checks, schemas, instrument tracker, criteria table, CI, licences, citation (`tests/`, `schemas/`, `data/`).
4. **Website and briefs** — self-contained screening app (`site/`), jurisdiction-aware rules, printable briefs (`briefs/`), Netlify-ready publish directory.

## Verification status (see `docs/VERIFICATION.md`)

| Status | Examples |
|---|---|
| **Published value / rule text** | EOS-80 density, cooling flow, Okubo diffusivity, DO saturation, Emerson ammonia (freshwater), WA marine increment, **CA Thermal Plan new coastal (R-2 closed)** |
| **Simulation / parity** | Occupancy detection trap, TVD numerics, image inversion, browser↔Python engine parity (J-1), notebook handoffs (D-2) |
| **Needs benchmark** | Near-field dilution coefficients (P-3) — MTT integral comparison is in `docs/BENCHMARK_P3.md`; **EPA Visual Plumes UM3 outputs still required** |
| **Needs table check** | Seawater ammonia vs Bower & Bidwell 1978 (W-4) — CSV scaffold awaiting transcription |
| **Placeholder** | Species welfare / TGC parameters (B-2); BC, EU and Oregon temperature increments (`verify: true`) |

Screening outputs are for scoping. They are not a permit decision.

## How to contribute

- Officials and counsel: correct tracker rows with a primary-source URL (`data/instruments.json`); all 16 entries currently await sources.
- Scientists: Visual Plumes UM3 runs into `benchmarks/visual_plumes/outputs/`; species thresholds replacing placeholders.
- Engineers: open issues with the templates under `.github/ISSUE_TEMPLATE/`.

## Cite

Use `CITATION.cff`. A DOI is minted when the GitHub–Zenodo release is published (see `.zenodo.json`).
