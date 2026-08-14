#!/usr/bin/env python3
"""057 P1 — the 10 review swords, poorest to mythic.

Pipeline per vision/1bit-images.md: the model DESIGNS the 1-bit dither;
post-processing only enforces the grid. One render per sword yields both
the 100x160 portrait and the 48x30 icon (raw rotated 90°).

Usage: LUNA_GEMINI_API_KEY=... python plans/057-weapon-art/gen_swords.py [slug ...]
Outputs into plans/057-weapon-art/swords/.
"""

from __future__ import annotations

import asyncio
import io
import logging
import os
import sys

from PIL import Image, ImageOps

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "tools"))
import generate_banners as gb  # noqa: E402  (BAYER + provider client)

# the provider's http client logs full request URLs (key included) at
# INFO — keep the key out of the terminal
logging.getLogger("httpx").setLevel(logging.WARNING)

OUT = os.path.join(_HERE, "swords")
LW, LH = 100, 160   # large portrait
IW, IH = 48, 30     # icon
PANEL = (0x11, 0x15, 0x1F)
ART_TINT = (0xD9, 0xD9, 0xD3)

STYLE = (
    "1-bit pixel art of a SINGLE weapon in the classic Macintosh / "
    "Playdate poster style. STRICTLY two colors: pure black background, "
    "white ink — every midtone rendered as LARGE CHUNKY ordered Bayer "
    "dither pixels. The weapon stands VERTICAL, point up, perfectly "
    "centered, filling most of the frame height, on a PURE BLACK empty "
    "background. FULLY 3D-SHADED in dither, NOT a flat silhouette: one "
    "strong light from the top-left models the volume — lit side in "
    "dense white dither to near-white highlights, shadow side falling "
    "to solid black, big bold tonal steps that survive heavy "
    "downscaling. Crisp readable outline. No text, no border, no "
    "watermark, no hands, no scene. Weapon: "
)

# slug -> (rung-band styling + name-mined identity)
SWORDS: dict[str, str] = {
    "scrap_dagger": (
        "a POOR crude scrap-metal dagger — a short blade ground from a "
        "rusted sheet-metal offcut, edge chipped and uneven, tip "
        "slightly bent, grip just cord wrapped over bare tang, NO "
        "guard, NO ornament, NO glow, dull battered surface, small and "
        "pitiful in the frame with black space around it."),
    "boarspine_shortsword": (
        "a POOR rough shortsword — a stubby single-edged blade with a "
        "boar-tusk curve, hilt of carved bone rings, leather-strap "
        "grip, tiny plain iron stub guard, edge nicked from use, NO "
        "ornament, NO glow, dull worn steel, modest size in the frame."),
    "iron_sword": (
        "a PLAIN honest iron arming sword — straight double-edged "
        "blade with a single clean fuller, simple straight crossguard, "
        "plain round pommel, leather-wrapped grip, well-kept but "
        "completely unadorned, NO glow, NO engraving, the standard "
        "soldier's sword, modest in the frame."),
    "goblin_iron_falchion": (
        "a PLAIN brutal goblin-iron falchion — a heavy single-edged "
        "chopping blade with a clipped tip, crude rivets down the "
        "spine, mismatched dark iron plates, a jagged hand-guard of "
        "hammered scrap, tooth-marks notched into the spine, NO glow, "
        "menacing but cheap."),
    "wolfbite": (
        "a FORGED wolf-fanged longsword — clean bright steel blade "
        "with a narrow etched fuller, the crossguard cast as a "
        "snarling wolf's open jaw gripping the blade between its "
        "fangs, pommel a wolf's-head, wire-wrapped grip, the FIRST "
        "faint edge-light: a thin subtle dither glow tracing the "
        "cutting edge only."),
    "emberfang": (
        "a FINE ember-forged blade — a slightly curved sword whose "
        "dark steel is split by GLOWING EMBER SEAMS, cracks down the "
        "blade radiating heat as designed dither glow ramps, guard of "
        "two swept dragon-fang points, heat shimmer rising off the "
        "edge as sparse dither, grip of char-black leather with a "
        "glowing core peeking between wraps."),
    "thornsong": (
        "a FINE living thorn-blade — an elegant leaf-shaped sword "
        "grown as much as forged, briar vines in relief coiling the "
        "whole blade and bursting into a thorned guard, small white "
        "blossoms at the ricasso, a soft designed glow breathing "
        "along the vine lines, graceful and ornate."),
    "oathkeeper": (
        "a MASTER ceremonial greatsword — a long cathedral-forged "
        "blade engraved with lines of runic oath-script down the "
        "center that GLOW with a clean designed radiance, a wide "
        "winged crossguard like spread angel wings, a ring pommel "
        "holding a glowing gem, light pooling off the runes in "
        "gradient halos, large and commanding in the frame."),
    "starfall": (
        "a MYTHIC star-metal blade — a long sword seemingly cut from "
        "the night sky, blade body of deep black speckled with "
        "star-point white dither, a comet-tail of designed glow "
        "streaming off the tip, guard of two crescent arcs, the whole "
        "weapon wrapped in a radiant gradient halo, huge in the "
        "frame, dramatic."),
    "dawnbreaker": (
        "a MYTHIC dawn-forged greatsword — a colossal blade blazing "
        "like sunrise, a designed radial gradient sunburst halo "
        "erupting from behind the blade, edge lines of pure white "
        "light, rays streaming upward as dither ramps, ornate solar "
        "crown guard with a burning core gem, the most radiant and "
        "elaborate weapon imaginable, filling the frame."),
}


