"""Build one printable policy brief per model-language file into briefs/.

Officials asked for something they can print or attach to a file. Each brief is
assembled from the same sources as the website, so it cannot drift from them:

- the problem statement is the first paragraph of section 1 of policy/FRAMEWORK.md;
- the status paragraph is the preamble of the model-language file itself;
- the instrument rows come from data/instruments.json, selected by each entry's `doc`;
- the clauses are copied between the `<!-- clause: id -->` markers, byte for byte;
- the asks come from the rows of policy/RECOMMENDATIONS.md whose hidden
  `<!-- instruments: id -->` marker names an instrument in this brief.

Nothing is retyped and no date, status or citation is written here. The "generated"
date is data/instruments.json's `as_of`, so regenerating on a different day produces
an identical file and tests/test_briefs.py can check the committed output is current.

    python app/briefs.py            # write briefs/*.md (+ PDF/DOCX if pandoc is installed)
    python app/briefs.py --check    # fail if briefs/ is stale
"""
from __future__ import annotations
import json, re, shutil, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import GROUPS, ROOT, parse_group          # noqa: E402  single source for the parser

OUT = ROOT / "briefs"
VERSION = "0.1.0"
LICENCE = ("Framework, model language and this brief: CC BY 4.0. "
           "Code: Apache-2.0. Aquatic Disclosure Schema: CC0.")
DISCLAIMER = (
    "Screening results from the Aquatic Guardian tool are for scoping and public "
    "understanding. They are not legal advice and do not replace a regulatory "
    "mixing-zone study, a Clean Water Act \u00a7316 demonstration, a Fisheries Act "
    "authorisation or species-expert review. Legal status changes: check each "
    "instrument's primary source before relying on a date.")
RECOMMENDATION_MARK = re.compile(r"<!--\s*instruments:\s*(?P<ids>[\w,\s-]+?)\s*-->")
WORDS_PER_PRINTED_PAGE = 500        # 11 pt body text on A4/Letter with normal margins


def framework_problem_statement() -> str:
    """First paragraph of section 1 of policy/FRAMEWORK.md, verbatim."""
    text = (ROOT / "policy" / "FRAMEWORK.md").read_text()
    section = re.search(r"^## 1\. .*?$(?P<body>.*?)^## ", text, re.S | re.M)
    if section is None:
        raise ValueError("policy/FRAMEWORK.md has no section 1")
    paragraphs = [p.strip() for p in section["body"].strip().split("\n\n") if p.strip()]
    return paragraphs[0]


def recommendation_rows() -> list[dict]:
    """Rows of the table in policy/RECOMMENDATIONS.md with the instrument ids they act on."""
    rows = []
    for line in (ROOT / "policy" / "RECOMMENDATIONS.md").read_text().splitlines():
        if not line.startswith("| ") or set(line) <= set("|- "):
            continue
        mark = RECOMMENDATION_MARK.search(line)
        cells = [c.strip() for c in RECOMMENDATION_MARK.sub("", line).strip().strip("|").split("|")]
        if cells[0] in ("#", ""):
            continue
        if mark is None:
            raise ValueError(f"recommendation row has no instruments marker: {line[:60]}")
        rows.append({"n": cells[0], "who": cells[1], "instrument": cells[2], "ask": cells[3],
                     "timing": cells[4],
                     "instrument_ids": [i.strip() for i in mark["ids"].split(",")]})
    return rows


def dates_cell(entry: dict) -> str:
    return "; ".join(f"{d['date']}, {d['event']}" for d in entry["dates"]) or "none recorded"


def instruments_table(entries: list[dict]) -> str:
    head = ("| Instrument | Type | Legal status | Key dates | Where it bites | What to ask for |\n"
            "|---|---|---|---|---|---|\n")
    rows = []
    for e in entries:
        status = f"{e['status']} ({e['stage']})"
        if e.get("verify"):
            doubts = [e["verify_note"]] if e.get("verify_note") else []
            if not e.get("sources"):
                doubts.append("No primary-source link recorded in the repository yet.")
            status += " — **check**: " + " ".join(doubts)
        rows.append(f"| {e['name']} — {e['jurisdiction']} | {e['type']} | {status} "
                    f"| {dates_cell(e)} | {e['hook']} | {e['action']} |")
    return head + "\n".join(rows) + "\n"


def asks_table(rows: list[dict]) -> str:
    head = "| Who | Instrument | Ask | Timing |\n|---|---|---|---|\n"
    return head + "\n".join(f"| {r['who']} | {r['instrument']} | {r['ask']} | {r['timing']} |"
                            for r in rows) + "\n"


