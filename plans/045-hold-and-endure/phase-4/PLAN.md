# Phase 4 — the floor comes back after a fight

## Goal

The card after killing an animal (and after being driven back, fleeing,
polymorph or sleep-walk escapes — all five `_after_fight_options`
consumers) shows the floor's full menu: hunt, deep hunt (when
unlocked), stew/heal/medgel/trauma kit (when hurt), flare answer, keep
(with the correct fallen-warden label), NPC talk, gate (when a deeper
floor is unlocked), town — plus the hunt/keep art tiles. Measurable:
after a hunt victory with hp < max, the option ids are a superset of
`_gate_town_options` ids.

## Steps

1. `engine/combat.py _after_fight_options()` (~1249): deferred
   `from . import core` (pattern at combat.py:1041); build rows from
   `core._gate_town_options(p, floor)`; relabel the `hunt` row to
   "Hunt the wilds again"; insert the `gate` row ("Back to the tower
   gate") after `hunt` when `p["unlocked_floor"] > floor.floor` (that
   row is a gate-town-scene affordance, not part of
   `_gate_town_options`) — verify `gate` dispatches from
   `location == "gate_town"` before relying on it.
2. Victory/exit scenes (~1186, 1487, 1651, 1869, 1960): attach
   `option_art=core._gate_town_art(floor)` where the scene supports it
   (victory card at minimum, combat.py:1231–1245).
3. Leave untouched: first-clear `next`/`skip` reel branch (1187–1194),
   `_shared_warden_victory`, `_death` menus.

Inheritance: vendored at ship time.

## Verification

New tests in `tests/test_045_hold_and_endure.py`:
- hunt victory (hurt, floor with NPC, deep-hunt floor) → options include
  `hunt`, `hunt_deep`, `stew`, `heal`, `keep`, `talk`, `town`; and
  `gate` present iff `unlocked_floor > floor`.
- every offered id survives a round-trip through `apply_choice` (the
  gate-town handler accepts it) — guards against offering rows the
  `gate_town` dispatcher can't handle.
- after-fall keep label shows the monument wording, not "3 ⚡".
Then `pytest tests/test_engine.py tests/test_031_the_shape_of_things.py tests/test_045_hold_and_endure.py`.

## Rollback

`git revert` the phase commit — pure option-list construction, no
state.
