# Phase 3 — endurance made visible

## Goal

Every forge card for a shield/armour shows both numbers — `+N DEF` and
`END n` — where END is the damage the piece can turn before it breaks;
weapons/shoes show their END in swings/strides. The pack cell hover,
item tip and character sheet show `left/total`. Repair rows state what
they restore. Prices are untouched; a test proves END rises with price
within each ladder (so 1000-END plate reads costly, 200-END cheap, and
the warded/keen styles price their endurance honestly).

## Unit design (the load-bearing insight)

Wear per blow is `guard_wear = 6·blocked_by_piece/bonus` pool-units
(economy.py:1674). Therefore `pool·bonus/6` is the total damage the
piece can turn, and `left·bonus/6` falls by exactly the damage absorbed
each blow. Displaying that product IS the user's requested mechanic
("blows of 54+36+10 = 100 then it's broken") with zero change to combat
math, balance, or saved durability values. No migration.

## Steps

1. `economy.py` — add `endurance(item) -> int` = `round(item_pool·bonus/6)`
   for shield/armor; for weapon/shoes return `item_pool // wear-per-use`
   (weapon swing tick / shoe stride tick — read the actual tick constants
   in combat.py before writing this; label stays END). Add
   `endurance_left(item, left) -> int` with the same scaling.
2. `engine/core.py` — `_stat(g)` / rack hint (~1114–1135): hint becomes
   `pay ◈ {price:,} · +{bonus} DEF · END {endurance}` (ATK/spd
   respectively); style rows too. Repair row hint (~1283) appends
   `restores END {endurance}`.
3. `engine/core.py _pack_strip()` (~75–78): alongside `dur` fraction,
   ship `dur_left`/`dur_max` as END-scaled ints.
4. `render.py _slot_cell()` (~986–999): hover tip becomes
   `END {left}/{total} — repair at the Forge` (guard with `.get` so old
   scenes from a not-yet-rolled server render as today — scene/render
   halves ship separately).
5. `engine/tips.py item_tip()` (~562): append `END left/total` for
   owned gear, `END total` for catalog gear.
6. `sheet.py _piece()`: `(worn to N%)` becomes `(END left/total)`,
   broken text keeps the half-strength warning.
7. New test `tests/test_045_hold_and_endure.py`: (a) END monotone
   non-decreasing with price within each slot ladder at fixed style, and
   keen < base < warded at fixed rung; (b) after `_monster_hit` with a
   shield equipped, displayed END drops by exactly `blocked_by_piece`
   (±1 rounding); (c) forge hint contains both `DEF` and `END`.

Inheritance: vendored at ship time.

## Verification

- `pytest tests/test_045_hold_and_endure.py tests/test_034_shield_wear.py tests/test_035_the_plate_pays_too.py tests/test_014_inventory_tooltips.py`
- Full suite + difficulty gate compare (no economy numbers changed —
  gate result must equal HEAD's).
- Print the T1–T5 shield/armor table (price, DEF, END) in the execution
  status as the "numbers work" record.

## Rollback

`git revert` the phase commit — display-only; no state written.
