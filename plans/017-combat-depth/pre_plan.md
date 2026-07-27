# 017 — Combat Depth: pre-plan

Status: PRE-PLAN (detailed explanation + design decisions; the actionable
task breakdown follows in `plan.md` after review)

Inputs:
- Roy's brief, 2026-07-27 (verbatim ideas reorganized below)
- Current-mechanics digest (live `economy.py` / `combat.py` / `core.py` /
  `routes.py` — see "what exists today" notes inline)
- **[vision/kingdom-rush.md](../../vision/kingdom-rush.md)** — the design
  reference for the counter system. One sentence version: *depth comes
  from a few orthogonal, readable, named rules with intended counters —
  never from stat inflation.*

---

## 0. The one-paragraph summary

Today every class fights the same way (one shared damage formula, one
`armored` trait, one intended answer: attack). This overhaul makes the
three professions three genuinely different **damage types** (melee /
ranged / magic), gives every monster a readable **defense profile**
(armor tier, magic-resistance tier, flying flag, HP bulk), and rebuilds
the economy around that triangle: deeper forge ladders, a mage shop,
scarce off-class counter-gear, and equipment **durability**. The player's
new core skill is *diagnosis* — read the enemy card, decide fight or
flee, buy the right counter. Everything arrives staged so floor 1 plays
exactly as simply as it does now.

---

## 1. Professions become real (damage types)

**Today:** classes are option decks only (warrior `shield_wall`,
sorcerer `sleep_spell`, archer `treeline_shot`); everyone's ATK is
`3×level + weapon`; everyone starts with the same Rusted Shiv.

**Target:**

