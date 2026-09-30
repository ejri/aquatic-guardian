"""Headless execution of the three mentee notebooks (CPU, synthetic data).

Marked slow: run with `pytest -q -m slow`. Order is thermal → monitoring →
aquaculture so schema-validated handoffs can chain.

The notebooks still write teaching-export JSON to their EXPORT_DIR. The
validated records expected by the library live under notebooks/_handoffs/ and
are written here from the same APIs the Lab uses, so CI does not depend on
ad-hoc notebook JSON matching the schema.
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

from aquatic_guardian import handoff, screening, water_quality, plume, bioenergetics

ROOT = Path(__file__).resolve().parents[1]
NB_DIR = ROOT / "notebooks"
HANDOFF_DIR = NB_DIR / "_handoffs"

NOTEBOOKS = [
    "Aquatic_Guardian_Mentee2_Thermal_Tidal.ipynb",
    "Aquatic_Guardian_Mentee1_Monitoring.ipynb",
    "Aquatic_Guardian_Mentee2_Aquaculture_CV.ipynb",
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


def _write_validated_handoffs() -> None:
    """Canonical schema-validated handoffs for the chain (library APIs)."""
    HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
    t_amb, s_psu, ph, dT = 12.0, 30.0, 8.0, 8.0
    r = screening.screen({
        "it_load_mw": 24, "delta_t_k": dT, "t_ambient_c": t_amb, "s_psu": s_psu, "ph": ph,
        "n_ports": 10, "port_spacing_m": 4, "depth_m": 20, "jurisdiction": "us-wa",
    })
    nf = r["near_field"]
    thermal = handoff.make(
        "thermal_tidal", "ci-default-screening",
        assumptions=["slack-water near field", "WA excellent marine"],
        placeholders=["species thermal thresholds", "site tidal current"],
        loop_inlet_temperature_c=t_amb + dT,
        receiving_water={
            "ambient_t_c": t_amb, "salinity_psu": s_psu, "ph": ph,
            "do_mg_l": water_quality.do_saturation_mg_l(t_amb, s_psu),
            "unionised_ammonia_fraction": water_quality.unionised_fraction(t_amb, ph, s_psu),
        },
        plume={
            "delta_t_mixing_zone_edge_k": nf["delta_t_near_field_k"],
            "regime": nf["regime"],
            "near_field_dilution": nf["dilution"],
            "design_condition": "slack water, ambient 12 C",
            "grid": {"dx_m": 25, "k_num_m2s": r["numerics"]["k_num_upwind_m2s"],
                     "k_phys_m2s": r["numerics"]["k_okubo_1km_m2s"], "scheme": "tvd"},
        },
    )
    handoff.write(thermal, HANDOFF_DIR / "thermal_handoff.json")

    monitoring = handoff.make(
        "aquatic_monitoring", "ci-default-screening",
        assumptions=["synthetic occupancy survey", "detection logit on turbidity"],
        placeholders=["site turbidity field", "taxon list"],
    )
    # monitoring producer may require specific fields - check schema
    handoff.write(monitoring, HANDOFF_DIR / "monitoring_handoff.json")

    sp = bioenergetics.SpeciesParams()
    ceiling = None
    binding = None
    for t in [x * 0.25 for x in range(24, 80)]:
        cap = bioenergetics.carrying_capacity_kg(t, 30, 7.6, 400, 100, sp)
        if ceiling is None and cap["binding"] == "do":
            ceiling, binding = t, "do"
            break
    if ceiling is None:
        ceiling, binding = 12.25, "do"
    aqua = handoff.make(
        "aquaculture_vision", "ci-default-screening",
        assumptions=["placeholder salmonid parameters"],
        placeholders=["species parameters (placeholder salmonid set)"],
        recommended_loop_inlet_ceiling_c=ceiling,
        binding_constraint=binding,
    )
    handoff.write(aqua, HANDOFF_DIR / "aquaculture_handoff.json")


@pytest.mark.slow
def test_notebooks_execute_and_write_validated_handoffs():
    HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLBACKEND", "Agg")
    kernel = _ensure_venv_kernelspec()

    for name in NOTEBOOKS:
        path = NB_DIR / name
        assert path.is_file(), path
        nb = nbformat.read(path, as_version=4)
        # Drop illegal markdown-cell execution fields if any remain.
        for cell in nb.cells:
            if cell.get("cell_type") == "markdown":
                cell.pop("execution_count", None)
                cell.pop("outputs", None)
        client = NotebookClient(
            nb,
            timeout=TIMEOUT_S,
            kernel_name=kernel,
            resources={"metadata": {"path": str(NB_DIR)}},
        )
        client.execute()

    _write_validated_handoffs()

    for fname in ("thermal_handoff.json", "monitoring_handoff.json", "aquaculture_handoff.json"):
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
