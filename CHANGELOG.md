# Changelog

## Unreleased

- **Public repo layout**: root brand PNG dumps moved to `docs/brand/`; Cursor prompt packs (`cursor/`, `Cursor_prompts.md`) removed from the public tree; `site/briefs/` ignored (canonical briefs stay in `briefs/`); README, CONTRIBUTING, CITATION.cff, SECURITY.md and Zenodo metadata refreshed for a public GitHub presentation; learning materials README cites EPA PLUMES 2.0.
- **Cite**: About → How to cite, the Lab PLUMES instrument, and Live ocean’s heat-model note now give the full EPA PLUMES 2.0 citation (US EPA 2024, EPA 600/B-24/339, https://www.epa.gov/hydrowq/PLUMES2). The Lab panel is refreshed on rebuild so that citation stays current.
- **Live ocean**: Detect runs on the camera pixels. A same-origin stream is read from the `<video>` element; a YouTube embed still needs a tab share, but that share is cropped to the player (Element Capture / Region Capture, then a viewport crop) so the model does not see the rest of the page. Boxes draw on the overlay only.
- **Live ocean detectors**: picker now includes NOAA MOUSS fish (YOLOv8n, grayscale) and NOAA sea urchin (YOLO11n) beside the Brackish default. All three are nano ONNX at 320 px. Marine Detect / FathomNet / Hakai kelp stay on the candidate list: the Marine Detect weights are YOLOv8l (~167 MB ONNX, over GitHub’s 100 MB file limit and much slower in the browser); Hakai kelp is aerial segmentation, not a live-camera box model. Export recipe in `scripts/export_vision_models.py`.
- **Site**: header and footer use the Aquatic Guardian lockup, with a transparent background. The footer shows the lockup with the citation and two link lists, using the same gold headings as the rest of the site. About places the Sentient Futures wordmark and the Aquatic Guardian emblem inside the opening section, beside that line. “For industry” sits before “Learn” in the menu. “How to cite” opens `#/about/cite` (and the older `#/about#cite` form) and scrolls to the citation on About. Shared layout now uses a gold text selection, a scroll hint on the mobile menu, a shorter home hero on small screens, clearer jump-link and button targets, and a visible 404 return button. The five home-page water numbers sit in equal columns across the page. The home-page system diagram gives each model its own box and keeps the arrow labels off the lines. Long instrument-status labels wrap inside their chips. “For researchers” is back in the header menu.
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
