# Aquatic Guardian

**A plug-in aquatic, ecological and animal-welfare module for data-centre regulation.** Version 0.1.0, 29 September 2026. A Sentient Futures project.

Governments are writing data-centre rules now, mostly about energy, grids and communities. Almost all of a data centre's electricity leaves as heat, and where that heat goes into seawater, rivers or lakes, or the servers sit in the water, it reaches animals directly. Aquatic Guardian supplies the definitions, metrics, screening methods, permit conditions and model clauses to add that footprint to the instruments already on the table: the US AI Data Center Moratorium Act (S.4214 / H.R.9442), the EU data-centre rating scheme and minimum performance standards, the Cloud and AI Development Act, British Columbia's competitive power allocation, CWA §316 and the Fisheries Act.

It builds on *Governing the Ocean Server Farm* (Elchami, Kaplan and Daher, Sentient Futures, April 2026).

## What is in the repository

| Deliverable | Where |
|---|---|
| Policy framework, recommendations and model language for the US (federal and state), permits, the EU, Canada, BBNJ, ISO/IEC and the UK | `policy/` |
| Verified screening library (heat budget, intake, near-field plume, tidal excursion, numerical diffusion, DO, ammonia, temperature rules, occupancy, underwater imaging, tracking metrics, bioenergetics, sentience reporting) | `src/aquatic_guardian/` |
| 40 automated checks against published values and known-truth simulations, including browser-engine parity | `tests/`, `docs/VERIFICATION.md` |
| The six technical corrections adopted from the fact-check | `docs/CORRECTIONS.md` |
| Aquatic Disclosure Schema (CC0) and notebook handoff schema | `schemas/`, `docs/METRICS.md`, `docs/CROSSWALK.md` |
| Instrument tracker and criteria table, each entry with its source | `data/` |
| How the three Colab notebooks import the library and exchange validated JSON | `notebooks/INTEGRATION.md` |
| Public website and screening app (single self-contained page) | `site/index.html`, built by `app/build.py` |
| Agent brief, Cursor project rules and a phased Cursor prompt pack | `AGENTS.md`, `.cursor/rules/`, `cursor/PROMPTS.md` |

## Quick start

```bash
pip install -e ".[test]"
pytest -q                 # 40 checks
python app/build.py       # rebuild site/index.html from policy text, data and engine
```

In Colab:

```python
!pip -q install "git+https://github.com/<org>/aquatic-guardian.git@v0.1.0"
import aquatic_guardian as ag
r = ag.screening.screen({"it_load_mw": 24, "delta_t_k": 8, "t_ambient_c": 12})
r["near_field"]["delta_t_near_field_k"], [f["text"] for f in r["flags"]]
```

## Single sources of truth

- Model language lives only in `policy/model-language/*.md`, between `<!-- clause: id -->` markers. The website extracts it at build time.
- The tracker lives only in `data/instruments.json`.
- Screening logic lives in `src/aquatic_guardian/screening.py`; `app/engine.js` mirrors it and `tests/test_engine_parity.py` fails if they diverge.
- CI (`.github/workflows/ci.yml`) runs the tests and fails if the built site or bundled resources are stale.

## Status and limits

Screening results are for scoping and public understanding. The near-field coefficients await a Visual Plumes UM3 or NRFIELD benchmark; stratified trapping and far-field transport are not modelled; every species welfare parameter is still a placeholder. None of this is legal advice or a substitute for a regulatory mixing-zone study, a §316 demonstration, a Fisheries Act authorisation or species-expert review. See `docs/VERIFICATION.md` for what must be done before any result leaves the team.

## Licences and citation

Code: Apache-2.0 (`LICENSE`). Policy text, docs and site text: CC BY 4.0. Schemas: CC0. Data: CC BY 4.0 (`LICENSE-docs.md`). Cite with `CITATION.cff`.
