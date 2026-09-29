"""data/instruments.json must validate, and the review report must find what it claims to.

The tracker is the part of this repository most likely to go quietly wrong: statuses
and dates age, and an entry with no source cannot be checked by anyone. The schema
enforces the shape, and these tests exercise the report that tells a person what to
look at.
"""
from __future__ import annotations
import copy, json, subprocess, sys
from datetime import date
from pathlib import Path
import pytest

jsonschema = pytest.importorskip("jsonschema")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import tracker_report                                  # noqa: E402

DATA = json.loads((ROOT / "data" / "instruments.json").read_text())
SCHEMA = json.loads((ROOT / "schemas" / "instruments.schema.json").read_text())


@pytest.fixture
def validator():
    return jsonschema.Draft202012Validator(SCHEMA)


def test_the_schema_is_itself_valid(validator):
    jsonschema.Draft202012Validator.check_schema(SCHEMA)
    assert SCHEMA["$id"].endswith("instruments.schema.json")


def test_instruments_json_validates(validator):
    errors = sorted(validator.iter_errors(DATA), key=lambda e: list(e.absolute_path))
    assert errors == [], "\n".join(f"{list(e.absolute_path)}: {e.message}" for e in errors)


def test_the_schema_is_mirrored_into_the_package():
    mirrored = ROOT / "src" / "aquatic_guardian" / "resources" / "schemas" / "instruments.schema.json"
    assert mirrored.exists(), "run python app/build.py"
    assert mirrored.read_bytes() == (ROOT / "schemas" / "instruments.schema.json").read_bytes()


def test_the_schema_rejects_an_invented_source(validator):
    bad = copy.deepcopy(DATA)
    bad["instruments"][0]["sources"] = [{"url": "example.gov/bill", "title": "A bill",
                                         "accessed": "2026-09-29"}]
    assert list(validator.iter_errors(bad)), "a source url must be an absolute http(s) URL"


def test_the_schema_rejects_an_unsourced_entry_claiming_to_be_verified(validator):
    bad = copy.deepcopy(DATA)
    bad["instruments"][0]["sources"] = []
    bad["instruments"][0]["verify"] = False
    bad["instruments"][0].pop("verify_note", None)
    assert list(validator.iter_errors(bad))


def test_the_schema_requires_a_reason_when_a_sourced_entry_is_still_unverified(validator):
    """An empty sources array is a reason on its own. A sourced entry needs a note."""
    ok = copy.deepcopy(DATA)
    ok["instruments"][0]["sources"] = []
    ok["instruments"][0]["verify"] = True
    ok["instruments"][0].pop("verify_note", None)
    assert list(validator.iter_errors(ok)) == []

    bad = copy.deepcopy(ok)
    bad["instruments"][0]["sources"] = [
        {"url": "https://www.waterboards.ca.gov/water_issues/programs/ocean/docs/wqplans/thermpln.pdf",
         "title": "California Thermal Plan", "accessed": "2026-09-29", "primary": True}]
    assert list(validator.iter_errors(bad))


def test_the_schema_rejects_an_unknown_stage(validator):
    bad = copy.deepcopy(DATA)
    bad["instruments"][0]["stage"] = "probably happening"
    assert list(validator.iter_errors(bad))


def test_every_entry_names_a_model_language_file_that_exists():
    for e in DATA["instruments"]:
        assert (ROOT / e["doc"]).exists(), (e["id"], e["doc"])


def test_last_checked_is_never_later_than_the_tracker_date():
    as_of = tracker_report.parse(DATA["as_of"])
    for e in DATA["instruments"]:
        assert tracker_report.parse(e["last_checked"]) <= as_of, e["id"]


def test_instrument_ids_are_unique():
    ids = [e["id"] for e in DATA["instruments"]]
    assert len(ids) == len(set(ids))


# -------------------------------------------------------------------- the report

