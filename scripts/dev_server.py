#!/usr/bin/env python3
"""Serve site/ with allow-listed /api/proxy (ocean data) and /api/yt/* (live
HLS for browser ML). Usage: python scripts/dev_server.py [port=8765]

YouTube pixels cannot be read from an iframe. This server resolves a live
playlist with yt-dlp (optional) and rewrites segment URLs through
/api/media so a same-origin <video> can feed ONNX in the page.
"""
from __future__ import annotations

import re
import subprocess
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

try:
    import certifi
    VERIFY = certifi.where()
except Exception:
    VERIFY = True

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
YT_DLP = ROOT / ".venv" / "bin" / "yt-dlp"
ALLOWED = {
    "marine-api.open-meteo.com",
    "coastwatch.pfeg.noaa.gov",
    "coastwatch.noaa.gov",
    "pae-paha.pacioos.hawaii.edu",
    "api.tidesandcurrents.noaa.gov",
    "api-iwls.dfo-mpo.gc.ca",
    "www.ndbc.noaa.gov",
    "data.oceannetworks.ca",
}
UA = "AquaticGuardianDevProxy/1.0 (+https://github.com/ejri/aquatic-guardian)"
_VID_RE = re.compile(r"^[A-Za-z0-9_-]{6,20}$")
_YT_CACHE: dict[str, tuple[float, str]] = {}


def _host_ok(host: str | None) -> bool:
    if not host:
        return False
    if host in ALLOWED:
        return True
    return host.endswith(".googlevideo.com") or host == "manifest.googlevideo.com"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(SITE), **k)

    def do_OPTIONS(self):
        if self.path.startswith("/api/"):
            self.send_response(204)
            self._cors()
            self.end_headers()
            return
        self.send_error(404)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/proxy":
            return self._proxy(parse_qs(parsed.query).get("url", [""])[0], rewrite_m3u8=False)
        if parsed.path == "/api/media":
            return self._proxy(parse_qs(parsed.query).get("url", [""])[0], rewrite_m3u8=True)
        if parsed.path == "/api/yt/hls":
            return self._yt_hls(parse_qs(parsed.query).get("v", [""])[0])
        if parsed.path == "/api/yt/status":
            return self._json(200, {"yt_dlp": YT_DLP.is_file() or bool(_which("yt-dlp")), "ok": True})
        return super().do_GET()

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, code: int, obj: dict):
        import json
        body = json.dumps(obj).encode()
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _yt_hls(self, vid: str):
        if not _VID_RE.match(vid or ""):
            self.send_error(400, "bad video id")
            return
        try:
            src = _resolve_hls(vid)
        except Exception as e:
            self._json(502, {"error": str(e), "hint": "pip install yt-dlp in .venv"})
            return
        try:
            import httpx
            with httpx.Client(timeout=25, verify=VERIFY, follow_redirects=True,
                              headers={"User-Agent": UA}) as client:
                r = client.get(src)
            if r.status_code != 200:
                self.send_error(502, f"playlist upstream {r.status_code}")
                return
            text = _rewrite_playlist(r.text, base=src)
        except Exception as e:
            self.send_error(502, str(e))
            return
        body = text.encode()
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "application/vnd.apple.mpegurl")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _proxy(self, raw: str, rewrite_m3u8: bool):
        try:
            u = urlparse(raw)
        except Exception:
            self.send_error(400, "bad url")
            return
        if u.scheme != "https" or not _host_ok(u.hostname):
            self.send_error(403, f"host not allowed: {u.hostname}")
            return
        try:
            import httpx
            with httpx.Client(timeout=30, verify=VERIFY, follow_redirects=True,
                              headers={"User-Agent": UA}) as client:
                r = client.get(raw)
            if r.status_code != 200:
                self.send_error(502, f"upstream {r.status_code}")
                return
            ctype = r.headers.get("content-type", "application/octet-stream")
            body = r.content
            if rewrite_m3u8 and ("mpegurl" in ctype or raw.endswith(".m3u8") or body[:7] == b"#EXTM3U"):
                text = _rewrite_playlist(body.decode("utf-8", "replace"), base=raw)
                body = text.encode()
                ctype = "application/vnd.apple.mpegurl"
        except Exception as e:
            self.send_error(502, str(e))
            return
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", ctype.split(";")[0] or "application/octet-stream")
        self.send_header("Cache-Control", "public, max-age=30")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def _which(name: str) -> str | None:
    from shutil import which
    return which(name)


def _resolve_hls(vid: str) -> str:
    import time
    now = time.time()
    hit = _YT_CACHE.get(vid)
    if hit and now - hit[0] < 300:
        return hit[1]
    bin_ = str(YT_DLP) if YT_DLP.is_file() else _which("yt-dlp")
    if not bin_:
        raise RuntimeError("yt-dlp not installed")
    url = f"https://www.youtube.com/watch?v={vid}"
    out = subprocess.check_output(
        [bin_, "-g", "-f", "bv*[height<=720]/b[height<=720]/best", "--no-warnings", url],
        text=True,
        timeout=45,
    ).strip().splitlines()
    if not out:
        raise RuntimeError("yt-dlp returned no URL")
    # Prefer a video playlist (not audio-only)
    src = out[0]
    for line in out:
        if "itag/14" in line or "/videoplayback" in line or "hls_playlist" in line:
            src = line
            break
    _YT_CACHE[vid] = (now, src)
    return src


def _rewrite_playlist(text: str, base: str) -> str:
    """Point absolute and relative playlist entries at /api/media."""
    base_u = urlparse(base)
    root = f"{base_u.scheme}://{base_u.netloc}"
    parent = base.rsplit("/", 1)[0] + "/"
    lines = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            # rewrite URI="..." inside tags
            if "URI=\"" in line:
                def repl(m):
                    return 'URI="' + _media_url(_abs(m.group(1), root, parent)) + '"'
                line = re.sub(r'URI="([^"]+)"', repl, line)
            lines.append(line)
            continue
        lines.append(_media_url(_abs(s, root, parent)))
    return "\n".join(lines) + "\n"


def _abs(ref: str, root: str, parent: str) -> str:
    if ref.startswith("https://"):
        return ref
    if ref.startswith("/"):
        return root + ref
    return parent + ref


def _media_url(abs_url: str) -> str:
    return "/api/media?url=" + quote(abs_url, safe="")


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    has = YT_DLP.is_file() or bool(_which("yt-dlp"))
    print(f"Serving {SITE} at http://127.0.0.1:{port}/")
    print(f"  ocean proxy: /api/proxy   yt HLS: /api/yt/hls?v=ID  (yt-dlp {'yes' if has else 'NO'})")
    print("Open http://127.0.0.1:%d/#/observe" % port)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
