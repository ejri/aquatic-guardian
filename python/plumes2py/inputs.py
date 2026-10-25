"""Model inputs, mirroring the PLUMES2.0 Diffuser / Effluent / Ambient /
Model Run tabs (manual §4.2), plus the extra fields the extended metrics need.

All quantities are SI internally. Loaders accept the CSV files PLUMES2.0
saves (``Diffuser_example.csv`` etc.) and its ``.prj`` project file so an
existing PLUMES2.0 project can be re-run here unchanged.
"""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional, Sequence

from .seawater import MGD_TO_M3S, CFS_TO_M3S


@dataclass
class Diffuser:
    port_diameter: float              # m
    port_elevation: float             # m above seabed
    vertical_angle: float             # deg from horizontal, + up
    horizontal_angle: float           # deg, counter-clockwise from x-axis
    n_ports: int = 1
    spacing: float = 0.0              # m between ports
    port_depth: float = 10.0          # m below surface to port centreline
    x: float = 0.0
    y: float = 0.0
    contraction: float = 1.0          # diffuser contraction coefficient
    # Not a PLUMES2.0 input: orientation of the diffuser line. PLUMES2.0 has
    # no field for it; ports are taken as normal to the diffuser (manual Fig. 6).
    axis_deg: Optional[float] = None

    @property
    def water_depth(self) -> float:
        return self.port_depth + self.port_elevation

    @property
    def diffuser_axis_deg(self) -> float:
        return self.horizontal_angle + 90.0 if self.axis_deg is None else self.axis_deg

    def validate(self) -> List[str]:
        errs = []
        if self.port_depth <= 0:
            errs.append("Port depth must be greater than zero; PLUMES2.0 cannot model surface discharges.")
        if self.port_elevation < 0:
            errs.append("Port elevation cannot be negative.")
        if self.port_diameter <= 0:
            errs.append("Port diameter must be positive.")
        if self.n_ports < 1:
            errs.append("At least one port is needed.")
        if self.n_ports > 1 and self.spacing <= 0:
            errs.append("Multiport diffusers need a port spacing greater than zero.")
        if not 0 < self.contraction <= 1:
            errs.append("Contraction coefficient must be in (0, 1]; 0.61 sharp-edged, 1.0 bell-mouthed.")
        return errs


@dataclass
class Effluent:
    flow: float                       # total discharge, m^3/s
    salinity: float = 0.0             # psu
    temperature: float = 20.0         # C
    concentration: float = 100.0      # pollutant, mg/L (kg/kg in PLUMES2.0 output label)

    @classmethod
    def from_units(cls, flow: float, flow_units: str = "m3/s", **kw) -> "Effluent":
        u = flow_units.lower()
        q = flow * {"m3/s": 1.0, "cms": 1.0, "mgd": MGD_TO_M3S, "cfs": CFS_TO_M3S}[u]
        return cls(flow=q, **kw)


@dataclass
class AmbientRow:
    depth: float                       # m, positive down
    speed: float = 0.0                 # near-field current, m/s
    direction: float = 0.0             # deg, ccw from x-axis
    salinity: float = 32.0             # psu
    temperature: float = 10.0          # C
    background: float = 0.0            # pollutant background, mg/L
    decay: float = 0.0                 # 1/day
    far_speed: Optional[float] = None  # far-field current, m/s
    far_direction: Optional[float] = None
    alpha: float = 0.0003              # Brooks dispersion parameter, m^(2/3)/s


