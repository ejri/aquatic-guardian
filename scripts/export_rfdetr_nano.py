#!/usr/bin/env python3
"""Export Community Fish Detector RF-DETR Nano 640 to ONNX for Live ocean.

Downloads the CFD Apache-2.0 checkpoint if needed, then exports ONNX via rfdetr.

    pip install 'rfdetr[onnx]'
    python scripts/export_rfdetr_nano.py

Writes site/models/rfdetr-nano-640.onnx and flips models.json shipped=true.
"""
from __future__ import annotations

import json
import hashlib
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "site" / "models" / "rfdetr-nano-640.onnx"
CAT = ROOT / "site" / "models" / "models.json"
CACHE = ROOT / ".cache" / "cfd-2026.02.02-rf-detr-nano-640.pth"
PTH_URL = (
    "https://github.com/filippovarini/community-fish-detector/releases/download/"
    "cfd-2026.02.02-rf-detr-nano/community-fish-detector-2026.02.02-rf-detr-nano-640.pth"
)
# Published on the GitHub release page for cfd-2026.02.02-rf-detr-nano
PTH_SHA256 = "076b0a80d5dbc3361fb2be707d521ce96fe990b453fb1c215d99194fc65b4762"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_pth() -> Path:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    if CACHE.is_file() and _sha256(CACHE) == PTH_SHA256:
        return CACHE
    print(f"Downloading {PTH_URL} …")
    urllib.request.urlretrieve(PTH_URL, CACHE)
    digest = _sha256(CACHE)
    if digest != PTH_SHA256:
        CACHE.unlink(missing_ok=True)
        raise SystemExit(f"SHA-256 mismatch: got {digest}, expected {PTH_SHA256}")
    return CACHE


def mark_shipped() -> None:
    cat = json.loads(CAT.read_text())
    for m in cat["models"]:
        if m["id"] == "rfdetr-nano":
            m["shipped"] = True
            m["file"] = "models/rfdetr-nano-640.onnx"
            m["size"] = 640
            m["labels"] = ["fish"]
            m["architecture"] = "rfdetr"
            m["note"] = (
                "Community Fish Detector RF-DETR Nano 640 (cfd-2026.02.02). "
                "Apache-2.0. AP 0.596 on publisher's CFD validation split — not "
                "directly comparable across cameras. Screening only."
            )
    cat["as_of"] = "2026-11-11"
    cat["default"] = "rfdetr-nano"
    CAT.write_text(json.dumps(cat, indent=2) + "\n")


def main() -> int:
    try:
        from rfdetr import RFDETRNano  # type: ignore
    except ImportError:
        print("Install: pip install 'rfdetr[onnx]'", file=sys.stderr)
        return 1
    pth = ensure_pth()
    model = RFDETRNano(pretrain_weights=str(pth), resolution=640)
    exported = model.export(output_dir=str(OUT.parent), batch_size=1)
    src = Path(exported) if exported else None
    if src is None or not src.is_file():
        # rfdetr versions differ: look for newest .onnx under site/models or cwd
        candidates = sorted(OUT.parent.glob("*.onnx"), key=lambda p: p.stat().st_mtime, reverse=True)
        candidates += sorted(Path(".").glob("**/rfdetr*.onnx"))
        candidates += sorted(Path("output").glob("**/*.onnx")) if Path("output").is_dir() else []
        if not candidates:
            print("Export finished but no ONNX file found.", file=sys.stderr)
            return 1
        src = candidates[0]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if src.resolve() != OUT.resolve():
        OUT.write_bytes(src.read_bytes())
    print(f"Wrote {OUT} ({OUT.stat().st_size / 1e6:.1f} MB).")
    mark_shipped()
    print("Updated models.json: rfdetr-nano shipped=true.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
