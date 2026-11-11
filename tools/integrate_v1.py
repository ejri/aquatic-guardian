"""Inject the v1.0 additions (Live ocean route, PLUMES 2.0 lab panel, new
verification rows) into a built v0.2.1 index.html.

    python tools/integrate_v1.py path/to/v0.2.1/index.html site/index.html

Idempotent: running it on an already-patched file changes nothing. Every
insertion is anchored on markup that exists in v0.2.1; a missing anchor stops
the script with the anchor's name, so template changes are caught.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEARN_SRC = ROOT / "learning_materials" / "learn-route" / "learn.html"
MARK = "<!-- aquatic-guardian v1.0 -->"
LEARN_MARK = "<!-- ================= LEARN CV ================= -->"
FONTS = ("https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700;800"
         "&family=Public+Sans:wght@400;500;600;700&family=Source+Serif+4:ital,wght@0,400;0,600;1,400&display=swap")

VISION_DETAILS = r'''          <details>
            <summary>Options</summary>
            <p class="small">Finds animals with a class-agnostic detector in the browser (RF-DETR Nano when available; otherwise motion). Labels map to 12 plain groups. Optional relay naming uses BioCLIP 2. Legacy Ultralytics YOLO weights are AGPL-3.0 — see site/models/ATTRIBUTION.md.</p>
            <label class="field"><input type="checkbox" id="vis-name-species" checked> Name species (sends small image crops to our server)</label>
            <label class="field">Detector<select id="vis-model-pick"><option value="rfdetr-nano">RF-DETR Nano (Apache-2.0, fish/animal)</option><option value="motion">Motion only (low-power)</option><option value="brackish-yolov8n">Legacy: Brackish YOLOv8n (AGPL-3.0)</option><option value="noaa-mouss-fish-yolov8n">Legacy: NOAA MOUSS fish (AGPL-3.0)</option><option value="noaa-urchin-yolo11n">Legacy: NOAA sea urchin (AGPL-3.0)</option></select></label>
            <label class="field">Or upload .onnx<input type="file" id="vis-model" accept=".onnx"></label>
            <label class="field">Input size<select id="vis-model-size"><option value="320" selected>320 px (fast)</option><option value="640">640 px (accurate)</option></select></label>
            <label class="field">Class names, comma separated<input type="text" id="vis-model-labels" value="animal"></label>
            <p class="small muted" id="vis-model-status">Loading detector…</p>
            <div id="vis-model-candidates"></div>
          </details>'''

OBSERVE = r'''
<!-- ================= LIVE OCEAN ================= -->
<div data-route="observe" class="deep">
  <section class="pagehead obs-head">
    <div class="wrap">
      <p class="kicker">Live ocean</p>
      <h1>Live underwater cameras</h1>
      <p class="lede">Ocean conditions and heat screening at the camera you open. Detection runs on-device on the feed.</p>
      <p class="obs-deadline" id="obs-deadline" hidden></p>
    </div>
  </section>

  <section class="obs-browse" aria-labelledby="obs-map-h">
    <div class="wrap">
      <h2 class="vh" id="obs-map-h">Choose a camera</h2>
      <div class="obs-map-stage">
        <div class="obs-mapbox" id="obs-map">
          <div class="obs-zoom">
            <svg id="obs-map-svg" role="img" aria-label="World map of live underwater cameras and ocean data-centre sites"></svg>
            <div id="obs-markers" class="obs-markers"></div>
          </div>
          <div class="obs-map-glow" aria-hidden="true"></div>
          <div class="obs-map-chrome">
            <span class="obs-map-title">Live cameras</span>
            <span class="obs-map-hint" id="obs-status" role="status"></span>
          </div>
        </div>
        <div class="obs-map-foot">
          <div class="obs-regions" id="obs-regions" role="group" aria-label="Filter by region"></div>
          <label class="obs-sites-lab"><input type="checkbox" id="obs-sites-toggle" checked> Data-centre sites</label>
        </div>
      </div>

      <div class="obs-film" aria-labelledby="obs-gal-h">
        <div class="obs-film-head">
          <h2 id="obs-gal-h">Cameras here</h2>
          <p id="obs-gal-count"></p>
        </div>
        <div class="obs-gallery" id="obs-gallery"></div>
      </div>
    </div>
  </section>

  <section class="obs-station" id="obs-station" hidden aria-labelledby="obs-name">
    <div class="wrap obs-station-inner">
      <div class="obs-cinema">
        <div class="obs-cinema-main">
          <div class="obs-player" id="obs-player">
            <div id="obs-media" class="obs-media"></div>
            <canvas id="vis-overlay" class="vis-overlay" aria-hidden="true"></canvas>
          </div>
          <div class="obs-detect-bar">
            <button type="button" class="btn glow sm" id="vis-run">Find animals</button>
            <button type="button" class="btn line sm" id="vis-stop" disabled hidden>Stop</button>
            <label class="vis-file-link">Use a video file<input type="file" id="vis-file" accept="video/*"></label>
            <p id="vis-msg" class="small muted" role="status">Finds and follows animals in the video. Boxes appear on the video.</p>
          </div>
          <p class="obs-credit" id="obs-credit"></p>
        </div>
        <aside class="obs-side" aria-label="This camera">
          <p class="obs-place-kicker" id="obs-place-kicker"></p>
          <h2 id="obs-name"></h2>
          <p class="obs-meta" id="obs-meta"></p>
          <p class="obs-species" id="obs-species"></p>
          <div class="obs-research" role="group" aria-label="Tools">
            <button type="button" class="res-card" id="res-detect" data-detect="1">
              <b>Find animals</b>
              <span>Boxes on this camera feed</span>
            </button>
            <button type="button" class="res-card" data-goto="obs-tab-ocean">
              <b>Conditions</b>
              <span>Temperature, current, heat stress</span>
            </button>
            <button type="button" class="res-card" data-goto="obs-tab-heat">
              <b>Heat screen</b>
              <span>Data-centre screening</span>
            </button>
          </div>
          <div class="obs-now-groups" id="obs-now" aria-live="polite"></div>
          <div class="obs-heat-mini callout" id="obs-heat-mini" hidden></div>
          <p class="obs-site-note" id="obs-site-note" hidden></p>
        </aside>
      </div>

      <div class="obs-tabs" id="obs-tabs">
        <div role="tablist" aria-label="Research at this place">
          <button type="button" role="tab" id="obs-tab-vision" aria-controls="obs-p-vision" aria-selected="true">Animals</button>
          <button type="button" role="tab" id="obs-tab-ocean" aria-controls="obs-p-ocean" aria-selected="false" tabindex="-1">Conditions</button>
          <button type="button" role="tab" id="obs-tab-heat" aria-controls="obs-p-heat" aria-selected="false" tabindex="-1">Heat screen</button>
          <button type="button" role="tab" id="obs-tab-animals" aria-controls="obs-p-animals" aria-selected="false" tabindex="-1">Species</button>
          <button type="button" role="tab" id="obs-tab-rules" aria-controls="obs-p-rules" aria-selected="false" tabindex="-1">Rules</button>
        </div>

        <div role="tabpanel" id="obs-p-vision" aria-labelledby="obs-tab-vision" tabindex="0">
          <p class="obs-lede">Finds and follows animals in the video. Boxes appear on the video above.</p>
          <div id="obs-vis-out" hidden>
            <div class="vis-grid">
              <div><div class="readouts" id="vis-ro"></div><ul class="obs-flags" id="vis-flags" aria-live="polite"></ul><p class="small muted" id="vis-src"></p><p class="vis-summary" id="vis-summary"></p></div>
              <div><svg id="vis-chart" viewBox="0 0 640 200" role="img" aria-label="Animals in view over time"></svg><p class="small muted">Animals in view (last minutes).</p></div>
            </div>
            <p class="small"><a href="#vis-how-sure" id="vis-how-sure-link">How sure is this?</a></p>
            <div id="vis-how-sure" class="small muted" hidden>
              <p>The detector finds animals it can resolve on this camera. It misses animals that are tiny, murky, or night-dark. A count is not a population estimate.</p>
            </div>
          </div>
''' + VISION_DETAILS + r'''
          <details>
            <summary>Limits</summary>
            <p class="small">Behaviour indicators, not welfare scores. Low visibility (&lt;25/100) makes counts unreliable. If the feed is a YouTube embed, your browser will ask to share this tab so the detector can see the video — choose <b>This tab</b>. Screening only.</p>
          </details>
        </div>

        <div role="tabpanel" id="obs-p-ocean" aria-labelledby="obs-tab-ocean" tabindex="0" hidden>
          <div id="obs-ocean"></div>
        </div>

        <div role="tabpanel" id="obs-p-heat" aria-labelledby="obs-tab-heat" tabindex="0" hidden>
          <p class="obs-lede">If a seawater-cooled data centre were built at this camera, using today's water. Warming at the mixing-zone edge is checked against a named rule only where one applies. Screening only — not a permit.</p>
          <div class="sc-grid">
            <div class="sc-ctrl">
              <div class="ctl"><label for="sc-it-mw">IT load <output id="sc-it-mw-o"></output></label><input type="range" id="sc-it-mw" min="0.5" max="200" step="0.5" value="24" data-u="MW"></div>
              <div class="ctl"><label for="sc-delta-t-k">Cooling-water rise <output id="sc-delta-t-k-o"></output></label><input type="range" id="sc-delta-t-k" min="1" max="15" step="0.5" value="8" data-u="°C"></div>
              <div class="ctl"><label for="sc-rule">Screening rule</label><select id="sc-rule"><option value="custom" selected>No limit set for this location</option><option value="wa_marine">Washington, WAC 173-201A-210</option><option value="ca_new_coastal">California coast, Thermal Plan</option><option value="ca_enclosed_bay">California enclosed bay, Thermal Plan</option><option value="or_marine">Oregon, OAR 340-041-0028(7)</option></select></div>
              <div class="ctl"><label for="sc-mode">Design</label><select id="sc-mode"><option value="outfall">Pumped outfall with diffuser</option><option value="pod">Submerged pod, passive hull cooling (screening only)</option></select></div>
              <details class="sc-more">
                <summary>More design and water inputs</summary>
                <div class="ctl"><label for="sc-pue">PUE <output id="sc-pue-o"></output></label><input type="range" id="sc-pue" min="1.03" max="2" step="0.01" value="1.15"></div>
                <div class="ctl"><label for="sc-reuse">Heat recovered before discharge <output id="sc-reuse-o"></output></label><input type="range" id="sc-reuse" min="0" max="90" step="1" value="0" data-u="%"></div>
                <div class="ctl"><label for="sc-n-ports">Diffuser ports <output id="sc-n-ports-o"></output></label><input type="range" id="sc-n-ports" min="1" max="40" step="1" value="4"></div>
                <div class="ctl"><label for="sc-spacing">Port spacing <output id="sc-spacing-o"></output></label><input type="range" id="sc-spacing" min="1" max="40" step="0.5" value="8" data-u="m"></div>
                <div class="ctl"><label for="sc-port-depth">Port depth <output id="sc-port-depth-o"></output></label><input type="range" id="sc-port-depth" min="4" max="60" step="1" value="15" data-u="m"></div>
                <div class="ctl"><label for="sc-sst">Water temperature (live) <output id="sc-sst-o"></output></label><input type="range" id="sc-sst" min="-2" max="33" step="0.1" value="12" data-u="°C"></div>
                <div class="ctl"><label for="sc-current">Current (live) <output id="sc-current-o"></output></label><input type="range" id="sc-current" min="0.01" max="1.5" step="0.01" value="0.1" data-u="m/s"></div>
                <div class="ctl"><label for="sc-salinity">Salinity <output id="sc-salinity-o"></output></label><input type="range" id="sc-salinity" min="0" max="42" step="0.1" value="32" data-u="psu"></div>
                <div class="ctl"><label for="sc-chronic">Mixing-zone radius <output id="sc-chronic-o"></output></label><input type="range" id="sc-chronic" min="20" max="1000" step="10" value="300" data-u="m"></div>
              </details>
            </div>
            <div>
              <div id="sc-verdict" class="verdict" aria-live="polite"></div>
              <div class="readouts" id="sc-ro"></div>
              <div class="sc-charts">
                <figure><svg id="sc-side" viewBox="0 0 640 260" role="img" aria-label="Side view of the plume rising from the outfall"></svg><figcaption>Side view of one port's plume.</figcaption></figure>
                <figure><svg id="sc-decay" viewBox="0 0 640 260" role="img" aria-label="Warming above ambient against distance"></svg><figcaption>Warming above ambient; mixing-zone edge marked.</figcaption></figure>
              </div>
              <h4>Through a tidal cycle</h4>
              <div id="sc-tide"></div>
              <ul class="flags" id="sc-checks"></ul>
              <div class="row" style="margin-top:1rem">
                <button type="button" class="btn line sm" id="sc-mc">Run 80 uncertainty scenarios</button>
                <button type="button" class="btn line sm" id="sc-lab">Open full model in Lab</button>
                <button type="button" class="btn line sm" id="sc-json">Download scenario</button>
              </div>
              <p class="small" id="sc-mc-out" aria-live="polite"></p>
              <p class="small muted" id="sc-msg" role="status"></p>
            </div>
          </div>
        </div>

        <div role="tabpanel" id="obs-p-animals" aria-labelledby="obs-tab-animals" tabindex="0" hidden><div id="obs-animals"></div></div>
        <div role="tabpanel" id="obs-p-rules" aria-labelledby="obs-tab-rules" tabindex="0" hidden><div id="obs-rules"></div></div>
      </div>
    </div>
  </section>

  <section class="obs-method" aria-labelledby="obs-method-h">
    <div class="wrap">
      <h2 id="obs-method-h">How this page works</h2>
      <div class="cols">
        <div><h3>Streams</h3><p>Many open-ocean cams come from <a href="https://explore.org/livecams/oceans/" rel="noopener">explore.org Oceans</a> and play here through YouTube's privacy-enhanced player. Others keep their own players. Aquariums, surface views and scheduled clips are labelled. Some streams move to new links. We check nightly. If a camera fails, pick another.</p></div>
        <div><h3>Ocean data</h3><p>Sea temperature, currents and sea level come from Open-Meteo Marine. Heat stress comes from NOAA Coral Reef Watch. Tide predictions come from NOAA CO-OPS and Fisheries and Oceans Canada. Nothing loads until you open this page.</p></div>
        <div><h3>Heat model</h3><p>The EPA’s PLUMES 2.0 near- and far-field mixing (<a href="https://www.epa.gov/hydrowq/PLUMES2" rel="noopener">EPA 600/B-24/339</a>), rebuilt so it runs in the browser. Full controls and verification live in the <a href="#/lab/sim-plumes">Lab</a>.</p></div>
        <div><h3>What it is not</h3><p>Screening, not a permit decision. Species thresholds marked as placeholders need literature or veterinary input before they are relied on.</p></div>
      </div>
    </div>
  </section>
</div>
'''

PLUMES_LAB = r'''
            <div class="inst" id="sim-plumes">
              <div class="inst-head"><h3>PLUMES 2.0, rebuilt in Python and running here</h3><span class="tag">UM3 near field and Brooks far field from US EPA (2024) EPA 600/B-24/339; checked against the EPA's Example_project output; browser copy parity-tested</span></div>
              <div class="inst-body">
                <div class="inst-view">
                  <svg id="pl-traj" viewBox="0 0 720 300" style="width:100%;height:auto;display:block;background:#021017;border-radius:8px" role="img" aria-label="Plume trajectory in side view, with the EPA reference points when the example is loaded"></svg>
                  <div class="readouts" id="pl-ro"></div>
                  <svg id="pl-recon" viewBox="0 0 720 260" style="width:100%;height:auto;display:block;background:#021017;border-radius:8px;margin-top:1rem" role="img" aria-label="Dilution and warming from the port through the far field on one curve"></svg>
                  <p class="small muted" style="margin-top:.4rem">Near field to far field on one curve: flux-averaged dilution (gold) and centreline dilution (blue) along the plume, then Brooks' far-field dilution from where the plume stops rising, with the mixing-zone edges marked.</p>
                  <table class="pl-val" id="pl-val"></table>
                  <details style="margin-top:1rem"><summary>Output in the PLUMES 2.0 text layout</summary><pre class="json" id="pl-txt" tabindex="0" style="max-height:26rem"></pre></details>
                </div>
                <div class="inst-ctrl">
                  <form class="pl-form" id="pl-form" onsubmit="return false">
                    <label class="wide">Start from<select id="pl-preset"><option value="epa">EPA Example_project (reference)</option><option value="dc">24 MW seawater-cooled data centre</option></select></label>
                    <h5>Diffuser</h5>
                    <label>Port diameter (m)<input id="pl-port_diameter" type="number" step="any"></label>
                    <label>Port elevation (m)<input id="pl-port_elevation" type="number" step="any"></label>
                    <label>Vertical angle (°)<input id="pl-vertical_angle" type="number" step="any"></label>
                    <label>Horizontal angle (°)<input id="pl-horizontal_angle" type="number" step="any"></label>
                    <label>Ports<input id="pl-n_ports" type="number" step="1" min="1"></label>
                    <label>Spacing (m)<input id="pl-spacing" type="number" step="any"></label>
                    <label>Port depth (m)<input id="pl-port_depth" type="number" step="any"></label>
                    <label>Contraction<input id="pl-contraction" type="number" step="any"></label>
                    <h5>Effluent</h5>
                    <label>Flow (m³/s)<input id="pl-flow" type="number" step="any"></label>
                    <label>Salinity (psu)<input id="pl-salinity" type="number" step="any"></label>
                    <label>Temperature (°C)<input id="pl-temperature" type="number" step="any"></label>
                    <label>Pollutant (mg/L)<input id="pl-concentration" type="number" step="any"></label>
                    <h5>Mixing zones (m)</h5>
                    <label>Acute<input id="pl-acute" type="number" step="any"></label>
                    <label>Chronic<input id="pl-chronic" type="number" step="any"></label>
                    <label class="wide">Ambient profile: depth, current, direction, salinity, temperature, far-field current, Brooks alpha<textarea id="pl-ambient" spellcheck="false"></textarea></label>
                    <h5>Run settings</h5>
                    <label>Far-field law<select id="pl-farfield_case"><option value="four_thirds">4/3 power (open ocean)</option><option value="linear">Linear (estuary)</option><option value="constant">Constant (channel)</option></select></label>
                    <label>Stop near field at<select id="pl-max_rise_fall"><option value="0">First trap level</option><option value="1">Maximum rise</option><option value="2">Second trap level</option><option value="3">Maximum fall</option></select></label>
                    <label>Aspiration coefficient<input id="pl-aspiration" type="number" step="any"></label>
                    <label>Forced-entrainment scale<input id="pl-forced_scale" type="number" step="any"></label>
                    <label class="wide">Rule<select id="pl-rule"><option value="">None</option><option value="wa_marine">Washington</option><option value="ca_new_coastal">California coast</option><option value="or_marine">Oregon ocean and bays</option></select></label>
                  </form>
                  <div class="pl-actions"><button type="button" class="btn glow sm" id="pl-run">Run model</button><button type="button" class="btn line sm" id="pl-dl-txt">Download text</button><button type="button" class="btn line sm" id="pl-dl-json">Download scenario</button></div>
                  <p class="small muted" id="pl-msg" role="status" style="margin-top:.6rem"></p>
                </div>
              </div>
              <p class="finding"><b>What the rebuild found.</b> PLUMES 2.0's Fortran source is not public, so the model was rebuilt from the manual and checked against the EPA's shipped example. The first 25 steps match to three decimals; along the whole plume dilution is within 2.9 % and the surfacing point within 1.2 %, with one forced-entrainment scale (0.81) fitted to that single case, to be confirmed with the 16-case benchmark kit. Three discrepancies in the EPA materials: the example effluent is 2.63 °C in the shipped files but 26.3 °C in the manual text; manual eq. 11 doubles the case-2 width growth that eq. 15 and the derivation imply; and the manual's table and the shipped program start the far field at different distances (about 7.2 m against 4.4 m).</p>
              <p class="small muted">Source: US EPA. 2024. <i>PLUMES2.0 – Dilution Model: Model Theory and User Manual</i>. EPA 600/B-24/339. Office of Research and Development. <a href="https://www.epa.gov/hydrowq/PLUMES2" rel="noopener">https://www.epa.gov/hydrowq/PLUMES2</a>. Cite this document when you use this instrument; see also <a href="#/about/cite">How to cite</a>.</p>
            </div>
'''

VER_ROWS = [
    ["P-6", "UM3 near field rebuilt in Python (plumes2py)", "EPA Example_project: steps 5-25 to 0.002; trajectory RMS 2.9 %; surfacing dilution 169.5 vs 169.75, diameter, x, y, depth within 1.2 %", "Published value (one case); forced-entrainment scale fitted, needs 16-case benchmark"],
    ["P-7", "Brooks far field, three cases", "Manual Fig. 14 independent far field reproduced to 0.006 in every row; Fig. 12 to 0.1 %", "Published value"],
    ["P-8", "Manual discrepancies", "Example effluent 2.63 C (files) vs 26.3 C (text); eq. 11 factor 2; far-field origin 7.2 m (manual) vs 4.4 m (program)", "Needs outside check (report to EPA/SSMC)"],
    ["P-9", "Merged plumes cannot out-dilute isolated ones (UM3)", "Property test over port spacing 0.5-8 m", "Simulation"],
    ["J-5", "Browser PLUMES engine (site/js/plumes2.js)", "9 scenarios, 1,500 values, rel. tol. 1e-7 against plumes2py", "Parity"],
]


def _refresh_vision_panel(html: str) -> str:
    """Swap the vision model <details> even on an already-patched page."""
    new, n = re.subn(
        r"<details(?:\s+open)?\s*>\s*<summary>Use a fish detector instead of motion</summary>.*?</details>"
        r"|<details(?:\s+open)?\s*>\s*<summary>Detection model(?: \(bundled \+ optional upload\))?</summary>.*?</details>"
        r"|<details(?:\s+open)?\s*>\s*<summary>Options</summary>.*?</details>",
        VISION_DETAILS,
        html,
        count=1,
        flags=re.S,
    )
    return new if n else html


def learn_route() -> str:
    """Insert learning_materials/learn-route/learn.html as the #/learn route."""
    if not LEARN_SRC.is_file():
        raise SystemExit("anchor not found: learning_materials/learn-route/learn.html")
    raw = LEARN_SRC.read_text(encoding="utf-8")
    if 'data-route="learn"' not in raw or LEARN_MARK not in raw:
        raise SystemExit("anchor not found: data-route=learn in learning_materials/learn-route/learn.html")
    if 'class="on"' in raw.split('data-route="learn"', 1)[1][:80]:
        raise SystemExit("learn route must not hardcode class=on; the router sets that")
    return "\n" + raw.strip() + "\n"


