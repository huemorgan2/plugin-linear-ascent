# 075 — Speed is not a shield: the chase never fully stops

Status: planned (roy, 2026-08-24). Not started. Not deployed.

## Problem (roy, 2026-08-24 — measured)

A player who out-speeds a monster and fights at range with a **bow or
magic** is effectively invulnerable. Speed was meant to be a *garnish*
(pre-plan §3.3: "stacking speed can never become a hidden invulnerability
hack; armor and resistance stay the main defense axes"). In practice, a
speed lead alone makes a ranged fighter untouchable.

### Evidence — code
- At range, a shot draws **no answer at all**. `combat.py` `attack`
  path, `unreachable = _range_state(p) == "at_range"`:
  `engine/combat.py:2589-2598` — *"the shot flies, nothing flies back —
  the gap is armor."*
- Per player action the monster gets **exactly one** attempt to close
  **one** length, and that attempt floors at 5%:
  `economy.p_close = clamp(0.25 + 0.15·(mspd−pspd), 0.05, 0.95)`
  (`economy.py:616-618`); applied once per round in
  `_advance_chase` (`engine/combat.py:382-406`), which **deals no
  damage** — it only moves the monster.
- A caught player re-opens almost for free: `p_open` caps at 0.90
  (`economy.py:621-623`), and `open_distance` is refused only when the
  monster is *equal or faster* (`engine/combat.py:2267-2273`).
- Magic cannot even give ground (no gap ladder — `create_distance`
  requires `_damage_type == "ranged"`, `engine/combat.py:2294`), so a
  sorcerer simply stands, casts full damage at both ranges, and is
  chased one 5%-length at a time.

### Evidence — sim (400 fights, tanky 4000-HP husk, floor 6, max HP 193)
`plans/075-speed-is-not-a-shield/sim075.py` (to be committed with the
plan). HP lost to KILL a 4000-HP monster:

| speed lead | archer HP lost | sorcerer HP lost |
|---|---|---|
| +1 | 78.8 | 30.1 |
| +2 | 51.2 | 12.0 |
| +3 | 32.1 | 10.2 |
| +5 | **7.7** | **10.2** |

At a +5 lead an archer soaks under 8 HP of 193 to grind down a
4000-HP monster. A sorcerer is near-free at every lead. This is the hack.

### What "the other game" shipped, and why it isn't enough
A prior build added the 036/048 **gap ladder** — `create_distance`
("give ground on purpose") with a parting-blow roll
`p_gap_hit = clamp(0.65 − 0.12·(pspd−mspd), 0.05, 0.95)`
(`economy.py:591-595`). It has two faults:
1. It only fires when the *archer chooses* to give ground; a stander
   (magic, or an archer who just shoots) is never touched.
2. It is linear and floors fast, so it is simultaneously *too punishing*
   near parity (65% at equal speed) and *irrelevant* at a big lead.
It was never written up as a plan and never got 031 §7's "ranged
honesty" rule. This plan replaces it with one coherent model.

## Root cause
The monster gets a single, damage-free close-attempt per player round,
and range is treated as absolute armor. There is no *persistent pursuit*:
nothing lets a determined monster take several steps — and eventually a
swing — inside one player action. So a speed lead, which should only
**reduce the rate** at which the monster catches you, instead **removes
it entirely**.

## Design — the monster gives chase (persistent, decaying, never zero)

The fix, per roy's spec: after a player's **ranged or magic** action the
monster takes a **pursuit phase** of one or more turns. Each turn it
advances a length, and when it reaches you it strikes. A bigger speed
lead means fewer of those turns land — but the chance **never reaches
0**. Enough turns over a long fight will eventually connect.

### 1. How many pursuit turns (the aggression) — weapon decides
The monster always gets its base pursuit turn. It may get more:

| Player weapon | +2nd turn | +3rd turn |
|---|---|---|
| **Bow** | 90% | 10% (only if the 2nd happened) |
| **Magic** | 50% | — |
| Melee | unchanged — this plan does not touch melee |

Bow invites the harder chase (you are actively running); a caster stands,
so the chase is shorter — but still real. Numbers are the starting point;
phase 3 sim-fits them.

**Flyers get zero extra turns**, whatever the player's weapon — see §6.
The extra-turn rule is only for grounded monsters chasing a runner.

### 2. Whether a pursuit turn lands (the decay) — speed decides
One curve, replacing both `p_close` (for pursuit) and `p_gap_hit`:

```
adv = player_speed − monster_speed
p_pursue(adv) =
    CAP                                    if adv <= 0   # as fast / faster: it keeps up
    FLOOR + (BASE − FLOOR) · DECAY**adv    if adv  > 0   # decays, never to 0
```
Starting constants (sim-fitted in phase 3):
`CAP = 0.90, BASE = 0.55, FLOOR = 0.05, DECAY = 0.60`.

| adv | p_pursue | feel |
|---|---|---|
| ≤0 | 0.90 | equal/faster monster keeps up — ranged is a hard counter (intended, 002) |
| +1 | 0.35 | a small lead helps, does not save you |
| +2 | 0.23 | |
| +3 | 0.16 | |
| +5 | 0.09 | big lead — mostly clean |
| +10 | 0.053 | **never zero** — a 10× lead still trickles |

Multiplicative decay (not linear) is the point: it approaches the FLOOR
asymptotically, so "twice as fast" is much safer but "infinitely fast"
is still not immune.

### 3. What a pursuit turn does
- **gap > 0:** advance one length (`gap -= 1`) on a `p_pursue` success.
  Reaching `gap == 0` puts the monster in reach *this round*.
- **gap == 0 (in reach):** the turn is a **strike** — a real
  `_monster_hit`, halved (it is striking mid-chase, not set and braced).
- **Cap:** at most **one** full pursuit strike per player round; any
  further reached-turns in the same round are halved again (so a triple
  pursuit cannot chain-kill). Cap and halving are sim-tuned against the
  death-rate gate.
- Dodge still rolls on each incoming strike (armor/resist stay primary;
  speed already spoke through `p_pursue`, so pursuit strikes pass
  `no_dodge=False` — the small capped dodge is the last word).

### 4. Ranged honesty, revised (supersedes 031 §7 for this case)
031 §7 said an at-range shot draws no answer. That stays *within the
shot itself* — nothing flies back the instant you loose. The change:
the monster's **pursuit phase** may close the gap and reach you **within
the same round**, so a shot is no longer a guaranteed free hit. Prose
must make this legible: name each length closed and each blow landed, so
a caught player understands *the chase caught up*, not "range broke."

### 5. Retire `p_gap_hit`
`create_distance` (give ground) becomes just another ranged action that
triggers the pursuit phase. The separate `p_gap_hit` parting-blow is
removed; one speed curve (`p_pursue`) governs all monster catch-up. The
gap ladder's **damage** payoff (`bow_gap_mult` 1.0/1.25/1.5) is
untouched — giving ground still buys draw-power; it just no longer has
its own bespoke hit roll.

### 6. Flyers — the one exemption (the bow's whole purpose)
A sword does **0** damage to a flying monster (`melee vs fly` is the one
legal zero in the game — `combat.py:1202`, `_verdict` "cannot reach it").
So against a flyer the player is *forced* onto a bow or magic. Piling the
new extra hits onto the only weapons that can touch it would punish the
forced answer. So flyers are carved out:

1. **No extra pursuit turns.** A flyer gets only its single normal action
   per round — never the bow's 2nd/3rd or magic's 2nd. The extra-turn
   rule is for grounded things chasing a runner; a flyer is not that.
2. **You cannot back away from a flyer.** `open_distance` and
   `create_distance` are refused against a flyer — it is in the air and
   simply follows. The option is hidden (or refused with a plain reason).
3. **Flyers stay fast.** Keep flying monsters at `SPEED_FAST` or higher so
   they close the opening gap in about a round and you cannot out-position
   them. Their threat is *denying the kite and forcing close range*, not
   extra hits.

**Why not "just make them fast"?** Because speed alone would make flyers
*worse*, not exempt: in the general model the extra hits LAND based on
speed, so a fast flyer with no special rule would connect on every extra
turn — the most brutal case, the opposite of the intent. The exemption
must be an explicit flying flag, independent of the speed number.

**Bow does full power vs a flyer — this preserves the triangle, it does
NOT buff the bow.** The game's damage triangle (`economy.TYPE_MULT`)
already makes each weapon the single answer to one enemy type:

| Enemy type | Sword | Bow | Magic |
|---|---|---|---|
| **Flying** | 0.0 | **1.0** | 0.6 |
| Armoured | 0.5 | 0.15 | **1.0** |
| Magic-resist | **1.0** | 0.5 | 0.15 |
| Plain | 1.0 | 1.0 | 1.0 |

So the bow (1.0) is the designed flyer answer and magic (0.6) is the
weaker one. But the bow also carries a separate ×0.5 "cramped up close"
penalty, which stacks: bow up close vs a flyer = 1.0 × 0.5 = **0.5**,
below magic's flat **0.6**. Because a flyer closes fast and cannot be
kited, most of the fight is up close — so *keeping* the penalty would
make **magic the better flyer answer**, inverting the triangle. Dropping
the close penalty **against flyers only** (an airborne target is above
you; an arrow is still the right tool) restores the intent: bow 1.0,
magic 0.6, sword 0. This is balance, not a bow buff.

Net matchup after this — a clean rock-paper-scissors where each weapon
owns one type:
- **Flying → the bow's kingdom** (bow 1.0, magic 0.6, sword 0).
- **Armoured → magic's kingdom** (magic 1.0, sword 0.5, bow 0.15).
- **Magic-resist → the sword's kingdom** (sword 1.0, bow 0.5, magic 0.15).

Magic is not weakened overall — it owns armoured enemies, where the bow
is nearly useless. It simply is not *also* the flyer answer. The flyer is
dangerous because it gets on you fast and you cannot run — not because it
hits three times.

## Player-facing copy — plain English (audit)

Rule for this whole feature: **plain, straightforward English. No game
jargon.** Banned in any player-facing string here: *bowwork, give ground,
the gap is armor, parting blow, speed tells, kite, lengths* (say "paces"),
*legs* (as in "faster legs"), *toll, rake, at range* (say "far away" /
"up close"). Full sentences. A stranger reads it once and understands.

Every surface this feature touches, with its plain replacement:

### Tooltips (`engine/tips.py`)
- **Run in** (`close_in`): "Run in to reach it with your weapon. This
  always works and uses your turn. As you close, the monster gets one hit
  on you at half strength. Only melee weapons need this — bows and magic
  already hit from far away."
- **Back away** (`open_distance`): "Back away to put space between you and
  the monster. It keeps chasing, so this buys room, not safety — the
  faster you are than it, the more often you get away clean. Uses your
  turn. You cannot back away from a flying monster; it follows you."
- **Step back for a better shot** (`create_distance`): "Step back one pace
  to give your bow more room. A bow hits harder from farther away — a
  little more at 2 paces, more at 3. As you move, the monster may catch
  you and land a hit; being faster than it makes that less likely, but
  never impossible. Uses your turn."
- **Run** (`run`/flee): "Try to leave the fight. The faster you are than
  the monster, the better your chance to get away. If it catches you, you
  take a hit and the fight goes on."

### In-fight lines (`engine/combat.py`)
- Shot from far away (replaces "the shot flies, nothing flies back — the
  gap is armor" and "It has no answer at this range"): "Your shot hits for
  −N. It is still coming for you."
- A pursuit step closes (replaces the `_advance_chase` lines "eats a
  length of the open ground" / "comes on across open ground"): "It rushes
  in — N paces away now."
- The gap fully closes (replaces "closes the gap — it is on you now"): "It
  reaches you — you are in its range now."
- A pursuit hit lands (replaces the retired parting-blow "it collects the
  toll — rakes you as you pull away"): "It catches up and hits you as you
  move: −N HP."
- You stay ahead (replaces "You break clean — your legs beat its lunge"):
  "You stay ahead of it — nothing lands."
- Dodge (replaces "you slip the blow — speed tells"): "You dodge the hit —
  you were too fast for it."
- Flyer refusal for back-away / step-back (NEW): "It is in the air — there
  is no way to put ground between you. You will have to fight it here."

### Enemy info card `[i]` (`render.py`)
- Speed help (`_TIP_SPD`, ~line 901): "SPD — how fast you move (your build
  plus your boots). Higher speed helps you dodge, get away, and stay ahead
  when something chases you."
- Chase line, you faster (replaces the misleading "You hold the range and
  you choose the exit — kite it.", ~line 1415): "You are faster than it,
  so you will usually stay ahead — but it keeps trying to close, so it
  will catch you now and then."
- Chase line, it faster (~1413): "It is faster than you. It will close the
  distance, and you cannot count on getting away."
- Chase line, even (~1417): "You are about the same speed — neither of you
  gets away clean."
- Flying tag help (`_TIP_KIND["fly"]`, ~2131): "Flying — a sword cannot
  reach it; use a bow or magic. You also cannot back away from it, because
  it follows you through the air."

Each string above is the source of truth; phase 2 wires exactly these
words. A dojo reader who is not a designer must understand every line.

## Fix — phases

1. **The curve** — `economy.p_pursue`, `economy.pursuit_turns(weapon)`;
   retire `p_gap_hit`. Unit tests: decay monotonic, floors at FLOOR>0,
   never 0, `adv<=0 → CAP`, turn-count distributions. `phase-1/PLAN.md`.
2. **Wire the chase + flyers + copy** — `combat.py`: after a ranged/magic
   action run the pursuit phase (N turns, each `p_pursue`, strike on
   reach, capped); fold `create_distance` into it. **Flyers:** no extra
   pursuit turns; refuse back-away / step-back with the plain reason; bow
   does full power vs a flyer at any range (recommended default). Wire the
   exact plain-English strings from the copy audit above into `tips.py`,
   `combat.py`, and `render.py` (info card). Update the 002/031/036/048
   tests to the revised honesty model. `phase-2/PLAN.md`.
3. **Content, sim, rebalance, ship** — audit floors 1–10 so every flying
   monster is `SPEED_FAST`+; commit `sim075.py`; fit the constants to the
   gates below; full pytest; dojo browser walk; version bump; vendor sync.
   Not deployed unless roy says so. `phase-3/PLAN.md`.

## Verification (whole plan)

### Sim gates (`sim075.py`, 10k rolls)
- **The hack is gone.** A ranged/magic player at +5 speed lead loses a
  *meaningful, survivable* share of HP over a long kill (target: no
  longer <10 HP of 193; land it in a tuned band, e.g. 25–60 HP) — and
  the damage-taken curve is **monotonically decreasing** in speed lead.
- **Never zero.** At +10 lead the monster still lands ≥1 strike across a
  long fight in the large majority of runs (p_pursue floor holds).
- **Direction preserved.** More speed = safer, always (no inversion).
- **Ground monster that is fast still hard-counters ranged.** `adv ≤ 0`
  → it runs a kiter down (002 intent intact).
- **Melee unchanged.** Warrior floor-1 rounds-to-kill and win-rate
  within noise of today (regression gate from `test_017_speed_chase`).
- **Survivable, not brutal.** Per-floor death-rate for an *at-level*
  ranged player within the 039/046 target band after tuning.

### Flyer gates
- **No extra hits.** A flyer never lands more than one strike per player
  round regardless of the player's weapon (bow or magic) — the extra
  pursuit turns are skipped entirely for flyers.
- **No back-away.** `open_distance` / `create_distance` are refused vs a
  flyer at any speed lead; the option is absent from the menu.
- **Bow stays useful.** A bow's damage vs a flyer is full at both ranges
  (recommended default), i.e. no ×0.5 up-close penalty against flyers.
- **Still a threat.** A fast flyer closes to your range within ~1 round
  and the fight is then close quarters (it cannot be kited).

### Unit
- `p_pursue`: bounds, monotonic decay, `>0` floor, `adv<=0` cap.
- `pursuit_turns`: bow ~E[2.0] (0.9+0.1 tail), magic ~E[1.5], melee 0,
  **flyer 0 extra** (guaranteed, whatever the weapon).
- Pursuit phase: at most one full strike/round; a fully-closed gap sets
  `range=close`; dodge still applies; death checked between strikes.
- Flyer: back-away/step-back options are not offered and are refused if
  submitted as raw ids; bow damage vs flyer equal at both ranges.

### Copy / plain-English
- Every string in the copy audit appears verbatim in the code, and none
  of the banned jargon words appear in any player-facing string this
  feature touches (grep gate in the test).

### Dojo (`luna/dojo/tests/speed-is-not-a-shield/`)
Seed a floor-6 archer with +boots (adv +3) vs a slow **ground** husk:
- shoot it — the card shows the monster **closing paces and occasionally
  reaching and hitting** you; you are not free.
- stand as a sorcerer — the monster still closes sometimes and lands the
  odd hit; casting is strong but not immune.
Then seed a **flying** monster:
- the "back away" / "step back" option is **gone**; trying it is refused
  in plain words ("it is in the air…").
- it reaches you fast and the fight is up close; it lands **one** hit per
  round, never a double; your bow still hits full.
- vs melee: the sword reads "cannot reach it" (unchanged).
All prose reads as a chase catching up, never "range broke"; a
non-designer understands every tooltip and line; no numbers leak into the
fiction.

## Companion problem — the triangle must have teeth (measured)

roy's design law: at-level, the **right weapon must win and the wrong
weapon must lose (switch or flee)**; a **+2 level cushion** may brute-
force the "half" matchups; a glance should stay wrong, not just slow.

Measured today (300 fights each, floor-6 monsters, win% [avg rounds]):

```
matchup                       L4(-2)      L6(at)      L8(+2)
sword vs armoured   (x0.5 )  100% [ 2.2]  100% [ 3.2]  100% [ 4.8]
bow   vs armoured   (x0.15)   92% [18.4]   93% [17.3]   90% [19.1]
magic vs armoured   (x1   )  100% [16.9]  100% [15.1]  100% [12.9]
sword vs fly        (x0   )  100% [ 4.9]  100% [ 7.7]  100% [13.6]
bow   vs fly        (x1   )  100% [ 5.7]  100% [ 6.3]  100% [ 3.7]
magic vs fly        (x0.6 )  100% [ 5.5]  100% [ 5.0]  100% [ 3.5]
```

**Finding: the triangle changes fight LENGTH, not the outcome.** Every
weapon wins ≥90% vs every type at-level and even 2 levels under. Two
causes: (1) the `max(1, …)` damage floor (`economy.py:885`) turns every
"zero"/"glance" cell into ≥1 per hit — a sword grinds a flyer to death
despite the ×0; (2) early floors are tuned soft, so 18 slow rounds do not
kill you. So "right weapon or flee" is not enforced anywhere today.

**This is a separate mechanic from the speed hack** and should be its own
plan — **076 "the triangle decides"** — covering:
- Relax the `max(1)` floor for glance/zero cells (a ×0 is truly 0; a
  ×0.15 rounds to 0 on small hits) so a wrong-weapon fight *stalls*.
- Tie win/lose to the triangle: at-level a wrong-weapon fight runs long
  enough that monster damage kills first → switch or flee. `+2` levels
  (×1.69 damage) pulls the "half" cells back to a win; the ×0.15 glance
  needs ~7 levels (i.e. effectively never — a glance is the wrong tool).

Gate carried into this plan's dojo: a wrong-weapon fight vs an at-level
armoured/flyer must be a visible loss/flee, not a slow win — even though
the *code* change lands in 076.

## Rollback
One commit per phase; `git revert` in reverse. The model is gated behind
the new `economy` functions and one new `combat` pursuit helper —
reverting `economy.py` + `combat.py` restores today's behavior exactly.
No player-doc/state schema change: the encounter already carries `gap`
and `range`; no new persisted field. Old clients render the extra
chase/strike lines as ordinary scene body text.

## Operational notes
- Lands in **both** places: plugin engine AND `worldd/vendor` (run
  `worldd/tools/vendor_game.sh`, bump the submodule pointer).
- No deploy to Render unless roy says so.

## Open decisions (defaults chosen — say the word to change)
- **Faster-player floor:** never 0 (roy's call). Default FLOOR 5%.
- **Strikes per round from pursuit:** capped at 1 full + halved extras
  (default) vs uncapped (brutal) vs strictly 1 (softer).
- **Bow vs magic aggression:** 90%/10% vs 50% per roy. Kept as the
  starting split; phase 3 may nudge within ±10 pts to hit the gates.
- **`p_gap_hit`:** retired and unified into `p_pursue` (default) vs kept
  alongside (two curves — rejected as the current inconsistency).
- **Melee:** untouched (default) — this is a ranged/magic rebalance.
- **031 §7:** revised, not deleted — the shot itself still draws no
  instant counter; the pursuit is what reaches you.
- **Flyers exempt from extra hits:** yes (roy's call). A flyer gets one
  action per round only; the bow/magic exist to answer flyers.
- **No back-away from a flyer:** yes (roy's call) — the option is hidden
  vs flyers.
- **Flyers made fast, not "just fast":** flying is an explicit flag that
  turns off the extra hits AND the back-away option; speed is set high on
  top. Relying on the speed number alone is rejected (it would make a
  fast flyer the most brutal case, not an exempt one).
- **Bow full power vs a flyer: DECIDED — yes (roy, balance).** Drops the
  bow's ×0.5 close penalty against flyers only. This preserves the damage
  triangle (bow 1.0 / magic 0.6 / sword 0 vs flyers); keeping the penalty
  would push bow to 0.5 < magic 0.6 and make magic the better flyer
  answer, which is *not* wanted. Magic keeps its own kingdom (armoured),
  so it is neither a superpower nor a disadvantage.
