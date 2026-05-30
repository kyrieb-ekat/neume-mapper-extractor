#!/usr/bin/env python3
"""Crop neume bounding boxes from local manuscript page images.

Reads corrected JSON annotations from neume_punching_v11 subdirectories and
saves each annotated region as a PNG named SG{manuscript}_{page}_{box:03d}.png.
"""

import argparse
import json
import re
import sys
from glob import glob
from pathlib import Path

from PIL import Image

DEFAULT_INPUT = (
    "/Users/ekaterina/Documents/Documents_angantyr/muscrat/tools/neume_punching_v11"
)
DEFAULT_OUTPUT = (
    "/Users/ekaterina/Documents/Documents_angantyr/muscrat/experiments"
    "/exp_neume_crops_cross_manuscript/neume_crops340"
)

# Matches e.g. "SGCod340_56.jpg" or "SGCod340_48_v11.jpg"
FILENAME_RE = re.compile(r"SGCod(\d+)_(\d+)", re.IGNORECASE)


def parse_args():
    p = argparse.ArgumentParser(description="Crop neumes from local corrected JSON annotations.")
    p.add_argument("--input-dir", default=DEFAULT_INPUT)
    p.add_argument("--output-dir", default=DEFAULT_OUTPUT)
    return p.parse_args()


def crop_page(subdir: Path, output_dir: Path) -> int:
    json_matches = list(subdir.glob("corrected/*_corrected.json"))
    if not json_matches:
        print(f"  WARNING: no corrected JSON found in {subdir.name}, skipping.")
        return 0

    json_path = json_matches[0]
    with open(json_path) as f:
        data = json.load(f)

    image_name = data.get("imageName", "")
    m = FILENAME_RE.search(image_name)
    if not m:
        print(f"  WARNING: cannot parse manuscript/page from '{image_name}', skipping.")
        return 0

    manuscript, page = m.group(1), m.group(2)
    img_width = data.get("imageWidth", 0)
    img_height = data.get("imageHeight", 0)

    img_path = subdir / image_name
    if not img_path.exists():
        print(f"  ERROR: image not found: {img_path}", file=sys.stderr)
        return 0

    img = Image.open(img_path).convert("RGB")
    # Use actual image dimensions for clamping
    w_img, h_img = img.size

    annotations = data.get("annotations", [])
    saved = 0
    for idx, ann in enumerate(annotations, start=1):
        bbox = ann.get("bbox")
        if not bbox or len(bbox) < 4:
            continue
        x, y, w, h = bbox
        # Clamp to image bounds
        x1 = max(0, int(x))
        y1 = max(0, int(y))
        x2 = min(w_img, int(x + w))
        y2 = min(h_img, int(y + h))
        if x2 <= x1 or y2 <= y1:
            continue
        crop = img.crop((x1, y1, x2, y2))
        filename = f"SG{manuscript}_{page}_{idx:03d}.png"
        crop.save(output_dir / filename)
        saved += 1

    return saved


def main():
    args = parse_args()
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    if not input_dir.is_dir():
        print(f"ERROR: input directory not found: {input_dir}", file=sys.stderr)
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    subdirs = sorted(p for p in input_dir.iterdir() if p.is_dir())
    if not subdirs:
        print("No subdirectories found in input directory.", file=sys.stderr)
        sys.exit(1)

    total = 0
    for subdir in subdirs:
        n = crop_page(subdir, output_dir)
        if n:
            print(f"  {subdir.name}: {n} crops saved")
        total += n

    print(f"\nDone. {total} crops saved to {output_dir}")


if __name__ == "__main__":
    main()
