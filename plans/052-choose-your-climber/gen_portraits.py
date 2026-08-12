#!/usr/bin/env python3
"""052: the three climber portraits — warrior woman, elf man, giant.

Same law as tools/generate_030_art.py (whose style text, pipeline and
provider client are imported): nano-banana-pro designs the dither, the
pipeline only enforces the grid. The giant's frame is 140x260 — 1.3x
the human 100x200 — so his size is baked into the PNG's aspect and
every surface that draws him at natural ratio shows a bigger figure.

Usage: python plans/052-choose-your-climber/gen_portraits.py [slug ...]
Key: LUNA_GEMINI_API_KEY from env, falling back to ../../luna/.env.
Raws saved versioned (__raw_vN) — a good render is never overwritten.
"""

from __future__ import annotations

import asyncio
import glob
import importlib.util
import io
import os
import sys
import types

from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..", "..")

# The plugin_image_gen package __init__ pulls luna_sdk, which no venv
# here carries — register providers.py under the package name by hand
# (the 049 gen_demoplayers trick) so generate_banners' import resolves.
_prov = os.path.join(_ROOT, "..", "plugin-image-gen", "plugin_image_gen",
                     "providers.py")
_spec = importlib.util.spec_from_file_location(
    "plugin_image_gen.providers", _prov)
_providers = importlib.util.module_from_spec(_spec)
_pkg = types.ModuleType("plugin_image_gen")
_pkg.providers = _providers
sys.modules["plugin_image_gen"] = _pkg
sys.modules["plugin_image_gen.providers"] = _providers
_spec.loader.exec_module(_providers)

sys.path.insert(0, os.path.join(_ROOT, "tools"))
import generate_030_art as g030  # noqa: E402

PORTRAITS = os.path.join(_ROOT, "plugin_linear_ascent", "content", "art",
                         "portraits")
RAW = os.path.join(_HERE, "raw")
PREVIEW = os.path.join(_HERE, "preview")

# The 049 demo-player cast, restated for the 030 portrait style (front
# view, arms at sides — the style text owns pose and light).
JOBS = {
    "portrait_human": ((100, 200), "human figure", (
        "a human woman fighter — strikingly beautiful and feminine, "
        "athletic build, confident bearing, long tied-back hair, in "
        "fitted practical armor that keeps her graceful figure, a sword "
        "sheathed at her hip.")),
    "portrait_elf": ((100, 200), "elven figure", (
        "a male elf — slender and elegant, sharp fine features, long "
        "hair, tall pointed ears clearly visible against the dark, in "
        "sleek travel leathers, a shortbow slung across the back.")),
    "portrait_giant": ((140, 260), "gigantic figure", (
        "a GIANT warrior — enormously broad and towering, built like a "
        "mountain: a great thick braided beard, immensely broad "
        "shoulders, a barrel chest, massive heavy limbs, in heavy plate "
        "and mail, huge gauntleted fists at his sides.")),
}


async def gen_one(slug: str, key: str) -> str:
    (w, h), figure, desc = JOBS[slug]
    prompt = (g030.PORTRAIT_STYLE.replace("human figure", figure)
              + desc)
    res = await g030.providers.generate(
        g030.providers.MODELS["nano-banana-pro"], prompt,
        aspect="9:16", api_key=key,
    )
    if "error" in res:
        return f"FAIL {slug}: {res['error']} — {str(res.get('detail'))[:200]}"
    raw = Image.open(io.BytesIO(res["image_bytes"]))
    v = len(glob.glob(os.path.join(RAW, f"{slug}__raw_v*.png"))) + 1
    raw.save(os.path.join(RAW, f"{slug}__raw_v{v}.png"))
    bits = g030.to_1bit(raw, w, h)
    g030.bits_to_png(bits, (255, 255, 255)).save(
        os.path.join(PORTRAITS, f"{slug}_{w}x{h}.png"))
    g030.bits_to_png(bits, g030._hx(g030.TEXT_INK), scale=2,
                     bg=g030.PANEL).save(
        os.path.join(PREVIEW, f"{slug}_preview.png"))
    ink = sum(map(sum, bits)) / (w * h)
    return f"ok   {slug}: {w}x{h} ink {ink:.0%} (raw v{v})"


async def main() -> None:
    os.makedirs(RAW, exist_ok=True)
    os.makedirs(PREVIEW, exist_ok=True)
    key = os.environ.get("LUNA_GEMINI_API_KEY", "").strip()
    if not key:
        env = os.path.join(_ROOT, "..", "luna", ".env")
        if os.path.exists(env):
            for line in open(env):
                line = line.strip()
                if line.startswith("LUNA_GEMINI_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not key:
        sys.exit("LUNA_GEMINI_API_KEY not set (env or luna/.env)")
    slugs = sys.argv[1:] or list(JOBS)
    for r in await asyncio.gather(*(gen_one(s, key) for s in slugs)):
        print(r)


if __name__ == "__main__":
    asyncio.run(main())
