#!/usr/bin/env python3
"""Fine-tune RF-DETR Nano on a merged marine COCO dataset.

Requires: pip install -r models/train/requirements.txt

Smoke mode runs 1 epoch on the synthetic set from prepare_merged_coco.py --smoke.
Full runs need the real merged COCO under models/train/data/merged and a GPU/MPS host.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataset", type=Path, required=True, help="COCO root with train/ and valid/")
    ap.add_argument("--epochs", type=int, default=50)
    ap.add_argument("--batch-size", type=int, default=4)
    ap.add_argument("--grad-accum", type=int, default=4)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--device", default=None, help="cpu | mps | cuda (default: auto)")
    ap.add_argument("--output", type=Path, default=ROOT / "models" / "train" / "runs")
    ap.add_argument("--smoke", action="store_true", help="1-epoch laptop check; do not ship weights")
    args = ap.parse_args()

    dataset = args.dataset.resolve()
    if not (dataset / "train" / "_annotations.coco.json").is_file():
        raise SystemExit(f"missing {dataset / 'train' / '_annotations.coco.json'}")
    if not (dataset / "valid" / "_annotations.coco.json").is_file():
        raise SystemExit(f"missing valid split; run prepare_merged_coco.py first")

    import torch
    from rfdetr import RFDETRNano

    if args.device:
        device = args.device
    elif torch.cuda.is_available():
        device = "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"

    epochs = 1 if args.smoke else args.epochs
    run_dir = args.output / ("smoke" if args.smoke else datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ"))
    run_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "dataset": str(dataset),
        "epochs": epochs,
        "batch_size": args.batch_size,
        "grad_accum_steps": args.grad_accum,
        "lr": args.lr,
        "device": device,
        "smoke": bool(args.smoke),
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "note": "Smoke run — not for shipping" if args.smoke else "Merged marine fine-tune",
        "shipped_weights_remain": "site/models/rfdetr-nano-640.onnx (CFD cfd-2026.02.02 interim until a verified full run replaces it)",
    }
    (run_dir / "run.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))

    model = RFDETRNano(num_classes=1)
    model.train(
        dataset_dir=str(dataset),
        epochs=epochs,
        batch_size=args.batch_size,
        grad_accum_steps=args.grad_accum,
        lr=args.lr,
        output_dir=str(run_dir),
        device=device,
        run_test=False,
    )
    meta["finished_utc"] = datetime.now(timezone.utc).isoformat()
    meta["output_dir"] = str(run_dir)
    (run_dir / "run.json").write_text(json.dumps(meta, indent=2))
    print(f"done → {run_dir}")
    if args.smoke:
        print("smoke only: keep shipping CFD interim ONNX until a full merged fine-tune is verified")


if __name__ == "__main__":
    main()
