"""Build the published site in site/ from the source fragments in web/parts/.

Only built output lives in site/ (that is the Netlify publish directory); the
editable fragments live in web/parts/. site/index.html gets the screening
engine, the instrument tracker, and every model-language clause from
policy/model-language/*.md injected, so the website never drifts from the
repository's single sources of truth. site/404.html reuses the same head.
`--check` fails if either published file, or a mirrored package resource, is stale.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARTS = ROOT / "web" / "parts"
SITE = ROOT / "site"
PAGES = {"index.html": ("1_head.html", "2_body.html", "3_script.html"),
         "404.html": ("1_head.html", "404_body.html")}
# 1_head.html is shared, so pages other than index.html get their own title and description.
PAGE_META = {"404.html": ("Page not found: Aquatic Guardian",
                          "That page is not on the Aquatic Guardian site. Go to the home page for "
                          "the framework, the model language, the policy tracker and the screening tool.")}
GROUPS = [("us-federal", "US federal"), ("us-state-model-bill", "US states"),
          ("permit-conditions", "Permits"), ("eu", "European Union"),
          ("canada", "Canada"), ("international", "International and UK")]
CLAUSE = re.compile(r"<!-- clause: (?P<id>[\w-]+) -->\n(?P<body>.*?)\n<!-- /clause -->", re.S)
BRIEF_BASE = "https://github.com/ejri/aquatic-guardian/blob/main/briefs"


def parse_group(path: Path) -> dict:
    """Title, status preamble and clauses of one model-language file.

    `context` is the prose between a clause's heading and the clause itself, which
    app/briefs.py prints above the clause. `text` is the clause body exactly as the
    markers enclose it; nothing downstream may reword it.
    """
    text = path.read_text()
    lines = text.splitlines()
    title = lines[0].lstrip("# ").strip()
    intro_end = next((i for i, l in enumerate(lines[1:], 1) if l.startswith("## ")), len(lines))
    intro = "\n".join(lines[1:intro_end]).strip()
    clauses, prev_end = [], 0
    for m in CLAUSE.finditer(text):
        before = text[:m.start()]
        heads = list(re.finditer(r"^#{2,3} (.+)$", before, re.M))
        head_end = heads[-1].end() if heads else 0
        clauses.append({"id": m["id"], "heading": heads[-1].group(1) if heads else title,
                        "context": text[max(head_end, prev_end):m.start()].strip(),
                        "text": m["body"].strip()})
        prev_end = m.end()
    return {"title": title, "intro": intro, "clauses": clauses}


def site_data() -> dict:
    policy = []
    for stem, label in GROUPS:
        g = parse_group(ROOT / "policy" / "model-language" / f"{stem}.md")
        # `context` is for the briefs only; leave it out so the page stays small.
        g["clauses"] = [{k: v for k, v in c.items() if k != "context"} for c in g["clauses"]]
        g.update({"key": stem, "label": label,
                  "path": f"policy/model-language/{stem}.md"})
        policy.append(g)
    criteria = json.loads((ROOT / "data" / "criteria.json").read_text())
    return {"instruments": json.loads((ROOT / "data" / "instruments.json").read_text()),
            "policy": policy,
            "jurisdictions": criteria.get("jurisdictions", []),
            "briefs": [{"label": label, "file": f"{stem}.md", "url": f"{BRIEF_BASE}/{stem}.md"}
                       for stem, label in GROUPS]}


def build(page: str) -> str:
    out = "".join((PARTS / name).read_text() for name in PAGES[page])
    if page in PAGE_META:
        title, desc = PAGE_META[page]
        out = re.sub(r"<title>.*?</title>", f"<title>{title}</title>", out, count=1, flags=re.S)
        out = re.sub(r'(<meta name="description" content=)".*?"', rf'\1"{desc}"', out, count=1, flags=re.S)
    if "/*__ENGINE__*/" in out:
        out = out.replace("/*__ENGINE__*/", (ROOT / "app" / "engine.js").read_text())
    if "/*__DATA__*/" in out:
        out = out.replace("/*__DATA__*/",
                          "window.AG_DATA = " + json.dumps(site_data(), ensure_ascii=False) + ";")
    return out


MIRROR = [("schemas", "aquatic-disclosure.schema.json"), ("schemas", "notebook-handoff.schema.json"),
          ("schemas", "instruments.schema.json"),
          ("data", "criteria.json"), ("data", "instruments.json")]


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
            print(f"wrote {target} ({len(html)/1024:.0f} KB)")
