#!/usr/bin/env python3
"""049 demo: the three players x three weapons on a black background.

Same look as the monster demos (black-and-white semi-realistic 3D
render, full side view, zoomed out) but on a pure black void — no
landscape. 3 characters x 3 weapons = 9 images -> demo-players/.

Usage:
  python plans/049-monster-image-remake/gen_demoplayers.py
Key: LUNA_GEMINI_API_KEY from env, falling back to ../../luna/.env.
"""

from __future__ import annotations

import asyncio
import importlib.util
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..", "..")
OUT = os.path.join(_HERE, "demo-players")

_prov = os.path.join(_ROOT, "..", "plugin-image-gen",
                     "plugin_image_gen", "providers.py")
_spec = importlib.util.spec_from_file_location("providers", _prov)
providers = importlib.util.module_from_spec(_spec)
sys.modules["providers"] = providers
_spec.loader.exec_module(providers)

STYLE = (
    "Black and white 3D render, semi-realistic, monochrome greyscale "
    "only, high contrast, cinematic lighting, realistic detailed "
    "textures and materials. Background: PURE SOLID BLACK void (#000000, "
    "never grey) — no landscape, no floor detail, nothing but darkness "
    "around the figure. Camera pulled far back — a wide zoomed-out shot, "
    "camera at the same fixed distance in every image of this series. ONE "
    "character standing in full SIDE VIEW (profile), feet planted, "
    "facing RIGHT, the ENTIRE body visible from head to boots — never "
    "cropped by the frame edge, {scale}, "
    "sharp readable silhouette "
    "picked out by strong dramatic rim light out of the darkness. "
    "No color, no text, no borders, no watermark. "
)

# {scale} pins the figure height so each character keeps ONE size across
# its three images, and the giant reads two heads taller than the others.
HUMAN_SCALE = ("standing EXACTLY one third of the frame height — the same "
               "size in every image of this series")
GIANT_SCALE = ("standing EXACTLY half of the frame height — a towering "
               "GIANT, two full heads taller than a human warrior and "
               "twice as wide, the same size in every image of this series")

CHARACTERS = {
    "fighter": (HUMAN_SCALE, (
        "a human woman fighter — strikingly beautiful and feminine, "
        "athletic, confident stance, long tied-back hair, in fitted "
        "practical armor that keeps her graceful figure")),
    "elf": (HUMAN_SCALE, (
        "a male elf — slender and elegant, sharp fine features, "
        "long hair, pointed ears, in sleek travel leathers")),
    "giant": (GIANT_SCALE, (
        "a GIANT — an enormous towering warrior two full heads taller "
        "than any human and twice as wide, built like a mountain: a "
        "great thick braided beard, immensely broad shoulders, a barrel "
        "chest, massive heavy limbs, in heavy plate and mail")),
}

WEAPONS = {
    "wand": ("holding ONE single glowing magic wand raised, faint arcane "
             "light, the other hand empty"),
    "bow": "drawing a bow with an arrow nocked",
    "sword": ("gripping ONE single drawn sword, blade catching the rim "
              "light, the other hand empty"),
}

ONE_WEAPON = (" Exactly ONE weapon in the whole image — no second weapon, "
              "no scabbard, no spare blades or wands anywhere on the body.")


async def gen_one(job: dict, key: str) -> str:
    res = await providers.generate(
        providers.MODELS["nano-banana-pro"], job["prompt"],
        aspect="21:9", api_key=key,
    )
    if "error" in res:
        return f"FAIL {job['slug']}: {res['error']} — {str(res.get('detail'))[:200]}"
    ext = "png" if "png" in res.get("mime", "") else "jpg"
    open(os.path.join(OUT, f"{job['slug']}.{ext}"), "wb").write(
        res["image_bytes"])
    return f"ok   {job['slug']}"


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


async def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    key = api_key()
    jobs = [
        {"slug": f"{c}_{w}",
         "prompt": (f"{STYLE.format(scale=scale)}Character: {cdesc}, "
                    f"{wdesc}.{ONE_WEAPON}")}
        for c, (scale, cdesc) in CHARACTERS.items()
        for w, wdesc in WEAPONS.items()
    ]
    if len(sys.argv) > 1:
        want = set(sys.argv[1:])
        jobs = [j for j in jobs if j["slug"] in want]
    print(f"{len(jobs)} images -> {OUT}")
    for i in range(0, len(jobs), 3):
        batch = jobs[i:i + 3]
        for line in await asyncio.gather(*(gen_one(j, key) for j in batch)):
            print(line, flush=True)


if __name__ == "__main__":
    asyncio.run(main())
