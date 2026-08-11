# Phase 5 — monsters switch to types + total visibility

Goal: the triangle goes LIVE; every card shows every number; every
defeat teaches. Mastery study effects land here too.

## Tests first (red)

1. `tests/test_048_visible.py` (T2 in full): params+sign on every
   hunt row and fight card; verdict names actual best answer +
   rank; locked gate texts; per-slot labels with predicted damage;
   TRAINED block on profile; miss/shallow lines name the rank;
   defeat-cause table (armoured-vs-bow, fly-vs-blade-only,
   rank≤1, plain overreach) — each names one lever; School "what
   improves"; bounty label (red until ph 6 for the label — mark
   that one case phase-6-skip).
2. `test_smoothness.py` floor axis (T3): walk floors 1–100 per
   path at rank 6, reference gear; caps ADJACENT 0.40 / TREND
   0.15; every floor: each path has ≥1 monster answered at ×1.0.
3. T1 mastery-effect cases un-skipped: riposte returns 25% mean
   swing on shallow monster hit; long draw crits gap-3 top-10%
   roll ×1.5; focus lifts staff .6/.5 answers to .75.

## Code (green)

- `combat.py`: damage path → `typed_damage_048` by monster type
  (old typed_damage dies); blade-vs-fly = 0 with run-truth text;
  mastery effects; predicted-damage labels on attack options;
  verdict scene; defeat-cause sentence picker (table by cause).
- `creature_stats`: TYPE_SPEED/ATK/HP applied; `TYPE_GOLD` in
  gold path; TIER_MULT/PROFILE_GOLD/FLYING_GOLD_MULT die;
  `type_from_traits` bridges legacy YAML until ph 7.
- `render/pane/scene`: full stat line + sign everywhere; "no
  sign — every weapon bites full" for plain.

## Green =

T2 (minus bounty label), T3 floor axis, suite.
Commit: `048 phase 5: the triangle lives — typed monsters, total
visibility, defeats that teach`.
