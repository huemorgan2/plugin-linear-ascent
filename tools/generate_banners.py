#!/usr/bin/env python3
"""Linear Ascent scene banners — model-generated, then forced to true 1-bit.

Pipeline (styleguide: design/pixel_art.md):
  1. Gemini image model (nano-banana-pro via plugin-image-gen's provider
     client) paints the scene, 21:9, prompted for big dithered GRADIENTS —
     gradient skies, glow ramps, light pools — so the banners read alive,
     not flat silhouettes.
  2. Post-process to spec: center-crop to 20:7, downscale to the native
     grid, autocontrast, Bayer 8x8 ordered dither -> exactly two states per
     pixel, white ink on transparency. The model can return anything; the
     grid and the 1-bit discipline are enforced here.

Native 320x112 (2x the original 160x56 grid — sharper detail, still chunky
at ~2x CSS upscale with image-rendering: pixelated).

Usage: LUNA_GEMINI_API_KEY=... python tools/generate_banners.py [slug ...]
Outputs: content/art/banners/<slug>_320x112.png   (white ink, alpha)
         content/art/banners/preview/banner_<slug>_preview.png (tinted, on panel)
         content/art/banners/raw/<slug>_raw.png   (model output, for reference)
"""

from __future__ import annotations

import asyncio
import io
import os
import sys

from PIL import Image, ImageOps

_HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(_HERE, "..", "content", "art", "banners")
RAW = os.path.join(ART, "raw")
PREVIEW = os.path.join(ART, "preview")
W, H = 320, 112  # native grid — 20:7, upscaled ~2x in the card

sys.path.insert(0, os.path.join(_HERE, "..", "..", "plugin-image-gen"))
from plugin_image_gen import providers  # noqa: E402

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
    "designed gradients: a large sky that fades smoothly from dense white "
    "dither at the horizon to black at the top (or the reverse), soft glow "
    "ramps radiating from every light source, gradient pools of light on the "
    "ground, atmospheric depth where far things dissolve into sparse dither. "
    "Wide cinematic shot, low horizon, one dominant subject, light from the "
    "top-left, rich dithered texture in ground and sky. Chunky visible "
    "pixels. No text, no borders, no watermark. "
    "Scene: "
)

