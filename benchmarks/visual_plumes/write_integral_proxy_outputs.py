#!/usr/bin/env python3
"""Write integral-model centreline dilutions as Visual Plumes *proxy* CSVs.

EPA Visual Plumes is Windows-only and is not available in this environment.
These files exercise the load/merge path and give a literature-consistent
independent estimate (Morton–Taylor–Turner integral, same as
``benchmarks/integral_jet.py``). They are **not** UM3 outputs.

Provenance is recorded in ``outputs/PROVENANCE.json``. Real Visual Plumes
files must replace these before P-3 can leave "Needs benchmark".
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from benchmarks.integral_jet import integrate_round_jet  # noqa: E402
from benchmarks.visual_plumes.write_um3_decks import (  # noqa: E402
    case_id,
)

OUT = Path(__file__).resolve().parent / "outputs"

# Representative subset (not the full 320-case sweep): corners + mid-range.
SUBSET = [
    (0.1, 0.02, 0.005, 4.0),
    (0.1, 0.05, 0.015, 10.0),
    (0.3, 0.05, 0.015, 25.0),
    (0.3, 0.15, 0.025, 25.0),
    (0.6, 0.15, 0.025, 50.0),
    (0.6, 0.4, 0.04, 50.0),
    (1.0, 0.4, 0.04, 80.0),
    (1.0, 0.02, 0.005, 10.0),
]


def write_case(d: float, Q: float, gp: float, z: float) -> Path:
    cid = case_id(d, Q, gp, z)
    res = integrate_round_jet(d, Q, gp, z, n_points=max(80, int(z * 10)))
    zs = list(res.z_m)
    ss = list(res.dilution_centreline)
    path = OUT / f"{cid}.csv"
    lines = ["z_m,dilution_centreline"]
    step = max(1, len(zs) // 40)
    idxs = sorted(set(list(range(0, len(zs), step)) + [len(zs) - 1]))
    for i in idxs:
        lines.append(f"{zs[i]:.6g},{ss[i]:.6g}")
    path.write_text("\n".join(lines) + "\n")
    return path


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    written = []
    for d, Q, gp, z in SUBSET:
        # Skip physically absurd shallow/strong jet edge cases if needed.
        if z < 2.0 * d:
            continue
        p = write_case(d, Q, gp, z)
        written.append(p.name)
    meta = {
        "source": "integral_mtt_proxy",
        "not_visual_plumes": True,
        "model": "benchmarks/integral_jet.py (Morton–Taylor–Turner, α_j=0.057, α_p=0.083)",
        "literature": [
            "Morton, Taylor & Turner (1956)",
            "Fischer et al. (1979) mixing asymptotes (library C_POINT=0.089)",
            "Lee & Chu (2003) entrainment coefficients",
        ],
        "note": (
            "These CSVs are independent integral estimates used because EPA "
            "Visual Plumes (Windows) could not be run here. Replace with true "
            "UM3 exports before treating P-3 as closed."
        ),
        "files": written,
    }
    (OUT / "PROVENANCE.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(f"wrote {len(written)} proxy CSVs + PROVENANCE.json under {OUT}")


if __name__ == "__main__":
    main()
