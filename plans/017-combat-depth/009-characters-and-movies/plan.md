# Phase 009 — Characters, races, movies, kill FX

Goal: the cast matches the canon — three showcase characters (male elf
ARCHER, female human WARRIOR, giant dwarf WIZARD), halflings migrated,
dwarves rendered as giants everywhere, kill FX per damage type.

Can start in parallel any time after 001 (needs the bestiary names and
the damage-type kill hooks only).

## Tasks

1. **Race migration** (`engine/state.py` doc v2): halfling → closest
   race, default human (an in-world pending-event letter explains the
   change and the retired luck bonus); creation menu drops halfling;
   `RACES` table updated. Luck-day flag/charm mechanics unaffected.
2. **Art canon:** all character prompts updated to the three showcase
   characters + the giant-dwarf scale rule (two heads taller, wider —
   `vision/story.md` is canon). Creation scene blurbs re-checked.
3. **Intro movie:** regenerate the refugee/climber scenes with the
   three characters (Veo pipeline, `plans/016-intro-movie/` tooling);
   the dwarf must visibly loom.
4. **Kill FX ×3 (floors 1–3 first — approved staging):** each floor
   1–3 monster family gets melee/arrow/magic kill variants; `_kill_fx`
   picks by the landing damage type; renderer skips missing art
   silently (later floors ride 008 batches).
5. Icons/consistency pass: 16×16/32×32 1-bit constraint audit on
   everything 003–006 added.
   003 retro: trait icons ship as CSS-mask SVG data-URLs built from
   grids in `icons.py` (`test_017_info_card.py` asserts 16-wide grids
   and valid masks) — the audit extends those tests, not eyeballs.
6. Vendor sync + deploy; version bump + publish.

## Tests / acceptance

- Unit: migration (halfling docs of each class), `_kill_fx` type
  selection, creation menu has exactly 3 races.
- Migration soak: run `ensure_current` over a snapshot of every player
  doc shape in the shared world (worldd export) — zero errors.
- Art review: side-by-side frames in the summary — dwarf scale is
  unmistakable; movie plays in `movie.html`.
- Dojo: create a character (3 races only); kill a wolf as each class
  and see three different endings.

Exit: all green, published, worldd synced, `execution_summary.md`.
