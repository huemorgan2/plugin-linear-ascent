#!/usr/bin/env python3
"""Linear Ascent title card — 320x200 1-bit, same pipeline as the banners.

Uses the ascent banner's raw model output as a style/composition reference
(providers.edit), zoomed out to show the ground and Roothollow, with the
game title rendered inside the image.

Usage: LUNA_GEMINI_API_KEY=... python tools/generate_title.py
Outputs: content/art/title/ascent_title_320x200.png  (white ink, alpha)
         content/art/title/ascent_title_preview.png  (tinted, on panel, 2x)
         content/art/title/ascent_title_raw.png      (model output)
"""

from __future__ import annotations

import asyncio
import io
import os
import sys

from PIL import Image, ImageOps

_HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(_HERE, "..", "content", "art")
OUT = os.path.join(ART, "title")
REF = os.path.join(ART, "banners", "raw", "ascent_raw.png")
W, H = 320, 200  # 16:10 title card, upscaled ~2x with pixelated rendering

sys.path.insert(0, os.path.join(_HERE, "..", "..", "plugin-image-gen"))
from plugin_image_gen import providers  # noqa: E402

BAYER = [
    [0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44, 4, 36, 14, 46, 6, 38], [60, 28, 52, 20, 62, 30, 54, 22],
    [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21],
]

PROMPT = (
    "Redraw this exact scene as a 1-bit pixel art TITLE SCREEN in the same "
    "classic Macintosh / Playdate / 1-bit Akira poster style. STRICTLY two "
    "colors: pure black and pure white — every midtone rendered as ordered "
    "Bayer dithering, big designed gradients everywhere. Zoom OUT: pull the "
    "camera back and lower so much more of the GROUND is visible — a wide "
    "plain at the tower's foot with the small refugee village of Roothollow "
    "(shack rooflines, one antenna, a dirt road leading toward the tower), "
    "the colossal banded tower further away, still rising out of frame "
    "through a sunlit cloud deck, its two great anchor chains reaching the "
    "ground, bright hopeful morning sky full of soft cumulus clouds, sun "
    "with a wide radial halo. Across the upper sky render the title "
    "'LINEAR ASCENT' in VERY LARGE bold blocky pixel capitals, solid pure "
    "black, perfectly legible, spelled exactly L-I-N-E-A-R space "
    "A-S-C-E-N-T, no other text anywhere. Luminous, optimistic, mostly "
    "light. No borders, no watermark."
)

PANEL = (0x11, 0x15, 0x1F)
DIM = (0x8B, 0x93, 0xA7)


def to_1bit(img: Image.Image) -> list[list[int]]:
    """Center-crop to 16:10, downscale to the grid, Bayer-dither to bits."""
    img = img.convert("L")
    w, h = img.size
    target = W / H
    if w / h > target:
        nw = int(h * target)
        img = img.crop(((w - nw) // 2, 0, (w + nw) // 2, h))
    else:
        nh = int(w / target)
        img = img.crop((0, (h - nh) // 2, w, (h + nh) // 2))
    img = img.resize((W, H), Image.LANCZOS)
    img = ImageOps.autocontrast(img, cutoff=1)
    px = img.load()
    return [
        [1 if px[x, y] / 255 > (BAYER[y % 8][x % 8] + 0.5) / 64 else 0
         for x in range(W)]
        for y in range(H)
    ]


def bits_to_png(bits: list[list[int]], color: tuple[int, int, int],
                scale: int = 1, bg: tuple[int, int, int] | None = None) -> Image.Image:
    out = Image.new("RGBA", (W, H))
    po = out.load()
    for y in range(H):
        for x in range(W):
            if bits[y][x]:
                po[x, y] = (*color, 255)
            else:
                po[x, y] = (*bg, 255) if bg else (0, 0, 0, 0)
    if scale > 1:
        out = out.resize((W * scale, H * scale), Image.NEAREST)
    return out


async def main() -> None:
    api_key = os.environ.get("LUNA_GEMINI_API_KEY", "").strip()
    if not api_key:
        sys.exit("LUNA_GEMINI_API_KEY not set")
    os.makedirs(OUT, exist_ok=True)
    with open(REF, "rb") as f:
        ref = (f.read(), "image/png")
    res = await providers.edit(
        providers.MODELS["nano-banana-pro"], PROMPT, ref,
        aspect="3:2", api_key=api_key,
    )
    if "error" in res:
        sys.exit(f"FAIL: {res['error']} — {str(res.get('detail'))[:300]}")
    raw = Image.open(io.BytesIO(res["image_bytes"]))
    raw.save(os.path.join(OUT, "ascent_title_raw.png"))
    bits = to_1bit(raw)
    bits_to_png(bits, (255, 255, 255)).save(
        os.path.join(OUT, f"ascent_title_{W}x{H}.png"))
    bits_to_png(bits, DIM, scale=2, bg=PANEL).save(
        os.path.join(OUT, "ascent_title_preview.png"))
    ink = sum(map(sum, bits)) / (W * H)
    print(f"ok   ascent_title: ink {ink:.0%}")


if __name__ == "__main__":
    asyncio.run(main())
