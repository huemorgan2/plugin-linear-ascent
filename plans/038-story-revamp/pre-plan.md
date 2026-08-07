# 038 — The Story Revamp (pre-plan)

*Make the shipped game tell the story the lore now tells: a hundred distinct
stolen countries, monsters that are possessed — not evil — and a blade that
frees instead of kills. Nothing is beyond touch: floors, monsters, art,
animations, copy, and characters are all in scope.*

## The gap (what we found)

The lore layer is finished and the shipped game contradicts it:

- **Floors.** `vision/lore/floors/floor_001..100.md` are complete — each with
  land, flora, places, people, keeper, "The six" beasts (each written **was →
  now**: true animal → fevered shape), finds, Warden, and "when it falls."
  The shipped `plugin_linear_ascent/content/floors/*.yaml` still run the OLD
  ten-biome-block order; **only floor 1 matches the lore.** From floor 11 up,
  zone, gate-town, warden, and monsters all diverge.
- **The mercy system doesn't exist in the build.** Native / Pressed /
  Wrongmade appear nowhere in shipped YAML, schema, or engine. `_victory()`
  says "`{name} defeated`" for everything; the kill-GIF prompt beats literally
  say *"the dead {noun} lies completely still"* — the exact opposite of canon
  ("you are not killing the animal, you are killing the thing wearing it").
- **Animations barely exist.** ~7 hardcoded creature families (all tier 1)
  have kill GIFs, out of 406 shipped creatures. Floor world/warden GIFs exist
  for floors 1–10 only.
- **Guns are still in.** Scrap-rifles/pistols in floors 2–10 + 81 YAML, in
  banner/GIF prompts, and in `design/pixel_art.md`. Canon: no firearms.

## Areas of change

1. **Schema: teach the game the three kinds.** Add `kind: native | pressed |
   wrongmade` to `Encounter` (and `warden:` — wardens are Wrongmade) in
   `content/schema.py`. Validation: every encounter tagged, no exceptions.
2. **Floor content rewrite (the big one).** Regenerate all 100
   `floor_NNN.yaml` from their lore file: zone, gate-town, arrival, keeper
   NPC, warden block, and encounters taken from "The six" (id, name, kind,
   lore line, fight prose that describes the **fevered** shape and implies the
   true animal underneath). Fix floor sequence to the world-lore table order.
   Guns out everywhere.
