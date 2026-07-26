#!/usr/bin/env python3
"""Faction sigil banners — 30 heraldic designs for plan 010's Community tab.

Same discipline as scene banners (tools/generate_banners.py, styleguide
design/pixel_art.md): Gemini paints it, then center-crop to 20:7,
downscale to 320x112, Bayer 8x8 -> true 1-bit, white ink on alpha.
The difference is the grammar: not a scene but a CREST — one bold
centered emblem a founder picks when naming their faction.

Usage: LUNA_GEMINI_API_KEY=... python tools/generate_faction_banners.py [slug ...]
Outputs: plugin_linear_ascent/content/art/banners/factions/<slug>_320x112.png
         .../factions/preview/faction_<slug>_preview.png
         .../factions/raw/<slug>_raw.png
"""

from __future__ import annotations

import asyncio
import io
import os
import sys

from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import generate_banners as gb  # noqa: E402  (shared 1-bit pipeline)

ART = os.path.join(_HERE, "..", "plugin_linear_ascent", "content", "art",
                   "banners", "factions")
RAW = os.path.join(ART, "raw")
PREVIEW = os.path.join(ART, "preview")

STYLE = (
    "1-bit pixel art heraldic guild crest banner in the classic "
    "Macintosh / Playdate / 1-bit Akira poster style. STRICTLY two "
    "colors: pure black and pure white — every midtone rendered as "
    "ordered Bayer dithering. Composition: ONE bold emblem CENTERED in "
    "a wide banner, large and instantly readable as a faction sigil, "
    "backed by a strong radial gradient glow halo that fades to black "
    "at the frame edges, with subtle symmetric flanking ornament that "
    "never competes with the emblem. HARD SCI-FI HERALDRY: the emblem "
    "is built from machined arcanotech — segmented armor plating, "
    "rivet lines, glowing power seams, exposed cables and conduits, "
    "circuit-board traces, antenna masts, thruster vents, holographic "
    "ring overlays — a medieval crest reforged by engineers. Flanking "
    "ornament is technological too: cable bundles, cooling fins, "
    "hazard chevrons, radiating antenna rays instead of laurels. "
    "Chunky visible pixels, rich dithered gradients in the halo and "
    "background. No text, no letters, no borders, no watermark. "
    "Emblem: "
)

