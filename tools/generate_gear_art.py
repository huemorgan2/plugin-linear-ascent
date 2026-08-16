#!/usr/bin/env python3
"""058 — the rest of the shop wears its own face.

Same pipeline as generate_weapon_art.py (which this imports for the
grid/ink/panel helpers): one nano-banana-pro render per design, two
shipped assets each (100x160 portrait + 30x48 icon, same 5:8 crop).

95 designs: 28 martial shields, 19 caster focuses, 28 armor pieces,
5 boots, 15 relics. keen/warded variants reuse base art + tint.

Ships into plugin_linear_ascent/content/art/gear/{large,icons}/.
Raws (never shipped) land in plans/058-gear-art/raws/.

Usage: LUNA_GEMINI_API_KEY=... python tools/generate_gear_art.py [slug ...]
       --force regenerates even when the shipped pair exists.
"""

from __future__ import annotations

import asyncio
import io
import os
import sys

from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import generate_banners as gb                  # noqa: E402
import generate_weapon_art as gw               # noqa: E402  helpers

_ROOT = os.path.join(_HERE, "..")
SHIP = os.path.join(_ROOT, "plugin_linear_ascent", "content", "art",
                    "gear")
LARGE_DIR = os.path.join(SHIP, "large")
ICON_DIR = os.path.join(SHIP, "icons")
RAW_DIR = os.path.join(_ROOT, "plans", "058-gear-art", "raws")
REVIEW = os.path.join(_ROOT, "plans", "058-gear-art", "review")

LW, LH = gw.LW, gw.LH
IW, IH = gw.IW, gw.IH

STYLE = (
    "1-bit pixel art of a SINGLE piece of adventurer's equipment in "
    "the classic Macintosh / Playdate poster style. STRICTLY two "
    "colors: pure black background, white ink — every midtone rendered "
    "as LARGE CHUNKY ordered Bayer dither pixels. The object is "
    "perfectly centered in a vertical frame, filling most of it, on a "
    "PURE BLACK empty background. FULLY 3D-SHADED in dither, NOT a "
    "flat silhouette: one strong light from the top-left models the "
    "volume — lit side in dense white dither to near-white highlights, "
    "shadow side falling to solid black, big bold tonal steps that "
    "survive heavy downscaling. Crisp readable outline. No text, no "
    "border, no watermark, no hands, no body, no mannequin, no scene. "
    "The object: ")