def brief(stem: str, label: str, instruments: dict, recommendations: list[dict]) -> str:
    group = parse_group(ROOT / "policy" / "model-language" / f"{stem}.md")
    doc = f"policy/model-language/{stem}.md"
    entries = [e for e in instruments["instruments"] if e["doc"] == doc]
    ids = {e["id"] for e in entries}
    asks = [r for r in recommendations if ids & set(r["instrument_ids"])]
    as_of = instruments["as_of"]

    p = [f"# Aquatic Guardian brief: {label}", "",
         f"**{group['title']}.** Aquatic Guardian {VERSION}. Instrument statuses as of "
         f"{as_of}. Generated from the repository by `app/briefs.py`; do not edit this file.", "",
         "## Why this is needed", "", framework_problem_statement(), ""]

    if group["intro"]:
        p += ["## Where this stands", "", group["intro"], ""]

    if entries:
        p += [f"## Instruments this attaches to ({len(entries)})", "",
              f"From `data/instruments.json`, status as of {as_of}.", "",
              instruments_table(entries)]
    else:
        p += ["## Instruments this attaches to", "",
              f"No entry in `data/instruments.json` names `{doc}`. Add one before using this brief.",
              ""]

    if asks:
        p += ["## What to ask for", "",
              "From `policy/RECOMMENDATIONS.md`, restricted to the instruments above.", "",
              asks_table(asks)]

    p += [f"## Model language ({len(group['clauses'])} clauses)", "",
          f"Copied verbatim from `{doc}`. Bracketed values are for the adopting authority to set. "
          "Licensed CC BY 4.0; please cite the repository.", ""]
    for c in group["clauses"]:
        p += [f"### {c['heading']}", "", f"Clause id: `{c['id']}`", ""]
        if c["context"]:
            p += [c["context"], ""]
        p += [c["text"], ""]

    p += ["---", "",
          f"Aquatic Guardian {VERSION}, a Sentient Futures project, building on *Governing the "
          "Ocean Server Farm* (Elchami, Kaplan and Daher, Sentient Futures, April 2026). "
          f"Sources as of {as_of}.", "",
          LICENCE, "", DISCLAIMER, ""]
    return "\n".join(p)


def index(pages: dict[str, str]) -> str:
    p = ["# Policy briefs", "",
         "One brief per model-language file, generated by `app/briefs.py` from "
         "`policy/`, `data/instruments.json` and `policy/RECOMMENDATIONS.md`. "
         "Do not edit these files; regenerate them.", "",
         "| Brief | File | Printed pages (estimate) |", "|---|---|---|"]
    for (stem, label), text in zip(GROUPS, [pages[s] for s, _ in GROUPS]):
        p.append(f"| {label} | [`{stem}.md`]({stem}.md) | {printed_pages(text):.1f} |")
    p += ["", f"Page estimates assume about {WORDS_PER_PRINTED_PAGE} words to a printed page; "
          "tables and clause text set longer than that, so treat them as a floor.", ""]
    return "\n".join(p)


def printed_pages(markdown: str) -> float:
    return len(markdown.split()) / WORDS_PER_PRINTED_PAGE


def build_all() -> dict[str, str]:
    instruments = json.loads((ROOT / "data" / "instruments.json").read_text())
    recommendations = recommendation_rows()
    pages = {stem: brief(stem, label, instruments, recommendations) for stem, label in GROUPS}
    pages["README"] = index(pages)
    return pages


def convert(path: Path) -> list[str]:
    """PDF and DOCX through pandoc when it is installed. Missing pandoc is not an error."""
    made = []
    if shutil.which("pandoc") is None:
        return made
    for fmt in ("pdf", "docx"):
        target = path.with_suffix("." + fmt)
        try:
            subprocess.run(["pandoc", str(path), "-o", str(target),
                            "--metadata", "title=" + path.stem], check=True,
                           capture_output=True, text=True)
            made.append(target.name)
        except subprocess.CalledProcessError as exc:
            print(f"pandoc could not write {target.name}: "
                  f"{(exc.stderr or '').strip().splitlines()[-1:] or exc}", file=sys.stderr)
    return made


def main(argv: list[str]) -> int:
    check = "--check" in argv
    pages = build_all()
    if not check:
        OUT.mkdir(exist_ok=True)
    stale = []
    for name, text in pages.items():
        target = OUT / f"{name}.md"
        if check:
            if not target.exists() or target.read_text() != text:
                stale.append(target.name)
            continue
        target.write_text(text)
        extra = convert(target) if name != "README" else []
        print(f"{target.relative_to(ROOT)}  {printed_pages(text):.1f} printed pages"
              + (f"  (+ {', '.join(extra)})" if extra else ""))
    if check:
        if stale:
            print("briefs are stale, run python app/briefs.py: " + ", ".join(stale), file=sys.stderr)
            return 1
        print(f"briefs/ is up to date ({len(pages)} files)")
        return 0
    over = [f"{s}.md ({printed_pages(pages[s]):.1f})" for s, _ in GROUPS
            if printed_pages(pages[s]) > 2]
    if over:
        print("\nOver about two printed pages: " + ", ".join(over))
    if shutil.which("pandoc") is None:
        print("pandoc is not installed, so only Markdown was written. "
              "Install pandoc (and a LaTeX engine for PDF) to get PDF and DOCX.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
