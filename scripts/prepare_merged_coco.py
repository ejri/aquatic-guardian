#!/usr/bin/env python3
"""Build a COCO detection dataset for RF-DETR marine fine-tune.

Default remap: every annotation category → single class ``animal`` (id 1).

  --smoke     write a tiny synthetic train/valid set (no downloads)
  --sources   one or more COCO roots (each with train/ and optional valid/)
  --out       output dataset root
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ANIMAL = {"id": 1, "name": "animal", "supercategory": "animal"}


def _write_split(split_dir: Path, images: list[dict], anns: list[dict]) -> None:
    split_dir.mkdir(parents=True, exist_ok=True)
    coco = {
        "info": {"description": "Aquatic Guardian merged marine detection", "version": "0.1"},
        "licenses": [{"id": 1, "name": "see source datasets"}],
        "categories": [ANIMAL],
        "images": images,
        "annotations": anns,
    }
    (split_dir / "_annotations.coco.json").write_text(json.dumps(coco, indent=2))


def make_smoke(out: Path, n_train: int = 12, n_valid: int = 4, size: int = 320) -> None:
    rng = random.Random(0)
    for split, n in (("train", n_train), ("valid", n_valid)):
        images, anns = [], []
        ann_id = 1
        for i in range(n):
            img = Image.new("RGB", (size, size), (4, 40, 55))
            draw = ImageDraw.Draw(img)
            boxes = []
            for _ in range(rng.randint(1, 3)):
                w, h = rng.randint(30, 90), rng.randint(20, 70)
                x0, y0 = rng.randint(5, size - w - 5), rng.randint(5, size - h - 5)
                draw.ellipse([x0, y0, x0 + w, y0 + h], fill=(180, 140, 40))
                boxes.append((x0, y0, w, h))
            name = f"{split}_{i:03d}.jpg"
            path = out / split / name
            path.parent.mkdir(parents=True, exist_ok=True)
            img.save(path, quality=90)
            images.append({"id": i + 1, "file_name": name, "width": size, "height": size})
            for (x0, y0, w, h) in boxes:
                anns.append({
                    "id": ann_id, "image_id": i + 1, "category_id": 1,
                    "bbox": [float(x0), float(y0), float(w), float(h)],
                    "area": float(w * h), "iscrowd": 0,
                })
                ann_id += 1
        _write_split(out / split, images, anns)
    print(f"smoke COCO written to {out}")


def _load_coco(split_dir: Path) -> dict:
    ann = split_dir / "_annotations.coco.json"
    if not ann.is_file():
        # common Roboflow / COCO alternate names
        for alt in ("annotations.json", "instances_default.json"):
            if (split_dir / alt).is_file():
                ann = split_dir / alt
                break
    if not ann.is_file():
        raise FileNotFoundError(f"no COCO json in {split_dir}")
    return json.loads(ann.read_text())


def merge_sources(sources: list[Path], out: Path) -> None:
    for split in ("train", "valid"):
        images, anns = [], []
        next_img, next_ann = 1, 1
        for src in sources:
            split_dir = src / split
            if not split_dir.is_dir():
                # allow flat train-only sources to contribute to train only
                if split == "valid":
                    continue
                split_dir = src
            try:
                coco = _load_coco(split_dir)
            except FileNotFoundError:
                print(f"skip missing annotations: {split_dir}")
                continue
            id_map = {}
            for im in coco.get("images", []):
                src_file = split_dir / im["file_name"]
                if not src_file.is_file():
                    # nested paths
                    alt = split_dir / Path(im["file_name"]).name
                    src_file = alt if alt.is_file() else src_file
                if not src_file.is_file():
                    continue
                new_name = f"{src.name}_{split}_{next_img:06d}{src_file.suffix.lower()}"
                dest = out / split / new_name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dest)
                id_map[im["id"]] = next_img
                images.append({
                    "id": next_img, "file_name": new_name,
                    "width": im.get("width", 0), "height": im.get("height", 0),
                })
                next_img += 1
            for a in coco.get("annotations", []):
                if a.get("iscrowd"):
                    continue
                img_id = id_map.get(a["image_id"])
                if img_id is None:
                    continue
                bbox = a.get("bbox") or []
                if len(bbox) != 4:
                    continue
                anns.append({
                    "id": next_ann, "image_id": img_id, "category_id": 1,
                    "bbox": [float(x) for x in bbox],
                    "area": float(a.get("area") or bbox[2] * bbox[3]),
                    "iscrowd": 0,
                })
                next_ann += 1
        if not images and split == "valid" and (out / "train").is_dir():
            # duplicate a few train images as valid if no valid split existed
            continue
        if images:
            _write_split(out / split, images, anns)
            print(f"{split}: {len(images)} images, {len(anns)} boxes → {out / split}")
    # ensure valid exists
    if not (out / "valid" / "_annotations.coco.json").is_file() and (out / "train").is_dir():
        train_ann = json.loads((out / "train" / "_annotations.coco.json").read_text())
        # take up to 10% / min 2 images
        n = max(2, len(train_ann["images"]) // 10)
        keep = {im["id"] for im in train_ann["images"][:n]}
        v_imgs, v_anns = [], []
        for im in train_ann["images"][:n]:
            src = out / "train" / im["file_name"]
            dest = out / "valid" / im["file_name"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            if src.is_file():
                shutil.copy2(src, dest)
            v_imgs.append(im)
        aid = 1
        for a in train_ann["annotations"]:
            if a["image_id"] in keep:
                b = dict(a); b["id"] = aid; aid += 1
                v_anns.append(b)
        _write_split(out / "valid", v_imgs, v_anns)
        print(f"valid: carved {len(v_imgs)} images from train")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--sources", nargs="*", type=Path, default=[])
    ap.add_argument("--out", type=Path, default=ROOT / "models" / "train" / "data" / "merged")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if args.smoke:
        make_smoke(args.out)
        return
    if not args.sources:
        raise SystemExit("pass --sources DIR [DIR ...] or --smoke")
    merge_sources([p.resolve() for p in args.sources], args.out.resolve())


if __name__ == "__main__":
    main()
