/* Aquatic Guardian browser simulation kernels. Apache-2.0.
 * Ports of src/aquatic_guardian numerics, imaging, tracking and bioenergetics.
 * tests/test_sims_parity.py checks these against the Python reference.
 */
(function (root) {
  "use strict";
  var E = root.AquaticGuardian || (typeof require !== "undefined" ? require("./engine.js") : null);

  function mc(r) { return Math.max(0, Math.min(Math.min(2 * r, 0.5 * (1 + r)), 2)); }

  /* 1-D periodic advection-diffusion, identical arithmetic to numerics.advect_diffuse_1d */
  function advect1d(c0, u, k, dx, dt, nSteps, scheme) {
    if (u < 0) return advect1d(c0.slice().reverse(), -u, k, dx, dt, nSteps, scheme).reverse();
    var n = c0.length, c = c0.slice(), cfl = u * dt / dx, i;
    if (cfl > 1 || k * dt / (dx * dx) > 0.5) throw new Error("unstable time step");
    var face = new Array(n), flux = new Array(n), nc = new Array(n);
    for (var s = 0; s < nSteps; s++) {
      for (i = 0; i < n; i++) {
        var cm1 = c[(i - 1 + n) % n], cp1 = c[(i + 1) % n];
        if (scheme === "upwind") face[i] = c[i];
        else {
          var num = c[i] - cm1, den = cp1 - c[i];
          var r = Math.abs(den) > 1e-300 ? num / den : 0.0;
          face[i] = c[i] + 0.5 * mc(r) * (1 - cfl) * (cp1 - c[i]);
        }
        flux[i] = u * face[i];
      }
      for (i = 0; i < n; i++) {
        var a = c[(i - 1 + n) % n], b = c[(i + 1) % n];
        nc[i] = c[i] - dt / dx * (flux[i] - flux[(i - 1 + n) % n]) + k * dt / (dx * dx) * (b - 2 * c[i] + a);
      }
      var tmp = c; c = nc; nc = tmp;
    }
    return c;
  }

  function effectiveK(c0, c1, x, elapsed) {
    function v(c) { var m = 0, mu = 0, s2 = 0, i; for (i = 0; i < c.length; i++) { m += c[i]; mu += x[i] * c[i]; } mu /= m;
      for (i = 0; i < c.length; i++) s2 += (x[i] - mu) * (x[i] - mu) * c[i]; return s2 / m; }
    return (v(c1) - v(c0)) / (2 * elapsed);
  }

  /* 2-D depth-averaged far-field transport on a coast-attached grid.
   * Row 0 is the shoreline (no flux). Open offshore and along-shore boundaries.
   * Signed along-shore velocity; flux-limited (MC) or first-order upwind.
   */
  function Transport2D(nx, ny, dx) {
    this.nx = nx; this.ny = ny; this.dx = dx;
    this.c = new Float32Array(nx * ny); this.n = new Float32Array(nx * ny);
    this.fx = new Float32Array((nx + 1) * ny); this.fy = new Float32Array(nx * (ny + 1));
  }
  Transport2D.prototype.reset = function () { this.c.fill(0); };
  Transport2D.prototype.step = function (u, k, dt, scheme, src) {
    var nx = this.nx, ny = this.ny, dx = this.dx, c = this.c, fx = this.fx, fy = this.fy, i, j;
    var cfl = Math.abs(u) * dt / dx, d = k * dt / (dx * dx);
    function at(ii, jj) {
      if (jj < 0) jj = 0;                       // shoreline mirror (no flux)
      if (jj >= ny) return 0;                   // offshore ambient
      if (ii < 0) return u > 0 ? 0 : c[jj * nx];            // inflow ambient / outflow zero-gradient
      if (ii >= nx) return u < 0 ? 0 : c[jj * nx + nx - 1];
      return c[jj * nx + ii];
    }
    for (j = 0; j < ny; j++) {
      for (i = 0; i <= nx; i++) {               // face between i-1 and i
        var face;
        if (u >= 0) {
          var up = at(i - 1, j), dn = at(i, j), uu = at(i - 2, j);
          if (scheme === "upwind") face = up;
          else { var den = dn - up, r = Math.abs(den) > 1e-12 ? (up - uu) / den : 0; face = up + 0.5 * mc(r) * (1 - cfl) * (dn - up); }
        } else {
          var up2 = at(i, j), dn2 = at(i - 1, j), uu2 = at(i + 1, j);
          if (scheme === "upwind") face = up2;
          else { var den2 = dn2 - up2, r2 = Math.abs(den2) > 1e-12 ? (up2 - uu2) / den2 : 0; face = up2 + 0.5 * mc(r2) * (1 - cfl) * (dn2 - up2); }
        }
        fx[j * (nx + 1) + i] = u * face * dt / dx - d * (at(i, j) - at(i - 1, j));
      }
    }
    for (j = 0; j <= ny; j++) for (i = 0; i < nx; i++)
      fy[j * nx + i] = j === 0 ? 0 : -d * (at(i, j) - at(i, j - 1));
    var nn = this.n;
    for (j = 0; j < ny; j++) for (i = 0; i < nx; i++) {
      var q = j * nx + i;
      nn[q] = c[q] - (fx[j * (nx + 1) + i + 1] - fx[j * (nx + 1) + i]) - (fy[(j + 1) * nx + i] - fy[j * nx + i]);
      if (nn[q] < 0) nn[q] = 0;
    }
    if (src) nn[src.j * nx + src.i] += src.rate * dt;
    this.n = c; this.c = nn;
  };
  Transport2D.prototype.total = function () { var s = 0; for (var q = 0; q < this.c.length; q++) s += this.c[q]; return s; };

  /* Underwater image formation, Akkaynak & Treibitz */
  function imgForward(J, z, bd, bb, binf) { return J * Math.exp(-bd * z) + binf * (1 - Math.exp(-bb * z)); }
  function imgInvert(I, z, bd, bb, binf, tmin) {
    tmin = tmin === undefined ? 0.1 : tmin;
    var t = Math.exp(-bd * z), back = binf * (1 - Math.exp(-bb * z));
    return { J: (I - back) / Math.max(t, tmin), t: t, gain: 1 / Math.max(t, 1e-300), recoverable: t >= tmin };
  }

  /* Bioenergetics (placeholder species), mirrors bioenergetics.py */
  var SPECIES = { name: "generic salmonid (PLACEHOLDER)", tgc: 2.5, t_opt: 15.0, t_max: 22.0, mo2_mg_kg_h_at_tref: 250,
    t_ref: 12.0, q10: 2.3, do_floor_mg_l: 7.0, feed_rate_frac_bw_day: 0.012, feed_protein_frac: 0.45,
    nh3_limit_mg_l: 0.0125, max_density_kg_m3: 30.0, placeholder: true };
  function growthFactor(t, sp) { if (t <= sp.t_opt) return 1.0; if (t >= sp.t_max) return 0.0; return (sp.t_max - t) / (sp.t_max - sp.t_opt); }
  function carrying(t, s, ph, flowM3h, tankM3, sp, fracSat) {
    sp = sp || SPECIES; fracSat = fracSat === undefined ? 1.0 : fracSat;
    var doIn = E.doSat(t, s) * fracSat;
    var budget = Math.max(doIn - sp.do_floor_mg_l, 0.0) * flowM3h * 1000.0;
    var mo2 = sp.mo2_mg_kg_h_at_tref * Math.pow(sp.q10, (t - sp.t_ref) / 10.0);
    var bDo = budget / mo2;
    var tanPerKgDay = sp.feed_rate_frac_bw_day * sp.feed_protein_frac * 0.092 * 1e6;
    var tanLimit = sp.nh3_limit_mg_l / E.nh3Frac(t, ph, s);
    var bNh3 = tanLimit * flowM3h * 24 * 1000.0 / tanPerKgDay;
    var bW = sp.max_density_kg_m3 * tankM3;
    var lim = { "do": bDo, ammonia: bNh3, welfare: bW }, bind = "do";
    if (bNh3 < lim[bind]) bind = "ammonia";
    if (bW < lim[bind]) bind = "welfare";
    return { limits_kg: lim, capacity_kg: lim[bind], binding: bind, do_in_mg_l: doIn };
  }
  function yieldIndex(t, s, ph, flow, tank, sp) {
    sp = sp || SPECIES;
    return carrying(t, s, ph, flow, tank, sp).capacity_kg * Math.min(t, sp.t_opt) * growthFactor(t, sp);
  }

  /* Constant-velocity Kalman filter, one axis, mirrors tracking.kalman_cv */
  function KalmanCV(x0, dt, sigmaX, q) {
    this.dt = dt; this.R = sigmaX * sigmaX; this.q = q;
    this.x = [x0, 0]; this.P = [[this.R, 0], [0, 1]]; this.first = true;
  }
  KalmanCV.prototype.update = function (z) {
    var dt = this.dt, x = this.x, P = this.P, q = this.q;
    if (!this.first) {
      x = [x[0] + dt * x[1], x[1]];
      var p00 = P[0][0] + dt * (P[1][0] + P[0][1]) + dt * dt * P[1][1], p01 = P[0][1] + dt * P[1][1],
        p10 = P[1][0] + dt * P[1][1], p11 = P[1][1];
      P = [[p00 + q * dt * dt * dt / 3, p01 + q * dt * dt / 2], [p10 + q * dt * dt / 2, p11 + q * dt]];
    }
    this.first = false;
    var S = P[0][0] + this.R, K0 = P[0][0] / S, K1 = P[1][0] / S, innov = z - x[0];
    x = [x[0] + K0 * innov, x[1] + K1 * innov];
    P = [[P[0][0] - K0 * P[0][0], P[0][1] - K0 * P[0][1]], [P[1][0] - K1 * P[0][0], P[1][1] - K1 * P[0][1]]];
    this.x = x; this.P = P;
    return x[1];
  };
  function kalmanSeries(obs, dt, sigmaX, q) {  // obs[t][k][ax]
    var steps = obs.length, n = obs[0].length, out = [], t, k, f = [];
    for (k = 0; k < n; k++) f.push([new KalmanCV(obs[0][k][0], dt, sigmaX, q), new KalmanCV(obs[0][k][1], dt, sigmaX, q)]);
    for (t = 0; t < steps; t++) { var row = []; for (k = 0; k < n; k++) row.push([f[k][0].update(obs[t][k][0]), f[k][1].update(obs[t][k][1])]); out.push(row); }
    return out;
  }
  function polarisation(vs) {
    var sx = 0, sy = 0, m = 0;
    for (var i = 0; i < vs.length; i++) { var n = Math.hypot(vs[i][0], vs[i][1]); if (n > 0) { sx += vs[i][0] / n; sy += vs[i][1] / n; m++; } }
    return m ? Math.hypot(sx / m, sy / m) : NaN;
  }

  /* Camera siting, mirrors tracking.fov_width / tracking.camera_screen */
  function fovWidth(d, deg, flat) {
    var half = deg * Math.PI / 360;
    if (flat) half = Math.asin(Math.sin(half) / 1.333);
    return 2 * d * Math.tan(half);
  }
  function cameraScreen(d, deg, px, fps, v, arena, flat) {
    var w = fovWidth(d, deg, flat), ppf = v * px / w / fps, whole = arena <= w, dwell = whole ? Infinity : w / v;
    var risk = whole && ppf < 15 ? "low" : (dwell < 3 || ppf > 30 ? "high" : "moderate");
    return { fov_m: w, px_per_frame: ppf, whole_arena: whole, dwell_s: dwell, risk: risk };
  }

  /* Seeded RNG for reproducible demos */
  function rng(seed) {
    var a = seed >>> 0;
    function next() { a |= 0; a = a + 0x6D2B79F5 | 0; var t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }
    next.normal = function () { var u = 0, v = 0; while (u === 0) u = next(); while (v === 0) v = next(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); };
    return next;
  }

  var api = { advect1d: advect1d, effectiveK: effectiveK, Transport2D: Transport2D, imgForward: imgForward, imgInvert: imgInvert,
    SPECIES: SPECIES, growthFactor: growthFactor, carrying: carrying, yieldIndex: yieldIndex, KalmanCV: KalmanCV,
    kalmanSeries: kalmanSeries, polarisation: polarisation, fovWidth: fovWidth, cameraScreen: cameraScreen, rng: rng };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.AGSims = api;
})(typeof window !== "undefined" ? window : this);
