"""The briefs in briefs/ must be generated, current, and quote clauses exactly.

A brief is the version an official prints or attaches to a file, so a clause that
has been reworded, truncated or silently dropped on the way into a brief is the
failure mode these tests exist to catch.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
import briefs                                          # noqa: E402
from build import CLAUSE, GROUPS                       # noqa: E402

MODEL_LANGUAGE = sorted((ROOT / "policy" / "model-language").glob("*.md"))
STEMS = [stem for stem, _ in GROUPS]


@pytest.fixture(scope="module")
def pages() -> dict[str, str]:
    return briefs.build_all()


def test_every_model_language_file_has_a_brief():
    assert {p.stem for p in MODEL_LANGUAGE} == set(STEMS)


def test_committed_briefs_are_up_to_date(pages):
    """`python app/briefs.py` must be rerun whenever a source changes."""
    stale = [name for name, text in pages.items()
             if not (ROOT / "briefs" / f"{name}.md").exists()
             or (ROOT / "briefs" / f"{name}.md").read_text() != text]
    assert stale == [], f"run python app/briefs.py: {stale}"


def test_every_clause_appears_in_exactly_one_brief_byte_for_byte(pages):
    briefs_text = {stem: pages[stem] for stem in STEMS}
    seen = {}
    for path in MODEL_LANGUAGE:
        for m in CLAUSE.finditer(path.read_text()):
            clause_id, body = m["id"], m["body"].strip()
            assert clause_id not in seen, f"duplicate clause id {clause_id}"
            containing = [s for s, text in briefs_text.items() if body in text]
            assert len(containing) == 1, (clause_id, containing)
            assert containing[0] == path.stem, (clause_id, containing[0], path.stem)
            # The id is printed too, so a reader can trace the clause back to source.
            assert f"`{clause_id}`" in briefs_text[path.stem], clause_id
            seen[clause_id] = containing[0]
    assert len(seen) == sum(len(CLAUSE.findall(p.read_text())) for p in MODEL_LANGUAGE)
    assert len(seen) >= 20


def test_briefs_quote_the_framework_problem_statement_verbatim(pages):
    statement = briefs.framework_problem_statement()
    assert statement in (ROOT / "policy" / "FRAMEWORK.md").read_text()
    for stem in STEMS:
        assert statement in pages[stem], stem


def test_every_recommendation_row_names_real_instruments():
    ids = {e["id"] for e in json.loads((ROOT / "data" / "instruments.json").read_text())["instruments"]}
    rows = briefs.recommendation_rows()
    assert len(rows) >= 13
    for r in rows:
        assert r["instrument_ids"], r
        assert set(r["instrument_ids"]) <= ids, r["instrument_ids"]


def test_every_recommendation_reaches_at_least_one_brief(pages):
    instruments = json.loads((ROOT / "data" / "instruments.json").read_text())["instruments"]
    doc_of = {e["id"]: e["doc"] for e in instruments}
    for r in briefs.recommendation_rows():
        docs = {doc_of[i] for i in r["instrument_ids"]}
        stems = [Path(d).stem for d in docs]
        assert stems, r
        assert any(r["ask"] in pages[s] for s in stems), (r["n"], stems)


def test_every_instrument_reaches_its_brief(pages):
    for e in json.loads((ROOT / "data" / "instruments.json").read_text())["instruments"]:
        stem = Path(e["doc"]).stem
        assert stem in pages, (e["id"], e["doc"])
        assert e["name"] in pages[stem], e["id"]
        # A contested entry must carry its warning into the printed brief.
        if e.get("verify"):
            assert "**check**" in pages[stem], e["id"]


def test_briefs_carry_the_licence_and_the_screening_disclaimer(pages):
    for stem in STEMS:
        text = pages[stem]
        assert briefs.LICENCE in text and briefs.DISCLAIMER in text, stem
        assert f"Aquatic Guardian {briefs.VERSION}" in text, stem
        assert "Sentient Futures" in text, stem
        # The generation date is a repository date, not today's, so output is stable.
        as_of = json.loads((ROOT / "data" / "instruments.json").read_text())["as_of"]
        assert f"as of {as_of}" in text, stem
        assert not re.search(r"\bTODO\b|\bTBD\b", text), stem
