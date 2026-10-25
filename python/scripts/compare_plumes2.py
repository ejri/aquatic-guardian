"""Compare plumes2py with PLUMES2.0 runs, and refit the forced-entrainment scale.

Each case is a folder holding the CSVs PLUMES2.0 saves (Diffuser_*.csv,
Effluent_*.csv, Ambient_*.csv, Mixing_zone_*.csv) and its text output
(ModelResults_TxtOutputs.dat or any *.dat/*.txt in the PLUMES2.0 layout).

    python scripts/compare_plumes2.py benchmarks/plumes2/case*          # report
    python scripts/compare_plumes2.py benchmarks/plumes2/case* --fit    # refit 0.81
    python scripts/compare_plumes2.py plumes2py/data                    # EPA example

Pass criteria follow the benchmark kit: terminal flux-averaged dilution,
plume diameter and rise within 5 %, the same termination type, and far-field
dilution at the chronic boundary within 5 %.
"""
from __future__ import annotations

import argparse
import copy
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from plumes2py import load_plumes2_csvs, run  # noqa: E402

STEP = re.compile(r"^\s+(\d+)\s+([\d.]+)\s+([\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-[\d.]+)\s*$")
FAR = re.compile(r"^\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*$")


def parse_output(path: Path) -> dict:
    near, far, events, far_on, last_event = [], [], [], False, None
    for line in path.read_text(errors="replace").splitlines():
        if "Starting Farfield" in line:
            far_on = True
            continue
        m = STEP.match(line)
        if m and not far_on:
            near.append([int(m.group(1))] + [float(x) for x in m.group(2, 3, 4, 5, 6)])
            if last_event:
                events.append((last_event, near[-1][0]))
                last_event = None
            continue
        if far_on:
            f = FAR.match(line)
            if f:
                far.append([float(x) for x in f.groups()])
        elif line.strip().startswith("-") and any(k in line for k in ("traps", "surfaces", "merging", "Bottom", "bottom", "rise", "fall")):
            last_event = line.strip("- \n")
    term = "surface" if any("surface" in e[0] for e in events) else ("bottom" if any("ottom" in e[0] for e in events) else "other")
    return {"near": near, "far": far, "events": events, "termination": term}


def find_output(folder: Path) -> Path:
    for pat in ("ModelResults*.dat", "*.dat", "*.txt"):
        hits = sorted(folder.glob(pat))
        if hits:
            return hits[0]
    raise FileNotFoundError(f"no PLUMES2.0 output in {folder}")


def compare(folder: Path, flow_units: str, forced_scale: float | None = None) -> dict:
    sc = load_plumes2_csvs(folder, flow_units=flow_units)
    if forced_scale is not None:
        sc.settings.forced_scale = forced_scale
    ref = parse_output(find_output(folder))
    res = run(sc, isolated_check=False)
    e = res["nearfield"]["end"]
    r = ref["near"][-1]
    rise_ref = sc.diffuser.port_depth - abs(r[5])
    rise = sc.diffuser.port_depth - e["depth"]
    out = {"case": folder.name, "termination_ref": ref["termination"], "termination": res["nearfield"]["termination"],
           "dilution_ref": r[1], "dilution": e["dilution"], "diameter_ref": r[2], "diameter": e["diameter"],
           "rise_ref": rise_ref, "rise": rise}
    chronic = sc.mixing_zone.chronic
    if ref["far"] and chronic and res.get("farfield"):
        fr = min(ref["far"], key=lambda q: abs(q[2] - chronic))
        mine = min(res["farfield"]["rows"], key=lambda q: abs(q["distance"] - fr[2]))
        out.update(far_distance=fr[2], far_ref=fr[0], far=mine["dilution"])
    def rel(a, b):
        return abs(a / b - 1) if b else float("inf")
    out["pass"] = (rel(out["dilution"], out["dilution_ref"]) <= 0.05 and rel(out["diameter"], out["diameter_ref"]) <= 0.05
                   and rel(out["rise"], out["rise_ref"]) <= 0.05 and out["termination"] == out["termination_ref"]
                   and ("far" not in out or rel(out["far"], out["far_ref"]) <= 0.05))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folders", nargs="+", type=Path)
    ap.add_argument("--flow-units", default="MGD")
    ap.add_argument("--fit", action="store_true", help="grid-search forced_scale over all cases")
    a = ap.parse_args()
    rows = [compare(f, a.flow_units) for f in a.folders]
    print(f"{'case':24s} {'term ref/ours':16s} {'dil ref':>9s} {'ours':>9s} {'err%':>6s} {'diam err%':>9s} {'rise err%':>9s} {'far err%':>8s} pass")
    for r in rows:
        pe = lambda k: 100 * (r[k] / r[k + '_ref'] - 1) if r.get(k + "_ref") else float("nan")  # noqa: E731
        print(f"{r['case'][:24]:24s} {r['termination_ref'][:7]+'/'+r['termination'][:7]:16s} {r['dilution_ref']:9.2f} {r['dilution']:9.2f} "
              f"{pe('dilution'):6.2f} {pe('diameter'):9.2f} {pe('rise'):9.2f} {pe('far') if 'far' in r else float('nan'):8.2f} {'yes' if r['pass'] else 'NO'}")
    print(f"{sum(r['pass'] for r in rows)} of {len(rows)} cases pass")
    if a.fit:
        best = None
        for k in [x / 100 for x in range(60, 111, 1)]:
            cs = [compare(f, a.flow_units, k) for f in a.folders]
            errs = [math.log(c["dilution"] / c["dilution_ref"]) for c in cs]
            rms = math.sqrt(sum(e * e for e in errs) / len(errs))
            if best is None or rms < best[0]:
                best = (rms, k)
        print(f"best forced_scale {best[1]:.2f} (RMS log error in terminal dilution {100 * best[0]:.2f} %); "
              "update Settings.forced_scale and site/js/plumes2.js defaults together, then rerun the parity fixtures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
