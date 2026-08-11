# Phase 4 — classes die

Goal: no class question, no off-class system, gates follow
slotted-weapon+rank, sheet shows TRAINED+HOLDING. The big test
sweep lands here. Biggest phase; still one commit.

## Tests first (red)

1. `tests/test_048_no_classes.py` (T7 engine part):
   - `economy.CLASSES` / `OFF_CLASS_*` / `class_starter` absent;
   - no `p.get("clazz")`/`p["clazz"]` reads in engine outside
     state.py migration/tolerance (AST or grep with whitelist);
   - creation flow scenes: race → name (no class scene); rendered
     creation/town/shop/tip text free of warrior/archer/sorcerer/
     class words (weapon-line slugs whitelisted).
2. T1 gate cases: for a fresh classless doc — treeline needs bow
   slotted + bow≥4 (locked text `needs Bow rank 4 (you: 2)`);
   create distance bow≥6; gap draw bow≥8; shield wall shield +
   blade≥4; sleep staff≥6; per-slot attack options with sword+bow
   both slotted (labels weapon+rank+predicted dmg).
3. Starter: creation grants Rusted Sword + blade 2; armory lists
   basic_bow + worn_staff at 60 gold; all weapon lines listed for
   everyone at list price.

## Code (green)

- `core.py`: `_creation_class_scene`/`_creation_pick_class` die;
  race → name; starter kit fixed.
- `economy.py`: CLASSES/OFF_CLASS_*/off_class_price/offer/arrow
  burn die; BASIC_WEAPON_PRICE=60; armory declassed; contracts →
  weapon-path wording (CONTRACT_CLASS_GOLD_MULT → path jobs).
- `combat.py`: every clazz gate → slotted-weapon+rank gate (N7
  table); one attack option per held weapon (each rolls own rank;
  triangle answer text comes ph 5); off-class miss/burn branches
  die.
- `tips.py`, `social.py`, `scene.py`, `icons.py`, `render.py`:
  class words → weapon words; icons ⚔/➶/✦ by path.

## The sweep (scripted)

~30 files with local `create_character(..., clazz=...)`:
`python plans/048-the-weapon-decides/phase-4/sweep_tests.py`
- rewrites the local helpers' creation walk (drop the class
  choose; keep signature, map clazz→pre-trained path rank 6 +
  grant that path's basic weapon into held) so each file's
  MEANING survives;
- `test_017_offclass_migration.py` deleted (T1 migration covers);
  off-class racks in test_017_shops + class-gate cases in
  test_037_sleep/test_036_gap_and_grants rewritten as rank gates;
- expected-text fixes done by hand from the failure list.
Keep the sweep script in this folder for the record.

## Green =

T7 engine part, T1 gates, full swept suite.
Commit: `048 phase 4: classes die — weapon+rank gates, School-era
creation, test sweep`.

## Learnings applied (from phase 2)

- Delete the two transitional off-class gates in combat.py (marked
  `transitional until phase 4`): the atk//2 floor branch in
  _player_hit and the `not _off_class` guard on the rank miss.
- `_train_path` fallback `p.get("clazz")` dies with the class field.

## Learnings applied (from phase 3)

- Every writer of `gear["weapon"]` must maintain `p["held"]` —
  `_gear_purchase` and `_wear_from_pack` do; when the class racks
  die, keep the held bookkeeping in whatever replaces them (one
  helper, not three copies).
- Off-class death touches MORE than combat: `_gear_purchase` (off
  pricing + "off-class: half the bite" note), `pack_actions`, the
  Arcanum's off_class_offer rack. Grep `off_class|_off_class`.
- New/removed town options must keep `tips.py` in step (test_014
  walks every option) and new *_LEVEL constants must register in
  unlocks.py + the test_020 guard set.
- Rows removed from menus can't be reached via `apply_choice`
  (option validation) — test dead-row guards via the action
  handler directly.
