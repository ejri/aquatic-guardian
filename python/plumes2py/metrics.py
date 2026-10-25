"""Metrics PLUMES2.0 does not report.

* Flow classification from CORMIX length scales (Jirka & Doneker), which the
  DOS PLUMES lineage also used for model selection.
* Thermal excess two ways: against local ambient (what a thermometer at that
  depth reads) and attributable to effluent heat ((T0 - Ta,port)/S). In
  stratified water a rising plume carries cooler deep water upward, so the
  two differ; screening uses the larger.
* Distances and footprint areas to excess-temperature thresholds, joining the
  near and far fields.
* Exposure for an organism drifting with the plume centre: degree-minutes and
  time above thresholds.
* Dissolved-oxygen saturation lost to warming (Garcia & Gordon 1992).
* Heat budget check: rho cp Q dT0.
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional

from .brooks import FarfieldResult, centerline_ratio, distance_to_dilution
from .inputs import Scenario
from .seawater import density, heat_capacity, oxygen_saturation_mg_l
from .um3 import NearfieldResult

THRESHOLDS_C = (2.22, 1.0, 0.83, 0.5, 0.3, 0.1)   # 0.83 C = 1.5 F (CA dispersion isotherm)


def flow_class(sc: Scenario, nf: NearfieldResult) -> Dict:
    ini = nf.initial
    Q, M, B = ini["port_flow"], ini["momentum_flux"], ini["buoyancy_flux"]
    H = sc.diffuser.water_depth
    ua = max(sc.ambient.at(sc.diffuser.port_depth)["speed"], 1e-6)
    LQ = Q / math.sqrt(M) if M > 0 else 0.0
    LM = M ** 0.75 / math.sqrt(abs(B)) if B != 0 else float("inf")
    lm = math.sqrt(M) / ua
    lb = abs(B) / ua ** 3
    if LM > H:
        regime = "momentum-dominated jet over the full depth"
    elif lm < LM and lm < H:
        regime = "jet bent over by the current" if lb < lm else "buoyant plume bent over by the current"
    else:
        regime = "buoyancy-dominated plume"
    if B < 0:
        regime = "negatively buoyant (sinking) " + regime
    return {"L_Q_m": LQ, "L_M_m": LM, "l_m_m": lm, "l_b_m": lb, "water_depth_m": H,
            "regime": regime, "port_froude": ini["port_froude"],
            "note": "CORMIX length scales: L_M jet-to-plume, l_m jet-to-crossflow, l_b plume-to-crossflow."}


def _excess(sc: Scenario, nf: NearfieldResult) -> Dict:
    t0 = sc.effluent.temperature
    ta_port = sc.ambient.at(sc.diffuser.port_depth)["temperature"]
    end = nf.end
    local = end.delta_t
    attributable = (t0 - ta_port) / end.dilution
    attributable_cl = (t0 - ta_port) / end.centerline_dilution
    return {"t0": t0, "ta_port": ta_port, "local": local, "attributable": attributable,
            "attributable_cl": attributable_cl}


def thermal(sc: Scenario, nf: NearfieldResult, ff: Optional[FarfieldResult]) -> Dict:
    e = _excess(sc, nf)
    sign = 1.0 if e["t0"] >= e["ta_port"] else -1.0
    # conservative: larger magnitude in the direction of the discharge
    dt_end = sign * max(sign * e["local"], sign * e["attributable"])
    governs = "local ambient" if sign * e["local"] >= sign * e["attributable"] else "effluent heat"
    mz = sc.mixing_zone
    out: Dict = {
        "ambient_at_port_c": e["ta_port"], "dt_discharge_c": e["t0"] - e["ta_port"],
        "dt_end_nearfield_c": dt_end, "dt_end_local_c": e["local"],
        "dt_end_attributable_c": e["attributable"],
        "dt_end_centerline_attributable_c": e["attributable_cl"],
        "governing_reference": governs,
        "surfaced": nf.termination == "surface",
        "bottom_contact": nf.termination == "bottom",
    }

    def dt_at(dist: Optional[float]) -> Optional[float]:
        if dist is None:
            return None
        if ff is None or dist <= ff.start_distance:
            # inside the near field: interpolate along the horizontal distance
            best = None
            for s in nf.steps:
                if s.distance <= dist:
                    best = s
            s = best or nf.steps[0]
            return sign * max(sign * s.delta_t, sign * (e["t0"] - e["ta_port"]) / s.dilution)
        r = centerline_ratio(ff.case, ff.beta * (dist - ff.start_distance) / ff.w0)
        return dt_end * r

    out["dt_acute_c"] = dt_at(mz.acute)
    out["dt_chronic_c"] = dt_at(mz.chronic)
    out["dt_surface_1000ft_c"] = dt_at(304.8) if nf.termination == "surface" else 0.0

    # distances to thresholds and footprint areas (upper bound: full wastefield width)
    reach = []
    mag0 = abs(dt_end)
    for thr in THRESHOLDS_C:
        if abs(out["dt_discharge_c"]) <= thr:
            reach.append({"threshold_c": thr, "distance_m": 0.0, "area_m2": 0.0, "within": "never exceeded"})
            continue
        if mag0 <= thr:
            # crossed inside the near field
            d_cross, area = None, 0.0
            prev = nf.steps[0]
            for s in nf.steps[1:]:
                area += s.diameter * max(s.distance - prev.distance, 0.0)
                if abs(e["t0"] - e["ta_port"]) / s.dilution <= thr:
                    d_cross = s.distance
                    break
                prev = s
            reach.append({"threshold_c": thr, "distance_m": d_cross, "area_m2": area, "within": "near field"})
            continue
        if ff is None:
            reach.append({"threshold_c": thr, "distance_m": None, "area_m2": None, "within": "beyond near field"})
            continue
        target_dil = ff.start_dilution * mag0 / thr
        d = distance_to_dilution(target_dil, ff.start_distance, ff.start_dilution, ff.w0, ff.speed,
                                 ff.alpha, ff.case)
        area = None
        if d is not None:
            # integrate width over the far field (trapezoid, 200 panels) + near-field strip
            n = 200
            area = 0.0
            for i in range(n):
                x0 = ff.start_distance + (d - ff.start_distance) * i / n
                x1 = ff.start_distance + (d - ff.start_distance) * (i + 1) / n
                from .brooks import width_ratio
                w0r = width_ratio(ff.case, ff.beta * (x0 - ff.start_distance) / ff.w0)
                w1r = width_ratio(ff.case, ff.beta * (x1 - ff.start_distance) / ff.w0)
                area += 0.5 * (w0r + w1r) * ff.w0 * (x1 - x0)
            area += ff.w0 * ff.start_distance
        reach.append({"threshold_c": thr, "distance_m": d, "area_m2": area, "within": "far field"})
    out["threshold_reach"] = reach
    return out


def exposure(sc: Scenario, nf: NearfieldResult, ff: Optional[FarfieldResult], th: Dict) -> Dict:
    """Thermal dose for an organism carried at the plume centre (centreline
    excess, conservative), integrated until the excess falls below 0.1 C or
    the far-field output ends."""
    dT0 = th["dt_discharge_c"]
    dose = 0.0
    t_above = {thr: 0.0 for thr in (2.0, 1.0, 0.5)}
    prev = nf.steps[0]
    peak = abs(dT0)
    for s in nf.steps[1:]:
        dt = s.time - prev.time
        a = abs(dT0) / max(prev.centerline_dilution, 1.0)
        b = abs(dT0) / max(s.centerline_dilution, 1.0)
        dose += 0.5 * (a + b) * dt
        for thr in t_above:
            if 0.5 * (a + b) > thr:
                t_above[thr] += dt
        prev = s
    t_nf = nf.end.time
    if ff is not None and ff.rows:
        cl0 = abs(th["dt_end_centerline_attributable_c"])
        rows = ff.rows
        for r0, r1 in zip(rows, rows[1:]):
            dt = (r1.time_h - r0.time_h) * 3600
            a, b = cl0 / r0.farfield_factor, cl0 / r1.farfield_factor
            dose += 0.5 * (a + b) * dt
            for thr in t_above:
                if 0.5 * (a + b) > thr:
                    t_above[thr] += dt
            if b < 0.1:
                break
    return {"peak_excess_c": peak, "degree_minutes": dose / 60.0,
            "nearfield_transit_s": t_nf,
            "minutes_above": {f"{k:g}C": v / 60.0 for k, v in t_above.items()},
            "note": "Centreline (worst-case) path; a drifting organism's actual path samples lower excess."}


def oxygen(sc: Scenario, th: Dict) -> Dict:
    s = sc.ambient.at(sc.diffuser.port_depth)["salinity"]
    t = th["ambient_at_port_c"]
    base = oxygen_saturation_mg_l(s, t)
    out = {"saturation_ambient_mg_l": base}
    for key, dt in (("end_of_pipe", th["dt_discharge_c"]), ("chronic_edge", th.get("dt_chronic_c"))):
        if dt is None:
            continue
        sat = oxygen_saturation_mg_l(s, t + dt)
        out[f"saturation_{key}_mg_l"] = sat
        out[f"loss_{key}_mg_l"] = base - sat
        out[f"loss_{key}_pct"] = 100 * (base - sat) / base
    return out


def heat_budget(sc: Scenario) -> Dict:
    e = sc.effluent
    ta = sc.ambient.at(sc.diffuser.port_depth)["temperature"]
    rho = density(e.salinity, e.temperature)
    cp = heat_capacity(e.salinity, 0.5 * (e.temperature + ta))
    mw = rho * cp * e.flow * (e.temperature - ta) / 1e6
    mgd = e.flow / 0.0438126364
    return {"heat_to_water_mw": mw, "flow_m3s": e.flow, "flow_mgd": mgd,
            "us_316b_2mgd_trigger": mgd >= 2.0,
            "note": "Heat relative to ambient at port depth. The 316(b) flag is the 2 MGD design-intake "
                    "threshold only; the 25 % cooling-use test and applicability to data centres need "
                    "legal confirmation."}


def caveats(sc: Scenario, nf: NearfieldResult) -> List[str]:
    out = list(nf.warnings)
    ua = sc.ambient.at(sc.diffuser.port_depth)["speed"]
    if ua < 0.03:
        out.append("Current below 0.03 m/s: near slack water, re-entrainment of earlier effluent is likely and "
                   "the steady-state assumption is weak (PLUMES2.0 manual §5). Treat dilution as an upper bound.")
    if nf.termination == "bottom":
        out.append("Plume contacted the seabed: boundary interaction is outside UM3's assumptions; "
                   "use CORMIX or a field dye study.")
    if nf.termination == "surface" and nf.end.dilution < 20:
        out.append("Plume surfaced at low dilution: surface boil mixing is oversimplified by the model.")
    if sc.effluent.salinity < 1 and sc.ambient.at(sc.diffuser.port_depth)["salinity"] > 20:
        out.append("Effluent salinity is near zero in seawater. That is right for wastewater but wrong for "
                   "seawater-cooled data centres, whose discharge salinity equals intake salinity.")
    return out
