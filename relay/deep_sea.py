"""Server-side detectors for cameras tagged deep / benthic (audit P2).

Intended weights (not bundled — too large for the browser path):
- FathomNet Megalodon: class-agnostic \"object\" (YOLOv8x; Ultralytics AGPL — check card)
- 2025 MBARI Benthic Supercategory: 29 groups (CC BY 4.0 on card)

Set AG_DEEP_SEA_WEIGHTS to a local .pt/.onnx path to enable. Until then the
endpoint returns a clear unavailable payload so Live ocean can fall back.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional


SUPPORTED = {
    "megalodon": {
        "label": "FathomNet Megalodon",
        "url": "https://huggingface.co/FathomNet/megalodon",
        "classes": ["object"],
    },
    "mbari_benthic_2025": {
        "label": "2025 MBARI Benthic Supercategory",
        "url": "https://huggingface.co/FathomNet/2025-MBARI-Benthic-Supercategory-Object-Detector",
        "classes": 29,
    },
}


def available_backend() -> Optional[str]:
    path = os.environ.get("AG_DEEP_SEA_WEIGHTS")
    if path and Path(path).is_file():
        return os.environ.get("AG_DEEP_SEA_MODEL", "megalodon")
    return None


def detect_frame(_image_bytes: bytes, *, model: str = "megalodon") -> Dict[str, Any]:
    backend = available_backend()
    if not backend:
        return {
            "ok": False,
            "detections": [],
            "backend": None,
            "note": "Deep-sea weights not configured. Set AG_DEEP_SEA_WEIGHTS to a local checkpoint.",
            "candidates": SUPPORTED,
        }
    # Real inference is operator-local; keep the contract stable for the relay API.
    return {
        "ok": True,
        "detections": [],
        "backend": backend,
        "model": model if model in SUPPORTED else backend,
        "note": "Weights present; wire ultralytics/onnxruntime locally before relying on boxes.",
    }


def sam_audit_stub(prompts: Optional[List[str]] = None) -> Dict[str, Any]:
    """Offline SAM 3.1 text-prompt audit hook (audit P2). GPU-only; not for live."""
    return {
        "ok": False,
        "prompts": prompts or ["fish", "sea turtle", "ray", "octopus"],
        "note": "SAM 3.1 is offline-only for auditing the browser detector. Not wired in this build.",
    }
