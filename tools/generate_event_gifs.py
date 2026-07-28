#!/usr/bin/env python3
"""Linear Ascent event GIFs — Veo video, forced to true 1-bit, frame by frame.

Same discipline as generate_banners.py (styleguide: design/pixel_art.md),
extended in time:
  1. Veo (via the Gemini API) films a short, locked-off, high-contrast
     black-and-white shot of the event. The model provides motion and
     gradients; it is NOT asked to dither — dither at video resolution
     would turn to mush when downscaled.
  2. Every frame goes through the banner post-process: center-crop to
     20:7, downscale to the native 320x112 grid, level-stretch, Bayer 8x8
     ordered dither -> exactly two states per pixel, white ink on
     transparency. Contrast levels are computed ONCE across all frames
     (not per frame) so the animation doesn't flicker.
  3. Frames are assembled into a GIF at the native grid, plus a 2x
     tinted preview on the panel color for review. One-shot events
     (kills) play ONCE and hold the final still frame; ambient scenes
     (the opening tower) loop forever with a crossfaded seam.

Two video backends:
  fal (default) — Kling 2.5 Turbo Pro via fal.ai; much better action
      coherence (bodies, impacts, falls) than Veo. Key: $FAL_KEY or
      FAL_KEY= in ../luna/.env. Text-to-video only.
  veo — Gemini API Veo 3.1; still used automatically for events with an
      `image` first-frame reference (fal path here has no image-to-video).
      Key: $LUNA_GEMINI_API_KEY.

Usage:
  python tools/generate_event_gifs.py [slug ...]
  python tools/generate_event_gifs.py boar_kill --backend veo           # force the old backend
  python tools/generate_event_gifs.py boar_kill --from-video path.mp4   # skip generation, reuse a clip
  python tools/generate_event_gifs.py boar_kill --force                 # re-shoot even if the mp4 exists

Outputs: content/art/events/<slug>_320x112.gif        (white ink, alpha)
         content/art/events/preview/<slug>_preview.gif (tinted, on panel, 2x)
         content/art/events/raw/<slug>.mp4             (Veo output, for reference)
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(_HERE, "..", "plugin_linear_ascent", "content", "art",
                   "events")
# Raw Veo mp4s are reference material, not runtime assets — they live at the
# repo root (like banners/creatures raw) so they never ship in the plugin zip.
RAW = os.path.join(_HERE, "..", "content", "art", "events", "raw")
PREVIEW = os.path.join(ART, "preview")
W, H = 320, 112  # same native grid as the scene banners
FPS = 12         # GIF playback rate; Veo footage is resampled down to this

API_ROOT = "https://generativelanguage.googleapis.com/v1beta"
VIDEO_MODEL = "veo-3.1-generate-preview"

FAL_QUEUE = "https://queue.fal.run"
FAL_MODEL = "fal-ai/kling-video/v2.5-turbo/pro/text-to-video"
NEGATIVE = "color, text, captions, watermark, camera shake, zoom, pan"

BAYER = [
    [0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44, 4, 36, 14, 46, 6, 38], [60, 28, 52, 20, 62, 30, 54, 22],
    [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21],
]

STYLE = (
    "Stark high-contrast BLACK AND WHITE short film shot, in the spirit of "
    "1-bit Macintosh / Playdate pixel art posters: bold dark silhouettes "
    "against luminous gradient light, smooth glow ramps from every light "
    "source, atmospheric haze, deep blacks and bright whites, almost no "
    "midtones. LOCKED-OFF STATIC CAMERA on a tripod, no camera movement, "
    "no pans, no zooms. Wide cinematic shot, low horizon, all action kept "
    "in the central horizontal band of the frame. No color, no text, no "
    "watermark. Scene: "
)

DIM, VIOLET, GOLD, RED = "#8b93a7", "#8b5cf6", "#f5a524", "#f4645f"

# ── 009 art canon: the three showcase characters ─────────────────────────
# Every human figure in event art is one of these three (vision/story.md
# is canon; the giant-dwarf scale rule is non-negotiable — a dwarf is two
# heads taller than a human or an elf and visibly wider, and must loom).
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

# Per-event config:
#   prompt     scene description appended to STYLE
#   tint       preview ink color
#   seconds    clip length to request from Veo (4/6/8)
#   loop       True: loop forever (ambient). False: play once, hold the
#              final frame (one-shot events like kills).
#   trim       optional (start_s, end_s) window kept from the source clip
#              (end_s None = to the end) — used to cut to a clean ending
#   hold_ms    extra time added to the final frame when loop=False
#   image      optional first-frame reference (path relative to the
#              plugin root) -> Veo image-to-video, anchors the scene to
#              existing banner art
#   crossfade  seconds of the clip's tail blended into its head when
#              loop=True, so the loop has no visible seam
#   size       output grid (defaults to the 320x112 banner grid; the
#              title card uses 320x200)
#   split      seconds (measured after trim) where the one-shot action
#              ends and the ambient tail begins. Emits TWO gifs instead
#              of one: <slug>_intro (plays once, holds) and <slug>_loop
#              (ambient tail, crossfaded seam, loops forever). Dither
#              levels are computed across BOTH segments so the pane can
#              swap intro -> loop without a visible jump. `crossfade`
#              applies to the loop segment.
EVENTS: dict[str, dict] = {
    # Legacy untyped kills (shipped 011, spear-hunter era). The prompts
    # below are recut to the canon warrior so any reshoot lands on
    # canon; the typed 009 variants supersede them at runtime.
    "boar_kill": {
        "prompt": (
            f"{CAST_WARRIOR} faces a feral boar the size of a cart in a "
            "moonlit meadow, huge luminous gradient sky behind them. The "
            "boar charges once; the warrior sidesteps and cuts it down "
            "with one clean killing sword stroke; the boar crashes to "
            "the turf and lies completely still, and the dust settles "
            "quickly. The FINAL TWO SECONDS are a perfectly still "
            "tableau: the warrior standing motionless over the dead "
            "boar, sword lowered, absolutely nothing moving — a frozen "
            "closing frame."),
        "tint": DIM, "seconds": 8, "loop": False, "hold_ms": 2000,
        # the source clip's last ~2.5s are a near-identical held tableau;
        # keep one beat of it and let hold_ms freeze the rest
        "trim": (0.0, 5.5),
    },
    "wolf_kill": {
        "prompt": (
            f"{CAST_WARRIOR} faces a gaunt grey wolf, ribs showing, "
            "beside a dark hedgerow in a moonlit meadow, a distant "
            "floodlight tower sweeping one gradient beam across the "
            "grass. The wolf lunges once; the warrior braces and meets "
            "it with one clean killing sword stroke; the wolf drops to "
            "the grass and lies completely still, and the dust settles "
            "quickly. The FINAL TWO SECONDS are a perfectly still "
            "tableau: the warrior standing motionless over the dead "
            "wolf, sword lowered, absolutely nothing moving — a frozen "
            "closing frame."),
        "tint": DIM, "seconds": 8, "loop": False, "hold_ms": 2000,
        "trim": (0.0, 5.5),
    },
    "goblin_kill": {
        "prompt": (
            f"{CAST_WARRIOR} faces a small long-eared goblin silhouette "
            "in heavy scavenged plate armor, old snapped arrows "
            "bristling from its breastplate, dragging a notched "
            "longsword beside a wooden fence rail in a dusk meadow, "
            "hedgerows and a distant watchtower behind. The armored "
            "goblin heaves the longsword up and swings once, wild; the "
            "warrior slips inside the arc and drives her sword through "
            "the gap at its collar in one clean killing thrust; the "
            "goblin crashes down in its plate and lies completely "
            "still, the longsword fallen in the grass, and the dust "
            "settles quickly. The FINAL TWO SECONDS are a perfectly "
            "still tableau: the warrior standing motionless over the "
            "fallen armored goblin, sword lowered, absolutely nothing "
            "moving — a frozen closing frame."),
        "tint": DIM, "seconds": 8, "loop": False, "hold_ms": 2000,
        "trim": (0.0, 5.5),
    },
    "brackjaw_kill": {
        "prompt": (
            f"{CAST_WARRIOR} faces Warden Brackjaw — a huge wolf of "
            "welded armor plate with glowing eyes, half machine — on a "
            "moonlit meadow before a dark stair-lift gantry, one "
            "floodlight beam raking the grass. The machine-wolf charges "
            "once; the warrior sidesteps and drives her sword deep "
            "between its armor plates in one clean killing thrust; a "
            "burst of sparks, and the machine-wolf crashes to the turf "
            "and goes dark and completely still, its eyes fading out, "
            "and the dust settles quickly. The FINAL TWO SECONDS are a "
            "perfectly still tableau: the warrior standing motionless "
            "over the dead machine, sword lowered, absolutely nothing "
            "moving — a frozen closing frame."),
        "tint": VIOLET, "seconds": 8, "loop": False, "hold_ms": 2000,
        "trim": (0.0, 5.5),
    },
    "ascent_open": {
        "prompt": (
            "the colossal tower of stacked stolen realms stands PERFECTLY "
            "STILL — the tower, its layered bands, the two great anchor "
            "chains, the ground and the sun do not move or change at all. "
            "The ONLY motion in the entire shot: the sunlit cloud deck and "
            "cloud banks drift very slowly and steadily sideways past the "
            "tower, and the sun's halo breathes almost imperceptibly. "
            "Extremely subtle, calm, ambient, continuous motion. "
            "Absolutely no zoom, no pan, no camera drift."),
        "tint": DIM, "seconds": 8, "loop": True, "crossfade": 1.5,
        "image": os.path.join("content", "art", "banners", "raw",
                              "ascent_raw.png"),
    },
    "ascent_title": {
        "prompt": (
            "the title screen stands PERFECTLY STILL — the huge blocky "
            "'LINEAR ASCENT' lettering, the colossal banded tower, its two "
            "great anchor chains, the village of shacks, the dirt road, "
            "the ground and the sun do not move or change AT ALL, frozen "
            "solid. The ONLY motion in the entire shot: the cloud deck "
            "around the tower's waist and the far cloud banks drift very "
            "slowly and steadily sideways, and the sun's halo breathes "
            "almost imperceptibly. Extremely subtle, calm, ambient, "
            "continuous motion. Absolutely no zoom, no pan, no camera "
            "drift, no new elements."),
        "tint": DIM, "seconds": 8, "loop": True, "crossfade": 1.5,
        "size": (320, 200),
        "image": os.path.join("content", "art", "title",
                              "ascent_title_raw.png"),
    },
    # ── 016 intro movie ── one scene per story beat, all 320x200.
    # Ambient scenes loop forever; scenes with an action beat are split
    # into <slug>_intro (plays once) + <slug>_loop (ambient tail).
    "intro_aldervale": {
        "prompt": (
            "a vast peaceful fantasy panorama at dusk stands PERFECTLY "
            "STILL — a river winding past a small port town, slender "
            "signal towers with beacon lights along the banks, a softly "
            "glowing forest on one side, huge mountains on the far "
            "horizon with warm furnace light at their roots; nothing "
            "moves or changes at all. The ONLY motion in the entire "
            "shot: the river water glints softly, the signal beacons "
            "pulse slowly, the forest glow and forge glow breathe "
            "almost imperceptibly, and thin mist drifts very slowly "
            "across the valley. Extremely subtle, calm, ambient, "
            "continuous motion. Absolutely no zoom, no pan, no camera "
            "drift."),
        "tint": DIM, "seconds": 8, "loop": True, "crossfade": 1.5,
        "size": (320, 200),
    },
    "intro_theft": {
        "prompt": (
            "a dark night landscape: a whole hill with a small town on "
            "it, its windows still lit, tears free of the ground along "
            "cracks of blinding light and rises slowly and majestically "
            "into the black sky, dust and debris pouring off its ragged "
            "underside, tiny human silhouettes standing at the rim of "
            "the crater below, watching their home leave without them. "
            "In the FINAL THREE SECONDS the risen land comes to rest "
            "hanging high in the sky and holds there — the only "
            "remaining motion is thin dust drifting down and the cracks "
            "of light in the ground pulsing faintly."),
        "tint": VIOLET, "seconds": 8, "split": 5.0, "crossfade": 1.0,
        "size": (320, 200),
    },
    "intro_tower": {
        "prompt": (
            "an impossibly tall megastructure tower seen from near the "
            "ground: a narrow colossal column of dozens and dozens of "
            "thin stacked horizontal bands of captured land welded with "
            "black iron seams, rising straight up PAST THE TOP OF THE "
            "FRAME — its summit is never visible, lost far above the "
            "clouds; two great anchor chains sweep down from high on "
            "its flanks to the dark ground, small engine lights glowing "
            "along the weld seams. Everything stands PERFECTLY STILL. "
            "The ONLY motion in the entire shot: a cloud deck drifts "
            "very slowly and steadily sideways across the tower's "
            "middle, and the weld lights pulse almost imperceptibly. "
            "Extremely subtle, calm, ambient, continuous motion. "
            "Absolutely no zoom, no pan, no camera drift."),
        "tint": DIM, "seconds": 8, "loop": True, "crossfade": 1.5,
        "size": (320, 200),
    },
    "intro_warden": {
        "prompt": (
            "a night scene inside a captured realm: a vast dark "
            "industrial wall of riveted black iron spans the entire "
            "background, with a single pair of enormous sealed "
            "elevator doors at its center, twenty times human height; "
            "tall thin floodlight masts rake hard beams down across a "
            "dark grassy field in front of the wall. Before the doors "
            "stands the silhouette of a Warden — a huge four-legged "
            "beast of welded armor plate, half animal half "
            "war-machine, two bright eye-lamps burning — standing "
            "guard, PERFECTLY STILL. No tents, no buildings. The ONLY "
            "motion in the entire shot: the floodlight beams flicker "
            "subtly, the Warden's shoulders rise and fall very slowly "
            "as if breathing, and its eye-lamps pulse faintly. "
            "Extremely subtle, calm, ambient, continuous motion. "
            "Absolutely no zoom, no pan, no camera drift."),
        "tint": VIOLET, "seconds": 8, "loop": True, "crossfade": 1.5,
        "size": (320, 200),
    },
    "intro_refugee": {
        # 009: the refugee walk is the showcase cast — and the dwarf
        # must visibly loom over the other two.
        "prompt": (
            "seen from behind at a low angle with a STATIC camera: "
            "three small refugee silhouettes carrying almost nothing "
            f"walk slowly side by side — {CAST_WARRIOR}; {CAST_ARCHER}; "
            f"and {CAST_WIZARD}, towering two heads over his two "
            "companions — through wreckage-strewn ground toward the "
            "base of a colossal dark banded tower that fills the whole "
            "sky ahead, then they come to a stop and stand completely "
            "still, looking up at it. In the FINAL THREE SECONDS the "
            "three figures stand motionless — the only remaining motion "
            "is thin dust drifting sideways and the tower's distant "
            "lights pulsing faintly. The camera never moves: no zoom, "
            "no pan, no tracking."),
        "tint": DIM, "seconds": 8, "split": 5.0, "crossfade": 1.0,
        "size": (320, 200),
    },
    "intro_roothollow": {
        "prompt": (
            "a quiet refugee shantytown at night huddled at the foot "
            "of a colossal dark tower wall: rows of small shacks and "
            "tents made of tarps stretched over scrap metal, several "
            "SMALL calm cookfires — only two or three of them, tiny, "
            "knee-height, far smaller than the tents — with "
            "silhouettes of figures sitting around them, warm gradient "
            "firelight pooling on the ground and shack walls against "
            "the black mass of the tower behind. Most of the camp is "
            "dark and asleep. NO large fire, NO explosion, NO big "
            "smoke plume, NO wall of flames — a calm, sleeping camp "
            "lit by a few embers. Everything stands PERFECTLY STILL "
            "except: the tiny flames flicker softly, thin smoke wisps "
            "rise slowly, and the fire glow breathes. Extremely "
            "subtle, calm, ambient, continuous motion. Absolutely no "
            "zoom, no pan, no camera drift."),
        "tint": GOLD, "seconds": 8, "loop": True, "crossfade": 1.5,
        "size": (320, 200),
    },
    "intro_stone": {
        "prompt": (
            "a night square in a refugee camp: a tall granite monolith "
            "standing on a low plinth, small silhouettes gathered "
            "around it. Engraved lines of names on the monolith ignite "
            "one by one from within with bright light, line after line "
            "down the stone; then, high above in the black sky behind "
            "it, one whole horizontal band of a colossal dark tower "
            "snaps alight, flooding the scene with light from above. "
            "In the FINAL THREE SECONDS everything holds still — the "
            "only remaining motion is the lit names shimmering faintly "
            "and the lit tower band glowing steadily."),
        "tint": GOLD, "seconds": 8, "split": 5.0, "crossfade": 1.0,
        "size": (320, 200),
    },
    "intro_shard": {
        "prompt": (
            "close shot: an open scarred hand held out, palm up, over "
            "dark rubble. A small crystal shard rises slowly from the "
            "rubble and ignites with brilliant light, coming to rest "
            "floating just above the palm, throwing hard rim light "
            "across the silhouetted figure and the wreckage around. In "
            "the FINAL THREE SECONDS the shard simply floats in place "
            "above the motionless palm — the only remaining motion is "
            "its light pulsing slowly, like breathing."),
        "tint": GOLD, "seconds": 8, "split": 5.0, "crossfade": 1.0,
        "size": (320, 200),
    },
    "intro_muster": {
        # 009: the showcase cast anchors the muster line's center; the
        # giant dwarf breaks the line's silhouette.
        "prompt": (
            "before the towering sealed doors of a fortress keep, lit "
            "by one great luminous gradient backlight: a broad line of "
            "many climber silhouettes — swords, bows, spears, one "
            "hulking salvaged war-machine frame among them — standing "
            "shoulder to shoulder facing the doors, under tall tattered "
            f"banners on poles. At the line's center: {CAST_WARRIOR}; "
            f"{CAST_ARCHER}; and {CAST_WIZARD}, looming two heads over "
            "every other climber in the line, his bulk breaking the "
            "line's silhouette. Everything stands PERFECTLY STILL "
            "except: the banners ripple slowly in the wind, thin dust "
            "drifts sideways low over the ground, and the backlight "
            "halo breathes almost imperceptibly. Extremely subtle, "
            "calm, ambient, continuous motion. Absolutely no zoom, no "
            "pan, no camera drift."),
        "tint": DIM, "seconds": 8, "loop": True, "crossfade": 1.5,
        "size": (320, 200),
    },
}

# ── 009 kill FX variants: floors 1–3 families × landing damage type ─────
# The victory scene shows YOUR kill: melee is the warrior's sword,
# arrow the archer's shot, magic the giant wizard's cast. Engine side:
# combat._kill_fx prefers <family>_kill_<type>, falls back to the
# legacy <family>_kill, and the renderer skips missing art silently.
_KILL_MONSTERS = {
    "wolf": ("a gaunt grey wolf, ribs showing, beside a dark hedgerow "
             "in a moonlit meadow", "wolf"),
    "boar": ("a feral boar the size of a cart in a moonlit meadow, "
             "huge luminous gradient sky behind", "boar"),
    "goblin": ("a small long-eared goblin in heavy scavenged plate "
               "armor dragging a notched longsword, by a wooden fence "
               "rail in a dusk meadow", "armored goblin"),
    "rat": ("a hedgerow rat grown to the size of a hound, low and "
            "quick, by a broken granary fence in a moonlit meadow",
            "giant rat"),
    "tortoise": ("a shellback tortoise the size of a cart, huge domed "
                 "shell scarred like old armor, on dark marsh ground "
                 "under thin drifting mist", "tortoise"),
    # NOTE: "translucent ghostly haunt" made Veo fail server-side
    # (code 13, twice) — the wisp-of-light wording below generates fine.
    "haunt": ("a strange wisp creature — a small drifting cloud of pale "
              "glowing light with a faint flickering core, hovering "
              "above the orchard floor between dark apple trees",
              "wisp creature"),
}

_KILL_BEATS = {
    "melee": (CAST_WARRIOR,
              "The {noun} comes on once; the warrior steps in and cuts "
              "it down with one clean killing sword stroke; the {noun} "
              "crashes down and lies completely still, and the dust "
              "settles quickly. The FINAL TWO SECONDS are a perfectly "
              "still tableau: the warrior standing motionless over the "
              "dead {noun}, sword lowered, absolutely nothing moving — "
              "a frozen closing frame."),
    "arrow": (CAST_ARCHER,
              "The shot opens MID-ACTION with zero build-up: from the "
              "very first frame the {noun} is already at a full "
              "furious sprint, charging straight at the archer, and "
              "the archer's bow is already drawn to full anchor. He "
              "looses INSTANTLY — within the first second the arrow "
              "strikes the charging {noun} hard mid-stride; its "
              "momentum carries it crashing and skidding through the "
              "grass, and it lies completely still. No waiting, no "
              "hesitation, no slow approach — charge, shot and impact "
              "are one continuous fast beat. The FINAL TWO SECONDS "
              "are a perfectly still tableau: the archer standing "
              "motionless, bow lowered, the dead {noun} on the ground "
              "before him, absolutely nothing moving — a frozen "
              "closing frame."),
    "magic": (CAST_WIZARD,
              "The {noun} closes in; the giant wizard plants his staff "
              "and one brilliant bolt of light leaps from its glowing "
              "head and strikes the {noun}; a hard flash, and the "
              "{noun} drops and lies dark and completely still. The "
              "FINAL TWO SECONDS are a perfectly still tableau: the "
              "giant wizard standing motionless, staff planted, "
              "looming over the dead {noun}, absolutely nothing "
              "moving — a frozen closing frame."),
}

for _fam, (_scene, _noun) in _KILL_MONSTERS.items():
    for _dt, (_cast, _beat) in _KILL_BEATS.items():
        EVENTS[f"{_fam}_kill_{_dt}"] = {
            "prompt": (f"{_cast} faces {_scene}. "
                       + _beat.format(noun=_noun)),
            "tint": DIM, "seconds": 8, "loop": False, "hold_ms": 2000,
            "trim": (0.0, 5.5),
        }

# Per-clip recuts of specific Kling takes — cut the tail before any
# stray post-tableau motion (e.g. the archer re-nocking an arrow).
EVENTS["wolf_kill_arrow"]["trim"] = (0.0, 4.6)

PANEL = (0x11, 0x15, 0x1F)


def _hx(s: str) -> tuple[int, int, int]:
    return tuple(int(s[i:i + 2], 16) for i in (1, 3, 5))


# ── Veo ──────────────────────────────────────────────────────────────────

def _ref_16x9_png(path: str) -> bytes:
    """Prepare a reference image for Veo: center-crop it to the event's
    OUTPUT aspect (W:H), then letterbox to exactly 16:9 by edge-replicating
    border rows/columns. Veo then has no reason to crop or reframe, and the
    final W:H center-crop of the video removes exactly the padding, so the
    GIF comes back with the reference's own composition."""
    import io
    img = Image.open(path).convert("RGB")
    w, h = img.size
    target = W / H
    if w / h > target:
        nw = round(h * target)
        img = img.crop(((w - nw) // 2, 0, (w + nw) // 2, h))
    elif w / h < target:
        nh = round(w / target)
        img = img.crop((0, (h - nh) // 2, w, (h + nh) // 2))
    w, h = img.size
    if w / h > 16 / 9:  # wider than the video frame -> pad top/bottom
        th = round(w * 9 / 16)
        out = Image.new("RGB", (w, th))
        top = (th - h) // 2
        out.paste(img, (0, top))
        for y in range(top):
            out.paste(img.crop((0, 0, w, 1)), (0, y))
        for y in range(top + h, th):
            out.paste(img.crop((0, h - 1, w, h)), (0, y))
        img = out
    elif w / h < 16 / 9:  # taller -> pad left/right
        tw = round(h * 16 / 9)
        out = Image.new("RGB", (tw, h))
        left = (tw - w) // 2
        out.paste(img, (left, 0))
        for x in range(left):
            out.paste(img.crop((0, 0, 1, h)), (x, 0))
        for x in range(left + w, tw):
            out.paste(img.crop((w - 1, 0, w, h)), (x, 0))
        img = out
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def veo_generate(prompt: str, seconds: int, api_key: str, out_mp4: str,
                 image: str | None = None) -> None:
    instance: dict = {"prompt": prompt}
    if image:
        import base64
        instance["image"] = {
            "bytesBase64Encoded": base64.b64encode(
                _ref_16x9_png(image)).decode(),
            "mimeType": "image/png",
        }
    body = {
        "instances": [instance],
        "parameters": {
            "aspectRatio": "16:9",
            "resolution": "720p",
            "durationSeconds": seconds,
            "negativePrompt": NEGATIVE,
        },
    }
    req = urllib.request.Request(
        f"{API_ROOT}/models/{VIDEO_MODEL}:predictLongRunning?key={api_key}",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    op = json.load(urllib.request.urlopen(req))
    name = op["name"]
    print(f"  veo operation {name}", flush=True)
    while not op.get("done"):
        time.sleep(10)
        op = json.load(urllib.request.urlopen(
            f"{API_ROOT}/{name}?key={api_key}"))
        print("  ...waiting", flush=True)
    if "error" in op:
        raise RuntimeError(f"veo error: {op['error']}")
    resp = op.get("response", {})
    vids = (resp.get("generateVideoResponse", {}).get("generatedSamples")
            or resp.get("generatedVideos") or [])
    if not vids:
        raise RuntimeError(f"no video in response: {json.dumps(resp)[:500]}")
    uri = vids[0]["video"]["uri"]
    dl = urllib.request.Request(uri, headers={"x-goog-api-key": api_key})
    with urllib.request.urlopen(dl) as r, open(out_mp4, "wb") as f:
        f.write(r.read())
    print(f"  saved {out_mp4} ({os.path.getsize(out_mp4) // 1024} KB)", flush=True)


# ── fal.ai (Kling 2.5 Turbo Pro) ─────────────────────────────────────────

def _fal_key() -> str:
    key = os.environ.get("FAL_KEY", "").strip()
    if key:
        return key
    env = os.path.join(_HERE, "..", "..", "luna", ".env")
    if os.path.isfile(env):
        with open(env) as f:
            for line in f:
                line = line.strip()
                if line.startswith("FAL_KEY="):
                    return line.split("=", 1)[1].strip().strip("'\"")
    sys.exit("FAL_KEY not set (env var or luna/.env)")


def _fal_json(url: str, key: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Key {key}"},
    )
    for attempt in range(5):
        try:
            return json.load(urllib.request.urlopen(req, timeout=60))
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"fal {e.code} at {url}: "
                               f"{e.read().decode()[:500]}") from e
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if attempt == 4:
                raise
            print(f"  network error ({e}), retrying...", flush=True)
            time.sleep(10 * (attempt + 1))


def fal_generate(prompt: str, seconds: int, key: str, out_mp4: str) -> None:
    # Kling durations are 5 or 10. Kills (configured 8s for Veo) fit a 5s
    # Kling clip — its action pacing is denser — and the freeze frame
    # comes from the prompt's closing tableau + hold_ms, not clip length.
    body = {
        "prompt": prompt,
        "duration": "5" if seconds <= 8 else "10",
        "aspect_ratio": "16:9",
        "negative_prompt": NEGATIVE,
    }
    sub = _fal_json(f"{FAL_QUEUE}/{FAL_MODEL}", key, body)
    print(f"  fal request {sub['request_id']}", flush=True)
    status = sub["status_url"]
    while True:
        time.sleep(8)
        st = _fal_json(status, key)
        s = st.get("status")
        print(f"  ...{s}", flush=True)
        if s == "COMPLETED":
            break
        if s not in ("IN_QUEUE", "IN_PROGRESS"):
            raise RuntimeError(f"fal status: {json.dumps(st)[:500]}")
    resp = _fal_json(sub["response_url"], key)
    uri = resp["video"]["url"]
    for attempt in range(5):
        try:
            with urllib.request.urlopen(uri, timeout=120) as r, \
                    open(out_mp4, "wb") as f:
                f.write(r.read())
            break
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if attempt == 4:
                raise
            print(f"  download error ({e}), retrying...", flush=True)
            time.sleep(10 * (attempt + 1))
    print(f"  saved {out_mp4} ({os.path.getsize(out_mp4) // 1024} KB)",
          flush=True)


# ── 1-bit pipeline (banner post-process, temporally stable) ──────────────

def read_frames(mp4: str, fps: int) -> list[Image.Image]:
    import imageio
    frames = []
    rdr = imageio.get_reader(mp4)
    src_fps = rdr.get_meta_data().get("fps", 24)
    step = max(1, round(src_fps / fps))
    for i, fr in enumerate(rdr):
        if i % step == 0:
            frames.append(Image.fromarray(fr))
    rdr.close()
    print(f"  {len(frames)} frames @ ~{src_fps / step:.1f} fps "
          f"(source {src_fps:.1f})", flush=True)
    return frames


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


def global_levels(frames: list[Image.Image]) -> tuple[int, int]:
    """One contrast stretch for the whole clip (autocontrast cutoff=1,
    but computed on the pooled histogram so frames don't flicker)."""
    hist = [0] * 256
    for f in frames:
        for i, c in enumerate(f.histogram()):
            hist[i] += c
    total = sum(hist)
    cut = total // 100  # 1% each tail, like ImageOps.autocontrast(cutoff=1)
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


def bits_to_frame(bits: list[list[int]], color: tuple[int, int, int],
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


def _durations(n: int, fps: int, loop: bool, hold_ms: int) -> list[int]:
    d = [round(1000 / fps)] * n
    if not loop:
        d[-1] += hold_ms
    return d


def save_gif_transparent(frames: list[Image.Image], path: str, fps: int,
                         loop: bool, hold_ms: int = 0) -> None:
    """White-ink-on-alpha GIF: palette index 0 transparent, index 1 white.
    loop=False omits the NETSCAPE loop extension -> plays once and holds
    the last frame."""
    pal = [0, 0, 0, 255, 255, 255] + [0, 0, 0] * 254
    pframes = []
    for f in frames:
        p = Image.new("P", f.size, 0)
        p.putpalette(pal)
        pp, fp = p.load(), f.load()
        for y in range(f.size[1]):
            for x in range(f.size[0]):
                if fp[x, y][3]:
                    pp[x, y] = 1
        pframes.append(p)
    kw = {"loop": 0} if loop else {}
    pframes[0].save(
        path, save_all=True, append_images=pframes[1:],
        duration=_durations(len(pframes), fps, loop, hold_ms),
        transparency=0, disposal=2, **kw,
    )


def save_gif_opaque(frames: list[Image.Image], path: str, fps: int,
                    loop: bool, hold_ms: int = 0) -> None:
    kw = {"loop": 0} if loop else {}
    frames[0].convert("RGB").save(
        path, save_all=True,
        append_images=[f.convert("RGB") for f in frames[1:]],
        duration=_durations(len(frames), fps, loop, hold_ms), **kw,
    )


# ── driver ───────────────────────────────────────────────────────────────

def crossfade_loop(grays: list[Image.Image], k: int) -> list[Image.Image]:
    """Blend the clip's last k frames into its first k, then drop the tail:
    frame j (j<k) becomes tail*(1-a) + head*a with a ramping up, so the
    GIF's wrap from the last kept frame back to frame 0 is continuous."""
    n = len(grays)
    m = n - k
    out = []
    for j in range(m):
        if j < k:
            a = (j + 1) / (k + 1)
            out.append(Image.blend(grays[m + j], grays[j], a))
        else:
            out.append(grays[j])
    return out


def _set_size(cfg: dict) -> None:
    global W, H
    W, H = cfg.get("size", (320, 112))


def process_split(slug: str, cfg: dict, grays: list[Image.Image]) -> str:
    """Two-gif output for scenes with an action beat: <slug>_intro plays
    once and holds; <slug>_loop is the ambient tail with a crossfaded
    seam. One shared level stretch across both segments keeps the pane's
    intro->loop swap invisible."""
    si = round(cfg["split"] * FPS)
    if not 0 < si < len(grays) - 1:
        raise ValueError(f"{slug}: split {cfg['split']}s outside clip")
    intro = grays[:si]
    k = max(1, round(cfg.get("crossfade", 1.0) * FPS))
    tail = crossfade_loop(grays[si:], k)
    print(f"  split: {len(intro)} intro + {len(tail)} loop frames "
          f"(crossfaded seam)", flush=True)
    lo, hi = global_levels(intro + tail)
    print(f"  levels {lo}..{hi} (shared across segments)", flush=True)
    intro_bits = [to_bits(g, lo, hi) for g in intro]
    loop_bits = [to_bits(g, lo, hi) for g in tail]
    save_gif_transparent(
        [bits_to_frame(b, (255, 255, 255)) for b in intro_bits],
        os.path.join(ART, f"{slug}_intro_{W}x{H}.gif"), FPS, loop=False)
    save_gif_transparent(
        [bits_to_frame(b, (255, 255, 255)) for b in loop_bits],
        os.path.join(ART, f"{slug}_loop_{W}x{H}.gif"), FPS, loop=True)
    # review preview: the intro, then the tail looping a few times
    prev = [bits_to_frame(b, _hx(cfg["tint"]), scale=2, bg=PANEL)
            for b in intro_bits + loop_bits * 3]
    save_gif_opaque(prev, os.path.join(PREVIEW, f"{slug}_preview.gif"),
                    FPS, loop=True)
    n = len(intro_bits) + len(loop_bits)
    ink = (sum(sum(map(sum, b)) for b in intro_bits + loop_bits)
           / (W * H * n))
    return (f"ok   {slug}: {len(intro_bits)} intro + {len(loop_bits)} "
            f"loop frames, ink {ink:.0%}, split")


def process(slug: str, mp4: str) -> str:
    cfg = EVENTS[slug]
    _set_size(cfg)
    loop = cfg.get("loop", False)
    frames = read_frames(mp4, FPS)
    if "trim" in cfg:
        s, e = cfg["trim"]
        frames = frames[round(s * FPS):
                        round(e * FPS) if e is not None else len(frames)]
        print(f"  trimmed to {len(frames)} frames", flush=True)
    grays = [crop_gray(f) for f in frames]
    if "split" in cfg:
        return process_split(slug, cfg, grays)
    if loop and cfg.get("crossfade"):
        grays = crossfade_loop(grays, max(1, round(cfg["crossfade"] * FPS)))
        print(f"  crossfaded loop seam, {len(grays)} frames", flush=True)
    lo, hi = global_levels(grays)
    print(f"  levels {lo}..{hi}", flush=True)
    all_bits = [to_bits(g, lo, hi) for g in grays]
    hold = cfg.get("hold_ms", 0)
    ink_frames = [bits_to_frame(b, (255, 255, 255)) for b in all_bits]
    save_gif_transparent(ink_frames, os.path.join(ART, f"{slug}_{W}x{H}.gif"),
                         FPS, loop, hold)
    prev = [bits_to_frame(b, _hx(cfg["tint"]), scale=2, bg=PANEL)
            for b in all_bits]
    save_gif_opaque(prev, os.path.join(PREVIEW, f"{slug}_preview.gif"),
                    FPS, loop, hold)
    ink = sum(sum(map(sum, b)) for b in all_bits) / (W * H * len(all_bits))
    mode = "loops" if loop else "plays once"
    return f"ok   {slug}: {len(all_bits)} frames, ink {ink:.0%}, {mode}"


def main() -> None:
    args = sys.argv[1:]
    from_video = None
    backend = "fal"
    force = "--force" in args
    if force:
        args.remove("--force")
    if "--backend" in args:
        i = args.index("--backend")
        backend = args[i + 1]
        args = args[:i] + args[i + 2:]
    if backend not in ("fal", "veo"):
        sys.exit(f"unknown backend: {backend}")
    if "--from-video" in args:
        i = args.index("--from-video")
        from_video = args[i + 1]
        args = args[:i] + args[i + 2:]
    slugs = args or list(EVENTS)
    unknown = [s for s in slugs if s not in EVENTS]
    if unknown:
        sys.exit(f"unknown slugs: {unknown}; have {list(EVENTS)}")
    for d in (ART, RAW, PREVIEW):
        os.makedirs(d, exist_ok=True)
    for slug in slugs:
        mp4 = from_video or os.path.join(RAW, f"{slug}.mp4")
        if not from_video and (force or not os.path.isfile(mp4)):
            cfg = EVENTS[slug]
            _set_size(cfg)
            image = cfg.get("image")
            if image:
                image = os.path.join(_HERE, "..", image)
            # image-conditioned events stay on Veo (image-to-video)
            use = "veo" if image else backend
            print(f"gen  {slug} [{use}]...", flush=True)
            if use == "fal":
                fal_generate(STYLE + cfg["prompt"], cfg["seconds"],
                             _fal_key(), mp4)
            else:
                api_key = os.environ.get("LUNA_GEMINI_API_KEY", "").strip()
                if not api_key:
                    sys.exit("LUNA_GEMINI_API_KEY not set")
                veo_generate(STYLE + cfg["prompt"], cfg["seconds"], api_key,
                             mp4, image)
        print(process(slug, mp4), flush=True)


if __name__ == "__main__":
    main()
