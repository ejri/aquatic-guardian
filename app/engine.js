/* Aquatic Guardian screening engine (JavaScript mirror of src/aquatic_guardian/screening.py).
 * Apache-2.0. Parity with the Python reference is checked by tests/test_engine_parity.py.
 * Screening only: conservative slack-water, stagnant, unstratified near-field assumptions.
 */
(function (root) {
  "use strict";
  var G = 9.81, CP_SEA = 3990.0, CP_FRESH = 4184.0;
  var MGD_TO_M3S = 3.785411784e3 / 86400.0, THROUGH_SCREEN = 0.5 * 0.3048;
  var M2 = 12.4206012 * 3600.0, OMEGA = 2 * Math.PI / M2;
  var C_POINT = 0.089, C_LINE = 0.38, JET_DECAY = 5.6;
  var COOLING = { once_through: 1.0, hybrid: 0.5, closed_loop_air: 0.0 };
  var WA = { extraordinary: 13.0, excellent: 16.0, good: 19.0, fair: 22.0 };
  var F_TO_K = 5 / 9;

  /* Mirror of the intake_rules and jurisdictions sections of data/criteria.json.
   * tests/test_engine_parity.py fails if these tables drift from that file. */
  var INTAKE_RULES = {
    us_cwa_316b: { label: "US cooling-water intake rules", country: "US", status: "rule",
      source: "Clean Water Act \u00a7316(b) and 40 CFR Part 125 (2 MGD design-intake trigger, 25 % cooling-use test, and the 1 % tidal-excursion-volume test for new facilities in estuaries at 40 CFR 125.84)" },
    ca_fisheries_act: { label: "Fisheries Act (Canada)", country: "CA", status: "rule",
      source: "Fisheries Act s.34(1), s.35 and s.36(3): water changed by heat can be a deleterious substance, and intake works can harmfully alter fish habitat. No numeric intake threshold." },
    none: { label: "No intake rule applied", country: null, status: "placeholder",
      source: "This repository does not yet transcribe an intake rule for this jurisdiction. The \u00a7316(b) arithmetic is still shown for comparison but no intake requirement is asserted." }
  };
  var JURISDICTIONS = [
    { id: "us-wa", label: "Washington (United States)", country: "US", status_as_of: "2026-09-29",
      temperature_rule: "wa_marine", temperature_status: "rule",
      temperature_source: "WAC 173-201A-210(1)(c)", intake_rule: "us_cwa_316b",
      note: "Marine water-body categories set a 1-DMax criterion; a point source may add no more than 12/(T-2) \u00b0C at the edge of the mixing zone, and no more than 0.3 \u00b0C where the criterion is already exceeded naturally. Pick the category for the receiving water below.",
      verify: false },
    { id: "us-ca", label: "California (United States)", country: "US", status_as_of: "2026-09-29",
      temperature_rule: "ca_new_coastal", temperature_status: "rule",
      temperature_source: "California Thermal Plan \u00a73.B.(3)\u2013(4), coastal waters, new discharges (SWRCB; text transcribed in data/checks/ca_thermal_plan.md)",
      intake_rule: "us_cwa_316b",
      note: "New coastal discharges: no more than 4 \u00b0F (2.22 \u00b0C) above natural at the shoreline, the ocean substrate, or the ocean surface beyond 1,000 ft, and no more than 20 \u00b0F (11.1 \u00b0C) above natural at the discharge itself.",
      verify: false },
    { id: "us-or", label: "Oregon (United States)", country: "US", status_as_of: "2026-09-29",
      temperature_rule: "custom", temperature_status: "placeholder", temperature_source: null,
      intake_rule: "us_cwa_316b",
      note: "Oregon's numeric temperature standard is not transcribed in this repository, so no state increment is applied. Enter the increment from the applicable standard or permit. Federal intake rules still apply.",
      verify: true,
      verify_note: "Needs Oregon's temperature standard transcribed from the primary rule text before this jurisdiction can carry a numeric increment." },
    { id: "us-other", label: "Other United States state or federal waters", country: "US", status_as_of: "2026-09-29",
      temperature_rule: "custom", temperature_status: "placeholder", temperature_source: null,
      intake_rule: "us_cwa_316b",
      note: "Federal intake rules apply nationally, but this repository transcribes state temperature standards only for Washington and California. Enter the increment your state standard or permit sets.",
      verify: true,
      verify_note: "No state temperature standard transcribed; the increment is user-supplied." },
    { id: "ca-bc", label: "British Columbia (Canada)", country: "CA", status_as_of: "2026-09-29",
      temperature_rule: "custom", temperature_status: "placeholder", temperature_source: null,
      intake_rule: "ca_fisheries_act",
      note: "British Columbia sets thermal limits in the waste discharge authorisation issued under the Environmental Management Act, so the numeric increment is permit-specific rather than a published standard. Enter the increment the authorisation sets.",
      verify: true,
      verify_note: "Permit-specific: no published numeric marine thermal increment is transcribed in this repository." },
    { id: "eu", label: "European Union member state", country: "EU", status_as_of: "2026-09-29",
      temperature_rule: "custom", temperature_status: "placeholder", temperature_source: null,
      intake_rule: "none",
      note: "Water temperature is a supporting element of ecological status under the Water Framework Directive, but the numeric limit comes from the member state's water permit. Enter that increment. EU law sets no cooling-water intake screening rule equivalent to \u00a7316(b).",
      verify: true,
      verify_note: "Member-state permit values and any national thermal standard are not transcribed in this repository." },
    { id: "other", label: "Other or not listed", country: null, status_as_of: "2026-09-29",
      temperature_rule: "custom", temperature_status: "placeholder", temperature_source: null,
      intake_rule: "none",
      note: "No jurisdiction-specific rule is applied and no intake requirement is asserted. Enter the increment from the applicable standard or permit and treat the result as arithmetic only.",
      verify: true,
      verify_note: "No rules transcribed for this selection." }
  ];

  function jurisdiction(id) {
    var j = null;
    for (var i = 0; i < JURISDICTIONS.length; i++) if (JURISDICTIONS[i].id === id) j = JURISDICTIONS[i];
    if (!j) throw new Error("unknown jurisdiction " + id);
    var intake = INTAKE_RULES[j.intake_rule];
    return { id: j.id, label: j.label, country: j.country, temperature_rule: j.temperature_rule,
      temperature_status: j.temperature_status, temperature_source: j.temperature_source,
      status_as_of: j.status_as_of, note: j.note, verify: j.verify,
      verify_note: j.verify_note === undefined ? null : j.verify_note,
      intake_rule: j.intake_rule, intake_label: intake.label, intake_status: intake.status,
      intake_source: intake.source };
  }

  var DEFAULTS = {
    it_load_mw: 24.0, pue: 1.15, cooling_type: "once_through", fraction_to_water: null,
    reuse_fraction: 0.0, delta_t_k: 8.0, water_type: "marine", t_ambient_c: 12.0, s_psu: 30.0,
    ph: 8.0, u_peak_ms: 0.3, depth_m: 20.0, n_ports: 10, port_diameter_m: 0.3,
    port_spacing_m: 4.0, cooling_fraction: 1.0, jurisdiction: "us-wa", temperature_rule: null,
    wa_category: "excellent", custom_increment_k: 1.0, grid_dx_m: 25.0, grid_dt_s: 10.0,
    aquaculture_reuse: false
  };

  function density(t, s) {
    var rw = 999.842594 + 6.793952e-2 * t - 9.095290e-3 * t * t + 1.001685e-4 * Math.pow(t, 3)
      - 1.120083e-6 * Math.pow(t, 4) + 6.536332e-9 * Math.pow(t, 5);
    var a = 8.24493e-1 - 4.0899e-3 * t + 7.6438e-5 * t * t - 8.2467e-7 * Math.pow(t, 3) + 5.3875e-9 * Math.pow(t, 4);
    var b = -5.72466e-3 + 1.0227e-4 * t - 1.6546e-6 * t * t;
    s = Math.max(s, 0);
    return rw + a * s + b * Math.pow(s, 1.5) + 4.8314e-4 * s * s;
  }
  function rhoCp(t, s) {
    var cp = CP_FRESH + (CP_SEA - CP_FRESH) * Math.min(Math.max(s, 0), 35) / 35;
    return density(t, s) * cp;
  }
  function reducedGravity(ta, dt, s) {
    var ra = density(ta, s), re = density(ta + dt, s);
    return G * (ra - re) / ra;
  }
  function doSat(t, s) {
    var A = [2.00907, 3.22014, 4.05010, 4.94457, -2.56847e-1, 3.88767];
    var B = [-6.24523e-3, -7.37614e-3, -1.03410e-2, -8.17083e-3];
    var ts = Math.log((298.15 - t) / (273.15 + t));
    var ln = A[0] + A[1] * ts + A[2] * ts * ts + A[3] * Math.pow(ts, 3) + A[4] * Math.pow(ts, 4) + A[5] * Math.pow(ts, 5)
      + s * (B[0] + B[1] * ts + B[2] * ts * ts + B[3] * Math.pow(ts, 3)) - 4.88682e-7 * s * s;
    return Math.exp(ln) * 1.42905;
  }
  function pka(t, s) {
    var p = 0.09018 + 2729.92 / (t + 273.2);
    if (s > 0) { var I = 19.9273 * s / (1000 - 1.005109 * s); p += (0.1552 - 0.0003142 * t) * I; }
    return p;
  }
  function nh3Frac(t, ph, s) { return 1 / (1 + Math.pow(10, pka(t, s) - ph)); }
  function okubo(L) { return 0.0103 * Math.pow(L * 100, 1.15) * 1e-4; }
  function okuboCross(k) { return Math.pow(k * 1e4 / 0.0103, 1 / 1.15) / 100; }
  function kNum(u, dx, dt) { var c = dt ? Math.abs(u) * dt / dx : 0; return Math.abs(u) * dx / 2 * (1 - c); }

  function temperatureRule(rule, t, cat, custom) {
    if (rule === "wa_marine") {
      var crit = WA[cat];
      if (t >= crit) return { criterion_c: crit, allowed_increment_k: 0.3, basis: "natural exceedance: 0.3 C cap" };
      var formula = t > 2 ? 12 / (t - 2) : Infinity, head = crit - t;
      if (formula <= head) return { criterion_c: crit, allowed_increment_k: formula, basis: "12/(T-2) at mixing-zone edge" };
      return { criterion_c: crit, allowed_increment_k: head, basis: "headroom to criterion" };
    }
    if (rule === "ca_new_coastal") return { criterion_c: null, allowed_increment_k: 4 * F_TO_K,
      max_discharge_delta_k: 20 * F_TO_K, basis: "CA Thermal Plan (new coastal): 4 F at surface beyond 1,000 ft" };
    if (rule === "custom") return { criterion_c: null, allowed_increment_k: +custom, basis: "permit-specific increment" };
    throw new Error("unknown rule " + rule);
  }

  function nearField(flow, n, d, sp, depth, ta, dt, s, u) {
    var gp = reducedGravity(ta, dt, s);
    var Q = flow / n, uj = Q / (Math.PI * d * d / 4), M = Q * uj, Bf = gp * Q;
    var L = n > 1 ? n * sp : d, q = flow / L, b = gp * q;
    var lM = Bf > 0 ? Math.pow(M, 0.75) / Math.sqrt(Bf) : Infinity;
    var r = sp / depth, reg = n <= 1 ? "point" : (r <= 0.3 ? "line" : (r >= 1.0 ? "point" : "transitional"));
    var z = depth, sJet = z / (JET_DECAY * d);
    var sPt = gp > 0 ? Math.max(C_POINT * Math.pow(Bf, 1 / 3) * Math.pow(z, 5 / 3) / Q, sJet) : sJet;
    var sLn = gp > 0 ? C_LINE * Math.pow(b, 1 / 3) * z / q : NaN;
    var S = reg === "point" ? sPt : (reg === "line" ? sLn : Math.min(sPt, sLn));
    S = Math.max(S, 1);
    return { g_prime: gp, regime: reg, s_over_H: r, dilution_point: sPt, dilution_line: sLn,
      dilution: S, delta_t_near_field_k: dt / S, jet_dominated: lM > depth, jet_velocity_ms: uj,
      total_flow_error_factor: Math.pow(n, 2 / 3) };
  }

  function requiredReporting(cool, marine, aqua) {
    var items = [];
    if (cool !== "closed_loop_air") items.push("impingement counts by taxon, life stage and tier",
      "entrainment estimates by taxon and life stage (eggs/larvae separate)",
      "fish aggregation and cold-shock events at the outfall");
    if (marine) items.push("marine mammal and sea turtle interaction log (MMPA/ESA/SARA)");
    if (aqua) items.push("named welfare standard for any farmed species using reused heat",
      "stocking density, water quality and mortality by species", "stunning and slaughter method");
    return items;
  }

  function screen(input) {
    var f = {}, k;
    for (k in DEFAULTS) f[k] = DEFAULTS[k];
    for (k in (input || {})) if (input[k] !== undefined) f[k] = input[k];
    if (f.it_load_mw < 0 || f.pue < 1) throw new Error("IT load must be >= 0 and PUE >= 1.0");
    if (!(f.delta_t_k > 0)) throw new Error("Temperature rise must be above 0 K");
    var frac = f.fraction_to_water === null ? COOLING[f.cooling_type] : f.fraction_to_water;
    var s = f.water_type !== "fresh" ? f.s_psu : 0;
    var qRej = f.it_load_mw * f.pue, qReuse = qRej * frac * f.reuse_fraction;
    var qW = qRej * frac * (1 - f.reuse_fraction);
    var flow = qW > 0 ? qW * 1e6 / (rhoCp(f.t_ambient_c, s) * f.delta_t_k) : 0;
    var o = { inputs: Object.assign({}, f, { fraction_to_water: frac, s_psu: s }),
      heat_rejected_mw: qRej, heat_reused_mw: qReuse, heat_to_water_mw: qW, flow_m3s: flow,
      flow_l_s_per_mw_it: f.it_load_mw ? flow * 1000 / f.it_load_mw : 0 };
    var juris = jurisdiction(f.jurisdiction), ruleId = f.temperature_rule || juris.temperature_rule;
    o.jurisdiction = Object.assign({}, juris, { resolved_temperature_rule: ruleId });
    var mgd = flow / MGD_TO_M3S;
    o.intake_316b = { design_intake_mgd: mgd, exceeds_2_mgd: mgd > 2, cooling_fraction: f.cooling_fraction,
      likely_applicable: mgd > 2 && f.cooling_fraction >= 0.25, min_screen_open_area_m2: flow / THROUGH_SCREEN };
    var exc = 2 * f.u_peak_ms / OMEGA;
    o.tidal_excursion_m = exc;
    var vol = Math.PI * Math.pow(exc / 2, 2) * f.depth_m, wd = flow * 12.4206 * 3600;
    var tf = vol > 0 ? wd / vol : Infinity;
    o.tidal_volume_check = { reference_volume_m3: vol, withdrawn_per_cycle_m3: wd, fraction: tf, within_1_percent: tf <= 0.01 };
    var rule = temperatureRule(ruleId, f.t_ambient_c, f.wa_category, f.custom_increment_k);
    o.temperature_rule = rule;
    if (flow > 0) {
      var nf = nearField(flow, Math.round(f.n_ports), f.port_diameter_m, f.port_spacing_m, f.depth_m,
        f.t_ambient_c, f.delta_t_k, s, f.u_peak_ms);
      nf.meets_rule = nf.delta_t_near_field_k <= rule.allowed_increment_k;
      o.near_field = nf;
    } else o.near_field = null;
    var tDis = f.t_ambient_c + f.delta_t_k, doA = doSat(f.t_ambient_c, s), doD = doSat(tDis, s);
    var fa = nh3Frac(f.t_ambient_c, f.ph, s), fd = nh3Frac(tDis, f.ph, s);
    o.water_quality = { do_sat_ambient_mg_l: doA, do_sat_discharge_mg_l: doD, do_sat_drop_frac: 1 - doD / doA,
      nh3_frac_ambient: fa, nh3_frac_discharge: fd, nh3_frac_ratio: fd / fa };
    var kn = kNum(f.u_peak_ms, f.grid_dx_m, f.grid_dt_s);
    o.numerics = { k_num_upwind_m2s: kn, k_okubo_at_dx_m2s: okubo(f.grid_dx_m), k_okubo_1km_m2s: okubo(1000),
      crossover_scale_m: kn > 0 ? okuboCross(kn) : 0 };
    o.reporting = requiredReporting(f.cooling_type, f.water_type !== "fresh", !!f.aquaculture_reuse);
    o.flags = flags(o, f);
    return o;
  }

  function flags(o, f) {
    var fl = [];
    function add(id, sev, text) { fl.push({ id: id, severity: sev, text: text }); }
    var intakeRule = o.jurisdiction.intake_rule;
    if (intakeRule === "us_cwa_316b") {
      if (o.intake_316b.likely_applicable) add("intake_316b", "high", "Design intake exceeds 2 MGD with >= 25% cooling use: CWA §316(b) intake rules likely apply (US).");
      if (f.water_type === "estuarine" && !o.tidal_volume_check.within_1_percent) add("tidal_volume", "high", "Intake exceeds 1% of the tidal-excursion volume (new-facility estuary test, 40 CFR 125.84).");
    } else if (intakeRule === "ca_fisheries_act" && o.flow_m3s > 0) {
      add("fisheries_act", "high", "Fisheries Act (Canada): water changed by heat can be a deleterious substance under s.34(1), s.36(3) prohibits depositing one, and intake works may need a s.35 authorisation for harmful alteration of fish habitat.");
    } else if (intakeRule === "none" && o.flow_m3s > 0) {
      add("no_intake_rule", "caution", "No cooling-water intake rule is transcribed for this jurisdiction, so no intake requirement is screened. The US 2 MGD arithmetic is shown for comparison only.");
    }
    if (o.jurisdiction.temperature_status === "placeholder") add("jurisdiction_rule", "caution", "No numeric temperature standard is transcribed for this jurisdiction. The allowed increment is the value you entered, not a published limit, so this result cannot show that a design complies.");
    var nf = o.near_field;
    if (nf !== null) {
      if (!nf.meets_rule) add("temperature", "high", "Screening temperature rise at the surface exceeds the allowed increment under slack-water conditions.");
      if (nf.regime === "transitional") add("regime", "caution", "Port spacing is between line- and point-plume regimes; the lower dilution is used. Run UM3/NRFIELD or CORMIX.");
      if (nf.jet_dominated) add("jet", "caution", "Momentum length exceeds depth: the discharge is jet-dominated and plume asymptotes are outside their range.");
      if (o.inputs.n_ports > 1) add("per_port", "info", "Per-port fluxes used. Feeding total flow into a point-plume law would understate dilution " + nf.total_flow_error_factor.toFixed(1) + "x.");
    }
    var mx = o.temperature_rule.max_discharge_delta_k;
    if (mx !== undefined && mx !== null && f.delta_t_k > mx) add("max_delta", "high", "Discharge temperature rise exceeds the rule's maximum above natural (20 F under the CA Thermal Plan).");
    if (o.water_quality.do_sat_drop_frac > 0.1) add("do", "caution", "Oxygen saturation at discharge temperature is more than 10% below ambient, while fish oxygen demand rises.");
    if (o.numerics.k_num_upwind_m2s > o.numerics.k_okubo_1km_m2s) add("numerics", "caution", "At this grid spacing, first-order upwind diffusion exceeds physical mixing at 1 km: far-field plumes will be over-dispersed.");
    if (f.u_peak_ms >= 0.6) add("tidal_speed", "info", "Peak current is typical of straits and passes rather than open coast; confirm with station data.");
    if (f.reuse_fraction > 0 && f.aquaculture_reuse) add("welfare", "caution", "Heat reuse for aquaculture must name a welfare standard; more farmed animals is not automatically a benefit.");
    return fl;
  }

  var api = { version: "0.1.0", DEFAULTS: DEFAULTS, screen: screen, doSat: doSat, nh3Frac: nh3Frac,
    density: density, okubo: okubo, temperatureRule: temperatureRule,
    JURISDICTIONS: JURISDICTIONS, INTAKE_RULES: INTAKE_RULES, jurisdiction: jurisdiction };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.AquaticGuardian = api;
})(typeof window !== "undefined" ? window : this);
