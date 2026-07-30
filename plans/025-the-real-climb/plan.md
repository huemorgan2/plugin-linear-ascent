# 025 — The Real Climb (floors 1–10)

## The complaint

> "this is way too easy — I have no problem that it'll be super steep and
> super hard… right now there is no way to win [the Warden]."
>
> "the progression of items to buy is boring — I worked 3 days to advance
> a level only to find that… I have no more things to buy at level 4."
>
> "all monsters now for me in level one are one shot to two shots — and
> they all give the same amount of coins and XP (or so I feel)."
>
> "at level 3 I wasn't afraid of any monster."

All four readings are correct, and each has a structural cause.

## Why the game is flat (measured, not guessed)

### 1. Every creature on a floor IS the same monster

`schema.Floor` computes ONE stat line per floor from `economy.monster_stats(F)`
and every encounter on that floor uses it (`combat.start_encounter`, the
`else` branch). Content may not author numbers at all — `_FORBIDDEN_NUMERIC_KEYS`
rejects `atk/def/hp/xp/gold`. Per-creature difference today comes only from:

- **defense traits** (`armor_*`, `resist_*`, `flying`, `bulwark`) — and
  `TRAIT_INTRO_FLOOR` bans armor before floor 2, resist before 3, flying
  before 4, fast before 5, bulwark/slow before 6. **Floor 1 is trait-free
  by lint.** All four floor-1 animals are one monster in four costumes.
- **the specimen roll** — HP ×0.55/1.0/1.4/2.0 and ATK ×1.0 except alpha
  ×1.2.

So the *only* stat that ever varies for a floor-1 player is HP, over a
2.0/0.55 = 3.6× window, on an 18 HP animal.

### 2. Nothing can hurt you

The monster damage rule is:

```
raw  = rng(atk/2 … atk)
chip = ceil(raw / 4)          # CHIP_DIVISOR — armor blunts, never nullifies
dmg  = max(chip, raw − DEF/2)
```

Floor 1 gives ATK 5. A level-1 player in the T1 kit has DEF 14, so
`raw − 7` is always negative and **every hit lands for the 1-point chip**.
A floor-1 monster needs ATK ≈ 12 before its bite beats the chip floor at
all, and ~20 before it hurts. Monster ATK is `3.3·F + 2` — it does not
reach 12 until floor 3, and by then the player's DEF has grown too. The
early game cannot deal damage **by construction**.

### 3. Every kill pays the same

`xp_per_kill(F) = 4·F` with ±25% jitter, and **nothing else touches XP** —
not specimen, not traits. Gold at least varies (specimen 0.45–2.3×,
profile 1.1–1.5×). The player's read — "same coins and XP" — is precisely
true for XP and nearly true for gold.

### 4. Levels 2, 4, 5, 7, 8, 9 and 10 sell nothing

Band-1 gear gates on rungs: whole rung T at `band_start(T)`, mid rung T.5
at `band_start(T)+5`. In levels 1–10 that is **three gate moments**:

| Level | What unlocks |
|---|---|
| 1 | T1 weapon (own line), Scrapwood Buckler, Padded Jerkin |
| 3 | Cobbled Boots; the Arcanum door (sorcerers get staff + focus) |
| 6 | The T1.5 mids: Iron Sword / Sinew-Backed Bow / Coalglass Staff, Banded Kite, Studded Jack |
| 11 | T2 whole tier |

Levels 2, 4, 5, 7, 8, 9, 10 add **zero** purchasable items for every
class. Three days of work for a level that sells nothing is exactly what
the player reported.

### 5. The Warden regenerates faster than a lone climber can return

Fixed once in 024 (solo band trickle → 0, silence window 30h), but the
player's ask goes further: **floors 1–10 must not heal at all.**

---

## The design rules this plan establishes

1. **A floor is a range of animals, not one animal.** Every floor offers
   prey you farm, peers you fight, and something that will kill you.
2. **Danger pays.** XP and gold both scale with the creature's real
   threat. A hulking savage pays multiples of a limping runt.
3. **The chip floor is not the difficulty curve.** Dangerous archetypes
   carry ATK high enough to beat `DEF/2`, or they are not dangerous.
4. **Every level sells something.** No level 1–10 may unlock nothing.
5. **Upgrades buy access, not comfort.** A new tier should open animals
   you had to run from.
