# 077 — The triangle decides: right weapon or flee

Status: planned (roy, 2026-08-24). Not started. Not deployed.
**Hard dependency: plan 075 (speed is not a shield) must land first** —
without it, a kiter takes a long fight for free and none of this bites.

## Problem (roy, 2026-08-24 — measured)

The weapon-vs-type triangle is supposed to be the whole point of combat:
bring the right weapon or the fight goes badly. Today it only changes how
**long** a fight takes, never whether you **win**. Measured, floor-6
monsters, win% [avg rounds], 300 fights each (from `075/PLAN.md`):

```
matchup                       L4(-2)      L6(at)      L8(+2)
sword vs armoured   (x0.5 )  100% [ 2.2]  100% [ 3.2]  100% [ 4.8]
bow   vs armoured   (x0.15)   92% [18.4]   93% [17.3]   90% [19.1]
magic vs armoured   (x1   )  100% [16.9]  100% [15.1]  100% [12.9]
sword vs fly        (x0   )  100% [ 4.9]  100% [ 7.7]  100% [13.6]
bow   vs fly        (x1   )  100% [ 5.7]  100% [ 6.3]  100% [ 3.7]
magic vs fly        (x0.6 )  100% [ 5.5]  100% [ 5.0]  100% [ 3.5]
```

Every weapon wins ≥90% vs every type, even 2 levels under. You can bow an
armoured boar to death (18 rounds) and never be in danger.

## Root cause (two, and they interact with speed)
1. **The `max(1, …)` damage floor** (`economy.py:885`,
   `return max(1, round(max(1, base) * mult))`) turns every "zero" and
   "glance" cell into **≥1 damage per hit**. A sword grinds a flyer
   despite ×0; a bow grinds plate despite ×0.15. Wrong weapon is slow,
   never impossible.
2. **A long fight is not a dangerous fight.** The extra rounds only hurt
   if the monster lands hits during them. Two escapes today:
   - **Kiting** (the 075 speed hack): a faster ranged/magic player takes
     the long fight for free. **075 fixes this for FAST monsters.**
   - **The two hard types are both SLOW** (`TYPE_SPEED`: armoured 3,
     magic_resist 3). A ranged player out-speeds them and kites safely
     even after 075. Length there costs time, not blood.

roy's design law: **at-level, the right weapon wins and the wrong weapon
loses — you must switch or flee.** A +2 level cushion may brute-force the
"half" matchups. A glance stays wrong, not merely slow.

### Speed/ATK facts that shape each case (verified `economy.py:674-675`)
- **fly = speed 7, ATK 0.6** — already FASTER than a base player (5) and
  hits soft. The fast case is partly self-enforcing: a flyer out-speeds
  you, so melee-vs-fly you can't even kite. This is exactly the 075
  flyer design ("just make them fast, no second-hit privilege") — fly=7
  already delivers it. Bring a bow.
