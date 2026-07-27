# 017 — Combat Depth: the full plan

Status: PLAN (numbers fixed; execution happens in the numbered phase
folders — see §7). Everything here derives from
[pre_plan.md](./pre_plan.md) (all open questions resolved 2026-07-27)
and the two research docs
([kingdom-rush.md](../../vision/kingdom-rush.md),
[minecraft-items.md](../../vision/minecraft-items.md)).

Grounding: every "today" fact below was read from the live engine
(`economy.py`, `engine/combat.py`, `engine/state.py`, `engine/core.py`,
`content/schema.py`, 100 floor YAMLs) on 2026-07-27.

---

## 1. Scope in one paragraph

Three professions become three damage types (melee / ranged / magic).
Every monster gets a readable defense profile (armor tier, magic
resistance tier, flying, bulk, **speed**) shown on a new **[i] card**
with an always-on HP bar. Combat gains a two-state range model (at
range / close) that makes speed real: kiting, fleeing, chasing, and a
small log-decay dodge. The economy grows second forge rungs, a shoes
ladder, a mage shop (Arcanum), off-class stopgap gear, durability with
Forge repairs, a relic catalog (one dramatic effect + one hard
limitation, every time), a rebuilt death penalty (random gold+weapon
loss, cancellable by the Weapon Reincarnation Spell), variable pawn
pricing, and faction armory donations. Halflings migrate to the closest
race; dwarves become giants in all art; kill FX gain per-damage-type
variants (floors 1–3 first). Complexity arrives one rule per floor —
floor 1 stays exactly as simple as today.

## 2. Combat: damage types, profiles, and the chase

### 2.1 Player damage types

| Class | Type | Basic weapon (new, tier 0, indestructible, free) | Notes |
|---|---|---|---|
| warrior | **melee** | Rusted Sword (+5 ATK — the renamed Rusted Shiv) | today's FORGE weapon ladder becomes the warrior line |
| archer | **ranged** | Basic Bow (+5 ATK, basic arrows infinite) | new bow ladder, same price/bonus shape |
| sorcerer | **magic** | Worn Wooden Staff (+5 ATK) | new staff ladder in the Arcanum; spell damage ignores DEF |

- ATK formula unchanged: `3·level + weapon_bonus (+hone)`.
- **Magic ignores the monster's flat DEF entirely** (`raw` applies in
  full) but is cut by the resist tier. Melee/ranged keep today's
  `raw − DEF/2` and are additionally cut by the armor tier.
- Creation grants the class basic weapon (doc migration gives existing
  players theirs, §6).

### 2.2 Monster defense profiles

Content grows new qualitative traits (schema `ALLOWED_TRAITS`); the
engine prices them in `economy.py` — content never carries numbers.

| Trait | Effect (multiplies FINAL damage of the cut type) |
|---|---|
| `armor_low` / `armor_med` / `armor_high` | physical (melee+ranged) damage ×0.75 / ×0.50 / ×0.25 |
| `resist_low` / `resist_med` / `resist_high` | magic damage ×0.75 / ×0.50 / ×0.25 |
| `flying` | melee damage = **0** (cannot hit) without a Sky-hook; ranged/magic unaffected |
| `bulwark` | HP ×2.2 and +1 armor tier — the outlast-you enemy |
| `slow` / `fast` | speed 3 / 7 on the 1–10 scale (default 5, §2.4) |

- Named tiers in all UI: None / Low / Medium / High (Great/Immune
  reserved for scripted encounters, not authorable).
- **Minimum-damage rule preserved:** any type that CAN hit always chips
  ≥1 (the 013 lesson — never silently zero). Melee-vs-flying is the one
  legal zero, and the card says why.
- Legacy `armored` trait: content-migrated to `armor_med` (floor-1
  goblin gets it *removed* — kindergarten rule); the old ×1.25/×1.5
  stat multipliers are retired in favor of the tier system. The
  `ARMORED_GOLD_MULT` pay-bump generalizes: **any profile trait bumps
  gold** (armor/resist tiers ×1.1/×1.25/×1.4, flying ×1.2, bulwark
  ×1.5) so hard monsters stay worth diagnosing.
