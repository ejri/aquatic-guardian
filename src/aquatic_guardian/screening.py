"""End-to-end facility screening. Mirrored exactly by app/engine.js; the test
suite checks the two implementations agree on randomised scenarios.

A screening result says whether a design is likely to trigger regulatory
requirements or exceed criteria under conservative (slack-water, stagnant,
unstratified) near-field assumptions. It is not a permit-grade prediction.
"""
from __future__ import annotations
from . import cooling, intake, plume, tidal, numerics, water_quality, criteria, sentience

DEFAULTS = {
    "it_load_mw": 24.0, "pue": 1.15, "cooling_type": "once_through",
    "fraction_to_water": None, "reuse_fraction": 0.0, "delta_t_k": 8.0,
    "water_type": "marine", "t_ambient_c": 12.0, "s_psu": 30.0, "ph": 8.0,
    "u_peak_ms": 0.3, "depth_m": 20.0,
    "n_ports": 10, "port_diameter_m": 0.3, "port_spacing_m": 4.0,
    "cooling_fraction": 1.0, "jurisdiction": "us-wa", "temperature_rule": None,
    "wa_category": "excellent", "custom_increment_k": 1.0,
    "grid_dx_m": 25.0, "grid_dt_s": 10.0, "aquaculture_reuse": False,
}


def screen(facility: dict | None = None) -> dict:
    f = {**DEFAULTS, **(facility or {})}
    frac = cooling.COOLING_TYPES[f["cooling_type"]] if f["fraction_to_water"] is None else f["fraction_to_water"]
    s = f["s_psu"] if f["water_type"] != "fresh" else 0.0
    q_rej = cooling.heat_rejected_MW(f["it_load_mw"], f["pue"])
    q_reuse = q_rej * frac * f["reuse_fraction"]
    q_w = cooling.heat_to_water_MW(f["it_load_mw"], f["pue"], frac, f["reuse_fraction"])
    flow = cooling.cooling_flow_m3s(q_w, f["delta_t_k"], f["t_ambient_c"], s) if q_w > 0 else 0.0
    out = {"inputs": {**f, "fraction_to_water": frac, "s_psu": s},
           "heat_rejected_mw": q_rej, "heat_reused_mw": q_reuse, "heat_to_water_mw": q_w,
           "flow_m3s": flow, "flow_l_s_per_mw_it": flow * 1000 / f["it_load_mw"] if f["it_load_mw"] else 0.0}

    # The jurisdiction picks the temperature rule and the intake rule. An explicit
    # temperature_rule overrides the jurisdiction's default, for permit-specific work.
    juris = criteria.jurisdiction(f["jurisdiction"])
    rule_id = f["temperature_rule"] or juris["temperature_rule"]
    out["jurisdiction"] = {**juris, "resolved_temperature_rule": rule_id}

    out["intake_316b"] = intake.cwa316b_screen(flow, f["cooling_fraction"])
    exc = tidal.excursion_half_cycle(f["u_peak_ms"])
    out["tidal_excursion_m"] = exc
    out["tidal_volume_check"] = intake.tidal_volume_check(flow, exc, f["depth_m"])

    rule = criteria.temperature_rule(rule_id, f["t_ambient_c"], f["wa_category"],
                                     f["custom_increment_k"])
    out["temperature_rule"] = rule
    if flow > 0:
        d = plume.Diffuser(flow, int(f["n_ports"]), f["port_diameter_m"], f["port_spacing_m"])
        nf = plume.near_field(d, f["depth_m"], f["t_ambient_c"], f["delta_t_k"], s, f["u_peak_ms"])
        out["near_field"] = {k: nf[k] for k in ("g_prime", "regime", "s_over_H", "dilution_point",
                                                "dilution_line", "dilution", "delta_t_near_field_k",
                                                "jet_dominated")}
        out["near_field"]["jet_velocity_ms"] = d.jet_velocity_ms
        out["near_field"]["total_flow_error_factor"] = plume.total_flow_error_factor(d.n_ports)
        out["near_field"]["meets_rule"] = nf["delta_t_near_field_k"] <= rule["allowed_increment_k"]
    else:
        out["near_field"] = None

    t_dis = f["t_ambient_c"] + f["delta_t_k"]
    do_a = water_quality.do_saturation_mg_l(f["t_ambient_c"], s)
    do_d = water_quality.do_saturation_mg_l(t_dis, s)
    fa = water_quality.unionised_fraction(f["t_ambient_c"], f["ph"], s)
    fd = water_quality.unionised_fraction(t_dis, f["ph"], s)
    out["water_quality"] = {"do_sat_ambient_mg_l": do_a, "do_sat_discharge_mg_l": do_d,
                            "do_sat_drop_frac": 1 - do_d / do_a,
                            "nh3_frac_ambient": fa, "nh3_frac_discharge": fd, "nh3_frac_ratio": fd / fa}

    knum = numerics.k_num_upwind(f["u_peak_ms"], f["grid_dx_m"], f["grid_dt_s"])
    out["numerics"] = {"k_num_upwind_m2s": knum, "k_okubo_at_dx_m2s": numerics.okubo_kh(f["grid_dx_m"]),
                       "k_okubo_1km_m2s": numerics.okubo_kh(1000.0),
                       "crossover_scale_m": numerics.okubo_crossover_scale(knum) if knum > 0 else 0.0}

    out["reporting"] = sentience.required_reporting(f["cooling_type"], f["water_type"] != "fresh",
                                                    bool(f["aquaculture_reuse"]))
    out["flags"] = _flags(out, f)
    return out


