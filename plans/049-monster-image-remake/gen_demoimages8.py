#!/usr/bin/env python3
"""049: outlined 3D render style -> demoimages8/.

New style probe: the demoimages4 composites re-rendered by the model
with bold contour OUTLINES (toon/cel-shader ink lines) around the
characters, creatures and major shapes — aimed at surviving the
1-bit downscale with readable silhouettes.

Default run: the same 10-image review sample as demoimages7 (first
10 monsters in floor order, cycling the 9 player-weapon combos).

Usage:
  python plans/049-monster-image-remake/gen_demoimages8.py [name ...]
Key: LUNA_GEMINI_API_KEY from env, falling back to ../../luna/.env.
"""

from __future__ import annotations

import asyncio
import glob
import importlib.util
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..", "..")
SRC = os.path.join(_HERE, "demoimages4")
OUT = os.path.join(_HERE, "demoimages8")

_prov = os.path.join(_ROOT, "..", "plugin-image-gen",
                     "plugin_image_gen", "providers.py")
_spec = importlib.util.spec_from_file_location("providers", _prov)
providers = importlib.util.module_from_spec(_spec)
sys.modules["providers"] = providers
_spec.loader.exec_module(providers)

PROMPT = (
    "Redraw this exact image in a black-and-white 3D render style WITH "
    "BOLD OUTLINES: every figure, creature and major object contoured by "
    "a thick, clean, dark ink line, like a toon/cel shader outline pass "
    "over a 3D render. The character and the creature get the heaviest, "
    "cleanest contour lines so their silhouettes read instantly; "
    "background shapes get lighter, thinner outlines. Keep the exact "
    "same composition, poses, camera and lighting. Flatten fine "
    "photoreal micro-texture into simple shaded surfaces — bold shapes, "
    "clear tonal separation between character, creature, midground and "
    "sky. Monochrome greyscale only, no color, no text, no borders, "
    "no watermark."
)

SAMPLE_COUNT = 10


def sample_names() -> list[str]:
    combos = [f"{c}_{w}"
              for c in ("fighter", "elf", "giant")
              for w in ("wand", "bow", "sword")]
    monsters, seen = [], set()
    for path in sorted(glob.glob(os.path.join(SRC, "*.jpg"))):
        m = "_".join(os.path.basename(path).split("_")[:-2])
        if m not in seen:
            seen.add(m)
            monsters.append(m)
    return [f"{m}_{combos[i % len(combos)]}"
            for i, m in enumerate(monsters[:SAMPLE_COUNT])]


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


async def gen_one(name: str, key: str) -> str:
    img = open(os.path.join(SRC, f"{name}.jpg"), "rb").read()
    res = await providers.edit(
        providers.MODELS["nano-banana-pro"], PROMPT, (img, "image/jpeg"),
        aspect="21:9", api_key=key,
    )
    if "error" in res:
        return f"FAIL {name}: {res['error']} — {str(res.get('detail'))[:200]}"
    ext = "png" if "png" in res.get("mime", "") else "jpg"
    open(os.path.join(OUT, f"{name}.{ext}"), "wb").write(res["image_bytes"])
    return f"ok   {name}"


async def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    key = api_key()
    names = sys.argv[1:] or sample_names()
    print(f"{len(names)} images -> {OUT}")
    for i in range(0, len(names), 4):
        batch = names[i:i + 4]
        for line in await asyncio.gather(*(gen_one(n, key) for n in batch)):
            print(line, flush=True)


if __name__ == "__main__":
    asyncio.run(main())
