# Phase 3 — School: the charm pouch (level 9)

## Goal
At level ≥ 9 a player buys the charm slot at the School once; below 9
the row is visible, locked, and explains why.

## Steps
- `economy.py`: `CHARM_SLOT_LEVEL=9`, `CHARM_SLOT_XP=400`,
  `CHARM_SLOT_GOLD_ANCHOR=250`, `charm_slot_gold(frontier)`.
- `core._school_scene`: row `buy_charm_slot` after `buy_carry3`;
  `locked=True` + "🔒 level 9" hint under 9; hidden once owned.
- `core._school_charm` (mirror `_school_carry`): refuse if owned /
  level short / XP / gold; on success `p["charm_slot"]=True`, ledger
  `note="charm pouch"`, "+ POUCH — one charm or potion rides at your
  belt now." line.
- tips: `buy_charm_slot`.

## Verification
- pytest: level 8 → locked row + refusal text; level 9, short XP →
  refusal; success → flag, gold/xp deltas, ledger row; second buy
  refused.

## Rollback
`git revert`; a doc with `charm_slot=True` on the phase-2 engine still
has the slot (flag already exists there).

## Execution status
Executed 2026-08-18. `_school_scene`: POUCH line always present (owned /
locked "opens at level 9" / priced `CHARM_SLOT_XP` XP + `charm_slot_gold`);
`buy_charm_slot` row locked under 9, hidden once owned. `_school_charm`
mirrors `_school_carry` (owned / level / XP / fee refusals, ledger note
"charm pouch", "+ POUCH" line). tips: `buy_charm_slot`. Tests: 3 new in
test_069 (locked row + refusal at 8; XP and fee refusals at 9; success
deltas + ledger + row hidden + second buy refused). Suite: 1276 passed,
6 pre-existing failures.
