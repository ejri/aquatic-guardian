"""Translate a data-centre cooling design into a PLUMES scenario.

Seawater-cooled and submerged facilities discharge water at intake salinity,
not 0 psu (an Aquatic Guardian benchmark finding: PLUMES2.0 runs for data
centres must set effluent salinity to ambient). Heat reaching the water is
IT load x PUE x (share rejected to water) x (1 - reuse before discharge).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional

from .inputs import Ambient, AmbientRow, Diffuser, Effluent, MixingZone, Scenario, Settings
from .seawater import density, heat_capacity


@dataclass
class DataCentreDesign:
    it_mw: float = 24.0
    pue: float = 1.15
    share_to_water: float = 1.0       # fraction of facility heat rejected to the water body
    reuse_fraction: float = 0.0       # recovered before discharge (ERF-style)
    delta_t_k: float = 8.0            # cooling-water temperature rise
    n_ports: int = 4
    port_diameter: Optional[float] = None   # m; auto-sized for target velocity if None
    target_port_velocity: float = 3.0       # m/s
    spacing: float = 8.0
    port_depth: float = 15.0
    port_elevation: float = 1.0
    vertical_angle: float = 20.0
    horizontal_angle: float = 0.0
    mode: str = "outfall"             # "outfall" (pumped) or "pod" (passive hull, screening only)
    pod_hull_delta_t_k: float = 1.0   # pod mode: warm boundary-layer excess at the hull


def heat_to_water_mw(d: DataCentreDesign) -> float:
    return d.it_mw * d.pue * d.share_to_water * (1.0 - d.reuse_fraction)


def build(d: DataCentreDesign, *, sst_c: float, salinity: float, current_ms: float,
          current_dir: float = 0.0, profile: Optional[List[AmbientRow]] = None,
          acute_m: float = 30.0, chronic_m: float = 300.0, alpha: float = 0.0003) -> Scenario:
    P = heat_to_water_mw(d) * 1e6
    dT = d.pod_hull_delta_t_k if d.mode == "pod" else d.delta_t_k
    t_out = sst_c + dT
    rho = density(salinity, t_out)
    cp = heat_capacity(salinity, sst_c + dT / 2)
    Q = P / (rho * cp * dT) if dT > 0 else 0.0
    n = max(1, d.n_ports)
    if d.mode == "pod":
        # Passive pod: heat leaves through a warm boundary layer rising off the
        # hull. Approximate as a low-momentum buoyant source of the same heat
        # (screening only; UM3 is not designed for distributed hull heat).
        diam = d.port_diameter or max(0.5, math.sqrt(4 * Q / n / (math.pi * 0.05)))
        vertical = 90.0
    else:
        diam = d.port_diameter or math.sqrt(4 * (Q / n) / (math.pi * d.target_port_velocity))
        vertical = d.vertical_angle
    diffuser = Diffuser(port_diameter=diam, port_elevation=d.port_elevation, vertical_angle=vertical,
                        horizontal_angle=d.horizontal_angle, n_ports=n, spacing=d.spacing,
                        port_depth=d.port_depth)
    effluent = Effluent(flow=Q, salinity=salinity, temperature=t_out, concentration=0.0)
    if profile is None:
        depth = d.port_depth + d.port_elevation
        profile = [AmbientRow(depth=z, speed=current_ms, direction=current_dir, salinity=salinity,
                              temperature=sst_c, far_speed=current_ms, far_direction=current_dir,
                              alpha=alpha) for z in (0.0, depth)]
    s = Settings(farfield_stop_distance=max(chronic_m, 2 * chronic_m))
    s.farfield_output_interval = max(5.0, round(chronic_m / 30, 0))
    return Scenario(diffuser, effluent, Ambient(profile), MixingZone(acute=acute_m, chronic=chronic_m),
                    s, name=f"{d.it_mw:g} MW data centre ({d.mode})")
