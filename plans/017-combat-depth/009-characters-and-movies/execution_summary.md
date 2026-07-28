# 009 — Characters, races, movies, kill FX: execution summary

Shipped as v0.26.0. The cast now matches the canon: three races, three
showcase characters (female human WARRIOR, male elf ARCHER, giant dwarf
WIZARD), typed kill endings on floors 1–3, the intro movie reshot with
the cast.

## What was built

1. **Doc v4 — halfling retirement** (`engine/state.py`). New docs are
   v4; `ensure_current` re-registers existing halflings as human (the
   closest line) and, for playing docs, delivers an in-world letter
   ("ROOTHOLLOW · A LETTER FROM THE REGISTRAR / The Stone re-registers
   your line") exactly once. Mid-creation halflings migrate silently.
   The racial luck bonus retired with the listing; luck DAYS and luck
   CHARMS never keyed off race and are untouched (`core._maybe_present`
   and `combat._victory` now test only the `luck_day` flag). `RACES`
   lists three lines; the creation slate renders from it, so halfling
   is gone from the gate (invalid options are no-ops — no guard code
   needed). Tips lost the halfling angle; `vision/story.md` records the
   retirement.
2. **Typed kill FX** (`engine/combat.py`). `_kill_fx` now prefers
   `<family>_kill_<melee|arrow|magic>` by the LANDING damage type
   (weapon-decided, `_damage_type`), falls back to the legacy untyped
   `<family>_kill`, then `ascent_open` on first clears. Family matching
   is per-token-prefix ("wolfpack" is wolf; "curator" is NOT rat).
   Families cover every floor 1–3 wilds monster: wolf, boar, goblin,
   rat, tortoise, haunt (+ brackjaw retains its untyped cinematic).
3. **18 new kill GIFs** via the Veo 1-bit pipeline
   (`tools/generate_event_gifs.py`): 6 families × 3 damage types, each
   ending on a frozen killer-over-monster tableau — the warrior's sword
   stroke, the archer's single arrow, the giant wizard's staff bolt.
   Config is generated (`_KILL_MONSTERS` × `_KILL_BEATS`), so a new
   family is one dict line.
4. **Art canon** — `CAST_WARRIOR/ARCHER/WIZARD` constants encode the
   showcase characters incl. the giant-dwarf scale rule; every legacy
   kill prompt was recut from the spear hunter to the canon warrior
   (shipped GIFs kept; reshoots land on canon).
5. **Intro movie reshoots** — `intro_refugee` (the three refugees
   before the tower, dwarf looming) and `intro_muster` (the cast
   anchors the line, the dwarf breaks its silhouette). Verified live
   in-game during the dojo, not just in movie.html.
6. **Icon audit** (16×16 1-bit, both surfaces): every FORGE item,
   every relic (pack strip via `icons.icon_key` AND shop rows via
   `render._opt_gear_icon` — they resolve independently), every
   apothecary item lands on a real glyph, never the pack crate; all
   grids are exactly 16×16 `#`/`.`. All green without fixes — 004/006
   held.

## The day-seed catch (and three real walls it was hiding)

The full-suite run crossed the 06:00 UTC world-day boundary and two
"green" tests failed: every sim roll is keyed by
`(user, world_day, counter)`, so the matchup gates were re-rolling
daily, and marginal matchups flipped with the date. Fixes:

- `_sim_fight` now pins `state.world_day` to `_SIM_DAY = 137` — the
  gates measure design, not today's dice (001 + 008 gates both ride
  this).
- With the pin, a scan (`scan_walls.py`) surfaced every wall the lucky
  008 seed had been hiding — three med-tier counters that were "safe
  AND quick" for their countered class: floor 15 `rod_wisp`
  (flying+resist_med, sorcerer 90% win at 1.48× drag), floor 66
  `shroud_crab` (armor_med+slow — the exact 008 prey-grade shape),
  floor 74 `glade_dancers` (resist_med, 1.59× vs the 1.6× bar). All
  three bumped to the high tier (YAML + band specs); smoothness and
  lint gates held without re-tuning weights.
- `test_open_distance_success_and_failure` pinned its damage roll: a
  low day roll chips 1, which the −50% free hit legally rounds to 0.

## Verification

- 406 plugin tests green (20 new in `test_017_characters.py`:
  migration × class, letter idempotence, luck survival, `_kill_fx`
  selection incl. token safety, art-on-disk gate, icon audit); 53
  worldd tests green against the synced vendor.
- **Migration soak** (`soak.py`): `ensure_current` over all 1,535 real
  docs in the shared world DB — 17 doc shapes, 6 halflings → 0, zero
  errors. Rerunnable against any DATABASE_URL for the 010 prod
  rehearsal.
- **Dojo (real browser, screenshots in `dojo/`)**: three-race slate,
  registrar letter once-only with doc → `human|4`, and the same floor
  hunted as all three classes producing three different endings
  (`wolf_kill_melee` / `rat_kill_arrow` / `boar_kill_magic` — asserted
  from the scene doc AND read off the screen).

## Learnings (propagated to 010 + dojo skill)

- **Day-seeded gates are landmines**: any test whose rolls derive from
  `world_day()` re-rolls every UTC morning. Pin the day in sims; treat
  a test that fails "for no reason" after 06:00 UTC as this first.
  And when a threshold gate passes, ask how close — the three walls
  above all sat within noise of their bars.
- **Veo error code 13 can be prompt-triggered**: "translucent ghostly
  haunt" failed server-side twice; rewording to "wisp creature — a
  drifting cloud of pale glowing light" generated first try. If the
  same slug fails twice while others pass, reword before retrying.
- **A failed slug aborts the whole batch** — the generator raises on
  the first Veo error, so completed clips are kept (mp4 cache) but the
  rest never run. Chain follow-up commands with `;` not `&&`, and
  re-run only the missing slugs.
- **Luna restart is part of art shipping**: `render._fx_data_url`
  lru-caches misses — a Luna that booted before the GIFs landed will
  never show them. Vendor sync + worldd restart (008 lesson) + Luna
  restart (009 lesson) is the full checklist.
- **Browser mechanics**: the pane iframe is the one whose src contains
  `plugin-linear-ascent` (index 3 of 4); after a psql doc edit, reload
  the iframe and WAIT (~3 s) in a separate evaluate — clicks in the
  same evaluate land on the stale scene. The scene doc's `fx` field
  (`doc->'scene'->>'fx'`) is the ground truth for which ending played.
- The dwarf reads GIANT (beyond two heads) in both reshoots — accepted:
  the acceptance bar was "unmistakable", and the frames are epic.
