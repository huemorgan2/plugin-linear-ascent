#!/usr/bin/env python3
"""049: render demoimages4/ into 1-bit -> demoimages4_1bit/.

Same discipline as tools/generate_creatures.py: center-crop to the
game banner ratio, downscale to 320x112, autocontrast, ordered Bayer
8x8 dither, white ink on black. Saved at 2x nearest-neighbour
(640x224) so the demos are easy to eyeball; pixels stay 1-bit true.

Already-converted files are skipped, so rerunning fills gaps.

Usage:
  python plans/049-monster-image-remake/gen_demoimages4_1bit.py [name ...]
"""

from __future__ import annotations

import glob
import os
import sys

from PIL import Image, ImageOps

_HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(_HERE, "demoimages4")
OUT = os.path.join(_HERE, "demoimages4_1bit")

W, H = 320, 112
SCALE = 2

BAYER = [
    [0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44, 4, 36, 14, 46, 6, 38], [60, 28, 52, 20, 62, 30, 54, 22],
    [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21],
]


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
    img = ImageOps.autocontrast(img, cutoff=1)
    px = img.load()
    out = Image.new("RGB", (W, H), (0, 0, 0))
    po = out.load()
    for y in range(H):
        for x in range(W):
            if px[x, y] / 255 > (BAYER[y % 8][x % 8] + 0.5) / 64:
                po[x, y] = (255, 255, 255)
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
        print(f"ok   {name}", flush=True)
    print(f"{n} converted -> {OUT}")


if __name__ == "__main__":
    main()
