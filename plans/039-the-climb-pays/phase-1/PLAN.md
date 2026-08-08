# 039 phase 1 — the floor shapes the draw

## Goal

On floors 4+, the hunt's draw distribution visibly hardens with altitude:
prey and runt shares fall, lethal draws keep real weight, and the reward
ceiling rises — measured as: floor-6 normal-hunt EV(gold/⚡) ≥ 2.5× floor
1, and floor-6 10th-percentile kill pay > floor-1 median kill pay.
Content yamls stay untouched and numberless.

## Steps

All in `plugin_linear_ascent/economy.py` unless noted; opening-bid
numbers, sim-final in phase 3.

1. **Prey fade** — new `prey_weight_mult(floor) -> float`: 1.0 through
   floor 3, then −0.15/floor to a floor of 0.25 (floor 4 → 0.85, floor 8+
   → 0.25). Applied in `combat.hunt_table` to creatures whose bite word
   is `feeble`. The moths and voles still exist (lore, scans, deep-floor
   flavor) — the tower just sends fewer of them at altitude.
2. **Runt fade** — `specimen_table(floor)` replaces direct use of
   `SPECIMENS` weights in `start_encounter`: runt weight 25 through floor
   3, then −3/floor to a floor of 8 (floor 8+: runt 8, common 55, tough
   26, alpha 11 — reweighted to keep gold-expectation ≈ 1.0; assert in
   sim like 008 did).
3. **Rubber-band ladder** — `rubber_band_cut(floor)`: 0.20 floors 1–3,
   0.35 floors 4–6, 0.50 floors 7+. Replaces the flat `RUBBER_BAND_CUT`
   read in `hunt_table`.
4. **Reward-cap ladder** — `reward_mult_cap(floor)`: 6.0 floors 1–3,
   then +0.5/floor from 4 (floor 10 → 9.5). Must stay under
   `warden_gold(floor) / gold_per_kill(floor)` — assert it in the sim so
   one lucky draw still never outpays a Warden.
5. Thread `floor` through `kill_reward_mult(traits)` →
   `kill_reward_mult(floor, traits)`; update call sites
   (`engine/combat.py` reward paths).
6. Tests: extend `tests/test_025_the_real_climb.py` (or add
   `tests/test_039_climb_pays.py`) — table shapes at floors 1/3/4/6/8,
   prey fade applied only to feeble, runt fade reweighting sums to 100,
   cap ladder monotone and warden-bounded.

## Verification

- `uv run --project ../luna python -m pytest tests -q` green.
- Quick sim spot-check (phase-3 harness, coarse run): floor-6 EV/⚡ ≥
  2× floor 1 already with opening bids (final ≥ 2.5× owned by phase 3).

## Rollback

`git revert` the phase commit — pure-function knobs, no state or content
changes.

## Execution status

_(appended after execution)_
