# 057 — every weapon wears its own face

Today all 27 swords share one 16×16 glyph, all 27 bows another, all 27
staves a third. The racks read as one weapon sold 27 times. This plan
gives every weapon its own 1-bit art, at two sizes, and turns the
Arcanum into the same card wall the Forge already is.

## What ships

1. **Unique art per weapon** — 85 unique designs: 81 shop-line
   weapons (27 swords + 27 bows + 27 staves, `economy.weapon_line`)
   plus the four basics (`rusted_shiv`, `rusted_sword`, `basic_bow`,
   `worn_staff`). The 60 `keen_`/`warded_` variants reuse their base
   weapon's art with the existing `_STYLE_TINT` recolor — no extra
   renders. Two assets each:
   - **Large portrait `100x160`** (white ink on alpha) — the hero
     image, shown on hover.
   - **Icon `30x48`** (white ink on alpha, upright) — replaces the
     shared glyph on the Forge/Arcanum cards and anywhere the weapon
     icon renders from FORGE gear (pack strip keeps 32×32 grid glyphs
     for non-weapons; weapons switch to the new icons).
2. **Hover = the big picture.** The card's tooltip already supports
   server-authored HTML (`data-tiph`, rendered via TIP_JS innerHTML).
   Weapon cards embed the 100x160 as a data-URL `<img>` above the
   colored param line — hovering a rack card shows the weapon large.
3. **The Arcanum becomes the Forge's twin.** `_arcanum_scene` gets
   `grid=True`, drops the prose `body_lines`, keeps ONE line of
   explanation (the shard note), and adds the same folded legend the
   Forge carries. Same card wall, same hints, same [i] tips.

## The style ladder — weak steel looks weak

Power must read at a glance. Rung drives the design language; every
prompt is built from the same ladder so the three lines age in step:

| rung      | levels | design language |
|-----------|--------|-----------------|
| 1.0–1.4   | 0–5    | POOR: crude, chipped, dull, wrapped grips, no ornament, no glow, small in frame, workmanlike |
| 1.5–1.9   | 5–10   | PLAIN: honest clean steel, simple guard, still zero glow, modest size |
| 2.0–3.5   | 10–35  | FORGED: proper weapon, etched fuller / laminated limbs / fitted brass, first faint edge-light |
| 4.0–5.5   | 35–55  | FINE: ornate guard, engraved runes, designed glow ramps along the edge, larger in frame |
| 6.0–7.5   | 55–75  | MASTER: elaborate silhouette, radiant rune-light, energy licking the edge, dramatic |
| 8.0–10.0  | 75–100 | MYTHIC: huge in frame, blazing halos, starlight/dawn gradients pouring off the blade |

Each weapon's prompt = ladder band + its NAME mined for identity
(Wolfbite → wolf-jaw guard; Emberfang → ember glow seams; Dawnbreaker
→ sunrise halo), so no two weapons in a band look alike either.

## Pipeline (per vision/1bit-images.md)

Model designs the dither; post only enforces the grid:

1. nano-banana-pro, aspect 9:16, prompted for **1-bit pixel art
   directly**: single weapon, vertical, centered, pure black
   background, FULLY 3D-SHADED in chunky Bayer dither (not a flat
   silhouette), one strong top-left light, designed glow gradients
   only where the ladder allows them, no text/border/watermark.
2. Enforce: center-crop to 5:8 → LANCZOS to 100x160 →
   `autocontrast(cutoff=1)` → Bayer 8x8 → white ink on alpha.
3. **Icon derived from the same raw** (no second model call): 30x48
   is exactly the portrait's 5:8 aspect, so the icon is the same
   upright center-crop downscaled — LANCZOS to 30x48 → autocontrast →
   Bayer. One render, two assets, and the icon always matches its
   hero image.
4. Raws saved versioned in the plan folder (never shipped); shipped
   PNGs are 1-bit and tiny (~1–3 KB each — ~250 KB total for all 85).

New tool: `tools/generate_weapon_art.py` — SCENES-style table built
procedurally from `economy.weapon_line` + the ladder + per-name
identity hints; accepts slugs as args; skips existing unless
`--force`; batches of 4.

## Code touches

- `icons.py` or `render.py`: weapon icon resolution — if
  `content/art/weapons/icons/<slug>_30x48.png` exists, render it as
  the mask (same data-URL technique as banners); else fall back to
  the old shared glyph. `.gicon` CSS size 32×32 → 30×48.
- `render.py` card wall: weapon cards get `data-tiph` = `<img>` (large
  art data-URL, 100px wide) + colored params + prose.
- `core.py` `_arcanum_scene`: `grid=True`, legend, one-line support.
- Tests: every `weapon_line` slug resolves a 30x48 icon and a 100x160
  portrait; arcanum scene has `grid` set; a weapon card's tiph carries
  an `<img>`; ladder smoke (a rung-1 asset and a rung-10 asset exist
  and differ).

## Phases

1. **P1 — this folder: 10 sample swords** (below) + this plan. STOP
   for review — roy judges the look before any bulk generation.
2. **P2** — bulk-generate all 85 (≈85 model calls), review contact
   sheets, regenerate the misses.
3. **P3** — wire icons + hover + Arcanum card wall + tests, ship.

## P1 — the 10 review swords

`swords/` holds, for each: `<slug>_raw.png` (model output),
`<slug>_100x160.png` (shipped-spec white ink, previewed on panel),
`<slug>_30x48.png` (icon), and a `contact_sheet.png` with all ten side
by side, poorest → mythic:

scrap_dagger (1.0) · boarspine_shortsword (1.3) · iron_sword (1.5) ·
goblin_iron_falchion (1.7) · wolfbite (2.0) · emberfang (3.0) ·
thornsong (4.0) · oathkeeper (5.0) · starfall (7.0) · dawnbreaker (10.0)
