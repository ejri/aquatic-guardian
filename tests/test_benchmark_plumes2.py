"""The PLUMES 2.0 benchmark kit stays in sync with the library and handles its inputs."""
import csv, subprocess, sys
from pathlib import Path
import pytest

B = Path(__file__).resolve().parents[1] / "benchmarks" / "plumes2"
sys.path.insert(0, str(B))
import make_cases, compare  # noqa: E402


def test_cases_csv_matches_current_library():
    on_disk = list(csv.DictReader((B / "cases.csv").open()))
    fresh = make_cases.rows()
    assert [r["case_id"] for r in on_disk] == [r["case_id"] for r in fresh]
    for a, b in zip(on_disk, fresh):
        assert float(a["library_min_dilution_at_surface"]) == pytest.approx(b["library_min_dilution_at_surface"], abs=0.01)


def test_compare_reports_verdicts_on_synthetic_results(tmp_path):
    cases = {r["case_id"]: r for r in csv.DictReader((B / "cases.csv").open())}
    p = tmp_path / "results.csv"
    with p.open("w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["case_id", "centerline_dilution", "centerline_depth_at_termination_m", "merged"])
        w.writerow(["A1", float(cases["A1"]["library_min_dilution_at_surface"]) * 1.4, 0, ""])
        w.writerow(["B1", float(cases["B1"]["library_min_dilution_at_surface"]) * 0.8, 0, "yes"])
        w.writerow(["C1", float(cases["A1"]["library_min_dilution_at_surface"]) * 1.9, 0, ""])
    rows = {r["case_id"]: r for r in compare.compare(p)}
    assert rows["A1"]["conservative"] and rows["A1"]["useful"]
    assert not rows["B1"]["conservative"] and rows["B1"]["merging_consistent"]
    assert rows["C1"]["dilution_grows_with_current"]


def test_compare_without_results_exits_cleanly(tmp_path):
    r = subprocess.run([sys.executable, str(B / "compare.py"), str(tmp_path / "none.csv")], capture_output=True, text=True)
    assert r.returncode == 0 and "No results yet" in r.stdout
