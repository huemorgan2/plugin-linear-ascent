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
