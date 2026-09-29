"""Build site/index.html from the ordered fragments in site/parts/.

Injects the screening engine, the instrument tracker, and every model-language
clause from policy/model-language/*.md, so the website never drifts from the
repository's single sources of truth. `--check` fails if site/index.html is stale.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GROUPS = [("us-federal", "US federal"), ("us-state-model-bill", "US states"),
          ("permit-conditions", "Permits"), ("eu", "European Union"),
          ("canada", "Canada"), ("international", "International and UK")]
CLAUSE = re.compile(r"<!-- clause: (?P<id>[\w-]+) -->\n(?P<body>.*?)\n<!-- /clause -->", re.S)


def parse_group(path: Path) -> dict:
    text = path.read_text()
    lines = text.splitlines()
    title = lines[0].lstrip("# ").strip()
    intro_end = next((i for i, l in enumerate(lines[1:], 1) if l.startswith("## ")), len(lines))
    intro = "\n".join(lines[1:intro_end]).strip()
    clauses = []
    for m in CLAUSE.finditer(text):
        before = text[:m.start()]
        heads = re.findall(r"^#{2,3} (.+)$", before, re.M)
        clauses.append({"id": m["id"], "heading": heads[-1] if heads else title,
                        "text": m["body"].strip()})
    return {"title": title, "intro": intro, "clauses": clauses}


def build() -> str:
    tpl = "".join(p.read_text() for p in sorted((ROOT / "site" / "parts").glob("*.html")))
    policy = []
    for stem, label in GROUPS:
        g = parse_group(ROOT / "policy" / "model-language" / f"{stem}.md")
        g.update({"key": stem, "label": label,
                  "path": f"policy/model-language/{stem}.md"})
        policy.append(g)
    data = {"instruments": json.loads((ROOT / "data" / "instruments.json").read_text()),
            "policy": policy}
    engine = (ROOT / "app" / "engine.js").read_text()
    out = tpl.replace("/*__ENGINE__*/", engine)
    out = out.replace("/*__DATA__*/", "window.AG_DATA = " + json.dumps(data, ensure_ascii=False) + ";")
    return out


MIRROR = [("schemas", "aquatic-disclosure.schema.json"), ("schemas", "notebook-handoff.schema.json"),
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
    if not mirror("--check" in sys.argv):
        sys.exit("package resources differ from schemas/ or data/: run python app/build.py")
    html = build()
    target = ROOT / "site" / "index.html"
    if "--check" in sys.argv:
        if not target.exists() or target.read_text() != html:
            sys.exit("site/index.html is stale: run python app/build.py")
        print("site/index.html is up to date")
    else:
        target.write_text(html)
        print(f"wrote {target} ({len(html)/1024:.0f} KB)")
