"""Multi-run analyses regulators ask for and PLUMES2.0 leaves to the user.

* ``critical_conditions``: sweep design currents and stratification and
  report the lowest dilution at the mixing-zone edge (manual §4.2.4: worst
  case can be at high or low current, strong or weak stratification).
* ``tidal_cycle``: quasi-steady runs through an M2 cycle; fraction of the
  cycle in which the screening limit is exceeded (the California rule is
  stated for "at least 50 % of any tidal cycle").
* ``monte_carlo``: parameter and model-form uncertainty (aspiration and
  forced-entrainment coefficients, Brooks alpha, current, ambient T).
* ``tornado``: one-at-a-time sensitivity ranking.
"""
from __future__ import annotations

import copy
import math
import random
from typing import Callable, Dict, List, Optional, Sequence

from .model import run
from .regulations import evaluate


def _scaled_currents(sc, factor: float, direction: Optional[float] = None):
    s = copy.deepcopy(sc)
    for r in s.ambient.rows:
        r.speed = max(r.speed * factor, 0.0)
        if r.far_speed is not None:
            r.far_speed = max(r.far_speed * factor, 1e-4)
        if direction is not None:
            r.direction = direction
            r.far_direction = direction
    if hasattr(s.ambient, "_uxy"):
        del s.ambient._uxy
    return s


def _key(res: Dict, what: str) -> Optional[float]:
    m = res["metrics"]
    if what == "dilution_chronic":
        return (m.get("farfield") or {}).get("dilution_chronic") or m["nearfield"]["dilution"]
    if what == "dt_chronic":
        return m["thermal"]["dt_chronic_c"]
    if what == "dilution_nearfield":
        return m["nearfield"]["dilution"]
    raise KeyError(what)


def critical_conditions(sc, current_factors: Sequence[float] = (0.1, 0.25, 0.5, 1.0, 1.5, 2.0),
                        stratifications: Sequence[str] = ("as given", "mixed"),
                        rule: Optional[str] = None) -> Dict:
    rows = []
    for strat in stratifications:
        base = copy.deepcopy(sc)
        if strat == "mixed":
            # vertically mixed: depth-averaged T and S at every level
            n = len(base.ambient.rows)
            tm = sum(r.temperature for r in base.ambient.rows) / n
            sm = sum(r.salinity for r in base.ambient.rows) / n
            for r in base.ambient.rows:
                r.temperature, r.salinity = tm, sm
        for f in current_factors:
            s = _scaled_currents(base, f)
            try:
                res = run(s, rule=rule, isolated_check=False)
            except ValueError as exc:
                rows.append({"stratification": strat, "current_factor": f, "error": str(exc)})
                continue
            rows.append({
                "stratification": strat, "current_factor": f,
                "current_ms": s.ambient.at(s.diffuser.port_depth)["speed"],
                "dilution_nearfield": _key(res, "dilution_nearfield"),
                "dilution_chronic": _key(res, "dilution_chronic"),
                "dt_chronic_c": _key(res, "dt_chronic"),
                "termination": res["nearfield"]["termination"],
                "verdict": res.get("compliance", {}).get("verdict"),
            })
    ok = [r for r in rows if "error" not in r]
    worst = min(ok, key=lambda r: r["dilution_chronic"]) if ok else None
    return {"rows": rows, "worst": worst}