# slug -> emblem prompt (all previews tinted DIM — role tinting is the UI's job)
SIGILS: dict[str, str] = {
    "wolf_howl": (
        "a cyborg wolf's head thrown back mid-howl, one side flesh and "
        "one side segmented armor plating with a glowing optic eye, "
        "cables running down the neck into a collar of conduits, a "
        "gradient moon disc ringed by a thin orbital station band "
        "behind the muzzle."),
    "comet_fall": (
        "a falling wrecked satellite burning up as a comet, solar "
        "panel wings shearing off, a long dithered plasma tail "
        "crossing the frame diagonally, trailing fragments and thin "
        "telemetry trace lines."),
    "gear_sword": (
        "a tall knight's longsword with a clearly drawn crossguard "
        "and grip, held perfectly vertical, its glowing plasma blade "
        "driven point-down through the center hole of a large "
        "machined cog lying flat behind it — the full sword dominant "
        "and unmistakable, arcs of light flaring where blade meets "
        "metal."),
    "twin_moons": (
        "two interlocking crescents — one a cratered moon, the other "
        "a curved orbital station of hull plates, windows and antenna "
        "masts — sharing a soft gradient halo with a tiny shuttle "
        "spark passing between them."),
    "raven_spread": (
        "a mechanical raven with wings fully spread, feathers as "
        "layered blade fins with rivet lines, a single glowing "
        "camera-lens eye, thin cables trailing from its talons."),
    "serpent_spire": (
        "a segmented machine serpent of armored vertebrae coiled "
        "three times around a lattice antenna spire, head raised at "
        "the beacon tip, its tongue an electric spark, aircraft "
        "warning lights glowing along the mast."),
    "storm_fist": (
        "a powered gauntlet of hydraulic pistons and armor plates "
        "gripping a lightning bolt, thick supply cables running off "
        "the wrist, the bolt fracturing into arc branches above, "
        "glow pooling in the servo palm."),
    "anvil_spark": (
        "a massive gravity anvil hovering on downward thruster vents, "
        "hazard chevrons on its flank, one star-shaped plasma spark "
        "rising off its horn in a bright gradient ray."),
    "crossed_spears": (
        "two plasma lances crossed behind a round energy-shield "
        "emitter, their tips glowing hot with gradient halos, sensor "
        "pennants and cable tassels hanging from each shaft."),
    "star_hourglass": (
        "a containment-field hourglass held in a riveted metal frame, "
        "falling sand rendered as a stream of glowing energy motes, "
        "the lower chamber burning bright like a reactor, gauge dials "
        "on the frame."),
    "circuit_eye": (
        "a wide-open eye inside a triangle of brushed metal plate, "
        "iris drawn as concentric holographic HUD rings, circuit "
        "traces running out of each corner to small node lights."),
    "root_reactor": (
        "a broad tree whose trunk is half armor-clad, roots becoming "
        "circuit-board traces that feed a buried glowing reactor "
        "core, cooling pipes rising among the branches, leaves as "
        "sparse pixel motes."),
    "broken_crown": (
        "a heavy crown of machined plate and antenna spikes cracked "
        "clean through the middle, the wide fissure leaking a bright "
        "vertical beam of reactor light, severed circuit traces "
        "sparking at the break."),
    "mecha_dragon": (
        "a colossal mechanical dragon head facing straight forward, "
        "long and angular like a warship prow — segmented armor "
        "plates, twin glowing optic eyes, jaw vents leaking plasma "
        "between exposed piston jaw-struts, cable bundles as "
        "whiskers, two swept-back antenna horns."),
    "phoenix_rise": (
        "a machine phoenix rising with wings of swept turbine blades, "
        "tail dissolving into thruster exhaust embers, a radial "
        "gradient sunburst of afterburner glow behind it."),
    "kraken_orb": (
        "four segmented cable-tentacles of an abyssal machine rising "
        "from below to cradle a glowing energy core orb, magnetic "
        "clamp suckers picked out in dither, small status lights "
        "along each arm."),
    "bolt_shield": (
        "a kite shield split per-pale — one half riveted hull plating "
        "with weld seams, the other a bright energy field with a "
        "black lightning bolt — a small shield generator node glowing "
        "at the top."),
    "warden_key": (
        "an ornate skeleton key held vertical, its bow a spinning "
        "reactor ring, its bit shaped like a tower silhouette with "
        "lit windows, data-light pulses running up the shaft."),
    "lantern_moth": (
        "a hooded containment lantern of riveted iron holding a caged "
        "plasma core with a wide gradient glow, one large moth with "
        "circuit-veined translucent wings silhouetted against the "
        "light."),
    "core_scarab": (
        "an armored machine scarab with folded wing-case hull plates "
        "and piston legs, carrying a small blazing reactor sun above "
        "its head between raised forelegs, vent slits glowing along "
        "its sides."),
    "ram_gate": (
        "a ram's skull reforged as an armored war-helm — hydraulic "
        "rams inside the great curled horns, a rivet line across the "
        "brow, one glowing optic socket — mounted over two crossed "
        "battering chains with heavy links."),
    "chained_sun": (
        "a caged fusion sun — a blazing core held inside a "
        "containment ring of struts — bound by two heavy chains "
        "pulling taut toward the lower corners, rays and plasma "
        "flares escaping between the links."),
    "dagger_rose": (
        "a slim monofilament dagger with a glowing edge piercing "
        "downward through an open rose whose stem is braided wire "
        "and whose thorns are soldered pins, one petal falling, a "
        "drop of light at the blade tip."),
    "meteor_maul": (
        "a two-handed war maul held upright, its head a captured "
        "cratered meteor clamped in a hydraulic cage still glowing "
        "in the cracks, stabilizer fins and cables along the haft."),
    "watch_owl": (
        "a squat sentinel owl of armor plates facing forward, eyes "
        "as two bright camera-lens glows with HUD rings, antenna "
        "ear-tufts, talons gripping a horizontal energy blade as a "
        "perch."),
    "web_star": (
        "a huge radial spiderweb of taut glowing fiber-optic strands "
        "filling the frame, drawn as a classic concentric web with "
        "clear spokes and rings, light pulses traveling the threads, "
        "a small eight-pointed data-star node caught burning at the "
        "very center."),
    "summit_flag": (
        "a jagged mountain peak with a tiny relay beacon mast planted "
        "at the summit, its signal lamp burning like a star directly "
        "above, thin transmission rings radiating from the light."),
    "tide_hook": (
        "a cresting wave curling around a heavy magnetic grapple "
        "hook with a glowing charge coil, spray breaking into pixel "
        "flecks, a taut winch cable running out of frame."),
    "sky_chart": (
        "a constellation of seven satellites joined by thin signal "
        "lines into a climbing figure, each node a small machine "
        "star, the topmost one largest with a bright halo and solar "
        "panel wings."),
    "iron_heart": (
        "an anatomical heart cast in riveted iron with piston valves "
        "and gauge dials, one glowing power seam down the middle, "
        "two short chains falling from its cable arteries."),
}

W, H = gb.W, gb.H


async def gen_one(slug: str, api_key: str) -> str:
    res = await gb.providers.generate(
        gb.providers.MODELS["nano-banana-pro"], STYLE + SIGILS[slug],
        aspect="21:9", api_key=api_key,
    )
    if "error" in res:
        return f"FAIL {slug}: {res['error']} — {str(res.get('detail'))[:200]}"
    raw = Image.open(io.BytesIO(res["image_bytes"]))
    raw.save(os.path.join(RAW, f"{slug}_raw.png"))
    bits = gb.to_1bit(raw)
    gb.bits_to_png(bits, (255, 255, 255)).save(
        os.path.join(ART, f"{slug}_{W}x{H}.png"))
    gb.bits_to_png(bits, gb._hx(gb.DIM), scale=2, bg=gb.PANEL).save(
        os.path.join(PREVIEW, f"faction_{slug}_preview.png"))
    ink = sum(map(sum, bits)) / (W * H)
    return f"ok   {slug}: ink {ink:.0%}"


async def main() -> None:
    api_key = os.environ.get("LUNA_GEMINI_API_KEY", "").strip()
    if not api_key:
        sys.exit("LUNA_GEMINI_API_KEY not set")
    for d in (ART, RAW, PREVIEW):
        os.makedirs(d, exist_ok=True)
    slugs = sys.argv[1:] or list(SIGILS)
    unknown = [s for s in slugs if s not in SIGILS]
    if unknown:
        sys.exit(f"unknown slugs: {unknown}; have {list(SIGILS)}")
    for i in range(0, len(slugs), 4):
        batch = slugs[i:i + 4]
        for line in await asyncio.gather(*(gen_one(s, api_key) for s in batch)):
            print(line, flush=True)


if __name__ == "__main__":
    asyncio.run(main())
