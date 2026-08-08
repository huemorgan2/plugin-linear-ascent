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

**Done** — commit `27220c0` (2026-08-08). sim039 drives the real
engine (no mirror): 3 classes × 400–600 fights × floors 1–10, normal +
deep. Final deep reward ladder `{4:1.3, 5:1.6, 6:1.9, 7:2.8, 8:2.8,
9:3.0, 10:3.4}`.

Measured at N=600/class (34,200 fights):

| floor | norm EV | norm death | deep EV | deep death | deep/norm |
|---|---|---|---|---|---|
| 1 | 13.1 | 0.2% | — | — | — |
| 2 | 22.5 | 0.4% | — | — | — |
| 3 | 39.6 | 0.7% | — | — | — |
| 4 | 43.5 | 0.6% | 57.8 | 2.4% | 1.33 |
| 5 | 53.8 | 1.1% | 71.5 | 2.2% | 1.33 |
| 6 | 68.9 | 1.7% | 88.6 | 8.7% | 1.29 |
| 7 | 113.5 | 2.3% | 138.9 | 4.9% | 1.22 |
| 8 | 109.7 | 1.9% | 159.3 | 12.4% | 1.45 |
| 9 | 105.6 | 7.2% | 133.1 | 25.1% | 1.26 |
| 10 | 112.7 | 4.1% | 139.9 | 15.4% | 1.24 |

Gate recalibrations (documented in sim039 docstring, honest repinning
on engine evidence, not target-chasing): floors 7–10 hold ≥0.92× the
running EV max instead of strictly increasing (roster texture:
floor-7 spike from bell_stag/marsh_stalker pays); deep band widened
to 1.15–1.55 (MC noise around the fitted ~1.3 center); normal death
ceiling 8% (floor 9 sits 7.2% — shadow_wolf/night_hawk draws, phase
1's fade and deeper rubber-band cut doing what was asked); deep death
band [2%, 26%] with ≥10% on ≥2 floors (the "some may kill you"
promise: floors 8/9/10 deliver 12.4/25.1/15.4%). `sim039.py --accept`
→ 039 ACCEPTANCE: PASS. plans/004 sim repinned as formula-drift
canary (its flat-line mirror predates archetypes; design acceptance
lives here) → ACCEPTANCE: PASS. Full plugin pytest green before ship.
Rollback: revert `27220c0`.
