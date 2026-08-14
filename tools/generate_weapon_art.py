#!/usr/bin/env python3
"""057 P2 — every weapon wears its own face.

One nano-banana-pro render per weapon (the model DESIGNS the 1-bit
dither, per vision/1bit-images.md); post only enforces the grid. Each
render yields both shipped assets — the 100x160 hover portrait and the
30x48 card icon (same 5:8 crop, downscaled).

The 10 P1 review swords (plans/057-weapon-art/swords/) are copied, not
regenerated — roy approved those exact renders.

Ships into plugin_linear_ascent/content/art/weapons/{large,icons}/.
Raws (never shipped) land in plans/057-weapon-art/raws/.

Usage: LUNA_GEMINI_API_KEY=... python tools/generate_weapon_art.py [slug ...]
       --force regenerates even when the shipped pair exists.
"""

from __future__ import annotations

import asyncio
import io
import logging
import os
import shutil
import sys

from PIL import Image, ImageOps

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import generate_banners as gb  # noqa: E402  (BAYER + provider client)

# the provider's http client logs full request URLs (key included) at
# INFO — keep the key out of the terminal
logging.getLogger("httpx").setLevel(logging.WARNING)

_ROOT = os.path.join(_HERE, "..")
SHIP = os.path.join(_ROOT, "plugin_linear_ascent", "content", "art",
                    "weapons")
LARGE_DIR = os.path.join(SHIP, "large")
ICON_DIR = os.path.join(SHIP, "icons")
RAW_DIR = os.path.join(_ROOT, "plans", "057-weapon-art", "raws")
P1_DIR = os.path.join(_ROOT, "plans", "057-weapon-art", "swords")
REVIEW = os.path.join(_ROOT, "plans", "057-weapon-art", "review")

LW, LH = 100, 160   # large portrait
IW, IH = 30, 48     # icon — same 5:8 crop, upright
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

