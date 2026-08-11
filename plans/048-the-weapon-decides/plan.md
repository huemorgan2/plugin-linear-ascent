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

Design law: **fun is difficulty overcome and understood.** Every
piece must pass: can I lose? can I tell why? can I change it next
time?

Decisions made (2026-08-11):
- Races stay untouched: human / elf / dwarf.
- Skill is a number and a bar — **trained rank 0–10** (rescaled from
  0–5 for a stronger feeling of progression). No rank names.
- The magic-resistant type is called **magic-resistant**, is weak to
  the sword and not fully armoured.
- FLY hits weak — fast but low ATK; armoured and magic-resistant hit
  hard but are slow.
- Every monster shows **all its numbers** plus its sign, everywhere.
- Floors 1–10 drop extra coin so the player can buy and try every
  path's basic weapon early.
- **Maxing one path (rank 10) costs about the XP of reaching player
  level ~10** — a real goal, reached around the first band's end.
- At rank 10 a path opens **mastery studies** — more things to learn
  in that profession — and formally opens the other weapon types.
- **Spreading over all three paths is deliberately slower** — each
  rank costs more than the last (it costs XP), and no player should
  find tri-path investment optimal.
- **Carry is a School skill**: a second weapon slot is learnable
  from level 1; a third slot costs a lot more and opens at player
  level 8 (shown locked until then). Each slotted weapon is its own
  attack option in the fight — sword attack AND bow attack.
- Tests change FIRST: visibility (why I lost, every monster param),
  smooth scaling with no bumps across levels, weapon rungs, and
  floors, and healthy progression pacing are all asserted before
  the mechanics land.

## The design in one paragraph

Delete classes. Every player is a climber. What you fight *like* is
decided by what is in your hand — blade, bow, or staff — and how
well you fight is decided by how much you have **trained that path**
at the School. Monsters come in three signed types — FLY ⚡,
ARMOURED ⛨, MAGIC-RESISTANT ✧ — and each type has one weapon that
answers it well, one that answers it poorly, and one that barely
works. The game gains a second progression layer: levels make your
body stronger, training makes your *hands* better. A countered
monster is never "not for your class" — it is "not for the weapon
you brought and trained", and both are choices the player owns.

---

# PART I — THE NUMBERS

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
TYPE_SPEED = {"fly": 7, "armoured": 3, "magic_resist": 3, "plain": 5}
TYPE_ATK   = {"fly": 0.6, "armoured": 1.4, "magic_resist": 1.4,
              "plain": 1.0}
TYPE_HP    = {"fly": 0.9, "armoured": 1.2, "magic_resist": 1.0,
              "plain": 1.0}
TYPE_GOLD  = {"fly": 1.2, "armoured": 1.3, "magic_resist": 1.3,
              "plain": 1.0}
```

Weights apply on top of `creature_stats` (which already rides the
pillar). **Dies:** `armor_*`, `resist_*`, `flying`, `slow`, `fast`
traits; `TIER_MULT`; `PROFILE_GOLD`; `FLYING_GOLD_MULT`;
`profile_gold_mult`. `bulwark` survives as an orthogonal elite
marker (▣, HP ×2.2, gold ×1.5) — a wall, not a weapon-answer.

## N2. The damage triangle

Damage of path P against type T: `raw_after_def × TYPE_MULT[T][P]`.

| type | ⚔ blade | ➶ bow | ✦ staff |
|---|---|---|---|
| `fly` | **0.0 — can't reach** | **1.0** | 0.6 |
| `armoured` | 0.5 | 0.15 | **1.0** |
| `magic_resist` | **1.0** | 0.5 | 0.15 |
| `plain` | 1.0 | 1.0 | 1.0 |

- Staff (magic) keeps ignoring flat DEF (`base = raw`); blade and
  bow keep `base = raw − DEF//2`. Then
  `dmg = max(1, round(base × mult))` — the ≥1 chip law (013)
  survives; blade-vs-fly is the single legal 0.
- ×0.15 answers chip 1s and 2s — visibly a mistake, not a wall.
- `BOW_CLOSE_MULT` (0.5) and the gap ladder (1.0/1.25/1.5) stack on
  top unchanged.

