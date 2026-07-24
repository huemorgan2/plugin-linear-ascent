#!/usr/bin/env python3
"""Linear Ascent creature/warden images — prompts built from floor YAMLs.

Plan: plans/005-art-expansion/plan.md. Same pipeline as
generate_banners.py: model paints the scene, post-process enforces the
grid and the 1-bit discipline (crop -> downscale -> autocontrast ->
Bayer 8x8 -> white ink on alpha).

Sizes (plan §1): 320x112 for every encounter and regular warden;
320x200 for milestone bosses (floors 10, 20, ... 100).

Prompts are NOT hand-written: each is STYLE preamble + tier lighting
(plan §2 sky progression) + the encounter's own `name` and `prose`
from plugin_linear_ascent/content/floors/floor_NNN.yaml.

Usage:
  LUNA_GEMINI_API_KEY=... python tools/generate_creatures.py --floor 1
  python tools/generate_creatures.py --floor 1-10          # a tier
  python tools/generate_creatures.py grey_wolf warden_001  # by slug
Outputs:
  content/art/creatures/<slug>_320x112.png       (white ink, alpha)
  content/art/creatures/raw/<slug>_raw.png       (model output)
  content/art/creatures/preview/<slug>_preview.png (tinted, on panel)
  content/art/creatures/preview/sheet_floor_NNN.png (contact sheet)
"""

from __future__ import annotations

import argparse
import asyncio
import glob
import io
import os
import re
import sys

import yaml
from PIL import Image, ImageOps

_HERE = os.path.dirname(os.path.abspath(__file__))
FLOORS = os.path.join(_HERE, "..", "plugin_linear_ascent", "content", "floors")
ART = os.path.join(_HERE, "..", "content", "art", "creatures")
RAW = os.path.join(ART, "raw")
PREVIEW = os.path.join(ART, "preview")

BANNER = (320, 112)   # 20:7 — every encounter and regular warden
TALL = (320, 200)     # 8:5 — milestone bosses only

BAYER = [
    [0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44, 4, 36, 14, 46, 6, 38], [60, 28, 52, 20, 62, 30, 54, 22],
    [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21],
]

STYLE = (
    "1-bit pixel art banner in the classic Macintosh / Playdate / 1-bit Akira "
    "poster style. STRICTLY two colors: pure black and pure white — every "
    "midtone rendered as ordered Bayer dithering. The image must be FULL OF "
    "designed gradients: a large gradient sky, soft glow ramps radiating "
    "from every light source, gradient pools of light on the ground, "
    "atmospheric depth where far things dissolve into sparse dither. "
    "Wide cinematic creature shot: ONE dominant creature as the clear focal "
    "subject, large in frame, strong readable silhouette, three-quarter "
    "view, low horizon, rim light from the top-left, rich dithered texture "
    "in ground and sky. Chunky visible pixels. No text, no borders, no "
    "watermark. "
)

# Tier lighting per plan §2 sky progression — appended to every prompt.
TIER_LIGHT = {
    1: ("Setting: stolen meadowland under the tower's floodlights at dusk — "
        "a LUMINOUS gradient dusk sky, bright at the horizon, floodlight "
        "beams sweeping the grass, hedgerow lines, distant tower leg."),
    2: ("Setting: dwarven fusion-halls and dead mines — great pillars, "
        "lamplight pools, rail tracks, gradient darkness overhead."),
    3: ("Setting: drowned marsh at dusk — still water mirroring a gradient "
        "sky, cairns and rusted exo-rigs, drifting grave-lights, ground "
        "mist in dithered bands."),
    4: ("Setting: lightless caverns — the darkest tier, one lantern or "
        "glow source carving a radial gradient out of pure black, web "
        "strands and server-racks catching the light."),
    5: ("Setting: ash desert under HARD BRIGHT glare — mostly white sky, "
        "sparse dither, heat shimmer, low slag dunes, a thin dark "
        "horizon."),
    6: ("Setting: glacier fortress under BRIGHT snow glare — mostly white, "
        "sparse dither, aurora bands, frozen sea, long blue-white "
        "shadows."),
    7: ("Setting: wide-open peaks ABOVE a sunlit cloud sea — a huge "
        "luminous open sky, mostly white, sparse dither, wrecked "
        "sky-ships, the great outdoors, vast and bright."),
    8: ("Setting: shadow forest under a pale paper-grey sky — bare black "
        "boughs, ground fog in smooth bands, one distant lantern halo."),
    9: ("Setting: demon siege outworks — furnace light leaking in thin "
        "bright gradient ramps, welded black iron, smoke sky, drifting "
        "sparks."),
    10: ("Setting: the obsidian citadel and reactor-throne — black glass "
         "reflecting thin bright gradient light, chains of light, deep "
         "shadow at the edges."),
}

# Appended after the YAML prose — prose sometimes quotes signage
# ("GRAND CHAMPION"), and the model will happily letter it.
NO_TEXT = (" IMPORTANT: render any signs, banners, or lettering mentioned "
           "above as illegible weathered marks — absolutely no readable "
           "letters or words anywhere in the image.")

DIM, VIOLET = "#8b93a7", "#8b5cf6"
PANEL = (0x11, 0x15, 0x1F)

sys.path.insert(0, os.path.join(_HERE, "..", "..", "plugin-image-gen"))
from plugin_image_gen import providers  # noqa: E402


def _hx(s: str) -> tuple[int, int, int]:
    return tuple(int(s[i:i + 2], 16) for i in (1, 3, 5))


