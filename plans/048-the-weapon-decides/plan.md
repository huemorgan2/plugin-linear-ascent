# 048 — the weapon decides (no classes, trained hands)

## Problem (designer's words, 2026-08-11)

*"Having an archer that has a treeline shot while a warrior doesn't,
and they have the same attack, is an issue. If we solve it with types
of monsters and damage, they will be balanced — not fun. So I'm
questioning the types of warriors. Maybe we move it to the types of
weapons you pick, not the type of player. There is no archer — there
is a warrior only, and you are an archer when you buy a bow. And you
train to be better at it, in the school. You spend XP to learn the
bow, improve your aim. You buy a sword but your chance of yielding
its full power is low — you train. So we add another layer of
progress: buy any weapon type, train each path, and then you can
attack all three types of monsters and be better at it."*

Design law this plan serves: **fun is difficulty overcome and
understood.** Every piece must pass three questions: can I lose?
can I tell why? can I change it next time?

Decisions already made (2026-08-11):
- Races stay untouched: human / elf / dwarf.
- Ranks are numbers only — **trained rank 0–5**, shown as a bar. No
  rank names.
- The magic-resistant type is called **magic-resistant** (not
  spellguard), is **weak to the sword** and **not fully armoured**.
- FLY monsters hit **weak** — fast but low ATK; armoured and
  magic-resistant hit hard but are slow.
- Every monster shows **all its numbers** plus its sign, everywhere.
- Floors 1–10 drop **extra coin** so the player can buy and try the
  basic weapon of every path early.

## The design in one paragraph

Delete classes. Every player is a climber. What you fight *like* is
decided by what is in your hand — blade, bow, or staff — and how well
you fight is decided by how much you have **trained that path** at
the School. Monsters come in three signed types — FLY ⚡, ARMOURED ⛨,
MAGIC-RESISTANT ✧ — and each type has one weapon that answers it
well, one that answers it poorly, and one that barely works. The game
gains a second progression layer: levels make your body stronger (as
today), training makes your *hands* better with each weapon. A
countered monster is never "not for your class" — it is "not for the
weapon you brought and trained", and both are choices the player owns.

---

# PART I — THE NUMBERS

Everything new, changed, or deleted. All names final unless marked.

## N1. Monster types (replaces armor/resist tiers + flying/slow/fast)

One type per monster: `fly` / `armoured` / `magic_resist` / `plain`.
The type bundles **sign, speed, attack weight, and the damage
triangle** — one authoring decision instead of five traits.

| type | sign | SPD | ATK weight | HP weight |
|---|---|---|---|---|
| `fly` | ⚡ | 7 (fast) | ×0.6 — many weak cuts | ×0.9 |
| `armoured` | ⛨ | 3 (slow) | ×1.4 — rare, heavy | ×1.2 |
| `magic_resist` | ✧ | 3 (slow) | ×1.4 — rare, heavy | ×1.0 |
| `plain` | — | 5 | ×1.0 | ×1.0 |

```python
TYPE_SPEED  = {"fly": 7, "armoured": 3, "magic_resist": 3, "plain": 5}
TYPE_ATK    = {"fly": 0.6, "armoured": 1.4, "magic_resist": 1.4,
               "plain": 1.0}
TYPE_HP     = {"fly": 0.9, "armoured": 1.2, "magic_resist": 1.0,
               "plain": 1.0}
```

Weights apply on top of `creature_stats` (which already carries the
pillar); an armoured monster on floor N hits like a plain monster
about one floor up, a flyer like two floors down — but far more
often (SPD 7 vs 3 through `p_close`).

**Dies:** `armor_low/med/high`, `resist_low/med/high`, `flying`,
`slow`, `fast` traits; `TIER_MULT`; `PROFILE_GOLD`;
`FLYING_GOLD_MULT`. `bulwark` survives as an orthogonal elite marker
(▣, HP ×2.2, gold ×1.5) — it is a wall, not a weapon-answer.
**Gold bump:** `TYPE_GOLD = {"fly": 1.2, "armoured": 1.3,
"magic_resist": 1.3, "plain": 1.0}` (replaces the tier-based
`profile_gold_mult`).