## N3. Trained ranks 0–10 (replaces the whole off-class system)

Per-path integer **trained rank 0–10** on the player doc:

```python
p["training"] = {"blade": 2, "bow": 0, "staff": 0}  # new-player start
```

Effects of rank R with a path-P weapon in hand:

```python
TRAIN_MISS_PCT   = lambda R: max(0, round(25 - 2.5 * R))
                   # 25 → 0% at rank 10
TRAIN_ROLL_FLOOR = lambda R: (30 + 4 * R) / 100
                   # worst swing: 30% → 70% of ATK at rank 10
```

The swing rolls uniform in `[roll_floor(R)·ATK, ATK]`. Today's fixed
`[ATK/2, ATK]` with no miss ≈ **rank 5** — the middle of the ladder
is the old feel; everything above it is new power. A miss eats the
round and the monster answers. Mean damage rank 0 → 10 rises ≈
×1.34 with all misses gone — training is consistency the player can
feel, in ten visible steps instead of five.

**Costs** — each rank costs more than the last; XP is the currency
of learning, gold the instructor's fee (rides the pillar so it never
trivializes). Frontier = highest unlocked floor:

```python
TRAIN_XP_ANCHOR   = 20
TRAIN_GOLD_ANCHOR = 8
train_xp(R)          = round(20 * R ** 1.5)
   # 20/57/104/160/224/294/371/453/540/632  (ranks 1..10)
train_gold(R, front) = round(8 * pillar(front) * R)
```

- **One path 0→10 = 2,855 XP ≈ the XP of body levels 1→10**
  (Σ xp_need(1..9) = 2,664) — mastering your first weapon is a
  level-10-sized achievement, landing near the first band's end.
- **All three paths = 8,565 XP ≈ body levels 1→21** — spreading is
  possible and deliberately slower; the sim tests (T5) assert a
  tri-path climber trails a single-path climber by several body
  levels at equal kills. No player should find it optimal; it is a
  long-game choice, not a trap (the cost is printed).
- Ranks never decay. XP re-bake: `XP_PER_KILL_SLOPE` 2.4 → **3.0**
  (+25%) so a one-path climber keeps today's level≈floor pace while
  funding the path (verified in the bake, T4).

**Dies:** `OFF_CLASS_PRICE_MULT`, `OFF_CLASS_DMG_MULT`,
`OFF_CLASS_MISS`, `off_class_price()`, `off_class_offer()`,
off-class arrow burn (`ARROW_PACK_*` dies with it).

## N4. Mastery at rank 10

Reaching rank 10 in a path is a public achievement (banner-hall
material). It opens:

1. **Mastery studies** — the School master offers further learning
   in that profession, priced in XP like ranks. First set (one per
   path, more can ship later):
   - ⚔ *Riposte* — a blocked/shallow monster strike returns 25% of
     your mean swing.
   - ➶ *Long draw* — gap-3 shots crit (×1.5) on the top 10% of the
     roll.
   - ✦ *Focus* — your ×0.6 and ×0.5 answers become ×0.75.
   Cost: `round(train_xp(10) * 1.5)` = 948 XP each.
2. **The invitation** — the master formally points the climber to
   the other two paths: a one-time card and a **20% XP discount on
   the other paths' ranks 1–5** ("a trained hand learns the next
   grip faster"). This is the "open them up to other weapon types"
   beat — the other paths were never locked, but mastery makes
   starting them cheaper and *narrated*.

**What the player sees:** the School bar at 10 turns gold; the row
gains a MASTERY line listing studies with costs; the invitation
card names the discount.

## N5. Carry — more than one weapon in the fight

A School skill, not an item. You enter every fight with your
**slotted** weapons; each slot is its own attack option:

```
› Sword attack ⚔ rank 6 — ~38 vs this one (steel: half)
› Bow attack   ➶ rank 3 — ~9 vs this one (arrows: glance)
```

Every slotted weapon rolls with its OWN path's rank and its own
triangle answer — no switching action, no lost round. Weapons
beyond your slots stay in the pack; slots are rearranged freely in
town or between fights, never mid-fight.

