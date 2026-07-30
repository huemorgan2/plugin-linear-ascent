# 026 — A Gate Is Never Free

## The complaint

> "why did you remove the cost of energy on every boss attack it was
> great!!! now i can attack without limit"

> "i also liked in the past that you couldnt run when you wanted —
> sometimes it would follow you — so there was a price to pay for attaking
> the boss. it was great and never happened after — maybe just a chance it
> didnt happen but it was great."

Nothing had been removed. `COST_WARDEN_ATTEMPT = 3` is charged on `strike`
exactly as it was in 022/001, and the getaway has rolled on speed since
§2.4 (`p_flee`, 60% at even speed). Both readings are still correct,
because both mechanics were load-bearing on something that had quietly
stopped being true: **that the Warden can hurt you.**

## Why it happened (measured)

A keep fight has exactly two exits: you kill it, or it kills you. 3 ⚡ is
the price of the *fight*, and the pool is literally measured in those
fights — `strike_fight_damage`: *"fight until one round from death, then
withdraw"*, `warden_pool_fights(1) = 3.2`.

But nothing enforced the withdrawal, and the damage rule is
`max(⌈raw/4⌉, raw − DEF/2)`. Once a climber's DEF outgrew a floor, the
gate's bite collapsed onto the 1-point chip floor:

| kit at the floor-1 gate (ATK 15) | its blow lands for | rounds you survive | pool (426) falls in |
|---|---|---|---|
| level 1, T1 reference | 2–8 | 19 | 3.2 charges (as designed) |
| level 4, rung 1.3 | 2–4 | ~45 | 0.4 of one charge |
| level 6, rung 1.5 | 2–4 | ~46 | 0.15 of one charge |

So: unlimited swings per charge (the fight never ended), and a failed
escape that cost 1 HP (not a chase). 025 made it *feel* new only because
the wound became permanent, so one uninterrupted grind ended the gate
instead of the Warden healing it back overnight.

### The bug found next door, which was worse

`_report_shared_strike` measured a fight's damage as `hp_max − hp`, and
`social.warden_action` sets `hp_max` to the **body's full size** while
`hp` picks up the pool where the last blade left it. A climber walking
into a gate already cut to 200/426 was therefore credited with the other
**226 on his first swing**. Every wounded gate fell in one or two charges
to whoever turned up — including the ones the player was grinding.

## What was rejected first (both measured, both wrong)

The instinct is to make a Warden's blow heavier. Two versions were built
and thrown away:

1. **A per-round floor at the mean bite** (blow ≥ 7% of your pool). It
   sits at the *average* blow, so it deletes the entire lower half of the
   roll distribution: at-level floor-4 gate wins fell 88% → 73%.
2. **Halving the chip divisor for wardens** (`⌈raw/2⌉`). Scales with the
   Warden's ATK, which is enormous at depth — the coordination band fell
   from ~60% at-level wins to 11–26% on floors 21–29.

The damage table is load-bearing in both directions. **The exchange was
what had no bound.**

## The change

### 1. One charge buys one exchange

`economy.warden_exchange_rounds(F)` — the rounds an at-level climber
survives on that floor (19 at floor 1, 9 by floor 5). It is now the same
function `strike_fight_damage` counts with, so the fight a player is sold
and the unit the pool is priced in cannot drift.

The exchange also ends the moment you cut **one fight-unit**
(`pool_unit(F)`, 133 at floor 1) out of the body — the half the round
budget could not carry, because a level-10 blade deals three at-level
fights' worth inside a 19-round exchange and would still take a
3.2-fight gate in a single charge.

Either way the Warden's guard closes, it drives you back to the gate
town, the wound stays cut, and the ⚡ was the price of the exchange.
Personal/echo bouts (no pool, no world effect) are untouched.

What that buys, floor 1 (pool 426 = 3.2 units of 133):

| your level | charges to close it | rounds | HP paid | times left on the floor |
|---|---|---|---|---|
| 1 | 3 (9 ⚡) | 21 | 91 | 1 |
| 3 | 3 (9 ⚡) | 16 | 43 | 0 |
| 6 | 3 (9 ⚡) | 10 | 25 | 0 |
| 10 | 3 (9 ⚡) | 8 | 16 | 0 |

Out-levelling a gate now buys **efficiency** — fewer rounds, less blood,
less risk — and never the gate itself.

### 2. A gate never lets you walk

- `WARDEN_FLEE_MAX = 0.75`: speed decides the getaway everywhere in the
  tower, but against a Warden it only ever improves your odds to 3-in-4.
- `WARDEN_GRAB_SHARE = 0.06`: the blow that catches you turning lands its
  grip — at least 6% of your own body — instead of a 1-point chip.

### 3. The wound is measured from where you joined it

`e["hp_join"]` is stamped at join and `_cut_this_fight()` reads it.
`hp_max` still carries the body's size, so the war bar, the scan and the
"bites deep" prose are unchanged.

## What did NOT move

Deliberately, and asserted: `world_warden_hp(1) == 426`, `pool_unit(1) ==
133`, the 3–4-fights-per-gate law, the whole 022/002 win-rate band, the
monotone effort curve, and `WARDEN_POOL_TUNE == 3` — **no live pool needs
resizing**, so the walls standing in production stay exactly as deep as
the climbers left them.

## Why not 1 ⚡ per attack round (what the player literally asked for)

Priced it: the floor-1 gate takes ~57 rounds of an at-level climber, so
the gate would cost ~57 ⚡ against a 21 ⚡ bar — three days of energy for
the *first* gate, and worse for every floor above. It also punishes
exactly the wrong player, since the weakest climber needs the most
rounds. The bounded exchange delivers what he wanted (a charge no longer
buys an unlimited fight; there is a price for standing in front of a
boss) without making the first gate unreachable alone.

## Tests

`tests/test_026_the_gate_bites_back.py` — 24 gates: the keep fight always
ends; the charge equals the pool's own unit; driven-back is a third exit
that keeps the wound; ⚡ still charged once; nobody takes a gate in one
standing at levels 1/4/6/10/20; a gate costs ≥3 charges from anyone; local
bouts stay unbounded; a Warden catches a fleeing climber ≥4 times in 40;
the grab is real blood and scales with the body; the wilds keep the 95%
getaway; a strike reports only what this blade cut; the bar still shows
the body; and the 022/024 numbers are pinned.