# slug -> (scene prompt, role tint for the preview)
DIM, VIOLET, GOLD, RED = "#8b93a7", "#8b5cf6", "#f5a524", "#f4645f"
SCENES: dict[str, tuple[str, str]] = {
    "roothollow": (
        "a frontier village at night — shack rooflines on the horizon, one "
        "colossal metal tower leg cutting the starry sky diagonally, big "
        "moon with a gradient halo, thin radio antenna with a beacon, a dirt "
        "path leading in through gradient ground haze.", DIM),
    "forge": (
        "inside a blacksmith forge — an anvil silhouetted against a blazing "
        "plasma arc whose glow falls off in a wide radial gradient, hanging "
        "chains catching the light, a wall of tools fading into darkness, "
        "gradient glow pooling on the floor.", DIM),
    "vault": (
        "a massive round wheel-lock vault door set in a heavy stone face, "
        "small keypad glowing with a soft gradient halo, coins scattered "
        "across a counter in the foreground, top-left light raking the "
        "stone in a smooth gradient.", DIM),
    "lodge": (
        "a timber longhouse at night behind a palisade line, exactly one "
        "window lit with warm gradient glow spilling onto the snow, chimney "
        "smoke drifting as a soft dithered gradient into a starry sky.", DIM),
    "medlab": (
        "an apothecary med-lab interior — shelves of flasks and bottles, an "
        "IV stand, a cross sign on the wall, one hanging lamp casting a "
        "wide gradient pool of light that dissolves into darkness at the "
        "edges.", DIM),
    "relay": (
        "a radio relay station — tall lattice mast against a sky of "
        "gradient cloud banks, a pair of dish antennas, a wall of "
        "pigeonhole letter slots below, one blinking beacon with a glow "
        "halo.", DIM),
    "guildhall": (
        "a medieval guildhall interior seen straight-on from the entrance: "
        "a big round wooden table in the center foreground, cloth banners "
        "hanging from timber crossbeams overhead, a hearth fire glowing on "
        "the back wall with a radial gradient of light spreading across the "
        "floor toward the viewer, rafters dissolving into gradient shadow "
        "above.", DIM),
    "stone": (
        "a tall standing monolith engraved with glowing name-lines that "
        "halo outward in a soft gradient, a small crowd of silhouetted "
        "figures at its base, gradient dusk sky behind.", DIM),
    "ascent": (
        "the whole Ascent seen from far away on a bright hopeful morning — "
        "one colossal megastructure tower of a hundred stacked stolen "
        "realms, a BOLD DARK silhouette against a luminous sky, rising "
        "through a sunlit cloud deck and out of frame at the top, its "
        "layers reading as a few thick clearly-separated bands of land "
        "with strong black separation lines, two great chains anchoring "
        "it to the ground, the sky a huge BRIGHT gradient of dense white "
        "dither with soft cumulus banks kept low, sun with a wide radial "
        "halo placed at one-third from the left and vertically centered, "
        "birds as sparse specks — luminous, optimistic, mostly light, all "
        "key elements inside the central horizontal band of the frame.", DIM),
    "gate": (
        "a colossal tower gate — massive doorframe filling the frame, a "
        "lift cage hanging inside, chains and one thick cable running out "
        "of frame, gradient light streaming down from above through dust.", DIM),
    "greenreach": (
        "a rolling night meadow — gradient sky from dense starlit dither "
        "down to black, one dead tree, a distant floodlight tower sweeping "
        "a wide gradient beam across the grass, a lone wolf silhouette on "
        "the crest inside the beam.", DIM),
    "gnarl": (
        "a goblin warlord's throne room, throne CENTERED in frame: a "
        "throne built from stacked rifle crates, a fat crowned goblin "
        "silhouette slouched on it, ragged banners on both sides, two "
        "torches whose glow rises in narrow gradient ramps behind the "
        "throne — the background stays mostly dark, no large bright "
        "areas, deep gradient shadows at the edges.", VIOLET),
    "ironvale": (
        "a dead dwarven mine hall — massive squared pillars receding into "
        "gradient darkness, one huge cog half-buried in rubble as the focal "
        "subject, a single hanging lamp throwing a wide radial gradient of "
        "light across rail tracks that run toward the viewer, dust in the "
        "beam as sparse dither.", DIM),
    "skarn": (
        "an orc warlord's warcamp inside a forge hall, CENTERED: a hulking "
        "silhouette in a salvaged power-armor frame standing on an anvil "
        "dais, one great axe, ragged war banners either side, a quench-fire "
        "behind him rising in a narrow gradient glow ramp, edges of the "
        "frame in deep gradient shadow.", VIOLET),
    "barrows": (
        "a drowned marsh at dusk — still water mirroring a gradient sky, "
        "one great burial cairn with a leaning standing stone as the focal "
        "subject, a rusted exo-rig skeleton knee-deep in the water, thin "
        "grave-lights drifting with soft gradient halos, ground mist as "
        "dithered bands.", DIM),
    "barrowking": (
        "a barrow king rising from an opened grave mound, CENTERED: a tall "
        "crowned wight silhouette half-out of a hillside barrow door, "
        "grave-mist pouring down the slope in smooth gradients, two rows "
        "of standing stones leading in, a pale gradient moon halo behind "
        "the crown, edges in deep shadow.", VIOLET),
    "webdeep": (
        "a giant orb spiderweb CENTERED and filling the frame inside a "
        "black cavern, one large wrapped cocoon hanging at its center as "
        "the single bold focal subject, backlit by a lantern behind the "
        "web that throws a strong radial gradient glow, web strands thick "
        "and clearly drawn against the darkness, cave edges vignetting to "
        "pure black.", DIM),
    "vyx": (
        "a monstrous spider matriarch descending on a thread, CENTERED: a "
        "vast long-legged spider silhouette dropping into a lamplit "
        "chamber, egg sacs glowing faintly along the walls with soft "
        "gradient halos, her eyes catching light in rows, the ceiling "
        "dissolving into dense black above.", VIOLET),
    "scorch": (
        "an ash desert over reactor slag — low dunes in smooth dithered "
        "gradient bands, one dead tree charred to a spike as the focal "
        "subject, a cracked reactor dome on the horizon leaking a thin "
        "vertical glow ramp, a huge gradient sky from dense dither at the "
        "horizon to black above, heat shimmer.", DIM),
    "cindermaw": (
        "a colossal fire wyrm rearing from a caldera, CENTERED: a dragon "
        "silhouette with spread wings rising out of a crater, throat and "
        "belly seams glowing in bright gradient ramps, ash-fall drifting "
        "as sparse dither, the caldera rim ringed with half-melted tribute "
        "shapes, dark gradient sky.", VIOLET),
    "frosthold": (
        "a glacier fortress over a frozen sea — a wall of hewn ice blocks "
        "with one massive gate as the focal subject, frozen waves standing "
        "mid-swell in the foreground, aurora bands rendered as smooth "
        "dithered gradients across a starry sky, one watch-fire glowing "
        "with a warm gradient halo on the rampart.", DIM),
    "hrimgar": (
        "a frost giant jarl in his mead-hall, CENTERED: a huge horned "
        "silhouette seated on an ice throne, great axe across his knees, "
        "twin fire-trenches running toward the viewer in bright gradient "
        "ramps, ice rafters dissolving into gradient darkness overhead, "
        "banners of frozen silk either side.", VIOLET),
    "stormreach": (
        "open-sky mountain peaks above a cloud deck — one wrecked sky-ship "
        "impaled on a summit as the focal subject, its masts and rigging "
        "against a huge gradient storm sky, a single lightning bolt with a "
        "soft glow halo, cloud sea below in smooth dithered bands, birds "
        "as sparse specks.", DIM),
    "zephyra": (
        "a storm queen enthroned in the eye of a hurricane, CENTERED: a "
        "regal winged silhouette on a throne of masthead and glass atop a "
        "wrecked flagship deck, a crown of lightning with a bright radial "
        "gradient halo, the eye-wall curving up both sides of the frame in "
        "smooth dithered cloud gradients.", VIOLET),
    "gloom": (
        "a shadow forest under a paper-grey sky — black boughs closing "
        "overhead, one pale stag silhouette standing on a long ride "
        "between the trees as the focal subject, a single distant lantern "
        "with a soft gradient halo, ground fog in smooth dithered bands, "
        "the treeline dissolving into darkness.", DIM),
    "huntsman": (
        "a pale huntsman with his hounds, CENTERED: a tall figure in a "
        "wide-brimmed hat holding a hunting horn, dismounted before a "
        "hall of bare birch columns, a crescent of sitting hound "
        "silhouettes around him, pale mist pooling in gradient bands, a "
        "cold gradient sky the color of a held breath.", VIOLET),
    "hellmarch": (
        "demon siege outworks — a rampart wall of welded black iron "
        "crossing the frame, one huge horned gate as the focal subject, "
        "furnace light leaking through gun-slits in thin bright gradient "
        "ramps, chimney stacks against a smoke sky rendered in smooth "
        "dithered gradients, sparks drifting upward.", DIM),
    "malgrim": (
        "a demon herald announcing before a colossal gate, CENTERED: a "
        "tall armored silhouette with a raised sword, long banner-cloak, "
        "brass throat glowing in a narrow gradient ramp, the god-scaled "
        "black gate rising behind him out of frame, parade ground lit by "
        "two braziers with radial gradient pools.", VIOLET),
    "crown": (
        "an obsidian citadel at the tower's crown — black glass spires in "
        "silhouette, one central spire holding a caged column of light as "
        "the focal subject, the reactor beam rising in a bright vertical "
        "gradient ramp into a starless sky, polished ground reflecting it "
        "in a mirrored gradient pool.", DIM),
    "vharuk": (
        "the demon king rising from a reactor throne, CENTERED: a vast "
        "crowned silhouette standing before a black seat, chains of light "
        "radiating up and out from behind him in bright gradient rays, "
        "the throne room's obsidian floor reflecting the glow in a smooth "
        "gradient pool, the court as tiny dark shapes at the frame edges.", VIOLET),
    "death": (
        "a cracked skull half-buried in an ash field, a broken crystal "
        "shard floating above it radiating faint gradient rays, ash haze "
        "as a smooth ground gradient, empty gradient sky.", RED),
    "present": (
        "a strapped wooden crate with a cable tied in a bow, sitting on a "
        "doorstep at dawn — low sun throwing long shadows and a huge "
        "smooth gradient sunrise sky, gradient light washing the ground.", GOLD),
}

