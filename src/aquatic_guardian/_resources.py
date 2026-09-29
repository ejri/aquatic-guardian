"""Locate bundled schemas and data whether installed from a wheel or run from a checkout.

Canonical copies live in the repository's top-level schemas/ and data/ folders.
app/build.py mirrors them into src/aquatic_guardian/resources/ and CI fails if
the copies differ.
"""
from __future__ import annotations
from pathlib import Path

_PKG = Path(__file__).resolve().parent / "resources"
_REPO = Path(__file__).resolve().parents[2]


def path(kind: str, name: str) -> Path:
    for base in (_PKG / kind, _REPO / kind):
        p = base / name
        if p.exists():
            return p
    raise FileNotFoundError(f"{kind}/{name} not found in package resources or repository")
