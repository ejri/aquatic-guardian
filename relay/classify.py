"""Hierarchical taxon naming for Live ocean track crops (relay Stage B).

Browser finds and tracks animals; this module names a track when calibrated
confidence supports it, otherwise returns a broad display group.

Backend: BioCLIP 2 (MIT, imageomics/bioclip-2) when ``AG_BIOCLIP=1`` and
open_clip can load the checkpoint; otherwise a deterministic stub.
Thresholds live in ``relay/calibration/bioclip_thresholds.json``.
"""
from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

HERE = Path(__file__).parent
CALIB_PATH = HERE / "calibration" / "bioclip_thresholds.json"
log = logging.getLogger("ag.classify")

DISPLAY_GROUPS: List[str] = [
    "Fish", "Shark", "Ray", "Sea turtle", "Marine mammal", "Eel",
    "Octopus/squid/cuttlefish", "Crab/lobster/shrimp", "Sea star/urchin/cucumber",
    "Jellyfish", "Coral/sponge/sea fan", "Other animal",
]

_BIOCLIP: Optional[Tuple[Any, Any, Any]] = None  # model, preprocess, tokenizer


@lru_cache(maxsize=1)
def load_calibration() -> Dict[str, Any]:
    if CALIB_PATH.is_file():
        return json.loads(CALIB_PATH.read_text())
    return {"threshold": 0.7, "display_groups": DISPLAY_GROUPS, "status": "missing"}


def default_threshold() -> float:
    return float(load_calibration().get("threshold", 0.7))


def bioclip_enabled() -> bool:
    return os.environ.get("AG_BIOCLIP", "").strip() == "1"


def map_class(raw: str) -> str:
    s = (raw or "").lower().replace("_", " ").strip()
    if not s or s in {"moving object", "animal", "object"}:
        return "Other animal"
    if "shark" in s:
        return "Shark"
    if "ray" in s or "skate" in s:
        return "Ray"
    if "turtle" in s:
        return "Sea turtle"
    if any(k in s for k in ("whale", "dolphin", "seal", "otter", "mammal")):
        return "Marine mammal"
    if "eel" in s:
        return "Eel"
    if any(k in s for k in ("octopus", "squid", "cuttle", "cephalopod")):
        return "Octopus/squid/cuttlefish"
    if any(k in s for k in ("crab", "lobster", "shrimp", "prawn", "decapod")):
        return "Crab/lobster/shrimp"
    if any(k in s for k in ("star", "urchin", "cucumber", "echinoderm")):
        return "Sea star/urchin/cucumber"
    if "jelly" in s:
        return "Jellyfish"
    if any(k in s for k in ("coral", "sponge", "fan")):
        return "Coral/sponge/sea fan"
    if any(k in s for k in ("fish", "salmon", "trout", "bass", "cod", "grouper", "snapper", "parrot")):
        return "Fish"
    return "Other animal"


def hierarchical_label(
    scores: Dict[str, float],
    *,
    threshold: Optional[float] = None,
    species_list: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """Pick the deepest taxonomic string whose score passes ``threshold``."""
    thr = default_threshold() if threshold is None else threshold
    if not scores:
        return {
            "label": "Animal, unidentified", "group": "Other animal",
            "level": "unknown", "score": 0.0, "backend": "ladder",
        }

    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], -len(kv[0])))
    for name, score in ranked:
        if score < thr:
            continue
        group = map_class(name)
        level = "group" if name in DISPLAY_GROUPS else ("species" if " " in name else "taxon")
        if species_list and name not in species_list and level == "species":
            return {
                "label": f"Unusual for this camera — {name}",
                "group": group, "level": level, "score": float(score),
                "backend": "ladder", "regional": "down-weighted visitor",
            }
        label = name if level != "group" else (name if score >= 0.9 else f"{name}, unidentified")
        return {
            "label": label, "group": group, "level": level,
            "score": float(score), "backend": "ladder",
        }

    group_scores = {g: scores.get(g, 0.0) for g in DISPLAY_GROUPS}
    for raw, sc in scores.items():
        g = map_class(raw)
        group_scores[g] = max(group_scores.get(g, 0.0), sc)
    best_group = max(group_scores, key=group_scores.get)
    return {
        "label": f"{best_group}, unidentified",
        "group": best_group, "level": "group",
        "score": float(group_scores[best_group]), "backend": "ladder",
    }