def test_the_report_finds_a_stale_entry():
    as_of = tracker_report.parse(DATA["as_of"])
    limit = DATA["stale_after_days"]
    fresh = tracker_report.findings(DATA, as_of)
    assert fresh["stale"] == []
    later = date.fromordinal(as_of.toordinal() + limit + 1)
    aged = tracker_report.findings(DATA, later)
    assert {s["id"] for s in aged["stale"]} == {e["id"] for e in DATA["instruments"]}
    assert all(s["days"] == limit + 1 for s in aged["stale"])


def test_the_report_lists_every_entry_marked_verify_with_a_reason():
    f = tracker_report.findings(DATA, tracker_report.parse(DATA["as_of"]))
    assert {u["id"] for u in f["unverified"]} == {e["id"] for e in DATA["instruments"] if e["verify"]}
    assert all(u["note"] for u in f["unverified"]), "every verify entry must say what is in doubt"


def test_the_report_catches_a_past_date_still_described_as_future():
    data = copy.deepcopy(DATA)
    data["instruments"] = [{
        "id": "test-entry", "jurisdiction": "Nowhere", "name": "Test instrument",
        "type": "bill", "status": "Decision expected", "stage": "proposed",
        "dates": [{"date": "2026-01-15", "event": "Committee vote"}],
        "hook": "n/a", "action": "n/a", "last_checked": "2026-09-29", "sources": [],
        "doc": "policy/model-language/eu.md", "verify": True, "verify_note": "test"}]
    f = tracker_report.findings(data, tracker_report.parse("2026-09-29"))
    assert [p["id"] for p in f["past_dates_described_as_future"]] == ["test-entry"]
    assert f["past_dates_described_as_future"][0]["days"] > 200

    settled = copy.deepcopy(data)
    settled["instruments"][0]["status"] = "Voted down in committee"
    assert tracker_report.findings(settled, tracker_report.parse("2026-09-29"))[
        "past_dates_described_as_future"] == []


def test_the_report_reports_each_finding_once():
    """A status and a date event can both trip the future-wording check."""
    data = copy.deepcopy(DATA)
    data["instruments"] = [{
        "id": "dup", "jurisdiction": "Nowhere", "name": "Test", "type": "consultation",
        "status": "Open", "stage": "consultation",
        "dates": [{"date": "2026-01-15", "event": "Consultation closes"}],
        "hook": "n/a", "action": "n/a", "last_checked": "2026-09-29", "sources": [],
        "deadline": "2026-01-15",
        "doc": "policy/model-language/eu.md", "verify": True, "verify_note": "test"}]
    f = tracker_report.findings(data, tracker_report.parse("2026-09-29"))
    keys = [(p["id"], p["date"], p["event"]) for p in f["past_dates_described_as_future"]]
    assert len(keys) == len(set(keys))


def test_the_report_runs_as_a_script():
    for args in ([], ["--json"]):
        out = subprocess.run([sys.executable, str(ROOT / "scripts" / "tracker_report.py"),
                              "--today", DATA["as_of"], *args],
                             capture_output=True, text=True, check=True).stdout
        assert out.strip()
    text = subprocess.run([sys.executable, str(ROOT / "scripts" / "tracker_report.py"),
                           "--today", DATA["as_of"]],
                          capture_output=True, text=True, check=True).stdout
    for heading in ("Stale:", "Marked verify", "read as future"):
        assert heading in text
    payload = json.loads(subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "tracker_report.py"), "--json",
         "--today", DATA["as_of"]], capture_output=True, text=True, check=True).stdout)
    assert payload["count"] == len(DATA["instruments"])
    assert payload["stale_after_days"] == DATA["stale_after_days"]


def test_fail_on_stale_exits_non_zero_only_when_there_is_something_to_fix():
    limit = DATA["stale_after_days"]
    late = date.fromordinal(tracker_report.parse(DATA["as_of"]).toordinal() + limit + 5)
    run = subprocess.run([sys.executable, str(ROOT / "scripts" / "tracker_report.py"),
                          "--fail-on-stale", "--today", late.isoformat()],
                         capture_output=True, text=True)
    assert run.returncode == 1
