#!/usr/bin/env python3
"""049: the Liberation Dissolve, animated -> floor1/animation/.

One demo encounter: the grey wolf killed by the fighter with sword.
Frames follow floor1/LIBERATION.md exactly — frame 1 is the scene
itself; frames 2-6 are model edits, each generated FROM THE PREVIOUS
FRAME so the scene stays continuous. Every frame is grid-enforced to
1-bit and the set is assembled into a GIF.

Usage:
  python gen_floor1_liberation.py
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
SCENE = os.path.join(_HERE, "floor1", "scenes",
                     "floor001_grey_wolf_fighter_sword.jpg")
OUT = os.path.join(_HERE, "floor1", "animation")

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

TRUE_FORM = ("the original animal at its true small size: the shy grey "
             "wolf the farm dogs kept past the fences — knee-high to "
             "the monster it was, thin and ordinary")

BASE = (
    "The monster wolf is dissolving in the LIBERATION DISSOLVE: its "
    "solid black silhouette breaks apart into square chunky 1-bit "
    "dither particles — single white and black pixels and 2x2 blocks — "
    "that lift and scatter upward like sparks, dense at the body "
    "thinning to sparse dots above, while the fever's magic leaves it "
    "as one thin ribbon of sparse dither curling up and away. "
    "Everything else in the scene — background, light gradients, the "
    "player character — stays exactly the same. Keep the 1-bit pixel "
    "art style: strictly pure black and pure white, ordered Bayer "
    "dithering, no text, no borders, no watermark. "
)

STAGES = [
    "The dissolve is just beginning: the monster's white rim contour "
    "flares bright and hairline white cracks split its black "
    "silhouette. The body is still whole.",
    "The dissolve is halfway: the upper half of the monster has broken "
    "into the particle cloud; the legs still stand.",
    "The body is fully dissolved into a rising particle cloud. "
    f"Standing on the ground behind the thinning cloud, small and "
    f"whole: {TRUE_FORM}.",
    f"Only sparse drifting motes remain of the cloud. {TRUE_FORM} "
    "stands clearly in the monster's place, tiny by comparison.",
    "The particles are gone. The small ordinary grey wolf stands "
    "alone, calm, at its real size, in the exact spot where the "
    "monster died.",
]


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


async def main() -> None:
    if not os.path.exists(SCENE):
        sys.exit(f"scene not ready yet: {SCENE}")
    os.makedirs(OUT, exist_ok=True)
    key = api_key()

    frames = [os.path.join(OUT, f"frame{i}.jpg") for i in range(1, 7)]
    import shutil
    shutil.copyfile(SCENE, frames[0])
    print("ok   frame1 (scene)", flush=True)

    for i, stage in enumerate(STAGES, start=2):
        prev = open(frames[i - 2], "rb").read()
        res = await providers.edit(
            providers.MODELS["nano-banana-pro"], BASE + stage,
            (prev, "image/jpeg"), aspect="21:9", api_key=key)
        if "error" in res:
            sys.exit(f"FAIL frame{i}: {res['error']} — "
                     f"{str(res.get('detail'))[:160]}")
        open(frames[i - 1], "wb").write(res["image_bytes"])
        print(f"ok   frame{i}", flush=True)

    bits = [to_1bit(p) for p in frames]
    for i, b in enumerate(bits, start=1):
        b.save(os.path.join(OUT, f"frame{i}_1bit.png"))
    # hold the kill pose and the final calm frame longer
    durations = [700, 250, 250, 350, 350, 1200]
    bits[0].save(os.path.join(OUT, "liberation_grey_wolf.gif"),
                 save_all=True, append_images=bits[1:],
                 duration=durations, loop=0)
    print(f"gif  -> {os.path.join(OUT, 'liberation_grey_wolf.gif')}")


if __name__ == "__main__":
    asyncio.run(main())
