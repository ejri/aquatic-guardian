"""Aquatic Guardian relay.

* /api/plumes/*   the Python reference engine (plumes2py) for full-fidelity
                  runs, critical-condition sweeps, tidal cycles, Monte Carlo
* /api/proxy      allow-listed CORS proxy for ocean-data sources that block
                  browsers, with a 10-minute cache
* /ws/vision/{id} live behaviour metrics from server-side vision workers,
                  which start ONLY for streams listed in permitted_streams.json
                  with a recorded permission from the operator

Run locally:  uvicorn relay.app:app --reload   (from the repository root)
"""
from __future__ import annotations

import asyncio
import json
import os
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

import httpx
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from plumes2py import Scenario, reference_example, run
from plumes2py.datacenter import DataCentreDesign, build
from plumes2py.scenarios import critical_conditions, monte_carlo, tidal_cycle, tornado

HERE = Path(__file__).parent
ALLOWED_ORIGINS = [o for o in os.environ.get("AG_ALLOWED_ORIGINS", "http://localhost:8765,http://127.0.0.1:8765").split(",") if o]
PROXY_HOSTS = {
    "marine-api.open-meteo.com", "coastwatch.pfeg.noaa.gov", "coastwatch.noaa.gov",
    "pae-paha.pacioos.hawaii.edu", "api.tidesandcurrents.noaa.gov",
    "api-iwls.dfo-mpo.gc.ca", "www.ndbc.noaa.gov", "data.oceannetworks.ca",
}
CACHE_S = 600

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(_app):
    await start_workers()
    yield


app = FastAPI(title="Aquatic Guardian relay", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_methods=["GET", "POST"], allow_headers=["*"])


# ------------------------------------------------------------------ PLUMES --
class RunRequest(BaseModel):
    scenario: Dict
    rule: Optional[str] = None
    wa_category: str = "excellent"
    custom_increment: Optional[float] = None


class DataCentreRequest(BaseModel):
    design: Dict = Field(default_factory=dict)
    sst_c: float
    salinity: float
    current_ms: float
    acute_m: float = 30.0
    chronic_m: float = 300.0
    rule: Optional[str] = None
    custom_increment: Optional[float] = None


def _scenario(d: Dict) -> Scenario:
    try:
        return Scenario.from_dict(d)
    except (TypeError, KeyError, ValueError) as e:
        raise HTTPException(422, f"Scenario not understood: {e}")


def _run(sc: Scenario, rule, wa_category="excellent", custom_increment=None) -> Dict:
    try:
        return run(sc, rule=rule, wa_category=wa_category, custom_increment=custom_increment, convergence_check=True)
    except ValueError as e:
        raise HTTPException(422, str(e))


@app.get("/api/health")
def health():
    return {"ok": True, "engine": "plumes2py", "workers": sorted(HUB.running)}


@app.get("/api/plumes/example")
def example():
    return reference_example().to_dict()


@app.post("/api/plumes/run")
def plumes_run(req: RunRequest):
    return _run(_scenario(req.scenario), req.rule, req.wa_category, req.custom_increment)


@app.post("/api/plumes/datacentre")
def plumes_datacentre(req: DataCentreRequest):
    allowed = set(DataCentreDesign().__dict__)
    unknown = set(req.design) - allowed
    if unknown:
        raise HTTPException(422, f"Unknown design fields: {sorted(unknown)}")
    sc = build(DataCentreDesign(**req.design), sst_c=req.sst_c, salinity=req.salinity, current_ms=req.current_ms,
               acute_m=req.acute_m, chronic_m=req.chronic_m)
    out = _run(sc, req.rule, custom_increment=req.custom_increment)
    out["scenario"] = sc.to_dict()
    return out


@app.post("/api/plumes/critical")
def plumes_critical(req: RunRequest):
    return critical_conditions(_scenario(req.scenario), rule=req.rule)


@app.post("/api/plumes/tidal")
def plumes_tidal(req: RunRequest, u_peak: float = Query(..., gt=0, le=5), n: int = Query(24, ge=4, le=96)):
    return tidal_cycle(_scenario(req.scenario), u_peak, n=n, rule=req.rule)


@app.post("/api/plumes/montecarlo")
def plumes_mc(req: RunRequest, n: int = Query(200, ge=10, le=500), seed: int = 7):
    return monte_carlo(_scenario(req.scenario), n=n, seed=seed)


@app.post("/api/plumes/tornado")
def plumes_tornado(req: RunRequest):
    return tornado(_scenario(req.scenario))


