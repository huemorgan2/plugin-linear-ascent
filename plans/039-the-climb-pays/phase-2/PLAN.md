# 039 phase 2 — the deep hunt (⚡2, floor 4+)

## Goal

From floor 4, the gate town offers `[ HUNT DEEP — ⚡2 ]` beside
`[ HUNT — ⚡1 ]`: an informed opt-in to the dangerous end of the roster —
opponents harder in ATK and SPEED, **never** in HP — paying a clear
per-energy premium. Measured as: option absent on floor 3 and present on
floor 4; costs exactly 2 ⚡; deep-hunt fights never draw feeble prey or
runts; primed openers say so; per-⚡ EV 1.25–1.4× the normal hunt
(phase-3 owns the final number).

## Steps

1. `economy.py`:
   - `COST_WILDS_DEEP = 2`, `DEEP_HUNT_MIN_FLOOR = 4`.
   - Prime modifier constants: `DEEP_ATK_MULT = 1.3`,
     `DEEP_SPEED_BONUS = 2` (on the 1–10 scale, stacking with alpha's
     +1), `DEEP_REWARD_MULT = 2.25` (gold and XP; ≈ 1.1×/⚡ before the
     specimen shift pushes it further). **HP unchanged by design** —
     the fight gets scarier, not longer.
   - `DEEP_SPECIMENS`: runt 0, common 45, tough 35, alpha 20.
2. `engine/combat.py`:
   - `hunt_table(p, floor, deep=False)`: when deep — drop feeble-bite
     creatures entirely, skip the rubber band (the whole point is the
     player chose this), keep content weights otherwise.
   - `start_encounter(..., deep=False)`: apply prime ATK/speed, use
     `DEEP_SPECIMENS`, multiply the reward path by `DEEP_REWARD_MULT`,
     and mark `p["encounter"]["deep"] = True`.
   - Opener copy (mercy-vocabulary aware, coordinate with 038): prime
     fights open with a line in the house voice, e.g. *"You leave the
     lit paths. What finds you out here was never hunted thin."* plus
     the existing archetype/specimen tags — the read stays on the card
     before commitment.
3. `engine/core.py`: new option id `hunt_deep` in the gate-town options
   for floors ≥ `DEEP_HUNT_MIN_FLOOR`; spends `COST_WILDS_DEEP` (same
   refusal copy as hunt when short); ledger note `"wilds deep"`.
4. Render: option label shows the price (`[ HUNT DEEP — ⚡2 ]`), and the
   fight card keeps showing the archetype/specimen tags (already does).
5. Tests `tests/test_039_climb_pays.py`: option gating by floor, energy
   spend of 2, no feeble/runt draws in 500 seeded deep draws, ATK/speed
   raised while HP equals the non-deep stat line, reward multiplier
   applied, rubber band bypassed.

## Verification

- Full plugin suite green.
- Seeded playthrough script (tools or test): a level-appropriate sheet on
  floor 5 runs 50 deep hunts — observed death rate in the 5–20% band
  (coarse; phase 3 tightens), zero prey draws, average pay/⚡ above the
  normal hunt's.

## Rollback

`git revert` the phase commit. The new option id disappears with it; no
persisted state references it (the `deep` flag lives only inside a live
encounter dict).

## Execution status

**Done** — commit `1a36a1e` (2026-08-08). `hunt_deep` option at floor
4+ towns (⚡2, "harder, richer"), deep prime in `start_encounter`:
ATK ×1.2, speed +1, HP untouched — scarier, not longer. Deep table
drops prey species and feeble/frail specimens. Refusal short of 2⚡
returns the shard note and spends nothing. Verified: phase unit tests
pass; production walkthrough 2026-08-08 observed 2⚡ per deep hunt on
all 9 draws, the lit-paths opener, no prey/runts in the deep, and the
1⚡ refusal with energy intact
(`dojo/results/039-the-climb-pays-2026-08-08/`). Rollback: revert
`1a36a1e`.