- Wardens: `armor_low` + `resist_low` from band 3 (floor 21+);
  milestones get `armor_med` + `resist_med` + bulwark HP. Bosses are
  damage checks; regular monsters stay knowledge checks.

### 2.3 The intro staircase (one rule per floor)

Floor 1: plain profiles only ("take the full attack given"). First
`armor_*` monster: floor 2. First `resist_*`: floor 3. First `flying`:
floor 4. First `fast`: floor 5. First `bulwark`: floor 6. The floor
that introduces a rule carries exactly one monster using it.

### 2.4 Speed and the two-state range model

Speed scale 1–10. Monsters: slow 3 / normal 5 / fast 7 (alphas +1).
Player: base 5 + shoes bonus (§3.3).

- **Fights open `at_range`** (new `encounter["range"]` field).
- At range: bow/spells hit at full strength; **melee cannot attack**
  (new option: *Close in* — always succeeds, costs the round, monster
  hits at −50% while you cross). Monster attacks at −50% while at range
  (it is charging, not fighting).
- End of every at-range round the monster closes with
  `p_close = clamp(0.25 + 0.15·(mspd − pspd), 0.05, 0.95)`.
- Close quarters: bow damage ×0.6; melee/magic full.
- **Open distance** (new option, archers' bread and butter):
  `p = clamp(0.50 + 0.15·(pspd − mspd), 0.05, 0.90)`; costs the round;
  on failure the monster gets a free halved hit.
- **Flee** replaces today's flat 60%:
  `p_flee = clamp(0.60 + 0.12·(pspd − mspd), 0.10, 0.95)` — you can
  walk away from the slow, you cannot outrun the wolf without shoes.
- **Dodge (log decay, the "no hidden hack" rule):** with speed
  advantage `a = max(0, pspd − mspd)`:
  `dodge% = min(12, round(7 · log2(1 + a)))` → a=1: 7%, a=2: 11%,
  a=3+: 12% cap. Applies to every incoming hit (physical and magic).
  Armor/resist stay the primary defenses by construction.
- Speed appears on the [i] card as a named tier (Slow/Normal/Fast).

### 2.5 Class ability adjustments

- Treeline shot: unchanged, but the armor-tier system replaces the
  special-cased `armored` nullification (vs `armor_med+` the double is
  lost — same feel, general rule).
- Shield wall: unchanged; vs `flying` the counter deals 0 (can't reach).
- Sleep spell: monsters with `resist_high` are immune (the card and the
  refusal note say so) — the mage's own counter-pressure.

## 3. Economy: shops, gear, durability, relics, death

### 3.1 Forge second rungs (and the three weapon lines)

Between every tier T and T+1, a mid rung **T.5**:
`bonus(T.5) = midpoint`, `price(T.5) = round(√(price_T · price_T+1))`
(geometric — keeps days-to-afford smooth). Weapons exist in three
class lines (warrior blades = today's names; archer bows and sorcerer
staves get new names, same numbers). Shields serve warrior+archer;
focuses (Arcanum) serve sorcerers; armor is shared. Tier-1..2 example
(full 60-row table generated in phase 004):

| Rung | Warrior | Archer | Sorcerer (Arcanum) | +ATK | Price |
|---|---|---|---|---|---|
| 1 | Pigsticker | Ashwood Bow | Tallowwood Staff | 8 | 250 |
| 1.5 | Iron Sword | Sinew-Backed Bow | Coalglass Staff | 12 | 450 |
| 2 | Wolfbite | Wolfsight Recurve | Stormtwig Staff | 16 | 800 |
| 2.5 | Bloodgroove Falchion | Horncore Bow | Embervein Staff | 20 | 2,280 |

- Gear level gates: rung T at `band_start(T)` (today's rule); rung T.5
  at `band_start(T) + 5`.
- **The next locked rung is always visible** in every shop, greyed with
  "🔒 <name> — level N" (mirrors the locked-buildings roadmap).

### 3.2 Off-class stopgap gear

Any class can buy the previous-rung weapon of another line at **×3
price**; it deals **×0.5 damage**, **misses 25%** of the time (the miss
consumes the round; the monster answers), never hones, and bow use by
non-archers consumes bought arrows (10 per ◈-pack). It exists to break
a hard counter, not to build around.

### 3.3 Shoes (the speed ladder)

New gear slot `shoes` (Forge). Five rungs; speed bonus feeds §2.4 (and
the log-decay dodge keeps stacking honest):

| Rung | Name | +spd | Price | Level |
|---|---|---|---|---|
| 1 | Cobbled Boots | +1 | 500 | 3 |
| 2 | Wayfarer's Treads | +2 | 3,500 | 11 |
| 3 | Chasewind Boots | +3 | 24,000 | 21 |
| 4 | Skyline Striders | +4 | 120,000 | 41 |
| 5 | Stormstep Greaves | +5 | 400,000 | 61 |

Shoes are paid gear: they have durability (wear on flee/open-distance/
close-in actions) and sit in the death-loss pool like weapons.

### 3.4 The Arcanum

New town building, unlocks at **level 6** (locked row before that).
Sells the staff line, focuses (shield-slot equivalent, sorcerer-only),
and the mage relics (strip potion, curse scroll, polymorph dust).

### 3.5 Durability

- Every **paid** weapon/shield/armor/shoe carries `uses` (int).
  Pool by tier: `pool(T) = round(240 / (1 + 0.3·(T−1)))` → T1 240,
  T5 109, T10 65 — **better gear wears faster**, in uses not just rate.
- Wear: weapon −1 per player attack; shield/armor −1 per hit taken;
  shoes −1 per chase action (flee/open/close). Basic (tier-0) gear
  never wears.
- At 0: **broken**, not gone — bonus halved until repaired; the basic
  weapon is always there underneath.
- **Repair at the Forge: 20% of item price × missing fraction, plus
  `hone_xp(frontier)` XP** (a few XP — joins the existing XP sinks).
- UI: durability bar under the equipped item (pane sheet + [i]-style
  hover: "90% — repair at the Forge").
- **Staged onboarding:** durability activates per-slot the first time
  a player buys a paid item for it; the purchase scene teaches it in
  one line.

### 3.6 Death economy (decided rule)

Unchanged: daily `death_save` shard rescue; mercy at level ≤ 3 (half
gold, nothing else); banked gold always safe.

New, for level > 3 (replaces "all gold + armor/shield destroyed"):

- **Random gold loss:** 40–60% of carried gold (rng roll).
- **Random weapon loss:** every paid weapon (equipped or packed, any
  line) independently rolls **20%: gone for good**. Armor/shield/shoes
  are never destroyed by death anymore — they take a −50% durability
  hit instead (the repair economy absorbs what destruction used to).
- **Weapon Reincarnation Spell** (relic, §3.7): if held, one is
  consumed — **no gold loss, no weapon loss, and every weapon + armor
  piece repairs to full**. The ONLY thing a protected death can still
  take: each SPARE Reincarnation Spell rolls 50% lost. One is safe;
  a hoard leaks. (Roy's clarified rule.)

### 3.7 Relic catalog v1

Law: **one dramatic effect + one hard limitation; no permanent stats.**
Prices anchor to `daily_income(frontier)` (DI). Sold where noted;
introduced band by band (lint enforces the schedule).

| Relic | Effect | Limitation | Price | From |
|---|---|---|---|---|
| Quiver: Poisoned arrows ×5 | true damage over 3 rounds, ignores armor tiers | no-stack; some monsters immune | 0.3 DI | floor 6 |
| Quiver: Slowing arrows ×5 | target −2 speed for the fight | wears off; useless vs `slow` | 0.3 DI | floor 8 |
| Quiver: Piercing arrows ×5 | ignore armor tier on the shot | tiny count, archer-only | 0.5 DI | band 2 |
| Quiver: Fire arrows ×5 | +50% burst; ends regen effects | weak vs armor tiers (physical) | 0.3 DI | band 2 |
| Weapon oil | next 10 strikes +25% (physical weapons, any class, 100% reliable) | 10 strikes, then gone | 0.2 DI | floor 6 |
| Entangling net (warrior) | monster loses its round; can't close or flee through it | 3 per pack; never on Wardens | 0.25 DI | band 2 |
| Sky-hook (warrior) | melee can hit `flying` | −1 use per fight, 5 uses | 0.4 DI | band 2 (first flyer band) |
| Resistance-strip potion (mage) | removes resist tier for the fight | one fight | 0.3 DI | Arcanum |
| Curse scroll (mage) | halves armor tier for the fight (KR Sorcerer curse) | one fight | 0.3 DI | Arcanum |
| Polymorph dust (mage) | non-Warden monster becomes a harmless critter — fight skipped | **no loot, no XP**; one use | 1.2 DI | Arcanum band 3 |
| Veil Draught | untargetable until your first attack | one fight; timed | 0.5 DI | band 3 |
| Golden Apple | 2× HP overshield + all damage halved | one fight; overshield decays | 0.8 DI | band 3 |
| Weapon Reincarnation Spell | death takes nothing + full repair (§3.6) | consumed; spares leak 50% on a protected death | 1.0 DI | band 2 |
| Stone of Undying | cancels the death itself — stand up mid-fight | revive at 30% HP; **hold exactly 1**; consumed | 1.5 DI | band 3 |
| Severing Word | instakill any non-Warden monster | one use; **hold exactly 1** | 8 DI | band 4 |

Exclusivity: Stone / Apple / Veil — only one life-insurance active per
fight. Relics live in the pack, sell at the pawn, donate to the armory.

### 3.8 Faucet tightening + pawn + armory

- Alpha spoils: luck charm 30% → **10%** (medgel 90%).
- Warden rare loot: charm 40% → **15%** (tonic 85%).
- **Pawn variable rate:** deterministic from `world_day` seed, uniform
  **25–55%** (today flat 40%), shown in the shop ("the broker pays 32%
  today"); worn gear pays × its durability fraction. Pawn **always
  buys anything** — including relics.
- **Faction armory** (worldd): deposit gear/relics instead of selling;
  any member takes it (015 desk gets an ARMORY section; HMAC endpoints
  mirror the ledger's).

## 4. Readability: the [i] card and town

- **[i] badge** top-right on the enemy image (057 card-action plumbing).
  Opens the dossier: **enemy HP bar (always, round 1)**, armor tier,
  resist tier, flying flag, speed tier, 1–2 lore lines.
- New optional content field `lore:` per encounter (≤160 chars, linted).
- Scout keeps value: exact numbers + the monster's next intent.
- Icons: **1-bit, 16×16** (card stat rows, durability, tier shields),
  **32×32** (shop rows) — extends `icons.py`, consistent with the
  existing aesthetic.
- Town: locked rows with unlock levels (Arcanum L6, Relay, Fields…);
  **Tower Gate moves to the top** as "The Tower Gate — leave town and
  climb".

## 5. Agent beat (the one that remains)

First time a player fights a monster whose profile hard-counters them
(e.g. melee vs flying, mage vs resist_high), fire ONE moment nudge
(per monster type, flag-tracked) — that is exactly when a sidekick tip
has value. No other messaging changes (0.17.2 silence stays).

## 6. Content, art, and migration

- **Bestiary:** floors grow to 4–5 encounters with a lint-enforced
  spread: within every band ≥1 good target and ≥1 bad target per class,
  ≥1 fast and ≥1 slow monster. Floors 1–10 retrofit by hand in phase
  001/002; 11–100 in batches (phase 008).
- **Races:** halfling removed from creation; **automatic migration to
  the closest race** (default human) via `ensure_current` doc upgrade +
  a pending-event letter in-world. Dwarf giant lore (story.md, already
  canon) flows into all new art prompts.
- **Movies/FX:** intro movie regenerated with the three showcase
  characters (male elf archer, female human warrior, giant dwarf
  wizard); kill FX gain melee/arrow/magic variants for floors 1–3
  monsters first.
- **Doc migration (version 1 → 2)** in `ensure_current`: add
  `gear.shoes`, `durability` map, class basic weapon
  (archer→basic_bow, sorcerer→worn_staff, warrior keeps rusted_shiv
  renamed Rusted Sword), race conversion, `relics`/quiver inventory
  namespace, encounter field defaults. Lazy, idempotent, on any
  backend (local + worldd) — the existing pattern.
- **worldd:** no SQL migrations needed (JSONB docs); every phase ends
  with `vendor_game.sh` sync + deploy. Faction armory (phase 007) adds
  worldd endpoints + one table migration.

## 7. Testing strategy (every phase must pass)

1. **pytest** unit + scenario tests per phase (the suite is at 190).
2. **Sim gates** (extend the existing pattern): matchup sim (each class
   at-level beats its intended victims ≥80%, hard-countered fights won
   <30% or 2× longer), chase sim (kiting/flee curves within ±5% of
   spec), economy sim (repairs ≤20% of reference income; death loss
   expectation within spec; relic prices vs DI anchors).
3. **Difficulty smoothness gate (no bumps, no step functions):** a
   full-playthrough sim (`tests/test_smoothness.py`, lands in phase 001
   and grows with every phase) walks the at-level reference player of
   each class floor 1 → 100 and records, per floor: rounds-to-kill vs
   the floor's intended targets, death risk per fight, net income per
   energy, and days-to-next-purchase. Gate asserts:
   - adjacent-floor delta of every metric ≤ 25% (no cliffs);
   - band boundaries (10→11, 20→21, …) obey the SAME cap — tier jumps
     must be absorbed by the mid rungs, not felt as walls;
   - metrics are trend-monotone (smoothed slope never flips sign for
     >2 consecutive floors) so difficulty climbs, dips never spike.
   Every economy-touching phase must leave this gate green.
4. **Content lint** (`lint_floors` + new spread/lore/trait rules) stays
   a CI gate.
5. **Dojo browser test** per phase: real conversation + pane clicks
   against a local Luna, DOM timeline + screenshots (run-dojo skill) —
   the screen is read with eyes, not assumed from code.
6. Ship: version bump, marketplace publish, worldd vendor sync +
   Render deploy, `execution_summary.md` per phase.
7. **Phase retrospective (devprocess §7):** after each summary, re-read
   and amend ALL remaining phase plans with what the phase taught
   (date-stamped `> retro(NNN):` notes) before starting the next.

## 8. Phase index (folders in this directory)

| Phase | Folder | Ships |
|---|---|---|
| 001 | `001-damage-types/` | damage types, defense profiles, tier math, intro staircase, floors 1–10 retrofit |
| 002 | `002-speed-and-chase/` | speed axis, range states, kiting/flee/dodge, chase sim |
| 003 | `003-enemy-info-card/` | [i] dossier, HP bar, 1-bit stat icons, lore field, scout intent |
| 004 | `004-shops-and-gear/` | second rungs, bow/staff lines, shoes, Arcanum, locked rows, off-class gear |
| 005 | `005-durability/` | wear, broken state, Forge repair, bars, staged onboarding |
| 006 | `006-death-and-relics/` | new death economy, Reincarnation Spell, relic catalog v1, faucet cuts, variable pawn |
| 007 | `007-world-and-agent/` | faction armory (worldd), matchup moment, town locks + gate copy |
| 008 | `008-bestiary-at-scale/` | floors 11–100 profiles, 4–5 encounters/floor, monster art batch |
| 009 | `009-characters-and-movies/` | race migration, giant-dwarf art, intro movie, kill-FX ×3 (floors 1–3) |
| 010 | `010-balance-and-release/` | full-economy retune pass, shared-world migration check, dojo playtest, release |

Order rationale: 001→002 build the engine truth; 003 makes it visible
(nothing ships player-facing before it's readable); 004–006 build the
economy on the new combat; 007–009 are parallel-friendly; 010 gates
the whole overhaul. Art (009) can start any time after 001 fixes the
bestiary names.