def _enforce(img: Image.Image, w: int, h: int) -> Image.Image:
    """crop → grid → autocontrast → Bayer → white ink on alpha."""
    img = img.convert("L")
    iw, ih = img.size
    target = w / h
    if iw / ih > target:
        nw = int(ih * target)
        img = img.crop(((iw - nw) // 2, 0, (iw + nw) // 2, ih))
    else:
        nh = int(iw / target)
        img = img.crop((0, (ih - nh) // 2, iw, (ih + nh) // 2))
    img = img.resize((w, h), Image.LANCZOS)
    img = ImageOps.autocontrast(img, cutoff=1)
    px = img.load()
    out = Image.new("RGBA", (w, h))
    po = out.load()
    for y in range(h):
        for x in range(w):
            if px[x, y] / 255 > (gb.BAYER[y % 8][x % 8] + 0.5) / 64:
                po[x, y] = (255, 255, 255, 255)
    return out


def _on_panel(img: Image.Image, scale: int, tint=ART_TINT) -> Image.Image:
    """preview: tinted ink on the game's panel color, NEAREST-scaled."""
    w, h = img.size
    out = Image.new("RGB", (w, h), PANEL)
    po, pi = out.load(), img.load()
    for y in range(h):
        for x in range(w):
            if pi[x, y][3]:
                po[x, y] = tint
    return out.resize((w * scale, h * scale), Image.NEAREST)


async def gen_one(slug: str, api_key: str) -> str:
    res = await gb.providers.generate(
        gb.providers.MODELS["nano-banana-pro"], STYLE + SWORDS[slug],
        aspect="9:16", api_key=api_key,
    )
    if "error" in res:
        return f"FAIL {slug}: {res['error']} — {str(res.get('detail'))[:200]}"
    raw = Image.open(io.BytesIO(res["image_bytes"]))
    raw.save(os.path.join(OUT, f"{slug}_raw.png"))
    large = _enforce(raw, LW, LH)
    large.save(os.path.join(OUT, f"{slug}_{LW}x{LH}.png"))
    # icon: same raw rotated 90° (blade horizontal, point right)
    icon = _enforce(raw.rotate(-90, expand=True), IW, IH)
    icon.save(os.path.join(OUT, f"{slug}_{IW}x{IH}.png"))
    ink = sum(1 for y in range(LH) for x in range(LW)
              if large.load()[x, y][3]) / (LW * LH)
    return f"ok   {slug}: ink {ink:.0%}"


def contact_sheet() -> None:
    """all ten, poorest → mythic: portrait at 2x over its icon at 4x."""
    pad = 8
    cell_w = LW * 2 + pad
    sheet = Image.new("RGB", (cell_w * len(SWORDS) + pad,
                              LH * 2 + IH * 4 + pad * 4), PANEL)
    x = pad
    for slug in SWORDS:
        lp = os.path.join(OUT, f"{slug}_{LW}x{LH}.png")
        ip = os.path.join(OUT, f"{slug}_{IW}x{IH}.png")
        if not (os.path.exists(lp) and os.path.exists(ip)):
            continue
        big = _on_panel(Image.open(lp), 2)
        ico = _on_panel(Image.open(ip), 4)
        sheet.paste(big, (x, pad))
        sheet.paste(ico, (x + (big.width - ico.width) // 2,
                          LH * 2 + pad * 2))
        x += cell_w
    sheet.save(os.path.join(OUT, "contact_sheet.png"))


async def main() -> None:
    api_key = os.environ.get("LUNA_GEMINI_API_KEY", "").strip()
    if not api_key:
        sys.exit("LUNA_GEMINI_API_KEY not set")
    os.makedirs(OUT, exist_ok=True)
    slugs = sys.argv[1:] or list(SWORDS)
    unknown = [s for s in slugs if s not in SWORDS]
    if unknown:
        sys.exit(f"unknown: {unknown}")
    for i in range(0, len(slugs), 4):
        batch = slugs[i:i + 4]
        for line in await asyncio.gather(*(gen_one(s, api_key)
                                           for s in batch)):
            print(line, flush=True)
    contact_sheet()
    print("contact_sheet.png written")


if __name__ == "__main__":
    asyncio.run(main())
