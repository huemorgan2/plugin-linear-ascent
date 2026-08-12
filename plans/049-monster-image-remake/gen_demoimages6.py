#!/usr/bin/env python3
"""049: inverted 1-bit design -> demoimages6/.

Opposite tonal design from demoimages5 (dark world, bright rims):
here the BACKGROUND is bright and dither-shaded and the characters
read as DARK SILHOUETTES. Formula (lab round 5, tactic V):

  1. center-crop to 320x112, LANCZOS downscale
  2. median-3 denoise, autocontrast (cutoff 2)
  3. gamma 0.4 lift — midtone landscape rises into bright dither
  4. hard black floor — luma < 55 clamps to pure black, so figures
     (and deep shadow shapes) become solid silhouettes
  5. ordered Bayer 8x8 dither, saved at 2x nearest (640x224)

Already-converted files are skipped, so rerunning fills gaps.

Usage:
  python plans/049-monster-image-remake/gen_demoimages6.py [name ...]
"""

from __future__ import annotations

import glob
import os
import sys

import numpy as np
from PIL import Image, ImageFilter, ImageOps

_HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(_HERE, "demoimages4")
OUT = os.path.join(_HERE, "demoimages6")

W, H = 320, 112
SCALE = 2

LIFT = 0.4        # gamma < 1 brightens the landscape
BLACK = 55        # luma below this becomes solid silhouette black

BAYER8 = np.array([
    [0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44, 4, 36, 14, 46, 6, 38], [60, 28, 52, 20, 62, 30, 54, 22],
    [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21],
]) / 64.0


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
    a = np.asarray(img, dtype=np.float64)
    lifted = 255 * (a / 255) ** LIFT
    v = np.where(a < BLACK, 0, lifted) / 255.0
    ty, tx = np.indices(v.shape)
    bits = np.where(v > BAYER8[ty % 8, tx % 8], 255, 0).astype(np.uint8)
    out = Image.fromarray(bits).convert("RGB")
    return out.resize((W * SCALE, H * SCALE), Image.NEAREST)


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    want = set(sys.argv[1:])
    n = 0
    for path in sorted(glob.glob(os.path.join(SRC, "*.jpg"))):
        name = os.path.splitext(os.path.basename(path))[0]
        if want and name not in want:
            continue
        dst = os.path.join(OUT, f"{name}.png")
        if not want and os.path.exists(dst):
            continue
        to_1bit(Image.open(path)).save(dst)
        n += 1
    print(f"{n} converted -> {OUT}")


if __name__ == "__main__":
    main()
