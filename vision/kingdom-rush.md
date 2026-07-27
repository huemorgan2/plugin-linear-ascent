# Research: Kingdom Rush — Counter-Based Combat Depth

*Added 2026-07-27 as design reference for the combat-depth overhaul
(`plans/017-combat-depth/`). Companion to [research.md](./research.md).
Sources: [Armor and Magic resistance (KR wiki)](https://kingdomrushtd.fandom.com/wiki/Armor_and_Magic_resistance),
[Armor Types Breakdown (Ironhide official)](https://support.ironhidegames.com/support/solutions/articles/4000223666-armor-types-breakdown-kingdom-rush-battles-guide),
[Encyclopedia (KR wiki)](https://kingdomrushtd.fandom.com/wiki/Encyclopedia),
[Game Developer: "Kingdom Rush — the wonderful Campaign level design"](https://www.gamedeveloper.com/design/kingdom-rush---the-wonderful-campaign-level-design),
[GPA design analysis](https://gpa-site.com/en/game/kingdom-rush).*

## What Kingdom Rush is

Ironhide's 2011 tower-defense classic (plus sequels Frontiers, Origins,
Vengeance, Alliance). Players place four classes of towers — **Archers
(fast physical), Mages (slow magical), Artillery (area physical), Barracks
(melee blockers)** — along a fixed path and stop waves of enemies. It is
widely treated as the genre's design benchmark: enormous strategic depth
(GPA rates it 90% strategic depth) from a tiny set of orthogonal,
readable rules. That rule set — not the tower-defense format — is what
Linear Ascent should steal.

## The counter triangle: armor, magic resistance, flying

Every enemy carries **two independent defense stats and one movement
flag**:

| Stat | Icon in-game | Reduces | Countered by |
|---|---|---|---|
| **Physical armor** | grey shield | physical damage (archers, soldiers, artillery) | **magic** damage |
| **Magic resistance** | blue shield | magical damage (mage towers, spells) | **physical** damage (archers, artillery) |
| **Flying** | wings | melee ever touching it | ranged only (archers, mages); artillery can't target it |

Reduction is tiered and *named*, not raw numbers — the player reads a
word, not a spreadsheet:

| Tier | Reduction |
|---|---|
| None | 0% |
| Low | 1–30% |
| Medium | 31–60% |
| High | 61–90% |
| Great | 91%+ |
| Immune | 100% |

Design consequences that made this work:

1. **Orthogonality.** Armor and magic resistance are independent axes; an
   enemy is strong against *one kind* of damage, almost never both. The
   official tip literally says: "Magic damage is the best way to deal
   with armored enemies" / "Enemies with magic resistance receive less
   damage from magic attacks." Every enemy therefore has an intended
   answer, and the player's job is to *diagnose and switch*, not to
   grind.
2. **A third axis that is binary, not scalar.** Flying isn't "30% dodge"
   — melee simply cannot touch it. Binary rules are instantly readable
   and create hard "you cannot brute-force this" moments.
3. **The only both-shields enemies are bosses/elites**, and even then the
   answer is raw HP pressure plus timing of abilities — bosses are damage
   checks, regular enemies are *knowledge* checks.
4. **HP as the third defense.** Some enemies have no shields at all but
   massive HP pools (Earth Elementals, Trolls) — they don't resist you,
   they *outlast* you, punishing slow damage and rewarding burst or
   sustained multi-source pressure.

## Readability: tap the enemy, learn the enemy

- **Tap any enemy** mid-game to see its stats: HP, armor tier, magic
  resistance tier, abilities. No hidden math.
- The **Encyclopedia** records every enemy ever encountered with stats,
  abilities, and *flavor text about where it lives and what it does*.
  Discovery of a new enemy type is a collectible event.
- Incoming waves can be **scouted before they arrive** ("tap the wave
  icon"), so a counter-pick is a plan, not a reaction.

This is the single most transferable lesson: **the counter system only
creates strategy if the player can read the enemy's sheet at a glance.**
KR spends real UI on shields-with-tiers next to the HP bar; the depth
would be invisible noise without it.

## Staged introduction: one new rule per level

From the Game Developer campaign-design analysis:

- Level 1 has plain, unarmored, ground enemies only — the tutorial *is*
  the absence of the system.
- Each subsequent level introduces **exactly one new enemy type or rule**
  and is shaped so that the new thing matters (armored enemies arrive on
  the level after you unlock mages; the first flying wave arrives where
  artillery chokepoints would otherwise dominate).
- Levels deliberately **set up the next level's concept** — you meet two
  scouts of a new type at the end of level N, then face swarms of them in
  level N+1.
- The most unusual mechanics are introduced **last** to fight late-game
  burnout.

## Economy and pacing levers

- Gold is earned per kill and spent on build/upgrade; **selling back**
  a tower refunds most of its cost (90% with an upgrade), making
  re-speccing a legitimate move rather than a punishment.
- **Calling a wave early** grants bonus gold and cooldown reduction — a
  standing tempo-vs-safety wager.
- Between levels, stars buy **permanent account upgrades** on a clean
  grid — small, immediately-felt bonuses, never new rules.

## What Linear Ascent takes from this (mapping)

| Kingdom Rush | Linear Ascent (017 overhaul) |
|---|---|
| 4 tower classes with distinct damage types | 3 professions: **Warrior (melee physical), Archer (ranged physical), Mage (magical)** |
| Enemy armor tiers (grey shield) | Monster **armor** stat — cuts melee/ranged physical damage |
| Enemy magic resistance (blue shield) | Monster **magic resistance** — cuts spell damage |
| Flying units untouchable by barracks | **Airborne monsters** — melee can't reach without special (fast-depleting) gear; bows and spells work fine |
| High-HP unshielded enemies | **Bulwark monsters** — huge HP+armor pools that wear melee down over long fights |
| Bosses = all defenses + HP check | **Wardens** — big HP *plus* some armor *plus* some magic resistance |
| Tap enemy → stat card; Encyclopedia lore | **[i] info card on the enemy image**: HP bar, armor tier, resistance tier, flying flag, habitat/lore blurb |
| Named tiers (None/Low/Medium/High/Great/Immune) | Same named tiers — words, not percentages, in the UI |
| One new rule per level; tutorial = absence of rules | Floor 1 monsters: zero armor, zero resistance, grounded. New axes appear floor by floor |
| Balanced deck: bring every class | Solo player can *buy* off-class capability (warrior's bow, mage-piercing arrows) — expensive, scarce, degrades fast; faction play covers the rest |
| Sell-back refunds; early-wave wagers | Pawn shop always buys (variable price); run-from-this-fight is a legitimate, expected choice |

The core KR insight to preserve at every decision point: **depth comes
from a few orthogonal, readable, named rules with intended counters —
never from stat inflation.** A player should look at a monster card and
know within two seconds *why* this fight is bad for them and *who* it
would be good for.