def _replace_route_block(html: str, mark: str, route: str, block: str) -> str:
    start = html.find(mark)
    if start < 0:
        start = html.find(f'<div data-route="{route}"')
        if start < 0:
            return ""
    open_at = html.find(f'<div data-route="{route}"', start)
    if open_at < 0:
        return ""
    i, depth = open_at, 0
    while i < len(html):
        if html.startswith("</div>", i):
            depth -= 1
            i += 6
            if depth == 0:
                end = i
                while end < len(html) and html[end] in " \t\r\n":
                    end += 1
                return html[:start] + block.strip() + "\n" + html[end:]
            continue
        if html.startswith("<div", i) and (i + 4 == len(html) or html[i + 4] in " \t\r\n>"):
            depth += 1
            i += 4
            continue
        i += 1
    return ""


def _refresh_learn(html: str) -> str:
    """Replace or insert the Learn route so lesson edits ship on rebuild."""
    block = learn_route()
    replaced = _replace_route_block(html, LEARN_MARK, "learn", block)
    if replaced:
        return replaced
    if "</main>" not in html:
        return html
    return html.replace("</main>", block + "\n</main>", 1)


def _ensure_learn_assets(html: str) -> str:
    if 'href="css/learn.css"' not in html:
        if 'href="css/observe.css">' in html:
            html = html.replace(
                'href="css/observe.css">',
                'href="css/observe.css">\n<link rel="stylesheet" href="css/learn.css">',
                1,
            )
        else:
            html = html.replace("</head>", '<link rel="stylesheet" href="css/learn.css">\n</head>', 1)
    if 'src="js/learn.js"' not in html:
        if '<script src="js/plumes-lab.js"></script>' in html:
            html = html.replace(
                '<script src="js/plumes-lab.js"></script>',
                '<script src="js/plumes-lab.js"></script>\n<script src="js/learn.js"></script>',
                1,
            )
        else:
            html = html.replace(
                "<script>window.AGU.start();</script>",
                '<script src="js/learn.js"></script>\n<script>window.AGU.start();</script>',
                1,
            )
    if 'learn: "Learn computer vision' not in html:
        if 'observe: "Live ocean · Aquatic Guardian",' in html:
            html = html.replace(
                'observe: "Live ocean · Aquatic Guardian",',
                'observe: "Live ocean · Aquatic Guardian", learn: "Learn computer vision · Aquatic Guardian",',
                1,
            )
        else:
            html = html.replace(
                'about: "About · Aquatic Guardian"',
                'about: "About · Aquatic Guardian", learn: "Learn computer vision · Aquatic Guardian"',
                1,
            )
    if 'data-nav="learn"' not in html and 'data-nav="observe"' in html:
        html = html.replace(
            '<a href="#/observe" data-nav="observe" class="nav-live">Live ocean</a>',
            '<a href="#/observe" data-nav="observe" class="nav-live">Live ocean</a>\n'
            '      <a href="#/learn" data-nav="learn">Learn</a>',
            1,
        )
    return html


