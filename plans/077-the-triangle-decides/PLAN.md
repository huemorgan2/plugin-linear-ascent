# 077 — The triangle decides: right weapon or flee

Status: planned (roy, 2026-08-24); **revised after 075 shipped**
(0.100.0) with what its ~10k-fight simulation taught us. Not deployed.
**Hard dependency: plan 075 — LANDED.** Its pursuit model is what makes
this plan's "wrong weapon costs you blood" real.

## Problem (roy, 2026-08-24 — measured)

The weapon-vs-type triangle is supposed to be the whole point of combat:
bring the right weapon or the fight goes badly. Pre-075 it only changed
how **long** a fight takes, never whether you **win**. Measured, floor-6
monsters, win% [avg rounds], 300 fights each (pre-075 engine):

```
matchup                       L4(-2)      L6(at)      L8(+2)
sword vs armoured   (x0.5 )  100% [ 2.2]  100% [ 3.2]  100% [ 4.8]
bow   vs armoured   (x0.15)   92% [18.4]   93% [17.3]   90% [19.1]
magic vs armoured   (x1   )  100% [16.9]  100% [15.1]  100% [12.9]
sword vs fly        (x0   )  100% [ 4.9]  100% [ 7.7]  100% [13.6]
bow   vs fly        (x1   )  100% [ 5.7]  100% [ 6.3]  100% [ 3.7]
magic vs fly        (x0.6 )  100% [ 5.5]  100% [ 5.0]  100% [ 3.5]
```

Every weapon won ≥90% vs every type, even 2 levels under. **After 075**
the picture improved but the core hole remains: the floor-6 at-level
archer still WINS 97% against a roster that includes its ×0.15 glance
(sim075 survival grid) — a glance is slow, never wrong.

roy's design law: **at-level, the right weapon wins and the wrong weapon
loses — you must switch or flee.** A +2 level cushion may brute-force
the "half" (×0.5/×0.6) matchups. A glance stays wrong, not merely slow
(~7 levels to brute-force = effectively never).

## Root cause (revised on 075 evidence)

The first draft of this plan blamed the `max(1, …)` damage floor in
`economy.typed_damage_048`. The floor is real but marginal: it only
binds on early floors. The sharper truth from the numbers — **×0.15 of
a kitted player's damage still kills an at-level monster in ~17
rounds.** At floor 6 a glance hit is ~9 damage, not 1. The glance is
not a glance; it is a slow full hit. No damage-floor tweak fixes that;
the cell itself is too big.

What 075 already fixed (measured, sim075):
- A slow tank can no longer be kited for free: an at-level (+2 speed)
  archer bleeds ~253 HP per 4000-HP grind — the extra rounds now COST
  blood, which is exactly the "make it damaging" lever this plan's
  first draft thought it had to build. **It exists; 077 inherits it.**
- The step-back treadmill is dead; the sim policy for 077 is "shoot in
  place, step out only when caught".
- Flyers cannot be kited and the bow answers them at full power.

## Design — one lever, one line

### Lever A (the only mechanical change): the glance goes to ×0.015
`TYPE_MULT` glance cells `0.15 → 0.015` (**sim-fitted**: the plan
opened at 0.04, but the staff ignores DEF so a sorcerer still ground
out 20–47% of glance wins; 0.02 left 7% at +2 levels; 0.015 stalls
every band), and glance cells lose the `max(1)` chip floor (a tiny hit
may round to 0). Zero cell (blade-vs-fly) unchanged — already a true 0.

| Enemy type | Sword | Bow | Magic |
|---|---|---|---|
| Flying | 0.0 | **1.0** | 0.6 |
| Armoured | 0.5 | **0.015** | 1.0 |
| Magic-resist | 1.0 | 0.5 | **0.015** |
| Plain | 1.0 | 1.0 | 1.0 |

What the glance does across levels (base ≈ raw − DEF/2, PILLAR 1.3/level):
- **At-level:** ~2 dmg/hit vs a ~700-HP monster → 300+ rounds → the
  fight will not end. Meanwhile 075's pursuit bleeds you every round —
  the stubborn die, the sane flee or switch. Wrong = LOSS, in blood or
  in retreat, never a quiet win.