def load_jobs() -> list[dict]:
    """One job per image: encounters + wardens, prompts from YAML prose."""
    jobs = []
    for path in sorted(glob.glob(os.path.join(FLOORS, "floor_*.yaml"))):
        d = yaml.safe_load(open(path))
        floor, tier = d["floor"], d["tier"]
        light = TIER_LIGHT[tier]
        for e in d["encounters"]:
            prose = " ".join(e["prose"].split())
            jobs.append({
                "slug": e["id"], "floor": floor, "size": BANNER,
                "tint": DIM,
                "prompt": (f"{STYLE}Creature: {e['name']}. {prose} "
                           f"{light}{NO_TEXT}"),
            })
        milestone = floor % 10 == 0
        prose = " ".join(d["warden"]["prose"].split())
        jobs.append({
            "slug": (d["banner"] if milestone else f"warden_{floor:03d}"),
            "floor": floor, "size": TALL if milestone else BANNER,
            "tint": VIOLET,
            "prompt": (f"{STYLE}Creature: {d['warden']['name']}, the floor "
                       f"boss guarding the stair-gate. {prose} {light}{NO_TEXT}"),
        })
    # keep first occurrence when an id repeats across floors
    seen, uniq = set(), []
    for j in jobs:
        if j["slug"] not in seen:
            seen.add(j["slug"])
            uniq.append(j)
    return uniq


def to_1bit(img: Image.Image, w: int, h: int) -> list[list[int]]:
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
        [1 if px[x, y] / 255 > (BAYER[y % 8][x % 8] + 0.5) / 64 else 0
         for x in range(w)]
        for y in range(h)
    ]


def bits_to_png(bits: list[list[int]], color: tuple[int, int, int],
                scale: int = 1, bg: tuple[int, int, int] | None = None) -> Image.Image:
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


async def gen_one(job: dict, api_key: str) -> str:
    w, h = job["size"]
    aspect = "21:9" if (w, h) == BANNER else "16:10"
    res = await providers.generate(
        providers.MODELS["nano-banana-pro"], job["prompt"],
        aspect=aspect, api_key=api_key,
    )
    if "error" in res:
        return f"FAIL {job['slug']}: {res['error']} — {str(res.get('detail'))[:200]}"
    raw = Image.open(io.BytesIO(res["image_bytes"]))
    raw.save(os.path.join(RAW, f"{job['slug']}_raw.png"))
    bits = to_1bit(raw, w, h)
    bits_to_png(bits, (255, 255, 255)).save(
        os.path.join(ART, f"{job['slug']}_{w}x{h}.png"))
    bits_to_png(bits, _hx(job["tint"]), scale=2, bg=PANEL).save(
        os.path.join(PREVIEW, f"{job['slug']}_preview.png"))
    ink = sum(map(sum, bits)) / (w * h)
    return f"ok   {job['slug']}: ink {ink:.0%}"


def contact_sheet(jobs: list[dict], name: str) -> str | None:
    tiles = []
    for j in jobs:
        p = os.path.join(PREVIEW, f"{j['slug']}_preview.png")
        if os.path.exists(p):
            tiles.append((j["slug"], Image.open(p)))
    if not tiles:
        return None
    pad, label_h, cols = 16, 18, 2
    tw = max(im.width for _, im in tiles)
    th = max(im.height for _, im in tiles) + label_h
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (tw + pad) + pad, rows * (th + pad) + pad), PANEL)
    from PIL import ImageDraw
    draw = ImageDraw.Draw(sheet)
    for i, (slug, im) in enumerate(tiles):
        x = pad + (i % cols) * (tw + pad)
        y = pad + (i // cols) * (th + pad)
        draw.text((x, y), slug, fill=(0x8B, 0x93, 0xA7))
        sheet.paste(im, (x, y + label_h))
    out = os.path.join(PREVIEW, f"sheet_{name}.png")
    sheet.save(out)
    return out


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slugs", nargs="*", help="specific slugs to (re)generate")
    ap.add_argument("--floor", help="floor number or range, e.g. 1 or 1-10")
    args = ap.parse_args()

    api_key = os.environ.get("LUNA_GEMINI_API_KEY", "").strip()
    if not api_key:
        sys.exit("LUNA_GEMINI_API_KEY not set")
    for d in (ART, RAW, PREVIEW):
        os.makedirs(d, exist_ok=True)

    jobs = load_jobs()
    if args.floor:
        m = re.fullmatch(r"(\d+)(?:-(\d+))?", args.floor)
        if not m:
            sys.exit(f"bad --floor: {args.floor}")
        lo, hi = int(m.group(1)), int(m.group(2) or m.group(1))
        jobs = [j for j in jobs if lo <= j["floor"] <= hi]
    if args.slugs:
        have = {j["slug"]: j for j in jobs}
        missing = [s for s in args.slugs if s not in have]
        if missing:
            sys.exit(f"unknown slugs: {missing}")
        jobs = [have[s] for s in args.slugs]
    if not jobs:
        sys.exit("nothing to do")

    for i in range(0, len(jobs), 4):
        batch = jobs[i:i + 4]
        for line in await asyncio.gather(*(gen_one(j, api_key) for j in batch)):
            print(line, flush=True)

    name = (f"floor_{jobs[0]['floor']:03d}" if len({j["floor"] for j in jobs}) == 1
            else "run")
    sheet = contact_sheet(jobs, name)
    if sheet:
        print(f"sheet {os.path.relpath(sheet, os.path.join(_HERE, '..'))}")


if __name__ == "__main__":
    asyncio.run(main())