```python
WEAPON_SLOTS_BASE = 1          # everyone starts with one hand ready
CARRY2_XP,  CARRY2_GOLD  = 60,  30    # 2nd slot — learnable at level 1
CARRY3_XP,  CARRY3_GOLD_ANCHOR = 900, 200
CARRY3_LEVEL = 8               # 3rd slot: costs a lot more, opens at 8
carry3_gold(front) = round(200 * pillar(front))
```

- The 2nd slot is cheap on purpose — it is the classroom's key: buy
  a bow, learn carry, and the triangle is playable on floor 3.
- The 3rd slot is the completionist's answer to all three types at
  once — priced like a mid-tower luxury and gated at player level
  8. Below 8 it renders **locked with the requirement**:
  `3rd slot — 900 XP + ◈620 (needs level 8 — you: 5)`.

**What the player sees:** a CARRY row in the School under the three
path bars (S2); in the fight, one attack option per slotted weapon,
each labeled with its weapon, rank, and predicted damage against
THIS monster — the triangle made pickable. **In the profile/bag:**
hovering a weapon in the bag shows its tooltip with a
`Hold — promote to slot` action; picking it moves the weapon into a
holding slot (choosing which slot to bump when all are full).
Slotted weapons render at the top of the sheet as the HOLDING row
with their ⚔/➶/✦ path marks; a bag weapon's tooltip also says why
promotion is refused mid-fight.

## N6. Classes die; weapons and lines survive

- `CLASSES` dict, creation class question, `class_starter()` — die.
- `clazz` stays on old docs, ignored by the engine (migration N9).
- Weapon `line` tags survive as the path key:
  `PATH_OF_LINE = {"warrior": "blade", "archer": "bow",
  "sorcerer": "staff"}`; `DAMAGE_TYPE` stays line-keyed
  (melee/ranged/magic); every by-class read dies.
- The armory sells **every** weapon line to everyone at the one
  listed price (`line_twin` survives for trading).
- Starter kit: Rusted Sword (free) + blade rank 2. The other two
  gate-issue weapons become purchasable:

```python
BASIC_WEAPON_PRICE = 60        # basic_bow, worn_staff at the armory
```

  (+5 ATK, never wear, never lost.) ~3–4 kills on floors 3–5 under
  the young-tower bounty — all three basic weapons owned before
  floor 10 is the intended path.

## N7. Fight actions follow the weapon + rank (0–10 scale)

"In hand" = in a holding slot (N5). With two slots holding sword
and bow, both columns of options are live in the same fight.

| action | today | 048 gate |
|---|---|---|
| Sword/Bow/Staff attack | one "Attack" | one attack option per SLOTTED weapon (N5) |
| Treeline shot | archer only | bow in a slot, bow rank ≥ 4 |
| Create distance | archer only | bow in a slot, bow rank ≥ 6 |
| Gap draw ×1.25/×1.5 | archer only | bow in a slot, bow rank ≥ 8 |
| Shield wall | warrior only | shield equipped, blade rank ≥ 4 |
| Sleep spell | sorcerer only | staff in a slot, staff rank ≥ 6 |

The mid-fight switch-weapon action is NOT needed — slots replace
it. Locked actions render greyed with the requirement:
`Treeline shot — needs Bow rank 4 (you: 2)`.

## N8. Early-tower coin

```python
EARLY_COIN_FLOORS = 10
def early_coin_mult(floor):     # ×2.0 at floor 1 → ×1.1 at 10 → ×1.0
    return 2.0 - 0.1 * (floor - 1) if floor <= 10 else 1.0
```

Applied in the `gold_per_kill` path, labeled *"young-tower bounty"*
on the kill card so the fade never reads as a nerf. Funds the three
basic weapons (◈180) + the first ranks of each path by floor 10.
The first ten floors are the classroom — all three signs appear
there in weak specimens.

## N9. Migration (one-time, on first load of a legacy doc)

- `p["training"] = {old class's path: 6, others: 0}` — rank 6 on
  the new scale ≈ the old class feel plus one visible step of
  headroom.
- One-time card: *"The guilds dissolved their halls into one
  School. Your years as an archer are honored: Bow — trained
  rank 6."*
