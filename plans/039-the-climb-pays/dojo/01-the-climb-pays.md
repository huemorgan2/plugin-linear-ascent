# Dojo 039-01 — altitude means something

## Preconditions

- Production `/health` serves the shipped game version, `db: true`.
- A fresh isolated browser context (`/me` → null first). UA header on raw
  probes.
- A test account leveled to floor 6 access (use the seeded dev path or an
  existing probe account whose secret stays off the transcript), and a
  second low-level account parked on floor 3.

## Scenario

1. On floor 3's gate town: list the action options. Screenshot.
2. On floor 6's gate town: list the action options. Screenshot.
3. Floor 6, normal hunt ×10 (heal as needed): record each opponent's
   name, archetype/specimen tags, and the pay line. Note energy spent.
4. Floor 6, deep hunt ×6: record the same, plus the opener's
   leave-the-lit-paths line. Note energy per fight (must be 2).
5. Floor 1, normal hunt ×5 with the low-level account: record pay lines.
6. Deliberately fight (not run from) every savage/alpha draw met in
   step 4.

## Expected behavior

- Floor 3 offers `[ HUNT ]` only; floor 6 offers both `[ HUNT — ⚡1 ]`
  and `[ HUNT DEEP — ⚡2 ]` (labels show prices).
- Floor-6 normal hunts: mostly non-prey draws; every pay visibly above
  the floor-1 pay lines from step 5 (no floor-1-money kills).
- Deep hunts: no runts, no prey; openers carry the deep line and the
  archetype/specimen tags; fights feel faster/harder (opponent lands
  more and closes quicker), not longer.
- At least one step-6 fight forces a real retreat-or-die decision; dying
  is possible and, if it happens, is handled by the normal death flow.
- Energy ledger: step 3 spends 10 ⚡, step 4 spends 12 ⚡.

## Fail conditions

- Deep option on floor ≤ 3, or missing on 4+.
- A deep hunt draws a feeble/runt opponent.
- A deep opponent with visibly inflated HP (fight running long instead
  of hard).
- Any floor-6 kill paying at or below a floor-1 median kill.
- Deep hunt deducting 1 ⚡, or refusing with a wrong message at 1 ⚡ left.
- Console errors; scene-card art regressions.

## Verify

- DB (or ledger view): energy ledger entries `wilds` vs `wilds deep`
  match the counts; gold deltas match the pay lines.
- Sim tables from phase 3 committed alongside; spot-check one floor-6
  observed pay against the sim's p10–p90 band.
