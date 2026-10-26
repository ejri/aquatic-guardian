"""Live ocean bundled-detector catalogue must match files on disk."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAT = ROOT / "site" / "models" / "models.json"


def _catalog() -> dict:
    return json.loads(CAT.read_text())


def test_catalog_default_exists_and_ids_are_unique():
    cat = _catalog()
    ids = [m["id"] for m in cat["models"]]
    assert len(ids) == len(set(ids))
    assert cat["default"] in ids


def test_bundled_onnx_files_exist_and_labels_are_named():
    cat = _catalog()
    for m in cat["models"]:
        assert m["id"] and m["label"]
        if not m.get("file"):
            continue
        path = ROOT / "site" / m["file"]
        assert path.is_file(), f"missing {path}"
        assert path.stat().st_size > 1_000_000, f"{path} is too small to be an ONNX detector"
        labels = m.get("labels") or []
        assert labels and all(isinstance(s, str) and s.strip() for s in labels)
        assert m.get("size") == 320
        assert m.get("source")


def test_noaa_fish_uses_grayscale_preprocess():
    m = next(x for x in _catalog()["models"] if x["id"] == "noaa-mouss-fish-yolov8n")
    assert m["preprocess"] == "grayscale"
    assert m["labels"] == ["fish"]


def test_candidates_keep_named_sources_and_are_not_bundled():
    cat = _catalog()
    bundled = {m["id"] for m in cat["models"]}
    for c in cat["candidates"]:
        assert c["id"] not in bundled
        assert c["url"].startswith("https://")
        assert c.get("note")
