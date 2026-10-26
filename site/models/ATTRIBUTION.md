# Detection models bundled with Live ocean

Weights in this folder are third-party. The site Apache-2.0 licence does not replace their terms. Screening only.

| File | Source | Classes | Notes |
|---|---|---|---|
| `brackish-yolov8n.onnx` | [dronefreak/brackish-yolov8n](https://huggingface.co/dronefreak/brackish-yolov8n) | crab, fish, jellyfish, shrimp, small_fish, starfish | YOLOv8n, 320 px. Brackish Underwater (Limfjords, Denmark). See the model card for licence. |
| `noaa-mouss-fish-yolov8n.onnx` | [akridge/yolo8-fish-detector-grayscale](https://huggingface.co/akridge/yolo8-fish-detector-grayscale) | fish | YOLOv8n, 320 px. NOAA PIFSC MOUSS grayscale imagery. Scientific product; not official NOAA communication. |
| `noaa-urchin-yolo11n.onnx` | [akridge/yolo11n-sea-urchin-detector](https://huggingface.co/akridge/yolo11n-sea-urchin-detector) | urchin | YOLO11n, 320 px. Trained on Marine Detect + Roboflow urchin images. Scientific product; not official NOAA communication. |

Export recipe: `scripts/export_vision_models.py`.

Not bundled (too large or wrong task for live cameras): Orange Marine Detect YOLOv8l (FishInv / MegaFauna, ~167 MB ONNX), FathomNet VME YOLOv8x, Hakai Kelp-RGB aerial segmentation. Listed under `candidates` in `models.json`.
