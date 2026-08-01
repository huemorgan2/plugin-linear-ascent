#!/usr/bin/env python3
"""030 art — every new-size asset in the ledger, one parametric pipeline.

Same discipline as generate_banners.py (that module is imported for the
style text, the Bayer matrix and the provider client), extended with a
per-job size: center-crop the model output to the target aspect, downscale
to the native grid, autocontrast, Bayer 8x8 -> exactly two states per
pixel, white ink on alpha.

Jobs (the plan's asset ledger):
  portraits  portrait_{rags,leather,chain,scale,plate,aegis}_100x200.png
  rooms      {forge,lodge,vault,medlab,relay,guildhall,stone,gate,arcanum,
              roothollow,greenreach,gnarl,town_lamplit_steading}_320x200.png
  vault_interior_320x50.png   (the strongbox shelf band)
  paper_320x150.png           (the Morning Crier's grain)

Usage: LUNA_GEMINI_API_KEY=... python tools/generate_030_art.py [name ...]
  names are job keys below; no args = everything missing; --force redoes.
"""

from __future__ import annotations

import asyncio
import io
import os
import sys

from PIL import Image, ImageOps

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import generate_banners as gb  # noqa: E402  (style, BAYER, providers, SCENES)

providers = gb.providers
CONTENT_ART = os.path.join(_HERE, "..", "plugin_linear_ascent", "content",
                           "art")
BANNERS = os.path.join(CONTENT_ART, "banners")
PORTRAITS = os.path.join(CONTENT_ART, "portraits")
RAW = os.path.join(_HERE, "..", "content", "art", "030", "raw")
PREVIEW = os.path.join(_HERE, "..", "content", "art", "030", "preview")

TEXT_INK = "#e6e9f2"
DIM = "#8b93a7"
GOLD = "#f5a524"

PORTRAIT_STYLE = (
    "Dithered grayscale full-body character study rendered like a "
    "charcoal drawing, then reduced to two colors through fine ordered "
    "Bayer dithering — every surface described by smooth tonal "
    "GRADIENTS of dither density, never by outlines. NO hard contour "
    "lines, no cartoon linework, no cel shading, no ink outlines "
    "anywhere: forms emerge from light and shadow alone, soft edges "
    "dissolving into dither. ONE standing human figure fills the frame "
    "top to bottom — head near the top edge, boots at the bottom edge, "
    "facing the viewer, arms at the sides, weight square. Volumetric "
    "shading: one soft key light from the top-left rolling across "
    "every rounded form, deep core shadows. The background is pure "
    "flat black — NO glow, NO halo, NO aura, NO backlight of any kind "
    "behind the figure; the silhouette meets darkness directly. "
    "Painterly, somber, realistic proportions. No text, no border, no "
    "watermark. The figure: ")

# one silhouette, six wardrobes — the suit-up IS the reward
PORTRAIT_JOBS = {
    "portrait_rags": (
        "a fresh climber in patched cloth rags and wrapped feet, bare "
        "arms, a rope belt, hopeful stance — poor but unbowed."),
    "portrait_leather": (
        "a climber in a worn leather jerkin and bracers, sturdy boots, "
        "a short blade on the hip — the first honest kit."),
    "portrait_chain": (
        "a climber in a chainmail hauberk to the thigh over padded "
        "cloth, gauntlets, a belt of pouches — mail catching the light "
        "as dithered sparkle."),
    "portrait_scale": (
        "a climber in overlapping scale armour with a high collar, "
        "plated boots, a heavy cloak pinned at one shoulder — each "
        "scale row reading as a gradient band."),
    "portrait_plate": (
        "a climber in full plate armour, pauldrons and breastplate "
        "rim-lit, visor raised, a long sword point-down in one fist — "
        "a walking fortress."),
    "portrait_aegis": (
        "a champion in ornate master-forged aegis plate, crowned helm "
        "under one arm, filigree glowing faintly along every edge in "
        "soft gradient halos, a great cloak — the top of the ladder."),
    # 031: the lodge has a face — Wick, the keeper
    "portrait_wick": (
        "a stout old innkeeper with a magnificent braided beard, a "
        "leather apron over a rolled-sleeve shirt, one sleeve pinned "
        "flat over a missing left arm, a tankard in his remaining "
        "hand, laugh lines and tired kind eyes — a retired climber "
        "who runs the lodge now."),
}

# rooms regenerated tall (320x200) — prompts are the proven ones from the
# banner set; the model just gets more sky and floor to fill.
ROOM_SLUGS = ("forge", "lodge", "vault", "medlab", "relay", "guildhall",
              "stone", "gate", "arcanum", "roothollow", "greenreach",
              "gnarl", "town_lamplit_steading")

