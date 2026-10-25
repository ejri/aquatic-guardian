"""One call that runs the whole PLUMES2.0 chain plus extended metrics."""
from __future__ import annotations

import copy
import math
from typing import Dict, Optional

from . import __version__
from .brooks import run_farfield
from .inputs import Scenario
from .metrics import caveats, exposure, flow_class, heat_budget, oxygen, thermal
from .regulations import evaluate
from .um3 import run_nearfield


def wastefield_width(sc: Scenario, end_diameter: float) -> float:
    d = sc.diffuser
    n = max(1, int(d.n_ports))
    if n == 1:
        return end_diameter
    if sc.settings.wastefield_rule == "projected":
        cur = sc.ambient.far_at(0)["direction"]
        ang = math.radians(d.diffuser_axis_deg - cur)
        return (n - 1) * d.spacing * abs(math.sin(ang)) + end_diameter
    return (n - 1) * d.spacing + end_diameter


def run(sc: Scenario, *, rule: Optional[str] = None, wa_category: str = "excellent",
        custom_increment: Optional[float] = None, isolated_check: bool = True,
        convergence_check: bool = False) -> Dict:
    nf = run_nearfield(sc)
    st = sc.settings
    ff = None
    end = nf.end
    if st.farfield:
        far = sc.ambient.far_at(end.depth)
        amb_end = sc.ambient.at(end.depth)
        w0 = wastefield_width(sc, end.diameter)
        excess_end = thermal(sc, nf, None)["dt_end_nearfield_c"]
        ff = run_farfield(start_distance=end.distance, start_dilution=end.dilution, w0=w0,
                          speed=max(far["speed"], 1e-4), alpha=far["alpha"], case=st.farfield_case,
                          decay_per_day=far["decay"], start_conc=end.concentration,
                          background=amb_end["background"], start_delta_t=excess_end,
                          interval=st.farfield_output_interval,
                          stop_distance=st.farfield_stop_distance or sc.mixing_zone.chronic,
                          max_dilution=st.farfield_max_dilution,
                          acute=sc.mixing_zone.acute, chronic=sc.mixing_zone.chronic)
    th = thermal(sc, nf, ff)
    metrics = {
        "flow_class": flow_class(sc, nf),
        "thermal": th,
        "exposure": exposure(sc, nf, ff, th),
        "oxygen": oxygen(sc, th),
        "heat": heat_budget(sc),
        "nearfield": {
            "termination": nf.termination,
            "dilution": end.dilution,
            "centerline_dilution": end.centerline_dilution,
            "diameter_m": end.diameter,
            "x_m": end.x, "y_m": end.y, "depth_m": end.depth,
            "horizontal_distance_m": end.distance,
            "travel_time_s": end.time,
            "trap_depth_m": nf.trap_depth,
            "rise_height_m": nf.rise_height,
            "merged_at_step": nf.merged_at_step,
            "steps": nf.last_step.step if nf.last_step else end.step,
        },
    }
    if ff is not None:
        metrics["farfield"] = {
            "w0_m": ff.w0, "eps0_m2s": ff.eps0, "beta": ff.beta, "case": ff.case,
            "speed_ms": ff.speed, "start_distance_m": ff.start_distance,
            "dilution_acute": ff.at_acute.dilution if ff.at_acute else None,
            "dilution_chronic": ff.at_chronic.dilution if ff.at_chronic else None,
        }
    if isolated_check and sc.diffuser.n_ports > 1:
        iso = copy.deepcopy(sc)
        iso.diffuser.spacing = 1e6   # same per-port flow, neighbours far away
        nfi = run_nearfield(iso)
        metrics["merging"] = {
            "isolated_port_dilution": nfi.end.dilution,
            "merged_dilution": end.dilution,
            "penalty_pct": 100 * (1 - end.dilution / nfi.end.dilution) if nfi.end.dilution else None,
            "invariant_ok": end.dilution <= nfi.end.dilution * 1.02,
            "note": "Merged plumes cannot out-dilute isolated ones (Aquatic Guardian correction 7).",
        }
    if convergence_check:
        half = copy.deepcopy(sc)
        half.settings.step_mass_fraction = sc.settings.step_mass_fraction / 2
        nfh = run_nearfield(half)
        metrics["convergence"] = {
            "dilution_full_step": end.dilution, "dilution_half_step": nfh.end.dilution,
            "relative_change_pct": 100 * (nfh.end.dilution / end.dilution - 1),
        }
    out = {
        "engine": f"plumes2py {__version__}",
        "scenario": sc.to_dict(),
        "nearfield": {
            "steps": [s.as_row() for s in nf.steps],
            "events": nf.events,
            "termination": nf.termination,
            "end": end.as_row(),
            "initial": nf.initial,
        },
        "farfield": None if ff is None else {
            "rows": [r.__dict__ for r in ff.rows], "w0": ff.w0, "eps0": ff.eps0, "beta": ff.beta,
            "case": ff.case, "speed": ff.speed, "alpha": ff.alpha, "stop_reason": ff.stop_reason,
        },
        "metrics": metrics,
        "caveats": caveats(sc, nf),
    }
    if rule:
        out["compliance"] = evaluate(rule, out, wa_category=wa_category, custom_increment=custom_increment)
    return out