6. **The tower forgives the unlucky, not the reckless.** A rubber band
   cuts the odds of drawing a fight you'd lose by 80% — it never removes
   it.
7. **Quantities are shown, not stated.** Coins and aether are drawn as
   marks up to 99, then as a number.

---

## Phase 1 — Monster archetypes (the variance engine)

Content still authors no numbers. Add a **stat-archetype trait axis**
alongside the existing defense axis, and map it to multipliers in
`economy.py`:

```python
CREATURE_HP  = {"frail": 0.45, "lean": 0.7, "sturdy": 1.8,
                "hulking": 3.0}          # absent = 1.0
CREATURE_ATK = {"feeble": 0.6, "fierce": 2.4, "savage": 4.0}
```

`fierce`/`savage` are deliberately steep because of the chip-floor
arithmetic in §2: on floor 1, ATK 5 → 12 (fierce) or 20 (savage) is what
it takes for a bite to be felt at all. A savage floor-1 animal deals
3–13 per round instead of 1.

**The floor 1–10 spread** (a `prey / peer / brute / killer` shape per
floor, assigned to the four existing encounter ids so no new art is
needed). Floor 1 becomes:

| creature | traits | HP | ATK | fight |
|---|---|---|---|---|
| Hedgerow rat | `frail`, `feeble` | 8 | 3 | one hit, thin pay |
| Grey wolf | — | 18 | 5 | the baseline |
| Feral boar | `sturdy`, `fierce` | 32 | 12 | a real trade |
| Goblin straggler | `lean`, `savage` | 13 | 20 | glass cannon — it can kill you |

`TRAIT_INTRO_FLOOR` keeps gating the **defense** axis (armor from 2,
resist from 3, flying from 4, bulwark from 6). The archetype axis is
legal from floor 1 — it is the variance the first floor never had. The
floor-1 "no traits" lint rule is replaced by "no *defense* traits".

Speed joins the spread: `fast` and `slow` also become legal from floor 1
(they are chase math, not damage), so some animals must be outrun.

## Phase 2 — Danger pays (rewards follow the fight)

```python
def kill_reward_mult(traits) -> float      # hp_mult × (0.5 + 0.5·atk_mult)
```

Applied to **XP and gold both** (XP has never had a threat modifier),
composed with the existing specimen and profile multipliers, and capped
so a single kill can't outpay a Warden. Floor 1 becomes: rat ≈ 0.3×,
wolf 1.0×, boar ≈ 2.7×, goblin ≈ 1.6× — visible, and worth choosing
between.

## Phase 3 — The Wardens of 1–10 do not heal

- `world_warden_regen_hourly(F) = 0` for F ≤ 10 (already 0 through 30
  after 024) **and** `warden_silence_hours(F) = None` for F ≤ 10 — no
  silence close, no pity, no forgetting. A wound in the first ten floors
  is permanent until the floor falls.
- In exchange the first ten gates get **teeth**: pool ×1.6 and Warden ATK
  raised so a floor-1 Warden can actually kill a careless climber. The
  fight is a siege you chip at across days, exactly as asked — "they can
  have a large energy but even a single player can have at them over
  time."
- The keep card states the law: *"It does not heal. Every blow you land
  here is permanent."*

## Phase 4 — Something to buy at every level

Re-space band 1 from three gate moments to **ten** — one per level — and
do it by generalising the gate law rather than adding special cases:

```
rung T.k opens k steps into its band  →  band_start(T) + k
```

T.5 therefore still lands at band_start+5 (the pre-025 mid, untouched)
and band 1 gets nine new steps at levels 2–10. **No number is authored.**
Bonus interpolates linearly between the T1 and T2 rows and price
geometrically; at k=5 that is *exactly* the old mid (which was defined as
that midpoint and that geometric mean), which is the proof that nothing
already bought changes power or price.

| Level | Rung | Weapon | Shield / focus | Armor |
|---|---|---|---|---|
| 1 | 1.0 | 8 · ◈250 | 5 · ◈100 | 7 · ◈200 |
| 2 | 1.1 | 11 · ◈280 | 6 · ◈110 | 9 · ◈220 |
| 3 | 1.2 | 14 · ◈320 | 7 · ◈130 | 10 · ◈250 |
| 4 | 1.3 | 17 · ◈350 | 8 · ◈140 | 12 · ◈280 |
| 5 | 1.4 | 20 · ◈400 | 9 · ◈160 | 13 · ◈320 |
| 6 | 1.5 | 23 · ◈450 *(exists)* | 10 · ◈180 *(exists)* | 15 · ◈360 *(exists)* |
| 7 | 1.6 | 26 · ◈500 | 11 · ◈200 | 17 · ◈400 |
| 8 | 1.7 | 29 · ◈560 | 12 · ◈230 | 18 · ◈450 |
| 9 | 1.8 | 32 · ◈630 | 13 · ◈250 | 20 · ◈510 |
| 10 | 1.9 | 35 · ◈710 | 14 · ◈280 | 21 · ◈570 |

