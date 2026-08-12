#!/usr/bin/env python3
"""049: enforce one scale across the player renders.

The model won't hold a figure size across generations, so it is done
here: the background is pure black, so the figure's bounding box is
measurable. Humans (fighter, elf) are scaled to one common height,
the giant to 1.3x of it (two heads taller), everyone bottom-aligned
on the same ground line and centered. Overwrites demo-players/*.jpg.
"""

from __future__ import annotations

import glob
import os

from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(_HERE, "demo-players")

THRESH = 14          # >this luma = figure, not background
HUMAN_H = 0.58       # figure height as share of frame height
GIANT_H = 0.58 * 1.3
BASELINE = 0.92      # figure feet sit at this share of frame height


def bbox(img: Image.Image) -> tuple[int, int, int, int]:
    mask = img.convert("L").point(lambda p: 255 if p > THRESH else 0)
    box = mask.getbbox()
    if box is None:
        raise SystemExit("empty image")
    return box


def normalize(path: str) -> None:
    img = Image.open(path).convert("RGB")
    w, h = img.size
    x0, y0, x1, y1 = bbox(img)
    share = GIANT_H if os.path.basename(path).startswith("giant") else HUMAN_H
    f = (share * h) / (y1 - y0)
    img = img.resize((round(w * f), round(h * f)), Image.LANCZOS)
    sx0, sy0, sx1, sy1 = (round(v * f) for v in (x0, y0, x1, y1))
    canvas = Image.new("RGB", (w, h), (0, 0, 0))
    px = round(w / 2 - (sx0 + sx1) / 2)
    py = round(BASELINE * h - sy1)
    canvas.paste(img, (px, py))
    canvas.save(path, quality=95)
    print(f"ok   {os.path.basename(path)}  figure {y1 - y0}px -> "
          f"{round(share * h)}px")


if __name__ == "__main__":
    for path in sorted(glob.glob(os.path.join(OUT, "*.jpg"))):
        normalize(path)