# The style ladder (PLAN.md): POOR 1.0–1.4 · PLAIN 1.5–1.9 ·
# FORGED 2.0–3.5 · FINE 4.0–5.5 · MASTER 6.0–7.5 · MYTHIC 8.0–10.0.
# Each identity below opens with its band word and carries the band's
# rules (no glow before FORGED; halos only at MYTHIC).
WEAPONS: dict[str, str] = {
    # ── the four gate basics (rung 0 — poorest of the poor) ──────────
    "rusted_shiv": (
        "a WRETCHED tiny rusted shiv — a sliver of pitted salvage steel "
        "with no real edge, tip ground on a doorstep, grip just rag and "
        "tape, rust flaking off in dither specks, NO guard, NO ornament, "
        "NO glow, small and pathetic in the frame with black all around."),
    "rusted_sword": (
        "a WRETCHED rusted short sword — gate-issue salvage steel, blade "
        "pitted and rust-bloomed, edge rolled in places, plain stub "
        "crossguard, grip wrapped in fraying cord, NO ornament, NO glow, "
        "honest weight but sad steel, modest in the frame."),
    "basic_bow": (
        "a WRETCHED gate-issue laminate bow — a plain flat practice bow "
        "of glued wood strips, armory stamp band near the grip, string "
        "slightly frayed, NO ornament, NO glow, strung and standing "
        "vertical, small and plain in the frame."),
    "worn_staff": (
        "a WRETCHED worn wooden walking staff — plain focus wood polished "
        "smooth by a thumb at the grip, a shallow spiral of old carving "
        "almost rubbed away, tip capped in dull iron, NO ornament, NO "
        "glow, humble and small in the frame."),
    # ── warrior — 27 swords ──────────────────────────────────────────
    "scrap_dagger": (
        "a POOR crude scrap-metal dagger — a short blade ground from a "
        "rusted sheet-metal offcut, edge chipped and uneven, tip "
        "slightly bent, grip just cord wrapped over bare tang, NO "
        "guard, NO ornament, NO glow, dull battered surface, small and "
        "pitiful in the frame with black space around it."),
    "notched_cleaver": (
        "a POOR butcher's cleaver turned weapon — a heavy rectangular "
        "chopping blade with one deep ugly notch in the edge, meat-hook "
        "hole in the corner, riveted wooden slab handles, grease-dull "
        "steel, NO guard, NO ornament, NO glow, workmanlike and grim."),
    "ratcatchers_dirk": (
        "a POOR ratcatcher's dirk — a long thin needle of a blade with a "
        "slight bend, tiny tarnished disc guard, twine-wrapped grip with "
        "a loop for the belt, scratched from alley work, NO ornament, "
        "NO glow, skinny and mean in the frame."),
    "boarspine_shortsword": (
        "a POOR rough shortsword — a stubby single-edged blade with a "
        "boar-tusk curve, hilt of carved bone rings, leather-strap "
        "grip, tiny plain iron stub guard, edge nicked from use, NO "
        "ornament, NO glow, dull worn steel, modest size in the frame."),
    "gatewatch_gladius": (
        "a POOR surplus gladius — a short straight double-edged blade "
        "with an armory stamp punched near the guard, plain iron cross "
        "stub, wooden grip worn to a shine, evenly sharpened by someone "
        "who cared, NO ornament, NO glow, service-plain."),
    "iron_sword": (
        "a PLAIN honest iron arming sword — straight double-edged "
        "blade with a single clean fuller, simple straight crossguard, "
        "plain round pommel, leather-wrapped grip, well-kept but "
        "completely unadorned, NO glow, NO engraving, the standard "
        "soldier's sword, modest in the frame."),
    "wolfsteel_broadsword": (
        "a PLAIN broad-bladed sword of wolf-quenched steel — wide "
        "double-edged blade with a broad shallow fuller, faint hammer "
        "texture on the flats, plain crossguard with slightly "
        "down-turned tips, fur-trimmed grip wrap, NO glow, NO ornament, "
        "sturdy and heavy-set."),
    "goblin_iron_falchion": (
        "a PLAIN brutal goblin-iron falchion — a heavy single-edged "
        "chopping blade with a clipped tip, crude rivets down the "
        "spine, mismatched dark iron plates, a jagged hand-guard of "
        "hammered scrap, tooth-marks notched into the spine, NO glow, "
        "menacing but cheap."),
    "wardens_cast_off": (
        "a PLAIN keep-forged arming sword rehilted for smaller hands — "
        "a well-made straight blade whose engraved crest has been FILED "
        "OFF leaving a rough blank patch, mismatched newer crossguard "
        "and grip, honest quality under the scars, NO glow."),
    "emberquench_blade": (
        "a PLAIN forge-quenched sword — straight blade with a dark "
        "tempered band running along the cutting edge, quench-scorched "
        "steel shading from bright flat to charcoal edge in bold dither "
        "steps, plain guard, heat-darkened but NOT glowing, no ornament."),
    "wolfbite": (
        "a FORGED wolf-fanged longsword — clean bright steel blade "
        "with a narrow etched fuller, the crossguard cast as a "
        "snarling wolf's open jaw gripping the blade between its "
        "fangs, pommel a wolf's-head, wire-wrapped grip, the FIRST "
        "faint edge-light: a thin subtle dither glow tracing the "
        "cutting edge only."),
    "bloodgroove_falchion": (
        "a FORGED falchion with a deep blood-groove — broad curved "
        "single-edged blade, one deep channel drinking down its length, "
        "fitted brass guard and ferrule, clean professional steel, a "
        "faint dither light along the groove only, no halo."),
    "emberfang": (
        "a FORGED ember-cut axe blade on a short haft — dark dwarf "
        "steel split by GLOWING EMBER SEAMS, cracks radiating designed "
        "dither heat, guard of two swept fang points, char-black "
        "leather grip with a glowing core peeking between wraps, faint "
        "heat shimmer off the edge, no full halo."),
    "seared_cleaver": (
        "a FORGED war cleaver, quench-burnt — a tall heavy chopping "
        "blade with a scorched edge still holding ember light as a "
        "designed dither ramp, riveted spine, brass-capped haft, "
        "smoke-dark steel, the glow confined to the searing edge."),
    "thornsong": (
        "a FINE living thorn-blade — an elegant leaf-shaped sword "
        "grown as much as forged, briar vines in relief coiling the "
        "whole blade and bursting into a thorned guard, small white "
        "blossoms at the ricasso, a soft designed glow breathing "
        "along the vine lines, graceful and ornate."),
    "moonwake_saber": (
        "a FINE elven moon-saber — a long slender curved blade polished "
        "to a second mirror finish, a designed glow ramp running the "
        "curve like moonlight on a wake, crescent-moon guard, "
        "silver-wire grip, engraved wave lines near the hilt, elegant "
        "and slightly larger in the frame."),
    "oathkeeper": (
        "a MASTER ceremonial greatsword — a long cathedral-forged "
        "blade engraved with lines of runic oath-script down the "
        "center that GLOW with a clean designed radiance, a wide "
        "winged crossguard like spread angel wings, a ring pommel "
        "holding a glowing gem, light pooling off the runes in "
        "gradient halos, large and commanding in the frame."),
    "bannerbreak_blade": (
        "a FINE war sword that outlived its knight — a broad engraved "
        "blade, crossguard cast as a torn war-banner frozen mid-wave, "
        "battle scars proudly polished, a designed glow tracing the "
        "banner folds and the fuller, gem at the pommel, imposing."),
    "grimcleaver": (
        "a MASTER giant-slaying thunder maul-blade — a colossal "
        "executioner's cleaver with a storm-rune burned into the flat "
        "that GLOWS, arcs of designed lightning dither licking off the "
        "edge, haft banded in iron, dramatic radiant energy, large and "
        "heavy in the frame."),
    "ironstorm_maul": (
        "a MASTER storm maul — a massive squared iron head crackling "
        "with designed lightning arcs bridging its corners, glowing "
        "storm runes on the faces, thick banded haft with a spiked "
        "counterweight, sparks as sparse white dither, dramatic."),
    "starfall": (
        "a MYTHIC star-metal blade — a long sword seemingly cut from "
        "the night sky, blade body of deep black speckled with "
        "star-point white dither, a comet-tail of designed glow "
        "streaming off the tip, guard of two crescent arcs, the whole "
        "weapon wrapped in a radiant gradient halo, huge in the "
        "frame, dramatic."),
    "tempest_edge": (
        "a MASTER twice-charged storm saber — a curved blade wrapped in "
        "TWO designed lightning arcs spiraling its length, storm-cell "
        "capacitor glowing in the pommel, energy licking off the tip, "
        "radiant rune-light down the fuller, dramatic and large."),
    "duskrender": (
        "a MYTHIC phase-etched glaive — a long-hafted blade whose steel "
        "DISSOLVES at the edges into drifting dark speckle dither, "
        "phase-scored lines glowing across the blade, a gradient dusk "
        "halo behind it, the weapon half here and half elsewhere, huge "
        "in the frame."),
    "night_iron_glaive": (
        "a MYTHIC night-iron glaive — a glaive blade of light-drinking "
        "black iron shown as NEGATIVE SPACE rimmed in thin brilliant "
        "edge-light, darkness bleeding off it in dither wisps, a faint "
        "dark halo, ornate phase-etched socket and haft, huge and "
        "ominous."),
    "kingsbane": (
        "a MYTHIC demon-steel railblade — a long angular blade built "
        "like a rail weapon, twin glowing rails of designed energy "
        "running its length with crackling arcs bridging them, jagged "
        "demon-toothed guard, a burning gem core, radiant halo, huge "
        "and terrible in the frame."),
    "kingsguard_razor": (
        "a MYTHIC palace-forged razor — an impossibly long slender "
        "blade of demon-steel polished to white light, blazing filigree "
        "scrollwork down the flat, a crown-shaped guard, designed "
        "radiance pouring off the edge in gradient rays, elegant and "
        "enormous in the frame."),
    "dawnbreaker": (
        "a MYTHIC dawn-forged greatsword — a colossal blade blazing "
        "like sunrise, a designed radial gradient sunburst halo "
        "erupting from behind the blade, edge lines of pure white "
        "light, rays streaming upward as dither ramps, ornate solar "
        "crown guard with a burning core gem, the most radiant and "
        "elaborate weapon imaginable, filling the frame."),
    # ── archer — 27 bows (strung, standing vertical) ─────────────────
    "ashwood_bow": (
        "a POOR plain ash selfbow — one straight-grained wooden stave, "
        "simple nocks, hemp string, grip a strip of tied cloth, NO "
        "ornament, NO glow, dependable and dull, strung and standing "
        "vertical, small in the frame."),
    "green_hazel_bow": (
        "a POOR green hazel bow cut this season — a slightly crooked "
        "sapling stave with PATCHES OF BARK still on, whittle marks, "
        "rough twine string, NO ornament, NO glow, fresh pale wood, "
        "strung vertical, modest and crude."),
    "ratgut_shortbow": (
        "a POOR stubby shortbow with a ragged gut string — lumpy "
        "uneven limbs, the string visibly knotted and spliced in two "
        "places, grip of dirty rag, NO ornament, NO glow, alley-made "
        "and ugly, small in the frame."),
    "boarhorn_shortbow": (
        "a POOR horn-tipped shortbow — a stout wooden shortbow with "
        "rough boar-horn nock caps, hide-strap grip, stubborn thick "
        "limbs, tool marks everywhere, NO ornament, NO glow, strung "
        "vertical, squat and tough."),
    "gatewatch_shortbow": (
        "a POOR surplus issue shortbow — a plain flat-limbed shortbow "
        "with an armory stamp band burned near the grip, standard "
        "string, everything regulation and nothing more, NO ornament, "
        "NO glow, strung vertical, honest."),
    "sinew_backed_bow": (
        "a PLAIN sinew-backed bow — a clean wooden bow whose back "
        "carries a neatly glued sinew layer shown as fine lengthwise "
        "dither texture, tidy string wraps at the nocks, leather grip, "
        "NO glow, NO ornament, well-made and modest, strung vertical."),
    "wolfsinew_bow": (
        "a PLAIN wolf-sinew recurve — a compact recurve strung with "
        "visibly thick twisted sinew cord, fur-trimmed grip wrap, limb "
        "tips capped in plain bone, NO glow, NO ornament, hard-drawing "
        "hunter's tackle, strung vertical."),
    "goblin_notch_bow": (
        "a PLAIN crooked goblin bow — mismatched limbs plated with "
        "scrap iron strips, a row of tally notches carved down one "
        "limb, string anchored through drilled holes, crude rivets, NO "
        "glow, menacing but cheap, strung vertical."),
    "wardens_castbow": (
        "a PLAIN keep-issue war bow — a well-made recurve whose "
        "engraved crest has been FILED OFF the riser leaving a blank "
        "scar, iron nock caps, quality wood under the wear, NO glow, "
        "NO ornament, strung vertical."),
    "emberflight_shortbow": (
        "a PLAIN low-forge shortbow — clean wooden limbs whose nocks "
        "are scorched CHAR-BLACK from the forge, the char shading in "
        "bold dither steps, waxed string, NO glow (burnt, not "
        "burning), plain grip, strung vertical."),
    "wolfsight_recurve": (
        "a FORGED hunting recurve with a wolf-eye sight — clean "
        "laminated limbs, a small wolf's-eye bead above the grip "
        "holding the FIRST faint designed glow, precise string, brass "
        "limb bolts, keen and professional, strung vertical."),
    "horncore_bow": (
        "a FORGED horn-core composite bow — deeply reflexed limbs of "
        "layered horn and wood shown as banded dither laminations, "
        "fitted brass nock caps, tension you can see, a faint light "
        "along the limb bellies, no halo, strung vertical."),
    "emberflight_longbow": (
        "a FORGED dwarf-lathed longbow — a tall clean longbow with "
        "GLOWING PLASMA NOCKS, both string ends seated in designed "
        "ember-glow sockets, dark lathed wood with brass rings, the "
        "glow confined to the two nocks, strung vertical, tall in the "
        "frame."),
    "cinderfletch": (
        "a FORGED cinder bow — dark scorched limbs with ember light "
        "breathing through surface cracks as designed dither ramps, "
        "sparse cinder specks rising off the string line, brass "
        "fittings, the glow low and banked, strung vertical."),
    "thornstring": (
        "a FINE elven briar bow — limbs grown as living briar coiling "
        "with thorn relief, small white blossoms at the tips, the "
        "MONO-FIBER STRING itself a thin line of designed glow, "
        "graceful curves, ornate and elegant, strung vertical."),
    "silverlimb": (
        "a FINE silver-threaded recurve — polished limbs inlaid with "
        "silver thread tracery holding a cold designed glow, an "
        "engraved riser, no creak and no flaw, refined and ornate, "
        "strung vertical, larger in the frame."),
    "oathstring": (
        "a FINE knight's arc-bow — a war recurve whose limbs carry "
        "engraved oath-runes GLOWING with clean designed radiance, a "
        "winged riser like a folded gauntlet, a gem at the arrow rest, "
        "light pooling off the runes, commanding, strung vertical."),
    "drakespine_recurve": (
        "a FINE wyrm-bone recurve — limbs ribbed with actual wyrm "
        "vertebrae, bone spurs at the tips, designed glow seeping "
        "between the ribs, dark hide grip, trophy-ornate and slightly "
        "menacing, strung vertical, large."),
    "grimflight": (
        "a MASTER giant-slaying great bow — a one-hand ballista of a "
        "bow, massive banded limbs with glowing storm-runes, designed "
        "lightning arcs licking the string, iron-shod tips, dramatic "
        "radiant energy, very large in the frame, strung vertical."),
    "frosthawk_bow": (
        "a MASTER hawk-winged frost bow — the riser carved as a "
        "diving hawk, limbs feathered in relief and rimed with "
        "designed frost-glow, cold mist falling off them as sparse "
        "dither, a quiet radiant halo at the grip, dramatic, strung "
        "vertical."),
    "starshot": (
        "a MASTER storm-cell compound bow — angular machined limbs, "
        "twin cams GLOWING as designed energy wheels, cables of light, "
        "a capacitor core shining in the riser, crackling arcs at the "
        "cam edges, dramatic and large, strung vertical."),
    "stormnock": (
        "a MASTER twice-charged storm bow — recurve limbs wrapped in "
        "TWO spiraling designed lightning arcs, both nocks burning "
        "with charge, storm-runes down the riser, energy licking the "
        "string line, dramatic, strung vertical."),
    "duskwhisper": (
        "a MYTHIC phase-etched bow — limbs DISSOLVING at their edges "
        "into drifting dark speckle dither, the silent string a pure "
        "line of white light, phase-scores glowing across the riser, a "
        "gradient dusk halo behind it, huge and half-elsewhere, strung "
        "vertical."),
    "gloamreach": (
        "a MYTHIC cloak-field bow — limbs trailing long gradient veils "
        "of gloam like a cloak in wind, rendered as designed dither "
        "gradients, a dark radiant halo, ornate shadowed riser with a "
        "pale gem, enormous reach, filling the frame, strung vertical."),
    "kingspiercer": (
        "a MYTHIC demon-steel railbow — an angular bow built like a "
        "rail launcher, twin glowing energy rails running limb to limb "
        "with crackling arcs bridging them, jagged demon-toothed tips, "
        "a burning core gem in the riser, radiant halo, huge and "
        "terrible, strung vertical."),
    "hellbarb_bow": (
        "a MYTHIC hell-barbed bow — black limbs bristling with hooked "
        "barbs for what won't die, infernal designed glow seeping "
        "between the spikes, chained grip, a smoldering gradient halo, "
        "wicked and enormous in the frame, strung vertical."),
    "dawnstring": (
        "a MYTHIC dawn-forged great bow — a colossal bow bent double "
        "with a designed radial sunburst halo erupting from behind the "
        "riser, the string a blazing line of pure light, rays "
        "streaming upward as dither ramps, ornate solar crown tips, "
        "the most radiant bow imaginable, filling the frame, strung "
        "vertical."),
    # ── sorcerer — 27 staves ─────────────────────────────────────────
    "tallowwood_staff": (
        "a POOR tallow-wood staff — a plain pale walking staff of "
        "candle-soft wood with waxy drip ridges down one side, a tiny "
        "unlit spark notch at the tip, cord grip wraps, NO ornament, "
        "NO glow, humble and small in the frame."),
    "kindling_rod": (
        "a POOR kindling rod — a short crooked rod that is visibly a "
        "bundle of thin twigs bound with cord at three points, bark "
        "and whittle marks, frayed ends, NO ornament, NO glow, barely "
        "a wand, small and pitiful."),
    "ratbone_wand": (
        "a POOR ratbone wand — a small wand of knobby little bones "
        "lashed end to end with dirty twine, a tiny skull no bigger "
        "than a thumbnail at the tip, NO ornament, NO glow, grim and "
        "cheap, small in the frame."),
    "boarhide_stave": (
        "a POOR boarhide stave — a stout wooden stave wrapped in "
        "scarred boar hide straps, bristle tufts at the seams, gouge "
        "marks that the hide took first, iron heel cap, NO ornament, "
        "NO glow, squat and tough."),
    "gatewatch_baton": (
        "a POOR issue baton — a plain turned-wood baton with a stamped "
        "brass regulation band, a loop of cord at the butt, evenly "
        "worn, issued not chosen, NO ornament, NO glow, small and "
        "unremarkable."),
    "coalglass_staff": (
        "a PLAIN coalglass staff — a clean dark staff topped with a "
        "rough lump of coalglass held in three iron prongs, the glass "
        "DULL and banked (heat inside but not glowing), faceted "
        "highlights in bold dither, plain wraps, NO glow, modest."),
    "wolfsong_staff": (
        "a PLAIN wolf-song staff — a straight staff whose head is "
        "carved as a wolf mid-howl, mouth open to the sky, carved fur "
        "shown in dither texture, leather grip wraps, NO glow, NO "
        "metalwork beyond a plain ferrule, modest size."),
    "goblin_fetish_staff": (
        "a PLAIN goblin fetish staff — a crooked staff hung with "
        "borrowed god-charms: teeth, feathers, a bent coin on cords, a "
        "crude idol face carved at the head, mismatched iron bands, NO "
        "glow, menacing but cheap."),
    "wardens_broken_rod": (
        "a PLAIN mended rod — a keep-forged casting rod visibly "
        "CRACKED at mid-length and mended with two shrunk iron rings "
        "and tight cord, the old engraving interrupted by the break, "
        "quality under the scar, NO glow."),
    "emberquench_staff": (
        "a PLAIN emberquench walking staff — a sturdy staff whose head "
        "is char-darkened from banked low-forge heat, the char shading "
        "in bold dither steps down to clean wood, iron heel, NO glow "
        "(burnt, not burning), plain and honest."),
    "stormtwig_staff": (
        "a FORGED stormtwig staff — a green-wood staff whose tip "
        "splits into a tiny bare lightning-fork of twigs holding the "
        "FIRST faint designed glow, a thin static shimmer as sparse "
        "dither around the fork only, wrapped grip, fresh and alive."),
    "embervein_staff": (
        "a FORGED embervein staff — dark bark-covered staff with "
        "GLOWING EMBER VEINS branching under the cracked bark, the "
        "designed glow strongest at the head and fading down, brass "
        "ferrule, heat shimmer as sparse dither, no halo."),
    "ashspire_staff": (
        "a FORGED ashspire staff — a dwarf-kilned staff shaped like a "
        "tapering chimney spire, vent slits down the head GLOWING "
        "faintly from the draw inside, soot shading in bold dither, "
        "banded iron joints, the glow confined to the vents."),
    "cinderheart_staff": (
        "a FORGED cinderheart staff — a gnarled staff with a burning "
        "KNOT at its heart, ember light breathing through the bark "
        "cracks around the knot as designed dither ramps, char "
        "spreading outward, iron heel cap, banked power, no halo."),
    "thornweave_staff": (
        "a FINE thornweave staff — an elegant elven staff woven of "
        "briar mono-fiber, vines spiraling into an open thorned crown "
        "at the head, small white blossoms, a soft designed glow "
        "breathing along the vine lines, graceful and ornate."),
    "silverbough_staff": (
        "a FINE silverbough staff — a living bough grafted with "
        "silver thread tracery, the graft lines holding a cold "
        "designed glow, delicate leaf shapes in silver at the head, "
        "polished elegant curves, refined ornament, larger in frame."),
    "oathflame_staff": (
        "a FINE knight's arc-focus staff — a war staff crowned with an "
        "open ring holding a steady designed flame, oath-runes down "
        "the shaft GLOWING with clean radiance, winged collar under "
        "the ring, light pooling off the runes, commanding."),
    "wyrmtongue_staff": (
        "a FINE wyrmtongue staff — the head carved as a dragon's open "
        "mouth breathing a HELD flame of designed glow, scale relief "
        "down the neck of the staff in dither, fang details, dark "
        "hide grip wraps, ornate and menacing, large."),
    "grimspark_staff": (
        "a MASTER giant-slaying thunder rod — a massive iron-shod "
        "staff whose twin prongs cradle a crackling designed arc of "
        "lightning, storm-runes GLOWING down the shaft, sparks as "
        "sparse white dither, dramatic radiant energy, very large."),
    "frostbrand_staff": (
        "a MASTER frostbrand staff — a stave carrying a cold-field "
        "emitter head of concentric rings rimed in designed "
        "frost-glow, icy mist falling off it in sparse dither, a "
        "quiet radiant halo around the head, frozen ornament down the "
        "shaft, dramatic."),
    "starcaller_staff": (
        "a MASTER starcaller staff — a tall staff whose crown is a "
        "storm-cell core orb GLOWING bright, ringed by small orbiting "
        "star points on thin arcs, designed radiance pooling below "
        "the crown, engraved constellations down the shaft, dramatic "
        "and large."),
    "stormcrown_staff": (
        "a MASTER stormcrown staff — the head a jagged crown wrapped "
        "in TWO spiraling designed lightning arcs, twice-charged, "
        "energy licking between the crown points, glowing storm-runes "
        "down the shaft, dramatic and large in the frame."),
    "duskbinder_staff": (
        "a MYTHIC duskbinder staff — phase-etched heartwood whose "
        "edges DISSOLVE into drifting dark speckle dither, binding "
        "rings of pure light floating unattached around the shaft, a "
        "gradient dusk halo behind the head, huge and half-elsewhere."),
    "nightwell_staff": (
        "a MYTHIC nightwell staff — the head holds a WELL OF DARKNESS, "
        "a black orb shown as negative space rimmed in brilliant "
        "edge-light, light visibly bending into it as curved dither "
        "streaks, a dark radiant halo, ornate shadowed claw mount, "
        "enormous and ominous."),
    "kingscourge_staff": (
        "a MYTHIC demon-steel staff — an angular staff built around a "
        "glowing demon-steel core, twin energy rails running its "
        "length with crackling arcs bridging them, jagged toothed "
        "crown, a burning gem heart, radiant halo, huge and terrible."),
    "hellrune_staff": (
        "a MYTHIC hellrune staff — a black staff carved with runes "
        "that SHOULD NOT HOLD, each blazing with designed infernal "
        "light, the glow bleeding upward in gradient flames, chained "
        "rings, a smoldering halo, wicked and enormous in the frame."),
    "dawncaller_staff": (
        "a MYTHIC dawn-caller staff — a colossal staff whose crown "
        "erupts in a designed radial sunburst halo, a burning core "
        "gem held in an ornate solar crown, rays streaming upward as "
        "dither ramps, lines of pure white light down the shaft, the "
        "most radiant staff imaginable, filling the frame."),
}

