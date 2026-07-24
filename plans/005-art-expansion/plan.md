# 005 — Art Expansion: every creature, living places, a vast bright world

Goal: grow the art set from today's 38 banners to full coverage of the
game's cast and places, in the **same 1-bit Bayer-dithered style**
([design/pixel_art.md](../../design/pixel_art.md)), with three deliberate
shifts:

1. **Characters** — an image for every encounter and every Warden:
   the wolves, boars, goblins, spiders, trolls, giants, drakes, shades,
   demons — all ~400 of them.
2. **Places alive with people** — towns and interiors populated with
   small figures (market stalls, smoke, travelers, kids, guild crowds),
   not empty stage sets.
3. **Less gloom, more vastness** — outdoor scenes get big luminous
   gradient skies (the `ascent` banner is the reference: mostly light,
   sparse dither, optimistic). The higher the player climbs, the more
   open sky they see, paying off at Stormreach and the endgame.

**The complete image list, floor by floor (1–100), is in
[floors.md](./floors.md).**

## 1. Formats — two sizes only

- **320×112 (20:7)** — the standard. Every encounter, every regular
  warden, every zone banner, every gate-town banner, every interior.
  Same banner discipline as today: wide shot, one dominant subject,
  white ink on alpha, renderer tints.
- **320×200 (8:5, the title-card grid)** — reserved for the ten
  milestone bosses (floors 10, 20, … 100) and a handful of showpiece
  areas: the `ascent` reveal, the Stormreach cloud-sea vista, the
  `victory` dawn panorama. Taller frame = a moment that stops the game.

No new portrait format. Creature images are banner-composed: the
creature is the dominant subject of a wide scene (like `cindermaw`,
`vyx`, `huntsman` already are).

**Tints:** encounters and zones → `--dim`; wardens and milestone
bosses → `--violet`; death → `--red`; present/victory → `--gold`.

**Where shown (keeps "images are a reward, not wallpaper"):** the
encounter card (first-sighting prose) and warden arrival card only.
Combat round cards stay pure text.

## 2. Style shifts (edit the shared STYLE preamble + styleguide)

- **Daylight variant** of the prompt preamble for outdoor scenes:
  "mostly WHITE, sparse dither, a huge luminous sky, low soft cloud
  banks, long morning light" — invert today's night-sky default.
  Target ≥55% ink coverage on daylight scenes (the script already
  prints ink %; assert it).
- **Populated clause** for towns/interiors: "small silhouetted figures
  going about their day — stall keepers, children, a traveler leading
  a mule, chimney smoke, laundry lines" — 5–12 figures, none dominant.
- **Sky progression across tiers** (vastness the player feels):
  - T1–T3: floodlit night and dusk (as now) — the tower's belly.
  - T4: lightless (Webdeep) — the low point, darkest tier.
  - T5–T6: hard bright daylight (ash glare, snow glare).
  - T7 Stormreach: **wide-open blue-sky peaks above a cloud sea** —
    the "great outdoors" reveal; brightest zone banner in the game,
    320×200 showpiece.
  - T8: pale paper-grey, not black.
  - T9–T10: furnace dark — so the final contrast lands.
  - **Victory vista:** after Vharuk falls — dawn panorama from the
    Crown's summit, the whole world below, huge bright gradient sky.
    New `victory` 320×200 (gold tint), shown on the floor-100 clear card.
- Document all three shifts in `design/pixel_art.md`.

## 3. Image inventory (audited from content; full list in floors.md)

| Asset class | Count | Size |
|---|---|---|
| Encounter images (unique `id` across 100 floor YAMLs) | 299 | 320×112 |
| Regular wardens (floors x1–x9), `warden_NNN` | 90 | 320×112 |
| Milestone bosses (floors 10…100) — exist, regen only if the taller crop needs it | 10 | 320×200 |
| Zone banners (rework to sky rules, one per tier) | 10 | 320×112 (Stormreach 320×200) |
| Gate-town banners (new, populated, one per tier) | 10 | 320×112 |
| Village interiors regenerated with occupants | 6 | 320×112 |
| Showpieces: `ascent` (regen taller), `victory` (new) | 2 | 320×200 |
| **Total new/redone** | **≈417** | |

Content fix found during audit: `floor_010.yaml` has `banner: greenreach`
while every other milestone floor uses its boss banner — change to
`banner: gnarl`.

## 4. Prompts scale from content, not by hand

400 hand-written prompts is the trap. The floor YAMLs already contain
excellent prompt seeds — every encounter has `name` + `prose`
("A boar the size of a cart tears up the turf… tusks yellowed, one ear
ragged"). New `tools/generate_creatures.py`:

1. Walk `plugin_linear_ascent/content/floors/*.yaml`.
2. Build each prompt as: STYLE preamble (night/daylight variant by
   tier, §2) + creature `name` + its `prose` + the tier's biome flavor
   line (small lookup table, 10 entries).
3. Generate at 21:9, post-process to 320×112 (or 320×200 for
   milestone slugs) exactly as `generate_banners.py` does.
4. Emit a contact sheet per tier (`preview/sheet_tier_NN.png`, ~40
   images on one panel) for fast human review.
5. `--only <id ...>` and `--redo-list file` flags for the cull/regen
   loop.

Batches of 4 against the rate limit. ~410 generations ≈ a few hours of
wall-clock plus review passes; budget 1.3× calls for rejects.

## 5. Phases

**Phase A — specs and tooling (no API spend).** Style shifts §2 into
`design/pixel_art.md`; `generate_creatures.py` with a procedural
placeholder mode (like `tools/banners.py`) so card layout work starts
immediately; renderer support for the image slot on encounter/warden
cards; `floor_010.yaml` banner fix; manifest cache-busting.

**Phase B — pilot: Greenreach (tier 1, floors 1–10).** The floors.md
tier-1 block: 30 encounters + 9 wardens (320×112) + reworked brighter
`greenreach` zone banner + populated `town_lamplit_steading`. Human
review of the contact sheet settles the look before 90% of the spend.
Exit: pilot sheet approved.

**Phase C — full character sweep.** Tiers 2–10 from floors.md
(~269 encounters + 81 wardens), tier by tier, contact-sheet review per
tier, regen rejects.

**Phase D — living places.** 9 remaining gate-town banners, 6
interiors with occupants, 9 zone banners to the sky progression
(Stormreach 320×200 showpiece), `ascent` regen, `victory` vista.

**Phase E — wire and ship.** Encounter images key off encounter `id`,
wardens off `warden_NNN`/boss slug; new `town_banner:` value per tier;
bump plugin version, vendor sync, publish.

## 6. Open

- 16px inline icons (shop/loot rows) remain out of scope, as in
  pixel_art.md §5.
- Which non-boss areas earn 320×200 beyond Stormreach/ascent/victory —
  nominate during tier reviews.
