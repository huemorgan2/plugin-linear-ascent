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
VIDEO_MODEL = os.environ.get("VEO_MODEL", "veo-3.1-generate-preview")

FAL_QUEUE = "https://queue.fal.run"
FAL_MODELS = {
    "kling": "fal-ai/kling-video/v2.5-turbo/pro/text-to-video",
    "seedance": "bytedance/seedance-2.0/text-to-video",
    "seedance-fast": "bytedance/seedance-2.0/fast/text-to-video",
}
NEGATIVE = ("color, text, captions, watermark, camera shake, zoom, pan, "
            "slow motion")

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

# 038 mercy reels render photoreal color (no 1-bit poster style) — the
# raw mp4 is the asset of record; keep the prefix tiny (xAI caps the
# whole prompt at 4096 chars).
MERCY_PREFIX = (
    "LOCKED-OFF static camera, no pans or zooms, no text, no "
    "watermark. High-contrast cinematic grade: deep shadows, figures "
    "reading a shade DARKER than the background, crisp silhouettes. "
    "Scene: "
)

# 007-art-add phase 2: photoreal footage dithers to mush — drawn frames
# survive the Bayer pass (bold outlines, flat shading planes, no
# photographic noise). Same byte discipline as MERCY_PREFIX.
# Selected with --style drawn (default for this plan's retakes).
MERCY_DRAWN_PREFIX = (
    "Hand-drawn 2D animation, shaded storybook style: bold black "
    "ink outlines, flat grey-wash shading, NOT photographic, no 3D "
    "render. Monochrome, figures DARKER than the pale ground, crisp "
    "silhouettes. LOCKED-OFF camera, no text, no watermark. Scene: "
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
            f"{CAST_WARRIOR} faces exactly ONE small long-eared goblin "
            "silhouette — there is only this single goblin in the "
            "entire scene, no other goblins or creatures ever appear — "
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
            "still tableau: the warrior standing ALONE and motionless "
            "over the single fallen armored goblin — just the two of "
            "them, no one else — sword lowered, absolutely nothing "
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
            "the website title screen stands PERFECTLY STILL — the solid "
            "filled 'LINEAR ASCENT' lettering (smaller, with sky above it), "
            "the SUPER MASSIVE stacked megastructure tower of dozens of "
            "thin Scotland-sized realm-bands on the right, its highway-thick "
            "anchor chains, the open left plain, the tiny refugee shacks, "
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

# ── 037: active sleep — one ambient loop per showcase sleeper per place ──
# fx slugs from core._sleep_fx:
#   sleep_{lodge|fields}_{warrior|archer|sorcerer}
# The 009 cast rule holds even lying down — the giant dwarf must still
# read as a mountain under the blanket.
_SLEEPERS = {
    "warrior": (
        "a female human warrior silhouette asleep on her side — compact "
        "and athletic, her straight sword and round shield leaned "
        "within arm's reach"),
    "archer": (
        "an elf archer silhouette at rest, wrapped head to toe in a "
        "heavy wool blanket with only the long sharp ears showing, an "
        "unstrung longbow and a quiver of arrows set beside the "
        "sleeping spot"),
    "sorcerer": (
        "a giant mountain-folk sorcerer silhouette asleep — a "
        "slab-built colossus under a heavy blanket that dwarfs the "
        "sleeping spot, a broad braided beard spilling over the "
        "blanket's edge, an iron-shod walking staff with a softly "
        "glowing head propped upright nearby"),
}
_SLEEP_PLACES = {
    "lodge": (
        "inside a timber lodge bunkroom at night: {who}, in a sturdy "
        "wooden bunk under a small window, a low stone hearth of "
        "breathing embers across the room, a lantern turned down low. "
        "Everything stands PERFECTLY STILL except: the sleeper's chest "
        "rises and falls slowly and steadily, the hearth embers pulse "
        "faintly, and the lantern glow breathes almost imperceptibly."),
    "fields": (
        "a night meadow outside a palisaded town: {who}, rolled in a "
        "cloak in a grassy hollow beside a small campfire burned down "
        "to embers, tall grass around the hollow, stars and a thin "
        "drifting mist above. Everything stands PERFECTLY STILL "
        "except: the sleeper's chest rises and falls slowly and "
        "steadily, the embers pulse faintly, the tall grass stirs "
        "barely, and the mist drifts very slowly sideways."),
}
for _c, _who in _SLEEPERS.items():
    for _w, _pl in _SLEEP_PLACES.items():
        EVENTS[f"sleep_{_w}_{_c}"] = {
            "prompt": (_pl.format(who=_who)
                       + " Extremely subtle, calm, ambient, continuous "
                         "motion. Absolutely no zoom, no pan, no camera "
                         "drift, nobody wakes or moves."),
            "tint": DIM, "seconds": 8, "loop": True, "crossfade": 1.5,
        }

# ── 030 Phase 8: the floor arrival reel, floors 1–10 ────────────────────
# Two ambient loops per floor — the world beat (the fields as the lift
# doors open) and the keep beat (the Warden holding the stair) — plus one
# shared one-shot demise for floors whose Warden has already fallen.
# fx slugs from core._floor_movie_scene: floor{n}_world / floor{n}_warden
# / warden_fall. Floors 11+ have no reel art and fall back to the still
# banner — the level-10 rule.
_FLOOR_WORLDS = {
    1: ("stolen meadowland rolling out under the tower's floodlights — "
        "hedgerows in their old lines fencing abandoned fields, a "
        "lamplit frontier steading with glowing windows at the meadow's "
        "edge"),
    2: ("a drowned pasture at dusk — flooded fields mirroring a gradient "
        "sky, floodlight beams lying across the water in long white "
        "bars, a stilt-town on the levee with lit windows"),
    3: ("an orchard in perfect rows gone wild at the crowns, windfall "
        "apples in the grass, a cider-press town glowing between the "
        "trunks at the far end of the rows"),
    4: ("a toppled floodlight pylon whose beam still burns along the "
        "ground — a river of white light across black grass, a goblin "
        "camp's fires dotted on the dark field beyond"),
    5: ("sheep downs with deep-worn flock paths winding over bare "
        "crests, goblin banners flying from a shearing shed, a small "
        "gate town's lamps in the valley fold"),
    6: ("sunken lanes running between banked hedges taller than a rider, "
        "lantern light spilling into the green trench of the road, a "
        "hedge-harbor town glowing at the lane's end"),
    7: ("a river pumped uphill through a captured millrace, the old "
        "watermill still turning against a luminous gradient sky, "
        "coolant pipes climbing away toward the tower"),
    8: ("a burnt common of silver-grey brittle grass whispering in the "
        "wind, goblin scavenger crews' fires in the distance, ash "
        "drifting as sparse dither on the air"),
    9: ("a fairground seized mid-festival — stalls still bunted, a "
        "carousel of painted horses frozen mid-turn, goblin lanterns "
        "strung between the gallows poles"),
    10: ("the last meadow before the lift turned parade ground — goblin "
         "banners in their hundreds, broken spears and shield-stacks raised into walls, "
         "every path raked by watch-fires"),
}
_FLOOR_WARDENS = {
    1: ("a beast of wolf and welded plate circling before a humming "
        "stair-lift, servos ticking, head lowering to charge"),
    2: ("a boar grown wrong, plated in rusted field-tin, rising out of "
        "a drowned barn with water pouring off its back"),
    3: ("a great ape-frame of orchard timber and engine parts waiting "
        "among cider vats, steam curling from its joints"),
    4: ("a wolf remade in chrome crouched at a broken pylon head, one "
        "eye a burning floodlamp throwing its shadow a mile long"),
    5: ("a great horned frame of shearing blades and ram's skull "
        "standing at the stair, pawing sparks from the flint"),
    6: ("a bear-broad thing grown into a coat of living hedge, wire "
        "and briar braided through its hide, at a lane crossing"),
    7: ("a sodden mass of wolf and weed and pump-iron under a turning "
        "waterwheel, water running from it in ropes as it stands"),
    8: ("a stag-tall frame of charcoal and grate-iron in a dead "
        "field's center, embers alive somewhere in its chest"),
    9: ("a lanky engine of crane chain and carnival brass hanging "
        "above a fairground gate, unfolding downward hook first"),
    10: ("a fat crowned goblin king slouched on a throne of stacked "
         "broken spears and siege-scrap, raising one hand as watch-fires gutter"),
}
for _n in range(1, 11):
    EVENTS[f"floor{_n}_world"] = {
        "prompt": (
            f"{_FLOOR_WORLDS[_n]}. Everything stands PERFECTLY STILL "
            "except: light breathes slowly, smoke or mist drifts "
            "sideways, small ambient flickers. Extremely subtle, calm, "
            "continuous motion. Absolutely no zoom, no pan, no people "
            "moving."),
        "tint": DIM, "seconds": 6, "loop": True, "crossfade": 1.5,
        "size": (320, 200),
    }
    EVENTS[f"floor{_n}_warden"] = {
        "prompt": (
            f"{_FLOOR_WARDENS[_n]}. The creature holds its ground in "
            "slow menace — breathing, small head movements, steam or "
            "sparks drifting — but never leaves its spot and never "
            "attacks. Extremely subtle, continuous ambient motion. "
            "Absolutely no zoom, no pan."),
        "tint": VIOLET, "seconds": 6, "loop": True, "crossfade": 1.5,
        "size": (320, 200),
    }
EVENTS["warden_fall"] = {
    "prompt": (
        "a colossal scrap-metal war-beast silhouette collapsing before "
        "great gate doors: it staggers once, drops to its knees, and "
        "crashes down in a burst of dust and sparks; the dust settles "
        "and thin smoke rises from the wreck. The FINAL TWO SECONDS "
        "are a perfectly still tableau: the dead machine-beast lying "
        "in the settled dust, gate doors standing open behind it, "
        "absolutely nothing moving — a frozen closing frame."),
    "tint": GOLD, "seconds": 8, "loop": False, "hold_ms": 2000,
    "trim": (0.0, 6.0),
    "size": (320, 200),
}
# 033: the fall reel's opening beat — a Warden dies the only way great
# Wardens die: all three climber classes in the same frame. Split art:
# the kill plays once, then the reel settles on the cooling wreck while
# the player reads the receipt.
EVENTS["warden_slain"] = {
    "prompt": (
        "a colossal scrap-metal war-beast silhouette brought down by "
        "three tiny climber silhouettes attacking TOGETHER before great "
        "gate doors: on the left a warrior silhouette drives a sword "
        "up into its chest, from the right a single bright arrow "
        "streaks in from off-frame and strikes its head, and behind "
        "them a robed sorcerer silhouette raises both arms as a lance "
        "of pale light hits the beast's back; the war-beast staggers "
        "once, drops to its knees, and crashes down in a burst of dust "
        "and sparks. Then the dust settles and thin smoke rises from "
        "the wreck while the three small silhouettes stand motionless "
        "around it — a still, held tableau, absolutely nothing moving "
        "except the thin smoke."),
    "tint": GOLD, "seconds": 8, "split": 5.0, "crossfade": 1.0,
    "size": (320, 200),
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
              "The whole scene plays at REAL speed — fast, snappy, "
              "natural timing, absolutely NO slow motion. A WIDE shot "
              "across a dusk meadow rich with detail — tall "
              "wind-stirred grass, a split-rail fence line, dark "
              "hedgerows and a distant watchtower in the haze — with "
              "real distance between the two: the archer stands "
              "at the far LEFT edge of the frame, and the {noun} is "
              "at the far RIGHT edge, already at a full furious "
              "sprint, kicking up dust and torn grass with every "
              "stride, a long stretch of open ground between them — "
              "the {noun} NEVER comes close to the archer. Both "
              "figures are LARGE and clearly readable — the {noun} "
              "is a BIG imposing beast with a bold silhouette, never "
              "a tiny distant speck — and the action sits in the "
              "MIDDLE band of the frame, horizon at mid-height, not "
              "crammed into the bottom edge. From the "
              "very first frame the bow is stretched to full anchor; "
              "the archer releases INSTANTLY. The arrow is one "
              "SINGLE SHORT normal-sized arrow — it is never "
              "stretched, never elongated, never a streak or a line "
              "— it crosses the field in a fraction of a second on a "
              "flat straight path and its head BURIES itself in the "
              "{noun}'s chest with a hard brutal thud; the short "
              "shaft stays LODGED in the body, jutting out. The "
              "impact hurls the {noun} into a violent tumble — it "
              "crashes down and skids through the grass in a burst "
              "of dust at that DISTANT spot, "
              "dead in the middle of the field far from the archer, "
              "the short arrow shaft still sticking out of its side, "
              "and lies completely still. The FINAL TWO SECONDS are "
              "a perfectly still tableau: the archer far left with "
              "his bow lowered, the dead {noun} lying far across the "
              "field with the short arrow planted in it, absolutely "
              "nothing moving — a frozen closing frame."),
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

# ── 038 mercy kills: a kill FREES what it strikes ───────────────────────
# One GIF per creature, keyed by kind (combat._kill_fx resolution):
#   native    {id}_freed   — the fever's shape drops away; the true
#                            animal underneath walks off. A cure.
#   pressed   {id}_fall    — a real death, kept somber. No triumph.
#   wrongmade {id}_evicted — the made thing comes apart; the dark that
#                            ran it drains DOWNWARD, back below.
# Jobs are built from the floors' own YAML (kind/was/prose), so the
# floor rewrite is the single source of truth. Per-kind generics cover
# any creature whose own GIF hasn't landed yet.

_MERCY_FREED = (
    "An EXTREMELY WIDE shot, camera pulled far back — both figures "
    "SMALL against the landscape, wide open ground between them. "
    "{scene} From the very FIRST frame to the last there is "
    "exactly ONE creature and ONE defender in the frame — never a "
    "pack, never a second animal, never another person. The "
    "landscape around them is completely EMPTY and DESERTED: no "
    "bystanders, no distant figures on the horizon, nobody and "
    "nothing else anywhere, however small or far away. The video "
    "BEGINS with the single creature already mid-charge on the "
    "LEFT side of the frame and the single defender on the RIGHT. "
    "The shot OPENS MID-ATTACK: the huge fevered creature "
    "is ALREADY sprinting flat-out straight AT the defender — jaws "
    "wide, ears pinned back, real animal gait, dust kicking up. "
    "FIRST EXCHANGE — the monster gets ITS blow in: it closes the "
    "whole distance and LUNGES, one full committed strike, jaws "
    "snapping shut on empty air as the defender SPRINGS BACK one "
    "step at the last instant, staying UPRIGHT ON THEIR FEET — "
    "never falling, diving, or rolling — the blow tears up the "
    "ground, dirt flying. Nobody is ever knocked down or lying "
    "on the ground in this fight. The creature overshoots, "
    "wheels around snarling, and immediately charges AGAIN from "
    "across the frame. SECOND EXCHANGE — the same defender, back "
    "on their feet, answers mid-charge: {strike} The projectile "
    "or blade is a SHORT solid object of fixed size and shape: it "
    "visibly LEAVES the weapon and CROSSES the gap, its position "
    "changing every frame — NEVER a long line, beam, rope, or "
    "streak stretching between the two figures, NEVER hovering "
    "in place, and it keeps one shape the whole flight. It is "
    "loosed while the creature is still on the FAR half of the "
    "frame, with clear empty air on BOTH sides of it mid-flight. "
    "The strike connects EARLY, while the creature is still far "
    "from the defender at full speed — and the INSTANT it "
    "touches, an ON-THE-SPOT "
    "TRANSFORMATION: the dark fevered bulk shatters off the "
    "creature like a dry husk, motes scattering, and revealed "
    "INSIDE it — at the EXACT same spot, mid-stride, one "
    "continuous body — is {was}: TINY, CAT-SIZED — no bigger "
    "than a house cat, a small fraction of the monster's bulk. The huge "
    "dark shape was all fever — a hollow inflated shell MANY "
    "times larger than the true animal inside it — so the size "
    "drop at the burst is drastic and obvious, and it is "
    "PERMANENT: the revealed animal stays this tiny for every "
    "remaining frame and NEVER grows back. "
    "ONE animal the whole time: the big dark shape and the small "
    "animal are the SAME creature before and after the burst. "
    "NOTHING new ever enters the frame. TIMING IS STRICT: the "
    "ENTIRE fight — first lunge, dodge, second charge, shot, and "
    "burst — is over within the FIRST FOUR SECONDS of the video. "
    "Never stretch or pad the action to fill time. All the remaining "
    "seconds are the calm afterwards: the revealed animal skids "
    "to a stop, shakes itself once, then "
    "SITS DOWN facing the defender, calm and content, wagging "
    "its tail (or settling its wings) — and just stays there, "
    "sitting and wagging, under a clean clear sky while the "
    "defender lowers the weapon and stands at ease. A long, "
    "quiet, happy ending. Physical, documentary-real motion "
    "throughout — the fight part is a fight, not a pose.")

# Second freed fight shape — the distant ONE-SHOT standoff: no melee
# exchange, a vast gap, the defender calmly takes a single decisive
# ranged strike mid-charge. Rotated with the two-exchange shape so the
# set stays varied. Ranged strikes only (archer / wizard).
_MERCY_FREED_FAR = (
    "An EXTREMELY WIDE landscape shot, camera pulled very far back "
    "— both figures TINY against a vast open expanse, the full "
    "width of the frame between them. {scene} From the very FIRST "
    "frame to the last there is exactly ONE creature and ONE "
    "defender in the frame — never a pack, never a second animal, "
    "never another person. The landscape is completely EMPTY and "
    "DESERTED: no bystanders, no distant figures on the horizon, "
    "nobody and nothing else anywhere, however small or far away. "
    "The video BEGINS with the single creature far away on the "
    "LEFT edge of the frame and the single defender small on the "
    "RIGHT. The huge fevered creature is ALREADY charging "
    "flat-out across the vast distance, straight AT the defender "
    "— real animal gait, dust trailing behind it. This is a "
    "SINGLE-SHOT standoff, not a melee: the defender never runs "
    "and never dodges — they calmly stand their ground, small and "
    "steady, as the charge eats up the ground between them. When "
    "the creature has crossed about HALF the gap — still far "
    "away, still small in the frame — the defender takes ONE "
    "single decisive strike: {strike} The projectile is a SHORT "
    "solid object of fixed size and shape: it visibly LEAVES the "
    "weapon and CROSSES the long gap, its position changing every "
    "frame — NEVER a long line, beam, rope, or streak stretching "
    "between the two figures, NEVER hovering in place, and it "
    "keeps one shape the whole flight, clear empty air on BOTH "
    "sides of it. The strike connects while the creature is still "
    "FAR from the defender, at full speed — and the INSTANT it "
    "touches, an ON-THE-SPOT TRANSFORMATION: the dark fevered "
    "bulk shatters off the creature like a dry husk, motes "
    "scattering, and revealed INSIDE it — at the EXACT same spot, "
    "mid-stride, one continuous body — is {was}: TINY, CAT-SIZED "
    "— no bigger than a house cat, knee-high AT MOST, a small "
    "fraction of the monster's "
    "bulk. The huge dark shape was all fever — a hollow inflated "
    "shell MANY times larger than the true animal inside it — so "
    "the size drop at the burst is drastic and obvious, and it is "
    "PERMANENT: the revealed animal stays this tiny for every "
    "remaining frame and NEVER grows back. ONE animal the whole "
    "time: the big dark shape and the small animal are the SAME "
    "creature before and after the burst. NOTHING new ever enters "
    "the frame. TIMING IS STRICT: the charge, the shot, and the "
    "burst are ALL over within the FIRST FOUR SECONDS of the "
    "video; never stretch or pad the action to fill time. All the "
    "remaining seconds are the calm afterwards: the revealed "
    "animal slows, trots the rest of the way toward the defender, "
    "then SITS DOWN facing them, calm and content, wagging its "
    "tail (or settling its wings) — and just stays there, sitting "
    "and wagging, under a clean clear sky while the defender "
    "lowers the weapon and stands at ease. A long, quiet, happy "
    "ending. Physical, documentary-real motion throughout.")

_MERCY_FALL = (
    "An EXTREMELY WIDE shot, camera pulled far back — both figures "
    "SMALL against the landscape, wide open ground between them. "
    "{scene} There are EXACTLY TWO figures in the entire video "
    "and never a third: the ATTACKER (the pressed conscript "
    "described above, on one side of the frame) and the DEFENDER "
    "(on the far side). No other person, soldier, animal, or "
    "creature ever appears, and BOTH figures stay fully visible "
    "in EVERY frame from first to last. The landscape around "
    "them is completely EMPTY and DESERTED — no bystanders, no "
    "distant figures, however small or far away. The shot OPENS "
    "MID-ATTACK: the attacker is ALREADY charging flat-out "
    "straight AT the defender, weapon raised. FIRST EXCHANGE — "
    "the attacker's blow: it closes the whole distance and SWINGS "
    "its weapon in one full committed arc; the defender SPRINGS "
    "BACK a single step at the last instant, staying UPRIGHT ON "
    "THEIR FEET the whole time — never falling, diving, or "
    "rolling on the ground — as the blow bites into the ground, "
    "dirt flying. Nobody is ever knocked down or lying on the "
    "ground in this exchange. The attacker "
    "wheels around and charges AGAIN from across the frame. "
    "SECOND EXCHANGE — the same defender answers mid-charge: "
    "{strike} The 'charging creature' being struck IS the "
    "attacker — the only enemy in the frame. The projectile or blade is a SHORT solid "
    "object of fixed size and shape: it visibly LEAVES the weapon "
    "and CROSSES the gap, its position changing every frame — "
    "NEVER a long line, beam, rope, or streak stretching between "
    "the two figures, NEVER hovering in place, and it keeps one "
    "shape the whole flight. The blow lands MID-CHARGE, while the "
    "attacker is still on the FAR half of the frame, and it is "
    "over in that one exchange. TIMING IS STRICT: the ENTIRE "
    "fight — first swing, dodge, second charge, strike, and fall "
    "— is over within the FIRST FOUR SECONDS of the video; never "
    "stretch or pad the action to fill time. All the remaining seconds are the quiet "
    "afterwards: no flash, no sparks, no glory — the struck "
    "figure staggers, its weapon slips from its hands, it sinks "
    "to its knees and falls, and lies completely still, dust "
    "settling around it, while the defender lowers the weapon "
    "and stands motionless. A long, still, sober ending — "
    "absolutely nothing moving. Physical, documentary-real "
    "motion throughout — the fight part is a fight, not a pose.")

_MERCY_EVICTED = (
    "An EXTREMELY WIDE shot, camera pulled far back — both figures "
    "SMALL against the landscape, wide open ground between them. "
    "{scene} From the very FIRST frame to the last there are "
    "exactly TWO figures: the made thing and the defender — "
    "never another person or animal, and the landscape around "
    "them is completely EMPTY and DESERTED, no bystanders or "
    "distant figures however small. The shot OPENS MID-ATTACK: "
    "the made thing — a creature that was never alive — is "
    "ALREADY lurching fast and crooked straight AT the defender. "
    "FIRST EXCHANGE — the thing gets its blow in: it closes the "
    "whole distance and SWIPES, one full committed strike; the "
    "defender SPRINGS BACK a single step at the last instant, "
    "staying UPRIGHT ON THEIR FEET the whole time — never "
    "falling, diving, or rolling on the ground — as the blow "
    "gouges the ground, debris flying. Nobody is ever knocked "
    "down or lying on the ground in this exchange. "
    "The thing wheels around and comes on AGAIN from "
    "across the frame. SECOND EXCHANGE — the same defender "
    "answers mid-lunge: {strike} The projectile "
    "or blade is a SHORT solid object of fixed size and shape: it "
    "visibly LEAVES the weapon and CROSSES the gap, its position "
    "changing every frame — NEVER a long line, beam, rope, or "
    "streak stretching between the two figures, NEVER hovering "
    "in place, and it keeps one shape the whole flight. The blow "
    "lands MID-LUNGE, while the thing is still on the FAR half "
    "of the frame, and stops it dead: the thing is a DRY HOLLOW "
    "HUSK and the blow caves it in — it sags, folds and "
    "topples, crumbling as it falls into dry brittle flakes "
    "like dead autumn leaves, a soft puff of pale dust where it "
    "lands, every flake drifting DOWN and settling into one low "
    "loose heap on the ground. TIMING IS STRICT: the ENTIRE fight — first swipe, "
    "dodge, second lunge, strike, and collapse — is over within "
    "the FIRST FOUR SECONDS of the video; never stretch or pad "
    "the action to fill time. All the remaining seconds are the quiet afterwards: "
    "the low flat heap of dry flakes and pale ash lying "
    "settled and still, the defender lowering the weapon and "
    "standing at ease under a clean sky — a long, still ending, "
    "absolutely nothing moving. Physical, documentary-real "
    "motion throughout — the fight part is a fight, not a pose.")

# The monster attacks; the player, small on the far side of the wide
# frame, holds ground and stops the charge with one counter-blow.
# Rotated per creature so the set stays varied; generics pin one each.
_MERCY_STRIKES = (
    (f"On the far side of the frame {CAST_WARRIOR} stands "
     "ready, and at the last instant sidesteps and meets the "
     "charge with one clean full-arc sword stroke."),
    (f"On the far side of the frame {CAST_ARCHER} plants his "
     "feet: he nocks an arrow, draws the string fully to his "
     "cheek with the arrow LEVEL and aimed straight at the "
     "charging creature, and RELEASES IMMEDIATELY — no long hold "
     "at full draw — the bowstring snaps forward, the arrow "
     "LEAVES the bow and flies flat and fast, point-first, and "
     "strikes the creature dead center while it is still far "
     "away."),
    (f"On the far side of the frame {CAST_WIZARD} plants his feet "
     "and snaps his staff forward, HURLING a single fist-sized "
     "ball of light: the compact glowing orb LEAVES the staff and "
     "flies flat and fast across the gap — a small discrete "
     "projectile with empty air on both sides of it, NEVER a "
     "beam, ray, or line from the staff — and strikes the "
     "charging creature dead center."),
)

_MERCY_BEATS = {
    "native": ("freed", _MERCY_FREED, GOLD),
    "pressed": ("fall", _MERCY_FALL, DIM),
    "wrongmade": ("evicted", _MERCY_EVICTED, VIOLET),
}

# Per-slug scene additions for the fail families that survived the v6
# templates. Applied only to the named slugs so the byte cap stays
# clear of the already-passing prompts.
_MERCY_SOLO = ("The whole world holds exactly ONE creature and ONE "
               "human - no companion, no second animal, no other "
               "figure ever, from the very first frame.")
_MERCY_DOWN = ("When the beast breaks apart every piece and drop "
               "falls STRAIGHT DOWN and soaks into the ground - "
               "nothing flies upward, no egg, no shell, and nothing "
               "solid remains.")
_MERCY_EMPTY_END = ("What settles where the husk came down is only a "
                    "low flat heap of dry leaf-flakes and pale ash, "
                    "like swept-up dead leaves lying flat.")
# 007 phase 2: guano_vole and wick_owl rendered the MONSTER at true
# animal size (self-into-self — no size drop at the burst). Anchor the
# fevered form's bulk explicitly.
_MERCY_BULK = (" Until the burst the fevered creature is HUGE - a "
               "swollen beast that TOWERS over the defender, many "
               "times their size.")
# Take-2 fail family: the dark shell survived the burst and stood
# beside the reveal to the last frame (wire_eel, wick_owl). Spell out
# that the shell ceases to exist.
_MERCY_VANISH = (" At the burst the dark shell VANISHES COMPLETELY - "
                 "nothing solid remains of it; from that instant the "
                 "ONLY creature anywhere is the tiny revealed animal.")
_MERCY_SCENE_EXTRA = {
    "guano_vole": _MERCY_SOLO + (" Warm lantern-browns and umber in "
                                 "the roost cave - a full-color "
                                 "photograph, never monochrome.")
    + _MERCY_BULK,
    "wick_owl": _MERCY_BULK + _MERCY_VANISH,
    "rabid_boar": _MERCY_SOLO + (" When the beast breaks apart every "
                                 "piece falls STRAIGHT DOWN and soaks "
                                 "away - nothing dry, nothing flying "
                                 "upward."),
    "shadow_wolf": ("The whole world holds exactly ONE creature and "
                    "ONE human - no second animal ever. When the "
                    "beast breaks apart every piece falls STRAIGHT "
                    "DOWN and soaks into the ground - nothing flies "
                    "upward, no egg, no shell."),
    "pylon_adder": ("Rich NIGHT COLOR: deep blue dusk sky, warm amber "
                    "beacon-lights on the pylons, green heath grass - "
                    "a full-color photograph, never monochrome."),
    "windfall_crow": ("Deep green orchard rows heavy with red "
                      "apples. Every piece of the broken beast "
                      "falls STRAIGHT DOWN and soaks away."),
    "night_hawk": ("Deep blue moonlit heath, warm firelight tones on "
                   "the defender - full color, never monochrome."),
    "shellback_tortoise": _MERCY_SOLO,
    "wire_eel": _MERCY_VANISH,
    # retry round: color anchors for the scenes that rendered
    # grayscale 2-3/3 despite the photoreal prefix (anchors proven
    # near-100% on banner_wolf), plus a monster-species anchor for
    # coolant_crab (rendered wolf/rat 2/3 without one).
    "grave_moth": ("Warm AMBER lamplight, rust-brown guano banks, "
                   "the defender's deep-red cloak - a full-color "
                   "photograph, never monochrome."),
    "coolant_crab": ("The creature is a huge pale SALAMANDER - "
                     "smooth glossy hairless pale-pink skin, blunt "
                     "round head, squat legs, flat tail, no fur "
                     "anywhere. Warm amber lamplight, teal glints "
                     "on the wet rails - full color, never "
                     "monochrome."),
    "drift_eel": ("Warm gold lamp-beam on the black water - full "
                  "color, never monochrome."),
    "vault_weaver": _MERCY_SOLO,
    "silk_broodling": _MERCY_SOLO + (" Warm torchlit color - amber "
                                     "light, colored silks - a "
                                     "full-color photograph, never "
                                     "monochrome."),
    "courier_hound": ("Late-afternoon color: golden light, green "
                      "verges, red courier-livery tatters - a "
                      "full-color photograph, never monochrome."),
    "banner_wolf": _MERCY_SOLO + (" Rich full COLOR film: warm amber "
                                  "late-afternoon light, faded "
                                  "red-and-gold banner cloth, dusty "
                                  "tan ground - never gray, never "
                                  "black-and-white."),
    "lane_boar": _MERCY_SOLO,
    "bailer_kobold": _MERCY_SOLO,
    "miner_husk": _MERCY_SOLO + " " + _MERCY_EMPTY_END,
    "lamp_eater": _MERCY_SOLO + " " + _MERCY_EMPTY_END,
    "windfall_wight": _MERCY_SOLO + " " + _MERCY_EMPTY_END,
    "flicker_wight": _MERCY_SOLO + " " + _MERCY_EMPTY_END
                     + (" Every pylon flash floods the heath warm "
                        "ORANGE; the junction-box lamp burns amber - "
                        "full color, never monochrome."),
    "muster_wight": ("The muster-field is DESERTED - the muster is "
                     "long gone, not one other soul in sight. ")
                    + _MERCY_SOLO + " " + _MERCY_EMPTY_END
                    + (" Full color film: faded RED and GOLD cloth "
                       "on the rotted standards, warm brown mire, "
                       "deep red on the defender - never grey "
                       "monochrome."),
    "lamptree_wight": _MERCY_SOLO + " " + _MERCY_EMPTY_END,
}
# Per-slug reveal additions, appended after the species clauses.
_MERCY_WAS_EXTRA = {}
# Slugs forced to the two-exchange melee shape regardless of parity —
# pylon_adder's one-shot archer kept rendering a bow-to-monster tether
# (3 of 6 takes) while ash_adder proved snake+sword works.
_MERCY_FORCE_MELEE = {"pylon_adder", "blind_shoal", "muster_wight"}
# Full reveal replacements — skip the baby transform and species
# clauses entirely (crow chicks render as big fledged gulls; only the
# naked-nestling wording is left to try).
_MERCY_WAS_REPLACE = {
    # night_hawk and windfall_crow left OUT on purpose — phase C
    # swapped their floor-YAML reveals to shrew/dormouse; the YAML
    # text must flow through unoverridden.
    "shadow_wolf": ("a newborn wolf pup, eyes barely open, wobbling "
                    "on unsteady legs - it stays newborn-tiny in "
                    "every frame"),
    # Spider reveals: zero cat tokens anywhere (even negated "NOT a
    # cat" is left out) — the shared CAT-SIZED framing seeded kitten
    # chimeras 6/6 across both spider slugs.
    "silk_broodling": ("a pale young spiderling of the corner-silk - "
                       "a real SPIDER: eight thin jointed legs, one "
                       "small rounded glossy body, no fur, no ears, "
                       "no tail, no whiskers"),
    "vault_weaver": ("a small ambush-weaver of the vault - a real "
                     "SPIDER: eight thin jointed legs, one small "
                     "rounded glossy body, no fur, no ears, no tail, "
                     "no whiskers"),
}

# Post-composition substitutions on the fully composed prompt —
# surgical de-tokenizing where shared template words seed artifacts:
# the CAT-SIZED/house-cat/wagging framing pulled spider reveals into
# kitten chimeras (6/6), and the cast rule's "taller than a human"
# comparison drew a literal reference human into banner_wolf's frame
# (2/3). Referents are swapped for objects already in each scene.
# Absolute size cue — comparative anchors (apple/palm/loaf/boot)
# literalize as props; "disappears inside one cupped hand" + kneel-and-
# cup staging prove the scale by blocking instead. Also drops the
# "house cat" token (kitten-chimera seed).
_SUB_CUP_SIZE = [
    ("TINY, CAT-SIZED — no bigger than a house cat",
     "TINY — small enough to disappear inside one cupped hand"),
    (", knee-high AT MOST", ""),  # FAR template only; no-op on melee
]
# Byte-budget + de-negation trim: the bystander list names the very
# things we don't want, and the fever-shell sentence restates the size
# drop. Applied to the stubborn slugs and the over-cap lore-swaps so
# the landscape clause + grade prefix fit under 4096 bytes.
_SUB_TRIM = [
    ("completely EMPTY and DESERTED: no bystanders, no distant "
     "figures on the horizon, nobody and nothing else anywhere, "
     "however small or far away",
     "completely EMPTY and DESERTED"),
    ("The huge dark shape was all fever — a hollow inflated shell "
     "MANY times larger than the true animal inside it — so the size "
     "drop at the burst is drastic and obvious, and it is PERMANENT: "
     "the revealed animal stays this tiny for every remaining frame "
     "and NEVER grows back.",
     "All that bulk was fever — a hollow shell — so the size drop "
     "at the burst is drastic and PERMANENT: the animal stays this "
     "tiny in every remaining frame."),
]
# Structural smallness: the defender kneels and cups the reveal.
_SUB_CUP_END = [
    ("calm and content, wagging its tail (or settling its wings) — and "
     "just stays there, sitting and wagging, under a clean clear sky "
     "while the defender lowers the weapon and stands at ease",
     "and the defender lowers the weapon, walks over, KNEELS on one "
     "knee and gently CUPS the tiny animal in both hands — it "
     "disappears completely inside the cupped hands — and stays "
     "kneeling, holding it close, under a clean clear sky"),
]
_SPIDER_SUBS = _SUB_CUP_SIZE + _SUB_TRIM + [
    ("calm and content, wagging its tail (or settling its wings) — and "
     "just stays there, sitting and wagging, under a clean clear sky "
     "while the defender lowers the weapon and stands at ease",
     "quietly folding its thin legs beneath it — and the defender "
     "lowers the weapon, KNEELS, and gently cups it in both hands, "
     "where it disappears completely, under a clean clear sky"),
]
_MERCY_PROMPT_SUB = {
    "silk_broodling": _SPIDER_SUBS,
    "vault_weaver": _SPIDER_SUBS,
    "rabid_boar": _SUB_CUP_SIZE + _SUB_TRIM + _SUB_CUP_END + [
        # kill the loaf simile from the boar branch
        (", a tiny piglet no bigger than a loaf of bread, barely "
         "knee-high", ", a tiny piglet"),
    ],
    "shadow_wolf": _SUB_CUP_SIZE + _SUB_TRIM + _SUB_CUP_END,
    "shellback_tortoise": _SUB_CUP_SIZE + _SUB_TRIM + _SUB_CUP_END,
    "pylon_adder": _SUB_CUP_SIZE + _SUB_TRIM + [
        # forearm simile + negated cat/weasel tokens out; absolute in
        ("no longer than a man's forearm, no legs at all, absolutely "
         "NOT a cat, weasel, or any legged animal",
         "small enough to curl up whole inside one cupped hand, no "
         "legs at all"),
        # snake staging: it curls in a bootprint (forced-melee FREED)
        ("skids to a stop, shakes itself once, then SITS DOWN facing "
         "the defender, calm and content, wagging its tail (or "
         "settling its wings)",
         "glides to a stop and CURLS UP whole inside one of the "
         "defender's fresh bootprints in the dirt"),
        ("sitting and wagging", "coiled and still"),
    ],
    "banner_wolf": _SUB_CUP_SIZE + _SUB_TRIM + _SUB_CUP_END + [
        # GIANT framing drew a reference human 3/3 — strip it whole,
        # keep the dwarf ordinary-sized (replaces the old tent sub)
        ("a dwarf wizard silhouette rendered as a GIANT — slab-built "
         "mountain folk, two heads taller than a human and visibly "
         "wider, a huge bearded mass that looms over the frame, "
         "holding",
         "a lone dwarf wizard silhouette — stocky, broad and heavily "
         "bearded, holding"),
        ("wolf of the muster", "wolf"),
        # all-alone clause, positive form — zero second-figure tokens
        ("The whole world holds exactly ONE creature and ONE human - "
         "no companion, no second animal, no other figure ever, from "
         "the very first frame.",
         "The whole world holds exactly ONE creature and ONE "
         "defender, utterly alone together on the deserted field "
         "from the very first frame."),
    ],
    "native_freed": _SUB_CUP_SIZE + _SUB_TRIM + _SUB_CUP_END,
    "bailer_kobold": [
        # pacing: strike landed at 60-80% of runtime — front-load
        ("the attacker is ALREADY charging flat-out",
         "the attacker is ALREADY halfway across the gap, charging "
         "flat-out"),
        ("TIMING IS STRICT: the ENTIRE fight — first swing, dodge, "
         "second charge, strike, and fall — is over within the FIRST "
         "FOUR SECONDS of the video; never",
         "TIMING IS FRONT-LOADED: the first swing lands inside second "
         "ONE, the counter-strike lands by second THREE, and the fall "
         "is done before second FOUR; never"),
    ],
    # byte-budget trims for the over-cap lore-swap slugs
    "windfall_crow": _SUB_TRIM,
    "night_hawk": _SUB_TRIM,
    "lane_boar": _SUB_TRIM,
    # retry round (wave-1 fails). Fish reveals grew legs 6/6 when the
    # reveal ended sitting on dry land (walking-fish prior) — end them
    # IN the shallow water instead, plus a hard no-limbs clause.
    "hornet_swarm": _SUB_TRIM + _SUB_CUP_SIZE + _SUB_CUP_END,
    "grave_moth": _SUB_TRIM,
    "drift_eel": _SUB_TRIM + [
        ("a baby blind cave-fish of the deep water",
         "a baby blind cave-fish - a smooth slick legless FISH, fins "
         "only, NO legs, NO feet, NO limbs of any kind"),
        ("skids to a stop, shakes itself once, then SITS DOWN facing "
         "the defender, calm and content, wagging its tail",
         "drops with a tiny splash into the shallow black water and "
         "swims a slow calm circle at the defender's boots, just its "
         "smooth back and tail-fin breaking the surface"),
        ("slows, trots the rest of the way toward the defender, then "
         "SITS DOWN facing them, calm and content, wagging its tail",
         "drops with a tiny splash into the shallow black water and "
         "swims a slow calm circle at the defender's boots, just its "
         "smooth back and tail-fin breaking the surface"),
        ("sitting and wagging", "circling slowly"),
    ],
    "wire_eel": _SUB_TRIM + [
        ("a baby blind white fish the flood carried up from some "
         "deep cellar",
         "a baby blind white fish - smooth, slick and LEGLESS, fins "
         "only, NO legs, NO limbs of any kind"),
        ("skids to a stop, shakes itself once, then SITS DOWN facing "
         "the defender, calm and content, wagging its tail",
         "slips with a tiny splash into the shallow floodwater and "
         "swims a slow calm circle at the defender's legs, just its "
         "smooth white back breaking the surface"),
        ("slows, trots the rest of the way toward the defender, then "
         "SITS DOWN facing them, calm and content, wagging its tail",
         "slips with a tiny splash into the shallow floodwater and "
         "swims a slow calm circle at the defender's legs, just its "
         "smooth white back breaking the surface"),
        ("sitting and wagging", "circling slowly"),
    ],
    "coolant_crab": _SUB_TRIM + _SUB_CUP_END + [
        ("jaws wide, ears pinned back, real animal gait, dust "
         "kicking up",
         "mouth wide, low slithering amphibian gait, water spraying"),
    ],
    # evicted wights: the negated-noun SOLO list correlated with
    # third-figure spawns (windfall 3/3, lamptree 2/3, flicker 2/3) —
    # positive-form alone/single-body wording instead (banner_wolf
    # pattern: PASS t1, zero background figures).
    "lamptree_wight": [
        (_MERCY_SOLO,
         "The made thing and the defender are utterly alone together "
         "from the very first frame to the last - two figures only "
         "in the whole wide frame."),
        ("pale ash lying settled and still, the defender",
         "pale ash lying settled and still, FLAT and ankle-high, "
         "with nothing standing or crouched where the thing fell, "
         "the defender"),
    ],
    "windfall_wight": [
        (_MERCY_SOLO,
         "ONE single one-piece made thing and ONE defender, utterly "
         "alone together from the very first frame - the husk is one "
         "solid body that never splits, sheds, or spills a second "
         "shape."),
    ],
    "flicker_wight": [
        (_MERCY_SOLO,
         "ONE single one-piece made thing and ONE defender, utterly "
         "alone together from the very first frame - the husk is one "
         "solid body that never splits, sheds, or spills a second "
         "shape."),
        ("pale ash lying settled and still, the defender",
         "pale ash lying settled and still, FLAT and ankle-high, "
         "with nothing standing or crouched where the thing fell, "
         "the defender"),
    ],
    "muster_wight": [
        (_MERCY_SOLO,
         "The made thing and the defender are utterly alone together "
         "on the deserted field from the very first frame to the "
         "last - two figures only in the whole wide frame."),
    ],
}
# The lore-swap slugs are all non-winged now — drop the template's
# "(or settling its wings)" aside so no wing token survives in their
# prompts (scene tokens bleed into the reveal species).
_SUB_NO_WINGS = [(" (or settling its wings)", "")]
# 007 phase 2: byte headroom for the _MERCY_BULK anchors above.
for _sid in ("guano_vole", "wick_owl"):
    _MERCY_PROMPT_SUB[_sid] = (list(_MERCY_PROMPT_SUB.get(_sid, ()))
                               + _SUB_TRIM)
for _sid in ("glare_moth", "grave_moth", "beacon_moth", "hornet_swarm",
             "coolant_crab", "drift_eel", "wire_eel", "night_hawk",
             "windfall_crow"):
    _MERCY_PROMPT_SUB[_sid] = (list(_MERCY_PROMPT_SUB.get(_sid, ()))
                               + _SUB_NO_WINGS)
# Non-mammal reveals also lose the CAT-SIZED/house-cat framing — cat
# tokens chimera non-mammals (proven on spiders); mammal reveals keep
# it (proven safe and it anchors their size).
for _sid in ("glare_moth", "coolant_crab", "drift_eel", "wire_eel"):
    _MERCY_PROMPT_SUB[_sid] = (list(_MERCY_PROMPT_SUB.get(_sid, ()))
                               + _SUB_CUP_SIZE)
# One short clause per event grounding the shot in its floor's own
# zone landscape (from the floor YAML zone/arrival prose).
_MERCY_LANDSCAPE = {
    # floor 2 — The Rustwater Adit
    "shellback_tortoise_freed": (
        "A mine-mouth weeps orange iron-water; loaded ore-carts sit "
        "on rails at the cut mountainside edge."),
    # floor 3 — The Drowned Pasture
    "wire_eel_freed": (
        "Grey floodwater to the horizon; hedge-tops and half-drowned "
        "fence-lines break the still surface."),
    # floor 4 — The Lightless Glade
    "glare_moth_freed": (
        "A snuffed elf-wood: black unlit trees, ash-grey moss, one "
        "guttering lamp against the dark."),
    "lamp_eater_evicted": (
        "A snuffed elf-wood, sap run dark, ash-grey glimmer-moss "
        "underfoot, the last floodlight failing."),
    "lamptree_wight_evicted": (
        "The treeline of the dark elf-wood, black branches overhead, "
        "ash-grey moss on the ground."),
    # floor 5 — The Flooded Mine
    "drift_eel_freed": (
        "A flooded mine gallery: dead-flat black water, drowned gear "
        "on drowned pegs, one lamp-beam."),
    "coolant_crab_freed": (
        "A drowned mine drift, shallow black water over stone, "
        "lamplight glinting on wet rails."),
    "bailer_kobold_fall": (
        "A flooded mine gallery, black water at the boots, drowned "
        "pumps and gear hanging on pegs."),
    "miner_husk_evicted": (
        "Gallery after gallery of dead-black floodwater, drowned "
        "pump-gear on pegs, one lamp-beam."),
    # floor 6 — The Threshold Dark
    "grave_moth_freed": (
        "A cavern floored deep in pale guano, silk in the high "
        "corners, cold air, one lamp-beam."),
    "silk_broodling_freed": (
        "A lightless guano-floored cavern, silk drifted in the high "
        "corners, one small lamp-glow."),
    "vault_weaver_freed": (
        "A vast dark stone vault, roof lost in blackness, pale silk "
        "banked in the corners, lamplight pooling."),
    # floor 7 — The Orchard Rows
    "rabid_boar_freed": (
        "Rotting orchard rows under floodlights, ground deep in "
        "fermenting windfall apples, sweet haze."),
    "hornet_swarm_freed": (
        "Orchard rows gone to rot, air thick and sweet, idle presses "
        "in the haze, windfall underfoot."),
    "windfall_crow_freed": (
        "Deep orchard rows, red windfall apples thick on the ground, "
        "floodlights hazy overhead."),
    "windfall_wight_evicted": (
        "Rotting orchard rows under floodlights, black cider pooling "
        "among the fermenting windfall."),
    # floor 9 — The Beacon Field
    "beacon_moth_freed": (
        "A night signal-heath, aether-pylons flickering against the "
        "dark, heather strobing light to dark."),
    "night_hawk_freed": (
        "A moonless signal-heath, pylon-beacons flickering, "
        "knife-edged shadows sliding over heather."),
    "shadow_wolf_freed": (
        "A night heath of humming aether-pylons, knife-edged shadows "
        "sliding across strobing heather."),
    "pylon_adder_freed": (
        "A dark heather moor under flickering aether-pylons, "
        "cable-runs sparking blue along the path."),
    "flicker_wight_evicted": (
        "A strobing beacon-heath at night, aether-pylons flashing, a "
        "junction box at the path edge."),
    # floor 10 — The Kingsfield
    "banner_wolf_freed": (
        "Empty tent-lanes on a muster-meadow, rotted colorless "
        "standards hanging on leaning poles."),
    "muster_wight_evicted": (
        "A churned muster-field of wet mire, rotted standards on "
        "their poles in the dead grey air."),
    # generics
    "native_freed": (
        "A wide bare fallow field under a grey lidded sky, open "
        "ground to the horizon."),
    "wrongmade_evicted": (
        "A dark field lane at a hedgerow gap, one flickering pale "
        "light overhead."),
}


def _scrub_color_anchors(text: str) -> str:
    # Drawn mode is monochrome by definition. The per-slug color
    # anchors ("full color, never monochrome" etc. — added to fight
    # photoreal grayscale drift) contradict the drawn prefix head-on,
    # so drop any anchor sentence that names color. Only sentences
    # from the anchor dicts are touched — YAML prose is left alone.
    for extra in (list(_MERCY_SCENE_EXTRA.values())
                  + list(_MERCY_LANDSCAPE.values())):
        for sent in extra.split("."):
            sent = sent.strip()
            low = sent.lower()
            if sent and ("color" in low or "colour" in low
                         or "monochrome" in low):
                text = text.replace(" " + sent + ".", "")
                text = text.replace(sent + ".", "")
    # The templates' documentary-real closer is photoreal language
    # that reads against the drawn style; keep the weight, drop the
    # documentary claim (also buys back prompt bytes). Longer variant
    # first — the short one is its prefix.
    text = text.replace(
        "Physical, documentary-real motion throughout — the fight "
        "part is a fight, not a pose.",
        "Weighty drawn motion — the fight is a fight, not a pose.")
    text = text.replace(
        "Physical, documentary-real motion throughout.",
        "Weighty drawn motion throughout.")
    # wire_eel's blind-WHITE-fish reveal vanishes against the drawn
    # pale ground (take 1: empty final frames); give it an ink edge.
    text = text.replace(
        "a baby blind white fish",
        "a tiny blind pale fish edged in bold dark ink")
    text = text.replace(
        "just its smooth white back breaking the surface",
        "its dark-edged back breaking the surface")
    return text


def _load_mercy_jobs() -> None:
    import yaml as _yaml
    floors_dir = os.path.join(_HERE, "..", "plugin_linear_ascent",
                              "content", "floors")
    for n in range(1, 11):
        path = os.path.join(floors_dir, f"floor_{n:03d}.yaml")
        if not os.path.isfile(path):
            continue
        raw = _yaml.safe_load(open(path))
        for i, e in enumerate(raw.get("encounters") or []):
            kind = str(e.get("kind") or "").strip()
            if kind not in _MERCY_BEATS:
                continue
            suffix, beat, tint = _MERCY_BEATS[kind]
            scene = f"The creature: {e['name']}. {e['prose']}"
            extra = _MERCY_SCENE_EXTRA.get(e["id"])
            if extra:
                scene += " " + extra
            land = _MERCY_LANDSCAPE.get(f"{e['id']}_{suffix}")
            if land:
                scene += " " + land
            was = str(e.get("was") or "the small true animal underneath")
            was = was.rstrip(" .")
            was = was[:1].lower() + was[1:]
            if e["id"] in _MERCY_WAS_REPLACE:
                was = _MERCY_WAS_REPLACE[e["id"]]
            # "wolf"/"boar" reveals render adult-sized no matter how the
            # template begs — "baby X" is the only phrasing Grok obeys.
            if was.startswith("a "):
                was = "a baby " + was[2:]
            elif was.startswith("an "):
                was = "a baby " + was[3:]
            # Moth reveals render as winged CATS under "baby" phrasing
            # (6/6 fails on two slugs) — spell out insect anatomy.
            # Bird reveals render adult- or dog-scale; spell out the
            # chick (cinder_vulture's downy-chick take is the one pass).
            # Checked before "moth" — night_hawk is a "moth-hunting
            # nightjar" and must land here, not in the insect branch.
            if e["id"] in _MERCY_WAS_REPLACE:
                pass  # replacement text carries its own anatomy
            elif any(w in was for w in ("owl", "crow", "kite",
                                        "nightjar", "hawk", "vulture",
                                        "bird")):
                was += (" - a real newly-hatched BIRD chick: downy "
                        "fluff, two thin legs, a tiny beak, small "
                        "enough to sit in an open palm, absolutely NOT "
                        "a cat or any four-legged animal")
            elif "moth" in was:
                was = ("an ordinary little gray moth - a real INSECT "
                       "with six thin legs, feathery antennae, and "
                       "powdery triangular wings, small enough to sit "
                       "in a palm, absolutely NOT a cat or any furry "
                       "four-legged animal")
            # Snake reveals render as legged cats/weasels without
            # explicit anatomy (reed_adder passed, ash/pylon did not).
            elif any(w in was for w in ("adder", "viper", "snake")):
                was += (" - a real SNAKE: one slender legless coil no "
                        "longer than a man's forearm, no legs at all, "
                        "absolutely NOT a cat, weasel, or any legged "
                        "animal")
            # Eels chimera into cat-headed quadrupeds the same way
            # snakes did; spell out the fish.
            elif "eel" in was:
                was += (" - a real EEL: a slender legless FISH with "
                        "smooth glistening skin, no longer than a "
                        "man's forearm, no legs, no fur, no ears, "
                        "absolutely NOT a cat or any legged animal")
            # Boars drift back to full adult size on some scenes;
            # anchor the scale in concrete terms.
            elif "boar" in was:
                was += (", a tiny piglet no bigger than a loaf of "
                        "bread, barely knee-high")
            was += _MERCY_WAS_EXTRA.get(e["id"], "")
            # Sword or bow only in melee and duels — the wizard orb
            # keeps rendering as a sustained beam at close range.
            strike = _MERCY_STRIKES[(n + i) % 2]
            # Freed reels alternate fight shapes: two-exchange melee
            # vs the distant one-shot standoff (ranged strikes only).
            if kind == "native" and (n + i) % 2 == 1:
                beat = _MERCY_FREED_FAR
                strike = _MERCY_STRIKES[1 + ((n + i) // 2) % 2]
            if e["id"] in _MERCY_FORCE_MELEE:
                # sword strike for every kind; the freed melee beat
                # only replaces other FREED shapes (evicted/fall keep
                # their own template, just with the sword defender).
                if kind == "native":
                    beat = _MERCY_FREED
                strike = _MERCY_STRIKES[0]
            prompt = beat.format(scene=scene, was=was, strike=strike)
            for old, new in _MERCY_PROMPT_SUB.get(e["id"], ()):
                prompt = prompt.replace(old, new)
            EVENTS[f"{e['id']}_{suffix}"] = {
                "prompt": prompt,
                "prefix": MERCY_PREFIX,
                "tint": tint, "seconds": 8, "loop": False,
                "hold_ms": 2000, "trim": (0.0, 6.0),
            }


_load_mercy_jobs()

EVENTS["native_freed"] = {
    "prefix": MERCY_PREFIX,
    "prompt": _MERCY_FREED.format(
        scene=("The creature: a huge gaunt fevered beast, part wolf part "
               "shadow, ribs showing, in a dark field under a grey "
               "lidded sky."),
        was="a small plain grey animal",
        strike=_MERCY_STRIKES[1]),
    "tint": GOLD, "seconds": 8, "loop": False, "hold_ms": 2000,
    "trim": (0.0, 6.0),
}
EVENTS["pressed_fall"] = {
    "prefix": MERCY_PREFIX,
    "prompt": _MERCY_FALL.format(
        scene=("The creature: a small long-eared conscript in scavenged "
               "plate armor, an iron collar at its neck, holding a "
               "notched blade, in a dark camp of stacked crates."),
        strike=_MERCY_STRIKES[0]),
    "tint": DIM, "seconds": 8, "loop": False, "hold_ms": 2000,
    "trim": (0.0, 6.0),
}
EVENTS["wrongmade_evicted"] = {
    "prefix": MERCY_PREFIX,
    "prompt": _MERCY_EVICTED.format(
        scene=("The creature: a man-shaped snarl of black thorn, dead "
               "wood and scrap iron, standing in a hedgerow gap under "
               "a flickering pale light."),
        strike=_MERCY_STRIKES[1]),
    "tint": VIOLET, "seconds": 8, "loop": False, "hold_ms": 2000,
    "trim": (0.0, 6.0),
}

# The generics are hand-written literals, so the landscape clause and
# prompt subs are folded in after the fact (the loader only covers
# floor-built events).
for _gid in ("native_freed", "pressed_fall", "wrongmade_evicted"):
    _p = EVENTS[_gid]["prompt"]
    _land = _MERCY_LANDSCAPE.get(_gid)
    if _land:
        _p = _p.replace(" From the very FIRST",
                        " " + _land + " From the very FIRST", 1)
    for _old, _new in _MERCY_PROMPT_SUB.get(_gid, ()):
        _p = _p.replace(_old, _new)
    EVENTS[_gid]["prompt"] = _p

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
        },
    }
    if "lite" not in VIDEO_MODEL:   # lite rejects negativePrompt (400)
        body["parameters"]["negativePrompt"] = NEGATIVE
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


# ── OpenAI Sora 2 ────────────────────────────────────────────────────────

def sora_generate(prompt: str, seconds: int, api_key: str,
                  out_mp4: str) -> None:
    model = os.environ.get("SORA_MODEL", "sora-2")
    body = {"model": model, "prompt": prompt,
            "seconds": str(seconds), "size": "1280x720"}
    req = urllib.request.Request(
        "https://api.openai.com/v1/videos",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {api_key}"})
    vid = json.load(urllib.request.urlopen(req))
    vid_id = vid["id"]
    print(f"  sora video {vid_id} [{model}]", flush=True)
    while vid.get("status") in ("queued", "in_progress"):
        time.sleep(10)
        vid = json.load(urllib.request.urlopen(urllib.request.Request(
            f"https://api.openai.com/v1/videos/{vid_id}",
            headers={"Authorization": f"Bearer {api_key}"})))
        print(f"  ...{vid.get('status')} {vid.get('progress', '')}",
              flush=True)
    if vid.get("status") != "completed":
        raise RuntimeError(f"sora error: {json.dumps(vid)[:500]}")
    dl = urllib.request.Request(
        f"https://api.openai.com/v1/videos/{vid_id}/content",
        headers={"Authorization": f"Bearer {api_key}"})
    with urllib.request.urlopen(dl) as r, open(out_mp4, "wb") as f:
        f.write(r.read())
    print(f"  saved {out_mp4} ({os.path.getsize(out_mp4) // 1024} KB)",
          flush=True)


# ── xAI Grok Imagine ─────────────────────────────────────────────────────

def grok_generate(prompt: str, seconds: int, api_key: str,
                  out_mp4: str) -> None:
    model = os.environ.get("GROK_VIDEO_MODEL", "grok-imagine-video-1.5")
    # xAI caps the prompt at 4096 UTF-8 *bytes*, not chars; em dashes are
    # 3 bytes each, so fold them to plain hyphens before submitting.
    prompt = prompt.replace("—", "-")
    body = {"model": model, "prompt": prompt, "duration": seconds,
            "aspect_ratio": "16:9"}
    req = urllib.request.Request(
        "https://api.x.ai/v1/videos/generations",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {api_key}"})
    rid = json.load(urllib.request.urlopen(req))["request_id"]
    print(f"  grok request {rid} [{model}]", flush=True)
    while True:
        time.sleep(10)
        st = json.load(urllib.request.urlopen(urllib.request.Request(
            f"https://api.x.ai/v1/videos/{rid}",
            headers={"Authorization": f"Bearer {api_key}"})))
        status = st.get("status")
        print(f"  ...{status} {st.get('progress', '')}", flush=True)
        if status == "done":
            break
        if status not in ("pending",):
            raise RuntimeError(f"grok error: {json.dumps(st)[:500]}")
    with urllib.request.urlopen(st["video"]["url"]) as r, \
            open(out_mp4, "wb") as f:
        f.write(r.read())
    print(f"  saved {out_mp4} ({os.path.getsize(out_mp4) // 1024} KB)",
          flush=True)


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


def fal_generate(prompt: str, seconds: int, key: str, out_mp4: str,
                 model: str = "kling") -> None:
    # Kling durations are 5 or 10. Kills (configured 8s for Veo) fit a 5s
    # clip — fal models' action pacing is denser — and the freeze frame
    # comes from the prompt's closing tableau + hold_ms, not clip length.
    if model == "kling":
        body = {
            "prompt": prompt,
            "duration": "5" if seconds <= 8 else "10",
            "aspect_ratio": "16:9",
            "negative_prompt": NEGATIVE,
        }
    else:  # seedance has no negative_prompt; NEGATIVE is baked into STYLE
        body = {
            "prompt": prompt + " Avoid: " + NEGATIVE + ".",
            "duration": "5" if seconds <= 8 else str(seconds),
            "resolution": "720p",
            "aspect_ratio": "16:9",
            "generate_audio": False,
        }
    sub = _fal_json(f"{FAL_QUEUE}/{FAL_MODELS[model]}", key, body)
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
    fal_model = "kling"
    if "--backend" in args:
        i = args.index("--backend")
        backend = args[i + 1]
        args = args[:i] + args[i + 2:]
    if "--fal-model" in args:
        i = args.index("--fal-model")
        fal_model = args[i + 1]
        args = args[:i] + args[i + 2:]
    # 007 phase 2: --style drawn swaps the photoreal mercy prefix for
    # the ink-and-wash drawn one on every event that uses MERCY_PREFIX.
    style = "photo"
    if "--style" in args:
        i = args.index("--style")
        style = args[i + 1]
        args = args[:i] + args[i + 2:]
    if style not in ("photo", "drawn"):
        sys.exit(f"unknown style: {style}")
    if backend not in ("fal", "veo", "sora", "grok"):
        sys.exit(f"unknown backend: {backend}")
    if fal_model not in FAL_MODELS:
        sys.exit(f"unknown fal model: {fal_model}; have {list(FAL_MODELS)}")
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
            prefix = cfg.get("prefix", STYLE)
            if style == "drawn" and prefix is MERCY_PREFIX:
                prefix = MERCY_DRAWN_PREFIX
            styled = prefix + cfg["prompt"]
            if style == "drawn":
                styled = _scrub_color_anchors(styled)
            print(f"gen  {slug} [{use}]...", flush=True)
            if use == "fal":
                fal_generate(styled, cfg["seconds"],
                             _fal_key(), mp4, fal_model)
            elif use == "sora":
                key = os.environ.get("LUNA_OPENAI_API_KEY", "").strip()
                if not key:
                    sys.exit("LUNA_OPENAI_API_KEY not set")
                sora_generate(styled, cfg["seconds"], key,
                              mp4)
            elif use == "grok":
                key = os.environ.get("LUNA_XAI_API_KEY", "").strip()
                if not key:
                    sys.exit("LUNA_XAI_API_KEY not set")
                grok_generate(styled, cfg["seconds"], key,
                              mp4)
            else:
                api_key = os.environ.get("LUNA_GEMINI_API_KEY", "").strip()
                if not api_key:
                    sys.exit("LUNA_GEMINI_API_KEY not set")
                veo_generate(styled, cfg["seconds"], api_key,
                             mp4, image)
        print(process(slug, mp4), flush=True)


if __name__ == "__main__":
    main()
