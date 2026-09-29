"""Write EPA Visual Plumes UM3-style input decks for the P-3 near-field cases.

Visual Plumes is a Windows desktop application. These decks are text prompts a
person can use to enter each case; the exact binary input format varies by VP
version, so we emit a clear parameter sheet plus a minimal UM3-like card that
matches the comparison sweep in ``benchmarks/compare_near_field.py``.
"""
from __future__ import annotations

import json
from pathlib import Path

# Keep in sync with benchmarks/compare_near_field.py
DIAMETERS_M = [0.1, 0.3, 0.6, 1.0]
FLOWS_M3S = [0.02, 0.05, 0.15, 0.4]
G_PRIMES = [0.005, 0.015, 0.025, 0.04]
DEPTHS_M = [4.0, 10.0, 25.0, 50.0, 80.0]

DECK_DIR = Path(__file__).resolve().parent / "decks"


def case_id(d: float, Q: float, gp: float, z: float) -> str:
    return f"d{d:g}_Q{Q:g}_gp{gp:g}_z{z:g}".replace(".", "p")


def ambient_and_effluent(g_prime: float) -> dict:
    """Map reduced gravity to a simple T/S pair for UM3 data entry.

    Uses a fixed ambient (12 °C, 32 PSU) and sets effluent temperature so that
    UNESCO EOS-80 reduced gravity is approximately ``g_prime``. The value is
    approximate for deck preparation; the comparison key is still (d, Q, g', z).
    """
    # Linearised α_T ≈ 2e-4 /K for cool seawater → ΔT ≈ g' / (g α_T)
    # verify: operator should refine T_e in VP until reported g' matches.
    g = 9.81
    alpha_t = 2.0e-4  # verify order-of-magnitude thermal expansion
    delta_t = g_prime / (g * alpha_t)
    return {
        "t_ambient_c": 12.0,
        "s_ambient_psu": 32.0,
        "t_effluent_c": 12.0 + delta_t,
        "s_effluent_psu": 32.0,
        "delta_t_k_approx": delta_t,
        "note": "verify effluent T in VP so discharge g' matches case g_prime",
    }


def write_deck(d: float, Q: float, gp: float, z: float, out_dir: Path) -> Path:
    cid = case_id(d, Q, gp, z)
    ts = ambient_and_effluent(gp)
    area = 3.141592653589793 * d ** 2 / 4.0
    u = Q / area
    card = {
        "case_id": cid,
        "model": "UM3",
        "description": "Aquatic Guardian P-3 round buoyant jet, stagnant unstratified",
        "port": {
            "diameter_m": d,
            "flow_m3s": Q,
            "exit_velocity_ms": u,
            "vertical_angle_deg": 90.0,
            "horizontal_angle_deg": 0.0,
            "port_height_above_bottom_m": 0.0,
            "n_ports": 1,
        },
        "ambient": {
            "type": "stagnant_unstratified",
            "current_ms": 0.0,
            "depth_m": z,
            "t_c": ts["t_ambient_c"],
            "s_psu": ts["s_ambient_psu"],
        },
        "effluent": {
            "t_c": ts["t_effluent_c"],
            "s_psu": ts["s_effluent_psu"],
            "target_g_prime_m_s2": gp,
            "delta_t_k_approx": ts["delta_t_k_approx"],
            "note": ts["note"],
        },
        "output_request": {
            "save_csv_as": f"../outputs/{cid}.csv",
            "columns": ["z_m", "dilution_centreline"],
            "dilution_at_surface_z_m": z,
        },
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{cid}.json"
    path.write_text(json.dumps(card, indent=2), encoding="utf-8")

    # Human-readable entry sheet for the Windows UI
    txt = out_dir / f"{cid}.txt"
    txt.write_text(
        f"""Visual Plumes UM3 entry sheet — {cid}
========================================
Model: UM3 (or NRFIELD if preferred for multiport; this case is a SINGLE round port)
Ambient: stagnant, unstratified, depth H = {z} m, U = 0
Port: diameter D = {d} m, Q = {Q} m³/s, vertical (90°), one port
Exit velocity U0 ≈ {u:.4f} m/s
Ambient T/S: {ts['t_ambient_c']} °C / {ts['s_ambient_psu']} PSU
Effluent T/S (starting guess): {ts['t_effluent_c']:.3f} °C / {ts['s_effluent_psu']} PSU
Target reduced gravity g' = {gp} m/s²  ({ts['note']})

After the run, export centreline dilution versus height and save as:
  benchmarks/visual_plumes/outputs/{cid}.csv
with header:
  z_m,dilution_centreline
Include a row at z = {z} (surface / end of near field for this case).
""",
        encoding="utf-8",
    )
    return path


def write_all(out_dir: Path | None = None) -> list[Path]:
    out_dir = out_dir or DECK_DIR
    paths = []
    for d in DIAMETERS_M:
        for Q in FLOWS_M3S:
            for gp in G_PRIMES:
                for z in DEPTHS_M:
                    paths.append(write_deck(d, Q, gp, z, out_dir))
    manifest = {
        "n_cases": len(paths),
        "diameters_m": DIAMETERS_M,
        "flows_m3s": FLOWS_M3S,
        "g_primes": G_PRIMES,
        "depths_m": DEPTHS_M,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return paths


if __name__ == "__main__":
    written = write_all()
    print(f"Wrote {len(written)} decks under {DECK_DIR}")
