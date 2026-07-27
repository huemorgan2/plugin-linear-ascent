# Phase 002 — Speed & the chase: execution summary

Shipped as **0.19.0** (plugin published, worldd vendor synced + deployed).
Branch `017-combat-depth`, merged to `main`.

## What landed

- **Two-state range model.** Every fight opens `at_range`. Monster hits
  are halved at range; the monster rolls `p_close` at the end of each
  at-range round. Close quarters is full contact.
- **Chase curves in `economy.py`** (§2.4 of the master plan):
  `p_close = clamp(0.25 + 0.15·(mspd−pspd))`, `p_open`, `p_flee`, and
  `dodge% = min(12, round(7·log2(1+adv)))`. Speed scale slow 3 / normal
  5 / fast 7, alpha +1, player base 5 + shoe hook (`SHOE_SPEED` catalog
  fills in 004).
- **New options.** Melee at range gets **Close in** (replaces Attack;
  always crosses, eats one half-power hit). Anyone in close quarters
  gets **Open distance** (speed roll; failure = free half hit). Bare
  `attack` from a melee player at range aliases to `close_in` so old
  habits and the sidekick keep working.
- **Damage shape.** Bow ×0.6 in close quarters; magic full at both
  ranges; melee untouched. Flee replaced the flat 0.60 with `p_flee`.
- **Dodge** rolls before every incoming hit (physical and magic), from
  speed advantage only, capped 12% — armor stays the defense by
  construction.
- **Prose.** Range line in every fight scene ("◇ at range — it hasn't
  reached you yet" / "◇ close quarters — it is on top of you"),
  crossing/closing/dodge lines, tooltips for the two new options.
- Content audit: staircase holds — first `fast` on floor 5
  (downs_courser), `bulwark+slow` on 6, second fast on 10. No edits.

## Verification

- 247/247 tests. New `test_017_speed_chase.py` (28 tests): formula
  bounds, every range-machine branch, 10k-roll rate checks (close /
  flee / dodge within ±5% of formula), kite sims (archer beats the slow
  bulwark from range ≥85%; fast monster forces close by round ~2),
  warrior floor-1 regression (≤ +1.3 rounds — the crossing round).
- Smoothness gate remodeled per class: melee pays one crossing round,
  archers kite (flat multiplier), sorcerers stand and cast. Ranged vs
  fast reclassified as an intended hard counter (matchup gate owns it).
- Dojo (browser, local Luna + worldd, qa007): all five scenarios pass —
  warrior sees **Close in** at range and crosses for a −4 half hit;
  archer kited the floor-6 bull-boar for 23 rounds without it ever
  closing (and one "slip the blow" dodge landed); the floor-5 courser
  closed by round 4 and bow damage visibly dropped 15→1-4 while its
  hits jumped to −10; flee worked; the shard, asked mid-fight, re-synced
  and gave correct chase advice naming the courser's speed.

## Learnings (applied to future phase plans)

1. **The bow-at-close penalty is felt, not read.** In the dojo the
   damage collapse (15 → 1-4) reads as "something broke" — nothing on
   screen says ×0.6. 003's info card must show the range modifier line.
2. **DB doc fields are `clazz` and `gear.weapon`** — a swap that writes
   `class`/`weapon` silently does nothing and the scene keeps the old
   class moves. Recorded in the dojo doc; future phases reuse it.
3. **Range-line detection in scripted dojo loops must re-read after a
   settle delay** — innerText mid-render truncates and a `close
   quarters` check can miss. Poll twice before trusting a miss.
4. **Old tests want close quarters.** Any test that hunts then swings
   must pin `encounter["range"] = "close"` or route through Close in.
   New-phase tests should use a helper, not hand-rolled setups.
5. **Agent grounding held** — the 001-retro fix (agent re-syncs and
   names the current enemy) worked unprompted in scenario E.