# Style ladder as 057: POOR 1.0–1.4 · PLAIN 1.5–1.9 · FORGED 2.0–3.5 ·
# FINE 4.0–5.5 · MASTER 6.0–7.5 · MYTHIC 8.0–10.0; 0.0 gate kit is
# WRETCHED. No glow before FORGED (focuses excepted — dull light only);
# halos only at MYTHIC.
GEAR: dict[str, str] = {
    # ── martial shields — 28, front-on, vertical ─────────────────────
    "gate_buckler": (
        "a WRETCHED gate-issue buckler — a small round shield of thin "
        "stamped tin, dented and scuffed, single crude boss, armory "
        "number scratched near the rim, NO ornament, NO glow, small "
        "and sad in the frame."),
    "scrapwood_buckler": (
        "a POOR scrapwood buckler — a small round shield of mismatched "
        "salvage planks pegged together, grain going every direction, "
        "a bent nail boss, splinters at the rim, NO metal band, NO "
        "ornament, NO glow, humble and rough."),
    "plank_shield": (
        "a POOR plank shield — a tall rectangular door of three rough "
        "boards batten-nailed together, knots and splits showing, rope "
        "grip through drilled holes, NO ornament, NO glow, crude "
        "carpentry standing upright."),
    "ratskin_round": (
        "a POOR ratskin round shield — a small wicker round covered in "
        "patchy stitched rat hides, fur worn bald in spots, crude bone "
        "toggles at the rim, NO metal, NO ornament, NO glow, scrappy "
        "and mean."),
    "boarhide_buckler": (
        "a POOR boarhide buckler — a small round shield faced in "
        "thick bristly boar hide over wood, hide tacked with iron "
        "studs at the rim, one gouge scar across the face, NO "
        "ornament, NO glow, tough and plain."),
    "gatewatch_round": (
        "a POOR surplus round shield — armory-issue wooden round with "
        "a plain iron boss and rim band, stenciled service ring worn "
        "half away, evenly built by someone who cared, NO ornament, "
        "NO glow, service-plain."),
    "banded_kite": (
        "a PLAIN banded kite shield — a clean kite shape of pale "
        "boards with two honest horizontal iron bands riveted across, "
        "smooth face, tidy rim, NO device, NO ornament, NO glow, "
        "sturdy and unremarkable."),
    "wolfhide_targe": (
        "a PLAIN wolfhide targe — a round targe faced in grey wolf "
        "pelt, fur combed flat, simple iron boss, leather rim "
        "stitching in a neat ring, NO ornament, NO glow, clean "
        "hunter's kit."),
    "goblin_plate_buckler": (
        "a PLAIN goblin-plate buckler — a buckler of overlapping "
        "hammered scrap plates riveted like fish scales, edges filed "
        "smooth, ugly but solid, crooked boss, NO ornament, NO glow."),
    "wardens_cast_off_guard": (
        "a PLAIN warden's cast-off guard — a once-fine heater shield "
        "with its device chiseled off, straps replaced with rope, one "
        "old dent hammered mostly flat, good steel under scuffs, NO "
        "glow."),
    "emberband_round": (
        "a PLAIN emberband round — a wooden round shield with a "
        "kiln-blued iron band circling the rim, heat-tempered "
        "fire-pattern in the metal, plain face, NO glow, honest "
        "smith-work."),
    "ironbound_targe": (
        "a FORGED ironbound targe — a proper round targe with a "
        "polished conical boss, radial iron strapping riveted over "
        "hardwood, first faint edge-light along the polished bands, "
        "fitted and serious."),
    "boarhide_aspis": (
        "a FORGED boarhide aspis — a large round aspis with a bronze "
        "rim, face of layered lacquered boarhide with a subtle boar "
        "silhouette embossed, faint sheen on the bronze, real "
        "soldier's kit."),
    "dwarven_wall": (
        "a FORGED dwarven wall shield — a tall rectangular tower "
        "shield of riveted iron plates with a stepped geometric "
        "dwarven border, thick as a door, faint light on the rivet "
        "lines, immovable."),
    "kilnplate_round": (
        "a FORGED kilnplate round — a round shield of kiln-tempered "
        "steel with concentric hammered rings, heat-temper banding "
        "visible, faint edge-light on the rings, craftsman's pride."),
    "elfmirror": (
        "a FINE elfmirror shield — an elegant leaf-shaped shield of "
        "mirror-polished silver steel, slim engraved vine border, the "
        "face catching a designed soft gleam, ornate and light, glow "
        "ramping along the polished edge."),
    "moonglass_targe": (
        "a FINE moonglass targe — a round targe with a face of "
        "smoked moon-glass set in engraved silver, pale crescent "
        "glow swimming under the glass, ornate rim runes, elegant."),
    "drakescale_barrier": (
        "a FINE drakescale barrier — a kite shield faced in "
        "overlapping drake scales, each scale edged in worked brass, "
        "designed glow seeping between the scales, ornate and "
        "predatory."),
    "wyvernbone_wall": (
        "a FINE wyvernbone wall — a tall shield built on a lattice "
        "of pale wyvern ribs over dark hide, bone polished to ivory "
        "gleam, rune-etched bone rim glowing faintly, imposing."),
    "frostguard": (
        "a MASTER frostguard shield — a heater shield of blued steel "
        "rimed with radiant frost, elaborate ice-crystal boss "
        "blazing cold light, frozen light licking off the rim, "
        "dramatic and elite."),
    "frostrim_tower": (
        "a MASTER frostrim tower shield — a huge tower shield sheathed "
        "in ancient blue ice over black iron, radiant frost runes "
        "down the centerline, cold energy pouring off the rim, "
        "monumental."),
    "stormwardens_aegis": (
        "a MASTER stormwarden's aegis — an ornate round aegis with a "
        "storm-eye boss crackling with radiant lightning, elaborate "
        "cloud-scroll relief, arcs of energy licking the rim, "
        "dramatic."),
    "tempest_aegis": (
        "a MASTER tempest aegis — a kite shield alive with sculpted "
        "storm-front relief, radiant lightning veining the whole "
        "face, rim humming with charge, elite and loud with power."),
    "gloomturner": (
        "a MYTHIC gloomturner shield — a great round shield of "
        "polished obsidian that BENDS light, a thin blazing halo "
        "ring floating just off the face, darkness pouring off the "
        "rim like smoke, huge in the frame."),
    "gloamguard": (
        "a MYTHIC gloamguard — a tall shield of layered dusk-steel, "
        "a full twilight gradient pouring down the face from blazing "
        "crown to black foot, floating rune halo, huge and silent."),
    "hellgate_bulwark": (
        "a MYTHIC hellgate bulwark — a massive tower shield forged "
        "like a barred hell-gate, furnace light blazing through the "
        "grate seams, chained corners, a ring of embers haloing it, "
        "huge in the frame."),
    "hellgrate_shield": (
        "a MYTHIC hellgrate shield — a round shield of black iron "
        "grate-work over a core of roaring white fire, light "
        "streaming out in rays through the lattice, ember halo, "
        "overwhelming."),
    "the_unbroken": (
        "a MYTHIC legendary shield THE UNBROKEN — a battered-shaped "
        "yet flawless great heater radiating a huge starburst halo, "
        "a thousand hairline scars glowing white like a record of "
        "every blow it ever turned, immense in the frame."),
    # ── caster focuses — 19, small object floating centered ──────────
    "glass_bead_focus": (
        "a POOR glass bead focus — a single cloudy glass bead on a "
        "knotted leather thong, tiny air bubbles trapped inside, "
        "dull surface, NO glow, small and humble in the frame, "
        "hanging vertical."),
    "chipped_lens": (
        "a POOR chipped lens — a palm-sized round reading lens in a "
        "bent tin ring on a cord, one big chip missing from the "
        "edge, scratched glass, the faintest dull glint only, small "
        "in the frame."),
    "ratbone_charm": (
        "a POOR ratbone charm — a little bundle of rat bones bound "
        "in twine into a crude sigil, a tiny skull at the center, "
        "yellowed and dry, NO glow, dangling on a cord, small and "
        "grim."),
    "boartooth_fetish": (
        "a POOR boartooth fetish — a curved boar tusk wound with "
        "copper wire and strung with two wooden beads, scratched "
        "spiral carving, NO glow, hanging vertical, humble hedge "
        "magic."),
    "gatewatch_signet": (
        "a POOR gatewatch signet — a plain brass service ring with a "
        "worn gate sigil stamped flat, issued not earned, dull metal "
        "with one honest glint, NO glow, small in the frame."),
    "sootglass_bead": (
        "a PLAIN sootglass bead — a smoky dark glass sphere the size "
        "of a plum on a braided cord, soot swirls frozen inside, "
        "a first weak inner ember of light deep in the glass, "
        "clean and simple."),
    "wolfeye_stone": (
        "a PLAIN wolfeye stone — a polished agate with a slit-pupil "
        "band like a wolf's eye, set in a simple iron claw mount on "
        "a cord, faint watchful gleam in the band, plain and eerie."),
    "goblin_idol_shard": (
        "a PLAIN goblin idol-shard — a broken-off stone fragment of "
        "a grinning goblin idol face, one eye socket intact and "
        "faintly lit from within, wrapped in wire as a pendant, "
        "crude power."),
    "wardens_cracked_prism": (
        "a PLAIN warden's cracked prism — a finger-length crystal "
        "prism with one long internal crack, old warden filigree cap "
        "tarnished, thin light pooling along the crack, dignity in "
        "ruin."),
    "emberglass_lens": (
        "a PLAIN emberglass lens — a round lens of orange-tinged "
        "kiln glass in a blued iron ring, a slow ember smolder deep "
        "in the glass, smith-made and honest."),
    "ironglass_prism": (
        "a FORGED ironglass prism — a faceted prism of steel-grey "
        "glass in a fitted iron cage mount, edges catching a designed "
        "faint edge-light, precise craftsman's optics."),
    "kilnfire_lens": (
        "a FORGED kilnfire lens — a thick convex lens holding a "
        "captive kiln-flame glow at its heart, brass ring mount with "
        "rivets, warm light gathering to a bright focal point."),
    "moonwater_orb": (
        "a FINE moonwater orb — a glass orb of luminous captured "
        "moonlit water, slow ripples glowing inside, ornate silver "
        "crescent cradle, designed glow ramping around the rim, "
        "elegant."),
    "oathlight_prism": (
        "a FINE oathlight prism — a tall cut prism of clear crystal "
        "with a steady white flame of sworn light burning inside, "
        "engraved gold band mounts, rays fanning through the facets, "
        "ornate."),
    "grimlight_core": (
        "a MASTER grimlight core — a dark crystalline core hovering "
        "in a broken iron cage, radiant pale-green grave-light "
        "blazing from its cracks, energy licking between the bars, "
        "dramatic and ominous."),
    "starwell_lens": (
        "a MASTER starwell lens — a deep lens like a well of night "
        "sky, radiant stars drifting inside, elaborate astrolabe "
        "ring mount, starlight spilling over the rim, dramatic."),
    "duskmirror_orb": (
        "a MYTHIC duskmirror orb — a large orb of liquid dusk "
        "mirror, a full sunset gradient blazing across it, a thin "
        "halo ring of light orbiting the sphere, huge in the frame."),
    "kingseye_prism": (
        "a MYTHIC kingseye prism — a crowned royal prism holding a "
        "blazing golden eye of light, rays streaming through the "
        "facets in a full starburst halo, regal and overwhelming."),
    "dawnprism": (
        "a MYTHIC dawnprism — the first light of day caught in a "
        "great flawless prism, a full sunrise pouring out of it in "
        "blazing rays, huge starburst halo filling the frame around "
        "it."),
    # ── armor — 28, torso piece front-on, no body ────────────────────
    "gate_jerkin": (
        "a WRETCHED gate-issue jerkin — a thin canvas work vest with "
        "a stenciled armory number, loose threads, two missing "
        "toggles, NO padding to speak of, NO ornament, NO glow, "
        "limp and sad, front view."),
    "padded_jerkin": (
        "a POOR padded jerkin — a quilted cloth vest with uneven "
        "hand-stitched squares, stuffing leaking at one seam, worn "
        "ties at the front, NO metal, NO ornament, NO glow, humble "
        "and lumpy, front view."),
    "ratskin_vest": (
        "a POOR ratskin vest — a vest of many small stitched rat "
        "pelts, patchy fur outside, crude bone toggles, NO ornament, "
        "NO glow, scrappy gutter armor, front view."),
    "quilted_rags": (
        "a POOR quilted rag armor — layers of salvaged cloth strips "
        "quilted thick with big crooked stitches, colors gone to "
        "grey, rope belt, NO ornament, NO glow, beggar's plate, "
        "front view."),
    "boarhide_jack": (
        "a POOR boarhide jack — a stiff jack of thick bristly boar "
        "hide, hair-on panels, heavy iron tack studs at the seams, "
        "one gouge scar, NO ornament, NO glow, tough and plain, "
        "front view."),
    "gatewatch_surplus": (
        "a POOR surplus gambeson — armory-issue padded gambeson with "
        "a stamped service band on the chest, all straps present and "
        "even, honestly made, NO ornament, NO glow, service-plain, "
        "front view."),
    "studded_jack": (
        "a PLAIN studded jack — a clean leather jack with tidy rows "
        "of dome studs, honest buckles, smooth worn-in leather, NO "
        "ornament, NO glow, dependable kit, front view."),
    "wolfpelt_coat": (
        "a PLAIN wolfpelt coat — a hip-length coat of grey wolf "
        "pelts, fur collar, leather yoke and toggles, combed and "
        "clean, NO ornament, NO glow, hunter's winter kit, front "
        "view."),
    "goblin_scrap_brigandine": (
        "a PLAIN goblin-scrap brigandine — a cloth brigandine with "
        "mismatched salvaged plates riveted inside, rivet heads in "
        "crooked rows outside, ugly but solid, NO glow, front view."),
    "wardens_cast_mail": (
        "a PLAIN warden's cast mail — a fine mail shirt with its "
        "warden insignia torn off the chest leaving a shadow, a few "
        "rings replaced in brighter steel, good work gone anonymous, "
        "NO glow, front view."),
    "emberforge_scale": (
        "a PLAIN emberforge scale — a scale shirt of kiln-blued "
        "steel scales with heat-temper coloring, plain leather "
        "backing, smith-honest rows, NO glow, front view."),
    "riveted_leather": (
        "a FORGED riveted leather cuirass — a fitted hardened "
        "leather cuirass with bright riveted iron reinforcement "
        "bands, faint edge-light on the rivet lines, proper "
        "soldier's armor, front view."),
    "boiled_cuirass": (
        "a FORGED boiled cuirass — a molded boiled-leather torso "
        "shell with sculpted chest ridge, hard gleam on the curves, "
        "fitted brass buckles, faint edge-light, front view."),
    "chain_hauberk": (
        "a FORGED chain hauberk — a knee-length riveted mail hauberk "
        "with even glinting rows, reinforced collar, faint light "
        "rippling down the links, real soldier's steel, front view."),
    "kilnforged_scale": (
        "a FORGED kilnforged scale — overlapping kiln-tempered steel "
        "scales with rainbow heat-banding, fitted brass edging, "
        "faint edge-light on every scale row, craftsman's pride, "
        "front view."),
    "silverthread_mail": (
        "a FINE silverthread mail — a mail shirt woven with bright "
        "silver links tracing an elegant pattern through the steel, "
        "designed soft glow tracing the silver thread, ornate "
        "collar, front view."),
    "moonthread_weave": (
        "a FINE moonthread weave — a supple woven armor of pale "
        "moonlit thread, glowing crescent clasp, light rippling "
        "along the weave like moon on water, elegant, front view."),
    "wyrmhide_coat": (
        "a FINE wyrmhide coat — a long coat of iridescent wyrm "
        "hide, scale sheen shifting, worked silver clasps, designed "
        "glow along the scale edges, ornate and sleek, front view."),
    "drakehide_plate": (
        "a FINE drakehide plate — a half-plate of drake hide "
        "panels set in engraved steel frames, glow seeping at the "
        "panel seams, ornate predatory lines, front view."),
    "dwarven_powerplate": (
        "a MASTER dwarven powerplate — a massive geometric dwarven "
        "full cuirass with stepped border relief, radiant rune "
        "channels glowing across the chest, dramatic mountain-forge "
        "presence, front view."),
    "frostbound_carapace": (
        "a MASTER frostbound carapace — a plate carapace sheathed "
        "in ancient blue ice, radiant frost crystals blooming at "
        "the joints, cold light pouring off the edges, dramatic, "
        "front view."),
    "stormforged_plate": (
        "a MASTER stormforged plate — a blued full cuirass with a "
        "radiant storm-eye boss on the chest, lightning veining "
        "across the plates, energy licking the edges, elite, front "
        "view."),
    "tempestweave": (
        "a MASTER tempestweave — a flowing armor woven of storm "
        "itself over steel, radiant lightning threads crackling "
        "through dark cloth, charged and dramatic, front view."),
    "nightweave_harness": (
        "a MYTHIC nightweave harness — an armor woven of night sky, "
        "stars drifting in the weave, a thin blazing halo outlining "
        "the shoulders, darkness pouring off it like smoke, huge in "
        "the frame, front view."),
    "gloamshroud_mail": (
        "a MYTHIC gloamshroud mail — mail of dusk-steel under a "
        "shroud of living twilight, a full gradient from blazing "
        "crown to black hem, floating rune halo, silent and huge, "
        "front view."),
    "demonbone_panoply": (
        "a MYTHIC demonbone panoply — a full panoply of polished "
        "demon bone over black steel, ribs and horns sculpted into "
        "the chest, furnace light blazing in every seam, ember halo, "
        "huge in the frame, front view."),
    "hellforged_panoply": (
        "a MYTHIC hellforged panoply — a full panoply forged in "
        "hellfire, black iron with white-hot light streaming "
        "through every joint, chained pauldrons, a ring of embers "
        "haloing it, overwhelming, front view."),
    "aegis_of_the_vale": (
        "a MYTHIC armor AEGIS OF THE VALE — a radiant full cuirass "
        "of dawn-silver, a great tree of light blazing across the "
        "chest, a huge starburst halo pouring off the shoulders, "
        "immense in the frame, front view."),
    # ── shoes — 5, a PAIR of boots, three-quarter view ───────────────
    "cobbled_boots": (
        "a POOR pair of cobbled boots — mismatched leather work "
        "boots, one patched toe, uneven hobnails, laces of knotted "
        "twine, NO ornament, NO glow, honest and tired, one boot "
        "slightly ahead of the other."),
    "wayfarers_treads": (
        "a FORGED pair of wayfarer's treads — well-made travel "
        "boots with double-stitched seams, fitted brass lace hooks, "
        "soles carved with a compass tread, faint edge-light on the "
        "leather shine, one boot ahead."),
    "chasewind_boots": (
        "a FORGED pair of chasewind boots — sleek runner's boots of "
        "supple leather with swept-back wind flanges at the heel, "
        "faint speed-line sheen, light and fast, one boot ahead."),
    "skyline_striders": (
        "a FINE pair of skyline striders — elegant high boots with "
        "engraved silver shin guards, designed glow tracing cloud "
        "scrollwork up the shaft, soles barely touching ground, one "
        "boot ahead."),
    "stormstep_greaves": (
        "a FINE pair of stormstep greaves — armored boots with "
        "sculpted storm-cloud greaves, radiant lightning veining "
        "down to the heel, sparks at the soles, one boot ahead."),
    # ── relics — 15, the object itself, identity over grandeur ───────
    "poison_arrows": (
        "a bundle of three poisoned arrows bound with cord, heads "
        "dripping dark venom in beaded drops, fletching stained, a "
        "faint sick sheen on the tips, standing vertical points up."),
    "slowing_arrows": (
        "a bundle of three arrows with heavy blunt lead heads wound "
        "in dripping grey tar-webbing, strands sagging between them, "
        "fletching bound with cord, standing vertical points up."),
    "piercing_arrows": (
        "a bundle of three armor-piercing arrows with long needle "
        "bodkin heads of polished steel, bright cold glints on the "
        "points, tight war fletching, standing vertical points up."),
    "fire_arrows": (
        "a bundle of three fire arrows with oil-wrapped heads ALIGHT, "
        "flame and ember flecks streaming upward, charred shafts "
        "below the wrapping, standing vertical points up."),
    "weapon_oil": (
        "a squat glass bottle of weapon oil with a cork stopper and "
        "a hanging rag, thick golden oil catching the light inside, "
        "a whetstone leaning against the base, still-life centered."),
    "entangling_net": (
        "a folded entangling net of knotted rope hung from a single "
        "iron ring, small barbed weights dangling at the mesh "
        "corners, heavy realistic knotwork, hanging vertical."),
    "sky_hook": (
        "a sky-hook — a three-pronged grappling hook of polished "
        "steel on a neatly coiled rope, prongs gleaming, the coil "
        "stacked beneath it, standing vertical hook up."),
    "strip_potion": (
        "a tall thin potion vial of violently fizzing liquid, bubbles "
        "streaming upward, wax-sealed stopper with a hanging tag, "
        "the glass etched with a broken-shield mark, centered."),
    "curse_scroll": (
        "a sealed curse scroll — rolled black parchment bound in "
        "red cord with a dripping wax seal, a thin line of baleful "
        "script glowing where the roll gapes, standing vertical."),
    "polymorph_dust": (
        "an open drawstring pouch of polymorph dust, a pinch of "
        "glittering motes drifting up from it, tiny rabbit-shaped "
        "puff forming in the motes, whimsical and strange, "
        "centered."),
    "veil_draught": (
        "a round-bellied draught bottle of pale mist that will not "
        "settle, slow spirals of veil-fog inside the glass, silver "
        "wire wound at the neck, ghostly soft gleam, centered."),
    "golden_apple": (
        "a flawless golden apple, metallic skin polished to blazing "
        "highlights, one perfect leaf of gold at the stem, sitting "
        "on its own faint pool of light, centered."),
    "reincarnation_spell": (
        "an open spellbook page folded into a standing card, a "
        "phoenix sigil of fine linework blazing at its center, "
        "sparks rising off the ink, standing vertical."),
    "stone_of_undying": (
        "a fist-sized rough stone split by a glowing seam of white "
        "light, the crack blazing like dawn through a door, hovering "
        "just off the ground, centered."),
    "severing_word": (
        "a single rune-tablet of black slate with ONE deep-cut rune, "
        "the cut edges blazing white, hairline cracks spreading from "
        "the rune, hovering vertical, ominous and simple."),
    # ── 062: the Medlab shelf — 5 apothecary wares, the object alone ──
    "medgel": (
        "a PLAIN medgel — a small squat glass jar with a screw lid, "
        "half full of thick translucent healing gel that catches the "
        "light, a plain paper label band, a smear on the rim, small "
        "and honest, no glow."),
    "trauma_kit": (
        "a PLAIN field trauma kit — a compact canvas roll-pouch, "
        "flap open, showing a rolled linen bandage, a small "
        "stoppered vial and a curved needle, a stitched cross on the "
        "flap, worn and practical, no glow."),
    "trollblood_tonic": (
        "a FORGED trollblood tonic — a tall narrow flask with a "
        "wax-sealed cork, thick dark liquid inside with a faint slow "
        "inner glow, a wired-on tag, condensation beads on the glass, "
        "potent and heavy."),
    "energy_cell": (
        "a FORGED aether energy cell — a palm-sized cylindrical "
        "canister of banded brass and glass, a bright energy core "
        "visible through the glass window with soft light leaking at "
        "the seams, contact caps at both ends, standing upright."),
    "luck_charm": (
        "a PLAIN luck charm — a small carved bone token on a leather "
        "cord, a four-leaf clover cut into its face, a knot of red "
        "thread, a single tiny bell, hanging vertical, humble and "
        "hopeful, no glow."),
}