- **armoured / magic_resist = speed 3, ATK 1.4** — slow but hit HARD.
  They're kiteable (the hole), but once they close (post-075 pursuit)
  each hit is heavy. So for slow tanks, Lever A (glance can't grind) is
  the primary lever, and post-075 pursuit + 1.4 ATK is the secondary bite
  when they do reach you.
- The triangle is a rotation: **fly→bow, armoured→magic, magic_resist→
  blade**, plain→anything. The two ×0.15 glances are **bow vs armoured**
  and **magic vs magic_resist**; the ×0 wall is **blade vs fly**.

## Design — length must convert to a real cost

Keep fight-length as the readable signal (it is good and legible), but
make length **convert** to one of two real costs, chosen by the monster's
speed — because you cannot make a slow tank kill you, and you cannot make
a fast flyer stand still:

### Lever A — a glance cannot grind (fixes the slow tanks)
Relax the `max(1)` floor for the **zero and glance** cells so they do
(near) nothing:
- **Zero cell** (sword vs fly, ×0): truly **0** — a blade cannot touch a
  flyer, full stop. You cannot win; you flee or you brought the wrong kit.
- **Glance cell** (×0.15): rounds to **0 on ordinary hits** (it only
  chips on a big roll, if at all). Against a slow tank you now *stall* —
  the fight makes no progress, so you must switch or flee.
- **Half and full cells** (0.5 / 0.6 / 1.0): unchanged — still chip ≥1,
  still winnable.

Result for slow wrong-matchups: the fight doesn't kill you, it simply
**won't end** — the game's way of saying "wrong tool." Flee is the out.

### Lever B — a long fight against something that CAN reach you is lethal
For matchups where the monster reaches you (fast types, or once a slow
type closes), crank the per-round cost so an at-level wrong-weapon fight
actually **drains you toward death**, not a leisurely 18-round win. Tie
it to the triangle: if your damage-per-round is a fraction of the
reference, the fight runs long enough that the monster's damage exceeds
your pool → death unless you switch or flee. This is a tuning of monster
ATK / fight-length budget, sim-fitted (below), NOT a new mechanic.

### How the ±level intuition falls out (PILLAR = 1.3/level)
- **At-level, wrong weapon → lose** (die to a fast type; stall out vs a
  slow type). Right weapon → win.
- **+2 levels = ×1.69 damage** → shoves the "half" cells (0.5/0.6) back to
  a comfortable win: brute-force is fine when you out-level the content.
- **The ×0.15 glance needs ~7 levels** to brute-force — i.e. effectively
  never. A glance is the wrong tool, not a slow tool. (Open decision.)

## What else we need to fix (the audit roy asked for)
1. **Speed first (075).** Lever B is inert for ranged until the kite is
   closed. 077 is sequenced AFTER 075 and its sims assume 075 is in.
2. **Slow-tank kiteability.** Both hard types are speed 3. Verify that
   after 075 a booted ranged player cannot fully cheese a slow tank; if
   pursuit pressure is too weak at big speed leads, Lever A (glance = no
   progress) is the backstop — you can kite safely but you cannot kill,
   so you still must switch.
3. **In-fight mitigation audit.** Trollblood tonic (full heal), golden
   apple (×2-HP overshield), shield wall — confirm each is a ONE-SHOT
   clutch from the single charm slot, not a way to outlast a lethal-
   length fight indefinitely. They are the intended "save me once," not a
   loophole. No change expected; a test pins that they don't reset.
4. **Flee must be a real out** (it is the intended escape from a wrong
   matchup). Ties to 075's `p_flee`; verify a wrong-weapon player can
   reliably disengage a slow tank and sometimes a fast one.
5. **Monster ATK / kill-time tuning** so at-level "reachable" wrong
   fights are lethal without making RIGHT-weapon fights brutal, and
   without breaking the 039/046 death-rate bands for correct play.

## Fix — phases
1. **Glance/zero teeth** — relax the `max(1)` floor per cell in
   `economy.py`; unit tests for each triangle cell (0 stays 0; 0.15
   rounds to 0 on ordinary hits; 0.5/0.6/1.0 unchanged). `phase-1`.
2. **Lethal length** — tune the reachable-fight cost so at-level wrong =
   death/flee; audit mitigations (item 3); wire the "you're not hurting
   it — try another weapon or flee" steering line when a stall is
   detected. `phase-2`.
3. **Sim, content check, ship** — `sim077.py`: the win/lose grid must
   flip; full pytest; dojo; version bump; vendor sync. Not deployed unless
   roy says so. `phase-3`.

## Verification (whole plan) — the grid must flip
Re-run the grid above (post-075). Targets at-level (L=floor):
- **Right weapon:** win ≥90%.
- **Wrong weapon, reachable (fast type):** win ≤25% — you die or flee.
- **Wrong weapon, slow tank (glance):** kill-rate ~0% within a sane round
  cap — the fight stalls; flee succeeds.
- **+2 levels:** the "half" cells (0.5/0.6) return to ≥90% wins.
- **Glance (×0.15) at +2:** still a loss/stall (needs ~7 levels).
- **Right-weapon fights stay in the 039/046 death-rate band** (we did not
  make correct play brutal).
- **Mitigations** (tonic/apple/wall) each fire once and do not let a
  wrong-weapon player outlast a lethal fight.

### Dojo (`luna/dojo/tests/the-triangle-decides/`)
At-level floor-6 seeds:
- Bow vs the armoured boar: you visibly **fail to hurt it** ("your arrows
  glance off the plate") and must flee or swap — no slow win.
- Sword vs the flyer: "your blade cannot reach it" — 0 progress, flee.
- Right weapon each: a clean win.
- Over-level by 2 with a "half" matchup: a slow but real win (brute
  force allowed).
- Every steering line is plain English (see 075 copy law): "Your arrows
  glance off its plate — try a blade or magic, or run."

## Rollback
One commit per phase; `git revert` in reverse. Lever A is a localized
change to the damage floor; Lever B is tuning constants. No state/schema
change. Reverting `economy.py` restores today's grind-anything behavior.

## Operational notes
- Sequenced AFTER 075. Lands in plugin engine AND `worldd/vendor`
  (`vendor_game.sh` + submodule pointer). No deploy unless roy says so.

## Open decisions (defaults chosen)
- **Glance (×0.15) brute-forceable by leveling?** Default **no** — a
  glance is the wrong tool; ~7 levels is effectively never. Flip if you
  want everything winnable with enough grinding.
- **Zero cell truly 0?** Default **yes** (sword literally cannot hit a
  flyer). Flip to "chips 1" if you want no absolute walls.
- **Lever B strength:** tuned to "at-level wrong-and-reachable = death by
  the time you'd have won with the right weapon ×~3 rounds." Sim-fitted.
- **Stall steering line:** shown after N no-progress rounds (default 2)
  so a confused player is told to switch/flee, not left grinding.