def _replace_div_by_id(html: str, div_id: str, replacement: str) -> str:
    """Replace the outermost <div id="…">…</div> with replacement (keeps surrounding whitespace)."""
    needle = f'<div class="inst" id="{div_id}"' if div_id == "sim-plumes" else f'<div id="{div_id}"'
    open_at = html.find(needle)
    if open_at < 0 and div_id == "sim-plumes":
        open_at = html.find(f'<div id="{div_id}"')
    if open_at < 0:
        return html
    i, depth = open_at, 0
    while i < len(html):
        if html.startswith("</div>", i):
            depth -= 1
            i += 6
            if depth == 0:
                return html[:open_at] + replacement.strip() + html[i:]
            continue
        if html.startswith("<div", i) and (i + 4 == len(html) or html[i + 4] in " \t\r\n>"):
            depth += 1
            i += 4
            continue
        i += 1
    return html


def _refresh_observe(html: str) -> str:
    """Replace the Live ocean route block so layout edits ship on re-integrate."""
    mark = "<!-- ================= LIVE OCEAN ================= -->"
    start = html.find(mark)
    if start < 0:
        start = html.find('<div data-route="observe"')
        if start < 0:
            return html
    open_at = html.find('<div data-route="observe"', start)
    if open_at < 0:
        return html
    i, depth = open_at, 0
    while i < len(html):
        if html.startswith("</div>", i):
            depth -= 1
            i += 6
            if depth == 0:
                end = i
                while end < len(html) and html[end] in " \t\r\n":
                    end += 1
                return html[:start] + OBSERVE.strip() + "\n" + html[end:]
            continue
        if html.startswith("<div", i) and (i + 4 == len(html) or html[i + 4] in " \t\r\n>"):
            depth += 1
            i += 4
            continue
        i += 1
    return html


