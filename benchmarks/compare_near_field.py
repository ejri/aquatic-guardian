"""Sweep library near-field asymptotes against the independent integral model.

Parameter ranges match ``tests/test_engine_parity.py`` randomised screening inputs:
port diameter 0.1–1.0 m, depth 4–80 m, and discharge conditions that produce
reduced gravity and per-port flows spanning the same order as the parity suite.

Writes:
  benchmarks/results/near_field_comparison.csv
  benchmarks/results/near_field_ratio_vs_z_lM.svg

When Visual Plumes CSV files are present under benchmarks/visual_plumes/outputs/,
those columns are merged into the comparison CSV.
"""
from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from aquatic_guardian import plume  # noqa: E402
from benchmarks.integral_jet import dilution_at_height, jet_momentum_length  # noqa: E402

RESULTS = Path(__file__).resolve().parent / "results"
VP_OUTPUTS = Path(__file__).resolve().parent / "visual_plumes" / "outputs"


# Ranges from tests/test_engine_parity.py (and plausible per-port flows).
DIAMETERS_M = [0.1, 0.3, 0.6, 1.0]
# Per-port flows spanning weak to strong discharge (parity uses plant-scale total
# flow via cooling; here we set Q_port directly for a single round port).
FLOWS_M3S = [0.02, 0.05, 0.15, 0.4]
# Reduced gravity: heated seawater order 0.01–0.03 m/s² (S-2) plus weaker/stronger.
G_PRIMES = [0.005, 0.015, 0.025, 0.04]
DEPTHS_M = [4.0, 10.0, 25.0, 50.0, 80.0]


def library_point_envelope(Q: float, M: float, B: float, d: float, z: float) -> dict:
    """Library stagnant point-source envelope: max(jet, plume) asymptotes."""
    f = {"Q": Q, "M": M, "B": B, "q": Q, "b": B}
    s_plume = plume.dilution_point(f, z) if B > 0 else float("nan")
    s_jet = plume.dilution_jet(d, z)
    s = max(s_plume, s_jet) if B > 0 else s_jet
    s = max(s, 1.0)
    l_M = jet_momentum_length(M, B) if B > 0 else float("inf")
    return {
        "dilution_library": s,
        "dilution_library_plume": s_plume,
        "dilution_library_jet": s_jet,
        "l_M_m": l_M,
        "jet_dominated": bool(l_M > z) if math.isfinite(l_M) else True,
    }


def case_grid():
    for d in DIAMETERS_M:
        for Q in FLOWS_M3S:
            for gp in G_PRIMES:
                for z in DEPTHS_M:
                    yield d, Q, gp, z


def run_sweep() -> list[dict]:
    rows = []
    for d, Q, gp, z in case_grid():
        area = math.pi * d ** 2 / 4.0
        U = Q / area
        M = Q * U
        B = gp * Q
        lib = library_point_envelope(Q, M, B, d, z)
        integ = dilution_at_height(d, Q, gp, z)
        s_lib = lib["dilution_library"]
        s_int = integ["dilution_centreline"]
        ratio = s_lib / s_int if s_int > 0 else float("nan")
        # Conservative for thermal impact means lower predicted dilution.
        library_less_conservative = s_lib > s_int
        rows.append({
            "port_diameter_m": d,
            "port_flow_m3s": Q,
            "g_prime_m_s2": gp,
            "depth_m": z,
            "l_M_m": lib["l_M_m"],
            "z_over_l_M": z / lib["l_M_m"] if math.isfinite(lib["l_M_m"]) else float("inf"),
            "dilution_library": s_lib,
            "dilution_library_jet": lib["dilution_library_jet"],
            "dilution_library_plume": lib["dilution_library_plume"],
            "dilution_integral": s_int,
            "dilution_integral_volume": integ["dilution_volume"],
            "ratio_library_over_integral": ratio,
            "library_less_conservative": library_less_conservative,
            "jet_dominated_library": lib["jet_dominated"],
            "dilution_visual_plumes": "",
            "ratio_library_over_vp": "",
        })
    return rows


