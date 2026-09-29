"""Load Visual Plumes CSV outputs into the near-field comparison.

Expected file layout
--------------------
benchmarks/visual_plumes/outputs/<case_id>.csv

case_id matches ``write_um3_decks.case_id``, e.g. ``d0p3_Q0p05_gp0p015_z25.csv``.

CSV format (header required)::

    z_m,dilution_centreline
    0.0,1.0
    ...
    25.0,42.3

The loader takes the dilution at the depth encoded in the filename (surface /
case depth). If that z is missing, it linearly interpolates in z.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Optional


_CASE_RE = re.compile(
    r"^d(?P<d>[0-9p]+)_Q(?P<Q>[0-9p]+)_gp(?P<gp>[0-9p]+)_z(?P<z>[0-9p]+)$"
)


def _parse_num(token: str) -> float:
    return float(token.replace("p", "."))


def parse_case_id(stem: str) -> Optional[tuple[float, float, float, float]]:
    m = _CASE_RE.match(stem)
    if not m:
        return None
    return (
        _parse_num(m.group("d")),
        _parse_num(m.group("Q")),
        _parse_num(m.group("gp")),
        _parse_num(m.group("z")),
    )


def dilution_at_depth(csv_path: Path, depth_m: float) -> float:
    zs, ss = [], []
    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or "z_m" not in reader.fieldnames:
            raise ValueError(f"{csv_path}: need columns z_m,dilution_centreline")
        dil_key = "dilution_centreline"
        if dil_key not in reader.fieldnames:
            raise ValueError(f"{csv_path}: missing dilution_centreline column")
        for row in reader:
            zs.append(float(row["z_m"]))
            ss.append(float(row[dil_key]))
    if not zs:
        raise ValueError(f"{csv_path}: empty")
    # Exact match
    for z, s in zip(zs, ss):
        if abs(z - depth_m) <= 1e-6 * max(1.0, depth_m):
            return s
    # Linear interpolate / clamp
    pairs = sorted(zip(zs, ss), key=lambda p: p[0])
    if depth_m <= pairs[0][0]:
        return pairs[0][1]
    if depth_m >= pairs[-1][0]:
        return pairs[-1][1]
    for (z0, s0), (z1, s1) in zip(pairs, pairs[1:]):
        if z0 <= depth_m <= z1:
            t = (depth_m - z0) / (z1 - z0) if z1 != z0 else 0.0
            return s0 + t * (s1 - s0)
    return pairs[-1][1]


def load_all_outputs(outputs_dir: Path) -> dict[tuple[float, float, float, float], float]:
    """Return map (d, Q, g', z) -> centreline dilution at z."""
    out: dict[tuple[float, float, float, float], float] = {}
    if not outputs_dir.is_dir():
        return out
    for path in sorted(outputs_dir.glob("*.csv")):
        key = parse_case_id(path.stem)
        if key is None:
            continue
        _d, _Q, _gp, z = key
        out[key] = dilution_at_depth(path, z)
    return out
