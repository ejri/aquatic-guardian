"""Write benchmarks/plumes2/cases.csv: the PLUMES 2.0 (UM3) benchmark matrix for
register item P-3, with the library's screening prediction for each case.

Every case is a vertical discharge of heated SEAWATER (effluent salinity equals
ambient) into an unstratified 12 C, 30 psu ambient. Run: python benchmarks/plumes2/make_cases.py
"""
from __future__ import annotations
import csv, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from aquatic_guardian import plume  # noqa: E402

T_AMB, S_AMB, PORT_ELEV = 12.0, 30.0, 0.5
# id, purpose, n_ports, port_d_m, spacing_m, total_flow_m3s, delta_t_k, water_depth_m, current_ms
CASES = [
    ("A1", "single port, reference", 1, 0.30, 0.0, 0.084, 8.0, 20.0, 0.01),
    ("A2", "single port, weak buoyancy", 1, 0.30, 0.0, 0.084, 4.0, 20.0, 0.01),
    ("A3", "single port, strong buoyancy", 1, 0.30, 0.0, 0.084, 12.0, 20.0, 0.01),
    ("A4", "single port, jet-dominated, shallow", 1, 0.50, 0.0, 0.448, 15.0, 8.0, 0.01),
    ("A5", "single port, plume-dominated, deep", 1, 0.15, 0.0, 0.020, 8.0, 40.0, 0.01),
    ("A6", "single large pipe, whole 24 MW flow", 1, 1.00, 0.0, 0.840, 8.0, 20.0, 0.01),
    ("B1", "10 ports, line regime (s/H 0.2)", 10, 0.30, 4.0, 0.840, 8.0, 20.0, 0.01),
    ("B2", "10 ports, transitional (s/H 0.6)", 10, 0.30, 12.0, 0.840, 8.0, 20.0, 0.01),
    ("B3", "10 ports, point regime (s/H 1.25)", 10, 0.30, 25.0, 0.840, 8.0, 20.0, 0.01),
    ("B4", "20 ports, line, 48 MW", 20, 0.30, 2.0, 1.680, 8.0, 20.0, 0.01),
    ("B5", "4 ports, shallow, transitional (s/H 0.6)", 4, 0.25, 6.0, 0.300, 8.0, 10.0, 0.01),
    ("B6", "30 ports, line, ~120 MW, deeper", 30, 0.35, 5.0, 4.200, 8.0, 30.0, 0.01),
    ("C1", "A1 in a 0.1 m/s current", 1, 0.30, 0.0, 0.084, 8.0, 20.0, 0.10),
    ("C2", "A1 in a 0.3 m/s current", 1, 0.30, 0.0, 0.084, 8.0, 20.0, 0.30),
    ("C3", "B1 in a 0.1 m/s current", 10, 0.30, 4.0, 0.840, 8.0, 20.0, 0.10),
    ("C4", "B1 in a 0.3 m/s current", 10, 0.30, 4.0, 0.840, 8.0, 20.0, 0.30),
]


def library_min_dilution(n, d, s, q_total, dT, depth, rise):
    """The library's screening minimum (centreline) dilution after `rise` metres,
    using the same regime choice and envelope as plume.near_field."""
    from aquatic_guardian.seawater import reduced_gravity
    gp = reduced_gravity(T_AMB, dT, S_AMB)
    diff = plume.Diffuser(q_total, n, d, s if n > 1 else 1.0)
    f = plume.fluxes(diff, gp)
    reg = plume.regime(s if n > 1 else 1.0, depth, n)
    s_pt = max(plume.dilution_point(f, rise), plume.dilution_jet(d, rise))
    s_ln = plume.dilution_line(f, rise) if n > 1 else float("nan")
    val = s_pt if reg == "point" else min(s_pt, s_ln)
    return max(val, 1.0), reg


def rows():
    out = []
    for cid, why, n, d, s, q, dT, H, u in CASES:
        port_depth = H - PORT_ELEV
        lib, reg = library_min_dilution(n, d, s, q, dT, H, port_depth)
        out.append({"case_id": cid, "purpose": why, "number_of_ports": n, "port_diameter_m": d,
                    "port_spacing_m": s if n > 1 else "", "port_elevation_m": PORT_ELEV, "port_depth_m": port_depth,
                    "vertical_angle_deg": 90, "horizontal_angle_deg": 0, "total_effluent_flow_m3s": q,
                    "effluent_temperature_c": T_AMB + dT, "effluent_salinity_psu": S_AMB,
                    "ambient_temperature_c": T_AMB, "ambient_salinity_psu": S_AMB, "water_depth_m": H,
                    "current_ms": u, "library_regime": reg, "library_min_dilution_at_surface": round(lib, 2),
                    "library_rise_k_at_surface": round(dT / lib, 3)})
    return out


if __name__ == "__main__":
    r = rows()
    p = Path(__file__).with_name("cases.csv")
    with p.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(r[0])); w.writeheader(); w.writerows(r)
    print(f"wrote {p} ({len(r)} cases)")
