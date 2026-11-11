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
        labels = m.get("labels") or []
        assert labels and all(isinstance(s, str) and s.strip() for s in labels)
        assert m.get("size") in (320, 640)
        assert m.get("source")
        # Target weights (e.g. RF-DETR Nano) may be listed before the ONNX is exported.
        if m.get("shipped") is False:
            continue
        path = ROOT / "site" / m["file"]
        assert path.is_file(), f"missing {path}"
        assert path.stat().st_size > 1_000_000, f"{path} is too small to be an ONNX detector"


def test_rfdetr_is_default_path_and_apache():
    cat = _catalog()
    assert cat["default"] == "rfdetr-nano"
    m = next(x for x in cat["models"] if x["id"] == "rfdetr-nano")
    assert "Apache-2.0" in (m.get("license") or "")
    assert m.get("shipped") is True
    assert m.get("architecture") == "rfdetr"
    path = ROOT / "site" / m["file"]
    assert path.is_file() and path.stat().st_size > 1_000_000


def test_legacy_yolo_models_declare_agpl():
    cat = _catalog()
    for mid in ("brackish-yolov8n", "noaa-mouss-fish-yolov8n", "noaa-urchin-yolo11n"):
        m = next(x for x in cat["models"] if x["id"] == mid)
        assert "AGPL" in (m.get("license") or "")


def test_noaa_fish_uses_grayscale_preprocess():
    m = next(x for x in _catalog()["models"] if x["id"] == "noaa-mouss-fish-yolov8n")
    assert m["preprocess"] == "grayscale"
    assert m["labels"] == ["fish"]


def test_display_groups_are_twelve():
    groups = _catalog().get("display_groups") or []
    assert len(groups) == 12
    assert "Fish" in groups and "Other animal" in groups


def test_candidates_keep_named_sources_and_are_not_bundled():
    cat = _catalog()
    bundled = {m["id"] for m in cat["models"]}
    for c in cat["candidates"]:
        assert c["id"] not in bundled
        assert c["url"].startswith("https://")
        assert c.get("note")