def _flags(o: dict, f: dict) -> list[dict]:
    fl = []
    def add(i, sev, text):
        fl.append({"id": i, "severity": sev, "text": text})
    intake_rule = o["jurisdiction"]["intake_rule"]
    if intake_rule == "us_cwa_316b":
        if o["intake_316b"]["likely_applicable"]:
            add("intake_316b", "high", "Design intake exceeds 2 MGD with >= 25% cooling use: CWA §316(b) intake rules likely apply (US).")
        if f["water_type"] == "estuarine" and not o["tidal_volume_check"]["within_1_percent"]:
            add("tidal_volume", "high", "Intake exceeds 1% of the tidal-excursion volume (new-facility estuary test, 40 CFR 125.84).")
    elif intake_rule == "ca_fisheries_act" and o["flow_m3s"] > 0:
        add("fisheries_act", "high", "Fisheries Act (Canada): water changed by heat can be a deleterious substance under s.34(1), s.36(3) prohibits depositing one, and intake works may need a s.35 authorisation for harmful alteration of fish habitat.")
    elif intake_rule == "none" and o["flow_m3s"] > 0:
        add("no_intake_rule", "caution", "No cooling-water intake rule is transcribed for this jurisdiction, so no intake requirement is screened. The US 2 MGD arithmetic is shown for comparison only.")
    if o["jurisdiction"]["temperature_status"] == "placeholder":
        add("jurisdiction_rule", "caution", "No numeric temperature standard is transcribed for this jurisdiction. The allowed increment is the value you entered, not a published limit, so this result cannot show that a design complies.")
    nf = o["near_field"]
    if nf is not None:
        if not nf["meets_rule"]:
            add("temperature", "high", "Screening temperature rise at the surface exceeds the allowed increment under slack-water conditions.")
        if nf["regime"] == "transitional":
            add("regime", "caution", "Port spacing is between line- and point-plume regimes; the lower dilution is used. Run UM3/NRFIELD or CORMIX.")
        if nf["jet_dominated"]:
            add("jet", "caution", "Momentum length exceeds depth: the discharge is jet-dominated and plume asymptotes are outside their range.")
        if o["inputs"]["n_ports"] > 1:
            add("per_port", "info", f"Per-port fluxes used. Feeding total flow into a point-plume law would understate dilution {nf['total_flow_error_factor']:.1f}x.")
    mx = o["temperature_rule"].get("max_discharge_delta_k")
    if mx is not None and f["delta_t_k"] > mx:
        add("max_delta", "high", "Discharge temperature rise exceeds the rule's maximum above natural (20 F under the CA Thermal Plan).")
    if o["water_quality"]["do_sat_drop_frac"] > 0.1:
        add("do", "caution", "Oxygen saturation at discharge temperature is more than 10% below ambient, while fish oxygen demand rises.")
    if o["numerics"]["k_num_upwind_m2s"] > o["numerics"]["k_okubo_1km_m2s"]:
        add("numerics", "caution", "At this grid spacing, first-order upwind diffusion exceeds physical mixing at 1 km: far-field plumes will be over-dispersed.")
    if f["u_peak_ms"] >= 0.6:
        add("tidal_speed", "info", "Peak current is typical of straits and passes rather than open coast; confirm with station data.")
    if f["reuse_fraction"] > 0 and f["aquaculture_reuse"]:
        add("welfare", "caution", "Heat reuse for aquaculture must name a welfare standard; more farmed animals is not automatically a benefit.")
    return fl
