"""Near-field screening for multiport diffuser discharges.

Implements the length-scale framework of Fischer et al. (1979), Jirka (2004;
2006) and Lee & Chu (2003), with the port-spacing regime test of Tian,
Roberts & Daviero (2004): merged line plume when s/H <= 0.3, independent
point plumes when s/H >= 1.0, transitional in between.

Correction 1 (docs/CORRECTIONS.md): point-plume formulas take PER-PORT fluxes
(Q, M, B of one port). Line-plume formulas take PER-UNIT-LENGTH fluxes
(q = Q_T/L, m, b = g' q). Substituting total diffuser flow Q_T into a
point-plume law underestimates dilution by N**(2/3).

Dilution coefficients are the stagnant, unstratified asymptotic values quoted in
Fischer et al. (1979) for minimum (centreline) dilution: 0.089 for a round
plume and 0.38 for a line plume. They are parameters, not constants: lab and
field calibrations differ, and a UM3/NRFIELD or CORMIX benchmark is required
before regulatory use (docs/VERIFICATION.md, item P-3).
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from .seawater import reduced_gravity

C_POINT = 0.089       # S = C B^(1/3) z^(5/3) / Q     (round plume, minimum dilution)
C_LINE = 0.38         # S = C b^(1/3) z / q            (line plume, minimum dilution)
JET_DECAY = 5.6       # round jet centreline: S = z / (JET_DECAY d)


@dataclass
class Diffuser:
    total_flow_m3s: float
    n_ports: int
    port_diameter_m: float
    port_spacing_m: float

    @property
    def length_m(self) -> float:
        """Effective line length N*s (each port represents one spacing)."""
        return self.n_ports * self.port_spacing_m if self.n_ports > 1 else self.port_diameter_m

    @property
    def port_flow_m3s(self) -> float:
        return self.total_flow_m3s / self.n_ports

    @property
    def jet_velocity_ms(self) -> float:
        return self.port_flow_m3s / (math.pi * self.port_diameter_m ** 2 / 4.0)


def fluxes(d: Diffuser, g_prime: float) -> dict:
    Q = d.port_flow_m3s
    M = Q * d.jet_velocity_ms
    B = g_prime * Q
    L = d.length_m
    q = d.total_flow_m3s / L
    return {"Q": Q, "M": M, "B": B, "q": q, "m": M / d.port_spacing_m if d.n_ports > 1 else M,
            "b": g_prime * q, "L": L}


def length_scales(f: dict, u_ambient: float = 0.0) -> dict:
    ls = {
        "l_Q": f["Q"] / math.sqrt(f["M"]),
        "l_M": f["M"] ** 0.75 / math.sqrt(f["B"]) if f["B"] > 0 else float("inf"),
    }
    if u_ambient > 0:
        ls["l_m_crossflow"] = math.sqrt(f["M"]) / u_ambient       # jet-to-crossflow
        ls["l_b_crossflow"] = f["B"] / u_ambient ** 3              # plume-to-crossflow
        ls["F_line"] = u_ambient ** 3 / f["b"] if f["b"] > 0 else float("inf")
    return ls


def regime(port_spacing_m: float, depth_m: float, n_ports: int = 2) -> str:
    if n_ports <= 1:
        return "point"          # a single port cannot form a line plume
    r = port_spacing_m / depth_m
    if r <= 0.3:
        return "line"
    if r >= 1.0:
        return "point"
    return "transitional"


def dilution_point(f: dict, z: float, c: float = C_POINT) -> float:
    return c * f["B"] ** (1 / 3) * z ** (5 / 3) / f["Q"]


def dilution_line(f: dict, z: float, c: float = C_LINE) -> float:
    return c * f["b"] ** (1 / 3) * z / f["q"]


def dilution_jet(port_diameter_m: float, z: float) -> float:
    return z / (JET_DECAY * port_diameter_m)


def total_flow_error_factor(n_ports: int) -> float:
    """Factor by which a point-plume law under-predicts dilution when fed Q_T."""
    return n_ports ** (2 / 3)


def near_field(d: Diffuser, depth_m: float, t_ambient_c: float, delta_t_k: float,
               s_psu: float, u_ambient: float = 0.0) -> dict:
    """Stagnant, unstratified screening dilution at the surface (z = depth).

    Uses the envelope max(jet, plume) of the two asymptotes, each of which
    under-predicts dilution in the other's regime. Crossflow generally increases
    dilution, so the stagnant value is the conservative (low) case used at slack
    water. Stratification-driven trapping is NOT represented.
    """
    gp = reduced_gravity(t_ambient_c, delta_t_k, s_psu)
    f = fluxes(d, gp)
    ls = length_scales(f, u_ambient)
    reg = regime(d.port_spacing_m, depth_m, d.n_ports)
    z = depth_m
    s_point = max(dilution_point(f, z), dilution_jet(d.port_diameter_m, z)) if gp > 0 else dilution_jet(d.port_diameter_m, z)
    s_line = dilution_line(f, z) if gp > 0 else float("nan")
    if reg == "point":
        s = s_point
    elif reg == "line":
        s = s_line
    else:
        s = min(s_point, s_line)   # conservative bracket in the transitional band
    s = max(s, 1.0)
    return {
        "g_prime": gp, "fluxes": f, "length_scales": ls, "regime": reg,
        "s_over_H": d.port_spacing_m / depth_m,
        "dilution_point": s_point, "dilution_line": s_line, "dilution": s,
        "delta_t_near_field_k": delta_t_k / s,
        "jet_dominated": ls["l_M"] > depth_m,
    }