- **+2 levels (×1.69):** ~4/hit → still a stall. Brute force does NOT
  clear a glance (roy's call).
- **+7 levels (×6.3):** ~15/hit → ~50 rounds — technically possible,
  practically never. Matches "a glance needs ~7 levels".
- **Half cells (0.5/0.6) untouched** → +2 levels still brute-forces
  them (×1.69 turns a slow win into a comfortable one). The at-edge
  player (−1/−2 levels) finds them dicey via PILLAR, as intended.
- **The archer's honest out vs plate stays:** a piercing arrow treats
  armoured as plain (existing 006 rule) — the counter-tool is a
  consumable you chose to carry, not a grind.

### Lever B (verified, not built): the reachable wrong-fight is lethal
There is no "reachable glance" case to crank — both glance cells sit on
slow (speed 3) tanks, and the fast wrong-matchup (blade-vs-fly) is
already a true 0 where fleeing is the only end. 075's pursuit is the
damage engine for the stall. So Lever B is a **sim gate, not a code
change**: at-level wrong-weapon fights must end in death or flee, not
wins. (075 left deep hunts on floors 9–10 ~3 pts over the old 26%
death cap; re-check here — if the glance change shifts hunt rosters'
danger the numbers move together.)

### The steering line (the one new string)
A stalling player must be TOLD, in plain English, after 2 wasted
rounds, on the fight card:
- bow vs armoured: "Your arrows barely mark its plate. Use a blade or
  magic — or run."
- magic vs magic-resist: "Your spells slide off it. Use a blade or a
  bow — or run."
- blade vs fly (existing refusal stays, tightened): "Your blade cannot
  reach it. Use a bow or magic — or run."

### Copy audit (plain English, 075 jargon law applies)
- `render._TIP_KIND["armoured"]`: "Armoured — heavy plate. A blade cuts
  at half strength, arrows all but bounce off, magic goes through in
  full."
- `render._TIP_KIND["magic_resist"]`: "Magic resistance — spells barely
  scratch it. A blade cuts in full, arrows at half strength."
- Any surface printing the ×0.15 number follows the new value.

## Fix — phases
1. **The glance** — `economy.py`: `TYPE_MULT` 0.15→0.04 (both cells),
   glance cells exempt from the `max(1)` floor; unit tests per cell
   (zero stays 0; glance rounds to 0 on small hits and stays ~nothing
   on kitted hits; half/full byte-identical). `phase-1`.
2. **The steering line + copy** — stall counter on the encounter,
   type-appropriate line after 2 glance/zero attack rounds; `_TIP_KIND`
   rewrite. `phase-2`.
3. **Sim, tests, ship** — `sim077.py` win/lose grid (policy from 075:
   shoot in place, step out when caught; each class vs each type,
   levels −2/at/+2, ≥300 fights/cell → thousands total); full pytest;
   version bump; vendor sync. Not deployed unless roy says so.
   `phase-3`.

## Verification — the grid must flip
At-level (L = floor), 80-round cap:
- **Right weapon:** win ≥90%.
- **Glance matchups (bow-vs-armoured, magic-vs-magic_resist):**
  kill-rate ≈0% within the cap; the fight stalls (timeout) or kills the
  player — a visible LOSS either way. Flee (not modeled) is the out.
- **Zero (blade-vs-fly):** kill-rate 0% (already true), player bleeds.
- **+2 levels:** half cells (0.5/0.6) ≥90% win; glance cells still ~0%.
- **Half cells at-level:** winnable but visibly slower/bloodier than
  the right weapon.
- **Right-weapon death rates:** within noise of the post-075 sim075
  survival grid (this plan must not make correct play worse).
- **Steering line:** appears by round 2 of a glance/zero fight, reads
  plain, and never appears in a right-weapon fight.

### Dojo (after landing, combined with 075's walkthrough)
- Bow an armoured monster at-level: arrows visibly do ~nothing, the
  steering line shows, the monster's chase bleeds you, fleeing works.
- Sword a flyer: cannot reach it, steering line, flee.
- Right weapon each type: clean wins. Over-level +2 with a half cell:
  slow but real win.

## Rollback
One commit; `git revert` restores ×0.15 and the chip floor exactly. No
state/schema change (the stall counter lives on the transient
encounter dict).

## Operational notes
- Lands in plugin engine AND `worldd/vendor` + submodule pointer.
- No deploy unless roy says so.

## Open decisions (defaults chosen)
- **Glance value 0.015** (was 0.15; opened at 0.04, sim-fitted down —
  see Lever A). A kitted hit still shows a 1–2 scratch so the player
  sees SOMETHING happened — it reads as futility, not a bug.
- **Glance brute-forceable by leveling: effectively no** (~7 levels).
- **Zero cell stays absolute** (blade cannot touch a flyer, ever).
- **No monster-ATK crank** — 075's pursuit is the damage engine;
  verified by gate instead of built twice.
- **Steering after 2 wasted rounds** (not 1 — a single try is
  exploration, two is a pattern).
