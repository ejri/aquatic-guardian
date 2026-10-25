"""Headless browser test of the rebuilt #/learn route.
Run: python tests/browser/test_learn.py [out_dir]
Serves site/ on :8766 so it can run beside the main site test."""
import json, os, sys, threading, functools
from datetime import datetime, timedelta, timezone
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "site")
OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/learn-shots"
os.makedirs(OUT, exist_ok=True)
PORT = 8766
BASE = f"http://127.0.0.1:{PORT}/index.html"
KEYS = ["agl-path", "agl-done", "agl-quiz"]


def serve():
    class Q(SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    h = functools.partial(Q, directory=ROOT)
    s = ThreadingHTTPServer(("127.0.0.1", PORT), h)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
hours = [now - timedelta(hours=24) + timedelta(hours=i) for i in range(72)]
MARINE = {"latitude": 16.1, "longitude": -86.9, "timezone": "America/Tegucigalpa",
          "current_units": {"ocean_current_velocity": "km/h"},
          "current": {"time": now.strftime("%Y-%m-%dT%H:%M"), "sea_surface_temperature": 29.4, "wave_height": 0.6,
                      "ocean_current_velocity": 0.9, "ocean_current_direction": 250, "sea_level_height_msl": 0.12},
          "hourly": {"time": [h.strftime("%Y-%m-%dT%H:%M") for h in hours],
                     "sea_surface_temperature": [29.4] * 72, "sea_level_height_msl": [0.1] * 72,
                     "ocean_current_velocity": [0.4] * 72, "ocean_current_direction": [250] * 72, "wave_height": [0.6] * 72}}
CRW = {"table": {"columnNames": ["time", "latitude", "longitude", "CRW_DHW", "CRW_SST", "CRW_SSTANOMALY", "CRW_BAA_7D_MAX"],
                 "rows": [["2026-10-16T12:00:00Z", 16.075, -86.925, 5.2, 29.6, 1.1, 3]]}}
COOPS = {"predictions": [{"t": now.strftime("%Y-%m-%d %H:%M"), "v": "0.8"}]}
YT_STUB = """window.YT={Player:function(id,o){var el=document.getElementById(id);var f=document.createElement('iframe');f.title='YouTube video player (stub)';f.src='about:blank';el.replaceWith(f);this.destroy=function(){f.remove();};}};
Promise.resolve().then(function(){window.onYouTubeIframeAPIReady&&window.onYouTubeIframeAPIReady();});"""


def route(r):
    u = r.request.url
    if "/api/yt/status" in u:
        return r.fulfill(status=200, content_type="application/json", body='{"yt_dlp":false,"ok":true}')
    if "/api/yt/hls" in u:
        return r.fulfill(status=502, content_type="application/json", body='{"error":"stubbed"}')
    if u.startswith(f"http://127.0.0.1:{PORT}"):
        return r.continue_()
    if "fonts.googleapis.com" in u or "fonts.gstatic.com" in u:
        return r.continue_()
    if "marine-api.open-meteo.com" in u:
        return r.fulfill(status=200, content_type="application/json", body=json.dumps(MARINE), headers={"Access-Control-Allow-Origin": "*"})
    if "coastwatch.pfeg.noaa.gov" in u or "pae-paha.pacioos.hawaii.edu" in u or "coastwatch.noaa.gov" in u:
        return r.fulfill(status=200, content_type="application/json", body=json.dumps(CRW), headers={"Access-Control-Allow-Origin": "*"})
    if "tidesandcurrents.noaa.gov" in u:
        return r.fulfill(status=200, content_type="application/json", body=json.dumps(COOPS), headers={"Access-Control-Allow-Origin": "*"})
    if "youtube.com/iframe_api" in u:
        return r.fulfill(status=200, content_type="text/javascript", body=YT_STUB)
    return r.abort()


FAILS = []


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        FAILS.append(msg)


def clear_storage(page):
    page.evaluate(
        """() => { %s }"""
        % " ".join("localStorage.removeItem(%r);" % k for k in KEYS)
    )


def main():
    srv = serve()
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1366, "height": 900})
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on(
            "console",
            lambda m: errors.append(m.text)
            if m.type == "error"
            and "net::ERR_FAILED" not in m.text
            and "Failed to load resource" not in m.text
            else None,
        )
        page.route("**/*", route)

        page.goto(f"{BASE}#/")
        clear_storage(page)

        page.goto(f"{BASE}#/learn")
        page.wait_for_function("document.querySelectorAll('#lc-map li').length === 9", timeout=8000)
        check(page.locator("#lc-map li").count() == 9, "#lc-map li count is 9")
        check(page.locator("#lc-paths button").count() == 7, "#lc-paths button count is 7")
        check(page.locator("#lc-steps button").count() == 5, "#lc-steps button count is 5")
        check(not errors, "no console/page errors on #/learn: " + "; ".join(errors[:5]))

        page.click('#lc-steps button[data-s="3"]')
        page.wait_for_timeout(200)
        pressed = page.locator('#lc-cam-tour .seg[aria-label="Water"] button[aria-pressed="true"]').inner_text()
        check(pressed.strip() == "Murky harbour", 'tour step 4 presses "Murky harbour" (got %r)' % pressed)

        page.click('#lc-paths button[data-p="policy"]')
        page.wait_for_timeout(200)
        on = page.locator("#lc-map .lc-card:not(.lc-off)").count()
        check(on == 4, "Policy path leaves exactly 4 cards without lc-off (got %d)" % on)

        page.goto(f"{BASE}#/learn/m03")
        page.wait_for_function("document.querySelector('#lc-demo .inst')", timeout=8000)
        check(
            page.locator('[data-lc-view="module"]').is_visible(),
            "[data-lc-view=module] visible on #/learn/m03",
        )
        check(
            not page.locator('[data-lc-view="overview"]').is_visible(),
            "[data-lc-view=overview] hidden on #/learn/m03",
        )
        check(page.locator("#lc-demo .inst").count() >= 1, "#lc-demo .inst exists")

        page.click('.lc-q[data-q="0"] .lc-opt[data-j="1"]')
        page.wait_for_timeout(150)
        fb = page.locator('.lc-q[data-q="0"] .lc-fb').inner_text()
        check(fb.startswith("Right."), "quiz q1 correct starts with Right. (got %r)" % fb[:40])

        page.click("#lc-done")
        page.wait_for_timeout(200)
        page.goto(f"{BASE}#/learn/course")
        page.wait_for_function("document.querySelector('#lc-prog-text')", timeout=5000)
        check("1 of 9 done" in page.inner_text("#lc-prog-text"), "progress shows 1 of 9 done")

        errors.clear()
        page.goto(f"{BASE}#/observe")
        page.wait_for_timeout(400)
        page.goto(f"{BASE}#/learn/m01")
        page.wait_for_function("document.querySelector('#lc-article h1')", timeout=8000)
        check("Images are arrays" in page.inner_text("#lc-article h1"), "route switch opens module 01")
        check(not errors, "no errors after observe → learn/m01: " + "; ".join(errors[:5]))

        collisions = page.evaluate(
            """() => {
              const root = document.querySelector('[data-route="learn"]');
              const bad = ['hero', 'lab', 'nb', 'field'];
              return Array.from(root.querySelectorAll('*')).filter(el =>
                bad.some(c => el.classList.contains(c))).map(el => el.className);
            }"""
        )
        check(collisions == [], "no hero/lab/nb/field classes inside learn route: " + str(collisions[:5]))

        mp_ctx = b.new_context(viewport={"width": 390, "height": 844})
        mp = mp_ctx.new_page()
        mp.route("**/*", route)
        mp.goto(f"{BASE}#/")
        clear_storage(mp)
        mp.goto(f"{BASE}#/learn")
        mp.wait_for_function("document.querySelectorAll('#lc-map li').length === 9", timeout=8000)
        over = mp.evaluate("() => document.documentElement.scrollWidth")
        check(over <= 390, f"#/learn scrollWidth at 390 px (got {over})")
        mp.goto(f"{BASE}#/learn/m08")
        mp.wait_for_function("document.querySelector('#lc-demo .inst')", timeout=8000)
        over8 = mp.evaluate("() => document.documentElement.scrollWidth")
        check(over8 <= 390, f"#/learn/m08 scrollWidth at 390 px (got {over8})")
        mp_ctx.close()

        routes = ["learn", "learn/tour", "learn/course", "learn/m03", "learn/m08", "learn/m09", "learn/teach"]
        shots = []
        for color in ("light", "dark"):
            em = {"colorScheme": color}
            sc = b.new_context(viewport={"width": 1366, "height": 900}, color_scheme=color)
            sp = sc.new_page()
            sp.route("**/*", route)
            if color == "dark":
                sp.add_init_script("document.documentElement.setAttribute('data-theme','dark')")
            sp.goto(f"{BASE}#/")
            clear_storage(sp)
            for r in routes:
                sp.goto(f"{BASE}#/{r}")
                sp.wait_for_timeout(700)
                path = f"{OUT}/learn_{r.replace('/', '_')}_{color}_1366.png"
                sp.screenshot(path=path, full_page=False)
                shots.append(path)
            sc.close()
        mc = b.new_context(viewport={"width": 390, "height": 844})
        mp = mc.new_page()
        mp.route("**/*", route)
        mp.goto(f"{BASE}#/")
        clear_storage(mp)
        for r in routes:
            mp.goto(f"{BASE}#/{r}")
            mp.wait_for_timeout(700)
            path = f"{OUT}/learn_{r.replace('/', '_')}_mobile_390.png"
            mp.screenshot(path=path, full_page=False)
            shots.append(path)
        mc.close()
        print("screenshots:")
        for s in shots:
            print("  " + s)

        page.goto(f"{BASE}#/")
        clear_storage(page)
        b.close()
    srv.shutdown()
    print(f"\n{len(FAILS)} failures")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
