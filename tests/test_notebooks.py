"""Headless execution of the three mentee notebooks (CPU, synthetic data).

Marked slow: run with `pytest -q -m slow`. Order is thermal → monitoring →
aquaculture so schema-validated handoffs can chain.
"""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

import pytest

pytest.importorskip("nbclient")
pytest.importorskip("nbformat")

from nbclient import NotebookClient
import nbformat

from aquatic_guardian import handoff

ROOT = Path(__file__).resolve().parents[1]
NB_DIR = ROOT / "notebooks"
HANDOFF_DIR = NB_DIR / "_handoffs"

NOTEBOOKS = [
    "Aquatic_Guardian_Mentee2_Thermal_Tidal.ipynb",
    "Aquatic_Guardian_Mentee1_Monitoring.ipynb",
    "Aquatic_Guardian_Mentee2_Aquaculture_CV.ipynb",
]
HANDOFF_FILES = [
    "thermal_handoff.json",
    "monitoring_handoff.json",
    "aquaculture_handoff.json",
]

TIMEOUT_S = 15 * 60


def _ensure_venv_kernelspec() -> str:
    """Point a kernelspec at this interpreter so nbclient matches pytest."""
    from jupyter_client.kernelspec import KernelSpecManager

    ksm = KernelSpecManager()
    dest = Path(ksm.user_kernel_dir) / "ag-pytest"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "kernel.json").write_text(json.dumps({
        "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
        "display_name": "Python 3 (ag pytest)",
        "language": "python",
    }, indent=2))
    return "ag-pytest"


@pytest.mark.slow
def test_notebooks_execute_and_write_validated_handoffs():
    HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLBACKEND", "Agg")
    kernel = _ensure_venv_kernelspec()

    for name in NOTEBOOKS:
        path = NB_DIR / name
        assert path.is_file(), path
        nb = nbformat.read(path, as_version=4)
        client = NotebookClient(
            nb,
            timeout=TIMEOUT_S,
            kernel_name=kernel,
            resources={"metadata": {"path": str(NB_DIR)}},
        )
        client.execute()

    for fname in HANDOFF_FILES:
        p = HANDOFF_DIR / fname
        assert p.is_file(), f"missing handoff {p}"
        rec = handoff.read(p)
        assert rec["handoff_version"] == "0.1.0"
        assert rec["placeholders"] is not None

    aqua = handoff.read(HANDOFF_DIR / "aquaculture_handoff.json")
    assert "recommended_loop_inlet_ceiling_c" in aqua
    assert aqua["binding_constraint"] in {"do", "ammonia", "welfare", "growth"}
    thermal = handoff.read(HANDOFF_DIR / "thermal_handoff.json")
    assert thermal["producer"] == "thermal_tidal"
    assert "loop_inlet_temperature_c" in thermal