## N2. The damage triangle (replaces typed_damage tiers)

Damage of path P against type T: `raw_after_def × TYPE_MULT[T][P]`.

| type | ⚔ blade | ➶ bow | ✦ staff |
|---|---|---|---|
| `fly` | **0.0 — can't reach** | **1.0** | 0.6 |
| `armoured` | 0.5 | 0.15 | **1.0** |
| `magic_resist` | **1.0** | 0.5 | 0.15 |
| `plain` | 1.0 | 1.0 | 1.0 |

- Staff (magic) keeps ignoring flat DEF: `base = raw`. Blade and bow
  keep `base = raw − DEF//2`. Then `dmg = max(1, round(base × mult))`
  — the ≥1 chip law (013) survives, EXCEPT blade-vs-fly which is the
  single legal 0.
- ×0.15 answers chip 1s and 2s — visibly a mistake, not a wall.
- `BOW_CLOSE_MULT` (0.5) and `BOW_GAP_MULT` (1.0/1.25/1.5) stack on
  top unchanged — the gap ladder is the bow's identity, the triangle
  is the monster's.

## N3. Trained ranks (new; replaces the whole off-class system)

Per-path integer **trained rank 0–5**, stored on the player:

```python
p["training"] = {"blade": 1, "bow": 0, "staff": 0}   # new-player start
```

Effects of rank R when the held weapon is on path P:

```python
TRAIN_MISS_PCT   = lambda R: max(0, 25 - 5 * R)   # 25/20/15/10/5/0 %
TRAIN_ROLL_FLOOR = lambda R: (30 + 8 * R) / 100   # .30 → .70 of ATK
```

The swing rolls uniform in `[roll_floor(R)·ATK, ATK]` (today: fixed
`[ATK/2, ATK]` — rank 2½ is the old feel). A miss eats the round and
the monster answers with its normal counter. Mean damage rank 0 → 5
rises ≈ ×1.34 with no lost rounds — training is consistency the
player can feel.

Training costs, paid at the School, frontier = highest unlocked
floor:

```python
TRAIN_XP_ANCHOR   = 40
TRAIN_GOLD_ANCHOR = 15
train_xp(R)          = round(40 * R ** 1.5)        # 40/113/208/320/447
train_gold(R, front) = round(15 * pillar(front) * R)
```

- Full path 0→5: **1,128 XP** ≈ the XP of body levels ~7→9 — a real
  second sink, not a tax. Second and third paths are where the extra
  grind goes; broad mastery is the long game.
- Gold is the minor component (instructor's fee, rides the pillar so
  it never trivializes); XP is the currency of learning.
- Ranks never decay. Cap 5. XP re-bake: `XP_PER_KILL_SLOPE` 2.4 →
  **2.9** (+20%) so one-path climbers keep today's level≈floor pace
  while funding one path to ~3 by mid-tower (verify in the bake).

**Dies:** `OFF_CLASS_PRICE_MULT`, `OFF_CLASS_DMG_MULT`,
`OFF_CLASS_MISS`, `off_class_price()`, `off_class_offer()`, arrow
burn for off-class bows (`ARROW_PACK_*` stays only if some bow
mechanic still uses it — expected: dies).

## N4. Classes die; weapons and lines survive

- `CLASSES` dict, creation class question, `class_starter()` — die.
- `clazz` field stays on old docs, ignored (migration N7).
- Weapon `line` tags survive as the path key:
  `PATH_OF_LINE = {"warrior": "blade", "archer": "bow",
  "sorcerer": "staff"}`; `DAMAGE_TYPE` becomes line-keyed only
  (it already is: `{"warrior": "melee", "archer": "ranged",
  "sorcerer": "magic"}`).