# martial shields (0.0 gate + 27) and the rest, in ladder order for
# the review sheets — dict order above already runs poorest → mythic
GROUPS = {
    "shields": list(GEAR)[0:28],
    "focuses": list(GEAR)[28:47],
    "armor": list(GEAR)[47:75],
    "shoes_relics": list(GEAR)[75:95],
    "medlab": list(GEAR)[95:100],
}


def _paths(slug: str) -> tuple[str, str]:
    return (os.path.join(LARGE_DIR, f"{slug}_{LW}x{LH}.png"),
            os.path.join(ICON_DIR, f"{slug}_{IW}x{IH}.png"))


async def gen_one(slug: str, api_key: str) -> str:
    for attempt in range(3):
        res = await gb.providers.generate(
            gb.providers.MODELS["nano-banana-pro"], STYLE + GEAR[slug],
            aspect="9:16", api_key=api_key,
        )
        if "error" in res:
            return (f"FAIL {slug}: {res['error']} — "
                    f"{str(res.get('detail'))[:200]}")
        raw = Image.open(io.BytesIO(res["image_bytes"]))
        large = gw._enforce(raw, LW, LH)
        ink = gw._ink(large)
        if 0.02 <= ink <= 0.55:
            break
    else:
        return f"FAIL {slug}: ink {ink:.0%} after 3 tries"
    raw.save(os.path.join(RAW_DIR, f"{slug}_raw.png"))
    lp, ip = _paths(slug)
    large.save(lp)
    gw._enforce(raw, IW, IH).save(ip)
    note = " (retried)" if attempt else ""
    return f"ok   {slug}: ink {ink:.0%}{note}"


def contact_sheets() -> None:
    pad = 8
    for name, slugs in GROUPS.items():
        have = [s for s in slugs if all(os.path.exists(p)
                                        for p in _paths(s))]
        if not have:
            continue
        cell_w = LW * 2 + pad
        sheet = Image.new("RGB", (cell_w * len(have) + pad,
                                  LH * 2 + IH * 4 + pad * 4), gw.PANEL)
        x = pad
        for slug in have:
            lp, ip = _paths(slug)
            big = gw._on_panel(Image.open(lp), 2)
            ico = gw._on_panel(Image.open(ip), 4)
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
    force = "--force" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    slugs = args or list(GEAR)
    unknown = [s for s in slugs if s not in GEAR]
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
