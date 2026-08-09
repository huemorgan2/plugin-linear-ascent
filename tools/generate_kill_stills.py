#!/usr/bin/env python3
"""Linear Ascent kill stills — step 1+2 of the image-first reel pipeline.

Plan 044: the 038 text-to-video reels lost the 009 kill reels' quality
because nothing was validated before motion. New discipline:
  1. Generate the OPENING FRAME of each kill reel as a still image
     (nano-banana-pro, 21:9, the event-gif STYLE: smooth black-and-white
     gradients — the model must NOT dither; the grid discipline is ours).
  2. Emit BOTH review forms: the raw still and the pixelised result of
     the exact banner post-process (center-crop 20:7, downscale to
     320x112, level-stretch, Bayer 8x8 -> two states per pixel, white
     ink on alpha, tinted 2x preview on the panel color), plus contact
     sheets. A still must read in both forms to clear for animation.
  3. (phase 3, not here) Cleared stills become image first-frame
     references for image-to-video in generate_event_gifs.py.

Floor 6 pilot: six encounters x three player classes = 18 stills, slugs
`<encounter_id>_kill_<type>` keyed to content/floors/floor_006.yaml.

Usage:
  python tools/generate_kill_stills.py            # everything missing
  python tools/generate_kill_stills.py grave_moth_kill_arrow  # by slug
  python tools/generate_kill_stills.py --force    # re-shoot existing
  python tools/generate_kill_stills.py --repixel  # redo post-process only

Outputs (repo-root content/, reference material — never ships):
  content/art/events/stills/raw/<slug>.png
  content/art/events/stills/<slug>_320x112.png
  content/art/events/stills/preview/<slug>_preview.png
  content/art/events/stills/sheet_raw.jpg, sheet_pixel.png
"""

from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from PIL import Image, ImageDraw

_HERE = os.path.dirname(os.path.abspath(__file__))
STILLS = os.path.join(_HERE, "..", "content", "art", "events", "stills")
RAW = os.path.join(STILLS, "raw")
PREVIEW = os.path.join(STILLS, "preview")
W, H = 320, 112

API_ROOT = "https://generativelanguage.googleapis.com/v1beta"
IMAGE_MODEL = os.environ.get("STILL_MODEL", "gemini-3-pro-image")

BAYER = [
    [0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44, 4, 36, 14, 46, 6, 38], [60, 28, 52, 20, 62, 30, 54, 22],
    [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21],
]
PANEL = (0x11, 0x15, 0x1F)
DIM, VIOLET = "#8b93a7", "#8b5cf6"

STYLE = (
    "Stark high-contrast BLACK AND WHITE cinematic still frame, in the "
    "spirit of 1-bit Macintosh / Playdate pixel art posters: bold dark "
    "silhouettes against luminous gradient light, smooth glow ramps "
    "from every light source, atmospheric haze, deep blacks and bright "
    "whites, almost no midtones. Smooth gradients ONLY — no dithering, "
    "no pixelation, no grain. Wide cinematic shot, low horizon, every "
    "figure LARGE and clearly readable with a bold silhouette, all "
    "action kept in the central horizontal band of the frame. Exactly "
    "ONE creature and ONE defender in the frame, nothing and nobody "
    "else. No color, no text, no watermark. Scene: "
)

# 009 art canon — the three showcase characters (vision/story.md).
CAST_WARRIOR = (
    "a female human warrior silhouette — compact and athletic, straight "
    "sword in hand, a round shield slung on her back")
CAST_ARCHER = (
    "a slender male elf archer silhouette — tall and light on his feet, "
    "long sharp ears, a longbow in hand and a quiver at his hip")
CAST_WIZARD = (
    "a dwarf wizard silhouette rendered as a GIANT — slab-built mountain "
    "folk, two heads taller than a human and visibly wider, a huge "
    "bearded mass that looms over the frame, holding a heavy iron-shod "
    "staff with a softly glowing head")

# Floor 6, The Threshold Dark: the vault country past the last light.
SETTING = (
    "Deep inside a lightless cavern vault — a soft pale guano-banked "
    "floor, sheets of ancient silk in the high corners, stone roof lost "
    "in blackness, total dark beyond the light. ")