@dataclass
class Ambient:
    rows: List[AmbientRow]

    def __post_init__(self):
        if not self.rows:
            raise ValueError("Ambient profile needs at least one row.")
        self.rows = sorted(self.rows, key=lambda r: r.depth)

    def _interp(self, depth: float, attr: str) -> float:
        rows = self.rows
        if depth <= rows[0].depth:
            return getattr(rows[0], attr)
        if depth >= rows[-1].depth:
            return getattr(rows[-1], attr)
        for a, b in zip(rows, rows[1:]):
            if a.depth <= depth <= b.depth:
                f = (depth - a.depth) / (b.depth - a.depth) if b.depth > a.depth else 0.0
                va, vb = getattr(a, attr), getattr(b, attr)
                return va + f * (vb - va)
        return getattr(rows[-1], attr)

    def _component_rows(self):
        if not hasattr(self, "_uxy"):
            self._uxy = [(r.depth,
                          r.speed * math.cos(math.radians(r.direction)),
                          r.speed * math.sin(math.radians(r.direction))) for r in self.rows]
        return self._uxy

    def _interp_xy(self, depth: float):
        rows = self._component_rows()
        if depth <= rows[0][0]:
            return rows[0][1], rows[0][2]
        if depth >= rows[-1][0]:
            return rows[-1][1], rows[-1][2]
        for a, b in zip(rows, rows[1:]):
            if a[0] <= depth <= b[0]:
                f = (depth - a[0]) / (b[0] - a[0]) if b[0] > a[0] else 0.0
                return a[1] + f * (b[1] - a[1]), a[2] + f * (b[2] - a[2])
        return rows[-1][1], rows[-1][2]

    def at(self, depth: float) -> dict:
        """Ambient conditions at ``depth`` (linear interpolation, constant
        extrapolation, as in Visual Plumes). The current is interpolated as a
        vector, and its magnitude as a scalar, so a 350 to 10 deg turn works and
        the speed profile matches the table exactly."""
        sp = self._interp(depth, "speed")
        ux, uy = self._interp_xy(depth)
        mag = math.hypot(ux, uy)
        ux, uy = (ux / mag * sp, uy / mag * sp) if mag > 1e-12 else (0.0, 0.0)
        return {
            "salinity": self._interp(depth, "salinity"),
            "temperature": self._interp(depth, "temperature"),
            "background": self._interp(depth, "background"),
            "decay": self._interp(depth, "decay"),
            "ux": ux, "uy": uy, "speed": sp,
        }

    def far_at(self, depth: float) -> dict:
        r = min(self.rows, key=lambda q: abs(q.depth - depth))
        sp = self._interp(depth, "far_speed") if all(q.far_speed is not None for q in self.rows) else self._interp(depth, "speed")
        if all(q.far_direction is not None for q in self.rows):
            direction = self._interp(depth, "far_direction")
        else:
            direction = r.direction
        return {"speed": sp, "direction": direction, "alpha": self._interp(depth, "alpha"),
                "decay": self._interp(depth, "decay")}

    @classmethod
    def uniform(cls, depth: float, speed: float, temperature: float, salinity: float,
                direction: float = 0.0, alpha: float = 0.0003, n: int = 2) -> "Ambient":
        return cls([AmbientRow(depth=d, speed=speed, direction=direction, salinity=salinity,
                               temperature=temperature, far_speed=speed, far_direction=direction,
                               alpha=alpha)
                    for d in [0.0, depth]][: max(2, n)])


@dataclass
class MixingZone:
    acute: Optional[float] = None     # m from outfall
    chronic: Optional[float] = None   # m from outfall


@dataclass
class Settings:
    aspiration: float = 0.1           # Taylor aspiration coefficient (UM3 default)
    step_mass_fraction: float = 0.02  # target mass growth per step (sets dt)
    stop_at_bottom: bool = True
    stop_at_surface: bool = True
    stop_at_shoreline: bool = False
    shoreline_distance: float = 0.0
    shoreline_angle: float = 0.0
    max_rise_fall: int = 2            # 0 trap, 1 max rise, 2 second trap, 3 max fall
    nearfield_output_interval: int = 5
    farfield: bool = True
    farfield_case: str = "four_thirds"  # "constant" | "linear" | "four_thirds"
    farfield_output_interval: float = 10.0
    farfield_max_dilution: float = 5000.0
    farfield_stop_distance: Optional[float] = None  # default: chronic MZ
    max_steps: int = 50000
    # Entrainment closure (see um3.py and VALIDATION.md). Manual eq. 2 sums
    # forced and aspiration entrainment. The time step is set so the
    # unmerged entrainment adds step_mass_fraction of the element mass,
    # which reproduces the 2.00 %/step growth in the PLUMES2.0 reference.
    entrainment: str = "sum"           # "sum" (eq. 2) or "max" (JETLAG)
    shear_velocity: str = "relative"   # along-axis |V| - Ua.e, or "absolute" |V|
    dt_mode: str = "unmerged"          # "unmerged", "total" or "reference"
    # Scale on Frick's projected-area forced entrainment. 0.81 is calibrated
    # on the single public PLUMES2.0 reference trajectory (RMS 2.9 % in
    # dilution, terminal state within 1.2 %). Re-fit with benchmarks/plumes2/.
    forced_scale: float = 0.81
    forced_terms: tuple = (1.0, 1.0, 1.0)  # side, growth, curvature
    # Wastefield initial width rule (PLUMES2.0 computes it internally from the
    # merged plumes; the rule is not published - see VALIDATION.md).
    wastefield_rule: str = "diffuser_length_plus_diameter"