| Class | Damage type | Basic weapon (infinite, can't break) | Signature |
|---|---|---|---|
| Warrior | **Melee** (physical) | Rusted Sword | strongest raw hits, shield wall |
| Archer | **Ranged** (physical) | Basic Bow (basic arrows never run out) | hits flyers, treeline shot |
| Mage | **Magic** | Worn Wooden Staff | ignores armor, spell scales with level |

Rules from the brief, made precise:

1. **You start as your profession.** Archer creation grants the bow (not
   a shiv); mage the staff. Warriors unchanged.
2. **The basic weapon is a floor, not a phase.** It never degrades, never
   runs out, is never lost on death. You can always fight *somehow*.
3. **Your own path is the best path.** Class weapons scale with level for
   free (mage spells "as powerful as their level", warrior melee, archer
   basic arrows) — off-class gear never scales.
4. **Off-class capability is purchasable but bad**: a warrior can buy a
   bow — it costs a lot, does little damage (they're terrible shots:
   damage penalty + they eat the monster's counter more often), takes a
   pack slot, and its arrows deplete. Same for an archer swinging a
   sword, a mage doing either. This is deliberately a *stopgap tool*, not
   a build.

## 2. Monster defense profiles (the Kingdom Rush triangle)

**Today:** monsters have ATK/DEF/HP from a floor formula and at most the
`armored` trait (×1.25/×1.5/×1.25 multipliers, kills archer's double).
Exactly 3 wild encounters per floor.

**Target:** every encounter gets a **defense profile**:

| Axis | Values | Effect |
|---|---|---|
| **Armor** | None / Low / Med / High / Great (named tiers, % under the hood) | cuts **physical** damage (melee AND ranged) |
| **Magic resistance** | same tiers | cuts **magic** damage |
| **Flying** | yes/no | melee **cannot hit at all** without special gear; ranged/magic unaffected |
| **Bulk** | normal / bulwark | bulwark = big HP+armor pool that outlasts slow damage — the "wear you down" enemy |

Design constraints (straight from KR, see the research doc):

- **Orthogonal, almost never both.** A regular monster is strong against
  one damage type, weak to another. Only **Wardens/bosses get all three**
  (big HP + some armor + some magic resistance) — bosses are damage
  checks, regular monsters are knowledge checks.
- **Every monster has an intended counter** — and therefore an intended
  *victim*: the armored knight shrugs off arrows but melts to spells; the
  spell-eater walks through magic but dies to steel; the flyer is
  archer/mage food; the bulwark rewards burst (or a group).
- **Running is a strategy, not a failure.** The expected experience: on a
  new floor you fight the monsters that suit you and *run from the ones
  that don't* — until levels/gear/consumables let you clear the whole
  bestiary. (Run mechanics may need a small buff: telegraph the matchup
  before commit via the info card, ¶4.)
- **More variety per floor**: grow from 3 wilds to ~4–5 with a deliberate
  matchup spread (at least one good target and one bad target for every
  class on every floor band).
- The old `armored` trait is superseded by the armor tier.

**Floor 1 stays kindergarten:** zero armor, zero resistance, nothing
flies — "take the full attack given". First armored monster, first
resistant monster, and first flyer each get their own introduction floor
(one new rule at a time, the KR campaign lesson).

## 3. Forge, mage shop, and the second rung

**Today:** one gear row per 10-floor band (Pigsticker +8 @250 → Wolfbite
+16 @800 at level 11 …), shop shows only the current tier, apothecary
sells 6 items, pawn buys pack gear at flat 40%.

**Target:**

1. **Two rungs per band.** Between every existing tier and the next, an
   intermediate weapon/shield/armor rung (the brief's example: Pig shiv
   250/+8 → **Iron Sword 1,250/+10**). Numbers get fixed in plan.md, but
   the shape is: rung B costs ~4–5× rung A for ~+20–25% power, so there's
   always a *reachable* upgrade and an *aspirational* one within a band.
2. **The Forge serves warriors and archers** (blades, bows, arrows,
   armor). **A new Arcanum (mage shop)** sells mage-only gear — staves
   and focuses only a sorcerer can own — and unlocks by player level
   (locked-door UI until then, ¶7).
3. **Counter-consumables** (the strategic money sink, all heavily
   degradable/limited):
   - *Magic-piercing arrows* — expensive, come in 5s; let an archer break
     bulwarks/armored (physical-resistant no, armored yes — exact matrix
     in plan.md).
   - *Resistance-strip potion* (mage) — temporarily removes a monster's
     magic resistance.
   - *Weapon-oil potions* (anyone) — buff warrior/archer weapons vs
     non-magic-resistant monsters; potions always work 100% when used on
     physical weapons.
   - *Sky-hook / reach weapon* (warrior) — lets melee hit flyers,
     depletes fast.
4. **Pawn shop always buys** — anything, anytime, but at a **variable
   price** (daily/randomized rate around the current 40%, worse for
   worn gear per ¶5, occasional good days). No more "must re-equip at
   forge first" friction: old gear already drops to the pack on upgrade
   (this part exists today) and the pack is sellable.
5. **Faction armory donations:** instead of selling, deposit old gear to
   your faction; any member can take it. (Builds on the 015 faction desk
   ledger.)

## 4. The enemy info card ("[i]" on the monster image)

**Today:** headline shows `Name — ATK X / DEF Y`, HP appears after the
first exchange, Scout reveals full stats. No dossier, no bars.

**Target:** an **[i] badge on the top-right of the enemy image**. The
card shows, mirroring the player's own meters:

- **Enemy HP bar** (always, from round 1),
- **Armor tier** (shield icon + named tier),
- **Magic resistance tier**,
- **Flying** flag,
- 1–2 lines of lore: what it is, where it lives, what it drops.

This is non-negotiable UI for the whole feature (the KR lesson: the
counter system is invisible noise unless the enemy's sheet is readable
in two seconds). Scout keeps value by revealing *exact* numbers and the
monster's next intent.

## 5. Durability

**Today:** none. Death destroys armor+shield; that's the only gear sink.

**Target:**

- Every **paid** weapon/armor/shield has durability. Each strike (given
  or taken, respectively) wears it down a bit; **better gear wears
  faster** (higher tiers burn durability quicker — power is a running
  cost, another KR-style tempo wager).
- **Repair at the Forge: 20% of item value in gold + a few XP.** XP-as-
  aether already exists (honing, sleep spell) — repairs join that sink.
- **UI:** a small durability bar at the bottom of the equipped item;
  hover explains ("90% durability — repair at the Forge").
- **Staged:** the starter weapon never degrades, and degradation only
  begins when you buy your **first upgrade** — the tooltip teaches the
  mechanic at the exact moment it starts existing.
- At 0% the item doesn't vanish — it's *broken* (heavy damage penalty)
  until repaired; you always still have the basic weapon (¶1.2).

## 6. Economy tightening

- **Luck charms are too free** — today: 30% of alpha kills, 40% of every
  Warden kill, present jackpots, plus buyable at ◈300. Cut the drop
  rates hard (exact numbers in plan.md) so the ◈300 purchase matters.
- "Free medals": there is **no medal system in code** — what feels like
  free medals is the Warden guaranteed-rare drop. Same fix: rarer, or
  replaced by gold/materials.
- New sinks introduced by this plan (repairs, consumables, second rungs,
  mage shop) give the tightened faucets somewhere to matter.

## 7. Staged complexity and town readability

- **Locked buildings:** non-critical town locations render as locked
  rows with the unlock level on them ("🔒 Arcanum — level 6") — the
  Arcanum, Relay/messages, Fields, and other non-day-1 areas. A locked
  row *is* the roadmap; it answers "where do I go next".
- **The gate copy:** "Tower gate" becomes clearer and moves **to the top
  of the town list**, not the bottom — suggested label: **"The Tower
  Gate — leave town and climb"** (final copy at implementation).
- Durability, counter-consumables, and off-class gear all appear in
  shops only when relevant (level/tier gates), so the day-1 town is no
  more complex than today's.

## 8. Agent messaging: stop the per-action spam

**Today (verified in `routes.py`):** *every* `POST /act` fires
`send_muted_message` — death/boss as a "moment" (real reaction turn),
**everything else as an "awareness" note on every single click**. That's
the token waste.

**Target:**

- **Time-based digest:** ordinary play accumulates locally; the agent
  gets one awareness message per **~5 minutes of active gameplay**
  (rolling window, only while acts are actually happening), summarizing
  what changed and inviting a *helpful* line (a tip, a warning, a read
  on the current floor's matchups).
- **Moments stay instant** for death/boss — and gain the new "you're
  fighting a hard-countered matchup" beat (first time only per monster
  type) since that's exactly when a sidekick tip has value.
- Net effect: tokens drop by an order of magnitude; the agent speaks
  when it helps.

## 9. Characters, races, and the movies

- **Races: drop halfling; keep human / elf / dwarf.** (Today halfling
  exists with a luck bonus — migrate existing halflings or grandfather
  them; decision in plan.md.)
- **Three showcase characters** carried consistently through all art
  (intro movie, creation, endings):
  - male **elf** (brief says warrior — see open question 1),
  - old, strong-bodied, large **dwarf wizard**,
  - **female human warrior**, strong build.
- **Intro movie:** the refugee/climber scenes show these three (today's
  art is anonymous silhouettes — those scenes get re-generated).
- **Kill/ending FX:** each monster death gets **3 variants — melee kill,
  arrow kill, magic kill** — matching how it actually died. (Today: one
  generic kill GIF per early monster.) Art pipeline cost is the main
  driver here; see open question 3.

## 10. What this deliberately does NOT touch

- Energy pacing, bank, lodge, presents, PvP fields, factions structure,
  world Wardens/quorum flow, XP-as-purchased-levels (Guildhall) — all
  stay as shipped.
- The 056/057 card UI plumbing (standalone cards, click actions) — this
  plan builds *on* it, especially for the [i] card.

---

## Open questions (answer before plan.md)

1. **The elf showcase is listed as a warrior** — but then no archer
   appears among the three showcase characters, and two of three are
   warriors. Recommendation: make the elf the **archer** (bow iconography
   reads instantly, elves=bows is genre-native), keeping dwarf=wizard,
   human female=warrior — one character per profession.
2. **Existing players** on the shared world: halfling players and
   everyone's current single-rung gear must migrate. Proposal:
   grandfather halflings (race stays, no new creations), map existing
   gear to nearest new rung at full durability.
3. **Kill-FX ×3 variants** multiply the art budget (~5 monsters × 3 =
   15 GIFs for the early floors alone, more as floors get variety). OK
   to stage: floors 1–3 first, rest generated per content batch?
4. **Degradation on death:** today death destroys armor+shield outright.
   With durability in play, is death = destroy (as now), or death = heavy
   durability hit (softer, since repairs cost gold+XP)? Recommendation:
   heavy durability hit at L≤3 (mercy), destroy above — keeps death
   scary without double-punishing the new repair economy.
5. **The 5-minute agent digest** — flat 5 minutes, or beat-aligned
   (digest fires at natural pauses: back-in-town, floor change, out of
   energy)? Recommendation: whichever comes first, min 5 minutes between.

## Numbers to fix in plan.md (with the balance model)

- Full two-rung forge table (30 rows → 60) + Arcanum table.
- Armor/resistance tier percentages per named tier (proposal: 0 / 25 /
  50 / 75 / 90, Immune reserved for scripted encounters).
- Durability pools per tier, wear per strike, break threshold, repair
  XP amounts.
- Consumable prices/quantities (piercing arrows ×5, strip potion, oils,
  sky-hook) and their exact effect matrix vs the defense axes.
- Per-floor bestiary size (4–5) and the matchup spread guarantee.
- Charm/rare drop-rate cuts.
- Off-class purchase prices + miss/damage penalties.

## Suggested phasing (preview of plan.md)

1. **Engine: damage types + defense profiles** (schema, combat math,
   `armored` migration) + floor-1..N content retrofit.
2. **Enemy [i] card + enemy HP bar** (render + pane).
3. **Forge second rungs + Arcanum + consumables + pawn variable pricing
   + faction donations.**
4. **Durability** (state, wear, repair, bar UI, staged onboarding).
5. **Agent digest throttle** (routes.py rework).
6. **Town lock UI + gate copy/reorder.**
7. **Races/characters + movie & kill-FX art batch.**
8. **Economy retune + shared-world migration + playtest.**