PANEL = (0x11, 0x15, 0x1F)


def _hx(s: str) -> tuple[int, int, int]:
    return tuple(int(s[i:i + 2], 16) for i in (1, 3, 5))


def to_1bit(img: Image.Image) -> list[list[int]]:
    """Center-crop to 20:7, downscale to the grid, Bayer-dither to bits."""
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
    img = ImageOps.autocontrast(img, cutoff=1)  # keep the gradient ramps wide
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


async def gen_one(slug: str, api_key: str) -> str:
    prompt, tint = SCENES[slug]
    res = await providers.generate(
        providers.MODELS["nano-banana-pro"], STYLE + prompt,
        aspect="21:9", api_key=api_key,
    )
    if "error" in res:
        return f"FAIL {slug}: {res['error']} — {str(res.get('detail'))[:200]}"
    raw = Image.open(io.BytesIO(res["image_bytes"]))
    raw.save(os.path.join(RAW, f"{slug}_raw.png"))
    bits = to_1bit(raw)
    bits_to_png(bits, (255, 255, 255)).save(
        os.path.join(ART, f"{slug}_{W}x{H}.png"))
    bits_to_png(bits, _hx(tint), scale=2, bg=PANEL).save(
        os.path.join(PREVIEW, f"banner_{slug}_preview.png"))
    ink = sum(map(sum, bits)) / (W * H)
    return f"ok   {slug}: ink {ink:.0%}"


async def main() -> None:
    api_key = os.environ.get("LUNA_GEMINI_API_KEY", "").strip()
    if not api_key:
        sys.exit("LUNA_GEMINI_API_KEY not set")
    for d in (ART, RAW, PREVIEW):
        os.makedirs(d, exist_ok=True)
    slugs = sys.argv[1:] or list(SCENES)
    unknown = [s for s in slugs if s not in SCENES]
    if unknown:
        sys.exit(f"unknown slugs: {unknown}; have {list(SCENES)}")
    # Small batches: friendly to the rate limit, still ~4x faster than serial.
    for i in range(0, len(slugs), 4):
        batch = slugs[i:i + 4]
        for line in await asyncio.gather(*(gen_one(s, api_key) for s in batch)):
            print(line, flush=True)


if __name__ == "__main__":
    asyncio.run(main())
