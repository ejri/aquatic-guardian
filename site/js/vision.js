/* vision.js: computer vision on live ocean video, in the browser.
 *
 * Sources:
 *   1. fromVideo(el): same-origin <video> (HLS via /api/yt/hls) — preferred for ML.
 *   2. captureTab(el): getDisplayMedia when only an iframe is available.
 *   3. fromFile(file): a local clip.
 *   4. connectRelay(id): server-side detections for permitted streams.
 *
 * Pipeline: work canvas -> ONNX YOLOv8 (or motion) -> tracker -> metrics.
 */
(function (root) {
  "use strict";
  var ORT_URL = "https://cdn.jsdelivr.net/npm/onnxruntime-web@1.19.2/dist/ort.min.js";

  /* ------------------------------------------------ sources ---- */
  function captureTab(targetEl) {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getDisplayMedia)
      return Promise.reject(new Error("This browser cannot capture a tab. Try Chrome or Edge on a desktop, or analyse a video file instead."));
    var opts = { video: { displaySurface: "browser", frameRate: 15 }, audio: false, preferCurrentTab: true, selfBrowserSurface: "include", surfaceSwitching: "exclude" };
    return navigator.mediaDevices.getDisplayMedia(opts).then(function (stream) {
      var track = stream.getVideoTracks()[0], cropped = false;
      var p = Promise.resolve();
      if (targetEl && root.CropTarget && track.cropTo) {
        p = root.CropTarget.fromElement(targetEl).then(function (ct) { return track.cropTo(ct); }).then(function () { cropped = true; }).catch(function () {});
      }
      return p.then(function () {
        var v = document.createElement("video");
        v.muted = true; v.playsInline = true; v.srcObject = stream;
        return v.play().then(function () { return { video: v, stream: stream, cropped: cropped, kind: "tab" }; });
      });
    });
  }
  function fromFile(file) {
    var v = document.createElement("video");
    v.muted = true; v.playsInline = true; v.loop = true; v.src = URL.createObjectURL(file);
    return v.play().then(function () { return { video: v, stream: null, cropped: true, kind: "file", name: file.name }; });
  }
  function fromVideo(el) {
    if (!el || el.tagName !== "VIDEO")
      return Promise.reject(new Error("No video element to analyse."));
    if (el.readyState < 2)
      return new Promise(function (res, rej) {
        var on = function () { el.removeEventListener("loadeddata", on); fromVideo(el).then(res, rej); };
        el.addEventListener("loadeddata", on);
        setTimeout(function () { el.removeEventListener("loadeddata", on); rej(new Error("Video never became ready.")); }, 12000);
      });
    return Promise.resolve({ video: el, stream: null, cropped: true, kind: "video", keepAlive: true });
  }

  /* --------------------------------------------- image ops ---- */
  function erode(m, w, h, out) {
    for (var y = 0; y < h; y++) for (var x = 0; x < w; x++) {
      var i = y * w + x, v = m[i];
      if (v) { for (var dy = -1; dy <= 1 && v; dy++) for (var dx = -1; dx <= 1; dx++) { var yy = y + dy, xx = x + dx; if (yy < 0 || yy >= h || xx < 0 || xx >= w || !m[yy * w + xx]) { v = 0; break; } } }
      out[i] = v;
    }
    return out;
  }
  function dilate(m, w, h, out) {
    for (var y = 0; y < h; y++) for (var x = 0; x < w; x++) {
      var v = 0;
      for (var dy = -1; dy <= 1 && !v; dy++) for (var dx = -1; dx <= 1; dx++) { var yy = y + dy, xx = x + dx; if (yy >= 0 && yy < h && xx >= 0 && xx < w && m[yy * w + xx]) { v = 1; break; } }
      out[y * w + x] = v;
    }
    return out;
  }
  function components(mask, w, h, minArea) {
    var label = new Int32Array(w * h), next = 1, parent = [0];
    function find(a) { while (parent[a] !== a) { parent[a] = parent[parent[a]]; a = parent[a]; } return a; }
    for (var y = 0; y < h; y++) for (var x = 0; x < w; x++) {
      var i = y * w + x; if (!mask[i]) continue;
      var l = x > 0 ? label[i - 1] : 0, u = y > 0 ? label[i - w] : 0;
      if (!l && !u) { label[i] = next; parent.push(next); next++; }
      else if (l && u) { var a = find(l), b = find(u); label[i] = Math.min(a, b); if (a !== b) parent[Math.max(a, b)] = Math.min(a, b); }
      else label[i] = l || u;
    }
    var boxes = {};
    for (var j = 0; j < w * h; j++) {
      if (!label[j]) continue;
      var r = find(label[j]), bx = boxes[r], xx = j % w, yy = (j / w) | 0;
      if (!bx) boxes[r] = bx = { x0: xx, y0: yy, x1: xx, y1: yy, n: 0 };
      if (xx < bx.x0) bx.x0 = xx; if (xx > bx.x1) bx.x1 = xx; if (yy < bx.y0) bx.y0 = yy; if (yy > bx.y1) bx.y1 = yy; bx.n++;
    }
    return Object.keys(boxes).map(function (k) { return boxes[k]; }).filter(function (b) { return b.n >= minArea; })
      .map(function (b) { return { x: b.x0, y: b.y0, w: b.x1 - b.x0 + 1, h: b.y1 - b.y0 + 1, score: Math.min(1, b.n / 40), cls: "moving object", area: b.n }; });
  }
  function iou(a, b) {
    var x0 = Math.max(a.x, b.x), y0 = Math.max(a.y, b.y), x1 = Math.min(a.x + a.w, b.x + b.w), y1 = Math.min(a.y + a.h, b.y + b.h);
    var inter = Math.max(0, x1 - x0) * Math.max(0, y1 - y0);
    return inter / (a.w * a.h + b.w * b.h - inter + 1e-9);
  }
  function hull(pts) { // Andrew monotone chain; returns area
    if (pts.length < 3) return 0;
    var p = pts.slice().sort(function (a, b) { return a[0] - b[0] || a[1] - b[1]; });
    function cr(o, a, b) { return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]); }
    var lo = [], up = [];
    p.forEach(function (q) { while (lo.length >= 2 && cr(lo[lo.length - 2], lo[lo.length - 1], q) <= 0) lo.pop(); lo.push(q); });
    for (var i = p.length - 1; i >= 0; i--) { var q = p[i]; while (up.length >= 2 && cr(up[up.length - 2], up[up.length - 1], q) <= 0) up.pop(); up.push(q); }
    var h = lo.slice(0, -1).concat(up.slice(0, -1)), a = 0;
    for (var j = 0; j < h.length; j++) { var k = (j + 1) % h.length; a += h[j][0] * h[k][1] - h[k][0] * h[j][1]; }
    return Math.abs(a) / 2;
  }

  /* ---------------------------------------------- tracker ---- */
  // Constant-velocity Kalman filter per axis (position, velocity); size smoothed.
  function KF1(p0) { this.x = [p0, 0]; this.P = [[25, 0], [0, 100]]; }
  KF1.prototype.predict = function (dt, q) {
    var x = this.x, P = this.P;
    this.x = [x[0] + dt * x[1], x[1]];
    var p00 = P[0][0] + dt * (P[1][0] + P[0][1]) + dt * dt * P[1][1] + q * dt * dt * dt / 3;
    var p01 = P[0][1] + dt * P[1][1] + q * dt * dt / 2, p11 = P[1][1] + q * dt;
    this.P = [[p00, p01], [p01, p11]];
  };
  KF1.prototype.update = function (z, r) {
    var P = this.P, S = P[0][0] + r, k0 = P[0][0] / S, k1 = P[1][0] / S, y = z - this.x[0];
    this.x = [this.x[0] + k0 * y, this.x[1] + k1 * y];
    this.P = [[(1 - k0) * P[0][0], (1 - k0) * P[0][1]], [P[1][0] - k1 * P[0][0], P[1][1] - k1 * P[0][1]]];
  };
  function Tracker() { this.tracks = []; this.nextId = 1; }
  Tracker.prototype.step = function (dets, dt) {
    var T = this.tracks, q = 400, r = 4;
    T.forEach(function (t) { t.kx.predict(dt, q); t.ky.predict(dt, q); t.age++; t.miss++; });
    var hi = dets.filter(function (d) { return d.score >= 0.4; }), lo = dets.filter(function (d) { return d.score < 0.4; });
    function associate(pool, tracks) {
      var pairs = [];
      tracks.forEach(function (t, ti) {
        var pb = { x: t.kx.x[0] - t.w / 2, y: t.ky.x[0] - t.h / 2, w: t.w, h: t.h }, gate = 1.5 * Math.max(t.w, t.h, 4);
        pool.forEach(function (d, di) {
          var u = iou(pb, d), dist = Math.hypot(d.x + d.w / 2 - t.kx.x[0], d.y + d.h / 2 - t.ky.x[0]);
          var s = u > 0 ? 1 + u : (dist < gate ? 1 - dist / gate : -1);
          if (s > 0.05) pairs.push([s, ti, di]);
        });
      });
      pairs.sort(function (a, b) { return b[0] - a[0]; });
      var usedT = {}, usedD = {}, m = [];
      pairs.forEach(function (p) { if (!usedT[p[1]] && !usedD[p[2]]) { usedT[p[1]] = usedD[p[2]] = 1; m.push(p); } });
      return { matches: m, usedT: usedT, usedD: usedD };
    }
    var a = associate(hi, T);
    a.matches.forEach(function (p) { upd(T[p[1]], hi[p[2]]); });
    var rest = T.filter(function (t, i) { return !a.usedT[i]; });
    var b = associate(lo, rest);
    b.matches.forEach(function (p) { upd(rest[p[1]], lo[p[2]]); });
    function upd(t, d) {
      t.kx.update(d.x + d.w / 2, r); t.ky.update(d.y + d.h / 2, r);
      t.w = 0.7 * t.w + 0.3 * d.w; t.h = 0.7 * t.h + 0.3 * d.h; t.hits++; t.miss = 0; t.cls = d.cls; t.score = d.score;
      t.trail.push([t.kx.x[0], t.ky.x[0]]); if (t.trail.length > 20) t.trail.shift();
    }
    var self = this;
    hi.forEach(function (d, i) {
      if (a.usedD[i]) return;
      self.tracks.push({ id: self.nextId++, kx: new KF1(d.x + d.w / 2), ky: new KF1(d.y + d.h / 2), w: d.w, h: d.h, hits: 1, miss: 0, age: 0, cls: d.cls, score: d.score, trail: [], vPrev: [0, 0] });
    });
    this.tracks = this.tracks.filter(function (t) { return t.miss <= 8; });
    return this.tracks.filter(function (t) { return t.hits >= 2 && t.miss <= 2; });
  };

  /* ------------------------------------------ ONNX detector ---- */
  var ortPromise = null;
  function loadOrt() {
    if (root.ort) return Promise.resolve(root.ort);
    if (!ortPromise) ortPromise = new Promise(function (res, rej) {
      var s = document.createElement("script"); s.src = ORT_URL; s.onload = function () { res(root.ort); }; s.onerror = function () { rej(new Error("Could not load ONNX Runtime Web from jsDelivr.")); };
      document.head.appendChild(s);
    });
    return ortPromise;
  }
  function OnnxDetector(session, size, labels) { this.s = session; this.size = size; this.labels = labels || []; this.canvas = document.createElement("canvas"); this.canvas.width = this.canvas.height = size; }
  OnnxDetector.load = function (source, size, labels) {
    return loadOrt().then(function (ort) {
      var buf = source instanceof Blob ? source.arrayBuffer() : fetch(source).then(function (r) { if (!r.ok) throw new Error("Model download failed: HTTP " + r.status); return r.arrayBuffer(); });
      return buf.then(function (b) { return ort.InferenceSession.create(b, { executionProviders: ["webgpu", "wasm"] }); })
        .then(function (sess) { return new OnnxDetector(sess, size || 320, labels); });
    });
  };
  OnnxDetector.prototype.detect = function (srcCanvas, conf) {
    var S = this.size, ctx = this.canvas.getContext("2d", { willReadFrequently: true }), sw = srcCanvas.width, sh = srcCanvas.height;
    var sc = Math.min(S / sw, S / sh), nw = sw * sc, nh = sh * sc, ox = (S - nw) / 2, oy = (S - nh) / 2;
    ctx.fillStyle = "#727272"; ctx.fillRect(0, 0, S, S); ctx.drawImage(srcCanvas, ox, oy, nw, nh);
    var px = ctx.getImageData(0, 0, S, S).data, input = new Float32Array(3 * S * S);
    for (var i = 0; i < S * S; i++) { input[i] = px[i * 4] / 255; input[S * S + i] = px[i * 4 + 1] / 255; input[2 * S * S + i] = px[i * 4 + 2] / 255; }
    var ort = root.ort, feeds = {}, self = this;
    feeds[this.s.inputNames[0]] = new ort.Tensor("float32", input, [1, 3, S, S]);
    return this.s.run(feeds).then(function (out) {
      var o = out[self.s.outputNames[0]], d = o.data, C = o.dims[1], N = o.dims[2], dets = [];
      for (var j = 0; j < N; j++) {
        var best = 0, bc = 0;
        for (var c = 4; c < C; c++) { var v = d[c * N + j]; if (v > best) { best = v; bc = c - 4; } }
        if (best < (conf || 0.25)) continue;
        var cx = d[j], cy = d[N + j], w = d[2 * N + j], h = d[3 * N + j];
        dets.push({ x: (cx - w / 2 - ox) / sc, y: (cy - h / 2 - oy) / sc, w: w / sc, h: h / sc, score: best, cls: self.labels[bc] || ("class " + bc) });
      }
      dets.sort(function (a, b) { return b.score - a.score; });
      var keep = [];
      dets.forEach(function (q) { if (keep.every(function (k) { return iou(k, q) < 0.45; })) keep.push(q); });
      return keep;
    });
  };

  /* ------------------------------------------------ engine ---- */
  var METRICS = ["count", "speed_bl_s", "polarization_excess", "nnd", "dispersion", "vertical", "activity", "visibility"];
  function Engine(opts) {
    this.o = Object.assign({ width: 320, fps: 6, k: 2.5, minArea: 6, streamId: "unknown" }, opts || {});
    this.work = document.createElement("canvas"); this.ctx = this.work.getContext("2d", { willReadFrequently: true });
    this.tracker = new Tracker(); this.detector = null; this.running = false; this.history = []; this.crop = null;
    this.startles = []; this.baseline = loadBaseline(this.o.streamId);
  }
  Engine.prototype.attach = function (src, overlay, opts) {
    this.src = src; this.video = src.video; this.overlay = overlay; this.bg = null; this.tracker = new Tracker();
    this.boxesOnly = !!(opts && opts.boxesOnly);
    return this;
  };
  Engine.prototype.setCrop = function (rect) { this.crop = rect; this.bg = null; };
  Engine.prototype.start = function (onMetrics) {
    this.cb = onMetrics; this.running = true; this.last = performance.now(); this.tick(); return this;
  };
  Engine.prototype.stop = function () {
    this.running = false; clearTimeout(this.timer);
    if (this.src && this.src.stream && !this.src.keepAlive)
      this.src.stream.getTracks().forEach(function (t) { t.stop(); });
    saveBaseline(this.o.streamId, this.baseline);
  };
  Engine.prototype.tick = function () {
    var self = this; if (!this.running) return;
    var t0 = performance.now();
    this.process().then(function (m) { if (m && self.cb) self.cb(m); }).catch(function (e) { if (self.cb) self.cb({ error: e.message }); })
      .then(function () { var spent = performance.now() - t0; self.timer = setTimeout(function () { self.tick(); }, Math.max(0, 1000 / self.o.fps - spent)); });
  };
  Engine.prototype.process = function () {
    var v = this.video; if (!v || v.readyState < 2 || !v.videoWidth) return Promise.resolve(null);
    var cr = this.crop || { x: 0, y: 0, w: v.videoWidth, h: v.videoHeight };
    var W = this.o.width, H = Math.max(8, Math.round(W * cr.h / cr.w));
    if (this.work.width !== W || this.work.height !== H) { this.work.width = W; this.work.height = H; this.bg = null; }
    this.ctx.drawImage(v, cr.x, cr.y, cr.w, cr.h, 0, 0, W, H);
    var img = this.ctx.getImageData(0, 0, W, H).data, n = W * H, g = new Float32Array(n);
    var sumR = 0, sumG = 0, sumB = 0, sum = 0, sum2 = 0;
    for (var i = 0; i < n; i++) {
      var r = img[i * 4], gg = img[i * 4 + 1], b = img[i * 4 + 2], y = 0.299 * r + 0.587 * gg + 0.114 * b;
      g[i] = y; sum += y; sum2 += y * y; sumR += r; sumG += gg; sumB += b;
    }
    var now = performance.now(), dt = Math.min(2, (now - this.last) / 1000) || 1 / this.o.fps; this.last = now;
    // background model (running mean and variance)
    if (!this.bg) { this.bg = Float32Array.from(g); this.var = new Float32Array(n).fill(64); this.frames = 0; }
    var mask = new Uint8Array(n), a = this.frames < 10 ? 0.3 : 0.03, k2 = this.o.k * this.o.k, fg = 0;
    for (var j = 0; j < n; j++) {
      var d = g[j] - this.bg[j], isFg = d * d > k2 * Math.max(this.var[j], 16);
      mask[j] = isFg ? 1 : 0; if (isFg) fg++;
      var aa = isFg ? a * 0.1 : a;
      this.bg[j] += aa * d; this.var[j] = (1 - aa) * this.var[j] + aa * d * d;
    }
    this.frames++;
    var tmp = new Uint8Array(n); mask = dilate(erode(mask, W, H, tmp), W, H, new Uint8Array(n));
    var lap = 0;
    for (var yy = 1; yy < H - 1; yy++) for (var xx = 1; xx < W - 1; xx++) { var p = yy * W + xx, L = 4 * g[p] - g[p - 1] - g[p + 1] - g[p - W] - g[p + W]; lap += L * L; }
    var mean = sum / n, sd = Math.sqrt(Math.max(sum2 / n - mean * mean, 0));
    var vis = {
      luminance: mean / 255, contrast: sd / 128, sharpness: Math.min(1, Math.sqrt(lap / ((W - 2) * (H - 2))) / 40),
      blue_green: (sumB + sumG) / (2 * sumR + 1), index: 0
    };
    vis.index = Math.max(0, Math.min(1, 0.5 * Math.min(1, vis.contrast * 2.5) + 0.5 * vis.sharpness)) * (vis.luminance < 0.06 ? 0.2 : 1);
    var warm = this.frames < 8;
    var self = this, scale = { x: cr.w / W, y: cr.h / H };
    var detP = this.detector ? this.detector.detect(this.work, this.o.conf) : Promise.resolve(warm ? [] : components(mask, W, H, this.o.minArea));
    return detP.then(function (dets) {
      var tracks = self.tracker.step(dets, dt);
      var m = self.metrics(tracks, W, H, fg / n, vis, dt);
      m.detections = dets.length; m.tracks = tracks; m.source = self.detector ? "ONNX detector" : "motion (background subtraction)";
      m.frame = { w: W, h: H, crop: cr, scale: scale }; m.fps = 1 / dt; m.t = Date.now();
      self.draw(tracks, W, H);
      self.updateBaseline(m);
      return m;
    });
  };
  Engine.prototype.metrics = function (tracks, W, H, activity, vis, dt) {
    var N = tracks.length, diag = Math.hypot(W, H), sp = [], ux = 0, uy = 0, moving = 0, pts = [], cy = 0, startle = 0, self = this;
    tracks.forEach(function (t) {
      var vx = t.kx.x[1], vy = t.ky.x[1], s = Math.hypot(vx, vy), bl = Math.max(2, Math.sqrt(t.w * t.h));
      sp.push(s / bl); pts.push([t.kx.x[0], t.ky.x[0]]); cy += t.ky.x[0] / H;
      if (s > 0.5 * bl) { ux += vx / s; uy += vy / s; moving++; }
      var acc = Math.hypot(vx - t.vPrev[0], vy - t.vPrev[1]) / Math.max(dt, 1e-3) / bl;
      if (t.hits > 4 && acc > 6) startle++;
      t.vPrev = [vx, vy];
    });
    var now = Date.now(); if (startle) this.startles.push([now, startle]);
    this.startles = this.startles.filter(function (q) { return now - q[0] < 60000; });
    var nnd = null;
    if (N >= 2) { var tot = 0; pts.forEach(function (p, i) { var best = Infinity; pts.forEach(function (q, j) { if (i !== j) best = Math.min(best, Math.hypot(p[0] - q[0], p[1] - q[1])); }); tot += best; }); nnd = tot / N / diag; }
    var pol = moving ? Math.hypot(ux, uy) / moving : null;
    var nul = moving ? Math.sqrt(Math.PI) / (2 * Math.sqrt(moving)) : null;   // random-heading baseline (verification K-1)
    return {
      count: N, moving: moving,
      speed_bl_s: sp.length ? sp.reduce(function (a, b) { return a + b; }, 0) / sp.length : null,
      polarization: pol, polarization_null: nul, polarization_excess: pol === null ? null : pol - nul,
      nnd: nnd, dispersion: N >= 3 ? hull(pts) / (W * H) : null, vertical: N ? cy / N : null,
      activity: activity, startles_per_min: this.startles.reduce(function (a, q) { return a + q[1]; }, 0),
      visibility: vis.index, vis: vis, reliable: vis.index >= 0.25 && vis.luminance >= 0.06
    };
  };
  Engine.prototype.draw = function (tracks, W, H) {
    var c = this.overlay; if (!c) return;
    var rect = c.getBoundingClientRect(), dpr = root.devicePixelRatio || 1;
    if (c.width !== Math.round(rect.width * dpr)) { c.width = Math.round(rect.width * dpr); c.height = Math.round(rect.height * dpr); }
    var x = c.getContext("2d"), sx = c.width / W, sy = c.height / H;
    x.clearRect(0, 0, c.width, c.height);
    if (!this.boxesOnly) {
      x.imageSmoothingEnabled = true;
      x.drawImage(this.work, 0, 0, c.width, c.height);
    }
    x.lineWidth = 2 * dpr; x.font = (11 * dpr) + "px system-ui, sans-serif";
    tracks.forEach(function (t) {
      var hue = (t.id * 67) % 360, col = "hsl(" + hue + " 90% 65%)";
      x.strokeStyle = col; x.fillStyle = col;
      x.strokeRect((t.kx.x[0] - t.w / 2) * sx, (t.ky.x[0] - t.h / 2) * sy, t.w * sx, t.h * sy);
      x.beginPath(); t.trail.forEach(function (p, i) { if (i) x.lineTo(p[0] * sx, p[1] * sy); else x.moveTo(p[0] * sx, p[1] * sy); }); x.stroke();
      x.fillText("#" + t.id + (t.cls ? " " + t.cls : ""), (t.kx.x[0] - t.w / 2) * sx, (t.ky.x[0] - t.h / 2) * sy - 3 * dpr);
    });
  };

  /* --------------------------------------------- baselines ---- */
  function loadBaseline(id) { try { return JSON.parse(localStorage.getItem("ag:vision-base:" + id)) || {}; } catch (e) { return {}; } }
  function saveBaseline(id, b) { try { localStorage.setItem("ag:vision-base:" + id, JSON.stringify(b)); } catch (e) {} }
  Engine.prototype.updateBaseline = function (m) {
    if (!m.reliable) { m.anomalies = []; m.flags = ["Low visibility: counts and behaviour here are unreliable, and a drop would look like animals leaving when they are only harder to see."]; return; }
    var B = this.baseline, out = [], flags = [];
    METRICS.forEach(function (k) {
      var v = m[k]; if (v === null || v === undefined || !isFinite(v)) return;
      var s = B[k] || (B[k] = { n: 0, mean: v, var: 0 });
      if (s.n >= 120) { var z = (v - s.mean) / Math.sqrt(s.var + 1e-9); if (Math.abs(z) >= 3) out.push({ metric: k, z: z, value: v, usual: s.mean }); }
      var a = Math.max(0.01, 1 / (s.n + 1)), d = v - s.mean;
      s.mean += a * d; s.var = (1 - a) * (s.var + a * d * d); s.n++;
    });
    out.forEach(function (o) {
      var up = o.z > 0;
      var txt = { count: up ? "More animals in view than usual" : "Fewer animals in view than usual",
        speed_bl_s: up ? "Swimming faster than usual for this view" : "Swimming slower than usual for this view",
        polarization_excess: up ? "Fish are more aligned than usual" : "School alignment has broken up",
        nnd: up ? "Animals are spreading apart" : "Animals are bunching closer together",
        dispersion: up ? "Group covers more of the frame than usual" : "Group has contracted",
        vertical: up ? "Animals sit lower in the frame than usual" : "Animals have moved up in the frame (near the surface or camera top)",
        activity: up ? "More movement than usual" : "Less movement than usual",
        visibility: up ? "Water clearer than usual" : "Water murkier than usual" }[o.metric];
      flags.push(txt + " (z = " + o.z.toFixed(1) + ").");
    });
    m.anomalies = out; m.flags = flags; m.baseline_samples = (B.count || {}).n || 0;
    if ((this.n = (this.n || 0) + 1) % 30 === 0) saveBaseline(this.o.streamId, B);
  };

  /* ------------------------------------------------- relay ---- */
  function connectRelay(streamId, onMetrics) {
    if (!root.AG_RELAY) return null;
    var url = root.AG_RELAY.replace(/^http/, "ws").replace(/\/$/, "") + "/ws/vision/" + encodeURIComponent(streamId);
    var ws = new WebSocket(url);
    ws.onmessage = function (ev) { try { onMetrics(JSON.parse(ev.data)); } catch (e) {} };
    ws.onerror = function () { onMetrics({ error: "Relay connection failed for " + streamId + "." }); };
    return ws;
  }

  root.Vision = { captureTab: captureTab, fromFile: fromFile, fromVideo: fromVideo, Engine: Engine, OnnxDetector: OnnxDetector, connectRelay: connectRelay,
    _internals: { components: components, iou: iou, hull: hull, Tracker: Tracker, KF1: KF1, erode: erode, dilate: dilate } };
})(typeof self !== "undefined" ? self : this);