# the 10 P1 review swords roy approved — copied from the plan folder,
# never regenerated (their raws stay in plans/057-weapon-art/swords/)
P1_APPROVED = (
    "scrap_dagger", "boarspine_shortsword", "iron_sword",
    "goblin_iron_falchion", "wolfbite", "emberfang", "thornsong",
    "oathkeeper", "starfall", "dawnbreaker",
)


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


def _ink(img: Image.Image) -> float:
    w, h = img.size
    px = img.load()
    return sum(1 for y in range(h) for x in range(w)
               if px[x, y][3]) / (w * h)


def _on_panel(img: Image.Image, scale: int, tint=ART_TINT) -> Image.Image:
    w, h = img.size
    out = Image.new("RGB", (w, h), PANEL)
    po, pi = out.load(), img.load()
    for y in range(h):
        for x in range(w):
            if pi[x, y][3]:
                po[x, y] = tint
    return out.resize((w * scale, h * scale), Image.NEAREST)


def _paths(slug: str) -> tuple[str, str]:
    return (os.path.join(LARGE_DIR, f"{slug}_{LW}x{LH}.png"),
            os.path.join(ICON_DIR, f"{slug}_{IW}x{IH}.png"))


def copy_p1() -> None:
    for slug in P1_APPROVED:
        lp, ip = _paths(slug)
        src_l = os.path.join(P1_DIR, f"{slug}_{LW}x{LH}.png")
        src_i = os.path.join(P1_DIR, f"{slug}_{IW}x{IH}.png")
        if os.path.exists(src_l) and not os.path.exists(lp):
            shutil.copyfile(src_l, lp)
        if os.path.exists(src_i) and not os.path.exists(ip):
            shutil.copyfile(src_i, ip)