@dataclass
class Scenario:
    diffuser: Diffuser
    effluent: Effluent
    ambient: Ambient
    mixing_zone: MixingZone = field(default_factory=MixingZone)
    settings: Settings = field(default_factory=Settings)
    name: str = "scenario"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Scenario":
        amb = d["ambient"]
        rows = amb["rows"] if isinstance(amb, dict) else amb
        return cls(
            diffuser=Diffuser(**d["diffuser"]),
            effluent=Effluent(**d["effluent"]),
            ambient=Ambient([AmbientRow(**r) for r in rows]),
            mixing_zone=MixingZone(**d.get("mixing_zone", {})),
            settings=Settings(**d.get("settings", {})),
            name=d.get("name", "scenario"),
        )


# --------------------------------------------------------------------------
# PLUMES2.0 file loaders
# --------------------------------------------------------------------------

def _floats(row: Sequence[str]) -> List[Optional[float]]:
    out = []
    for c in row:
        c = c.strip().strip('"')
        try:
            out.append(float(c))
        except ValueError:
            out.append(None)
    return out


def _csv_rows(path: Path) -> List[List[str]]:
    with open(path, newline="") as f:
        return [r for r in csv.reader(f)]


def load_plumes2_csvs(folder: str | Path, flow_units: str = "MGD", case: int = 1) -> Scenario:
    """Load PLUMES2.0 ``Diffuser_*.csv``, ``Effluent_*.csv``, ``Ambient_*.csv``
    and ``Mixing_zone_*.csv`` from ``folder``. Effluent flow is in the units the
    GUI used when saving (the bundled example is in MGD)."""
    folder = Path(folder)
    pick = lambda pat: sorted(folder.glob(pat))[0]  # noqa: E731
    d = _floats(_csv_rows(pick("Diffuser*.csv"))[case - 1][1:])
    diffuser = Diffuser(port_diameter=d[0], port_elevation=d[1], vertical_angle=d[2],
                        horizontal_angle=d[3], n_ports=int(d[4]), spacing=d[5],
                        port_depth=d[6], x=d[7] or 0.0, y=d[8] or 0.0)
    e = _floats(_csv_rows(pick("Effluent*.csv"))[case - 1][1:])
    effluent = Effluent.from_units(e[0], flow_units, salinity=e[1], temperature=e[2],
                                   concentration=e[3] if len(e) > 3 and e[3] is not None else 0.0)
    rows = []
    for r in _csv_rows(pick("Ambient_*.csv")):
        v = _floats(r)
        if not v or v[0] is None:
            continue
        rows.append(AmbientRow(depth=v[0], speed=v[1], direction=v[2], salinity=v[3],
                               temperature=v[4], background=v[5] or 0.0, decay=v[6] or 0.0,
                               far_speed=v[7], far_direction=v[8], alpha=v[9] or 0.0003))
    mz = MixingZone()
    try:
        m = _floats(_csv_rows(pick("Mixing_zone*.csv"))[case - 1][1:])
        mz = MixingZone(acute=m[0], chronic=m[1])
    except (IndexError, FileNotFoundError):
        pass
    s = Settings(farfield_stop_distance=mz.chronic)
    return Scenario(diffuser, effluent, Ambient(rows), mz, s, name=folder.name)


def reference_example() -> Scenario:
    """The example project shipped with PLUMES2.0 (github.com/ssmc-uw/PLUMES2.0).

    Note: the manual text (§4.2.3) describes the effluent as 26.3 C, but the
    shipped Effluent_example.csv, Example_project.prj and the reference output
    table all carry 2.63 C. The files are what produced the reference output,
    so 2.63 C is used here.
    """
    sc = load_plumes2_csvs(Path(__file__).parent / "data", flow_units="MGD")
    sc.settings.farfield_output_interval = 5.0
    sc.name = "PLUMES2.0 Example_project"
    return sc
