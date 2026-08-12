#!/usr/bin/env python3
"""049: floor1/ plan assets -> the game's content/art/ formats.

  closeups/{id}.jpg              -> creatures/{id}_320x112.png
  movies/{id}_{race}_{line}.mp4  -> events/{id}_{verb}_{race}_{line}_320x112.gif

The encounter banner is the CLOSEUP — the monster alone (roy,
2026-08-12). The staged scenes are movie first-frames only and never
ship as creatures/ art; the scenes mode was removed.

Game spec (tools/generate_banners.py / generate_event_gifs.py): white
ink on alpha at 1x 320x112; GIFs palette index 0 transparent / 1 white,
play once (no loop extension), disposal 2. "warden" maps to warden_001.
Demo names map fighter->human, wand->staff, sword->blade.

Usage:
  python gen_floor1_game.py [closeups|movies ...]   (default all)
"""

from __future__ import annotations

import os
import sys

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageOps

_HERE = os.path.dirname(os.path.abspath(__file__))
FLOOR1 = os.path.join(_HERE, "floor1")
ART = os.path.join(_HERE, "..", "..", "plugin_linear_ascent",
                   "content", "art")

W, H = 320, 112
GIF_FPS = 10
BAYER8 = np.array([
    [0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44, 4, 36, 14, 46, 6, 38], [60, 28, 52, 20, 62, 30, 54, 22],
    [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21],
])

IDS = ["grey_wolf", "feral_boar", "hedge_rat", "lane_wolf",
       "goblin_straggler", "ember_shade", "warden"]
GAME_ID = {m: ("warden_001" if m == "warden" else m) for m in IDS}
VERB = {"grey_wolf": "freed", "feral_boar": "freed", "hedge_rat": "freed",
        "lane_wolf": "freed", "goblin_straggler": "fall",
        "ember_shade": "evicted", "warden": "evicted"}
RACES = {"human": "fighter", "elf": "elf", "dwarf": "dwarf"}
LINES = {"blade": "sword", "bow": "bow", "staff": "wand"}


def to_bits(img: Image.Image) -> np.ndarray:
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
    a = np.asarray(img, dtype=np.float64)
    ty, tx = np.indices(a.shape)
    return (a / 255 > (BAYER8[ty % 8, tx % 8] + 0.5) / 64)


def bits_to_ink_png(bits: np.ndarray, path: str) -> None:
    """White ink on alpha, 1x."""
    rgba = np.zeros((H, W, 4), dtype=np.uint8)
    rgba[bits] = (255, 255, 255, 255)
    Image.fromarray(rgba).save(path)


def save_ink_gif(frames: list[np.ndarray], path: str,
                 durations: list[int]) -> None:
    """Palette 0=transparent 1=white, play once, disposal 2."""
    pal = [0, 0, 0, 255, 255, 255] + [0, 0, 0] * 254
    pframes = []
    for bits in frames:
        p = Image.fromarray(bits.astype(np.uint8), mode="P")
        p.putpalette(pal)
        pframes.append(p)
    pframes[0].save(path, save_all=True, append_images=pframes[1:],
                    duration=durations, transparency=0, disposal=2)


def do_closeups() -> None:
    for m in IDS:
        src = os.path.join(FLOOR1, "closeups", f"{m}.jpg")
        dst = os.path.join(ART, "creatures", f"{GAME_ID[m]}_320x112.png")
        bits_to_ink_png(to_bits(Image.open(src)), dst)
        print(f"ok   creatures/{os.path.basename(dst)}", flush=True)


def do_movies() -> None:
    n = 0
    for m in IDS:
        for race in RACES:
            for line in LINES:
                src = os.path.join(FLOOR1, "movies",
                                   f"{m}_{race}_{line}.mp4")
                if not os.path.exists(src):
                    print(f"MISS {os.path.basename(src)}", flush=True)
                    continue
                dst = os.path.join(
                    ART, "events",
                    f"{GAME_ID[m]}_{VERB[m]}_{race}_{line}_320x112.gif")
                reader = imageio.get_reader(src)
                fps = reader.get_meta_data().get("fps", 24)
                step = max(1, round(fps / GIF_FPS))
                frames = [to_bits(Image.fromarray(f))
                          for i, f in enumerate(reader) if i % step == 0]
                reader.close()
                durations = [int(1000 * step / fps)] * len(frames)
                durations[-1] = 2000
                save_ink_gif(frames, dst, durations)
                n += 1
    print(f"ok   {n} event gifs", flush=True)


if __name__ == "__main__":
    modes = sys.argv[1:] or ["closeups", "movies"]
    for mode in modes:
        {"closeups": do_closeups, "movies": do_movies}[mode]()