def _refresh_plumes_lab(html: str) -> str:
    """Replace the Lab PLUMES instrument so citation and copy edits ship on re-integrate."""
    if 'id="sim-plumes"' not in html:
        return html
    return _replace_div_by_id(html, "sim-plumes", PLUMES_LAB)


def patch(html: str) -> str:
    """Return html with Live ocean + PLUMES Lab + Learn layered on. Idempotent when MARK is present."""
    if MARK in html:
        html = _refresh_vision_panel(_refresh_observe(html))
        html = _refresh_plumes_lab(html)
        html = _ensure_learn_assets(_refresh_learn(html))
        return html

    def sub(pattern, repl, name, count=1, flags=0):
        nonlocal html
        new, n = re.subn(pattern, repl, html, count=count, flags=flags)
        if n == 0:
            raise SystemExit(f"anchor not found: {name}")
        html = new

    # Saved-page offline font CSS -> live Google Fonts. Skip if the live link is already there.
    if "fonts.googleapis.com/css2?" not in html:
        sub(
            r'<link href="[^"]*css2_[^"]*\.css" rel="stylesheet">',
            f'<link href="{FONTS}" rel="stylesheet">',
            "fonts link",
        )
    # Netlify injects its own badge at serve time; it is not part of the source
    html = re.sub(r'<!-- This site is hosted on Netlify.*?-->\s*', "", html, flags=re.S)
    html = re.sub(r'<script async="" src="[^"]*hud_[^"]*"[^>]*></script>\s*', "", html)
    html = re.sub(r'<iframe id="nl-badge-frame".*?</iframe>\s*', "", html, flags=re.S)
    if 'href="css/observe.css"' not in html:
        sub(r"</head>", f'<link rel="stylesheet" href="css/observe.css">\n<link rel="stylesheet" href="css/learn.css">\n{MARK}\n</head>', "head end")
    else:
        sub(r"</head>", f"{MARK}\n</head>", "head end")
        if 'href="css/learn.css"' not in html:
            html = html.replace('href="css/observe.css">', 'href="css/observe.css">\n<link rel="stylesheet" href="css/learn.css">', 1)
    # Drop a prior MapLibre CDN inject if re-running integrate on a patched file
    html = re.sub(
        r'\n?<link rel="stylesheet" href="https://cdn\.jsdelivr\.net/npm/maplibre-gl[^"]*" crossorigin="anonymous">',
        "",
        html,
    )
    html = re.sub(
        r'\n?<script src="https://cdn\.jsdelivr\.net/npm/maplibre-gl[^"]*" crossorigin="anonymous"></script>\n?',
        "\n",
        html,
    )
    if 'data-nav="observe"' not in html:
        sub(r'(<nav class="primary" aria-label="Audiences">\s*)', r'\1<a href="#/observe" data-nav="observe" class="nav-live">Live ocean</a>\n      <a href="#/learn" data-nav="learn">Learn</a>\n      ', "primary nav")
    if 'href="#/observe">Live ocean</a>' not in html and 'href="#/observe">Open</a>' not in html:
        sub(r'(<a class="btn line" href="#/lab">Run the simulations</a>)', r'\1\n        <a class="btn line" href="#/observe">Live ocean</a>', "hero buttons")
    sub(r"</main>", OBSERVE + learn_route() + "\n</main>", "main end")
    sub(r'(<a href="#/lab/sim-margin">Safety margin</a>)', r'\1<a href="#/lab/sim-plumes">PLUMES 2.0 rebuilt</a>', "lab index")
    sub(r'(\s*<div class="reported"><h4>Handoff sent to the other two notebooks)', PLUMES_LAB + r"\1", "thermal handoff")
    sub(r"PLUMES 2\.0 benchmark pending", "benchmarked against the PLUMES 2.0 rebuild below", "sim-near tag")
    if 'observe: "Live ocean · Aquatic Guardian"' not in html:
        sub(r'(industry: "Design and disclosure · Aquatic Guardian",)', r'\1 observe: "Live ocean · Aquatic Guardian", learn: "Learn computer vision · Aquatic Guardian",', "titles")
    elif 'learn: "Learn computer vision' not in html:
        sub(r'(observe: "Live ocean · Aquatic Guardian",)', r'\1 learn: "Learn computer vision · Aquatic Guardian",', "titles")
    rows = ", ".join(json.dumps(r, ensure_ascii=False) for r in VER_ROWS)
    sub(r'("verification": \[)', r"\1" + rows.replace("\\", "\\\\") + ", ", "verification rows")
    sub(r'(<pre class="json">!pip -q install)', '<pre class="json">!pip -q install "git+https://github.com/ejri/aquatic-guardian.git@v1.0.0#subdirectory=python"\n'
        'from plumes2py import reference_example, run\nres = run(reference_example(), rule="wa_marine")   # PLUMES 2.0 rebuild</pre>\n          '
        r"\1", "use-the-code block")
    scripts = ('<script>window.AG_RELAY = window.AG_RELAY || null; /* e.g. "https://ag-relay.fly.dev" once relay/ is deployed */</script>\n'
               '<script src="js/plumes2.js"></script>\n<script src="js/ocean-data.js"></script>\n<script src="js/vision.js"></script>\n'
               '<script src="js/observatory.js"></script>\n<script src="js/plumes-lab.js"></script>\n<script src="js/learn.js"></script>\n')
    sub(r"(<script>window\.AGU\.start\(\);</script>)", scripts + r"\1", "start call")
    return html


def main(src: str, dst: str) -> None:
    html = Path(src).read_text(encoding="utf-8")
    out = patch(html)
    Path(dst).write_text(out, encoding="utf-8")
    if MARK in html and out == html:
        print("already v1.0; unchanged")
    elif MARK in html:
        print(f"refreshed v1.0 panel in {dst} ({len(out):,} bytes)")
    else:
        print(f"wrote {dst} ({len(out):,} bytes)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
