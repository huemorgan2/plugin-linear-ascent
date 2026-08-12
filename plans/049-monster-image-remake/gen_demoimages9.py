#!/usr/bin/env python3
"""049: outline-style 1-bit iteration pair -> demoimages9/.

One outlined render (from demoimages8/) plus its 1-bit conversion,
side by side in one folder, for fast formula iteration.

Formula (lab9, tactic E): thicken the ink lines at FULL resolution
(MinFilter DILATE) so they survive the downscale, then at 320x112:
line pixels (luma < LINE) -> solid black, everything else -> bright
dither band (FLOOR..255) from the undilated tone, Bayer 8x8.

Usage:
  python plans/049-monster-image-remake/gen_demoimages9.py [name ...]
"""

from __future__ import annotations

import os
import shutil
import sys

import numpy as np
from PIL import Image, ImageFilter, ImageOps

_HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(_HERE, "demoimages8")
OUT = os.path.join(_HERE, "demoimages9")

W, H = 320, 112
SCALE = 2

DILATE = 9     # ink-line thickening at full res (MinFilter size, odd)
LINE = 60      # luma below this (after dilation) -> solid black line
FLOOR = 140    # background band lower bound

NAMES = ["floor001_goblin_straggler_fighter_sword"]

BAYER8 = np.array([
    [0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44, 4, 36, 14, 46, 6, 38], [60, 28, 52, 20, 62, 30, 54, 22],
    [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21],
]) / 64.0


def crop(img: Image.Image) -> Image.Image:
    iw, ih = img.size
    t = W / H
    if iw / ih > t:
        nw = int(ih * t)
        return img.crop(((iw - nw) // 2, 0, (iw + nw) // 2, ih))
    nh = int(iw / t)
    return img.crop((0, (ih - nh) // 2, iw, (ih + nh) // 2))


def to_1bit(img: Image.Image) -> Image.Image:
    full = ImageOps.autocontrast(crop(img.convert("L")), cutoff=2)
    thick = full.filter(ImageFilter.MinFilter(DILATE))
    a = np.asarray(thick.resize((W, H), Image.LANCZOS), dtype=np.float64)
    t = np.asarray(full.resize((W, H), Image.LANCZOS), dtype=np.float64)
    bright = FLOOR + (t / 255) * (255 - FLOOR)
    v = np.where(a < LINE, 0, bright) / 255.0
    ty, tx = np.indices(v.shape)
    bits = np.where(v > BAYER8[ty % 8, tx % 8], 255, 0).astype(np.uint8)
    out = Image.fromarray(bits).convert("RGB")
    return out.resize((W * SCALE, H * SCALE), Image.NEAREST)


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    for name in sys.argv[1:] or NAMES:
        src = os.path.join(SRC, f"{name}.jpg")
        shutil.copyfile(src, os.path.join(OUT, f"{name}__original.jpg"))
        to_1bit(Image.open(src)).save(os.path.join(OUT, f"{name}__1bit.png"))
        print(f"ok   {name}", flush=True)


if __name__ == "__main__":
    main()
