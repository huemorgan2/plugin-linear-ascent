# Phase 3 — the School + mastery + carry

Goal: the training sink exists in town; carry slots exist on the
doc and the sheet. Classes still exist (die next phase).

## Tests first (red)

T1 school/mastery/carry cases in test_048_the_weapon_decides.py:

1. School room reachable from every gate town (town menu shows
   SCHOOL); scene lists three paths with rank, bar, and next-cost
   line (exact XP+gold from formulas, gold uses CURRENT frontier).
2. Train action: deducts XP and gold, bumps rank by 1; refusals:
   not enough XP, not enough gold, rank 10 ("nothing left to
   teach"); each refusal names the number.
3. "What improves" line present for next rank (miss% X→Y, worst
   swing A%→B%).
4. Rank 10: bar gold-marked; MASTERY row lists the path's study at
   948 XP; buying it sets flag + effect hook; invitation card fires
   once; other paths' ranks 1-5 cost 80% XP (assert discounted
   values, e.g. blade rank 1 for a bow-master: 16 XP).
5. Carry: `slots` field defaults `1`; School CARRY row; buy 2nd
   slot at level 1 (60 XP + 30 gold) → slots 2; 3rd slot refused
   below level 8 with text `needs level 8 — you: N`, purchasable
   at 8+ for 900 XP + round(200*pillar(front)) gold.
6. Holding: `p["held"]` list of weapon ids (len ≤ slots); default:
   the equipped weapon migrates to held[0]; promote-from-bag
   action on sheet moves weapon into slot (bump choice when full);
   refused mid-fight with reason. Sheet payload carries TRAINED
   block (3 paths + ranks) and HOLDING row; bag weapon tooltip of
   an untrained path warns (miss 25%, weak swings).

## Code (green)

- `state.py`: `slots`, `held` on the doc (+migration: equipped →
  held[0]); sheet payload TRAINED/HOLDING.
- `core.py`: School scene (town room next to armory), train flow,
  refusal lines, mastery purchase, invitation card + discount
  bookkeeping (`p["mastery"]`, `p["flags"]["invited_<path>"]`).
- `economy.py`: `MASTERY_XP = round(train_xp(10)*1.5) == 948`;
  `CARRY2_*`, `CARRY3_*`, `carry3_gold`, discount rule.
- `sheet.py`/`profile.py`/`pane.py`: TRAINED block, HOLDING row,
  bag tooltip promote action (mid-fight refusal).
- Mastery EFFECTS (riposte/long draw/focus) land with the triangle
  flip in phase 5 — this phase only sells and records them (tests
  assert the flag; effect tests marked for ph 5). KEEP the studies'
  effect asserts in a `pytest.mark.phase5` skip so red is honest.

## Green =

new cases + full suite.
Commit: `048 phase 3: the School — train, mastery, carry, holding`.