Every row exists in all three weapon lines and — new — as a caster focus,
so no class has a level that sells it nothing.

**Styles — "the same icon in different colours".** Every band-1 rung
ships in three cuts, so each gate is a *choice*, not a purchase:

| Style | Bonus | Durability | Price | Tint |
|---|---|---|---|---|
| plain | as tabled | ×1.0 | ×1.0 | steel |
| keen | ×1.15 | ×0.65 | ×1.40 | ember |
| warded | as tabled | ×1.75 | ×1.20 | frost |

Keen buys power with upkeep; warded buys upkeep with gold. They are real
`FORGE` items, so equipping, honing, wear, repair, the pawn shop, the
armory and the off-class twin logic all took them for free. `icons.py`
masks are tinted by `currentColor` already, so a style is a palette on
the same glyph — a real visual family for near-zero cost.

**Consumables for the first ten floors.** The tactical shelf starts at
floor 6 and mostly 11+, while the traits it answers appear from floor 2 —
so a walled matchup was a wall instead of a shopping list. Each counter
comes down to one floor after its trait: oil 2, curse scroll 3, poison
arrows and strip potion 4, slowing arrows and the net 5, sky-hook 6, fire
and piercing arrows 8. The flying+bite lint rule reads the hook's floor
from the shelf, so the law follows the price list.

**The tuning ripple (the important half of this phase):**
`_at_level_loadout` — the reference every monster and Warden number
derives from — read the WHOLE tier, so once band 1 sells nine more rungs
the tower would be tuned against a climber who does not exist. It now
reads `reference_rung(floor)`. This *also fixes a pre-existing bug*:
levels 6–10 could already buy rung 1.5 (+23) while the reference assumed
+8, which is part of why the band played flat. And `reference_hone` drops
to 0 through band 1 — with the rung ladder carrying the within-band
growth, counting honing too put the floor-10 reference above the floor-11
one, a cliff in a tower that must be a straight line. The 022/002 and 024
acceptance gates re-run as the proof.

## Phase 5 — The rubber band

Before the hunt table is rolled, score each candidate against the actual
player:

```
rounds_to_kill  = ceil(hp / player_damage_per_round)
damage_taken    ≈ rounds_to_kill × expected_monster_damage
lethal          = damage_taken ≥ 0.9 × player_hp
```

A lethal candidate keeps **20% of its weight** (an 80% cut, as asked).
Never zero: the tower must still be able to put something in front of you
that you have to run from — that is Phase 1's whole point. The scan and
the opener prose carry the warning (`savage`, `hulking` tags), so running
is an informed choice.

## Phase 6 — Draw the coins

Scene grows a structured `tally` (`[{"kind": "gold", "n": 37}, …]`) set on
every victory; the HTML renderer draws `n` coin masks for `n < 100` (a
wrapped grid, 10 per row) and falls back to `◈ 1,234` at 100+. Same for
aether/XP. The text surface keeps words, so nothing leaks into chat.
New `coin` and `aether` masks join `icons.py`.

---

## Acceptance

- No two creatures on any floor 1–10 share a stat line; each floor offers
  a one-hit prey and something that can kill an at-level player.
- A level-3 at-level player, played correctly, must RUN from at least one
  archetype on their floor.
- XP per kill varies at least 4× within a single floor; so does gold.
- Every level 1–10 unlocks at least one purchasable item; every rung
  offers three styles at three prices.
- Wardens 1–10 never regain a point of HP; a solo climber's wounds are
  permanent, and the pool is closable over days.
- A player whose expected outcome is death meets that fight 80% less
  often — but not never.
- Victory cards draw coins and aether up to 99, numerals beyond.
- Every 022/002 and 024 acceptance gate still passes after the reference
  loadout is re-anchored.
- `MUST_BE_DONE_LATER.md` records every 1–10 tuning decision that floors
  11–100 still need.
