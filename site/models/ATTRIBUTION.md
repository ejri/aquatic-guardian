# Detection models bundled with Live ocean

Weights in this folder are third-party. The site Apache-2.0 licence does **not** replace their terms. Screening only. Class labels shown to visitors are mapped to 12 plain groups (see `models.json` `display_groups`).

| File | Source | Licence | Classes | Notes |
|---|---|---|---|---|
| `rfdetr-nano-640.onnx` (**default**) | [Community Fish Detector RF-DETR Nano 640](https://github.com/filippovarini/community-fish-detector) (`cfd-2026.02.02`) | **Apache-2.0** | fish | Dynamic INT8 ONNX (~39 MB) for browser size; FP32 kept in `.cache/` via `scripts/export_rfdetr_nano.py`. Publisher AP 0.596 on CFD validation — not camera-comparable. |
| `brackish-yolov8n.onnx` | [dronefreak/brackish-yolov8n](https://huggingface.co/dronefreak/brackish-yolov8n) | **AGPL-3.0** (Ultralytics) | crab, fish, jellyfish, shrimp, small_fish, starfish | Legacy. Brackish Underwater (Limfjords, Denmark). |
| `noaa-mouss-fish-yolov8n.onnx` | [akridge/yolo8-fish-detector-grayscale](https://huggingface.co/akridge/yolo8-fish-detector-grayscale) | **AGPL-3.0** (Ultralytics) | fish | Legacy. NOAA PIFSC MOUSS grayscale. |
| `noaa-urchin-yolo11n.onnx` | [akridge/yolo11n-sea-urchin-detector](https://huggingface.co/akridge/yolo11n-sea-urchin-detector) | **AGPL-3.0** (Ultralytics) | urchin | Legacy. |

**Default path (Nov 2026):** RF-DETR Nano INT8 in the browser (CFD `cfd-2026.02.02` shipping weights; optional fine-tune scaffolding under `models/train/` is unused this release); ByteTrack + OC-SORT observation re-seed tracker; optional relay naming via BioCLIP 2 (**MIT**) when `AG_BIOCLIP=1` and `open_clip_torch` are set — see `relay/classify.py`, `relay/.env.example`, and `relay/calibration/bioclip_thresholds.json` (threshold 0.7 audit default, not field-calibrated).

**AGPL note:** Redistributing or modifying the legacy Ultralytics-trained ONNX weights may require offering corresponding source under AGPL-3.0. Prefer Apache/MIT models for new work. The About page states this.

Export: `scripts/export_rfdetr_nano.py`, `scripts/export_vision_models.py`.
