# 058 — the rest of the shop wears its own face

057 gave every weapon unique art at two sizes and the grow-on-hover
preview. This plan does the same for EVERYTHING else the shops sell:
shields, caster focuses, armor, boots — and the fifteen relics.
After this, no two things in any shop share a face.

## Inventory — 95 unique designs

| group            | count | rungs      | what they are |
|------------------|-------|------------|----------------|
| shields          | 28    | 0.0–10.0   | martial off-hand: bucklers → The Unbroken |
| focuses          | 19    | 1.0–10.0   | sorcerer off-hand: lenses, charms, orbs → Dawnprism |
| armor            | 28    | 0.0–10.0   | torso: jerkins → Aegis of the Vale |
| shoes            | 5     | 1.0–5.0    | boots: cobbled → Stormstep Greaves |
| relics           | 15    | —          | consumables: arrows, oils, nets, potions, scrolls |

The 60 `keen_`/`warded_` shield/armor variants reuse their base art
with the existing `_STYLE_TINT` recolor — no extra renders, exactly
as 057 did for weapons.

Two assets per design, same frames as 057 so every card and cell
shares one CSS system: **100x160 portrait** + **30x48 icon**, both
white ink on alpha, cut from one render.

## The style ladder carries over

Same bands as 057 (POOR → MYTHIC by rung; 0.0 gate-issue kit reads
WRETCHED). Group-specific composition:

- **shield**: front-on, centered, vertical. Crude planks → banded
  iron → mirror-polished → blazing bulwarks.
- **focus**: a small object held in air — lens, charm, orb —
  centered, glow allowed earlier (it IS a light), but POOR focuses
  stay dull glass and bone.
- **armor**: torso piece front-on — jerkin, mail, cuirass, plate.
  No mannequin, no body, no straps flying.
- **shoes**: a PAIR of boots, three-quarter view, one slightly ahead.
- **relic**: the object itself — arrow bundle, dripping flask,
  folded net, sealed scroll, glowing stone. Identity over grandeur.

## Pipeline

Identical to 057 (vision/1bit-images.md): nano-banana-pro prompted
for 1-bit chunky-Bayer pixel art, center-crop 5:8 → 100x160 →
autocontrast → Bayer 8x8 → white ink on alpha; icon is the same crop
at 30x48. Ink-fraction gate [0.02, 0.55] with 3 retries. Raws stay
in this folder; contact sheets in `review/` per group.

Tool: `tools/generate_gear_art.py` — same skeleton as
`generate_weapon_art.py`, 95-entry table, skips existing, batches
of 4. Ships to `plugin_linear_ascent/content/art/gear/{large,icons}`
(weapons keep their 057 home).

## Code touches

- `render.py`: the art helpers stop being weapon-only —
  `_gear_art_slug` resolves ANY Forge item (variants → base) plus
  relic slugs; `_gear_art_url` looks in `art/weapons` then
  `art/gear`. Shop rows, cards and pack cells then pick the face up
  with zero further wiring. The 057b preview builder grows a relic
  branch (name + price, no stat line).
- Tests: every design ships both faces; count is 95; armor/shield
  cards now wear `gicon gw` (updates 057's "armor keeps the shared
  glyph" assertion); a shield card carries a `wprev`; a relic card
  carries a `wprev`; pack cell wears gear art.

## Phases

1. **P1** — this plan + generator table. No stop: the 057 look is
   approved, the ladder and pipeline are proven; bulk-generate all
   95, review contact sheets, regenerate misses.
2. **P2** — wire the resolution generalization + relic preview +
   tests. Ship with 057b in 0.80.0.
