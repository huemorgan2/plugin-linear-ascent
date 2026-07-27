# 017 — Combat Depth: pre-plan

Status: PRE-PLAN (detailed explanation + design decisions; the actionable
task breakdown follows in `plan.md` after review)

Inputs:
- Roy's brief, 2026-07-27 (verbatim ideas reorganized below)
- Roy's addendum, 2026-07-27 evening: speed & archer range, shop next-tier
  visibility, icon constraints, the limited-upgrade catalog
- Current-mechanics digest (live `economy.py` / `combat.py` / `core.py` /
  `routes.py` — see "what exists today" notes inline)
- **[vision/kingdom-rush.md](../../vision/kingdom-rush.md)** — the design
  reference for the counter system, named weapon abilities, and the
  consumable shop. One sentence version: *depth comes from a few
  orthogonal, readable, named rules with intended counters — never from
  stat inflation.*
- **[vision/minecraft-items.md](../../vision/minecraft-items.md)** — the
  design reference for relics and limited upgrades. One sentence
  version: *one dramatic effect + one hard limitation, every time.*

---

## 0. The one-paragraph summary

Today every class fights the same way (one shared damage formula, one
`armored` trait, one intended answer: attack). This overhaul makes the
three professions three genuinely different **damage types** (melee /
ranged / magic), gives every monster a readable **defense profile**
(armor tier, magic-resistance tier, flying flag, HP bulk — plus a
**speed tier** that governs chases, kiting, and escapes), and rebuilds
the economy around that triangle: deeper forge ladders (weapons, armor,
**shoes**), a mage shop, scarce off-class counter-gear, a catalog of
**relics & limited wonders** (every one dramatic, every one hard-
limited), and equipment **durability**. The player's new core skill is
*diagnosis* — read the enemy card, decide fight or flee, buy the right
counter. Everything arrives staged so floor 1 plays exactly as simply
as it does now.

---

## 1. Professions become real (damage types)

**Today:** classes are option decks only (warrior `shield_wall`,
sorcerer `sleep_spell`, archer `treeline_shot`); everyone's ATK is
`3×level + weapon`; everyone starts with the same Rusted Shiv.

**Target:**

| Class | Damage type | Basic weapon (infinite, can't break) | Signature |
|---|---|---|---|
| Warrior | **Melee** (physical) | Rusted Sword | strongest raw hits, shield wall |
| Archer | **Ranged** (physical) | Basic Bow (basic arrows never run out) | hits flyers, fights at range, treeline shot |
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
| **Speed** | Slow / Normal / Fast (named tiers) | governs the chase: kiting, fleeing, catching — full rules in ¶3 |

Design constraints (straight from KR, see the research doc):

- **Orthogonal, almost never both.** A regular monster is strong against
  one damage type, weak to another. Only **Wardens/bosses get all three**
  (big HP + some armor + some magic resistance) — bosses are damage
  checks, regular monsters are knowledge checks.
- **Every monster has an intended counter** — and therefore an intended
  *victim*: the armored knight shrugs off arrows but melts to spells; the
  spell-eater walks through magic but dies to steel; the flyer is
  archer/mage food; the bulwark rewards burst (or a group); the fast
  wolf punishes kiting but is made of paper.
- **Running is a strategy, not a failure.** The expected experience: on a
  new floor you fight the monsters that suit you and *run from the ones
  that don't* — until levels/gear/consumables let you clear the whole
  bestiary. (Speed makes this real math — see ¶3 — and the info card
  telegraphs the matchup before commit, ¶6.)
- **More variety per floor**: grow from 3 wilds to ~4–5 with a deliberate
  matchup spread (at least one good target and one bad target for every
  class on every floor band).
- The old `armored` trait is superseded by the armor tier.

**Floor 1 stays kindergarten:** zero armor, zero resistance, nothing
flies, everything is Normal speed — "take the full attack given". First
armored monster, first resistant monster, first flyer, and first *fast*
monster each get their own introduction floor (one new rule at a time,
the KR campaign lesson).

## 3. Speed, distance, and the chase (new axis)

**Today:** no distance model at all — every fight is an abstract
exchange; `run` is a flat roll.

**Target:** a minimal range model that makes speed matter to every
class, without turning combat into a grid game:

1. **Fights open at range.** An archer's natural game is the opening:
   at distance the bow hits at full statistical strength. Each round
   the gap closes by the **monster's speed vs the player's speed**.
   Once the monster is *close*, bows suffer a close-quarters penalty —
   the archer's job is to **keep opening distance** (a combat action:
   succeeds on speed differential, costs the round).
