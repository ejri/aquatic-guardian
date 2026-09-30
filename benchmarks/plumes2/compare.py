"""Compare PLUMES 2.0 (UM3) results with the library's near-field screening (register item P-3).

    python benchmarks/plumes2/compare.py [results.csv]

Reads cases.csv and a filled copy of results_template.csv (default: results.csv),
evaluates the library at the same rise height UM3 reached, and reports per case:
  conservative  library dilution <= UM3 centreline dilution (screening does not understate the rise)
  useful        UM3 centreline <= 2 x library (screening is not so pessimistic it is useless)
plus whether dilution grows with current (C cases) and whether merging matches the regime.
Writes comparison.csv beside this script.
"""
from __future__ import annotations
import csv, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from make_cases import library_min_dilution  # noqa: E402

BASE = {"C1": "A1", "C2": "A1", "C3": "B1", "C4": "B1"}


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def compare(results_path: Path) -> list[dict]:
    cases = {r["case_id"]: r for r in csv.DictReader((HERE / "cases.csv").open())}
    res = {r["case_id"]: r for r in csv.DictReader(results_path.open()) if num(r.get("centerline_dilution"))}
    out = []
    for cid, r in res.items():
        c = cases[cid]
        n, d = int(c["number_of_ports"]), float(c["port_diameter_m"])
        s = float(c["port_spacing_m"] or 0)
        depth, port_depth = float(c["water_depth_m"]), float(c["port_depth_m"])
        cl_depth = num(r.get("centerline_depth_at_termination_m"))
        rise = port_depth - (cl_depth if cl_depth is not None else 0.0)
        lib, reg = library_min_dilution(n, d, s, float(c["total_effluent_flow_m3s"]),
                                        float(c["effluent_temperature_c"]) - float(c["ambient_temperature_c"]), depth, max(rise, 0.1))
        um3 = num(r["centerline_dilution"])
        ratio = um3 / lib
        row = {"case_id": cid, "regime": reg, "rise_m": round(rise, 2), "library_min_dilution": round(lib, 2),
               "um3_centerline_dilution": um3, "um3_flux_avg_dilution": num(r.get("flux_avg_dilution")),
               "ratio_um3_over_library": round(ratio, 3), "conservative": ratio >= 1.0, "useful": ratio <= 2.0,
               "merged_reported": (r.get("merged") or "").strip().lower(), "termination": r.get("termination", "")}
        if cid in BASE and BASE[cid] in res:
            row["dilution_grows_with_current"] = um3 >= num(res[BASE[cid]]["centerline_dilution"])
        if n > 1 and row["merged_reported"] in ("yes", "no"):
            row["merging_consistent"] = (row["merged_reported"] == "yes") == (reg != "point")
        out.append(row)
    return out


def main(argv):
    path = Path(argv[1]) if len(argv) > 1 else HERE / "results.csv"
    if not path.exists():
        print(f"No results yet. Copy results_template.csv to {path.name}, fill it from PLUMES 2.0, and rerun.")
        return 0
    rows = compare(path)
    if not rows:
        print("Results file has no centerline_dilution values yet.")
        return 0
    keys = sorted({k for r in rows for k in r}, key=lambda k: list(rows[0]).index(k) if k in rows[0] else 99)
    with (HERE / "comparison.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(rows)
    for r in rows:
        flags = [] if r["conservative"] else ["NOT CONSERVATIVE"]
        if not r["useful"]:
            flags.append("too pessimistic")
        if r.get("dilution_grows_with_current") is False:
            flags.append("dilution fell with current")
        if r.get("merging_consistent") is False:
            flags.append("merging disagrees with regime")
        print(f"{r['case_id']:>3} {r['regime']:<12} UM3/library = {r['ratio_um3_over_library']:.2f}  {'; '.join(flags) or 'ok'}")
    bad = [r["case_id"] for r in rows if not r["conservative"]]
    print(f"\n{len(rows)} cases compared. Not conservative: {', '.join(bad) or 'none'}. "
          f"Too pessimistic: {', '.join(r['case_id'] for r in rows if not r['useful']) or 'none'}.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