- Legacy monster traits mapped by `type_from_traits`: `flying` →
  `fly`; `armor_*` → `armoured`; `resist_*` → `magic_resist`; both
  → `magic_resist`; none → `plain`. Floor YAML is bulk-retagged in
  phase 7 so the mapping is transitional only.

---

# PART II — WHAT THE PLAYER SEES

## S1. Creation

One less question. Race (human/elf/dwarf) and name, as today. First
gate-town visit shows the School door: *"Any hand can hold any
weapon. The School teaches it to bite."*

## S2. The School (new room, every gate town, next to the armory)

```
⚔ BLADE   trained rank 6   ▰▰▰▰▰▰▱▱▱▱   next: rank 7 — 371 XP + 56 ◈
➶ BOW     trained rank 0   ▱▱▱▱▱▱▱▱▱▱   next: rank 1 — 20 XP + 8 ◈
✦ STAFF   trained rank 0   ▱▱▱▱▱▱▱▱▱▱   next: rank 1 — 20 XP + 8 ◈
✥ CARRY   1 weapon slot            2nd slot — 60 XP + 30 ◈
                                   3rd slot — locked (needs level 8)
```

Each "next" line says in words what improves: *"Rank 7: miss
10%→8%, your worst swing 54%→58% of full power."* A rank-10 bar
turns gold and shows its MASTERY studies. No silent numbers.

## S3. Every monster shows all its numbers

Hunt menu, fight scene, mechanics page — full parameter line + sign:

```
VAULT BOAR ⛨            HP 210 · ATK 116 · DEF 48 · SPD 3 (slow)
armoured — steel: half · arrows: glance · magic: full
```

Plain monsters: *"no sign — every weapon bites full."* The 003 law
(no silent numbers) extended to monsters completely.

## S4. The verdict, before every fight

Computed from the player's ACTUAL weapons and ranks:

- *"⛨ Armoured. Your arrows will glance (~40 shots). Steel: half.
  A staff bites full — yours is rank 0."*
- *"⚡ It flies. Your blade cannot reach it. Bow or staff, or walk
  away."*

## S5. The strike text teaches — and so does the defeat

Weapon line on the card: `Rusted Sword · ⚔ rank 4 ▰▰▰▰▱▱▱▱▱▱`.
Bad rolls blame the hand, not luck: *"Your half-trained swing lands
shallow — 12. A rank-8 hand would have cut nearer 30."* Misses:
*"Not yet your weapon — the swing goes wide. The School fixes
this."*

**The defeat card names the cause** — one sentence, one lever:
*"The boar's plate turned your arrows — 40 shots was always too
many. Steel halves it; a staff bites full."* / *"It flew; your
blade never reached it once."* / *"Your rank-1 staff missed four
rounds — the School in town fixes this."* Losing must teach WHY,
every time (T2 asserts it).

## S6. Early kills

*"+18 ◈ (young-tower bounty)"* on floors 1–10.

---

# PART III — REMOVING EVERY TRACE OF CLASSES

Validated by grep (2026-08-11). Every file that must change for
"there are no archers, only bows":

**Engine (`plugin_linear_ascent/`):**
- `economy.py` (47 refs) — `CLASSES`, `class_starter`,
  `CLASS_STARTERS` (items survive, the class KEYING dies),
  `OFF_CLASS_*` + `off_class_price/offer`, class-gated shop copy,
  `CONTRACT_CLASS_GOLD_MULT` → weapon-path jobs ("bow contracts",
  not "archer contracts"), `DAMAGE_TYPE` by-class fallback.
- `engine/core.py` (37) — `_creation_class_scene` /
  `_creation_pick_class` die; race → name directly; School scene;
  migration hook.
- `engine/state.py` (17) — `clazz` on the doc → tolerated-legacy;
  `training` dict + `slots` (held weapons, N5); sheet/profile
  payloads.
- `engine/combat.py` (23) — every `p.get("clazz")` gate (§N7);
  `_damage_type` reads the SLOTTED WEAPON's line, never the class;
  one attack option per slot; off-class miss/burn branches die.
- `engine/tips.py` (8) — class-named tips rewritten to weapon-named.
- `engine/profile.py`, `engine/scene.py`, `engine/social.py`,
  `pane.py`, `render.py`, `sheet.py`, `icons.py` — class label on
  the sheet/profile/pane becomes the three training bars + the
  HOLDING row; bag-weapon tooltips gain the `Hold — promote to
  slot` action (N5); class icons → path icons ⚔/➶/✦.