# ------------------------------------------------------------------- proxy --
_cache: Dict[str, tuple] = {}


@app.get("/api/proxy")
async def proxy(url: str):
    u = urlparse(url)
    if u.scheme != "https" or u.hostname not in PROXY_HOSTS:
        raise HTTPException(403, f"Host not on the allow-list: {u.hostname}")
    hit = _cache.get(url)
    if hit and time.time() - hit[0] < CACHE_S:
        return hit[1]
    headers = {"User-Agent": "AquaticGuardianRelay/1.0 (+https://github.com/ejri/aquatic-guardian)"}
    if u.hostname == "data.oceannetworks.ca" and os.environ.get("ONC_TOKEN"):
        url = url + ("&" if "?" in url else "?") + "token=" + os.environ["ONC_TOKEN"]
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(url, headers=headers)
    if r.status_code != 200:
        raise HTTPException(502, f"Upstream {u.hostname} returned {r.status_code}")
    try:
        data = r.json()
    except ValueError:
        data = {"text": r.text}
    _cache[url] = (time.time(), data)
    return data


# ------------------------------------------------------------------ vision --
class Hub:
    def __init__(self):
        self.clients: Dict[str, Set[WebSocket]] = {}
        self.latest: Dict[str, Dict] = {}
        self.running: Set[str] = set()
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    async def publish(self, sid: str, msg: Dict):
        self.latest[sid] = msg
        dead = []
        for ws in list(self.clients.get(sid, ())):
            try:
                await ws.send_text(json.dumps(msg, default=float))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.clients[sid].discard(ws)


HUB = Hub()


def load_permitted() -> List[Dict]:
    p = Path(os.environ.get("AG_PERMITTED", HERE / "permitted_streams.json"))
    if not p.exists():
        return []
    items = json.loads(p.read_text())["streams"]
    ok = []
    for s in items:
        perm = s.get("permission") or {}
        # no recorded permission, no worker: this is the line the relay will not cross
        if perm.get("status") == "granted" and perm.get("granted_by") and perm.get("date") and s.get("source"):
            ok.append(s)
    return ok


def resolve_source(src: str) -> str:
    if src.startswith("youtube:"):
        import streamlink  # optional; only for operators who granted permission
        streams = streamlink.streams("https://www.youtube.com/watch?v=" + src.split(":", 1)[1])
        if not streams:
            raise RuntimeError("stream offline")
        return (streams.get("480p") or streams.get("best")).url
    return src


def worker(s: Dict):
    import cv2
    from .vision import Engine, yolo_detector
    sid, fps = s["id"], float(s.get("fps", 2))
    det = yolo_detector(s["weights"]) if s.get("weights") else None
    while True:
        try:
            cap = cv2.VideoCapture(resolve_source(s["source"]))
            eng = Engine(detector=det)
            next_t = time.time()
            while cap.isOpened():
                ok, frame = cap.read()
                if not ok:
                    break
                if time.time() < next_t:
                    continue
                next_t = time.time() + 1 / fps
                msg = eng.process(frame)
                msg["stream_id"] = sid
                asyncio.run_coroutine_threadsafe(HUB.publish(sid, msg), HUB.loop)
            cap.release()
        except Exception as e:  # keep the worker alive; report and retry
            asyncio.run_coroutine_threadsafe(HUB.publish(sid, {"error": f"{sid}: {e}", "t": int(time.time() * 1000)}), HUB.loop)
        time.sleep(30)


async def start_workers():
    HUB.loop = asyncio.get_running_loop()
    if os.environ.get("AG_RUN_WORKERS") != "1":
        return
    for s in load_permitted():
        threading.Thread(target=worker, args=(s,), daemon=True, name="vision-" + s["id"]).start()
        HUB.running.add(s["id"])


@app.get("/api/streams")
def streams():
    return {"permitted": [{"id": s["id"], "permission": s["permission"]} for s in load_permitted()],
            "running": sorted(HUB.running)}


@app.websocket("/ws/vision/{sid}")
async def ws_vision(ws: WebSocket, sid: str):
    await ws.accept()
    if sid not in HUB.running:
        await ws.send_text(json.dumps({"error": f"No server analysis for {sid}: the operator has not granted permission, "
                                                 "or the relay was started without AG_RUN_WORKERS=1."}))
        await ws.close()
        return
    HUB.clients.setdefault(sid, set()).add(ws)
    if sid in HUB.latest:
        await ws.send_text(json.dumps(HUB.latest[sid], default=float))
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        HUB.clients[sid].discard(ws)
