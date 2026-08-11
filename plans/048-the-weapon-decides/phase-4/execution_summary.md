# Phase 4 — execution summary

Commit: `a66a7a3 048 phase 4: classes die — weapon+rank gates,
School-era creation, test sweep`. Suite: 1004 passed, 2 skipped,
1 xfailed; test_034 baseline-red excluded (fails on main too).

## What landed

- Creation: race → name. `_creation_class_scene`/`_creation_pick_class`
  deleted; `_creation_finish_race` grants Rusted Sword + blade 2 and
  seeds `held`. Prenamed docs skip the registrar straight to welcome.
- Off-class system deleted whole: `off_class_price`/`off_class_offer`/
  `CLASSES`/`class_starter`/`OFF_CLASS_*`/`_off_class`, arrow burn,
  quiver fallback, class racks, focus gate, hone exclusion.
- N7 gate table in economy.py (TREELINE_RANK 4, GAP_OPEN_RANK 6,
  GAP_DRAW_RANK 8, WALL_RANK 4, SLEEP_RANK 6); fight_scene builds
  locked rows `needs Bow rank 4 (you: 2)`; handlers refuse with
  `_no_round` so a refused click spends nothing.
- Per-held attack rows (`attack_<slug>` promotes then attacks);
  `_promote_held` is the single writer of held order.
- Basics (basic_bow/worn_staff) sell to anyone at flat
  BASIC_WEAPON_PRICE=60 via `_basic_buy` — FORGE price stays 0 so
  they never wear/pawn/drop (price>0 is the wear key).
- Relic stock filters by `combat._held_lines(p)`; refusal wording
  is "answers only to a staff…" (hand, not class).
- Meters.clazz now carries the PATH name (wire-compat: old clients
  render it as the calling); contracts keep job kind "class" and ids.
- 17 new tests in tests/test_048_no_classes.py (machinery-gone grep,
  classless creation, basics at 60, N7 gates, per-slot rows,
  rendered-text-is-class-free).

## The sweep

`sweep_tests.py` (kept in this folder) rewrote 31 files' local
creation helpers: class choose deleted, clazz mapped to path rank 6
+ that line's basic weapon in held. test_017_offclass_migration.py
deleted. Then a hand pass over 49 residual failures → 0.

## Learnings (propagated into phases 5–8)

1. **The sweep regex missed helpers not named
   create_character/make_character/_character** — test_033 `playing`,
   test_022_001 `playing`, test_036 `_player`-callers needed hand
   kits. Later phases: grep `apply_choice(p, "(warrior|archer|
   sorcerer)")` to find stragglers, not helper names.
2. **One engine bug hid behind the tests**: a leftover `if off:` note
   branch in `_gear_purchase` (core.py) — NameError only on the buy
   path. The phase-plan grep list (`off_class|_off_class`) missed the
   bare variable. Grep bare identifiers too after big deletes.
3. **Seeded-rng tests survive the kit** because it restores the exact
   pre-048 rank (6); tests that need the rank-8 draw bonus must now
   train it explicitly (test_036 ladder).
4. **Ident/calling wire fact for phase 7**: the pane shows race +
   PATH ("elf bow") — mechanics page and any copy must say path, not
   class.
5. **Migration tests must plant `p["clazz"]` themselves** now that
   new docs never carry it (test_017_damage_types v1 docs,
   test_048 legacy rank-6 migration).
