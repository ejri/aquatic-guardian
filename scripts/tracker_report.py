"""What in data/instruments.json needs a person to look at it again.

Three things go wrong with a policy tracker: entries quietly go out of date,
entries stay marked as unconfirmed for months, and dated events pass while the
status still describes them as forthcoming. This report finds all three.

    python scripts/tracker_report.py              # human-readable report
    python scripts/tracker_report.py --json       # same findings as JSON
    python scripts/tracker_report.py --fail-on-stale   # non-zero exit if anything is stale

Nothing here judges whether a status is correct. It only says which entries a
person should read the primary source for. The weekly GitHub Action in
.github/workflows/tracker.yml posts the output to a single tracking issue.
"""
from __future__ import annotations
import argparse, json, re
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRACKER = ROOT / "data" / "instruments.json"
# Words that describe an event as still to come. If one of these sits next to a date
# that has passed, the prose and the date disagree.
FUTURE_WORDS = re.compile(
    r"\b(due|expected|pending|upcoming|forthcoming|open|closes|closing|to come|awaited|"
    r"anticipated|planned|scheduled)\b", re.I)


def parse(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def findings(data: dict, today: date) -> dict:
    limit = data["stale_after_days"]
    stale, unverified, past_future, undated = [], [], [], []
    for e in data["instruments"]:
        age = (today - parse(e["last_checked"])).days
        if age > limit:
            stale.append({"id": e["id"], "name": e["name"], "last_checked": e["last_checked"],
                          "days": age})
        if e.get("verify"):
            doubts = [e["verify_note"]] if e.get("verify_note") else []
            if not e.get("sources"):
                doubts.append("No primary-source link yet.")
            unverified.append({"id": e["id"], "name": e["name"], "note": " ".join(doubts),
                               "sources": len(e.get("sources", []))})
        if not e.get("sources"):
            undated.append(e["id"])

        # A status that still speaks of something forthcoming, when the date it refers
        # to has passed. Deadlines are checked the same way.
        passed = [d for d in e["dates"] if parse(d["date"]) < today]
        if passed and FUTURE_WORDS.search(e["status"]):
            latest = max(passed, key=lambda d: d["date"])
            past_future.append({"id": e["id"], "name": e["name"], "status": e["status"],
                                "date": latest["date"], "event": latest["event"],
                                "days": (today - parse(latest["date"])).days})
        if e.get("deadline") and parse(e["deadline"]) < today:
            past_future.append({"id": e["id"], "name": e["name"], "status": e["status"],
                                "date": e["deadline"], "event": "deadline passed",
                                "days": (today - parse(e["deadline"])).days})
        for d in e["dates"]:
            if parse(d["date"]) < today and FUTURE_WORDS.search(d["event"]):
                past_future.append({"id": e["id"], "name": e["name"], "status": e["status"],
                                    "date": d["date"], "event": d["event"],
                                    "days": (today - parse(d["date"])).days})
    seen, unique = set(), []
    for p in past_future:
        key = (p["id"], p["date"], p["event"])
        if key not in seen:
            seen.add(key)
            unique.append(p)
    past_future = unique
    return {"as_of": data["as_of"], "today": today.isoformat(), "count": len(data["instruments"]),
            "stale_after_days": limit, "stale": stale, "unverified": unverified,
            "past_dates_described_as_future": past_future, "without_sources": undated}


def report(f: dict) -> str:
    lines = [f"# Tracker review: {f['count']} instruments",
             "",
             f"Run on {f['today']}. `data/instruments.json` says it is current as of "
             f"{f['as_of']}. An entry is stale after {f['stale_after_days']} days.",
             ""]

    lines += [f"## Stale: not checked for more than {f['stale_after_days']} days "
              f"({len(f['stale'])})", ""]
    if f["stale"]:
        lines += ["| Instrument | Last checked | Days |", "|---|---|---|"]
        lines += [f"| {s['name']} (`{s['id']}`) | {s['last_checked']} | {s['days']} |"
                  for s in sorted(f["stale"], key=lambda s: -s["days"])]
    else:
        lines.append("None.")
    lines.append("")

    lines += [f"## Marked verify ({len(f['unverified'])})", ""]
    if f["unverified"]:
        lines += ["| Instrument | Sources on file | What to confirm |", "|---|---|---|"]
        lines += [f"| {u['name']} (`{u['id']}`) | {u['sources']} | {u['note']} |"
                  for u in f["unverified"]]
    else:
        lines.append("None.")
    lines.append("")

    lines += [f"## Dates that have passed but read as future ({len(f['past_dates_described_as_future'])})", ""]
    if f["past_dates_described_as_future"]:
        lines += ["| Instrument | Status | Date | Event | Days ago |", "|---|---|---|---|---|"]
        lines += [f"| {p['name']} (`{p['id']}`) | {p['status']} | {p['date']} | {p['event']} "
                  f"| {p['days']} |"
                  for p in sorted(f["past_dates_described_as_future"], key=lambda p: -p["days"])]
    else:
        lines.append("None.")
    lines.append("")

    if f["without_sources"]:
        lines += [f"## No primary-source URL recorded ({len(f['without_sources'])})", "",
                  "These entries carry no link, so nobody can check them without searching "
                  "again. Add a primary source and set `verify` to false.", "",
                  ", ".join(f"`{i}`" for i in f["without_sources"]), ""]

    lines += ["---", "",
              "Edit `data/instruments.json` and open a pull request. Do not add a URL you have "
              "not opened. Regenerate the site and the briefs afterwards: "
              "`python app/build.py && python app/briefs.py`.", ""]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true", help="print the findings as JSON")
    ap.add_argument("--today", help="override today's date (YYYY-MM-DD), for tests")
    ap.add_argument("--fail-on-stale", action="store_true",
                    help="exit non-zero if anything is stale or reads as future")
    args = ap.parse_args()
    data = json.loads(TRACKER.read_text())
    f = findings(data, parse(args.today) if args.today else date.today())
    print(json.dumps(f, indent=2) if args.json else report(f))
    if args.fail_on_stale and (f["stale"] or f["past_dates_described_as_future"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
