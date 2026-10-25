"""Server-side vision, mirroring site/js/vision.js so the browser and the relay
report the same metrics with the same meaning.

Pipeline: 320 px working frame -> running-Gaussian background model ->
foreground mask -> 3x3 open -> connected components (or an optional YOLO
detector via ultralytics) -> constant-velocity Kalman tracker with greedy
two-stage association -> behaviour and visibility metrics.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

try:  # OpenCV is needed for capture and morphology; tests use it too
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None


def iou(a: Dict, b: Dict) -> float:
    x0, y0 = max(a["x"], b["x"]), max(a["y"], b["y"])
    x1, y1 = min(a["x"] + a["w"], b["x"] + b["w"]), min(a["y"] + a["h"], b["y"] + b["h"])
    inter = max(0.0, x1 - x0) * max(0.0, y1 - y0)
    return inter / (a["w"] * a["h"] + b["w"] * b["h"] - inter + 1e-9)


def hull_area(pts: List[List[float]]) -> float:
    if len(pts) < 3:
        return 0.0
    p = sorted(map(tuple, pts))

    def cr(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for q in p:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], q) <= 0:
            lo.pop()
        lo.append(q)
    for q in reversed(p):
        while len(up) >= 2 and cr(up[-2], up[-1], q) <= 0:
            up.pop()
        up.append(q)
    h = lo[:-1] + up[:-1]
    return abs(sum(h[i][0] * h[(i + 1) % len(h)][1] - h[(i + 1) % len(h)][0] * h[i][1] for i in range(len(h)))) / 2


class KF1:
    """Constant-velocity Kalman filter on one axis (same equations as vision.js)."""

    def __init__(self, p0: float):
        self.x = [p0, 0.0]
        self.P = [[25.0, 0.0], [0.0, 100.0]]

    def predict(self, dt: float, q: float):
        x, P = self.x, self.P
        self.x = [x[0] + dt * x[1], x[1]]
        p00 = P[0][0] + dt * (P[1][0] + P[0][1]) + dt * dt * P[1][1] + q * dt ** 3 / 3
        p01 = P[0][1] + dt * P[1][1] + q * dt * dt / 2
        self.P = [[p00, p01], [p01, P[1][1] + q * dt]]

    def update(self, z: float, r: float):
        P = self.P
        S = P[0][0] + r
        k0, k1 = P[0][0] / S, P[1][0] / S
        y = z - self.x[0]
        self.x = [self.x[0] + k0 * y, self.x[1] + k1 * y]
        self.P = [[(1 - k0) * P[0][0], (1 - k0) * P[0][1]], [P[1][0] - k1 * P[0][0], P[1][1] - k1 * P[0][1]]]


@dataclass
class Track:
    id: int
    kx: KF1
    ky: KF1
    w: float
    h: float
    hits: int = 1
    miss: int = 0
    cls: str = "moving object"
    score: float = 0.0
    v_prev: List[float] = field(default_factory=lambda: [0.0, 0.0])


class Tracker:
    def __init__(self):
        self.tracks: List[Track] = []
        self.next_id = 1

    def step(self, dets: List[Dict], dt: float) -> List[Track]:
        q, r = 400.0, 4.0
        for t in self.tracks:
            t.kx.predict(dt, q)
            t.ky.predict(dt, q)
            t.miss += 1
        hi = [d for d in dets if d["score"] >= 0.4]
        lo = [d for d in dets if d["score"] < 0.4]

        def associate(pool, tracks):
            pairs = []
            for ti, t in enumerate(tracks):
                pb = {"x": t.kx.x[0] - t.w / 2, "y": t.ky.x[0] - t.h / 2, "w": t.w, "h": t.h}
                gate = 1.5 * max(t.w, t.h, 4)
                for di, d in enumerate(pool):
                    u = iou(pb, d)
                    dist = math.hypot(d["x"] + d["w"] / 2 - t.kx.x[0], d["y"] + d["h"] / 2 - t.ky.x[0])
                    s = 1 + u if u > 0 else (1 - dist / gate if dist < gate else -1)
                    if s > 0.05:
                        pairs.append((s, ti, di))
            pairs.sort(key=lambda p: -p[0])
            ut, ud, m = set(), set(), []
            for s, ti, di in pairs:
                if ti not in ut and di not in ud:
                    ut.add(ti); ud.add(di); m.append((ti, di))
            return m, ut, ud

        def upd(t: Track, d: Dict):
            t.kx.update(d["x"] + d["w"] / 2, r)
            t.ky.update(d["y"] + d["h"] / 2, r)
            t.w = 0.7 * t.w + 0.3 * d["w"]
            t.h = 0.7 * t.h + 0.3 * d["h"]
            t.hits += 1
            t.miss = 0
            t.cls, t.score = d.get("cls", t.cls), d["score"]

        m, ut, ud = associate(hi, self.tracks)
        for ti, di in m:
            upd(self.tracks[ti], hi[di])
        rest = [t for i, t in enumerate(self.tracks) if i not in ut]
        m2, _, _ = associate(lo, rest)
        for ti, di in m2:
            upd(rest[ti], lo[di])
        for i, d in enumerate(hi):
            if i not in ud:
                self.tracks.append(Track(self.next_id, KF1(d["x"] + d["w"] / 2), KF1(d["y"] + d["h"] / 2), d["w"], d["h"],
                                         cls=d.get("cls", "moving object"), score=d["score"]))
                self.next_id += 1
        self.tracks = [t for t in self.tracks if t.miss <= 8]
        return [t for t in self.tracks if t.hits >= 2 and t.miss <= 2]


class Engine:
    def __init__(self, width: int = 320, k: float = 2.5, min_area: int = 6, detector=None):
        self.width, self.k, self.min_area, self.detector = width, k, min_area, detector
        self.bg = None
        self.var = None
        self.frames = 0
        self.tracker = Tracker()
        self.last = None
        self.startles: List = []

    def process(self, frame_bgr: np.ndarray, now: Optional[float] = None) -> Dict:
        now = time.time() if now is None else now
        h0, w0 = frame_bgr.shape[:2]
        W = self.width
        H = max(8, round(W * h0 / w0))
        small = cv2.resize(frame_bgr, (W, H), interpolation=cv2.INTER_AREA)
        b, g, r = small[..., 0].astype(np.float32), small[..., 1].astype(np.float32), small[..., 2].astype(np.float32)
        gray = 0.299 * r + 0.587 * g + 0.114 * b
        dt = min(2.0, now - self.last) if self.last else 0.5
        self.last = now
        if self.bg is None or self.bg.shape != gray.shape:
            self.bg = gray.copy()
            self.var = np.full_like(gray, 64.0)
            self.frames = 0
        a = 0.3 if self.frames < 10 else 0.03
        d = gray - self.bg
        fg = d * d > self.k ** 2 * np.maximum(self.var, 16.0)
        aa = np.where(fg, a * 0.1, a)
        self.bg += aa * d
        self.var = (1 - aa) * self.var + aa * d * d
        self.frames += 1
        kern = np.ones((3, 3), np.uint8)
        mask = cv2.dilate(cv2.erode(fg.astype(np.uint8), kern), kern)
        lap = cv2.Laplacian(gray, cv2.CV_32F, ksize=1)
        mean, sd = float(gray.mean()), float(gray.std())
        vis = {"luminance": mean / 255, "contrast": sd / 128,
               "sharpness": min(1.0, math.sqrt(float((lap[1:-1, 1:-1] ** 2).mean())) / 40),
               "blue_green": float((b.sum() + g.sum()) / (2 * r.sum() + 1))}
        vis["index"] = max(0.0, min(1.0, 0.5 * min(1, vis["contrast"] * 2.5) + 0.5 * vis["sharpness"])) * (0.2 if vis["luminance"] < 0.06 else 1)
        if self.detector is not None:
            dets = self.detector(small)
        elif self.frames < 8:
            dets = []
        else:
            n, lab, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
            dets = [{"x": float(s[0]), "y": float(s[1]), "w": float(s[2]), "h": float(s[3]), "area": int(s[4]),
                     "score": min(1.0, s[4] / 40), "cls": "moving object"} for s in stats[1:] if s[4] >= self.min_area]
        tracks = self.tracker.step(dets, dt)
        m = self.metrics(tracks, W, H, float(mask.mean()), vis, dt, now)
        m.update({"detections": len(dets), "source": "relay: " + ("detector" if self.detector else "motion (background subtraction)"),
                  "fps": 1 / dt if dt else None, "t": int(now * 1000),
                  "tracks": [{"id": t.id, "x": t.kx.x[0] / W, "y": t.ky.x[0] / H, "w": t.w / W, "h": t.h / H} for t in tracks]})
        return m

    def metrics(self, tracks, W, H, activity, vis, dt, now) -> Dict:
        N = len(tracks)
        diag = math.hypot(W, H)
        sp, pts = [], []
        ux = uy = cy = 0.0
        moving = startle = 0
        for t in tracks:
            vx, vy = t.kx.x[1], t.ky.x[1]
            s = math.hypot(vx, vy)
            bl = max(2.0, math.sqrt(t.w * t.h))
            sp.append(s / bl)
            pts.append([t.kx.x[0], t.ky.x[0]])
            cy += t.ky.x[0] / H
            if s > 0.5 * bl:
                ux += vx / s; uy += vy / s; moving += 1
            acc = math.hypot(vx - t.v_prev[0], vy - t.v_prev[1]) / max(dt, 1e-3) / bl
            if t.hits > 4 and acc > 6:
                startle += 1
            t.v_prev = [vx, vy]
        if startle:
            self.startles.append((now, startle))
        self.startles = [q for q in self.startles if now - q[0] < 60]
        nnd = None
        if N >= 2:
            tot = 0.0
            for i, p in enumerate(pts):
                tot += min(math.hypot(p[0] - q[0], p[1] - q[1]) for j, q in enumerate(pts) if j != i)
            nnd = tot / N / diag
        pol = math.hypot(ux, uy) / moving if moving else None
        nul = math.sqrt(math.pi) / (2 * math.sqrt(moving)) if moving else None
        return {"count": N, "moving": moving, "speed_bl_s": sum(sp) / len(sp) if sp else None,
                "polarization": pol, "polarization_null": nul, "polarization_excess": None if pol is None else pol - nul,
                "nnd": nnd, "dispersion": hull_area(pts) / (W * H) if N >= 3 else None,
                "vertical": cy / N if N else None, "activity": activity,
                "startles_per_min": sum(q[1] for q in self.startles), "visibility": vis["index"], "vis": vis,
                "reliable": vis["index"] >= 0.25 and vis["luminance"] >= 0.06,
                "flags": [] if vis["index"] >= 0.25 and vis["luminance"] >= 0.06 else
                ["Low visibility: counts and behaviour here are unreliable, and a drop would look like animals leaving when they are only harder to see."]}


def yolo_detector(weights: str, conf: float = 0.25):
    """Optional detector using ultralytics (AGPL-3.0: publish your relay source
    if you serve it). Returns a callable frame -> detections in working-frame px."""
    from ultralytics import YOLO  # noqa: WPS433 (optional dependency)
    model = YOLO(weights)

    def detect(frame):
        res = model.predict(frame, conf=conf, verbose=False)[0]
        names = res.names
        out = []
        for (x0, y0, x1, y1), c, k in zip(res.boxes.xyxy.tolist(), res.boxes.conf.tolist(), res.boxes.cls.tolist()):
            out.append({"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0, "score": float(c), "cls": names.get(int(k), str(k))})
        return out
    return detect
