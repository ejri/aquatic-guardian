# Aquatic Guardian: brief for coding agents

## What this project is
A plug-in aquatic, ecological and animal-welfare module for data-centre regulation, presented as a Sentient Futures project. v1.0 adds a Live ocean route, a Python rebuild of EPA PLUMES 2.0, and an optional relay. Parts that must stay consistent:

1. **Policy** (`policy/`): framework, recommendations, model clauses.
2. **Verified library** (`src/aquatic_guardian/`): screening asymptotes, water quality, occupancy, imaging, tracking, bioenergetics, disclosure.
3. **PLUMES rebuild** (`python/plumes2py/`): UM3 near field + Brooks far field; mirrored in `site/js/plumes2.js`.
4. **Website** (`web/parts/` → `app/build.py` → `tools/integrate_v1.py` → `site/`): audience routes plus `#/observe`, `#/learn`, and Lab PLUMES instrument. `site/js/`, `site/css/`, `site/data/` are first-class publish assets.
5. **Relay** (`relay/`): optional FastAPI for PLUMES API, CORS proxy, permission-gated vision.

Phase 1: *Governing the Ocean Server Farm* (https://oceanic-datacenters-governance.netlify.app).

## Commands
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[test]"
pip install -e ./python
python app/build.py                 # rebuild site (audience parts + v1 integrate) and mirror package resources
python app/build.py --check         # CI: fails if site or package resources are stale
python app/briefs.py --check
python scripts/tracker_report.py
cd python && pytest -q              # plumes2py (~53 tests)
node tests/parity.test.mjs          # browser PLUMES vs Python (1,500 values)
pytest -q relay/tests               # needs: pip install -r relay/requirements.txt
python tests/browser/test_site.py /tmp/shots        # Chromium; APIs stubbed
python tests/browser/test_learn.py /tmp/learn-shots  # rebuilt #/learn route
python scripts/dev_server.py 8765   # site + /api/proxy (fixes Coral Reef Watch CORS locally)
```

## Single sources of truth (never duplicate these)
| Content | Only lives in |
|---|---|
| Model clauses | `policy/model-language/*.md` |
| Instrument tracker | `data/instruments.json` |
| Thresholds / jurisdictions | `data/criteria.json`, mirrored in `app/engine.js` |
| Website audience markup | `web/parts/*.html`; Live ocean / PLUMES Lab / Learn via `tools/integrate_v1.py` |
| Learn CV course | `learning_materials/learn-route/` (notebooks in `learning_materials/aquatic-guardian-learn-cv/`) |
| Lab notebook results | `app/notebook_results.py` → `data/notebook_results.json` |
| Lab sim kernels (legacy) | `app/sims.js` |
| PLUMES physics | `python/plumes2py/`, mirrored in `site/js/plumes2.js` |
| Stream registry | `site/data/streams.json` |
| Verification status | `docs/VERIFICATION.md` (+ `VALIDATION.md` for PLUMES rebuild detail) |
| Policy briefs | `app/briefs.py` → `briefs/` |

## Non-negotiable rules
- **Every equation has a test** (published value or known-truth synthetic). Add a row to `docs/VERIFICATION.md`.
- **Never loosen a tolerance to make a test pass.**
- **Engine parity**: changes to `screening.py` ↔ `app/engine.js`; changes to `plumes2py` ↔ `site/js/plumes2.js` (`tests/parity.test.mjs`).
- **No invented numbers.** Mark unconfirmed values `placeholder` / `verify`.
- **Legal status is explicit** with a status date.
- **Screening, not permitting.**
- **Sentience reporting never collapses to one score**; eggs and larvae stay separate.
- **Site**: WCAG 2.2 AA; works at 390 px and in dark mode. External APIs allowed for Live ocean (Open-Meteo, NOAA, DFO, YouTube embed) per `netlify.toml` CSP Report-Only. No analytics/trackers.
- **Plain language** for public and officials.

## Definition of done
`python app/build.py --check` green, `cd python && pytest -q` green, `node tests/parity.test.mjs` green, `docs/VERIFICATION.md` / `CHANGELOG.md` updated, and a note of anything a human expert still has to check.
