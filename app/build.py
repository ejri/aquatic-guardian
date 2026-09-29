"""Build the published site in site/ from the source fragments in web/parts/.

Audience site (home + public + officials + lab + industry) is assembled from the
ordered HTML fragments. The screening engine, simulation kernels, instrument
tracker, model language and notebook Lab results are injected so the page never
drifts from the repository's single sources of truth.

`site/` is the Netlify publish directory (built output only).
`--check` fails if a published file or a mirrored package resource is stale.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARTS = ROOT / "web" / "parts"
SITE = ROOT / "site"
# Audience page: head, body (routes), data hooks, core UI, hero, lab notebooks, start.
INDEX_PARTS = (
    "1_head.html", "2_body.html", "3_data.html", "4_core.html",
    "5_hero.html", "6_thermal.html", "7_monitor.html", "8_aqua.html", "9_start.html",
)
PAGES = {"index.html": INDEX_PARTS, "404.html": ("1_head.html", "404_body.html")}
PAGE_META = {
    "404.html": (
        "Page not found: Aquatic Guardian",
        "That page is not on the Aquatic Guardian site.",
    )
}
GROUPS = [
    ("us-federal", "US federal"), ("us-state-model-bill", "US states"),
    ("permit-conditions", "Permits"), ("eu", "European Union"),
    ("canada", "Canada"), ("international", "International and UK"),
]
CLAUSE = re.compile(
    r"<!-- clause: (?P<id>[\w-]+) -->\n(?P<body>.*?)\n<!-- /clause -->", re.S
)
BRIEF_BASE = "https://github.com/ejri/aquatic-guardian/blob/main/briefs"


def parse_group(path: Path) -> dict:
    text = path.read_text()
    lines = text.splitlines()
    title = lines[0].lstrip("# ").strip()
    intro_end = next(
        (i for i, l in enumerate(lines[1:], 1) if l.startswith("## ")), len(lines)
    )
    intro = "\n".join(lines[1:intro_end]).strip()
    clauses, prev_end = [], 0
    for m in CLAUSE.finditer(text):
        before = text[:m.start()]
        heads = list(re.finditer(r"^#{2,3} (.+)$", before, re.M))
        head_end = heads[-1].end() if heads else 0
        clauses.append({
            "id": m["id"],
            "heading": heads[-1].group(1) if heads else title,
            "context": text[max(head_end, prev_end):m.start()].strip(),
            "text": m["body"].strip(),
        })
        prev_end = m.end()
    return {"title": title, "intro": intro, "clauses": clauses}


def notebook_results() -> dict:
    path = ROOT / "data" / "notebook_results.json"
    if not path.exists() or path.stat().st_size < 10:
        raise SystemExit(
            "data/notebook_results.json missing or empty: "
            "run python app/notebook_results.py"
        )
    return json.loads(path.read_text())


def recommendation_rows_for_site() -> list[list[str]]:
    """Table cells from policy/RECOMMENDATIONS.md (markers stripped)."""
    rows: list[list[str]] = []
    for line in (ROOT / "policy" / "RECOMMENDATIONS.md").read_text().splitlines():
        if not line.startswith("|") or line.startswith("|---") or line.startswith("| #"):
            continue
        cells = [re.sub(r"\s*<!--.*?-->", "", c).strip() for c in line.split("|")[1:-1]]
        if cells and cells[0].isdigit():
            rows.append(cells)
    return rows


def verification_rows_for_site() -> list[list[str]]:
    """ID / item / check / status from docs/VERIFICATION.md for the Lab table."""
    rows: list[list[str]] = []
    for line in (ROOT / "docs" / "VERIFICATION.md").read_text().splitlines():
        if not line.startswith("|") or line.startswith("|---") or line.startswith("| ID"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) >= 4 and re.match(r"^[A-Z]+-\d+$", cells[0]):
            # Drop markdown bold markers used in the register.
            status = re.sub(r"\*+", "", cells[3]).strip()
            rows.append([cells[0], cells[1], cells[2], status])
    return rows


def site_data() -> dict:
    policy = []
    for stem, label in GROUPS:
        g = parse_group(ROOT / "policy" / "model-language" / f"{stem}.md")
        g["clauses"] = [{k: v for k, v in c.items() if k != "context"} for c in g["clauses"]]
        g.update({"key": stem, "label": label, "path": f"policy/model-language/{stem}.md"})
        policy.append(g)
    criteria = json.loads((ROOT / "data" / "criteria.json").read_text())
    return {
        "instruments": json.loads((ROOT / "data" / "instruments.json").read_text()),
        "policy": policy,
        "jurisdictions": criteria.get("jurisdictions", []),
        "briefs": [
            {"label": label, "file": f"{stem}.md", "url": f"{BRIEF_BASE}/{stem}.md"}
            for stem, label in GROUPS
        ],
        "recommendations": recommendation_rows_for_site(),
        "verification": verification_rows_for_site(),
        # Lab page reads D.results.thermal / .monitoring / .aquaculture / .reported
        "results": notebook_results(),
    }


def build(page: str) -> str:
    missing = [n for n in PAGES[page] if not (PARTS / n).exists()]
    if missing:
        raise SystemExit(f"missing web/parts fragments for {page}: {missing}")
    out = "".join((PARTS / name).read_text() for name in PAGES[page])
    if page in PAGE_META:
        title, desc = PAGE_META[page]
        out = re.sub(r"<title>.*?</title>", f"<title>{title}</title>", out, count=1, flags=re.S)
        out = re.sub(
            r'(<meta name="description" content=").*?"',
            rf'\1{desc}"',
            out,
            count=1,
            flags=re.S,
        )
    if "/*__ENGINE__*/" in out:
        out = out.replace("/*__ENGINE__*/", (ROOT / "app" / "engine.js").read_text())
    if "/*__SIMS__*/" in out:
        out = out.replace("/*__SIMS__*/", (ROOT / "app" / "sims.js").read_text())
    if "/*__DATA__*/" in out:
        out = out.replace(
            "/*__DATA__*/",
            "window.AG_DATA = " + json.dumps(site_data(), ensure_ascii=False) + ";",
        )
    return out


MIRROR = [
    ("schemas", "aquatic-disclosure.schema.json"),
    ("schemas", "notebook-handoff.schema.json"),
    ("schemas", "instruments.schema.json"),
    ("data", "criteria.json"),
    ("data", "instruments.json"),
    ("data", "notebook_results.json"),
]


def mirror(check: bool) -> bool:
    ok = True
    for kind, name in MIRROR:
        src = ROOT / kind / name
        dst = ROOT / "src" / "aquatic_guardian" / "resources" / kind / name
        if check:
            ok &= dst.exists() and dst.read_bytes() == src.read_bytes()
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())
    return ok


if __name__ == "__main__":
    check = "--check" in sys.argv
    if not check:
        # Ensure Lab numbers exist before writing the page.
        nr = ROOT / "data" / "notebook_results.json"
        if not nr.exists() or nr.stat().st_size < 10:
            from app import notebook_results as nbr  # type: ignore
            # Fall through: invoke as subprocess-like main
            import runpy
            runpy.run_path(str(ROOT / "app" / "notebook_results.py"), run_name="__main__")
    if not mirror(check):
        sys.exit("package resources differ from schemas/ or data/: run python app/build.py")
    for page in PAGES:
        html, target = build(page), SITE / page
        if check:
            if not target.exists() or target.read_text() != html:
                sys.exit(f"site/{page} is stale: run python app/build.py")
            print(f"site/{page} is up to date")
        else:
            target.write_text(html)
            print(f"wrote {target} ({len(html) / 1024:.0f} KB)")