- The armory sells **every** weapon line to everyone at the one
  listed price. The three lines stay rung-for-rung mirrors
  (`line_twin` survives for trading).
- Starter kit: Rusted Sword (free, as today) + `p["training"]`
  blade 1. The two other gate-issue weapons become **purchasable**:

```python
BASIC_WEAPON_PRICE = 60        # basic_bow, worn_staff at the armory
```

  (+5 ATK, never wear, never lost — same stats as the starter
  sword.) At ◈60 they cost ~3–4 kills on floors 3–5 under the
  young-tower bounty (N6) — every player can own all three paths'
  basic weapons before floor 10.

## N5. Fight actions follow the weapon + rank

| action | today | 048 gate |
|---|---|---|
| Treeline shot | archer only | bow in hand, bow rank ≥ 2 |
| Create distance | archer only | bow in hand, bow rank ≥ 3 |
| Gap draw ×1.25/×1.5 | archer only | bow in hand, bow rank ≥ 4 |
| Shield wall | warrior only | shield equipped, blade rank ≥ 2 |
| Sleep spell | sorcerer only | staff in hand, staff rank ≥ 3 |
| **Switch weapon** (new) | — | second weapon in pack; costs the round (monster gets its close/strike roll) |

Locked actions render greyed with the requirement:
`Treeline shot — needs Bow rank 2 (you: 1)`.

## N6. Early-tower coin (new)

```python
EARLY_COIN_FLOORS = 10
def early_coin_mult(floor):        # ×2.0 at floor 1 → ×1.1 at 10 → ×1.0
    return 2.0 - 0.1 * (floor - 1) if floor <= 10 else 1.0
```

Applied in the `gold_per_kill` path for floors 1–10, labeled on the
kill card as *"young-tower bounty"* so the fade never reads as a
nerf. Purpose: fund all three basic weapons (◈180 total) + first
ranks in each path by floor 10. The first ten floors are the
classroom — all three signs appear there in weak specimens.

## N7. Migration (one-time, on first load of a legacy doc)

- `p["training"] = {old class's path: 3, others: 0}`.
- One-time card: *"The guilds dissolved their halls into one School.
  Your years as an archer are honored: Bow — trained rank 3."*
- Old class weapons keep working — line tags already map to paths.
- Old monster traits: `type_from_traits` maps legacy trait sets to
  the nearest type — `flying` → `fly`; `armor_*` → `armoured`;
  `resist_*` → `magic_resist`; both armor+resist → `magic_resist`;
  none → `plain`. Floor YAML is then bulk-retagged (phase 6) so the
  legacy mapping is transitional only.

---

# PART II — WHAT THE PLAYER SEES

## S1. Creation

One less question. Race (human/elf/dwarf) and name, as today. First
gate-town visit shows the School door: *"Any hand can hold any
weapon. The School teaches it to bite."*

## S2. The School (new room, every gate town, next to the armory)

```
⚔ BLADE   trained rank 3   ▰▰▰▱▱  next: rank 4 — 320 XP + 60 ◈
➶ BOW     trained rank 0   ▱▱▱▱▱  next: rank 1 — 40 XP + 15 ◈
✦ STAFF   trained rank 0   ▱▱▱▱▱  next: rank 1 — 40 XP + 15 ◈
```

Each "next" line says in words what improves: *"Rank 4: miss
15%→10%, your worst swing 54%→62% of full power."* No silent
numbers.

## S3. Every monster shows all its numbers

Hunt menu, fight scene, mechanics page — full parameter line + sign:

```
VAULT BOAR ⛨            HP 210 · ATK 116 · DEF 48 · SPD 3 (slow)
armoured — steel: half · arrows: glance · magic: full
```

Plain monsters: *"no sign — every weapon bites full."* This extends
the 003 law (no silent numbers) to monsters completely.

## S4. The verdict, before every fight

Computed from the player's ACTUAL weapons and ranks — the mechanics
HITS column personalized and moved to the moment of decision:

- *"⛨ Armoured. Your arrows will glance (~40 shots). Steel: half.
  A staff bites full — yours is rank 0."*
- *"⚡ It flies. Your blade cannot reach it. Bow or staff, or walk
  away."*

## S5. The strike text teaches

Weapon line on the fight card: `Rusted Sword · ⚔ rank 2 ▰▰▱▱▱`.
Bad rolls blamed on the hand, not luck: *"Your untrained swing lands
shallow — 12. A rank-4 hand would have cut nearer 30."* Misses:
*"Not yet your weapon — the swing goes wide. The School in town
fixes this."* A blade-only climber facing ⚡ gets the truth instead
of an Attack button: *"It is above you. Nothing in your pack
reaches. Run, or come back with a bow."* (Running from a flyer is
free — it doesn't chase downward.)

## S6. Early kills

*"+18 ◈ (young-tower bounty)"* on floors 1–10.

---

# PART III — CODE CHANGES BY FILE

- **`economy.py`** — add `TYPE_SPEED/ATK/HP/GOLD`, `TYPE_MULT`,
  `PATH_OF_LINE`, `TRAIN_*` tables + `train_xp`/`train_gold`,
  `early_coin_mult`, `BASIC_WEAPON_PRICE`; rewrite
  `profile_from_traits` → `type_from_traits` (with legacy mapping),
  `typed_damage(path, raw, def, mtype)`, `profile_gold_mult` →
  `TYPE_GOLD`; delete `TIER_MULT`, `PROFILE_GOLD`, `OFF_CLASS_*`,
  `off_class_price/offer`, `CLASSES`, `class_starter`; make
  `basic_bow`/`worn_staff` armory-listed at ◈60; bump
  `XP_PER_KILL_SLOPE` → 2.9.
- **`engine/combat.py`** — `_player_hit`: roll
  `[roll_floor(R)·ATK, ATK]`, miss `TRAIN_MISS_PCT(R)`; path from
  held weapon's line, rank from `p["training"]`; action gates per
  N5 (all `clazz ==` checks die); new `switch_weapon` option;
  full stat headline + sign on every card; verdict lines in
  `fight_scene`/hunt table; strike/miss text per S5.
- **`engine/core.py`** — creation: `_creation_pick_race` → name
  stage directly (class scene dies); init `p["training"]`; migration
  hook for legacy docs (N7); School scene + train choice handlers.
- **`state.py`** — `training` dict on the player doc; `clazz`
  tolerated-legacy.
- **Floor YAML (content)** — bulk retag 425 monsters: traits →
  one type (+ optional `bulwark`). The current ⚡/⛨/✧ signs on
  /mechanics say which is which.
- **`worldd/tools/gen_mechanics.py` + site** — HITS column becomes
  per-path at reference rank 3; TRAINING tab with the rank tables;
  simulator gets a rank input instead of a class dropdown.
- **Tests** — every phase below names its own.

---

# PART IV — PHASES (each lands green and shippable)

Run tests with the worldd venv per the release flow. Each phase is
one commit; the game is playable after every one.

## Phase 1 — the triangle (economy only, no behavior change yet)

Add types, `TYPE_*` tables, `type_from_traits` (with the legacy
trait mapping), new `typed_damage(path, ...)` alongside the old one.
Nothing calls the new code yet.

**Tests:** table-driven `test_type_triangle.py` — every
(type × path) cell of N2 exact; legacy trait sets map to the right
type; chip ≥1 everywhere except blade-vs-fly = 0; TYPE_SPEED/ATK/HP
applied by `creature_stats`.

## Phase 2 — trained ranks in the swing

`p["training"]` (default blade 1), `TRAIN_MISS_PCT`/
`TRAIN_ROLL_FLOOR`, `_player_hit` rolls by rank of the held weapon's
path. Classes still exist and still gate actions — only the damage
roll changes. Migration grant (old class path → rank 3) lands here
so existing players feel no nerf.