3. **Engine: a kill frees.** In `combat.py`:
   - `_victory()` copy by kind — Native: "the fever breaks — the true {animal}
     shakes itself loose and slips away" (cure); Wrongmade: "the made thing
     comes apart and drains downward" (eviction); Pressed: a real death,
     written plainly (the tragic one); Warden: eviction + the floor brightens.
   - `_kill_fx()` stops being a 7-family tuple: resolve `<encounter_id>_freed`
     / `_evicted` / `_kill` by slug, fall back to a per-kind generic
     (`native_freed`, `wrongmade_evicted`, `pressed_fall`), then nothing.
   - `[i]` dossier shows the kind in-world ("fevered — a possession riding a
     granary rat").
4. **Animations (the art centerpiece).** One **freeing GIF per creature**,
   prompt derived from the lore's was→now pair, played on the kill card:
   - **Native:** the fevered shape collapses/deflates and the ordinary animal
     steps out of it and walks off (massive angry rat → plain rat). One GIF
     per creature, reused across damage types (typed variants are a later
     polish pass, not this plan).
   - **Wrongmade:** no creature inside — the made shape comes apart (thorns to
     dead wood, chain to slack links) and the dark residue drains *downward*.
   - **Pressed (manufactured/conscript, upper floors' imps & hellknights
     included):** killed, not freed — falls and lies still; kept somber, never
     triumphant.
   - New `_KILL_BEATS` in `generate_event_gifs.py`: three per-kind beat
     scripts replacing the "dead {noun}" beats.
5. **Creature stills.** `generate_creatures.py` already derives prompts from
   YAML prose, so the floor rewrite drives new fevered-shape art
   automatically. New/renamed encounter ids need generation; ids that survive
   keep their PNG. Budget assumption: most of the 600 slots are new.
6. **Floor identity art.** One banner per floor (per-floor `banner:` slug
   replacing the 10 shared biome banners) so floor 4 and floor 6 are
   tellable apart at a glance; world+warden reveal GIFs stay a milestone-floor
   luxury (10, 20, … 100) plus any floor whose art already exists.
7. **Characters.** Keepers per floor from lore (name, role, greet/lore/warn).
   Wardens rewritten as "a mockery of the land's own beast" with eviction
   deaths. Milestone bosses (Gnarl, Skarn, … Vharuk) get their lore framing —
   Gnarl's rifle-crate throne becomes broken-spear/siege-scrap per canon.
8. **Copy sweep.** Intro movie beats, liberation/keeper lines, dossiers —
   kills are cures/evictions everywhere player-facing text speaks.

## The art bill (rough count)

| Asset | Count | Size | Tool |
|---|---|---|---|
| Creature stills (fevered shapes) | ~500–600 new/redone | 320×112 PNG | generate_creatures.py (auto from YAML) |
| Freeing/eviction/death GIFs | ~600 (one per encounter) | 320×112 GIF | generate_event_gifs.py + new per-kind beats |
| Warden stills | 90 + 10 milestone | 320×112/200 | generate_creatures.py |
| Warden eviction GIFs | 10 milestone first, rest generic | 320×200 | generate_event_gifs.py |
| Floor banners | 100 | 320×112 | generate_banners.py (prompts from lore "The land") |
| Gun-purge redoes | gnarl banner, floor-10 world/warden GIFs, floor-81 set | — | regenerate |

GIFs are the cost driver (video model, ~seconds each, per-frame dither). If
600 is too heavy for one pass: ship per-kind generic GIFs first (3 assets
unblock every floor), then per-creature GIFs floor-tier by floor-tier.

## How it runs in parallel

The serial spine is small; everything expensive fans out per floor-tier.

- **Phase 0 (serial, one session):** schema `kind` field + combat.py kill-card
  changes + new GIF beat scripts + a `tools/lore_to_floor.py` helper that
  parses a lore file's "The six"/keeper/warden into YAML scaffolding + the
  3 per-kind generic GIFs. After this, every floor is unblocked and
  independent.
- **Phase 1 (10 lanes × 10 floors):** one agent per tier (floors 1–10, 11–20,
  … 91–100). Each lane owns its ten floors end-to-end:
  1. rewrite the ten `floor_NNN.yaml` from lore (ids, kinds, prose, keeper,
     warden, no guns),
  2. run `generate_creatures.py` for its new slugs (+ contact sheet eyeball),
  3. run the freeing-GIF generation for its creatures,
  4. run its floor-banner prompts,
  5. self-QA: schema validation, one scripted fight per floor, screenshot of
     one freeing card.
  Lanes never touch shared files — floors are per-file, art is per-slug — so
  10 (or 20) can run simultaneously. API rate limits on the image/video
  models are the real ceiling; lanes batch 4 jobs at a time like the existing
  tools already do.
- **Phase 2 (serial, short):** milestone-boss pass (10 bosses, their reveal
  GIFs + lore framing), intro-movie copy sweep, full test suite, dojo
  walkthrough (fight a Native, a Pressed, a Wrongmade, and a Warden; verify
  the three kill cards read as cure / death / eviction), vendor, ship.

## Verification

- Schema gate: 100 floors load, every encounter has `kind`, zero
  banned-word/gun hits (`rg -i "rifle|pistol|gun"` over content = 0).
- Plugin + worldd suites green; new tests: kind-specific victory copy,
  `_kill_fx` slug resolution, warden eviction path.
- Dojo scenario per tier: enter floor, fight one of each kind, screenshot the
  freeing card, judge the copy against §5 of world-lore.md.

## Open decisions (deliberate, before phase 1)

1. **GIF depth for v1:** per-creature freeing GIFs for all 600, or per-kind
   generics + per-creature for tiers 1–3 first? (Cost/latency call.)
2. **Floor re-sequencing** moves players' current floor numbers — ship as an
   era reset or map old→new floor numbers for live tenants?
3. **Boss floor world/warden GIFs** for 20–100: this plan or a follow-up?