2. **Fast animals catch you.** A Fast monster reaches close range
   almost immediately and forecloses the kiting game; a Slow bulwark
   never catches a Normal-speed player who keeps stepping back. This is
   the archer's matchup axis the same way armor is the mage's.
3. **Speed helps everyone**:
   - *Archers*: keep range → full bow effectiveness (their core loop).
   - *Everyone vs magic/attacks*: speed contributes a dodge component —
     outrunning the fireball is a real defense (small, tiered, capped).
   - *Fleeing*: run success = speed differential, telegraphed on the
     enemy card. You can walk away from the Slow; you cannot outrun the
     wolf without better shoes.
   - *Warriors*: catching things — a fleeing enemy (or, in the Fields,
     a kiting archer) escapes a slow warrior; warriors who want to pin
     fast enemies need speed too. Speed is on every class's shopping
     list, not just the archer's.
4. **The Forge sells shoes.** New equipment slot: **footwear**, with its
   own price ladder ("better shoes that outrun faster enemies"),
   degradable like all paid gear (¶7). Shoe tiers raise the player's
   speed tier; the ladder is deliberately expensive because speed buys
   out of so many bad matchups (the Minecraft boots lesson: movement is
   gear, and it's never free).
5. **Speed is on the enemy card** (¶6) with a named tier, exactly like
   armor — the player must be able to read "Fast" and decide *don't
   kite, don't flee, kill it quick or don't start* in two seconds.

## 4. Forge, mage shop, and the second rung

**Today:** one gear row per 10-floor band (Pigsticker +8 @250 → Wolfbite
+16 @800 at level 11 …), shop shows only the current tier, apothecary
sells 6 items, pawn buys pack gear at flat 40%.

**Target:**

1. **Two rungs per band.** Between every existing tier and the next, an
   intermediate weapon/shield/armor rung (the brief's example: Pig shiv
   250/+8 → **Iron Sword 1,250/+10**). Numbers get fixed in plan.md, but
   the shape is: rung B costs ~4–5× rung A for ~+20–25% power, so there's
   always a *reachable* upgrade and an *aspirational* one within a band.
   Footwear (¶3.4) gets its own ladder alongside weapons/armor.
2. **The next tier is visible but locked.** Every shop lists the rung
   *above* the highest you can buy, greyed out with its unlock level
   ("🔒 Runeblade — level 16"). Same principle as the locked-buildings
   roadmap (¶9): the shop itself answers "what am I saving for". Applies
   to the Forge and the Arcanum both.
3. **The Forge serves warriors and archers** (blades, bows, arrows,
   armor, shoes). **A new Arcanum (mage shop)** sells mage-only gear —
   staves and focuses only a sorcerer can own — and unlocks by player
   level (locked-door UI until then, ¶9).
4. **Counter-consumables** (the strategic money sink, all heavily
   degradable/limited) — the class-counter subset of the full relic
   catalog (¶5):
   - *Magic-piercing arrows* — expensive, come in 5s; let an archer break
     armored targets (exact matrix in plan.md).
   - *Resistance-strip potion* (mage) — temporarily removes a monster's
     magic resistance.
   - *Weapon-oil potions* (anyone) — buff warrior/archer weapons vs
     non-magic-resistant monsters; potions always work 100% when used on
     physical weapons.
   - *Sky-hook / reach weapon* (warrior) — lets melee hit flyers,
     depletes fast.
5. **Pawn shop always buys** — anything, anytime, but at a **variable
   price** (daily/randomized rate around the current 40%, worse for
   worn gear per ¶7, occasional good days). No more "must re-equip at
   forge first" friction: old gear already drops to the pack on upgrade
   (this part exists today) and the pack is sellable.
6. **Faction armory donations:** instead of selling, deposit old gear to
   your faction; any member can take it. (Builds on the 015 faction desk
   ledger.)

## 5. Relics & limited wonders (the upgrade catalog)

**Today:** the apothecary's 6 items are the entire consumable game.

**Target:** a growing catalog of dramatic, memorable purchases across
all future levels — the long-term money sink and the reward for every
new floor band. The design law, straight from both research docs
(Minecraft's totem/apple/thorns, KR's shop and level-4 abilities):

> **Every relic = one dramatic effect + one hard limitation.**
> Acceptable limitations: single-use · hold-only-1 · timed · no-stack ·
> never-works-on-Wardens · burns its own durability · counted ammo ·
> either/or exclusivity. No relic grants permanent stats. Ever.

Starter catalog (from the brief + research; prices, exact numbers, and
the full list live in plan.md):

**Insurance** (the expensive top of the ladder — KR prices revival at
the very top of its shop, and so do we):

| Relic | Effect | Limitation |
|---|---|---|
| **Stone of Undying** | Death is cancelled; you stand back up mid-fight | revive at *partial* HP (not full); **hold exactly 1**; consumed on trigger |
| **Golden Apple** | 2× HP overshield + all damage halved | timed (one fight); the bonus HP decays, never heals back |
| **Thornmail** | attackers take damage every time they strike you | each reflection burns the armor's own durability |
| **Veil Draught** | monsters can't target you… | …until your first attack; one fight; timed |

**The quiver** (archer ammo types — one bow, many arrows, all counted;
the tipped-arrows lesson):

| Arrows ×5 | Effect | Limitation |
|---|---|---|
| **Poisoned** | true damage over time, ignores armor | does not stack; some monsters immune |
| **Slowing** | drops the target one speed tier (the kiting tool vs Fast monsters) | wears off; useless vs Slow |
| **Magic-piercing** | punch through armor tiers | tiny quantity, steep price |
| **Fire** | burst damage, stops regenerating enemies | weak vs armored |

**Warrior tools:** entangling net (monster loses the chase for a round —
can't close distance or flee; limited uses, never on Wardens), sky-hook
(hit flyers, depletes), weapon oils (¶4.4).

**Mage tools:** resistance-strip potion (¶4.4), **curse scroll** (halves
the target's armor — the mage's answer *borrowed from KR's Sorcerer
curse*), **polymorph dust** (turn one non-Warden monster into a harmless
critter — skip the fight, forfeit the loot).

**Ultimates** (one-per-pack, extravagant prices, the KR "Death's
Touch" slot): **Severing Word** — instantly kills any non-Warden
monster. Exists so late-game gold has somewhere legendary to go.

Rules that keep this sane:

- **Either/or exclusivity** where power concentrates (the
  Infinity-XOR-Mending lesson): only one *insurance* relic active at a
  time — Stone or Apple or Veil, pick before the fight.
- **Staged availability** (¶9): the catalog unrolls band by band; each
  new floor band's shops introduce 2–3 new relics, so there is always a
  new toy to discover and save for.
- Relics are pack items: they show in the pack, sell at the pawn
  (variable rate), and can be donated to the faction armory (¶4.6).

## 6. The enemy info card ("[i]" on the monster image)

**Today:** headline shows `Name — ATK X / DEF Y`, HP appears after the
first exchange, Scout reveals full stats. No dossier, no bars.

**Target:** an **[i] badge on the top-right of the enemy image**. The
card shows, mirroring the player's own meters:

- **Enemy HP bar** (always, from round 1),
- **Armor tier** (shield icon + named tier),
- **Magic resistance tier**,
- **Flying** flag,
- **Speed tier** (¶3 — the fight/flee/kite decision needs it),
- 1–2 lines of lore: what it is, where it lives, what it drops.

This is non-negotiable UI for the whole feature (the KR lesson: the
counter system is invisible noise unless the enemy's sheet is readable
in two seconds). Scout keeps value by revealing *exact* numbers and the
monster's next intent.

## 7. Durability

**Today:** none. Death destroys armor+shield; that's the only gear sink.

**Target:**

- Every **paid** weapon/armor/shield/shoe has durability. Each strike
  (given or taken, respectively; shoes wear per chase/flee action) wears
  it down a bit; **better gear wears faster** (higher tiers burn
  durability quicker — power is a running cost, another KR-style tempo
  wager).
- **Repair at the Forge: 20% of item value in gold + a few XP.** XP-as-
  aether already exists (honing, sleep spell) — repairs join that sink.
  (Minecraft's Mending enchant is the precedent: XP as repair currency
  works.)
- **UI:** a small durability bar at the bottom of the equipped item;
  hover explains ("90% durability — repair at the Forge").
- **Staged:** the starter weapon never degrades, and degradation only
  begins when you buy your **first upgrade** — the tooltip teaches the
  mechanic at the exact moment it starts existing.
- At 0% the item doesn't vanish — it's *broken* (heavy damage penalty)
  until repaired; you always still have the basic weapon (¶1.2).

## 8. Economy tightening

- **Luck charms are too free** — today: 30% of alpha kills, 40% of every
  Warden kill, present jackpots, plus buyable at ◈300. Cut the drop
  rates hard (exact numbers in plan.md) so the ◈300 purchase matters.
- "Free medals": there is **no medal system in code** — what feels like
  free medals is the Warden guaranteed-rare drop. Same fix: rarer, or
  replaced by gold/materials.
- New sinks introduced by this plan (repairs, consumables, second rungs,
  shoes, relics, mage shop) give the tightened faucets somewhere to
  matter.

## 9. Staged complexity and town readability

- **Locked buildings:** non-critical town locations render as locked
  rows with the unlock level on them ("🔒 Arcanum — level 6") — the
  Arcanum, Relay/messages, Fields, and other non-day-1 areas. A locked
  row *is* the roadmap; it answers "where do I go next". The same
  pattern extends inside the shops (¶4.2: next rung visible, locked).
- **The gate copy:** "Tower gate" becomes clearer and moves **to the top
  of the town list**, not the bottom — suggested label: **"The Tower
  Gate — leave town and climb"** (final copy at implementation).
- Durability, counter-consumables, relics, and off-class gear all appear
  in shops only when relevant (level/tier gates), so the day-1 town is
  no more complex than today's.

## 10. Agent messaging: stop the per-action spam

**✅ SHIPPED EARLY — v0.17.1 (2026-07-27),** pulled forward at Roy's
request. What went live:

- Ordinary pane acts **no longer message the agent at all** (previously
  every click landed an awareness row — the token waste).
- The sidekick gets **one check-in per ~5 minutes of active play**
  (clock only advances while acts happen): current state + an
  invitation to offer *one* helpful line, with silence explicitly
  invited.
- **Instant paths kept:** death/boss moments, and the awaits_text
  pass-through hint (the agent must know the game expects typed input).

Still open for plan.md (from the original design): the "you're fighting
a hard-countered matchup" first-time-per-monster moment — that beat
belongs with the defense-profile engine work, not the throttle.

## 11. Characters, races, movies, and art constraints

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
- **Icon constraints (new, applies to everything this plan adds):**
  all icons are super-low-pixel **1-bit** art — **16×16 px** for small
  icons (tier shields, speed, durability, relic glyphs in lists),
  **32×32 px** for large ones (shop rows, the [i] card stat row).
  Consistent with the existing 1-bit banner/creature aesthetic; also
  keeps the icon budget near zero bytes.

## 12. What this deliberately does NOT touch

- Energy pacing, bank, lodge, presents, PvP fields *mechanics* (speed
  interacts with fields chases, but the fields system itself stays),
  factions structure, world Wardens/quorum flow, XP-as-purchased-levels
  (Guildhall) — all stay as shipped.
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
   gear to nearest new rung at full durability, everyone starts at
   Normal speed with no shoes.
3. **Kill-FX ×3 variants** multiply the art budget (~5 monsters × 3 =
   15 GIFs for the early floors alone, more as floors get variety). OK
   to stage: floors 1–3 first, rest generated per content batch?
4. **Degradation on death:** today death destroys armor+shield outright.
   With durability in play, is death = destroy (as now), or death = heavy
   durability hit (softer, since repairs cost gold+XP)? Recommendation:
   heavy durability hit at L≤3 (mercy), destroy above — keeps death
   scary without double-punishing the new repair economy.
5. **How granular is the range model (¶3)?** Recommendation: exactly two
   states — *at range* and *close* — with speed deciding how fast the
   monster forces the transition and whether "open distance" succeeds.
   Two states is readable in prose ("it closes in!"), needs no grid, and
   still creates the full kiting game. Reject anything more granular.
6. **Does speed-as-dodge apply to all damage or only spells?** The brief
   says "dodging magic". Recommendation: small dodge vs *everything* at
   speed advantage (simpler rule, one icon), capped low so armor/res
   tiers stay the primary defense axes.
7. **The 5-minute agent digest** — ~~flat 5 minutes, or beat-aligned?~~
   **Resolved by shipping (¶10):** flat, act-driven clock; beat-aligned
   refinement can ride along with the matchup-moment work if wanted.

## Numbers to fix in plan.md (with the balance model)

- Full two-rung forge table (30 rows → 60) + Arcanum table + **shoes
  ladder** (tiers, prices, speed effect, wear rates).
- Armor/resistance tier percentages per named tier (proposal: 0 / 25 /
  50 / 75 / 90, Immune reserved for scripted encounters).
- **Speed model:** tier values, gap-close rates, "open distance" success
  odds, close-quarters bow penalty, dodge-from-speed coefficient and
  cap, flee success curve.
- Durability pools per tier, wear per strike, break threshold, repair
  XP amounts.
- **Relic catalog v1** (¶5): final list, prices, quantities, effect
  matrix vs the defense axes, exclusivity groups, per-band introduction
  schedule.
- Per-floor bestiary size (4–5) and the matchup spread guarantee — now
  including a speed spread (at least one Fast and one Slow per band).
- Charm/rare drop-rate cuts.
- Off-class purchase prices + miss/damage penalties.

## Suggested phasing (preview of plan.md)

1. **Engine: damage types + defense profiles + the speed/range model**
   (schema, combat math, `armored` migration) + floor-1..N content
   retrofit.
2. **Enemy [i] card + enemy HP bar** (render + pane, incl. the 16×16
   1-bit stat icons).
3. **Forge second rungs + shoes + Arcanum + locked next-tier rows +
   counter-consumables + pawn variable pricing + faction donations.**
4. **Relic catalog v1** (insurance + quiver + class tools; ultimates can
   trail).
5. **Durability** (state, wear, repair, bar UI, staged onboarding).
6. ~~Agent digest throttle~~ — **shipped in 0.17.1**; only the matchup
   moment remains (rides with phase 1).
7. **Town lock UI + gate copy/reorder.**
8. **Races/characters + movie & kill-FX art batch.**
9. **Economy retune + shared-world migration + playtest.**