BAND_JOBS = {
    "vault_interior": (
        "the inside shelf of a bank strongbox seen straight-on and "
        "extremely wide: heaped gold coins in mounds along the whole "
        "shelf, a few stacked coin towers and one tipped-over spill, "
        "small ingots at the back, one lamp's glow raking across the "
        "heap in a smooth gradient from bright at the left to dark at "
        "the right, everything inside a low horizontal band.",
        (320, 50), BANNERS, GOLD),
    "paper": (
        "a flat sheet of old newsprint filling the frame straight-on: "
        "subtle mottled paper grain, faint vertical column rules, "
        "smudged unreadable text blocks as soft gray dither bands, one "
        "worn fold line across the middle, edges slightly darkened in a "
        "gentle vignette gradient — absolutely no readable letters.",
        (320, 150), BANNERS, DIM),
}

PANEL = (0x11, 0x15, 0x1F)


def _hx(s: str) -> tuple[int, int, int]:
    return tuple(int(s[i:i + 2], 16) for i in (1, 3, 5))


def to_1bit(img: Image.Image, w: int, h: int) -> list[list[int]]:
    """Center-crop to w:h, downscale, Bayer-dither to bits."""
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
    return [
        [1 if px[x, y] / 255 > (gb.BAYER[y % 8][x % 8] + 0.5) / 64 else 0
         for x in range(w)]
        for y in range(h)
    ]


def bits_to_png(bits: list[list[int]], color: tuple[int, int, int],
                scale: int = 1,
                bg: tuple[int, int, int] | None = None) -> Image.Image:
    h, w = len(bits), len(bits[0])
    out = Image.new("RGBA", (w, h))
    po = out.load()
    for y in range(h):
        for x in range(w):
            if bits[y][x]:
                po[x, y] = (*color, 255)
            else:
                po[x, y] = (*bg, 255) if bg else (0, 0, 0, 0)
    if scale > 1:
        out = out.resize((w * scale, h * scale), Image.NEAREST)
    return out


def _jobs() -> dict[str, tuple[str, tuple[int, int], str, str]]:
    """name -> (full prompt, (w, h), out_dir, preview tint)."""
    jobs = {}
    for slug, prompt in PORTRAIT_JOBS.items():
        jobs[slug] = (PORTRAIT_STYLE + prompt, (100, 200), PORTRAITS,
                      TEXT_INK)
    for slug in ROOM_SLUGS:
        prompt, tint = gb.SCENES[slug]
        jobs[slug] = (gb.STYLE + prompt, (320, 200), BANNERS, tint)
    for slug, (prompt, size, outdir, tint) in BAND_JOBS.items():
        jobs[slug] = (gb.STYLE + prompt, size, outdir, tint)
    return jobs


def _aspect_for(w: int, h: int) -> str:
    """Closest generator aspect at or wider than the target — cropping
    trims, never invents."""
    r = w / h
    if r <= 0.6:
        return "9:16"
    if r <= 1.7:
        return "16:9"
    return "21:9"


async def gen_one(name: str, job, api_key: str) -> str:
    prompt, (w, h), outdir, tint = job
    res = await providers.generate(
        providers.MODELS["nano-banana-pro"], prompt,
        aspect=_aspect_for(w, h), api_key=api_key,
    )
    if "error" in res:
        return f"FAIL {name}: {res['error']} — {str(res.get('detail'))[:200]}"
    raw = Image.open(io.BytesIO(res["image_bytes"]))
    raw.save(os.path.join(RAW, f"{name}_raw.png"))
    bits = to_1bit(raw, w, h)
    bits_to_png(bits, (255, 255, 255)).save(
        os.path.join(outdir, f"{name}_{w}x{h}.png"))
    bits_to_png(bits, _hx(tint), scale=2, bg=PANEL).save(
        os.path.join(PREVIEW, f"{name}_preview.png"))
    ink = sum(map(sum, bits)) / (w * h)
    return f"ok   {name}: {w}x{h} ink {ink:.0%}"


async def main() -> None:
    api_key = os.environ.get("LUNA_GEMINI_API_KEY", "").strip()
    if not api_key:
        sys.exit("LUNA_GEMINI_API_KEY not set")
    force = "--force" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    jobs = _jobs()
    unknown = [a for a in args if a not in jobs]
    if unknown:
        sys.exit(f"unknown jobs: {unknown}; have {sorted(jobs)}")
    for d in (BANNERS, PORTRAITS, RAW, PREVIEW):
        os.makedirs(d, exist_ok=True)
    names = args or [
        n for n, (_, (w, h), outdir, _) in jobs.items()
        if force or not os.path.exists(
            os.path.join(outdir, f"{n}_{w}x{h}.png"))]
    if not names:
        print("nothing to do — all assets exist (use --force)")
        return
    for i in range(0, len(names), 4):
        batch = names[i:i + 4]
        for line in await asyncio.gather(
                *(gen_one(n, jobs[n], api_key) for n in batch)):
            print(line, flush=True)


if __name__ == "__main__":
    asyncio.run(main())
