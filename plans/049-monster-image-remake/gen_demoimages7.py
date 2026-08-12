#!/usr/bin/env python3
"""049: bright-world 1-bit, take 2 -> demoimages7/.

Fixes demoimages6's flaws (solid-black terrain masses; broken-up
characters): retinex-style illumination normalization. Each pixel is
divided by a heavy gaussian blur of the scene, so LARGE dark regions
(terrain shadow) flatten to the local average and land in the bright
dither band, while SMALL locally-dark blobs — the characters — stay
below the black threshold and render as solid black silhouettes.

Formula (lab round 7, tactic f of e-h):
  crop 320x112 -> median-3 -> autocontrast
  n = luma / gaussian_blur(luma, 16)
  n < 0.65        -> pure black (silhouettes)
  else            -> 165..255 shades-of-white band, Bayer 8x8

Default run: a 10-image review sample — the first 10 monsters in
floor order, cycling through all 9 player-weapon combos so every
character and weapon appears. Pass explicit names for other files.

Usage:
  python plans/049-monster-image-remake/gen_demoimages7.py [name ...]
"""

from __future__ import annotations

import glob
import os
import sys

import numpy as np
from PIL import Image, ImageFilter, ImageOps

_HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(_HERE, "demoimages4")
OUT = os.path.join(_HERE, "demoimages7")

W, H = 320, 112
SCALE = 2

RADIUS = 16       # illumination-estimate blur
BLACK_N = 0.65    # below this fraction of local average -> silhouette
FLOOR = 165       # background band lower bound (shades of white only)
SPAN = 0.9        # n range mapped across the band

BAYER8 = np.array([
    [0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44, 4, 36, 14, 46, 6, 38], [60, 28, 52, 20, 62, 30, 54, 22],
    [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21],
]) / 64.0

SAMPLE_COUNT = 10


def to_1bit(img: Image.Image) -> Image.Image:
    img = img.convert("L")
    iw, ih = img.size
    target = W / H
    if iw / ih > target:
        nw = int(ih * target)
        img = img.crop(((iw - nw) // 2, 0, (iw + nw) // 2, ih))
    else:
        nh = int(iw / target)
        img = img.crop((0, (ih - nh) // 2, iw, (ih + nh) // 2))
    img = img.resize((W, H), Image.LANCZOS)
    img = img.filter(ImageFilter.MedianFilter(3))
    img = ImageOps.autocontrast(img, cutoff=2)
    a = np.asarray(img, dtype=np.float64) + 1
    lo = np.asarray(img.filter(ImageFilter.GaussianBlur(RADIUS)),
                    dtype=np.float64) + 1
    n = a / lo
    bright = FLOOR + np.clip((n - BLACK_N) / SPAN, 0, 1) * (255 - FLOOR)
    v = np.where(n < BLACK_N, 0, bright) / 255.0
    ty, tx = np.indices(v.shape)
    bits = np.where(v > BAYER8[ty % 8, tx % 8], 255, 0).astype(np.uint8)
    out = Image.fromarray(bits).convert("RGB")
    return out.resize((W * SCALE, H * SCALE), Image.NEAREST)


def sample_names() -> list[str]:
    """First SAMPLE_COUNT monsters in floor order, cycling the 9 combos."""
    combos = [f"{c}_{w}"
              for c in ("fighter", "elf", "giant")
              for w in ("wand", "bow", "sword")]
    monsters, seen = [], set()
    for path in sorted(glob.glob(os.path.join(SRC, "*.jpg"))):
        m = "_".join(os.path.basename(path).split("_")[:-2])
        if m not in seen:
            seen.add(m)
            monsters.append(m)
    return [f"{m}_{combos[i % len(combos)]}"
            for i, m in enumerate(monsters[:SAMPLE_COUNT])]


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    names = sys.argv[1:] or sample_names()
    for name in names:
        to_1bit(Image.open(os.path.join(SRC, f"{name}.jpg"))).save(
            os.path.join(OUT, f"{name}.png"))
        print(f"ok   {name}", flush=True)
    print(f"{len(names)} converted -> {OUT}")


if __name__ == "__main__":
    main()
