"""Brooks (1960) far-field dilution, as used by PLUMES2.0 (manual §3.3.2,
Tables 1-2, eqs. 9-17).

Width growth follows from d(L^2)/dt = 24 eps (top-hat width L = 2 sqrt(3) sigma),
with eps = eps0 (case 1), eps0 L/w0 (case 2) or eps0 (L/w0)^(4/3) (case 3), and
beta = 12 eps0 / (u w0). The centreline concentration is
C/C0 = exp(-k t) erf( sqrt( 1.5 / ((L/w0)^2 - 1) ) ) in all three cases.

Correction: manual eq. 11 gives case 2 as w/w0 = 1 + 2 beta x/w0, but
integrating L dL/dx = 12 eps0 L/(u w0) gives w/w0 = 1 + beta x/w0, which is also
what the manual's own eq. 15 implies ((1 + beta x/w0)^2 - 1). This module uses
the derivation-consistent form; see VALIDATION.md.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional

CASES = ("constant", "linear", "four_thirds")


def eps0(alpha: float, w0: float) -> float:
    """Initial eddy diffusivity, eq. 17: eps0 = alpha w0^(4/3)."""
    return alpha * w0 ** (4.0 / 3.0)


def beta(alpha: float, w0: float, u: float) -> float:
    return 12.0 * eps0(alpha, w0) / (u * w0)


def width_ratio(case: str, bx: float) -> float:
    """w/w0 as a function of bx = beta x / w0."""
    if case == "constant":
        return math.sqrt(1.0 + 2.0 * bx)
    if case == "linear":
        return 1.0 + bx
    if case == "four_thirds":
        return (1.0 + (2.0 / 3.0) * bx) ** 1.5
    raise ValueError(f"unknown far-field case {case!r}; use one of {CASES}")


def centerline_ratio(case: str, bx: float) -> float:
    """C/C0 at the wastefield centre (no decay)."""
    if bx <= 0:
        return 1.0
    r2 = width_ratio(case, bx) ** 2 - 1.0
    return math.erf(math.sqrt(1.5 / r2)) if r2 > 0 else 1.0


@dataclass
class FarfieldRow:
    distance: float      # m from the diffuser
    travel: float        # m from the start of the far field
    width: float         # m
    dilution: float      # total (near x far)
    farfield_factor: float
    time_h: float        # hours since start of far field
    concentration: float  # mg/L, with decay and background
    delta_t: float       # excess temperature at the wastefield centre, C
    note: str = ""


@dataclass
class FarfieldResult:
    rows: List[FarfieldRow]
    w0: float
    eps0: float
    beta: float
    case: str
    speed: float
    alpha: float
    start_distance: float
    start_dilution: float
    at_acute: Optional[FarfieldRow] = None
    at_chronic: Optional[FarfieldRow] = None
    stop_reason: str = ""


def run_farfield(start_distance: float, start_dilution: float, w0: float, speed: float,
                 alpha: float = 0.0003, case: str = "four_thirds", decay_per_day: float = 0.0,
                 start_conc: float = 0.0, background: float = 0.0, start_delta_t: float = 0.0,
                 interval: float = 10.0, stop_distance: Optional[float] = None,
                 max_dilution: float = 5000.0, acute: Optional[float] = None,
                 chronic: Optional[float] = None, n_after: int = 0) -> FarfieldResult:
    """Steady Brooks far field starting at ``start_distance`` (horizontal
    distance of the end of the near field from the diffuser).

    Output rows are at the start, then at multiples of ``interval``, plus exact
    rows at the acute and chronic mixing-zone boundaries (PLUMES2.0 requires a
    1 m output interval to land on the boundary; here it is computed directly).
    """
    if case not in CASES:
        raise ValueError(f"unknown far-field case {case!r}")
    if speed <= 0:
        raise ValueError("Far-field current must be positive; Brooks' method needs advection. "
                         "For slack water use a low but non-zero design current and say so.")
    if w0 <= 0:
        raise ValueError("Initial wastefield width must be positive.")
    e0 = eps0(alpha, w0)
    b = 12.0 * e0 / (speed * w0)
    k = decay_per_day / 86400.0

    def row(dist: float, note: str = "") -> FarfieldRow:
        x = max(dist - start_distance, 0.0)
        bx = b * x / w0
        ratio = centerline_ratio(case, bx)
        t = x / speed
        decay = math.exp(-k * t)
        ff = 1.0 / ratio
        conc = background + (start_conc - background) * ratio * decay
        return FarfieldRow(distance=dist, travel=x, width=w0 * width_ratio(case, bx),
                           dilution=start_dilution * ff, farfield_factor=ff, time_h=t / 3600.0,
                           concentration=conc, delta_t=start_delta_t * ratio, note=note)

    stop = stop_distance if stop_distance is not None else (chronic if chronic else start_distance + 1000.0)
    rows = [row(start_distance, "start")]
    reason = "stop distance"
    d = (math.floor(start_distance / interval) + 1) * interval
    marks = sorted({m for m in (acute, chronic) if m is not None and m > start_distance})
    extra = 0
    while True:
        # insert exact mixing-zone rows
        while marks and marks[0] <= d:
            m = marks.pop(0)
            tag = "acute mixing zone" if m == acute else "chronic mixing zone"
            if not (rows and abs(rows[-1].distance - m) < 1e-9):
                rows.append(row(m, tag))
            else:
                rows[-1].note = tag
        if d > stop + 1e-9:
            if extra >= n_after:
                break
            extra += 1
        if rows and abs(rows[-1].distance - d) < 1e-9:
            r = rows[-1]          # a mixing-zone row already sits on this distance
        else:
            r = row(d)
            rows.append(r)
        if r.dilution >= max_dilution:
            reason = "maximum dilution"
            break
        if len(rows) > 100000:
            reason = "row limit"
            break
        d += interval
    res = FarfieldResult(rows=rows, w0=w0, eps0=e0, beta=b, case=case, speed=speed, alpha=alpha,
                         start_distance=start_distance, start_dilution=start_dilution,
                         stop_reason=reason)
    for r in rows:
        if acute is not None and abs(r.distance - acute) < 1e-9:
            res.at_acute = r
        if chronic is not None and abs(r.distance - chronic) < 1e-9:
            res.at_chronic = r
    return res


def distance_to_dilution(target: float, start_distance: float, start_dilution: float, w0: float,
                         speed: float, alpha: float = 0.0003, case: str = "four_thirds",
                         max_distance: float = 1e6) -> Optional[float]:
    """Distance from the diffuser at which total dilution first reaches ``target``."""
    if target <= start_dilution:
        return start_distance
    b = beta(alpha, w0, speed)

    def f(dist):
        return start_dilution / centerline_ratio(case, b * (dist - start_distance) / w0) - target

    lo, hi = start_distance, start_distance + 1.0
    while f(hi) < 0:
        hi = start_distance + (hi - start_distance) * 2
        if hi > max_distance:
            return None
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        if f(mid) < 0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)
