# Aquatic Guardian

**A plug-in aquatic, ecological and animal-welfare module for data-centre regulation** — screening physics, policy model language, live ocean cameras, in-browser detection, and a Python rebuild of EPA PLUMES 2.0. A [Sentient Futures](https://oceanic-datacenters-governance.netlify.app) project.

| | |
|---|---|
| **Version** | 1.0.0 |
| **Code** | [Apache-2.0](LICENSE) |
| **Docs / text** | [CC BY 4.0](LICENSE-docs.md) (schemas [CC0](LICENSE-docs.md)) |
| **Repository** | [github.com/ejri/aquatic-guardian](https://github.com/ejri/aquatic-guardian) |
| **Phase 1 site** | [Governing the Ocean Server Farm](https://oceanic-datacenters-governance.netlify.app) |
| **Learn notebooks** | [ejri/aquatic-guardian-learning-modules](https://github.com/ejri/aquatic-guardian-learning-modules) |

Screening results are for scoping and public understanding. They are **not** a permit decision, legal advice, or a substitute for a mixing-zone study, a §316 demonstration, a Fisheries Act authorisation, or species-expert review.

## What you get

- **Website** (`site/`): audience routes (public, officials, Lab, industry), **Live ocean** (`#/observe`), **Learn** (`#/learn`), and the **PLUMES 2.0, rebuilt** Lab instrument.
- **Verified library** (`src/aquatic_guardian/`): thermal screening asymptotes, water quality, occupancy, imaging, tracking, bioenergetics, disclosure schemas.
- **PLUMES rebuild** (`python/plumes2py/`, mirrored in `site/js/plumes2.js`): UM3 near field + Brooks far field from the EPA manual, parity-tested.
- **Policy** (`policy/`): framework, recommendations, model clauses; briefs in `briefs/`.
- **Relay** (`relay/`, optional): FastAPI for PLUMES API, CORS proxy, permission-gated vision.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[test]"
pip install -e ./python
python app/build.py --check
python scripts/dev_server.py 8765
# open http://127.0.0.1:8765/#/observe  and  #/learn
```

Checks:

```bash
cd python && pytest -q                 # plumes2py (~53 tests)
node tests/parity.test.mjs             # browser PLUMES vs Python (1,500 values)
pytest -q                              # catalogue / tracker / vision catalogue
python tests/browser/test_site.py /tmp/shots   # Chromium; APIs stubbed
```

Publish directory for Netlify is `site/` (`netlify.toml`). Optional relay: see `relay/` and Deploy notes in older CHANGELOG entries.

## Repository map

| Path | Role |
|---|---|
| `web/parts/` → `app/build.py` → `tools/integrate_v1.py` → `site/` | Website source and publish tree |
| `web/assets/` | Logos used on the site (processed) |
| `docs/brand/` | Brand source masters (not embedded) |
| `site/js/`, `site/css/`, `site/data/`, `site/models/` | First-class publish assets (Live ocean, PLUMES, detectors) |
| `learning_materials/learn-route/` | Source for `#/learn` |
| `python/plumes2py/` | PLUMES 2.0 rebuild |
| `policy/`, `briefs/`, `data/instruments.json` | Model language, briefs, instrument tracker |
| `docs/VERIFICATION.md`, `VALIDATION.md` | What is checked, and PLUMES rebuild detail |
| `AGENTS.md` | Single sources of truth for contributors and coding agents |

Do not edit `site/*.html` by hand for audience copy — edit `web/parts/` and rebuild. Do not commit `site/briefs/` (generated; canonical briefs are under `briefs/`).

## How to cite

**This project**

```
Elchami, I., & Aquatic Guardian contributors. (2026). Aquatic Guardian: a plug-in aquatic, ecological and sentience module for data-centre regulation (Version 1.0.0) [Computer software]. Sentient Futures. https://github.com/ejri/aquatic-guardian
```

Machine-readable: [`CITATION.cff`](CITATION.cff).

**EPA PLUMES 2.0** (cite when you use the Lab rebuild or `plumes2py`)

```
US EPA. 2024. PLUMES2.0 – Dilution Model: Model Theory and User Manual. EPA 600/B-24/339. Office of Research and Development. https://www.epa.gov/hydrowq/PLUMES2
```

**Phase 1**

```
Elchami, I., Kaplan, Z., & Daher, C. (2026). Governing the Ocean Server Farm. Sentient Futures. https://oceanic-datacenters-governance.netlify.app
```

## Data and credits

Live cameras belong to their operators (explore.org, Monterey Bay Aquarium, Ocean Networks Canada, Coral Morphologic and others) and are credited on the page. Ocean data: Open-Meteo (CC BY 4.0), NOAA Coral Reef Watch and CO-OPS (US public domain), DFO IWLS (Open Government Licence – Canada). Map: Natural Earth (public domain). Bundled detectors: see `site/models/ATTRIBUTION.md`.

## Known limits

- Forced-entrainment scale (0.81) is fitted to one EPA case; run the 16-case benchmark before relying on it outside similar conditions (`VALIDATION.md`, `docs/VERIFICATION.md` P-3 / P-6).
- Vision metrics are behaviour indicators against each view’s own baseline, not welfare scores; placeholders need species literature or veterinary review.
- Data-centre scenarios are steady-state screening, not a permit decision.
- Stream ids change; regional coverage has gaps (`docs/STREAMS.md`).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md), [GOVERNANCE.md](GOVERNANCE.md), and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Coding agents: start with [AGENTS.md](AGENTS.md).
