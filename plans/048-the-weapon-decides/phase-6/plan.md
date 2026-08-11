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

## Learnings applied (from phase 2)

- Rank 6 is NOT legacy parity (0.693 vs 0.75 mean): the bake must
  re-anchor the warden 60–85 band and the matchup farmable/danger
  gates at a rank-6 reference climber; drop reference_player's
  transitional rank pins (8 matchup / 7 warden) to the default 6.
- Migration-at-6 vs 7 is an open roy question; bake assumes 6.

## Learnings applied (from phase 3)

- **Carry-3 collision**: training spends the level bar, capped at
  xp_need(level). CARRY3_XP=900 vs the level-8 bar (543) means the
  level-8 gate is a lie until ~level 12 (bar 998). Bake must pick:
  CARRY3_XP ≤ 543, or CARRY3_LEVEL = 12 (and fix the printed
  sentence + tests either way). Same math blesses the ranks:
  rank 10 (632 XP) first fits at level ~10, MASTERY (948) at 12 —
  keep those as designed anchors when re-baking xp_need or
  XP_PER_KILL_SLOPE.
- School gold prices ride pillar(frontier) — any PILLAR change
  moves train_gold/carry3_gold; the bake's expected values must be
  computed with round() from the constants, never hand-copied.

## Learnings applied (from phase 4)

- Bake sims start from the classless doc: Rusted Sword + blade 2,
  basics at flat 60 through `_basic_buy` (FORGE price stays 0 —
  price>0 is the wear/pawn/death key; never move basics through
  `_gear_purchase`).
- Any test that leans on a gate threshold trains the rank
  explicitly; the conftest kit's rank 6 opens the gap but NOT the
  ×draw (rank 8) — silent at-threshold behavior was phase 4's
  test_036 trap.

## Learnings applied (from phase 5)

- **Smoothness measurement contract**: the pace walk reads floor
  `monster_stats` × TYPE_ATK/TYPE_HP — never per-encounter
  `creature_stats` (archetype spread leaked 235% ghost-cliffs).
  Any T3 rank/rung axis must keep the same split; archetype spread
  belongs to the matchup gate.
- **Model both bow stances**: `_chase_adjusted` picks kite-vs-stand
  by `(taken, total)` — bake pace math that assumes the kite
  against fast prey explodes the cycle and fails falsely.
- **Triangle grades are settled law**: full ×1.0 gates ≥80%;
  halves ×0.5/×0.6 float free (priced slog); only glances ×0.15
  and the zero must wall (<30%) or drag (≥1.6×). Do not re-tighten
  halves when re-anchoring the matchup gates at rank 6.
- **Pool rule sits at ≥1** (schema lint + measured 008 gate) until
  the phase-7 retag — the bake must not "fix" a 1-farmable floor
  with anchors; that's roster work, not numbers.
- **Band-boundary checks use the dip-forgiving rolling-max
  baseline** (022/002): recovery from an easy floor is not a wall.
- **Pin rng in threshold tests**: any new bake test asserting on a
  single roll pins `rng_int`/`roll_ok` (test_034's date-flake).
