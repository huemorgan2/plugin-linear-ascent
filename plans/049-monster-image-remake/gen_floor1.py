#!/usr/bin/env python3
"""049: floor 1 remake -> floor1/.

The production recipe from research/1bit-images.md: the model designs
the 1-bit dither art directly (banner style, like the arcanum banner),
post-process only enforces the 320x112 grid.

Outputs, per floor-1 enemy (6 encounters + warden):
  floor1/closeups/{id}.jpg            model render (designed 1-bit style)
  floor1/closeups/{id}_1bit.png       grid-enforced 1-bit (2x preview)
  floor1/scenes/floor001_{id}_{player}_{weapon}.jpg      + _1bit.png
                                       9 player-weapon combos per enemy,
                                       re-rendered from the demoimages4
                                       composites.

Usage:
  python gen_floor1.py closeups [id ...]
  python gen_floor1.py scenes   [slug ...]     (slug = floor001_{id}_{pw})
Skips existing files unless names are passed explicitly.
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
SRC4 = os.path.join(_HERE, "demoimages4")
OUT = os.path.join(_HERE, "floor1")

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

STYLE = (
    "1-bit pixel art in the classic Macintosh / Playdate / 1-bit Akira "
    "poster style. STRICTLY two colors: pure black and pure white — "
    "every midtone rendered as ordered Bayer dithering with large "
    "chunky dither pixels. FULL OF designed gradients: sky fading "
    "smoothly between dense white dither and black, soft glow ramps "
    "radiating from every light source, gradient pools of light on the "
    "ground, atmospheric depth where far things dissolve into sparse "
    "dither. No text, no borders, no watermark. "
)

CLOSEUP_PROMPT = (
    "Using the creature from the reference image, draw a CLOSE-UP "
    "encounter shot of it in " + STYLE +
    "The creature alone — NO human characters — huge in the frame, "
    "caught mid-advance toward the viewer at a dramatic three-quarter "
    "angle, FULLY 3D-SHADED in dither — NOT a flat silhouette: one "
    "strong directional light models the creature's volume like a 3D "
    "render translated to 1-bit. The lit side of its body is BRIGHT "
    "(dense white dither to near-white highlights), the shadow side "
    "falls to solid black, and every muscle, fur mass and plate rolls "
    "through LARGE CHUNKY dither midtones between the two — big bold "
    "tonal steps that survive heavy downscaling. Dark contour line "
    "around the body, eyes as white points. Keep the creature's exact "
    "design from the reference. Wide horizontal "
    "frame, low camera, the floor-1 fencerow meadow behind it "
    "dissolving into dither: hedgerow lines, floodlight glow gradient."
)

SCENE_PROMPT = (
    "Redraw this exact scene as " + STYLE +
    "The two figures — the player character on one side and the "
    "creature on the other — are SOLID BLACK SILHOUETTES with crisp "
    "readable white rim contours, standing out against the dithered "
    "background. Keep the exact same composition, poses and camera. "
    "Wide cinematic shot, rich dithered texture in ground and sky."
)

IDS = ["grey_wolf", "feral_boar", "hedge_rat", "lane_wolf",
       "goblin_straggler", "ember_shade", "warden"]
COMBOS = [f"{c}_{w}" for c in ("fighter", "elf", "giant")
          for w in ("wand", "bow", "sword")]


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
    """Grid enforcement: crop 20:7 -> 320x112 -> autocontrast -> Bayer."""
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


async def gen_closeup(mid: str, key: str) -> str:
    ref = os.path.join(SRC4, f"floor001_{mid}_fighter_wand.jpg")
    res = await providers.edit(
        providers.MODELS["nano-banana-pro"], CLOSEUP_PROMPT,
        (open(ref, "rb").read(), "image/jpeg"), aspect="21:9", api_key=key)
    if "error" in res:
        return f"FAIL {mid}: {res['error']} — {str(res.get('detail'))[:160]}"
    raw = os.path.join(OUT, "closeups", f"{mid}.jpg")
    open(raw, "wb").write(res["image_bytes"])
    to_1bit(raw).save(os.path.join(OUT, "closeups", f"{mid}_1bit.png"))
    return f"ok   {mid}"


async def gen_scene(slug: str, key: str) -> str:
    ref = os.path.join(SRC4, f"{slug}.jpg")
    res = await providers.edit(
        providers.MODELS["nano-banana-pro"], SCENE_PROMPT,
        (open(ref, "rb").read(), "image/jpeg"), aspect="21:9", api_key=key)
    if "error" in res:
        return f"FAIL {slug}: {res['error']} — {str(res.get('detail'))[:160]}"
    raw = os.path.join(OUT, "scenes", f"{slug}.jpg")
    open(raw, "wb").write(res["image_bytes"])
    to_1bit(raw).save(os.path.join(OUT, "scenes", f"{slug}_1bit.png"))
    return f"ok   {slug}"


async def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in ("closeups", "scenes"):
        sys.exit(__doc__)
    mode, names = sys.argv[1], sys.argv[2:]
    os.makedirs(os.path.join(OUT, mode), exist_ok=True)
    key = api_key()
    if mode == "closeups":
        todo = names or [m for m in IDS if not os.path.exists(
            os.path.join(OUT, mode, f"{m}.jpg"))]
        fn = gen_closeup
    else:
        all_slugs = [f"floor001_{m}_{pw}" for m in IDS for pw in COMBOS]
        todo = names or [s for s in all_slugs if not os.path.exists(
            os.path.join(OUT, mode, f"{s}.jpg"))]
        fn = gen_scene
    print(f"{len(todo)} {mode} -> {OUT}/{mode}")
    failed = 0
    for i in range(0, len(todo), 4):
        for line in await asyncio.gather(
                *(fn(n, key) for n in todo[i:i + 4])):
            print(line, flush=True)
            failed += line.startswith("FAIL")
    print(f"done, {failed} failed")


if __name__ == "__main__":
    asyncio.run(main())
