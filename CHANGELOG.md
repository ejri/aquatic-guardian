# Changelog

## Unreleased

- **Site**: header and footer use the Aquatic Guardian lockup, with a transparent background. The footer shows the full lockup, lined up with the citation. About places the Sentient Futures wordmark and the Aquatic Guardian emblem beside the opening line. “For industry” sits before “Learn” in the menu. “How to cite” opens `#/about/cite` (and the older `#/about#cite` form) and scrolls to the citation on About.
- **Tracker**: every instrument in `data/instruments.json` now has an opened
  primary-source URL (`verify: false`). SCIP status is applications closed
  (ISED, 1 June 2026); the AI Compute Challenge is still accepting applications.
  EnEfG status is “In force” (no draft amendment was confirmed). AB 93 veto
  consideration was stricken from file on 22 January 2026.
- **CI**: `verify` installs `pytest` for the relay job (it was missing, so the job exited 127).
  Checkout / setup-python / setup-node now use Node 24-compatible action majors; Node on the
  runner is 22.
- **Canada brief**: regenerated `briefs/canada.md` so it matches the BC Hydro Call for Power /
  Call for Demand row already in `data/instruments.json`.

- **Learn** (`#/learn`): rebuilt course route (tour, path finder, module pages, quizzes) from
  `learning_materials/learn-route/`. Classes are `lc-` and scoped to `[data-route="learn"]` so they
  no longer collide with site `.hero` / `.lab` / `.nb` / `.field`. The build mirrors `learn.css` /
  `learn.js` into `site/` and `--check` fails if they drift. Colab and GitHub buttons open
  [ejri/aquatic-guardian-learning-modules](https://github.com/ejri/aquatic-guardian-learning-modules).
  Tour and module cameras use real wildlife frames (live-camera stills plus NOAA public-domain
  turtle and humpback photographs) from `site/img/learn/`. Further-reading links that 403’d from
  publisher walls now use OpenCV’s GitHub tutorials, JSTOR for MacKenzie 2002, and the CSIRO
  author page for Khokher et al. 2021.

## 1.0.0 (2026-10-17)

- **Live stream + in-browser ML**: YouTube live cameras play as same-origin HLS (`/api/yt/hls` via yt-dlp in
  `scripts/dev_server.py`) into a `<video>` so ONNX YOLOv8n runs on the pixels; iframe fallback when HLS is
  unavailable. Detect draws boxes on the feed. Marketing ledes shortened. Stream registry refreshed
  (Monterey Bay deck id updated; Bonaire / Frying Pan / Anacapa / three AOP cams marked offline until new live ids).
- **Live ocean UI**: Full-bleed map with circular camera photo-pins; horizontal camera filmstrip; station tools
  (detect / ocean / heat) with live heat mini-verdict; heat controls collapsed by default; empty regions hidden.
- **Live feeds**: Full [explore.org Oceans](https://explore.org/livecams/oceans/) set wired in (Utopia wall + dock
  cams, Anacapa, Bonaire, Frying Pan Shark Cam, Catalina Wrigley, Homosassa manatees, Aquarium of the Pacific,
  OrcaLab/sea lion) with confirmed YouTube live ids; Coral City Camera; ONC schedules from
  [ONC Live Cameras](https://www.oceannetworks.ca/multimedia/live-cameras/) (Campbell River offline; Barkley Canyon
  Axis online; Cascadia, China Creek, Hartley Bay, Holyrood, Mothra).
- **Ocean data CORS**: same-origin Netlify `proxy` function + `scripts/dev_server.py` `/api/proxy` so Coral Reef
  Watch / CO-OPS / IWLS work without Fly when the browser blocks direct fetch.
- **Vision**: bundled Brackish YOLOv8n ONNX (`site/models/`) loads by default; class labels on tracks; catalogue
  lists Marine Detect and FathomNet/MBARI as next integrations.
- **Citations**: About → How to cite (Phase 2 Elchami + contributors; Phase 1 Elchami, Kaplan, Daher).
- **Tracker**: BC Hydro Call for Power EPAs awarded 13 May 2026; Call for Demand notifications delayed (sources linked).
- **Build / CI**: `app/build.py` applies `tools/integrate_v1.py` after the audience page so Live ocean and the
  PLUMES Lab panel survive rebuilds; CI covers plumes2py, JS/Python parity, relay, and the stubbed browser check;
  nightly `streams-health.yml` refreshes `site/data/streams.json`.
- **Live ocean** (`#/observe`): world map of 29 live underwater streams and 7 ocean data-centre sites; region
  filter; stream station with player, live conditions and five tabs (vision, ocean now, data-centre scenario,
  animals, rules). Deadline banner for FERC Project No. 15424 (closes 19 October 2026, 5:00 p.m. ET).
- **Vision**: in-browser tracking on a shared tab, a local file or relay detections; optional ONNX fish detector;
  behaviour and visibility metrics against each view's own baseline; low-visibility guard.
- **plumes2py**: Python rebuild of PLUMES 2.0 (UM3 + Brooks) with extended metrics, scenario builder, critical
  conditions, tidal cycle, Monte Carlo, tornado, PLUMES-format report, CLI. 53 tests.
- **plumes2.js**: browser mirror, parity-tested (1,500 values, 1e-7).
- **Lab**: "PLUMES 2.0, rebuilt" instrument with EPA reference overlay and validation table; near-field
  instrument now cites the benchmark; verification rows P-6 to P-9 and J-5.
- **Relay** (FastAPI): PLUMES endpoints, allow-listed ocean-data proxy, permission-gated vision workers.
- Oregon marine increment (OAR 340-041-0028(7), 0.3 °C) transcribed, marked for verification.
- Fixed in development: duplicate far-field rows when a mixing-zone boundary fell on an output interval; diffuser
  ports aimed against the current in the site's scenario builder.