**Tests:** rank 0 misses ~25% and floors at 30% (seeded RNG);
rank 5 never misses and floors at 70%; migration grants rank 3 to
the right path; legacy doc without `training` plays without error.

## Phase 3 — the School

School scene in gate towns; `train_xp`/`train_gold`; spend flow
(XP+gold check, rank +1, refusal texts). Rank effects already live
from phase 2, so training is immediately felt.

**Tests:** cost curve values exact (40/113/208/320/447 XP;
gold ×pillar(frontier)); can't train past 5; can't pay twice; XP
deducted from the pool, gold from the purse; School lines carry the
"what improves" sentence (003 law assert).

## Phase 4 — classes die

Creation drops the class question (race → name); everyone starts
Rusted Sword + blade 1; armory sells all lines at list price
(`OFF_CLASS_*` deleted); `basic_bow`/`worn_staff` purchasable ◈60;
action gates flip from `clazz` to weapon+rank (N5); `switch_weapon`
action added. Monster side still on old tiers — the triangle wires
in next.

**Tests:** creation flow race→name; new doc has training dict and
no clazz; every weapon purchasable by anyone at one price; each N5
gate opens exactly at its rank with the weapon held; switch spends
the round and the monster answers; treeline shot with bow rank 2
works for a doc that was never an archer.

## Phase 5 — monsters switch to types

`typed_damage` calls flip to the triangle; monster cards show the
full stat line + sign; verdict lines; blade-vs-fly shows the run
truth instead of attack; kill gold uses `TYPE_GOLD`. Legacy trait
mapping carries un-retagged YAML.

**Tests:** simulated fights per (type × path × rank ∈ {0,3,5})
match expected kill-turn counts within tolerance; fight card
contains HP/ATK/DEF/SPD and the sign; verdict text names the
player's actual best answer; melee attack option absent vs fly.

## Phase 6 — content retag + economy bake

Bulk retag 425 monsters' traits to the three types (script over
floor YAML, review diff by floor bands); `early_coin_mult` wired
with the bounty label; `XP_PER_KILL_SLOPE` → 2.9; re-run the bake
(kill bars, level≈floor pace with one path trained to 3 by
mid-tower); gen_mechanics per-path HITS + TRAINING tab; cache-bust.

**Tests:** no monster left with legacy traits (lint over YAML);
every floor 1–10 spawns at least one of each sign; coin mult exact
at floors 1/5/10/11; bake sanity — floor-10 climber income covers
3 basic weapons + ~6 ranks; existing production suite green.

## Phase 7 — polish pass (post-review)

Strike/miss teaching texts everywhere, School door line, one-time
migration card, mechanics simulator rank input. Play a floor-1→12
run by hand; fix what reads wrong.

**Tests:** production run checklist (release flow); the
three-question audit on one monster of each type at rank 0 and
rank 3.

---

# THE AUDIT

- **Can I lose?** Wrong weapon or untrained hand against a signed
  type is a visible, felt loss (or a forced run).
- **Can I tell why?** The sign and all stats are on the card before
  the fight; the verdict is written in your weapons' terms; every
  shallow hit or miss names the untrained hand.
- **Can I change it next time?** Two ways, both bought with play:
  train the path (School, XP+gold) or carry the counter-weapon
  (armory, ◈ + a round to switch). Nothing is locked to a day-one
  choice — there are no types of players.

## Open questions

1. ~~SPELLGUARD~~ — decided: named "magic-resistant"; weak to sword,
   not fully armoured; FLY hits weak.
2. Rank cap 5 — rare/late or reachable per path by mid-tower?
   (Plan prices it reachable: 447 XP + ◈75·pillar for the last step.)
3. Train-by-use (kills with the weapon drip path-XP) or School-only?
   Plan assumes School-only for legibility.
4. Two-weapon carry: free pack slot or a bought harness item?
   Plan assumes free pack slot (the round cost is the price).