- `content/schema.py` — creature trait vocabulary swaps to the four
  types; weapon `line` field survives.

**Content:** floor YAML (425 monsters, bulk retag, phase 7); any
class-worded flavor text (sweep with grep, phase 6).

**worldd:** `tools/gen_mechanics.py` (reference players per class →
per path×rank), `static/site/mechanics.js` (sim class dropdown →
path + rank inputs), mechanics legend.

**Acceptance (the trace lint, T7):** outside migration code and
legacy-doc tolerance, grep for `clazz|warrior|archer|sorcerer|class`
in engine + content + rendered scene text returns nothing
player-facing. Weapon-line slugs (`line: "archer"` etc.) are
whitelisted internal IDs — renamed only if free (open question 5).

---

# PART IV — THE TEST PLAN (tests change first)

The previous rebalances (017 smoothness gate, 022-002 retune, 025
climb, 043/046 bake) own today's balance tests. They are rewritten
to assert THIS plan before the mechanics land: each phase in Part V
starts by landing its tests red, then turns them green.

## T1. New suite `test_048_the_weapon_decides.py` — the mechanics

- Triangle: every (type × path) cell of N2 exact; chip ≥1
  everywhere except blade-vs-fly = 0; TYPE_SPEED/ATK/HP/GOLD
  applied by `creature_stats`; legacy trait sets map to the right
  type.
- Ranks: miss% and roll-floor exact at every R 0–10 (seeded RNG);
  rank 5 reproduces today's `[ATK/2, ATK]`-no-miss feel; cost
  curves exact (20/57/104/…/632 XP; gold ×pillar(frontier));
  can't train past 10; XP/gold actually deducted.
- Mastery: rank 10 opens studies at 948 XP; invitation discount
  20% on other paths' ranks 1–5; studies' effects measurable.
- Gates: each N7 action opens exactly at its rank with the weapon
  slotted, for a doc that never had that class.
- Carry: 2nd slot purchasable at level 1 (60 XP + 30 ◈); 3rd slot
  refused below level 8 and rendered locked with the requirement;
  with sword+bow slotted the fight offers BOTH attack options, each
  rolling its own path's rank and triangle answer; promote-from-bag
  works in town, refused mid-fight with a reason.
- Migration: legacy archer doc → bow 6; plays without error; card
  shown once.

## T2. New suite `test_048_visible.py` — understood, not just fair

The "can I tell why?" law as assertions on rendered scenes:
- Every fight card and hunt row contains HP, ATK, DEF, SPD, and the
  sign (or "no sign") of the monster — no parameter unshown.
- The pre-fight verdict names the player's actual best answer and
  its rank.
