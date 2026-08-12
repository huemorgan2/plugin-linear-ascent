#!/usr/bin/env python3
"""049 demo: every player x weapon x monster composite -> demoimages3/.

No model calls. The player renders sit on a pure black background, so
the figure is keyed out deterministically (threshold + flood-fill of
the border-connected background, which keeps dark armor interiors) and
pasted into the monster scene from demoimages2/ at the edge opposite
the monster, facing it, feet on the scene's ground line.

3 players x 3 weapons x 14 monsters = 126 images, named
  {player}_{weapon}_vs_{floorN}_{monster}.jpg

Usage:
  python plans/049-monster-image-remake/gen_demoimages3.py [name ...]
"""

from __future__ import annotations

import glob
import os
import sys

import numpy as np
import yaml
from PIL import Image, ImageFilter

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..", "..")
FLOORS = os.path.join(_ROOT, "plugin_linear_ascent", "content", "floors")
PLAYERS = os.path.join(_HERE, "demo-players")
MONSTERS = os.path.join(_HERE, "demoimages2")
OUT = os.path.join(_HERE, "demoimages3")

DARK = 18            # <=this luma can be background
SCALE = 0.62         # player size relative to their normalized render
MARGIN = 0.03        # player distance from the frame edge, share of width
BASELINE = 0.90      # player feet at this share of scene height


def monster_sides() -> dict[str, str]:
    """Rebuild the LEFT/RIGHT edge each monster was prompted to, in the
    same job order gen_demoimages.py used (parity of the running index)."""
    sides, i = {}, 0
    for path in sorted(glob.glob(os.path.join(FLOORS, "floor_*.yaml"))):
        d = yaml.safe_load(open(path))
        if d["floor"] not in (1, 2):
            continue
        for e in d["encounters"]:
            sides[f"floor{d['floor']}_{e['id']}"] = "LEFT" if i % 2 else "RIGHT"
            i += 1
        sides[f"floor{d['floor']}_warden"] = "LEFT" if i % 2 else "RIGHT"
        i += 1
    return sides


def figure_cutout(path: str) -> tuple[Image.Image, Image.Image]:
    """Key the figure off the black background. Background = dark pixels
    connected to the frame border (numpy flood-fill by iterative
    dilation), so dark areas inside the silhouette stay with the figure."""
    img = Image.open(path).convert("RGB")
    luma = np.asarray(img.convert("L"))
    dark = luma <= DARK
    bg = np.zeros_like(dark)
    bg[0, :] = dark[0, :]
    bg[-1, :] = dark[-1, :]
    bg[:, 0] = dark[:, 0]
    bg[:, -1] = dark[:, -1]
    while True:
        grown = bg.copy()
        grown[1:, :] |= bg[:-1, :]
        grown[:-1, :] |= bg[1:, :]
        grown[:, 1:] |= bg[:, :-1]
        grown[:, :-1] |= bg[:, 1:]
        grown &= dark
        if (grown == bg).all():
            break
        bg = grown
    mask = Image.fromarray(np.where(bg, 0, 255).astype(np.uint8))
    # shave a pixel so no black halo rides along, then soften the edge
    mask = mask.filter(ImageFilter.MinFilter(3))
    mask = mask.filter(ImageFilter.GaussianBlur(1.2))
    box = mask.getbbox()
    return img.crop(box), mask.crop(box)


def composite(scene_path: str, fig: Image.Image, mask: Image.Image,
              monster_side: str, out_path: str) -> None:
    scene = Image.open(scene_path).convert("RGB")
    w, h = scene.size
    f = SCALE
    fig = fig.resize((round(fig.width * f), round(fig.height * f)),
                     Image.LANCZOS)
    mask = mask.resize(fig.size, Image.LANCZOS)
    if monster_side == "LEFT":       # player goes right, turns to face left
        fig = fig.transpose(Image.FLIP_LEFT_RIGHT)
        mask = mask.transpose(Image.FLIP_LEFT_RIGHT)
        px = round(w * (1 - MARGIN)) - fig.width
    else:                            # monster right: player left, faces right
        px = round(w * MARGIN)
    py = round(h * BASELINE) - fig.height
    scene.paste(fig, (px, py), mask)
    scene.save(out_path, quality=92)


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    sides = monster_sides()
    scenes = sorted(glob.glob(os.path.join(MONSTERS, "*.jpg")))
    players = sorted(glob.glob(os.path.join(PLAYERS, "*.jpg")))
    want = set(sys.argv[1:])
    n = 0
    for ppath in players:
        pw = os.path.splitext(os.path.basename(ppath))[0]  # fighter_sword
        fig, mask = figure_cutout(ppath)
        for spath in scenes:
            mslug = os.path.splitext(os.path.basename(spath))[0]
            name = f"{pw}_vs_{mslug}"
            if want and name not in want:
                continue
            composite(spath, fig, mask, sides[mslug],
                      os.path.join(OUT, f"{name}.jpg"))
            n += 1
        print(f"ok   {pw} x {len(scenes)}", flush=True)
    print(f"{n} composites -> {OUT}")


if __name__ == "__main__":
    main()
