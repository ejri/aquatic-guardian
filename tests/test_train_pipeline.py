"""RF-DETR fine-tune scaffolding stays wired without inventing shipped weights."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_prepare_smoke_coco(tmp_path: Path):
    out = tmp_path / "smoke"
    subprocess.check_call(
        [sys.executable, str(ROOT / "scripts" / "prepare_merged_coco.py"), "--smoke", "--out", str(out)],
        cwd=ROOT,
    )
    train = json.loads((out / "train" / "_annotations.coco.json").read_text())
    valid = json.loads((out / "valid" / "_annotations.coco.json").read_text())
    assert train["categories"][0]["name"] == "animal"
    assert len(train["images"]) >= 8 and len(valid["images"]) >= 2
    assert (out / "train" / train["images"][0]["file_name"]).is_file()


def test_train_readme_and_scripts_exist():
    assert (ROOT / "models" / "train" / "README.md").is_file()
    assert (ROOT / "scripts" / "train_rfdetr_marine.py").is_file()
    readme = (ROOT / "models" / "train" / "README.md").read_text()
    assert "cfd-2026.02.02" in readme
    assert "not" in readme.lower() and "ship" in readme.lower()
