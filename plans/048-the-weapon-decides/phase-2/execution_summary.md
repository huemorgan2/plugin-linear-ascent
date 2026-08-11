# Phase 2 — execution summary (2026-08-11)

Status: DONE, green (1000 passed; only the pre-existing baseline-red
test_034 shield_wall remains).

## What landed

- `economy.py`: `PATH_OF_LINE`, `TRAIN_MISS_PCT`, `TRAIN_ROLL_FLOOR`,
  `train_xp`, `train_gold` (+anchors).
- `state.py`: doc v7 — `training` on `new_player` (all-0) and the v7
  migration: legacy doc → class path rank 6 + one-time School letter
  (pending event, playing docs only).
- `core.py`: class pick trains its path to 6 (transitional, dies ph 4).
- `combat.py`: `_train_path`/`_train_rank`; the swing floor rides the
  rank (`TRAIN_ROLL_FLOOR`); a rank miss eats the round and the
  monster answers, text names the rank and the School. OFF-CLASS
  hands stay wholly on the legacy penalty set (miss 25% + half
  damage + atk//2 floor) — the two systems NEVER stack; both gates
  carry "transitional until phase 4" comments.
- 9 new tests (formulas, costs, PATH_OF_LINE, creation grant,
  migration card once, swing floor per rank, miss prob per rank,
  miss-eats-round text, rank-10 never rolls a miss die).

## THE finding — rank 6 is not old-power parity

The plan claimed "rank 6 ≈ old feel". False once the miss counts:
mean swing = (floor+1)/2 × (1−miss):
  rank 6 = 0.77 × 0.90 = 0.693   (old = 0.75, −7.6%)
  rank 7 = 0.79 × 0.92 = 0.727
  rank 8 = 0.81 × 0.95 = 0.770
The 022 win-band laws caught it immediately (warden band 0.76 at
rank 0 ref; 0.883 at rank 8 — over the top; matchup farmable law
fails at rank 7 on floor 10). The legacy power sits BETWEEN rungs.

Transitional resolution (all documented in-code):
- `reference_player(clazz, floor, rank=8)` — matchup gate runs at 8
  (just above legacy), warden band at 7 (just below). Phase 6 MUST
  re-anchor both bands at the rank-6 reference climber.
- Payout-probing deterministic tests (test_025 tally, test_039 deep
  premium) pin rank 10 — a master never misses; the probe is the
  ledger, not the hand.
- test_017_characters version pin 6 → 7.

**Open question for roy (added to plan):** migrated veterans at rank
6 land ~7.6% under their old mean plus a 10% miss until they train
two ranks. Options: migrate at 7 (feel-neutral, one step of
headroom) or keep 6 and let the phase-6 bake soften monsters. Phase
6 proceeds with 6 + re-anchor unless roy says otherwise.

## Corrections to the master plan

- `train_xp(7)` = 370, not 371 (hand-rounding slip); one path 0→10 =
  2,854 XP; all three = 8,562. Plan and S2 mock fixed.

## Learnings → next phases

- Phase 4: deleting the off-class system must also delete BOTH
  transitional gates in combat.py (`_off_class` reads in
  `_player_hit` and the attack flow) — grep `transitional until
  phase 4`.
- Phase 6: bake targets updated — reference climber rank 6,
  re-anchor warden 60–85 band and matchup farmable/danger gates;
  `reference_player` default rank drops to 6 then.
- Adding any die roll shifts every downstream deterministic sim —
  tests probing payouts/tallies must pin rank 10 (miss die never
  rolled keeps the rng stream stable for the swing).