# encounter id -> (mid-attack description, preview tint)
CREATURES: dict[str, tuple[str, str]] = {
    "grave_moth": (
        "a pallid grave-rat with wide bat-like skin-flaps spread, diving "
        "through the light at head height in a burst of glowing "
        "grave-dust", DIM),
    "guano_vole": (
        "a bloated blind cave vole the size of a hound, pale-eyed, "
        "humping up out of the soft floor mid-lunge, loose ground "
        "spraying", DIM),
    "silk_broodling": (
        "a dog-sized cave broodling spider riding a single silk thread "
        "down from the black roof, forelegs first, legs spread wide "
        "against the glow", DIM),
    "vault_weaver": (
        "a sentinel ambush-spider the size of an ox descending head-first "
        "on a cable of steel silk from the unseen roof, eight eyes "
        "catching the light as eight bright points", DIM),
    "lane_boar": (
        "a blind guano-crusted boar filling the mouth of a narrow stone "
        "passage wall to wall, head down, front-on, mid-charge", DIM),
    "wrapped_husk": (
        "a man-shaped cocoon of pale silk walking upright out of the "
        "dark, trailing loose threads, blank where a face should be",
        VIOLET),
}

# class -> confrontation layout; {attack} is the creature mid-attack.
# The still is the frame BEFORE the kill — the frame video starts from.
LAYOUTS = {
    "melee": (
        f"{CAST_WARRIOR} stands at the RIGHT third of the frame inside "
        "the hard radial pool of a shielded storm-lamp at her hip, sword "
        "raised to strike, facing LEFT. At the LEFT third, {attack}, "
        "closing on her."),
    "arrow": (
        f"{CAST_ARCHER} stands at the far LEFT edge of the frame in the "
        "pool of a shielded lamp set on a rock at his feet, longbow "
        "drawn to full anchor, a short arrow nocked, aiming RIGHT. At "
        "the far RIGHT edge, {attack} — a long stretch of open cavern "
        "floor between them, faint silk-strands catching light along "
        "the gallery."),
    "magic": (
        f"{CAST_WIZARD} looms at the RIGHT third of the frame, staff "
        "planted, its head blazing a wide radial gradient of light that "
        "pools across the floor, facing LEFT. At the LEFT third, "
        "{attack}, lit hard by the staff-glow."),
}


def jobs() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for cid, (attack, tint) in CREATURES.items():
        for dtype, layout in LAYOUTS.items():
            out[f"{cid}_kill_{dtype}"] = {
                "prompt": STYLE + SETTING + layout.format(attack=attack),
                "tint": tint,
            }
    return out


# ── Gemini image call (stdlib, same shape as the gemini-image skill) ────
def _api_key() -> str:
    for name in ("LUNA_GEMINI_API_KEY", "GEMINI_API_KEY"):
        if os.environ.get(name):
            return os.environ[name]
    envf = os.path.join(_HERE, "..", "..", "luna", ".env")
    if os.path.isfile(envf):
        for line in open(envf):
            line = line.strip()
            for name in ("LUNA_GEMINI_API_KEY", "GEMINI_API_KEY"):
                if line.startswith(name + "="):
                    v = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if v:
                        return v
    sys.exit("no Gemini key: set LUNA_GEMINI_API_KEY or add to ../luna/.env")


def gen_image(prompt: str, key: str, out_png: str) -> None:
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {"aspectRatio": "21:9"},
        },
    }
    req = urllib.request.Request(
        f"{API_ROOT}/models/{IMAGE_MODEL}:generateContent?key={key}",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"})
    last = ""
    for attempt in range(3):
        try:
            d = json.load(urllib.request.urlopen(req, timeout=300))
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}: {e.read().decode()[:300]}"
            continue
        parts = (d.get("candidates") or [{}])[0].get(
            "content", {}).get("parts", [])
        for part in parts:
            inl = part.get("inlineData") or part.get("inline_data")
            if inl:
                with open(out_png, "wb") as fh:
                    fh.write(base64.b64decode(inl["data"]))
                return
        last = "no image part: " + " ".join(
            p.get("text", "") for p in parts)[:300]
    raise RuntimeError(last)


