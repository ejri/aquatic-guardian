"""Text output laid out like the PLUMES2.0 / Visual Plumes ASCII file
(manual Fig. 12), followed by the extended metrics."""
from __future__ import annotations

from typing import Dict

from .seawater import MGD_TO_M3S

LINE = "-" * 100


def text_report(res: Dict, interval: int = 5) -> str:
    sc = res["scenario"]
    d, e, mz = sc["diffuser"], sc["effluent"], sc["mixing_zone"]
    rows = sc["ambient"]["rows"]
    out = ["*" * 100, LINE, "Ambient Table:",
           "     Depth   Amb-cur   Amb-dir   Amb-sal   Amb-tem   Amb-pol     Decay   Far-spd   Far-dir   Disprsn",
           "       (m)     (m/s)     (deg)     (psu)       (C)    (mg/L)   (1/day)     (m/s)     (deg)(m0.67/s2)"]
    for r in rows:
        out.append(f"{r['depth']:10.3f}{r['speed']:10.3f}{r['direction']:10.3f}{r['salinity']:10.3f}"
                   f"{r['temperature']:10.3f}{r['background']:10.3f}{r['decay']:10.3f}"
                   f"{(r['far_speed'] if r['far_speed'] is not None else r['speed']):10.3f}"
                   f"{(r['far_direction'] if r['far_direction'] is not None else r['direction']):10.3f}"
                   f"{r['alpha']:10.5f}")
    out += [LINE, "Diffuser Table:",
            "     P-dia    P-elev   V-angle   H-angle     Ports   Spacing   AcuteMZ   ChrncMZ   P-depth   Ttl-flo   Eff-sal      Temp   Polutnt",
            "       (m)       (m)     (deg)     (deg)       ( )       (m)       (m)       (m)       (m)     (MGD)     (psu)       (C)    (mg/L)",
            f"{d['port_diameter']:10.3f}{d['port_elevation']:10.2f}{d['vertical_angle']:10.2f}{d['horizontal_angle']:10.2f}"
            f"{d['n_ports']:10.2f}{d['spacing']:10.2f}{(mz['acute'] or 0):10.2f}{(mz['chronic'] or 0):10.2f}"
            f"{d['port_depth']:10.2f}{e['flow'] / MGD_TO_M3S:10.2f}{e['salinity']:10.2f}{e['temperature']:10.2f}"
            f"{e['concentration']:10.2f}", LINE, "Simulation Results:",
            "              Dilutn    CL-Dil     P-dia    x-posn    y-posn     Depth     dT(C)",
            "      Step (FluxAvg)        ()       (m)       (m)       (m)       (m)   (local)"]
    ev_by_step = {}
    for ev in res["nearfield"]["events"]:
        ev_by_step.setdefault(ev["step"], []).append(ev["text"])
    steps = res["nearfield"]["steps"]
    last = steps[-1]["step"]
    for s in steps[1:]:
        for txt in ev_by_step.get(s["step"], []):
            out.append(f"{(' ' + txt + ' '):-^70}")
        if s["step"] % interval == 0 or s["step"] == last:
            out.append(f"{s['step']:10d}{s['dilution']:10.3f}{s['centerline_dilution']:10.3f}{s['diameter']:10.3f}"
                       f"{s['x']:10.3f}{s['y']:10.3f}{-s['depth']:10.3f}{s['delta_t']:10.3f}")
    end = res["nearfield"]["end"]
    out.append(f"{'  exact':>10}{end['dilution']:10.3f}{end['centerline_dilution']:10.3f}{end['diameter']:10.3f}"
               f"{end['x']:10.3f}{end['y']:10.3f}{-end['depth']:10.3f}{end['delta_t']:10.3f}"
               "   <- boundary contact, interpolated")
    ff = res.get("farfield")
    if ff:
        out += [f"{' Starting Farfield Calculations ':-^72}",
                f"Farfield dispersion based on wastefield width of : {ff['w0']:10.2f} (m)",
                {"four_thirds": "4/3 Power Law based Eddy Diffusivity is used:",
                 "linear": "Linearly varying Eddy Diffusivity is used:",
                 "constant": "Constant Eddy Diffusivity is used:"}[ff["case"]],
                "  Dilution     Width  Distance      Time     dT(C)",
                "        ()       (m)       (m)    (hrs.)  (centre)"]
        for r in ff["rows"]:
            if r["note"] == "chronic mixing zone":
                out.append(f"{' Reached Chronic Mixing Zone ':.^84}")
            out.append(f"{r['dilution']:10.3f}{r['width']:10.3f}{r['distance']:10.3f}{r['time_h']:10.3f}{r['delta_t']:10.3f}"
                       + (f"   {r['note']}" if r["note"] and r["note"] != "chronic mixing zone" else ""))
    m = res["metrics"]
    th = m["thermal"]
    out += ["", "=" * 100, "Extended metrics (plumes2py; not in PLUMES2.0)", "=" * 100,
            f"Flow regime: {m['flow_class']['regime']} (port Froude {m['flow_class']['port_froude']:.1f}; "
            f"L_M {m['flow_class']['L_M_m']:.2f} m, l_m {m['flow_class']['l_m_m']:.2f} m, l_b {m['flow_class']['l_b_m']:.2f} m)",
            f"Heat to water: {m['heat']['heat_to_water_mw']:.2f} MW; flow {m['heat']['flow_m3s']:.3f} m3/s "
            f"({m['heat']['flow_mgd']:.2f} MGD)",
            f"Excess temperature: discharge {th['dt_discharge_c']:+.2f} C; end of near field {th['dt_end_nearfield_c']:+.3f} C "
            f"(governed by {th['governing_reference']}); acute edge "
            + (f"{th['dt_acute_c']:+.3f} C" if th['dt_acute_c'] is not None else "n/a")
            + "; chronic edge " + (f"{th['dt_chronic_c']:+.3f} C" if th['dt_chronic_c'] is not None else "n/a")]
    for rr in th["threshold_reach"]:
        dist = "n/a" if rr["distance_m"] is None else f"{rr['distance_m']:.1f} m"
        area = "n/a" if rr["area_m2"] is None else f"{rr['area_m2']:.0f} m2"
        out.append(f"  |dT| > {rr['threshold_c']:.2f} C until {dist} ({rr['within']}); footprint <= {area}")
    ex = m["exposure"]
    out.append(f"Drifting-organism dose (centreline): {ex['degree_minutes']:.1f} C-min; minutes above "
               + ", ".join(f"{k}: {v:.1f}" for k, v in ex["minutes_above"].items()))
    ox = m["oxygen"]
    out.append(f"Oxygen saturation: ambient {ox['saturation_ambient_mg_l']:.2f} mg/L; lost at end of pipe "
               f"{ox.get('loss_end_of_pipe_mg_l', 0):.2f} mg/L")
    if "merging" in m:
        out.append(f"Merging penalty vs isolated port: {m['merging']['penalty_pct']:.1f} % "
                   f"(invariant {'holds' if m['merging']['invariant_ok'] else 'VIOLATED'})")
    if "compliance" in res:
        c = res["compliance"]
        out.append(f"Screening against {c['rule']['label']} ({c['rule']['source']}): {c['verdict']}")
        for ch in c["checks"]:
            v = "n/a" if ch["value_c"] is None else f"{ch['value_c']:.3f}"
            lim = "n/a" if ch["limit_c"] is None else f"{ch['limit_c']:.3f}"
            out.append(f"  {ch['check']}: {v} C vs {lim} C -> "
                       + {True: "pass", False: "EXCEEDS", None: "not assessed"}[ch["pass"]])
    for c in res["caveats"]:
        out.append(f"Caveat: {c}")
    return "\n".join(out)
