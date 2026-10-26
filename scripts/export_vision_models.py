#!/usr/bin/env python3
"""Export Live ocean ONNX detectors from the published PyTorch weights.

Usage (from the repo root, with ultralytics + onnx installed):

    python scripts/export_vision_models.py

Writes 320×320 opset-12 graphs to site/models/. Class names are read from
the checkpoints; they are not invented here.

Marine Detect FishInv / MegaFauna are YOLOv8l (~167 MB ONNX) and are not
copied into site/models/ (GitHub 100 MB file limit; ~20× nano FLOPs).
This script still exports them to /tmp/ag-models/ so you can upload the
.onnx by hand.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "site" / "models"
TMP = Path("/tmp/ag-models")

BUNDLED = (
    {
        "id": "noaa-mouss-fish-yolov8n",
        "url": "https://huggingface.co/akridge/yolo8-fish-detector-grayscale/resolve/main/yolov8n_fish_trained.pt",
        "pt": "yolov8n_fish_trained.pt",
        "onnx": "noaa-mouss-fish-yolov8n.onnx",
        "bundle": True,
    },
    {
        "id": "noaa-urchin-yolo11n",
        "url": "https://huggingface.co/akridge/yolo11n-sea-urchin-detector/resolve/main/yolo11n_urchin_trained.pt",
        "pt": "yolo11n_urchin_trained.pt",
        "onnx": "noaa-urchin-yolo11n.onnx",
        "bundle": True,
    },
    {
        "id": "marine-detect-fishinv",
        "url": (
            "https://stpubtenakanclyw.blob.core.windows.net/marine-detect/models2025/FishInv.pt"
            "?sv=2022-11-02&ss=bf&srt=co&sp=rltf&se=2099-12-31T18:55:46Z"
            "&st=2025-02-03T10:55:46Z&spr=https,http"
            "&sig=w%2FTQzrECsYsjtkBXNnnuFtn%2BC06PkjgLxDgRw%2FaUUKI%3D"
        ),
        "pt": "FishInv.pt",
        "onnx": "FishInv.onnx",
        "bundle": False,
    },
    {
        "id": "marine-detect-megafauna",
        "url": (
            "https://stpubtenakanclyw.blob.core.windows.net/marine-detect/models2025/MegaFauna.pt"
            "?sv=2022-11-02&ss=bf&srt=co&sp=rltf&se=2099-12-31T18:55:46Z"
            "&st=2025-02-03T10:55:46Z&spr=https,http"
            "&sig=w%2FTQzrECsYsjtkBXNnnuFtn%2BC06PkjgLxDgRw%2FaUUKI%3D"
        ),
        "pt": "MegaFauna.pt",
        "onnx": "MegaFauna.onnx",
        "bundle": False,
    },
)


def download(url: str, dest: Path) -> None:
    import urllib.request
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 1_000_000:
        return
    print("download", dest.name)
    urllib.request.urlretrieve(url, dest)


def export_one(spec: dict) -> dict:
    from ultralytics import YOLO
    pt = TMP / spec["pt"]
    download(spec["url"], pt)
    model = YOLO(str(pt))
    names = [model.names[i] for i in range(len(model.names))]
    print(spec["id"], "classes", names)
    onnx_path = model.export(format="onnx", imgsz=320, opset=12, simplify=True, dynamic=False)
    src = Path(onnx_path)
    dest = (OUT / spec["onnx"]) if spec["bundle"] else (TMP / spec["onnx"])
    dest.write_bytes(src.read_bytes())
    print("wrote", dest, dest.stat().st_size, "bundle" if spec["bundle"] else "local only")
    return {"id": spec["id"], "labels": names, "file": str(dest), "bytes": dest.stat().st_size}


def main() -> None:
    TMP.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    report = [export_one(spec) for spec in BUNDLED]
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