# ── banner post-process, single frame (same math as generate_event_gifs) ─
def crop_gray(img: Image.Image) -> Image.Image:
    img = img.convert("L")
    w, h = img.size
    target = W / H
    if w / h > target:
        nw = int(h * target)
        img = img.crop(((w - nw) // 2, 0, (w + nw) // 2, h))
    else:
        nh = int(w / target)
        img = img.crop((0, (h - nh) // 2, w, (h + nh) // 2))
    return img.resize((W, H), Image.LANCZOS)


def levels(img: Image.Image) -> tuple[int, int]:
    hist = img.histogram()
    total = sum(hist)
    cut = total // 100
    lo, acc = 0, 0
    for i in range(256):
        acc += hist[i]
        if acc > cut:
            lo = i
            break
    hi, acc = 255, 0
    for i in range(255, -1, -1):
        acc += hist[i]
        if acc > cut:
            hi = i
            break
    return lo, max(hi, lo + 1)


def to_bits(img: Image.Image, lo: int, hi: int) -> list[list[int]]:
    px = img.load()
    scale = 255 / (hi - lo)
    return [
        [1 if max(0, min(255, (px[x, y] - lo) * scale)) / 255
             > (BAYER[y % 8][x % 8] + 0.5) / 64 else 0
         for x in range(W)]
        for y in range(H)
    ]


def _hx(s: str) -> tuple[int, int, int]:
    s = s.lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


def bits_to_frame(bits: list[list[int]], color: tuple[int, int, int],
                  scale: int = 1,
                  bg: tuple[int, int, int] | None = None) -> Image.Image:
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


def pixelise(slug: str, tint: str) -> float:
    g = crop_gray(Image.open(os.path.join(RAW, f"{slug}.png")))
    lo, hi = levels(g)
    bits = to_bits(g, lo, hi)
    bits_to_frame(bits, (255, 255, 255)).save(
        os.path.join(STILLS, f"{slug}_{W}x{H}.png"))
    bits_to_frame(bits, _hx(tint), scale=2, bg=PANEL).save(
        os.path.join(PREVIEW, f"{slug}_preview.png"))
    return sum(map(sum, bits)) / (W * H)


# ── contact sheets: 6 creature rows x 3 class columns, labeled ──────────
def sheets(all_jobs: dict[str, dict]) -> None:
    cols = list(LAYOUTS)
    rows = list(CREATURES)
    pad, label_h = 8, 16
    for kind, tile, src, out_name in (
            ("raw", (480, 168), RAW, "sheet_raw.jpg"),
            ("pixel", (W * 2, H * 2), PREVIEW, "sheet_pixel.png")):
        tw, th = tile
        sheet = Image.new(
            "RGB", (pad + (tw + pad) * len(cols),
                    pad + (th + label_h + pad) * len(rows)), PANEL)
        d = ImageDraw.Draw(sheet)
        for r, cid in enumerate(rows):
            for c, dtype in enumerate(cols):
                slug = f"{cid}_kill_{dtype}"
                name = (f"{slug}.png" if kind == "raw"
                        else f"{slug}_preview.png")
                path = os.path.join(src, name)
                x = pad + c * (tw + pad)
                y = pad + r * (th + label_h + pad)
                d.text((x, y + 2), slug, fill=(139, 147, 167))
                if os.path.isfile(path):
                    im = Image.open(path).convert("RGB").resize(
                        (tw, th), Image.LANCZOS)
                    sheet.paste(im, (x, y + label_h))
        sheet.save(os.path.join(STILLS, out_name))
        print(f"sheet: {os.path.join(STILLS, out_name)}", flush=True)


def main() -> None:
    argv = sys.argv[1:]
    force = "--force" in argv
    repixel = "--repixel" in argv
    picked = [a for a in argv if not a.startswith("--")]
    all_jobs = jobs()
    bad = [s for s in picked if s not in all_jobs]
    if bad:
        sys.exit(f"unknown slug(s): {' '.join(bad)}\n"
                 f"known: {' '.join(all_jobs)}")
    todo = {s: all_jobs[s] for s in (picked or all_jobs)}
    for p in (STILLS, RAW, PREVIEW):
        os.makedirs(p, exist_ok=True)

    if not repixel:
        key = _api_key()

        def shoot(item: tuple[str, dict]) -> str:
            slug, cfg = item
            out_png = os.path.join(RAW, f"{slug}.png")
            if os.path.isfile(out_png) and not force:
                return f"skip {slug}: raw exists"
            try:
                gen_image(cfg["prompt"], key, out_png)
            except Exception as e:  # noqa: BLE001 — report, keep batch
                return f"FAIL {slug}: {e}"
            return f"ok   {slug}"

        with ThreadPoolExecutor(max_workers=4) as ex:
            for line in ex.map(shoot, todo.items()):
                print(line, flush=True)

    for slug, cfg in todo.items():
        if os.path.isfile(os.path.join(RAW, f"{slug}.png")):
            ink = pixelise(slug, cfg["tint"])
            print(f"1bit {slug}: ink {ink:.0%}", flush=True)
    sheets(all_jobs)


if __name__ == "__main__":
    main()
