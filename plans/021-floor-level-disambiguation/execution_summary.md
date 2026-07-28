# Execution summary — plan 021, floor is not level

Status: **complete**. Zero behaviour change, proven by golden values.

## What was done

- `economy.py` header: the vocabulary note (floor = tower, level = player,
  equated only in `reference_level`).
- `reference_level(floor)` + `reference_player_hp(floor)` added — the one
  named floor→level bridge.
- `warden_stats` now reads `reference_player_hp(floor)` instead of
  `player_max_hp(floor)` (the load-bearing conflation at economy.py:386).
- `_at_level_loadout` routed through `reference_level` + `player_atk` /
  `player_def` instead of restating their formulas inline.
- Renames: `gear_level_req` → `gear_player_level_req`,
  `rung_level_req` → `rung_player_level_req`,
  `floor_level_req` → `floor_entry_player_level`. Callers updated in
  `engine/core.py`, `engine/tips.py`, `economy.py`.

## Tests

`tests/test_021_floor_is_not_level.py`, four tests:

1. `test_warden_stats_unchanged` — golden tuples for all 100 floors,
   captured pre-refactor at a975042. Byte-identical after.
2. `test_warden_tuning_reads_the_reference_player` — patching
   `reference_player_hp` moves warden ATK (and nothing else).
3. `test_reference_level_is_the_only_floor_to_level_bridge` — AST guard:
   no module passes a `floor`/`unlocked_floor`/`frontier` variable into a
   level-typed function. This is the durable one.
4. `test_gate_and_gear_requirements_unchanged` — the three renamed gates
   return pre-rename values for every tier, rung and floor.

Suites: plugin **458 passed**, worldd **53 passed** after re-vendor.
Two existing tests needed *mechanical rename edits only*
(`test_economy.py::test_level_gates`, `test_017_shops.py`) — every
asserted number is unchanged, which the goldens independently prove.

## Learned / forward notes

- `_at_level_loadout`'s inline `3*floor + …` was a second, silent copy of
  the player formulas; it now shares them. Any future change to
  `player_atk`/`player_def` propagates to monster tuning automatically —
  022 phase 002 relies on this.
- The AST guard also flags `frontier` — cheap extra safety for 022 phase
  001, where the world frontier starts flowing into the plugin.