- Every locked action's text contains the gate (`needs Bow rank 4
  (you: 2)`); the locked 3rd carry slot shows `needs level 8 —
  you: N`.
- With multiple slots, each attack option is labeled with its
  weapon, rank, and predicted damage vs THIS monster; the bag
  tooltip carries the `Hold — promote to slot` action.
- Every miss/shallow-hit line names the rank as the cause.
- **Every defeat scene names the losing cause in one sentence
  containing a lever the player owns** (weapon choice, rank, or
  run) — table-driven over: killed by armoured with bow, by fly
  with blade only, by anything at rank ≤1, plain overreach.
- School rows carry the "what improves" sentence; early kills carry
  the bounty label.

## T3. Rewrite `test_smoothness.py` — no bumps, now over three axes

The 017 gate walked floors per CLASS. It now walks:
- **Floors 1–100** per path (blade/bow/staff) at reference rank
  (6), reference gear: rounds-to-kill vs intended targets, death
  risk, income — adjacent-floor moves ≤ 40%, 5-floor trend ≤ 15%,
  band boundaries absorbed, income never cliffs (all today's caps
  kept).
- **Ranks 0→10** on fixed floors {1, 5, 10, 25, 50}: mean kill
  speed strictly improves per rank; no single rank step moves
  rounds-to-kill by more than 20% (progression felt, never a wall
  or a dead rank).
- **Weapon rungs** tier 1→10 at fixed rank: same caps — upgrades
  step smoothly, no rung is a spike or a dud.
- Every type is SOMEONE's intended target on its floor: for each
  floor, each of the three paths has ≥1 monster it answers at ×1.0
  (no floor strands a path).

## T4. Rewrite the pace/economy gates (022-002 retune, 043/046 bake)

- Level≈floor law with the new sink: a one-path climber (trains
  main path on schedule, `XP_PER_KILL_SLOPE` 3.0) still lands
  level ≈ floor ±1 through the tower.
- **Rank-10 lands ≈ player level 10**: cumulative XP at level 10
  covers body levels + one path to 10 (assert within ±15%).
- Tri-path spread is slower: a sim climber splitting XP across all
  three paths trails the one-path climber by ≥3 body levels at
  equal kills by mid-tower — and never bricks (still climbs).
- Young-tower bounty: coin mult exact at floors 1/5/10/11; a
  floor-1→10 sim can afford basic bow + staff (◈120) + first two
  ranks of each path before floor 10 without farming.
- `test_022_002_retune` keeps its era/warden/cap laws — reruns
  against the new slope; thresholds re-anchored in the bake.

## T5. Progression-feel suite `test_048_progression.py` (new)

Scripted sim playthroughs (engine-level, seeded):
- "The intended first ten floors": buy bow at ~3, learn the 2nd
  carry slot, buy staff at ~5, train to 2/2/2 — every floor-1–10
  monster of every type is answerable by a SLOTTED weapon; no
  fight is a wall.
- "The specialist": blade-only to rank 10 by ~level 10 — mastery
  reached, invitation card fires.
- "Wrong-weapon lesson": bow-only climber meets armoured — loses
  or runs, defeat text names the staff/steel answer (ties into T2).

## T6. Sweep of the ~55 existing test files that build class docs

`conftest.py` helpers (`create_character(clazz=…)`, `fresh`) are
THE chokepoint — they change to build a climber + `training` dict
(param: which path pre-trained, default blade 6 ≈ old warrior).
Then, by group:
- **Die:** `test_017_offclass_migration.py` (off-class system gone
  — replaced by T1 migration cases), off-class racks in
  `test_017_shops.py`, class-gate cases in `test_037_sleep.py` /
  `test_036_gap_and_grants.py` (reborn as rank-gate cases in T1).
- **Rewrite meaning:** `test_017_damage_types.py` → triangle;
  `test_017_characters.py` → creation without the class question;
  `test_smoothness.py` per T3; retune per T4.
- **Mechanical sweep** (clazz kwarg → training kwarg, expected
  texts): the ~45 remaining files. Grep-driven; no meaning change.
- Dojo `.md` checklists under `tests/0*` referencing classes get a
  one-line deprecation note pointing at 048 (history, not deleted).

## T7. The trace lint `test_048_no_classes.py` (new)

- Engine grep (AST-level where sensible): no `clazz` reads outside
  `state.py` legacy-tolerance + migration; `CLASSES`,
  `OFF_CLASS_*`, `class_starter` do not exist.
- Rendered-text sweep: creation flow, town, shops, fight cards,
  tips, sheet — the words warrior/archer/sorcerer/class appear
  nowhere player-facing (weapon-line slugs whitelisted as internal
  IDs).
- Schema: creature traits accept only the four types (+ `bulwark`);
  legacy traits rejected by the content linter after phase 7.

---

# PART V — PHASES (tests first, each lands green, branch-only)

All work stays on branch `048-the-weapon-decides` (plugin + outer
repo). Tests run with the worldd venv per the release flow. Each
phase = one commit; the game is playable after every one. **Within
every phase: land the phase's tests first (red), then the code
(green).** No deploy without roy's explicit word.

## Phase 1 — conftest + the triangle

T6's conftest chokepoint (helpers grow the `training` shape while
still writing `clazz` for the legacy engine); T1 triangle tests;
then `TYPE_*` tables, `type_from_traits`, new
`typed_damage(path, …)` alongside the old one. Nothing
player-visible changes.

**Green =** T1 triangle cases + full existing suite.

## Phase 2 — trained ranks in the swing + migration

T1 rank/migration tests; then `p["training"]` (blade 2 default),
`TRAIN_MISS_PCT`/`TRAIN_ROLL_FLOOR` in `_player_hit` keyed to the
held weapon's line, migration grant (old class path → 6). Classes
still gate actions — only the roll changes; rank 6 ≈ old feel so
live players feel no nerf.

**Green =** T1 ranks/migration + suite (sweep fallout from T6
mechanical group as it surfaces).

## Phase 3 — the School + mastery

T1 school/mastery/carry tests; then the School scene, train flow
(XP+gold, refusals, "what improves" lines), rank-10 gold bar,
mastery studies, invitation + discount, carry slots (2nd at level
1, 3rd locked to level 8) + the slots field and promote-from-bag
UI on the sheet.

**Green =** T1 complete; T2 school assertions.

## Phase 4 — classes die

T7 trace lint (red), T1 gate cases; then: creation drops the class
question; everyone starts Rusted Sword + blade 2; armory sells all
lines (`OFF_CLASS_*` deleted); basic bow/staff at ◈60; action
gates flip to slotted-weapon+rank; per-slot attack options;
sheet/pane/profile show the three bars + HOLDING row;
tips/contracts reworded. The big T6 sweep lands here.

**Green =** T7 (engine part), T1 gates, swept suite.

## Phase 5 — monsters switch to types + total visibility

T2 (red), T3 floor-walk rewrite; then `typed_damage` flip, full
stat lines + signs on every card, verdicts, defeat-cause
sentences, blade-vs-fly run truth, `TYPE_GOLD`.

**Green =** T2, T3 floor axis, suite.

## Phase 6 — the balance bake

T3 rank/rung axes + T4 + T5 (red); then `XP_PER_KILL_SLOPE` → 3.0,
`early_coin_mult` + bounty label, anchor tuning until every T3/T4
gate holds (this is the bake — anchors in N3/N8 are the starting
guess, the tests are the law).

**Green =** T3, T4, T5 in full.

## Phase 7 — content retag + mechanics page

Retag 425 monsters' YAML to the four types (script + banded diff
review); schema linter rejects legacy traits (T7 schema part);
gen_mechanics per path×rank + TRAINING tab; simulator rank input;
cache-bust.

**Green =** T7 complete; every floor 1–10 spawns all three signs;
regenerated mechanics-data.

## Phase 8 — polish + hand playtest

Teaching texts everywhere, School door line, migration card,
banner-hall mastery mention. Hand-play floors 1–12 per the dojo
style; production checklist. The three-question audit on one
monster of each type at ranks 0/5/10.

---

# THE AUDIT

- **Can I lose?** Wrong weapon or untrained hand against a signed
  type is a visible, felt loss (or a forced run).
- **Can I tell why?** Every parameter of every monster is on the
  card; the verdict speaks in your weapons' terms; every miss names
  the hand; every DEFEAT names the cause and a lever (T2 enforces
  all of it).
- **Can I change it next time?** Train the path (School, XP+gold,
  ten visible steps), or slot the counter-weapon (armory ◈ + the
  carry skill — both attacks live in the same fight). Nothing is
  locked to a day-one choice.

## Open questions

1. Mastery studies (N4): ship the three named studies with 048, or
   ship the rank-10 gold bar + invitation first and studies in 049?
   (Plan ships all three — they are the "learn other things on that
   profession" beat.)
2. "Rank 10 ≈ level 10" is read as: ONE path maxed costs about the
   XP of body levels 1→10. If you meant all THREE paths by level
   10, the anchor drops 20 → 7 and spreading stops hurting —
   flagging because it changes the spread-is-slower principle.
3. Train-by-use (kills with the weapon drip path-XP) or
   School-only? Plan assumes School-only for legibility.
4. ~~Two-weapon carry~~ — decided: the CARRY School skill (N5) —
   2nd slot from level 1, 3rd slot expensive and level-8-gated;
   per-slot attack options replace the switch action.
5. Rename internal weapon-line slugs (`warrior/archer/sorcerer` →
   `blade/bow/staff`) — clean but touches every saved doc's gear;
   plan keeps the old slugs as whitelisted internal IDs.
