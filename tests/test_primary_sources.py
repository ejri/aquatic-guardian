"""Primary-source checks for register items W-4 and R-2.

W-4: Bower & Bidwell (1978) seawater un-ionised ammonia table
     (J. Fish. Res. Board Can. 35: 1012–1016). Rows marked TRANSCRIBE are
     skipped until a human pastes printed percent values with page numbers.

R-2: California Thermal Plan, coastal waters, new discharges — exact text in
     data/checks/ca_thermal_plan.md (SWRCB Thermal Plan PDF).
"""
from __future__ import annotations
import csv
import re
from pathlib import Path

import pytest

from aquatic_guardian import criteria, water_quality

ROOT = Path(__file__).resolve().parents[1]
BOWER = ROOT / "data" / "checks" / "bower_bidwell_1978.csv"
CA_PLAN = ROOT / "data" / "checks" / "ca_thermal_plan.md"

# Table prints percent NH3 typically to two or three significant figures
# (e.g. 1.44, 2.98, 4.28). Absolute 0.05 percentage points covers half a
# unit in the second decimal with a small guard; relative 2% covers larger
# cells such as 12.40%. Absolute OR relative must hold.
BOWER_ABS_PCT = 0.05
BOWER_REL = 0.02


def _bower_rows():
    with BOWER.open(newline="") as f:
        return list(csv.DictReader(f))


def test_bower_bidwell_csv_has_required_columns():
    rows = _bower_rows()
    assert rows, "bower_bidwell_1978.csv must have at least one data row"
    assert set(rows[0]) >= {
        "temperature_c", "ph", "salinity_psu", "unionised_percent", "source_page"
    }


def test_unionised_fraction_vs_bower_bidwell():
    """Compare library seawater fractions to transcribed table percents.

    Skip while any compared cell still says TRANSCRIBE (Phase 4 transcription
    gate). Tolerance justified by typical two-decimal printed percentages.
    """
    rows = _bower_rows()
    pending = [r for r in rows if str(r["unionised_percent"]).strip().upper() == "TRANSCRIBE"]
    if pending:
        pytest.skip(
            f"{len(pending)} Bower & Bidwell row(s) still marked TRANSCRIBE; "
            "paste printed percent NH3 and source_page from J. Fish. Res. Board "
            "Can. 35: 1012–1016 before this check can run."
        )
    for r in rows:
        t = float(r["temperature_c"])
        ph = float(r["ph"])
        s = float(r["salinity_psu"])
        pct = float(r["unionised_percent"])
        got = 100.0 * water_quality.unionised_fraction(t, ph, s)
        assert got == pytest.approx(pct, abs=BOWER_ABS_PCT) or got == pytest.approx(
            pct, rel=BOWER_REL
        ), (
            f"T={t} pH={ph} S={s}: library {got:.4f}% vs table {pct}% "
            f"(page {r['source_page']})"
        )


def test_ca_thermal_plan_text_matches_criteria():
    """Parse °F and distance from the transcribed Plan text; match library K."""
    text = CA_PLAN.read_text()
    assert "20°F" in text or "20° F" in text or "more than 20" in text
    assert "4°F" in text or "4° F" in text
    assert re.search(r"1[, ]?000\s+feet", text, re.I)

    # Plan uses "more than 20°F" (discharge) and "exceeding 4°F" (receiving water).
    f_vals = [float(x) for x in re.findall(
        r"(?:more than|exceeding)\s+(\d+(?:\.\d+)?)°F", text)]
    assert 20.0 in f_vals, f"expected 20°F discharge limit in Plan text; found {f_vals}"
    assert 4.0 in f_vals, f"expected 4°F receiving-water rise in Plan text; found {f_vals}"

    dist = re.search(r"beyond\s+(1[, ]?000)\s+feet", text, re.I)
    assert dist, "expected 'beyond 1,000 feet' in Plan text"
    feet = int(dist.group(1).replace(",", "").replace(" ", ""))
    assert feet == 1000

    r = criteria.ca_thermal_plan_new_coastal()
    f_to_k = 5.0 / 9.0
    assert r["allowed_increment_k"] == pytest.approx(4.0 * f_to_k, abs=1e-6)
    assert r["max_discharge_delta_k"] == pytest.approx(20.0 * f_to_k, abs=1e-6)