def merge_visual_plumes(rows: list[dict]) -> list[dict]:
    """Attach Visual Plumes centreline dilution when output CSVs are present."""
    try:
        from benchmarks.visual_plumes.load_outputs import load_all_outputs
    except ImportError:
        from visual_plumes.load_outputs import load_all_outputs  # type: ignore

    vp = load_all_outputs(VP_OUTPUTS)
    if not vp:
        return rows
    for row in rows:
        key = (
            round(row["port_diameter_m"], 6),
            round(row["port_flow_m3s"], 6),
            round(row["g_prime_m_s2"], 6),
            round(row["depth_m"], 6),
        )
        if key in vp:
            s_vp = vp[key]
            row["dilution_visual_plumes"] = s_vp
            row["ratio_library_over_vp"] = (
                row["dilution_library"] / s_vp if s_vp else ""
            )
    return rows


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def write_ratio_plot(rows: list[dict], path: Path) -> None:
    """SVG scatter of library/integral ratio versus z/l_M (no matplotlib needed)."""
    xs, ys, flags = [], [], []
    for r in rows:
        x = r["z_over_l_M"]
        y = r["ratio_library_over_integral"]
        if not (math.isfinite(x) and math.isfinite(y) and x > 0 and y > 0):
            continue
        xs.append(x)
        ys.append(y)
        flags.append(r["library_less_conservative"])
    if not xs:
        return

    w, h = 720, 420
    pad_l, pad_r, pad_t, pad_b = 70, 30, 40, 60
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    # log-x friendly padding
    xmin = max(xmin * 0.8, 1e-3)
    xmax = xmax * 1.2
    ymin = min(ymin, 0.5)
    ymax = max(ymax, 1.5)

    def xpix(x: float) -> float:
        lx0, lx1 = math.log10(xmin), math.log10(xmax)
        return pad_l + (math.log10(x) - lx0) / (lx1 - lx0) * (w - pad_l - pad_r)

    def ypix(y: float) -> float:
        return pad_t + (ymax - y) / (ymax - ymin) * (h - pad_t - pad_b)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}">',
        f'<rect width="{w}" height="{h}" fill="#fafaf8"/>',
        f'<text x="{w/2}" y="24" text-anchor="middle" font-family="Georgia, serif" '
        f'font-size="16">Library / integral dilution vs z/l_M</text>',
        f'<line x1="{pad_l}" y1="{h-pad_b}" x2="{w-pad_r}" y2="{h-pad_b}" stroke="#333"/>',
        f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{h-pad_b}" stroke="#333"/>',
        # y = 1 reference
        f'<line x1="{pad_l}" y1="{ypix(1.0)}" x2="{w-pad_r}" y2="{ypix(1.0)}" '
        f'stroke="#888" stroke-dasharray="4 4"/>',
        f'<text x="{w-pad_r}" y="{ypix(1.0)-4}" text-anchor="end" font-size="11" '
        f'fill="#555">ratio = 1</text>',
        f'<text x="{w/2}" y="{h-18}" text-anchor="middle" font-size="12" '
        f'font-family="system-ui,sans-serif">z / l_M (log)</text>',
        f'<text x="18" y="{h/2}" text-anchor="middle" font-size="12" '
        f'font-family="system-ui,sans-serif" transform="rotate(-90 18 {h/2})">'
        f'S_library / S_integral</text>',
    ]
    # tick labels
    for xt in np.geomspace(xmin, xmax, 5):
        parts.append(
            f'<text x="{xpix(xt)}" y="{h-pad_b+16}" text-anchor="middle" '
            f'font-size="10">{xt:.2g}</text>'
        )
    for yt in np.linspace(ymin, ymax, 5):
        parts.append(
            f'<text x="{pad_l-8}" y="{ypix(yt)+4}" text-anchor="end" '
            f'font-size="10">{yt:.2f}</text>'
        )
    for x, y, less_cons in zip(xs, ys, flags):
        color = "#b33" if less_cons else "#2a6"
        parts.append(
            f'<circle cx="{xpix(x)}" cy="{ypix(y)}" r="3.5" fill="{color}" '
            f'fill-opacity="0.75"/>'
        )
    parts.append(
        '<text x="80" y="50" font-size="11" fill="#2a6">green: library ≤ integral '
        '(library conservative or equal)</text>'
    )
    parts.append(
        '<text x="80" y="66" font-size="11" fill="#b33">red: library > integral '
        '(library less conservative)</text>'
    )
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def summarise(rows: list[dict]) -> dict:
    ratios = np.array([r["ratio_library_over_integral"] for r in rows], dtype=float)
    less = [r for r in rows if r["library_less_conservative"]]
    return {
        "n_cases": len(rows),
        "ratio_median": float(np.median(ratios)),
        "ratio_p10": float(np.percentile(ratios, 10)),
        "ratio_p90": float(np.percentile(ratios, 90)),
        "ratio_min": float(np.min(ratios)),
        "ratio_max": float(np.max(ratios)),
        "n_library_less_conservative": len(less),
        "frac_library_less_conservative": len(less) / len(rows),
    }


def main() -> None:
    rows = run_sweep()
    rows = merge_visual_plumes(rows)
    RESULTS.mkdir(parents=True, exist_ok=True)
    csv_path = RESULTS / "near_field_comparison.csv"
    svg_path = RESULTS / "near_field_ratio_vs_z_lM.svg"
    write_csv(rows, csv_path)
    write_ratio_plot(rows, svg_path)
    stats = summarise(rows)
    print("Wrote", csv_path)
    print("Wrote", svg_path)
    print("Cases:", stats["n_cases"])
    print(
        "ratio S_library/S_integral: "
        f"median={stats['ratio_median']:.3f} "
        f"p10={stats['ratio_p10']:.3f} p90={stats['ratio_p90']:.3f} "
        f"min={stats['ratio_min']:.3f} max={stats['ratio_max']:.3f}"
    )
    print(
        "Library less conservative than integral: "
        f"{stats['n_library_less_conservative']}/{stats['n_cases']} "
        f"({100*stats['frac_library_less_conservative']:.1f}%)"
    )
    if stats["n_library_less_conservative"]:
        # Show a few worst (highest ratio) non-conservative cases
        worst = sorted(rows, key=lambda r: -r["ratio_library_over_integral"])[:5]
        print("Highest library/integral ratios:")
        for r in worst:
            print(
                f"  d={r['port_diameter_m']} Q={r['port_flow_m3s']} "
                f"g'={r['g_prime_m_s2']} z={r['depth_m']} "
                f"z/l_M={r['z_over_l_M']:.3g} ratio={r['ratio_library_over_integral']:.3f} "
                f"S_lib={r['dilution_library']:.2f} S_int={r['dilution_integral']:.2f}"
            )


if __name__ == "__main__":
    main()
