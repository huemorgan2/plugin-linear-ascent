# 052 — Choose your climber

Three characters, three cards, one pick at the gate. The player who walks
out of the intro movie chooses who they are by clicking a portrait card —
and that portrait IS their face everywhere in the game from then on.

## The cast

| race key | card label | the figure | portrait |
|---|---|---|---|
| `human` | WARRIOR | a human woman fighter — athletic, confident, fitted practical armor | `portrait_human_100x200.png` |
| `elf` | ELF | a male elf — slender, sharp features, pointed ears, travel leathers | `portrait_elf_100x200.png` |
| `giant` | GIANT | a bearded giant — two heads taller and twice as wide, braided beard, plate and mail | `portrait_giant_140x260.png` |

`giant` replaces `dwarf` (same Stubborn +5% armor perk; docs migrate on
load exactly like halfling → human did in 017). The giant's canvas is
140x260 — 1.3x the human frame, the wick_giant precedent — so the giant
reads two heads taller and wider everywhere without any special casing:
the size is baked into the PNG's aspect.

## Art (vision/1bit-images.md law)

`gen_portraits.py` in this plan dir: nano-banana-pro prompted with the
030 PORTRAIT_STYLE (dither-designed charcoal, no outlines, pure black
void, figure fills the frame) + the 049 demo-player character texts;
enforcement is the proven 030 pipeline — center-crop → LANCZOS to grid →
autocontrast(cutoff=1) → Bayer 8x8 → white ink on alpha. Raws saved
versioned, previews at 2x on panel blue.

## The wardrobe dies

`_portrait_slug` returned `race x armor tier` (12 tier PNGs). 052: the
chosen character is the face, full stop — `_portrait_slug` returns the
race, `_tile_portrait_url` ignores armor, the 12 tier portraits are
deleted (portrait_wick stays — Wick is an NPC, not a wardrobe). The
armor progression still lives in the pack grid and the DEF pips; the
three faces are the only profile photos in the game.

`_portrait_data_url` learns the two frame sizes (100x200, 140x260) by
trying both. In the PLAYERS HERE grid a giant's face gets `.pface.giant`
— 30% taller, bottom-aligned, towering out of the tile row.

## The selection screen

`_creation_race_scene` becomes three portrait cards (the card-wall look,
divided by 3): `scene.gallery` tiles with `portrait_*` slugs. The
renderer resolves `portrait_*` gallery slugs through the portraits dir
(masked span, tint AETHER → TEXT on hover), lays the three in a
`.gal.chars` grid — figures bottom-aligned on one ground line, giant
biggest, card label (WARRIOR / ELF / GIANT) and the race's one-line
nature under each picture. Option rows duplicated by gallery tiles are
suppressed in the web pane (the agent tool still sees them in the scene
JSON, so ascent_choose keeps working).

## Ripples

- `economy.RACES`: `dwarf` → `giant`, blurb updated; `dfs()` checks
  `giant`; `tips.py` race tip re-keyed.
- `state.py` doc migration: `race == "dwarf"` → `"giant"` (halfling
  precedent, one line + note).
- 21 typed kill gifs `*_dwarf_{blade,bow,staff}_320x112.gif` renamed to
  `*_giant_*` so combat.py's `race x weapon-line` art lookup keeps
  hitting after the rename.
- worldd `test_world_api.py` picks `giant` instead of `dwarf`.
- tests: test_017 canon-cast list, test_014 option ids.

## Out of scope

The homepage `.trio` (WARRIOR/ARCHER/SORCERER marketing art) — separate
surface, separate art copies; can adopt the three new faces later.

## Release

0.69.0 — bump version.py + luna-plugin.toml, vendor, commit submodule
then root. No deploy without roy's word.
