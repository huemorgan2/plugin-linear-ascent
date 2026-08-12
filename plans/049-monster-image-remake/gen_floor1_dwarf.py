#!/usr/bin/env python3
"""049: the dwarf third of floor 1 -> floor1/.

The game's races are human / elf / dwarf (economy.RACES) — the demo
"giant" was never a game race. This builds the dwarf player and its 21
scenes (7 monsters x wand/bow/sword) by swapping the player figure
inside the EXISTING 1-bit fighter scenes via two-reference edit.

  players:  floor1/dwarf-player/dwarf_{weapon}.jpg     (black-bg render)
  scenes:   floor1/scenes/floor001_{id}_dwarf_{weapon}.jpg  + _1bit.png

Usage:
  python gen_floor1_dwarf.py players
  python gen_floor1_dwarf.py scenes [slug ...]
Key: LUNA_GEMINI_API_KEY from env, falling back to ../../luna/.env.
"""

from __future__ import annotations

import asyncio
import importlib.util
import os
import sys

import numpy as np
from PIL import Image, ImageOps

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..", "..")
SCENES = os.path.join(_HERE, "floor1", "scenes")
PLAYERS = os.path.join(_HERE, "floor1", "dwarf-player")

_prov = os.path.join(_ROOT, "..", "plugin-image-gen",
                     "plugin_image_gen", "providers.py")
_spec = importlib.util.spec_from_file_location("providers", _prov)
providers = importlib.util.module_from_spec(_spec)
sys.modules["providers"] = providers
_spec.loader.exec_module(providers)

W, H = 320, 112
BAYER8 = np.array([
    [0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44, 4, 36, 14, 46, 6, 38], [60, 28, 52, 20, 62, 30, 54, 22],
    [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21],
])

IDS = ["grey_wolf", "feral_boar", "hedge_rat", "lane_wolf",
       "goblin_straggler", "ember_shade", "warden"]
WEAPONS = {
    "wand": ("holding ONE single glowing magic wand raised, faint "
             "arcane light, the other hand empty"),
    "bow": "drawing a bow with an arrow nocked",
    "sword": ("gripping ONE single drawn sword, blade catching the rim "
              "light, the other hand empty"),
}

DWARF = (
    "a DWARF — a full head SHORTER than a human, stocky and broad as a "
    "door, thick chest and short powerful limbs, a great braided beard, "
    "heavy mail and a round iron helm"
)

PLAYER_PROMPT = (
    "Black and white 3D render, semi-realistic, monochrome greyscale "
    "only, high contrast, cinematic lighting, realistic detailed "
    "textures. Background: PURE SOLID BLACK void (#000000) — nothing "
    "but darkness around the figure. Wide zoomed-out shot, ONE "
    "character standing in full SIDE VIEW (profile), feet planted, "
    "facing RIGHT, the ENTIRE body visible head to boots, standing "
    "EXACTLY one quarter of the frame height — the same size in every "
    "image of this series: " + DWARF + ", {weapon}. Exactly ONE weapon "
    "in the whole image. Sharp readable silhouette picked out by "
    "strong dramatic rim light. No color, no text, no borders, no "
    "watermark."
)

SCENE_PROMPT = (
    "The first reference image is a finished 1-bit pixel art battle "
    "scene: a player character on one side, a monster on the other, "
    "ordered Bayer dithering, pure black and white. The second "
    "reference is a character render on a black background: " + DWARF +
    ". Recreate the FIRST image EXACTLY — same monster in the same "
    "pose, same background, same light gradients, same camera, same "
    "1-bit dither style — but REPLACE the player character with the "
    "dwarf from the second reference, standing in the same spot facing "
    "the monster, holding the same kind of weapon, rendered in the "
    "same style as the rest of the scene: a solid dark figure with a "
    "crisp white rim contour. The dwarf must read clearly SHORTER and "
    "STOCKIER than a human. STRICTLY two colors, no text, no borders."
)


def api_key() -> str:
    key = os.environ.get("LUNA_GEMINI_API_KEY", "").strip()
    if key:
        return key
    env = os.path.join(_ROOT, "..", "luna", ".env")
    if os.path.exists(env):
        for line in open(env):
            line = line.strip()
            if line.startswith("LUNA_GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("LUNA_GEMINI_API_KEY not set (env or luna/.env)")


def to_1bit(path: str) -> Image.Image:
    img = Image.open(path).convert("L")
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
    bits = np.where(a / 255 > (BAYER8[ty % 8, tx % 8] + 0.5) / 64,
                    255, 0).astype(np.uint8)
    return Image.fromarray(bits).convert("RGB").resize(
        (W * 2, H * 2), Image.NEAREST)


async def gen_player(weapon: str, key: str) -> str:
    res = await providers.generate(
        providers.MODELS["nano-banana-pro"],
        PLAYER_PROMPT.format(weapon=WEAPONS[weapon]),
        aspect="21:9", api_key=key)
    if "error" in res:
        return f"FAIL dwarf_{weapon}: {res['error']} — " \
               f"{str(res.get('detail'))[:160]}"
    open(os.path.join(PLAYERS, f"dwarf_{weapon}.jpg"), "wb").write(
        res["image_bytes"])
    return f"ok   dwarf_{weapon}"


async def gen_scene(slug: str, key: str) -> str:
    """slug = floor001_{id}_dwarf_{weapon}"""
    mid_weapon = slug[len("floor001_"):]
    mid, weapon = mid_weapon.rsplit("_dwarf_", 1)
    src = os.path.join(SCENES, f"floor001_{mid}_fighter_{weapon}.jpg")
    dwarf = os.path.join(PLAYERS, f"dwarf_{weapon}.jpg")
    res = await providers._gemini_generate(
        providers.MODELS["nano-banana-pro"], SCENE_PROMPT,
        aspect="21:9",
        refs=[(open(src, "rb").read(), "image/jpeg"),
              (open(dwarf, "rb").read(), "image/jpeg")],
        api_key=key)
    if "error" in res:
        return f"FAIL {slug}: {res['error']} — " \
               f"{str(res.get('detail'))[:160]}"
    raw = os.path.join(SCENES, f"{slug}.jpg")
    open(raw, "wb").write(res["image_bytes"])
    to_1bit(raw).save(os.path.join(SCENES, f"{slug}_1bit.png"))
    return f"ok   {slug}"


async def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in ("players", "scenes"):
        sys.exit(__doc__)
    mode, names = sys.argv[1], sys.argv[2:]
    key = api_key()
    if mode == "players":
        os.makedirs(PLAYERS, exist_ok=True)
        todo = names or [w for w in WEAPONS if not os.path.exists(
            os.path.join(PLAYERS, f"dwarf_{w}.jpg"))]
        for line in await asyncio.gather(
                *(gen_player(w, key) for w in todo)):
            print(line, flush=True)
        return
    all_slugs = [f"floor001_{m}_dwarf_{w}" for m in IDS for w in WEAPONS]
    todo = names or [s for s in all_slugs if not os.path.exists(
        os.path.join(SCENES, f"{s}.jpg"))]
    print(f"{len(todo)} scenes", flush=True)
    failed = 0
    for i in range(0, len(todo), 3):
        for line in await asyncio.gather(
                *(gen_scene(s, key) for s in todo[i:i + 3])):
            print(line, flush=True)
            failed += line.startswith("FAIL")
    print(f"done, {failed} failed", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
