# Phase 8 — polish + hand playtest

Goal: the words teach everywhere; a hand-played climb confirms the
paper game is the felt game.

## Work

1. Teaching texts: School door line (S1), migration card wording,
   banner-hall mastery mention, strike/miss/defeat text final
   pass, tips rewritten to weapon voice.
2. Three-question audit (fun law): one monster of each sign at
   ranks 0/5/10 — can I lose / tell why / change it — answers
   written into the execution summary.
3. Hand playtest floors 1–12 dojo-style via engine driving:
   fresh climber; buy bow floor ~3; learn 2nd slot; meet all
   three signs; one deliberate wrong-weapon defeat (read the
   card); train to blade 4; log every card that confused.
4. Production checklist per release flow (no deploy without roy's
   word): version bump proposal, vendor, regen, CHANGELOG draft —
   PREPARED, not executed.

## Green =

full suite, playtest log clean of unexplained losses.
Commit: `048 phase 8: the words teach — polish + playtest log`.

## Learnings applied (from phase 1)

- Add polish item: baseline-red
  `test_034_shield_wear.py::test_shield_wall_pays_for_the_whole_blow`
  (pre-existing on main; 047 floor-1 softening) — pin the fight to
  floor 3 per the sibling test's 043.2 precedent, pending roy's nod.
