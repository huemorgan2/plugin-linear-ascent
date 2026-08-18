# 066 — aether is scarce

## Problem (roy, 2026-08-18, floor 6 deep, after 065)
"I still see gold and XP on the same scale — six kills, all about the
same XP vs gold; the steepest was half XP to gold, still generous. XP
should be much lower and harder to gain." Card: Guano vole, 24 XP /
28 gold.

## Root cause
065 only put a FLOOR under gold (gold ≥ 1.25 × xp at the mean, card
gold ≥ xp + 1). The XP slope itself is 048's 3.0 (`xp_per_kill = 3.0 ·
bar^1.5 / wedge`), which pays 36 XP vs 37 base gold on floor 6 — a 1:1
scale — and levels a floor-6 hunter every ~10 kills (cap in 16 days at
30 kills/day, against the era model's SOLO_BAND_DAYS = 30). The card
clamp then lifts gold to xp + 1 on the low-gold rolls, so the two
numbers sit side by side.

## Fix (one plugin release)
- `XP_PER_KILL_SLOPE` 3.0 → 1.5. Kill XP halves everywhere: f6 36→18,
  f9 59→30, f12 81→41. Kills per level at level == floor: f6 10→20,
  f9 11→22, f29 24→48. One-path climber caps in 31 days (was 16) —
  inside the 14–42 law and on the era model's 30-day solo band; blade
  rank 10 still lands at body level 9. hone_xp / sleep_xp_cost ride
  xp_per_kill, so they stay priced in kills; School ranks (absolute
  XP) now cost twice the kills — the sink bites.
- `KILL_GOLD_OVER_XP` 1.25 → 2.0: the mean paycheck is at least twice
  the kill's XP (bites only f9–11: 57→60, 68→70, 75→75).
- Card law: `xp = min(xp, max(1, gold // 2))` replaces `gold = max(gold,
  xp + 1)` — XP is clamped DOWN to half the coin after every multiplier
  and jitter; coin is never inflated to meet it.

## Verification
- test_065: mean gold ≥ 2 × xp on floors 1–30; the floor-6 card never
  writes xp > gold / 2 (100 rolls, all specimens); runt < common <
  alpha XP holds.
- test_economy expectations: xp(5) 29→14, gold(5) 36→31 (the pillar ×
  bounty is back on top), xp(95) 70→35, gold(11) 92→75, gold(14) 146.
- test_048_bake pace laws (cap 14–42 days, blade 10 at level 9–12,
  tri-path lag) and test_022_002 days-to-cap pass unchanged.
- Full plugin suite; worldd suite untouched.

## Rollback
`git revert` the plugin commit. Banked XP stays; the next kill pays the
new scale.

## Execution status
- Done 2026-08-18. Plugin 00cfe89 (game 0.89.0), root 18fefcd.
- XP_PER_KILL_SLOPE 3.0→1.5: xp/kill f1 3→2, f5 29→14, f6 36→18,
  f9 59→30, f12 81→41. Kills per level at level==floor f6 10→20,
  f29 24→48. Pace sim: one-path cap 15.9→31.1 days (508→995 kills),
  blade 10 still at body level 9.
- KILL_GOLD_OVER_XP 1.25→2.0: mean gold f9 57→60, f11 75; f5 back to
  the pillar × bounty (36→31). Card law xp = min(xp, gold // 2).
- Tests: test_065 6/6 (rewritten to the 2× law); plugin suite 1226
  pass, same 6 pre-existing failures as 065 (verified on HEAD via
  stash). worldd untouched (vendor only).
- Local 8777 restarted on 0.89.0. Not deployed, not published.
