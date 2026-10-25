# Aquatic Guardian v1.0

Live underwater cameras, live ocean conditions, computer vision, and a Python rebuild of the EPA's PLUMES 2.0,
added to the v0.2.1 site (a Sentient Futures project).

## What's in this release

| Path | What it is |
|---|---|
| `site/` | The deployable website: v0.2.1 plus **Live ocean** (`#/observe`), **Learn** (`#/learn`), and the **PLUMES 2.0, rebuilt** Lab instrument (`#/lab/sim-plumes`) |
| `site/js/learn.js` | Learn tab: tour, path finder, module pages and in-page demos |
| `site/css/learn.css` | Learn tab styles, scoped to `[data-route="learn"]` with `lc-` classes |
| `site/notebooks/` | Nine Colab notebooks for the Learn tab (copied from `learning_materials/` at build) |
| `learning_materials/learn-route/` | Learn tab source: `learn.html`, `learn.css`, `learn.js` |
| `site/js/plumes2.js` | Browser PLUMES engine, a parity-tested mirror of `plumes2py` |
| `site/js/observatory.js` | Live ocean page: map, player, tabs |
| `site/js/ocean-data.js` | Open-Meteo Marine, NOAA Coral Reef Watch (ERDDAP), NOAA CO-OPS, DFO IWLS clients |
| `site/js/vision.js` | Tab capture / file / relay vision, motion or ONNX detector, Kalman tracker, behaviour metrics |
| `site/js/plumes-lab.js` | Lab instrument with EPA reference overlay and PLUMES-format output |
| `site/data/streams.json` | 29 streams, 7 ocean data-centre sites, region gaps |
| `site/data/world.json` | Equal Earth world map from Natural Earth 1:110m (public domain), no tile server |
| `python/plumes2py/` | Python rebuild of PLUMES 2.0 with extended metrics and multi-run analyses |
| `relay/` | Optional FastAPI server: PLUMES API, allow-listed data proxy, permission-gated vision workers |
| `tools/integrate_v1.py` | Applies the v1.0 additions to a built v0.2.1 `index.html` (idempotent) |
| `VALIDATION.md` | How the rebuild matches PLUMES 2.0, and four discrepancies found in the EPA materials |
| `docs/STREAMS.md` | Stream rules, operator permission template, regional gaps, nightly checks |

## Run it locally

```bash
python scripts/dev_server.py 8765   # site + allow-listed /api/proxy (Coral Reef Watch etc.)
# then open http://127.0.0.1:8765/#/observe  and  #/learn
cd python && pip install -e . && python -m pytest -q      # 53 tests
node tests/parity.test.mjs                                # browser engine vs Python: 1,500 values
python -m pytest -q relay/tests                           # 7 tests (pip install -r relay/requirements.txt)
python tests/browser/test_site.py /tmp/shots              # headless Chromium, external APIs stubbed (pip install playwright)
python tests/browser/test_learn.py /tmp/learn-shots       # rebuilt #/learn route
```

## Deploy

**Website (Netlify).** Publish directory `site`, no build command (`netlify.toml` is included). It ships a
Content-Security-Policy in *Report-Only* mode: run it for a week, check the console for violations, then rename
the header to `Content-Security-Policy`.

**Your build pipeline.** `site/index.html` was produced by `tools/integrate_v1.py` from the built v0.2.1 page.
Port the blocks it inserts (they are plain strings at the top of the script) into your templates, or run the script
as a post-build step: `python tools/integrate_v1.py build/index.html site/index.html`. It stops with the anchor's
name if a template change moves an insertion point.

**Relay (optional).** Needed for: browsers whose CORS blocks a data source, the full Python engine, and
server-side vision on permitted streams.

```bash
fly launch --copy-config --dockerfile relay/Dockerfile      # from the repository root
fly secrets set ONC_TOKEN=...                               # optional, Ocean Networks Canada API
```

Then in `site/index.html` set `window.AG_RELAY = "https://ag-relay.fly.dev"` and add that origin
(`https://` and `wss://`) to `connect-src` in `netlify.toml`. Vision workers start only with `AG_RUN_WORKERS=1`
**and** a granted permission recorded in `relay/permitted_streams.json`.

**Nightly stream check.** Add a `YOUTUBE_API_KEY` repository secret; `.github/workflows/streams-health.yml`
opens a pull request when streams end or move.

## How the pieces fit

```
Live ocean page ─┬─ YouTube privacy-enhanced player / operator link (never pixel-read)
                 ├─ ocean-data.js ── Open-Meteo, Coral Reef Watch, CO-OPS, IWLS ──(blocked?)── relay /api/proxy
                 ├─ vision.js ── shared tab | local file | relay /ws/vision/{id} (permitted streams only)
                 └─ plumes2.js ── live SST + current → data-centre scenario → UM3 → Brooks → rule screening
Lab ──────────── plumes2.js on a PLUMES 2.0-style form, EPA reference overlay
python/plumes2py ── reference implementation; relay /api/plumes/* serves it
```

## Data and credits

Streams belong to their operators (explore.org, Monterey Bay Aquarium, Ocean Networks Canada, Coral Morphologic,
The MEGA Lab, Ocean Exploration Trust, Schmidt Ocean Institute, The Nature Conservancy Australia, James Cook
University, California Academy of Sciences and others) and are credited on the page. Ocean data: Open-Meteo
(CC BY 4.0), NOAA Coral Reef Watch and CO-OPS (US public domain), Fisheries and Oceans Canada (Open Government
Licence – Canada). Map: Natural Earth (public domain). Code Apache-2.0, text CC BY 4.0, as in v0.2.1.

## Known limits

- The forced-entrainment scale (0.81) is fitted to one EPA case; run the 16-case benchmark
  (`python/scripts/compare_plumes2.py --fit`) before relying on it outside similar conditions.
- Stream ids change; entries marked unverified were not confirmed live. Several regions have no verified stream.
- Vision metrics are behaviour indicators against each view's own baseline, not welfare scores; species
  thresholds marked as placeholders need species literature or veterinary review.
- The data-centre scenario is steady-state screening (one design current, no slack-water re-entrainment), not a
  permit decision. Pod mode is a screening approximation; UM3 is not designed for distributed hull heat.
- External APIs were stubbed in automated tests; check the live page against real responses after deploying.
