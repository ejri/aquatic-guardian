"""Headless browser test of the v1.0 site with external APIs stubbed.
Run: python tests/browser/test_site.py  (serves site/ on :8765)"""
import json, math, os, sys, threading, time, functools
from datetime import datetime, timedelta, timezone
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "site")
OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/shots"
os.makedirs(OUT, exist_ok=True)

def serve():
    h = functools.partial(SimpleHTTPRequestHandler, directory=ROOT)
    class Q(SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    h = functools.partial(Q, directory=ROOT)
    s = ThreadingHTTPServer(("127.0.0.1", 8765), h)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s

now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
hours = [now - timedelta(hours=24) + timedelta(hours=i) for i in range(72)]
MARINE = {"latitude": 16.1, "longitude": -86.9, "timezone": "America/Tegucigalpa",
          "current_units": {"ocean_current_velocity": "km/h"},
          "current": {"time": now.strftime("%Y-%m-%dT%H:%M"), "sea_surface_temperature": 29.4, "wave_height": 0.6,
                      "ocean_current_velocity": 0.9, "ocean_current_direction": 250, "sea_level_height_msl": 0.12},
          "hourly": {"time": [h.strftime("%Y-%m-%dT%H:%M") for h in hours],
                     "sea_surface_temperature": [29.4 + 0.2 * math.sin(i / 4) for i in range(72)],
                     "sea_level_height_msl": [0.25 * math.cos(2 * math.pi * i / 12.42) for i in range(72)],
                     "ocean_current_velocity": [0.4 + 0.8 * abs(math.cos(2 * math.pi * i / 12.42)) for i in range(72)],
                     "ocean_current_direction": [250] * 72, "wave_height": [0.6] * 72}}
CRW = {"table": {"columnNames": ["time", "latitude", "longitude", "CRW_DHW", "CRW_SST", "CRW_SSTANOMALY", "CRW_BAA_7D_MAX"],
                 "rows": [["2026-10-16T12:00:00Z", 16.075, -86.925, 5.2, 29.6, 1.1, 3]]}}
COOPS = {"predictions": [{"t": (now + timedelta(hours=i - 6)).strftime("%Y-%m-%d %H:%M"), "v": str(round(0.8 + 0.7 * math.cos(2 * math.pi * i / 12.42), 3))} for i in range(48)]}
YT_STUB = """window.YT={Player:function(id,o){var el=document.getElementById(id);var f=document.createElement('iframe');f.title='YouTube video player (stub)';f.src='about:blank';el.replaceWith(f);this.destroy=function(){f.remove();};}};
// Resolve on the next microtask so loadYT can register onYouTubeIframeAPIReady first.
Promise.resolve().then(function(){window.onYouTubeIframeAPIReady&&window.onYouTubeIframeAPIReady();});"""

def route(r):
    u = r.request.url
    if "/api/yt/status" in u:
        return r.fulfill(status=200, content_type="application/json", body='{"yt_dlp":false,"ok":true}')
    if "/api/yt/hls" in u:
        return r.fulfill(status=502, content_type="application/json", body='{"error":"stubbed"}')
    if u.startswith("http://127.0.0.1:8765"): return r.continue_()
    if "marine-api.open-meteo.com" in u: return r.fulfill(status=200, content_type="application/json", body=json.dumps(MARINE), headers={"Access-Control-Allow-Origin": "*"})
    if "coastwatch.pfeg.noaa.gov" in u or "pae-paha.pacioos.hawaii.edu" in u or "coastwatch.noaa.gov" in u:
        return r.fulfill(status=200, content_type="application/json", body=json.dumps(CRW), headers={"Access-Control-Allow-Origin": "*"})
    if "tidesandcurrents.noaa.gov" in u: return r.fulfill(status=200, content_type="application/json", body=json.dumps(COOPS if "predictions" in u else {"data": [{"t": "x", "v": "14.1"}]}), headers={"Access-Control-Allow-Origin": "*"})
    if "youtube.com/iframe_api" in u: return r.fulfill(status=200, content_type="text/javascript", body=YT_STUB)
    return r.abort()

FAILS = []
def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond: FAILS.append(msg)

def main():
  srv = serve()
  with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1440, "height": 1000})
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" and "net::ERR_FAILED" not in m.text and "Failed to load resource" not in m.text else None)
    page.route("**/*", route)

    page.goto("http://127.0.0.1:8765/index.html#/")
    page.wait_for_timeout(800)
    check(page.locator('nav.primary a[data-nav="observe"]').count() == 1, "nav has Live ocean")
    check(page.locator('nav.primary a[data-nav="learn"]').count() == 1, "nav has Learn")
    check(page.locator('a[href="#/observe"]').count() >= 1, "home links to Live ocean")
    check(page.locator('a[href="#/learn"]').count() >= 1, "home links to Learn")

    page.goto("http://127.0.0.1:8765/index.html#/observe")
    page.wait_for_function("document.querySelectorAll('#obs-markers .mk').length > 30", timeout=8000)
    n = page.locator("#obs-markers .mk").count()
    check(n >= 36, f"map markers drawn (got {n}; expect streams + sites)")
    g = page.locator("#obs-gallery .cam-card").count()
    check(g >= 20, f"camera gallery cards (got {g})")
    pins = page.locator("#obs-markers .mk.pin img").count()
    check(pins >= 15, f"map photo-pins with thumbnails (got {pins})")
    check(page.locator('#obs-regions .chip[data-region="se-asia"]').count() == 0, "empty regions hidden from chips")
    check(page.locator('#obs-regions .chip[data-region="aquaculture"]').count() == 0, "salmon-farms empty chip hidden")
    check(page.locator(".obs-research .res-card").count() == 3, "research desk has three tools")
    page.wait_for_function("document.querySelector('#obs-now .ro') !== null", timeout=8000)
    check("Utila" in page.inner_text("#obs-name"), "default station is Utila top of wall")
    page.wait_for_function("document.querySelector('#obs-yt') || document.querySelector('#obs-player iframe') || document.querySelector('#obs-video')", timeout=8000)
    check(page.evaluate("() => !!(document.querySelector('#obs-yt') || document.querySelector('#obs-player iframe') || document.querySelector('#obs-video'))"), "stream player mounted")
    check(page.locator("#vis-run").count() == 1 and page.locator("#vis-overlay").count() == 1, "detect button + overlay present")
    page.wait_for_function("document.querySelectorAll('#vis-model-pick option').length >= 4", timeout=8000)
    # option.innerText is empty while Detection model <details> is closed
    pick = page.evaluate("() => [...document.querySelectorAll('#vis-model-pick option')].map(o => o.value)")
    check("brackish-yolov8n" in pick, "picker lists Brackish")
    check("noaa-mouss-fish-yolov8n" in pick, "picker lists NOAA fish")
    check("noaa-urchin-yolo11n" in pick, "picker lists NOAA urchin")
    check("29.4" in page.inner_text("#obs-now"), "live SST shown from Open-Meteo")
    check("5.2" in page.inner_text("#obs-now"), "degree heating weeks shown")
    check(page.locator("#obs-deadline").is_visible() == (datetime.now(timezone.utc) < datetime(2026, 10, 19, 21, tzinfo=timezone.utc)), "FERC deadline banner visibility matches the date")
    page.screenshot(path=f"{OUT}/observe_top.png")

    page.click("#obs-tab-ocean"); page.wait_for_timeout(400)
    check("Alert level 1" in page.inner_text("#obs-p-ocean"), "bleaching alert label rendered")
    check(page.locator("#obs-tide-svg path").count() > 0, "tide chart drawn")
    page.locator("#obs-tabs").screenshot(path=f"{OUT}/tab_ocean.png")

    page.click("#obs-tab-heat"); page.wait_for_timeout(700)
    v = page.inner_text("#sc-verdict")
    check(len(v) > 10, "scenario verdict rendered: " + v[:90].replace("\n", " "))
    check(page.locator("#sc-tide .tidebar span").count() == 24, "24-phase tidal bar")
    check(page.locator("#sc-side path").count() > 2 and page.locator("#sc-decay path").count() > 0, "plume charts drawn")
    page.fill("#sc-it-mw", "120"); page.dispatch_event("#sc-it-mw", "input"); page.wait_for_timeout(500)
    check("120" in page.inner_text("#sc-it-mw-o"), "IT load slider updates")
    page.click("#sc-mc"); page.wait_for_function("document.querySelector('#sc-mc-out').textContent.indexOf('percentile') > 0", timeout=20000)
    check(True, "Monte Carlo completed: " + page.inner_text("#sc-mc-out")[:110])
    page.locator("#obs-tabs").screenshot(path=f"{OUT}/tab_heat.png")

    page.click("#obs-tab-animals"); page.wait_for_timeout(200)
    check("corals" in page.inner_text("#obs-animals").lower(), "animals tab lists corals at a reef")
    page.click("#obs-tab-rules"); page.wait_for_timeout(200)
    check("Not transcribed" in page.inner_text("#obs-rules"), "Honduras maps to no transcribed rule")

    # region filter
    page.click('#obs-regions [data-region="ne-pacific"]'); page.wait_for_timeout(900)
    dim = page.locator("#obs-markers .mk.dim").count()
    check(dim > 10, f"region filter dims other markers ({dim})")
    page.screenshot(path=f"{OUT}/observe_nepacific.png")

    # external stream + BC rules
    page.goto("http://127.0.0.1:8765/index.html#/observe/onc-folger"); page.wait_for_timeout(900)
    check(page.locator("#obs-player .facade").count() == 1, "external stream shows facade with link")
    page.click("#obs-tab-rules"); page.wait_for_timeout(200)
    check("British Columbia" in page.inner_text("#obs-rules"), "Folger Pinnacle maps to British Columbia")

    # ocean compute site
    page.goto("http://127.0.0.1:8765/index.html#/observe/eastport"); page.wait_for_timeout(1500)
    check(page.locator("#obs-site-note").is_visible() and "Western Passage" in page.inner_text("#obs-site-note"), "Eastport site note")
    check(page.get_attribute("#obs-tab-heat", "aria-selected") == "true", "site opens the data-centre tab")

    # vision pipeline on a synthetic stream of moving fish
    page.goto("http://127.0.0.1:8765/index.html#/observe/utila-top"); page.wait_for_timeout(1000)
    page.evaluate("""() => {
      const c = document.createElement('canvas'); c.width = 640; c.height = 360; const g = c.getContext('2d');
      let t = 0; const fish = Array.from({length: 7}, (_, i) => ({x: 60 + i * 70, y: 80 + (i % 3) * 80, vx: 3 + (i % 2), vy: Math.sin(i)}));
      setInterval(() => { t++; g.fillStyle = '#0a5a70'; g.fillRect(0, 0, 640, 360);
        g.fillStyle = '#e8d38a'; fish.forEach(f => { f.x = (f.x + f.vx + 640) % 640; f.y += 0.3 * Math.sin(t / 10 + f.vx); g.beginPath(); g.ellipse(f.x, f.y, 16, 7, 0, 0, 7); g.fill(); }); }, 33);
      const v = document.createElement('video'); v.muted = true; v.srcObject = c.captureStream(30);
      return v.play().then(() => { window.__src = {video: v, stream: null, cropped: true, kind: 'file'}; });
    }""")
    page.click("#obs-tab-vision")
    page.evaluate("""() => { const eng = new Vision.Engine({streamId: 'test', fps: 8});
      eng.attach(window.__src, document.getElementById('vis-overlay'), {boxesOnly: true});
      document.getElementById('obs-vis-out').hidden = false; window.__m = null; eng.start(m => { window.__m = m; }); window.__eng = eng; }""")
    page.wait_for_timeout(6000)
    m = page.evaluate("() => { const m = window.__m; return m && {count: m.count, speed: m.speed_bl_s, pol: m.polarization, vis: m.visibility, act: m.activity, fps: m.fps, err: m.error}; }")
    print("     vision metrics:", m)
    check(m and not m.get("err") and 5 <= m["count"] <= 9, "tracker follows the 7 synthetic fish")
    check(m and m["pol"] is not None and m["pol"] > 0.8, "aligned school gives high polarization")
    page.locator("#obs-player").screenshot(path=f"{OUT}/vision.png")
    page.evaluate("() => window.__eng.stop()")

    # tab-share crop must map the camera box, not the whole page (V-3)
    crop_tab = page.evaluate("""() => {
      const v = { videoWidth: 1280, videoHeight: 800 };
      const el = { getBoundingClientRect: () => ({ left: 100, top: 200, width: 640, height: 360 }) };
      const win = { innerWidth: 1280, innerHeight: 800, outerWidth: 1280, outerHeight: 800, devicePixelRatio: 1, screen: { width: 1280, height: 800 }, screenX: 0, screenY: 0 };
      return Vision.cropFromElement(v, el, win);
    }""")
    check(crop_tab and abs(crop_tab["x"] - 100) < 0.5 and abs(crop_tab["y"] - 200) < 0.5
          and abs(crop_tab["w"] - 640) < 0.5 and abs(crop_tab["h"] - 360) < 0.5,
          "tab capture crop is the player rectangle")
    crop_nonsquare = page.evaluate("""() => {
      const v = { videoWidth: 2000, videoHeight: 500 };
      const el = { getBoundingClientRect: () => ({ left: 100, top: 50, width: 400, height: 200 }) };
      const win = { innerWidth: 1000, innerHeight: 500, outerWidth: 1000, outerHeight: 500, devicePixelRatio: 1, screen: { width: 3000, height: 2000 }, screenX: 0, screenY: 0 };
      return Vision.cropFromElement(v, el, win);
    }""")
    check(crop_nonsquare and abs(crop_nonsquare["x"] - 200) < 0.5 and abs(crop_nonsquare["y"] - 50) < 0.5
          and abs(crop_nonsquare["w"] - 800) < 0.5 and abs(crop_nonsquare["h"] - 200) < 0.5,
          "crop uses separate x and y scales (does not run on the whole frame)")

    # learn tab (full coverage is tests/browser/test_learn.py)
    page.goto("http://127.0.0.1:8765/index.html#/learn")
    page.wait_for_function("document.querySelectorAll('#lc-map li').length === 9", timeout=8000)
    check(page.locator("#lc").count() == 1, "learn root #lc present")
    check(page.locator("#lc-map li").count() == 9, "nine course modules")
    page.screenshot(path=f"{OUT}/learn_top.png")

    # lab panel
    page.goto("http://127.0.0.1:8765/index.html#/lab/sim-plumes"); page.wait_for_timeout(1500)
    txt = page.text_content("#pl-txt") if page.locator("#pl-txt").count() else ""
    check("Plume surfaces" in txt and "Starting Farfield" in txt, "PLUMES text output generated")
    val = page.inner_text("#pl-val")
    check("169.754" in val, "validation table compares with EPA reference")
    print("     " + val.replace("\n", " | ")[:400])
    page.locator("#sim-plumes").screenshot(path=f"{OUT}/lab_plumes.png")
    page.select_option("#pl-preset", "dc"); page.wait_for_timeout(500)
    check("within" in page.text_content("#pl-txt") or "exceeds" in page.text_content("#pl-txt"), "data-centre preset screens against a rule")
    # existing lab still works
    check(page.locator("#ver-table tr").count() > 40, "verification table renders with new rows")
    check("P-6" in page.inner_text("#ver-table"), "verification has P-6")

    # mobile
    m2 = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2)
    mp = m2.new_page(); mp.route("**/*", route)
    mp.on("pageerror", lambda e: errors.append("mobile: " + str(e)))
    mp.goto("http://127.0.0.1:8765/index.html#/observe"); mp.wait_for_timeout(2500)
    over = mp.evaluate("() => document.documentElement.scrollWidth - window.innerWidth")
    check(over <= 0, f"no horizontal scroll at 390 px (overflow {over})")
    mp.screenshot(path=f"{OUT}/mobile_observe.png", full_page=False)
    mp.click("#obs-tab-heat"); mp.wait_for_timeout(600)
    over2 = mp.evaluate("() => document.documentElement.scrollWidth - window.innerWidth")
    check(over2 <= 0, f"heat tab fits at 390 px (overflow {over2})")
    mp.goto("http://127.0.0.1:8765/index.html#/learn"); mp.wait_for_timeout(1200)
    over3 = mp.evaluate("() => document.documentElement.scrollWidth - window.innerWidth")
    check(over3 <= 0, f"learn tab fits at 390 px (overflow {over3})")
    mp.screenshot(path=f"{OUT}/mobile_learn.png", full_page=False)

    check(not errors, "no page errors: " + "; ".join(errors[:5]))
    b.close()
  srv.shutdown()
  print(f"\n{len(FAILS)} failures")
  sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
  main()
