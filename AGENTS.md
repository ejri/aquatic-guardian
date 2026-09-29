# Aquatic Guardian: brief for coding agents

## What this project is
A plug-in aquatic, ecological and animal-welfare module for data-centre regulation. It has four parts that must stay consistent:
1. **Policy** (`policy/`): framework, recommendations, model clauses for US, EU, Canada, international and UK instruments.
2. **Verified library** (`src/aquatic_guardian/`): screening physics, water quality, occupancy, imaging, tracking, bioenergetics, sentience reporting, disclosure and handoff records.
3. **Open-source packaging**: tests, schemas, data, CI, licences, citation, governance.
4. **Website and screening app** (`site/index.html`, built from `site/parts/` by `app/build.py`), presented as a Sentient Futures project.

Phase 1 was *Governing the Ocean Server Farm* (Elchami, Kaplan and Daher, Sentient Futures, April 2026), with a site at https://oceanic-datacenters-governance.netlify.app.

## Commands
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[test]"
pytest -q                      # must stay green; count only goes up
python app/build.py            # rebuild site and mirror schemas/data into the package
python app/build.py --check    # CI: fails if site or package resources are stale
```
Node 18+ is needed for `tests/test_engine_parity.py`.

## Single sources of truth (never duplicate these)
| Content | Only lives in |
|---|---|
| Model clauses | `policy/model-language/*.md`, between `<!-- clause: id -->` and `<!-- /clause -->` |
| Instrument tracker | `data/instruments.json` |
| Thresholds with sources | `data/criteria.json` |
| Screening logic | `src/aquatic_guardian/screening.py`, mirrored exactly in `app/engine.js` |
| Schemas | `schemas/*.json` (copied into the package by `app/build.py`) |
| Verification status | `docs/VERIFICATION.md` |

## Non-negotiable rules
- **Every equation has a test** that reproduces a published value (cite it in the test) or demonstrates the property on synthetic data with known truth. Add a row to `docs/VERIFICATION.md`.
- **Never loosen a tolerance to make a test pass.** Diagnose from the equations. If the physics is genuinely conditioned badly, document it and test the documented behaviour.
- **Engine parity**: any change to `screening.py` or modules it calls must be mirrored in `app/engine.js`; the parity test must pass.
- **No invented numbers.** Thresholds, coefficients, dates and legal citations come from a named source. If you cannot confirm one, mark it `placeholder` or `verify` and say so in your reply.
- **Legal status is explicit**: enacted law, proposed bill, guidance, consultation. Include the status date.
- **Screening, not permitting**: outputs are labelled as screening results. Nothing may tell a user a design "passes" using a placeholder value.
- **Sentience reporting never collapses to one score**; eggs and larvae stay separate rows.
- **Site**: one self-contained HTML file, no network requests except Google Fonts, WCAG 2.2 AA, works on a 390 px phone and in dark mode.
- **Plain language** in anything a member of the public or an official reads.

## Definition of done for any task
`pytest -q` green, `python app/build.py --check` green, `docs/VERIFICATION.md` and `CHANGELOG.md` updated, and a short note of anything that still needs a human expert.
