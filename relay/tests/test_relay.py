import json, math, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "python")]
import numpy as np
import cv2
from fastapi.testclient import TestClient
from relay.app import app, load_permitted
from relay.vision import Engine

client = TestClient(app)

def test_health():
    assert client.get("/api/health").json()["ok"]

def test_run_example_matches_reference():
    sc = client.get("/api/plumes/example").json()
    r = client.post("/api/plumes/run", json={"scenario": sc, "rule": "wa_marine"}).json()
    assert abs(r["metrics"]["nearfield"]["dilution"] / 169.754 - 1) < 0.012
    assert "convergence" in r["metrics"] and r["compliance"]["rule"]["id"] == "wa_marine"

def test_datacentre_endpoint_and_validation():
    r = client.post("/api/plumes/datacentre", json={"design": {"it_mw": 10}, "sst_c": 12, "salinity": 31, "current_ms": 0.2, "rule": "wa_marine"})
    assert r.status_code == 200 and r.json()["scenario"]["effluent"]["salinity"] == 31
    bad = client.post("/api/plumes/datacentre", json={"design": {"it_megawatts": 10}, "sst_c": 12, "salinity": 31, "current_ms": 0.2})
    assert bad.status_code == 422

def test_tidal_endpoint():
    sc = client.get("/api/plumes/example").json()
    r = client.post("/api/plumes/tidal?u_peak=0.3&n=8", json={"scenario": sc}).json()
    assert len(r["rows"]) == 8

def test_proxy_refuses_unlisted_hosts():
    assert client.get("/api/proxy", params={"url": "https://example.com/x"}).status_code == 403
    assert client.get("/api/proxy", params={"url": "http://marine-api.open-meteo.com/v1/marine"}).status_code == 403

def test_no_worker_without_recorded_permission():
    assert load_permitted() == []          # shipped entries are 'pending'
    with client.websocket_connect("/ws/vision/utila-top") as ws:
        assert "permission" in json.loads(ws.receive_text())["error"]

def test_server_vision_tracks_synthetic_school():
    eng = Engine()
    fish = [[60 + i * 70, 80 + (i % 3) * 80, 3 + (i % 2)] for i in range(7)]
    m = None
    for t in range(60):
        img = np.zeros((360, 640, 3), np.uint8); img[:] = (112, 90, 10)
        for f in fish:
            f[0] = (f[0] + f[2] * 4) % 640
            cv2.ellipse(img, (int(f[0]), int(f[1])), (16, 7), 0, 0, 360, (138, 211, 232), -1)
        m = eng.process(img, now=t / 8)
    assert 5 <= m["count"] <= 9 and m["polarization"] > 0.8