async def gen_one(slug: str, api_key: str) -> str:
    # inverted output (white bg) is a known intermittent model failure —
    # the ink fraction catches it; blanks too. Retry, keep the best.
    for attempt in range(3):
        res = await gb.providers.generate(
            gb.providers.MODELS["nano-banana-pro"], STYLE + WEAPONS[slug],
            aspect="9:16", api_key=api_key,
        )
        if "error" in res:
            return (f"FAIL {slug}: {res['error']} — "
                    f"{str(res.get('detail'))[:200]}")
        raw = Image.open(io.BytesIO(res["image_bytes"]))
        large = _enforce(raw, LW, LH)
        ink = _ink(large)
        if 0.02 <= ink <= 0.55:
            break
    else:
        return f"FAIL {slug}: ink {ink:.0%} after 3 tries"
    raw.save(os.path.join(RAW_DIR, f"{slug}_raw.png"))
    lp, ip = _paths(slug)
    large.save(lp)
    _enforce(raw, IW, IH).save(ip)
    note = " (retried)" if attempt else ""
    return f"ok   {slug}: ink {ink:.0%}{note}"


def contact_sheets() -> None:
    """one review sheet per rack line, poorest → mythic."""
    sys.path.insert(0, os.path.join(_ROOT))
    from plugin_linear_ascent import economy  # noqa: E402
    groups = {
        "basics": ["rusted_shiv", "rusted_sword", "basic_bow",
                   "worn_staff"],
        "warrior": [g.slug for g in economy.weapon_line("warrior")],
        "archer": [g.slug for g in economy.weapon_line("archer")],
        "sorcerer": [g.slug for g in economy.weapon_line("sorcerer")],
    }
    pad = 8
    for name, slugs in groups.items():
        have = [s for s in slugs if all(os.path.exists(p)
                                        for p in _paths(s))]
        if not have:
            continue
        cell_w = LW * 2 + pad
        sheet = Image.new("RGB", (cell_w * len(have) + pad,
                                  LH * 2 + IH * 4 + pad * 4), PANEL)
        x = pad
        for slug in have:
            lp, ip = _paths(slug)
            big = _on_panel(Image.open(lp), 2)
            ico = _on_panel(Image.open(ip), 4)
            sheet.paste(big, (x, pad))
            sheet.paste(ico, (x + (big.width - ico.width) // 2,
                              LH * 2 + pad * 2))
            x += cell_w
        sheet.save(os.path.join(REVIEW, f"{name}_sheet.png"))
        print(f"review/{name}_sheet.png — {len(have)}/{len(slugs)}",
              flush=True)


async def main() -> None:
    api_key = os.environ.get("LUNA_GEMINI_API_KEY", "").strip()
    if not api_key:
        sys.exit("LUNA_GEMINI_API_KEY not set")
    for d in (LARGE_DIR, ICON_DIR, RAW_DIR, REVIEW):
        os.makedirs(d, exist_ok=True)
    copy_p1()
    force = "--force" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    slugs = args or list(WEAPONS)
    unknown = [s for s in slugs if s not in WEAPONS]
    if unknown:
        sys.exit(f"unknown: {unknown}")
    todo = [s for s in slugs if force
            or not all(os.path.exists(p) for p in _paths(s))]
    print(f"{len(todo)} to render ({len(slugs) - len(todo)} already "
          "present)", flush=True)
    for i in range(0, len(todo), 4):
        batch = todo[i:i + 4]
        for line in await asyncio.gather(*(gen_one(s, api_key)
                                           for s in batch)):
            print(line, flush=True)
    contact_sheets()


if __name__ == "__main__":
    asyncio.run(main())