def tidal_cycle(sc, u_peak: float, *, residual: float = 0.0, direction: float = 0.0,
                n: int = 24, period_h: float = 12.42, rule: Optional[str] = None,
                min_speed: float = 0.005) -> Dict:
    """Quasi-steady runs at n phases of an M2 tide u(t) = residual + u_peak cos(wt).
    Each phase is a steady PLUMES run, so re-entrainment of earlier effluent at
    slack water is not represented (flagged in the output)."""
    rows = []
    for i in range(n):
        ph = 2 * math.pi * i / n
        u = residual + u_peak * math.cos(ph)
        dirn = direction if u >= 0 else (direction + 180.0) % 360.0
        s = copy.deepcopy(sc)
        for r in s.ambient.rows:
            r.speed = max(abs(u), min_speed)
            r.far_speed = max(abs(u), min_speed)
            r.direction = dirn
            r.far_direction = dirn
        if hasattr(s.ambient, "_uxy"):
            del s.ambient._uxy
        res = run(s, rule=rule, isolated_check=False)
        comp = res.get("compliance")
        rows.append({"hour": period_h * i / n, "u_ms": u,
                     "dilution_chronic": _key(res, "dilution_chronic"),
                     "dt_chronic_c": _key(res, "dt_chronic"),
                     "slack": abs(u) < 0.05,
                     "pass": None if not comp else all(c["pass"] is not False for c in comp["checks"])})
    graded = [r for r in rows if r["pass"] is not None]
    frac_fail = (sum(1 for r in graded if not r["pass"]) / len(graded)) if graded else None
    return {"rows": rows, "fraction_of_cycle_exceeding": frac_fail,
            "excursion_km": 2 * u_peak / (2 * math.pi / (period_h * 3600)) / 1000,
            "note": "Quasi-steady: each phase is a steady run. Slack-water phases understate concentrations "
                    "because effluent from earlier phases is re-entrained in reality."}


DEFAULT_RANGES = {
    "aspiration": (0.08, 0.12),          # UM3 aspiration coefficient
    "forced_scale": (0.65, 1.0),         # model-form: calibrated 0.81, uncalibrated 1.0
    "alpha": (0.0001, 0.0005),           # Brooks, manual eq. 17 range
    "current_factor": (0.5, 1.5),
    "ambient_dt": (-1.0, 1.0),           # C shift of the whole profile
}


def _apply(sc, name: str, v: float):
    s = copy.deepcopy(sc)
    if name == "aspiration":
        s.settings.aspiration = v
    elif name == "forced_scale":
        s.settings.forced_scale = v
    elif name == "alpha":
        for r in s.ambient.rows:
            r.alpha = v
    elif name == "current_factor":
        s = _scaled_currents(s, v)
    elif name == "ambient_dt":
        for r in s.ambient.rows:
            r.temperature += v
    return s


def monte_carlo(sc, n: int = 200, ranges: Optional[Dict] = None, seed: int = 7,
                what: str = "dilution_chronic") -> Dict:
    rng = random.Random(seed)
    ranges = ranges or DEFAULT_RANGES
    vals = []
    for _ in range(n):
        s = sc
        draw = {}
        for k, (lo, hi) in ranges.items():
            v = rng.uniform(lo, hi)
            draw[k] = v
            s = _apply(s, k, v)
        try:
            vals.append((_key(run(s, isolated_check=False), what), draw))
        except ValueError:
            continue
    xs = sorted(v for v, _ in vals if v is not None)

    def pct(p):
        if not xs:
            return None
        i = min(len(xs) - 1, max(0, int(round(p / 100 * (len(xs) - 1)))))
        return xs[i]
    return {"what": what, "n": len(xs), "p5": pct(5), "p50": pct(50), "p95": pct(95),
            "min": xs[0] if xs else None, "max": xs[-1] if xs else None, "ranges": ranges, "seed": seed}


def tornado(sc, ranges: Optional[Dict] = None, what: str = "dilution_chronic") -> List[Dict]:
    ranges = ranges or DEFAULT_RANGES
    base = _key(run(sc, isolated_check=False), what)
    out = []
    for k, (lo, hi) in ranges.items():
        a = _key(run(_apply(sc, k, lo), isolated_check=False), what)
        b = _key(run(_apply(sc, k, hi), isolated_check=False), what)
        out.append({"parameter": k, "low": lo, "high": hi, "at_low": a, "at_high": b,
                    "swing_pct": 100 * abs(b - a) / base if base else None})
    return sorted(out, key=lambda r: -(r["swing_pct"] or 0))
