"""Run the Python LCV near-field on every P-3 case and write a results CSV.

    python benchmarks/plumes2/run_python_lcv.py

Writes ``results_python_lcv.csv`` (same columns as ``results_template.csv``).
This is **not** EPA PLUMES 2.0 output and must not close verification item P-3.
"""
from __future__ import annotations

import csv
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

from python_lcv import simulate_from_case_row  # noqa: E402

OUT = HERE / "results_python_lcv.csv"
FIELDS = [
    "case_id", "plumes2_version", "run_date", "flux_avg_dilution",
    "centerline_dilution", "plume_diameter_m", "centerline_depth_at_termination_m",
    "termination", "merged", "notes",
]


def main() -> int:
    cases = list(csv.DictReader((HERE / "cases.csv").open()))
    rows = []
    today = date.today().isoformat()
    print(f"Running Python LCV on {len(cases)} cases (NOT EPA PLUMES 2.0)…")
    for c in cases:
        r = simulate_from_case_row(c)
        print(
            f"  {r.case_id:>3}  S_cl={r.centerline_dilution:8.2f}  "
            f"S_flux={r.flux_avg_dilution:8.2f}  diam={r.plume_diameter_m:6.2f} m  "
            f"{r.termination:<12} merged={r.merged or '-'}"
        )
        rows.append({
            "case_id": r.case_id,
            "plumes2_version": "python-lcv-lee-chu-not-epa",
            "run_date": today,
            "flux_avg_dilution": r.flux_avg_dilution,
            "centerline_dilution": r.centerline_dilution,
            "plume_diameter_m": r.plume_diameter_m,
            "centerline_depth_at_termination_m": r.centerline_depth_at_termination_m,
            "termination": r.termination,
            "merged": r.merged,
            "notes": r.notes,
        })
    with OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"\nWrote {OUT.relative_to(ROOT)}")
    print("Compare library vs this proxy with: python benchmarks/plumes2/compare.py benchmarks/plumes2/results_python_lcv.csv")
    print("P-3 stays open until real PLUMES 2.0 (Windows) results.csv is supplied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