def _load_bioclip() -> Optional[Tuple[Any, Any, Any]]:
    """Load BioCLIP 2 once per process. Returns (model, preprocess, tokenizer)."""
    global _BIOCLIP
    if _BIOCLIP is not None:
        return _BIOCLIP
    if not bioclip_enabled():
        return None
    try:
        import open_clip
        import torch
    except ImportError as e:
        log.warning("BioCLIP deps missing (%s); stub naming only", e)
        return None
    try:
        model, _, preprocess = open_clip.create_model_and_transforms(
            "hf-hub:imageomics/bioclip-2"
        )
        tokenizer = open_clip.get_tokenizer("hf-hub:imageomics/bioclip-2")
        model.eval()
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            model = model.to("mps")
        _BIOCLIP = (model, preprocess, tokenizer)
        log.info("BioCLIP 2 loaded (AG_BIOCLIP=1)")
        return _BIOCLIP
    except Exception as e:
        log.warning("BioCLIP 2 failed to load: %s", e)
        return None


def warmup_bioclip() -> bool:
    """Eagerly load weights so the first classify call is not cold."""
    return _load_bioclip() is not None


def _bioclip_scores(image_bytes: bytes, prompts: Sequence[str]) -> Optional[Dict[str, float]]:
    """Zero-shot BioCLIP 2 via open_clip. Returns None if weights unavailable."""
    if not bioclip_enabled() or not image_bytes:
        return None
    packed = _load_bioclip()
    if packed is None:
        return None
    model, preprocess, tokenizer = packed
    try:
        import io
        import torch
        from PIL import Image

        device = next(model.parameters()).device
        img = preprocess(Image.open(io.BytesIO(image_bytes)).convert("RGB")).unsqueeze(0).to(device)
        text = tokenizer(list(prompts)).to(device)
        with torch.no_grad():
            image_features = model.encode_image(img)
            text_features = model.encode_text(text)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            logits = (100.0 * image_features @ text_features.T).softmax(dim=-1)[0]
        return {p: float(logits[i].detach().cpu()) for i, p in enumerate(prompts)}
    except Exception as e:
        log.warning("BioCLIP inference failed: %s", e)
        return None


def classify_crop(
    image_bytes: bytes,
    *,
    species_list: Optional[Sequence[str]] = None,
    threshold: Optional[float] = None,
) -> Dict[str, Any]:
    thr = default_threshold() if threshold is None else threshold
    prompts: List[str] = list(DISPLAY_GROUPS)
    if species_list:
        prompts = list(species_list) + prompts
    scores = _bioclip_scores(image_bytes, prompts)
    if scores is not None:
        out = hierarchical_label(scores, threshold=thr, species_list=species_list)
        out["backend"] = "bioclip-2"
        out["calibration"] = load_calibration().get("status")
        return out
    return {
        "label": "Animal, unidentified",
        "group": "Other animal",
        "level": "group",
        "score": 0.0,
        "backend": "stub",
        "calibration": load_calibration().get("status"),
        "note": "BioCLIP 2 not loaded (set AG_BIOCLIP=1 and install open_clip); broad label only.",
    }


def classify_tracks(
    crops: Sequence[Dict[str, Any]],
    *,
    species_list: Optional[Sequence[str]] = None,
    threshold: Optional[float] = None,
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for crop in crops:
        raw = crop.get("image_bytes") or crop.get("bytes") or b""
        result = classify_crop(raw, species_list=species_list, threshold=threshold)
        result["track_id"] = crop.get("track_id")
        out.append(result)
    return out
