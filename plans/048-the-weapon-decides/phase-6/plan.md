# Phase 6 — the balance bake

Goal: numbers hold the law. Anchors in N3/N8 are the starting
guess; the tests are the law — tune until green.

## Tests first (red)

1. T3 remaining axes in test_smoothness.py: ranks 0→10 on floors
   {1,5,10,25,50} — kill speed strictly improves, no step >20%;
   weapon rungs 1→10 at fixed rank — same caps.
2. T4 rewrite (test_022_002_retune + bake gates): level≈floor ±1
   at slope 3.0 with on-schedule one-path training; rank-10 ≈
   level 10 ±15% XP; tri-path trails ≥3 levels at equal kills
   mid-tower and never bricks; coin mult exact at floors
   1/5/10/11; floor-1→10 sim affords bow+staff+ranks 2/2/2
   without farming; era/warden/cap laws re-anchored.
3. T5 `test_048_progression.py`: intended-first-ten-floors sim
   (buy bow ~3, 2nd slot, staff ~5, train 2/2/2, no wall);
   specialist blade→10 by ~level 10 + invitation; wrong-weapon
   lesson (bow vs armoured loses/runs, text names staff/steel).
4. Un-skip the bounty-label case from ph 5.

## Code (green)

- `XP_PER_KILL_SLOPE` 2.4 → 3.0; `early_coin_mult` + young-tower
  bounty label in gold_per_kill + kill card.
- Bake loop: run T3/T4/T5, adjust ONLY anchors (TRAIN_XP_ANCHOR,
  TRAIN_GOLD_ANCHOR, TYPE_ATK/HP weights, BASIC_WEAPON_PRICE,
  bounty slope) — never the caps. Record every anchor move and
  its reason in the execution summary (bake ledger).

## Green =

T3+T4+T5 full, suite.
Commit: `048 phase 6: the bake — slope 3.0, young-tower bounty,
anchors settled`.

## Learnings applied (from phase 1)

- Python banker's rounding (`round(4.5)==4`): compute every
  expected value in the bake with `round()`, never by hand.
- Suite-green gate excludes the baseline-red
  test_034 shield_wall case (pre-existing on main).
