"""UM3 near-field dilution, rebuilt in Python from PLUMES2.0 theory.

PLUMES2.0 (EPA/600/B-24/339) is distributed only as a Windows executable; its
Fortran 90 source is not public. This module re-derives the model from the
equations in the manual (§3.3.1, eqs. 2-7) and the papers it cites:

* Lagrangian control volume (LCV) with top-hat properties (Baumgartner, Frick
  & Roberts 1994; Lee & Cheung 1990).
* Continuity (eq. 2): dm/dt = forced entrainment + Taylor (aspiration)
  entrainment.
* Forced entrainment by the projected-area entrainment hypothesis (Frick
  1984): rho_a |U_a| [W h |sin t| + pi b (db/ds) h cos t + (pi b^2 / 2)
  d(cos t)/ds h], where t is the angle between the element axis and the
  current and W the projected width (reduced where neighbouring plumes from a
  multiport diffuser shield each other).
* Aspiration entrainment: rho_a A_T alpha |dV|, with A_T the element's exposed
  lateral area and dV the along-axis velocity difference between plume and
  ambient (alpha = 0.1 by default, as in UM3).
* Momentum (eq. 3), heat (eq. 4), salt (eq. 5) with EOS-80 sigma-t density.
* Merging (manual Fig. 4): each port's cross-section is a circle clipped by its
  neighbours at the projected port spacing; exposed perimeter and area follow
  from circle-segment geometry.
* Termination (manual §3.3.1): trapping, maximum rise or fall, and surface,
  bottom or shoreline contact. The surface test uses the vertical half-extent
  of an inclined cross-section, b cos(phi).
* Time step: chosen so that the reference aspiration entrainment of an
  unmerged element moving at its own speed equals ``step_mass_fraction``
  (default 2 %) of its mass. This reproduces the per-step dilution growth in
  the PLUMES2.0 reference output (1.101 at step 5, 1.213 at step 10).

Reported dilution is the flux-averaged volumetric dilution
D = (C_e - C_a)/(C_ave - C_a) (manual eq. 7 and §3.3.1), computed from a
conservative effluent tracer; centreline dilution uses the 3/2-power profile
peak-to-mean ratio (3.89 round, 2.22 merged line) blended from 1 at the source.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .inputs import Scenario
from .seawater import G, density

ROUND_PEAK_TO_MEAN = 3.89   # manual §3.3.1, 3/2-power profile, round plume
LINE_PEAK_TO_MEAN = 2.22    # fully merged line plume


# ---------------------------------------------------------------- geometry --

def merged_area(b: float, d: float) -> float:
    """Cross-section area of a circle of radius b clipped to a strip of width d
    (neighbours at +-d). Equals pi b^2 when 2b <= d."""
    if d >= 2 * b or d <= 0:
        return math.pi * b * b
    c = d / (2 * b)
    seg = b * b * math.acos(c) - (d / 2) * math.sqrt(max(b * b - d * d / 4, 0.0))
    return math.pi * b * b - 2 * seg


def exposed_perimeter(b: float, d: float) -> float:
    """Perimeter of the clipped cross-section that is still in contact with
    ambient water (the arcs inside the strip)."""
    if d >= 2 * b or d <= 0:
        return 2 * math.pi * b
    return 4 * b * math.asin(d / (2 * b))


def radius_from_area(area: float, d: float) -> float:
    """Invert merged_area for b (monotonic in b)."""
    b = math.sqrt(area / math.pi)
    if d <= 0 or 2 * b <= d:
        return b
    # area grows ~ 2 b d once fully merged; Newton on f(b) = A(b) - area
    lo, hi = b, max(b, area / d)  # A(area/d) >= area since A >= strip-limited
    hi = max(hi, d)
    while merged_area(hi, d) < area:
        hi *= 1.5
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if merged_area(mid, d) < area:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-12 * max(1.0, hi):
            break
    return 0.5 * (lo + hi)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _norm(a):
    return math.sqrt(_dot(a, a))


# ----------------------------------------------------------------- results --

@dataclass
class Step:
    step: int
    time: float            # s since release
    x: float
    y: float
    depth: float           # m below surface (positive)
    diameter: float        # m (2b)
    dilution: float        # flux-averaged, volumetric
    centerline_dilution: float
    temperature: float     # plume, C
    salinity: float
    density: float
    amb_temperature: float
    amb_density: float
    delta_t: float         # plume - ambient at same depth, C (flux-averaged)
    delta_t_centerline: float
    speed: float           # |V|
    w: float               # vertical velocity, + up
    concentration: float   # pollutant, mg/L
    merged: bool
    distance: float        # horizontal distance from the diffuser
    path_length: float     # along trajectory

    def as_row(self) -> dict:
        return self.__dict__.copy()


@dataclass
class NearfieldResult:
    steps: List[Step]
    events: List[Dict]
    termination: str
    end: Step
    trap_depth: Optional[float]
    rise_height: float
    merged_at_step: Optional[int]
    initial: Dict
    last_step: Optional[Step] = None
    warnings: List[str] = field(default_factory=list)

    def event_steps(self) -> Dict[str, int]:
        return {e["event"]: e["step"] for e in self.events}


# -------------------------------------------------------------------- model --

def run_nearfield(sc: Scenario) -> NearfieldResult:
    d, e, amb, st = sc.diffuser, sc.effluent, sc.ambient, sc.settings
    errs = d.validate()
    if errs:
        raise ValueError("; ".join(errs))
    warnings: List[str] = []

    n = max(1, int(d.n_ports))
    q_port = e.flow / n                                   # per-port flow (not total)
    a0 = d.contraction * math.pi * d.port_diameter ** 2 / 4
    b0 = math.sqrt(a0 / math.pi)
    u0 = q_port / a0
    th_v, th_h = math.radians(d.vertical_angle), math.radians(d.horizontal_angle)
    ehat = (math.cos(th_v) * math.cos(th_h), math.cos(th_v) * math.sin(th_h), math.sin(th_v))
    V = [u0 * ehat[0], u0 * ehat[1], u0 * ehat[2]]
    ax = math.radians(d.diffuser_axis_deg)
    dhat = (math.cos(ax), math.sin(ax), 0.0)

    rho0 = density(e.salinity, e.temperature)
    a_port = amb.at(d.port_depth)
    rho_a0 = density(a_port["salinity"], a_port["temperature"])
    gp0 = G * (rho_a0 - rho0) / rho0
    # densimetric Froude number at the port (manual §4.2.2 note: should exceed 1)
    froude = u0 / math.sqrt(abs(gp0) * d.port_diameter) if abs(gp0) > 0 else float("inf")
    if froude < 1:
        warnings.append(f"Port densimetric Froude number is {froude:.2f} (< 1): ambient water may "
                        "intrude into the ports; PLUMES2.0 assumes Fr > 1.")

    h = b0                         # element thickness (results are independent of it)
    m0 = rho0 * math.pi * b0 * b0 * h
    m = m0
    mT = m * e.temperature
    mS = m * e.salinity
    c_eff = e.concentration * 1000.0 / rho0               # mg/kg
    mc = m * c_eff
    b = b0
    x, y, depth = d.x, d.y, d.port_depth
    t = 0.0
    path = 0.0
    alpha = st.aspiration
    bottom = d.water_depth

    steps: List[Step] = []
    events: List[Dict] = []
    merged_at = None
    prev_b, prev_cos, prev_path = b0, None, 0.0
    rising = gp0 > 0
    buoy_sign = 1 if gp0 > 0 else -1
    w_sign = 1 if V[2] >= 0 else -1
    stage = 0                       # number of trap / rise / fall events passed
    trap_depth = None
    termination = "max steps"
    k_prof = ROUND_PEAK_TO_MEAN

    def snapshot(i: int, merged: bool) -> Step:
        T = mT / m
        S = mS / m
        rho = density(S, T)
        ab = amb.at(depth)
        rho_a = density(ab["salinity"], ab["temperature"])
        dil = (rho0 / rho) * (m / m0)
        # peak-to-mean factor: 1 at source, tends to 3.89 (round) or 2.22 (merged)
        kinf = LINE_PEAK_TO_MEAN if merged else ROUND_PEAK_TO_MEAN
        kk = 1 + (kinf - 1) * (1 - 1 / max(dil, 1.0))
        cl = max(1.0, dil / kk)
        dT = T - ab["temperature"]
        # centreline excess temperature, consistent with centreline dilution
        dT0 = e.temperature - ab["temperature"]
        dT_cl = dT0 / cl if dil > 1 else dT
        sp = _norm(V)
        conc = rho * (mc / m) / 1000.0
        return Step(step=i, time=t, x=x, y=y, depth=depth, diameter=2 * b, dilution=dil,
                    centerline_dilution=cl, temperature=T, salinity=S, density=rho,
                    amb_temperature=ab["temperature"], amb_density=rho_a, delta_t=dT,
                    delta_t_centerline=dT_cl, speed=sp, w=V[2], concentration=conc,
                    merged=merged, distance=math.hypot(x - d.x, y - d.y), path_length=path)

    merged_now = False
    steps.append(snapshot(0, False))

    for i in range(1, st.max_steps + 1):
        ab = amb.at(depth)
        Ta, Sa = ab["temperature"], ab["salinity"]
        rho_a = density(Sa, Ta)
        Ua = (ab["ux"], ab["uy"], 0.0)
        ua = _norm(Ua)
        T, S = mT / m, mS / m
        rho = density(S, T)
        sp = _norm(V)
        if sp < 1e-9:
            termination = "plume velocity vanished"
            break
        eh = (V[0] / sp, V[1] / sp, V[2] / sp)

        # projected port spacing in the element cross-section
        d_eff = d.spacing * _norm(_cross(eh, dhat)) if n > 1 else 0.0
        perim = exposed_perimeter(b, d_eff) if n > 1 else 2 * math.pi * b
        afrac = (merged_area(b, d_eff) / (math.pi * b * b)) if n > 1 else 1.0

        # aspiration (Taylor) entrainment
        dv = abs(sp - _dot(Ua, eh))
        Es = rho_a * alpha * perim * h * (dv if st.shear_velocity == "relative" else sp)

        # forced entrainment (projected-area hypothesis)
        Ef = 0.0
        Ef_ref = 0.0
        cos_t = 0.0
        if ua > 1e-12:
            uh = (Ua[0] / ua, Ua[1] / ua, 0.0)
            cos_t = _dot(eh, uh)
            cr = _cross(eh, uh)
            sin_t = _norm(cr)
            width = 2 * b
            if n > 1 and sin_t > 1e-9:
                nh = (cr[0] / sin_t, cr[1] / sin_t, cr[2] / sin_t)
                width = min(2 * b, d.spacing * abs(_dot(nh, dhat)))
            ds = path - prev_path
            dbds = (b - prev_b) / ds if ds > 0 else 0.0
            dcds = (cos_t - prev_cos) / ds if (ds > 0 and prev_cos is not None) else 0.0
            side = width * h * sin_t
            grow = afrac * math.pi * b * dbds * h * cos_t
            curv = afrac * 0.5 * math.pi * b * b * dcds * h
            tw = st.forced_terms
            area_rate = side * tw[0] + grow * tw[1] + curv * tw[2]
            Ef = rho_a * ua * max(area_rate, 0.0) * st.forced_scale
            Ef_ref = rho_a * ua * max(2 * b * h * sin_t * tw[0] + (math.pi * b * dbds * h * cos_t) * tw[1]
                                       + (0.5 * math.pi * b * b * dcds * h) * tw[2], 0.0) * st.forced_scale

        # time step: reference aspiration entrainment = step_mass_fraction * m
        E = (Es + Ef) if st.entrainment == "sum" else max(Es, Ef)
        if st.dt_mode == "total":
            ref_rate = E
        elif st.dt_mode == "unmerged":
            ref_rate = rho_a * alpha * 2 * math.pi * b * h * (dv if st.shear_velocity == "relative" else sp) + Ef_ref
        else:
            ref_rate = rho_a * alpha * 2 * math.pi * b * h * sp
        dt = st.step_mass_fraction * m / ref_rate
        dm = E * dt

        # momentum: entrained ambient momentum + buoyancy (eq. 3)
        buoy = G * (rho_a - rho) / rho
        mV = [m * V[0] + dm * Ua[0], m * V[1] + dm * Ua[1], m * V[2] + dm * Ua[2] + m * buoy * dt]
        m_new = m + dm
        V_new = [c / m_new for c in mV]
        # heat, salt, pollutant (eqs. 4, 5)
        mT += Ta * dm
        mS += Sa * dm
        c_a = ab["background"] * 1000.0 / rho_a
        mc += c_a * dm
        if ab["decay"] > 0:
            mc *= math.exp(-ab["decay"] * dt / 86400.0)

        # kinematics (trapezoidal)
        prev_path = path
        dx = 0.5 * (V[0] + V_new[0]) * dt
        dy = 0.5 * (V[1] + V_new[1]) * dt
        dz = 0.5 * (V[2] + V_new[2]) * dt
        x += dx
        y += dy
        depth -= dz
        path += math.sqrt(dx * dx + dy * dy + dz * dz)
        t += dt

        sp_new = _norm(V_new)
        h = h * sp_new / sp
        m = m_new
        V = V_new
        prev_b, prev_cos = b, (cos_t if ua > 1e-12 else None)

        T, S = mT / m, mS / m
        rho = density(S, T)
        eh = (V[0] / sp_new, V[1] / sp_new, V[2] / sp_new)
        d_eff = d.spacing * _norm(_cross(eh, dhat)) if n > 1 else 0.0
        area = m / (rho * h)
        b = radius_from_area(area, d_eff) if n > 1 else math.sqrt(area / math.pi)

        if n > 1 and not merged_now and 2 * b >= d_eff > 0:
            merged_now = True
            merged_at = i
            events.append({"step": i, "event": "merging", "text": "merging happened"})

        snap = snapshot(i, merged_now)
        steps.append(snap)

        # ---- events: trapping, max rise / fall ----
        ab2 = amb.at(depth)
        rho_a2 = density(ab2["salinity"], ab2["temperature"])
        new_buoy_sign = 1 if rho_a2 - rho > 0 else -1
        new_w_sign = 1 if V[2] > 0 else -1
        stop = None
        if new_buoy_sign != buoy_sign:
            stage += 1
            events.append({"step": i, "event": "trap" if trap_depth is None else "trap2",
                           "text": "Plume traps" if trap_depth is None else "Plume traps (2nd level)",
                           "depth": depth})
            if trap_depth is None:
                trap_depth = depth
            buoy_sign = new_buoy_sign
            if (st.max_rise_fall == 0 and stage >= 1) or (st.max_rise_fall == 2 and _count(events, ("trap", "trap2")) >= 2):
                stop = "trap level" if st.max_rise_fall == 0 else "second trap level"
        if new_w_sign != w_sign:
            w_sign = new_w_sign
            ev = "max_rise" if new_w_sign < 0 else "max_fall"
            events.append({"step": i, "event": ev,
                           "text": "Maximum rise" if ev == "max_rise" else "Maximum fall", "depth": depth})
            if (st.max_rise_fall == 1 and ev == "max_rise" and rising) or \
               (st.max_rise_fall == 1 and ev == "max_fall" and not rising) or \
               (st.max_rise_fall == 3 and ev == ("max_fall" if rising else "max_rise")):
                stop = ev.replace("_", " ")

        cosphi = math.hypot(V[0], V[1]) / sp_new
        half = b * cosphi
        if st.stop_at_surface and depth - half <= 0:
            events.append({"step": i, "event": "surface", "text": "Plume surfaces", "depth": depth})
            stop = "surface"
        elif st.stop_at_bottom and depth + half >= bottom and i > 1:
            events.append({"step": i, "event": "bottom", "text": "Bottom hit", "depth": depth})
            stop = "bottom"
        if st.stop_at_shoreline and st.shoreline_distance > 0:
            sa = math.radians(st.shoreline_angle)
            along = (x - d.x) * math.cos(sa) + (y - d.y) * math.sin(sa)
            if along + b >= st.shoreline_distance:
                events.append({"step": i, "event": "shoreline", "text": "Plume hits shoreline"})
                stop = "shoreline"
        if snap.dilution > 1e6:
            stop = "dilution limit"
        if stop:
            termination = stop
            break

    end = steps[-1]
    exact_end = None
    if termination in ("surface", "bottom") and len(steps) >= 2:
        exact_end = _interpolate_contact(steps[-2], steps[-1], termination, bottom)
    start_depth = d.port_depth
    rise = start_depth - min(s.depth for s in steps) if rising else max(s.depth for s in steps) - start_depth
    initial = {
        "port_velocity": u0, "port_flow": q_port, "effluent_density": rho0,
        "ambient_density_at_port": rho_a0, "reduced_gravity": gp0, "port_froude": froude,
        "momentum_flux": q_port * u0, "buoyancy_flux": q_port * gp0,
    }
    if termination == "max steps":
        warnings.append("Near-field integration reached the step limit before a termination criterion.")
    return NearfieldResult(steps=steps, events=events, termination=termination,
                           end=exact_end or end, last_step=end,
                           trap_depth=trap_depth, rise_height=rise, merged_at_step=merged_at,
                           initial=initial, warnings=warnings)


def _clearance(s: Step, kind: str, bottom: float) -> float:
    # vertical half-extent of an inclined cross-section: b cos(phi)
    cosphi = math.sqrt(max(s.speed ** 2 - s.w ** 2, 0.0)) / s.speed if s.speed > 0 else 1.0
    half = 0.5 * s.diameter * cosphi
    return (s.depth - half) if kind == "surface" else (bottom - s.depth - half)


def _interpolate_contact(a: Step, b: Step, kind: str, bottom: float) -> Step:
    """Linear interpolation to the exact boundary-contact point between the
    last two steps, so the terminal state does not depend on step size (an
    improvement on PLUMES2.0, which reports the first step past contact)."""
    ca, cb = _clearance(a, kind, bottom), _clearance(b, kind, bottom)
    if ca <= 0 or cb > 0 or ca == cb:
        return b
    f = ca / (ca - cb)
    vals = {}
    for k, va in a.__dict__.items():
        vb = getattr(b, k)
        if isinstance(va, bool) or k == "step":
            vals[k] = vb
        else:
            vals[k] = va + f * (vb - va)
    return Step(**vals)


def _count(events, names) -> int:
    return sum(1 for e in events if e["event"] in names)
