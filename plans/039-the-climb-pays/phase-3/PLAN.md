# 039 phase 3 — calibration: the sim owns the numbers

## Goal

Every opening-bid number from phases 1–2 replaced by a sim-derived value,
and the 004 acceptance gate green again with targets that describe the
game as designed — so future economy changes have a working tripwire.

## Steps

1. Extend the 017 fight sim (`plans/004-difficulty-review/sim.py` or the
   017 harness it wraps) to emit, per floor 1–10, per class, at-level
   loadout:
   - normal hunt: EV(gold/⚡), EV(xp/⚡), death rate, pay percentiles
     (p10/p50/p90);
   - deep hunt (floors 4+): same table.
2. Tune, in order: `DEEP_REWARD_MULT` → prey/runt fade slopes → cap
   ladder, until all targets hold:
   - normal-hunt EV/⚡ strictly increasing in floor; floor 6 ≥ 2.5×
     floor 1;
   - floor-6 p10 kill pay > floor-1 p50 kill pay;
   - deep-hunt EV/⚡ = 1.25–1.4× same-floor normal hunt;
   - deep-hunt death rate (at-level, kitted) 8–15%; normal-hunt death
     rate < 2% on floors 1–3 and < 6% anywhere;
   - specimen gold expectation within a few % of 1.0 at every floor
     (the 008 invariant, now per-floor);
   - `reward_mult_cap(floor) · gold_per_kill(floor) < warden_gold(floor)`
     for all floors ≤ 100.
3. Recalibrate the 004 acceptance gate: its warden baselines predate the
   post-030 retunes (it fails on untouched HEAD today — verified
   2026-08-02). Re-derive its targets from current HEAD + this plan's
   values, then `python3 plans/004-difficulty-review/sim.py --accept`
   must PASS and become a required check in phase 4's ship steps.
4. Freeze the final numbers into economy.py with the sim run's summary
   table pasted into this file's execution status.

## Verification

- `sim.py --accept` PASS on the branch (and FAIL if any 039 knob is
  reverted in isolation — the gate actually guards the new shape).
- Full plugin suite green.

## Rollback

Numbers-only commit; `git revert` restores the opening bids. The gate
recalibration reverts with it (the gate returns to its known-stale state,
no worse than today).

## Execution status

_(appended after execution)_
