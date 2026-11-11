# RF-DETR marine fine-tune (optional scaffolding)

Fine-tune **RF-DETR Nano** (Apache-2.0) on a merged COCO detection set, then export ONNX for `site/models/`.

## Status (2026-11-11)

| Artifact | Status |
|---|---|
| Shipped browser weights | CFD `cfd-2026.02.02` INT8 ONNX — **shipping detector for this release** |
| Merged-dataset fine-tune | **Out of scope** this release; pipeline kept for a later owner |
| Smoke train | Synthetic 1-epoch MPS check only (`--smoke`) |

Do not replace `site/models/rfdetr-nano-640.onnx` unless a later project explicitly resumes this work.

## Layout

```
models/train/
  README.md
  requirements.txt
  data/                 # gitignored downloads + merges
  runs/                 # gitignored checkpoints
```

Expected COCO layout for `rfdetr`:

```
dataset/
  train/_annotations.coco.json + images
  valid/_annotations.coco.json + images
```

## If resumed later

```bash
source .venv/bin/activate
pip install -r models/train/requirements.txt
python scripts/prepare_merged_coco.py --smoke --out models/train/data/smoke
python scripts/train_rfdetr_marine.py --dataset models/train/data/smoke --epochs 1 --smoke
# Full merge: place licensed COCO roots under models/train/data/raw/, then
# prepare_merged_coco.py --sources … --out models/train/data/merged
# train_rfdetr_marine.py --dataset … --epochs 50
# export via scripts/export_rfdetr_nano.py and update models.json + VERIFICATION V-6
```
