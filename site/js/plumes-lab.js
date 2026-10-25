/* plumes-lab.js: the "PLUMES 2.0, rebuilt" instrument in the Lab (#/lab/sim-plumes).
 * Runs site/js/plumes2.js (parity-tested mirror of python/plumes2py) on a
 * PLUMES 2.0-style form, overlays the EPA reference run, and writes the
 * output in the PLUMES 2.0 text layout. */
(function () {
  "use strict";
  var U = window.AGU, $ = U.$, fmt = U.fmt, esc = U.esc, P = window.Plumes2;
  var EPA_EXAMPLE = {"diffuser": {"port_diameter": 0.076, "port_elevation": 0.31, "vertical_angle": 45.0, "horizontal_angle": 30.0, "n_ports": 18, "spacing": 6.1, "port_depth": 11.0, "x": 0.0, "y": 0.0, "contraction": 1.0, "axis_deg": null}, "effluent": {"flow": 0.3505010912, "salinity": 0.0, "temperature": 2.63, "concentration": 100.0}, "ambient": {"rows": [{"depth": 0.0, "speed": 0.09, "direction": 0.0, "salinity": 32.0, "temperature": 14.0, "background": 0.0, "decay": 0.0, "far_speed": 0.05, "far_direction": 0.0, "alpha": 0.0003}, {"depth": 2.0, "speed": 0.085, "direction": 0.0, "salinity": 32.0, "temperature": 12.0, "background": 0.0, "decay": 0.0, "far_speed": 0.05, "far_direction": 0.0, "alpha": 0.0003}, {"depth": 4.0, "speed": 0.07, "direction": 0.0, "salinity": 32.0, "temperature": 8.0, "background": 0.0, "decay": 0.0, "far_speed": 0.05, "far_direction": 0.0, "alpha": 0.0003}, {"depth": 6.0, "speed": 0.065, "direction": 0.0, "salinity": 32.0, "temperature": 8.0, "background": 0.0, "decay": 0.0, "far_speed": 0.05, "far_direction": 0.0, "alpha": 0.0003}, {"depth": 8.0, "speed": 0.06, "direction": 0.0, "salinity": 32.0, "temperature": 8.0, "background": 0.0, "decay": 0.0, "far_speed": 0.05, "far_direction": 0.0, "alpha": 0.0003}, {"depth": 10.0, "speed": 0.055, "direction": 0.0, "salinity": 32.0, "temperature": 8.0, "background": 0.0, "decay": 0.0, "far_speed": 0.05, "far_direction": 0.0, "alpha": 0.0003}, {"depth": 12.0, "speed": 0.05, "direction": 0.0, "salinity": 32.0, "temperature": 8.0, "background": 0.0, "decay": 0.0, "far_speed": 0.05, "far_direction": 0.0, "alpha": 0.0003}]}, "mixing_zone": {"acute": 10.2, "chronic": 102.0}, "settings": {"aspiration": 0.1, "step_mass_fraction": 0.02, "stop_at_bottom": true, "stop_at_surface": true, "stop_at_shoreline": false, "shoreline_distance": 0.0, "shoreline_angle": 0.0, "max_rise_fall": 2, "nearfield_output_interval": 5, "farfield": true, "farfield_case": "four_thirds", "farfield_output_interval": 5.0, "farfield_max_dilution": 5000.0, "farfield_stop_distance": 102.0, "max_steps": 50000, "entrainment": "sum", "shear_velocity": "relative", "dt_mode": "unmerged", "forced_scale": 0.81, "forced_terms": [1.0, 1.0, 1.0], "wastefield_rule": "diffuser_length_plus_diameter"}, "name": "PLUMES2.0 Example_project"};
  var EPA_REF_NEAR = [[5, 1.101, 0.083, 0.011, 0.007, -10.987], [10, 1.213, 0.091, 0.024, 0.014, -10.972], [15, 1.337, 0.101, 0.038, 0.022, -10.956], [20, 1.474, 0.111, 0.054, 0.031, -10.938], [25, 1.624, 0.122, 0.071, 0.04, -10.919], [30, 1.791, 0.135, 0.089, 0.051, -10.898], [35, 1.975, 0.149, 0.11, 0.063, -10.874], [40, 2.178, 0.164, 0.133, 0.076, -10.848], [45, 2.402, 0.181, 0.158, 0.09, -10.82], [50, 2.65, 0.199, 0.185, 0.105, -10.789], [55, 2.923, 0.22, 0.216, 0.122, -10.754], [60, 3.225, 0.242, 0.249, 0.141, -10.717], [65, 3.558, 0.266, 0.286, 0.161, -10.676], [70, 3.926, 0.293, 0.326, 0.183, -10.631], [75, 4.332, 0.323, 0.37, 0.207, -10.582], [80, 4.78, 0.355, 0.419, 0.233, -10.528], [85, 5.275, 0.391, 0.472, 0.261, -10.469], [90, 5.822, 0.43, 0.53, 0.292, -10.405], [95, 6.425, 0.472, 0.594, 0.325, -10.335], [100, 7.092, 0.518, 0.663, 0.36, -10.259], [105, 7.827, 0.569, 0.738, 0.399, -10.176], [110, 8.64, 0.624, 0.82, 0.44, -10.085], [115, 9.536, 0.683, 0.91, 0.484, -9.987], [120, 10.527, 0.747, 1.007, 0.531, -9.879], [125, 11.62, 0.817, 1.111, 0.581, -9.763], [130, 12.827, 0.892, 1.225, 0.633, -9.636], [135, 14.159, 0.972, 1.346, 0.689, -9.499], [140, 15.631, 1.059, 1.476, 0.747, -9.351], [145, 17.255, 1.151, 1.614, 0.806, -9.192], [150, 19.049, 1.25, 1.758, 0.867, -9.024], [155, 21.029, 1.355, 1.91, 0.929, -8.844], [160, 23.215, 1.467, 2.069, 0.992, -8.654], [165, 25.629, 1.586, 2.235, 1.055, -8.453], [170, 28.294, 1.713, 2.407, 1.118, -8.241], [175, 31.236, 1.847, 2.586, 1.181, -8.017], [180, 34.485, 1.988, 2.771, 1.244, -7.782], [185, 38.072, 2.139, 2.963, 1.306, -7.536], [190, 42.032, 2.298, 3.162, 1.367, -7.278], [195, 46.404, 2.466, 3.369, 1.427, -7.008], [200, 51.232, 2.644, 3.583, 1.486, -6.726], [205, 56.562, 2.832, 3.805, 1.544, -6.432], [210, 62.446, 3.031, 4.035, 1.6, -6.126], [215, 68.943, 3.241, 4.275, 1.655, -5.807], [220, 76.117, 3.463, 4.525, 1.708, -5.475], [225, 84.036, 3.698, 4.785, 1.76, -5.132], [230, 92.781, 3.947, 5.057, 1.811, -4.775], [235, 102.435, 4.209, 5.341, 1.86, -4.406], [240, 113.094, 4.486, 5.639, 1.907, -4.024], [245, 124.863, 4.784, 5.949, 1.952, -3.632], [250, 137.648, 5.144, 6.256, 1.994, -3.263], [255, 147.499, 5.462, 6.466, 2.02, -3.029], [260, 155.017, 5.722, 6.621, 2.038, -2.869], [265, 161.123, 5.987, 6.763, 2.055, -2.732], [270, 165.961, 6.243, 6.894, 2.069, -2.614], [275, 169.754, 6.481, 7.017, 2.082, -2.512]]; // step, dilution, diameter, x, y, depth (ModelResults_TxtOutputs.dat)
  var EPA_REF_FAR = [[169.754, 110.588, 7.32, 0.016], [169.754, 111.537, 10.0, 0.031], [169.754, 113.306, 15.0, 0.06], [169.754, 115.067, 20.0, 0.088], [169.755, 116.83, 25.0, 0.115], [169.759, 118.599, 30.0, 0.143], [169.778, 120.376, 35.0, 0.171], [169.828, 122.16, 40.0, 0.199], [169.932, 123.952, 45.0, 0.227], [170.109, 125.752, 50.0, 0.255], [170.374, 127.559, 55.0, 0.282], [170.739, 129.374, 60.0, 0.31], [171.208, 131.196, 65.0, 0.338], [171.785, 133.026, 70.0, 0.366], [172.468, 134.863, 75.0, 0.393], [173.253, 136.708, 80.0, 0.421], [174.137, 138.561, 85.0, 0.449], [175.114, 140.42, 90.0, 0.476], [176.179, 142.288, 95.0, 0.504], [177.326, 144.163, 100.0, 0.532], [178.408, 145.833, 104.435, 0.556]]; // dilution, width, distance, time_h (shipped program)
  var DIFF = ["port_diameter", "port_elevation", "vertical_angle", "horizontal_angle", "n_ports", "spacing", "port_depth", "contraction"];
  var EFF = ["flow", "salinity", "temperature", "concentration"];
  var state = { sc: null, res: null, preset: "epa", dirty: false };

  function dcPreset() { return P.buildDataCentre({}, { sst_c: 12, salinity: 31, current_ms: 0.15 }); }
  function fill(sc) {
    DIFF.forEach(function (k) { $("#pl-" + k).value = sc.diffuser[k] == null ? "" : +(+sc.diffuser[k]).toPrecision(6); });
    EFF.forEach(function (k) { $("#pl-" + k).value = +(+sc.effluent[k]).toPrecision(6); });
    $("#pl-acute").value = sc.mixing_zone.acute == null ? "" : sc.mixing_zone.acute;
    $("#pl-chronic").value = sc.mixing_zone.chronic == null ? "" : sc.mixing_zone.chronic;
    $("#pl-ambient").value = (sc.ambient.rows || sc.ambient).map(function (r) {
      return [r.depth, r.speed, r.direction, r.salinity, r.temperature, r.far_speed == null ? r.speed : r.far_speed, r.alpha == null ? 0.0003 : r.alpha].join(", ");
    }).join("\n");
    var s = Object.assign(P.defaults(), sc.settings || {});
    $("#pl-farfield_case").value = s.farfield_case; $("#pl-max_rise_fall").value = String(s.max_rise_fall);
    $("#pl-aspiration").value = s.aspiration; $("#pl-forced_scale").value = s.forced_scale;
  }
  function read() {
    var base = JSON.parse(JSON.stringify(state.sc)), num = function (id) { var v = $("#pl-" + id).value; return v === "" ? null : +v; };
    DIFF.forEach(function (k) { base.diffuser[k] = num(k); });
    base.diffuser.n_ports = Math.max(1, Math.round(base.diffuser.n_ports || 1));
    EFF.forEach(function (k) { base.effluent[k] = num(k); });
    base.mixing_zone = { acute: num("acute"), chronic: num("chronic") };
    var rows = $("#pl-ambient").value.split(/\n+/).map(function (l) { return l.split(/[,;\t ]+/).filter(Boolean).map(Number); })
      .filter(function (r) { return r.length >= 5 && r.every(isFinite); })
      .map(function (r) { return { depth: r[0], speed: r[1], direction: r[2], salinity: r[3], temperature: r[4], far_speed: r.length > 5 ? r[5] : r[1], far_direction: r[2], alpha: r.length > 6 ? r[6] : 0.0003, background: 0, decay: 0 }; });
    if (rows.length < 1) throw new Error("The ambient profile needs at least one row of five numbers: depth, current, direction, salinity, temperature.");
    base.ambient = { rows: rows };
    base.settings = Object.assign({}, base.settings, { farfield_case: $("#pl-farfield_case").value, max_rise_fall: +$("#pl-max_rise_fall").value,
      aspiration: num("aspiration"), forced_scale: num("forced_scale"), farfield_stop_distance: base.mixing_zone.chronic });
    return base;
  }

  function run() {
    var msg = $("#pl-msg"), sc, res, rule = $("#pl-rule").value;
    try { sc = read(); res = P.run(sc, { rule: rule || null }); }
    catch (e) { msg.textContent = "The model stopped: " + e.message; return; }
    state.sc = sc; state.res = res;
    var showRef = state.preset === "epa" && !state.dirty;
    msg.textContent = res.engine + ": " + res.nearfield.steps.length + " near-field steps, ended at " + res.nearfield.termination + ".";
    var m = res.metrics, nf = m.nearfield, th = m.thermal;
    var cells = [["Near-field dilution", fmt(nf.dilution, 1) + "×"], ["Centreline dilution", fmt(nf.centerline_dilution, 1) + "×"], ["Plume diameter", fmt(nf.diameter_m, 2) + " m"],
      [{ surface: "Surfaced at depth", bottom: "Met seabed at depth", "trap level": "Trapped at depth", "second trap level": "Settled at depth" }[res.nearfield.termination] || "Stopped at depth", fmt(nf.depth_m, 2) + " m"], ["Trap depth", nf.trap_depth_m == null ? "none" : fmt(nf.trap_depth_m, 2) + " m"],
      ["Chronic-edge dilution", m.farfield && m.farfield.dilution_chronic ? fmt(m.farfield.dilution_chronic, 1) + "×" : "n/a"],
      ["Chronic-edge temperature change", th.dt_chronic_c == null ? "n/a" : fmt(th.dt_chronic_c, 3) + " °C"], ["Heat relative to ambient", fmt(m.heat.heat_to_water_mw, 2) + " MW"]];
    $("#pl-ro").innerHTML = cells.map(function (c) { return '<div class="ro"><b>' + esc(c[1]) + "</b><span>" + c[0] + "</span></div>"; }).join("");
    drawTraj(res, showRef); drawRecon(res, sc, showRef); validation(res, showRef);
    $("#pl-txt").textContent = textReport(sc, res);
  }
  function drawTraj(res, showRef) {
    var st = res.nearfield.steps, xs = st.map(function (s) { return s.x; }), last = st[st.length - 1];
    var xmax = Math.max.apply(null, xs.concat([1])) * 1.15, zmin = -(st[0].depth + 1.5);
    var series = [
      { pts: st.map(function (s) { return [s.x, -(s.depth - s.diameter / 2)]; }), color: "#eb7958", width: 1.2, dash: "3 3" },
      { pts: st.map(function (s) { return [s.x, -(s.depth + s.diameter / 2)]; }), color: "#eb7958", width: 1.2, dash: "3 3" },
      { pts: st.map(function (s) { return [s.x, -s.depth]; }), color: "#F7B24A", width: 2.4 }];
    var points = showRef ? EPA_REF_NEAR.filter(function (r, i) { return i % 3 === 0 || i === EPA_REF_NEAR.length - 1; }).map(function (r) { return { x: r[3], y: r[5], r: 4, color: "#9ED8E6" }; }) : [];
    U.chart($("#pl-traj"), { x: { min: 0, max: xmax, label: "x-distance from the outfall (m)" }, y: { min: zmin, max: 0.5, label: "Depth (m)", fmt: function (v) { return fmt(v, 0); } },
      series: series, points: points, hlines: [{ y: 0, color: "#9ED8E6", label: "surface" }].concat(res.nearfield.events.filter(function (e) { return e.event === "trap"; }).map(function (e) { return { y: -e.depth, color: "#C9A3FF", dash: "4 4", label: "trap level", left: true }; })) });
    void last;
  }
  function drawRecon(res, sc, showRef) {
    var st = res.nearfield.steps, ff = res.farfield, pts = [], cl = [];
    st.forEach(function (s) { var d = Math.max(s.distance, 0.01); pts.push([d, s.dilution]); cl.push([d, s.centerline_dilution]); });
    if (ff) ff.rows.forEach(function (r) { pts.push([Math.max(r.distance, 0.01), r.dilution]); });
    var dmax = Math.max(pts[pts.length - 1][0], sc.mixing_zone.chronic || 10) * 1.3, ymax = Math.max.apply(null, pts.map(function (p) { return p[1]; })) * 1.6;
    var refPts = showRef ? EPA_REF_FAR.map(function (r) { return { x: r[2], y: r[0], r: 3.5, color: "#9ED8E6" }; }) : [];
    var v = [];
    if (sc.mixing_zone.acute) v.push({ x: sc.mixing_zone.acute, color: "#C9A3FF", dash: "4 4", label: "acute" });
    if (sc.mixing_zone.chronic) v.push({ x: sc.mixing_zone.chronic, color: "#FF9470", dash: "4 4", label: "chronic", dy: 14 });
    U.chart($("#pl-recon"), { x: { min: 0.01, max: dmax, log: true, label: "Horizontal distance from the outfall (m)" }, y: { min: 1, max: ymax, log: true, label: "Dilution" },
      series: [{ pts: pts, color: "#F7B24A", width: 2.4 }, { pts: cl, color: "#9ED8E6", width: 1.6, dash: "5 4" }], points: refPts, vlines: v });
  }
  function validation(res, showRef) {
    var t = $("#pl-val");
    if (!showRef) { t.innerHTML = ""; return; }
    var e = res.nearfield.end, R = EPA_REF_NEAR[EPA_REF_NEAR.length - 1], ff = res.farfield;
    var at100 = ff && ff.rows.filter(function (r) { return Math.abs(r.distance - 100) < 1e-6; })[0];
    var rows = [["Dilution where the plume surfaces", R[1], e.dilution], ["Plume diameter (m)", R[2], e.diameter], ["x (m)", R[3], e.x], ["y (m)", R[4], e.y], ["Depth (m)", -R[5], e.depth],
      ["Dilution 5 steps in", EPA_REF_NEAR[0][1], res.nearfield.steps[5].dilution], ["Dilution 25 steps in", EPA_REF_NEAR[4][1], res.nearfield.steps[25].dilution]];
    if (at100) rows.push(["Far-field dilution at 100 m (manual Fig. 12)", 176.666, at100.dilution]);
    t.innerHTML = "<thead><tr><th>EPA reference case</th><th>PLUMES 2.0</th><th>This engine</th><th>Difference</th></tr></thead><tbody>" + rows.map(function (r) {
      var d = 100 * (r[2] / r[1] - 1);
      return "<tr><td>" + esc(r[0]) + "</td><td>" + fmt(r[1], 3) + "</td><td>" + fmt(r[2], 3) + '</td><td class="' + (Math.abs(d) <= 1.5 ? "ok" : "warn") + '">' + (d >= 0 ? "+" : "") + fmt(d, 2) + " %</td></tr>";
    }).join("") + "</tbody>";
  }
  function pad(v, w, d) { var s = typeof v === "number" ? v.toFixed(d == null ? 3 : d) : String(v); while (s.length < w) s = " " + s; return s; }
  function textReport(sc, res) {
    var L = [], d = sc.diffuser, e = sc.effluent, mz = sc.mixing_zone, line = new Array(101).join("-");
    L.push(new Array(101).join("*"), line, "Ambient Table:", "     Depth   Amb-cur   Amb-dir   Amb-sal   Amb-tem   Far-spd   Disprsn", "       (m)     (m/s)     (deg)     (psu)       (C)     (m/s)(m0.67/s2)");
    sc.ambient.rows.forEach(function (r) { L.push(pad(r.depth, 10) + pad(r.speed, 10) + pad(r.direction, 10) + pad(r.salinity, 10) + pad(r.temperature, 10) + pad(r.far_speed, 10) + pad(r.alpha, 10, 5)); });
    L.push(line, "Diffuser Table:", "     P-dia    P-elev   V-angle   H-angle     Ports   Spacing   AcuteMZ   ChrncMZ   P-depth   Ttl-flo   Eff-sal      Temp   Polutnt",
      "       (m)       (m)     (deg)     (deg)       ( )       (m)       (m)       (m)       (m)    (m3/s)     (psu)       (C)    (mg/L)",
      pad(d.port_diameter, 10) + pad(d.port_elevation, 10, 2) + pad(d.vertical_angle, 10, 2) + pad(d.horizontal_angle, 10, 2) + pad(d.n_ports, 10, 2) + pad(d.spacing, 10, 2) +
      pad(mz.acute || 0, 10, 2) + pad(mz.chronic || 0, 10, 2) + pad(d.port_depth, 10, 2) + pad(e.flow, 10, 4) + pad(e.salinity, 10, 2) + pad(e.temperature, 10, 2) + pad(e.concentration, 10, 2),
      line, "Simulation Results:", "              Dilutn    CL-Dil     P-dia    x-posn    y-posn     Depth", "      Step (FluxAvg)        ()       (m)       (m)       (m)       (m)");
    var ev = {}; res.nearfield.events.forEach(function (x) { (ev[x.step] = ev[x.step] || []).push(x.text); });
    var st = res.nearfield.steps, lastStep = st[st.length - 1].step;
    st.slice(1).forEach(function (s) {
      (ev[s.step] || []).forEach(function (t) { var b = " " + t + " ", n = Math.max(0, 70 - b.length), l = Math.floor(n / 2); L.push(new Array(l + 1).join("-") + b + new Array(n - l + 1).join("-")); });
      if (s.step % 5 === 0 || s.step === lastStep) L.push(pad(s.step, 10, 0) + pad(s.dilution, 10) + pad(s.centerline_dilution, 10) + pad(s.diameter, 10) + pad(s.x, 10) + pad(s.y, 10) + pad(-s.depth, 10));
    });
    var en = res.nearfield.end;
    L.push(pad("exact", 10) + pad(en.dilution, 10) + pad(en.centerline_dilution, 10) + pad(en.diameter, 10) + pad(en.x, 10) + pad(en.y, 10) + pad(-en.depth, 10) + "   <- boundary contact, interpolated");
    var ff = res.farfield;
    if (ff) {
      L.push("-------------------- Starting Farfield Calculations --------------------", "Farfield dispersion based on wastefield width of : " + pad(ff.w0, 10, 2) + " (m)",
        { four_thirds: "4/3 Power Law based Eddy Diffusivity is used:", linear: "Linearly varying Eddy Diffusivity is used:", constant: "Constant Eddy Diffusivity is used:" }[ff.case],
        "  Dilution     Width  Distance      Time     dT(C)", "        ()       (m)       (m)    (hrs.)  (centre)");
      ff.rows.forEach(function (r) { L.push(pad(r.dilution, 10) + pad(r.width, 10) + pad(r.distance, 10) + pad(r.time_h, 10) + pad(r.delta_t, 10) + (r.note && r.note !== "start" ? "   " + r.note : "")); });
    }
    var m = res.metrics;
    L.push("", "Extended metrics (plumes2py; not in PLUMES 2.0)", "Regime: " + m.flow_class.regime + "; port Froude " + fmt(m.flow_class.port_froude, 1),
      "Heat to water " + fmt(m.heat.heat_to_water_mw, 2) + " MW; discharge " + fmt(m.thermal.dt_discharge_c, 2) + " C above ambient; chronic edge " + fmt(m.thermal.dt_chronic_c, 3) + " C",
      "Organism dose along the centreline: " + fmt(m.exposure.degree_minutes, 1) + " C-min");
    if (m.merging) L.push("Merging penalty vs isolated port: " + fmt(m.merging.penalty_pct, 1) + " %");
    if (res.compliance) L.push("Screening: " + res.compliance.verdict + " (" + res.compliance.rule.source + ")");
    res.caveats.forEach(function (c) { L.push("Caveat: " + c); });
    return L.join("\n");
  }
  function load(preset) {
    state.preset = preset; state.dirty = false;
    state.sc = JSON.parse(JSON.stringify(preset === "dc" ? dcPreset() : EPA_EXAMPLE));
    fill(state.sc); $("#pl-rule").value = preset === "dc" ? "wa_marine" : ""; run();
  }
  function init() {
    if (!$("#sim-plumes")) return;
    $("#pl-preset").addEventListener("change", function (e) { load(e.target.value); });
    $("#pl-run").addEventListener("click", run);
    $("#pl-form").addEventListener("input", function () { state.dirty = true; });
    $("#pl-form").addEventListener("change", function (e) { if (e.target.id !== "pl-preset") { state.dirty = true; run(); } });
    $("#pl-dl-txt").addEventListener("click", function () { U.download("plumes2py_output.txt", $("#pl-txt").textContent, "text/plain"); });
    $("#pl-dl-json").addEventListener("click", function () { try { U.download("scenario.json", JSON.stringify(read(), null, 2), "application/json"); } catch (e) { $("#pl-msg").textContent = e.message; } });
    load("epa");
  }
  U.plumesLoad = function (sc) { state.preset = "custom"; state.dirty = true; state.sc = JSON.parse(JSON.stringify(sc)); if ($("#pl-port_diameter")) { fill(state.sc); run(); } };
  U.download = U.download || function (name, text, type) { var a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([text], { type: type })); a.download = name; document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500); };
  var prev = U.inits.lab;
  U.inits.lab = function (sub) { if (prev) prev(sub); init(); };
})();
