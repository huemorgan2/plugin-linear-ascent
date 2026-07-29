# Linear Ascent — Economy & Numbers

The 100-floor plan: difficulty, bosses, grind, gold, XP, gear, and the social economy. Formulas are the design; the tables are sample points. All numbers are v1 targets — tune in play, but keep the *shapes*.

## 0. The law — gold buys time, never power (022/004)

Every gold sink in the game buys back **time**, never a stat the grind
can't reach. The two worked examples that set the pattern:

- **The Energy cell** (1/day, medlab): it refills ⚡ — it does not raise
  ATK, DEF, or the level. What you bought is *tonight's session back*,
  not a stronger character. Tomorrow you and the climber who saved the
  gold are identical.
- **Potions and the healing ladder** (stew → tent → potion): dawn closes
  every wound for free (022/004 — full HP at the world-day tick, and
  only there). Paying mid-session doesn't buy HP a patient climber
  can't have; it buys *not waiting for dawn*. The potion sink survives
  the free heal precisely because it prices the hours, not the health.

The test for any new sink: if a rich climber and a patient climber end
the week with different character sheets, the sink is buying power —
redesign it. (Levels come only from XP; gear gates ride levels and the
world's floor; contract payouts are a bonus on hunting you'd do anyway.)

## 1. Energy and the XP pool (pacing) — 006

| Meter | Cap | Refills | Spent on |
|---|---|---|---|
| **Energy ⚡** | 24 (+1 per 10 levels) | 1 per 45 min (~32/day) | wilds fight 1 · Warden attempt 3 · milestone boss commit 5 · PvP attack 3 |
| **Aether ✦ = the XP pool** | `xp_need(level)` — the bar to the next level | earned by fighting, never by time | honing (½ frontier kill) · Sleep Spell (1 kill, no award) · shard scan fallback (½ kill) |

006 deleted the mana meter. *Aether is crystallized experience*: the ✦ bar
is your progress inside the current level, and abilities burn what you've
learned. One rule sentence: **levels are forever and open doors; the XP
inside your current level is aether — spend it and you level slower, hoard
it and you level sooner.** Spending never reduces the pool below 0 and
never touches level. Level-up subtracts the level's cost (overflow carries).

Levels gate content: tier-T gear requires level ≥ 10·(T−1)+1, and entering
floor F requires level ≥ F − 10 (on top of Warden unlocks) — gold alone
can't make a veteran. Levels can never be taken away by any mechanic.

A session drains in 10–20 minutes; two or three sessions a day is optimal, binging is impossible. Energy flask (1/day) is the only refill. No paid refills.

## 2. Player baseline

- ATK = 3 × level + weapon
- DEF = 2 × level + shield + armor
- HP = 40 + 12 × level
- Carried gold: unlimited, lootable. Banked gold: safe, forever.

## 3. Monsters, XP, and gold (the grind)

For a regular monster on floor **F**:

| Stat | Formula |
|---|---|
| ATK / DEF / HP | 4F+2 / 3F / 12F+25 |
| XP per kill | **12 × F** (±25%) |
| Gold per kill | **8 × F** (±50% — luck) |

- **XP to level up:** need(L→L+1) = **60 × L^1.5**. (L1: 60 · L10: 1,900 · L30: 9,860 · L50: 21,200 · L70: 35,100 · L90: 51,200)
- **Fights per level ≈ 5 × √L** when fighting at-level — 5 fights at level 1, ~35 at level 50, ~50 at level 99. The grind visibly deepens but never explodes.
- **Time to cap:** ~3,300 at-level fights ≈ 165 days at 20 fights/day, cut to **~4–5 months** by boss XP, quests, and presents. The climb is a season, not a weekend.
- **Fade rule:** fighting on a floor more than 5 below your level pays × max(0.25, 1 − 0.1×(level − F − 5)). Farming floor 3 at level 40 is pocket change; helping a friend there still pays *something*.
- **Daily income at level:** ~20 fights × 8F + vendored loot ≈ **200 × F gold/day**.

## 4. The 100-floor difficulty table (sample rows)

| Floor | Monster ATK/DEF/HP | XP/kill | Gold/kill | Gear tier sold | Days in tier (est.) |
|---|---|---|---|---|---|
| 5 | 22 / 15 / 85 | 60 | 40 | T1 | ~6 |
| 15 | 62 / 45 / 205 | 180 | 120 | T2 | ~8 |
| 25 | 102 / 75 / 325 | 300 | 200 | T3 | ~10 |
| 35 | 142 / 105 / 445 | 420 | 280 | T4 | ~12 |
| 45 | 182 / 135 / 565 | 540 | 360 | T5 | ~14 |
| 55 | 222 / 165 / 685 | 660 | 440 | T6 | ~16 |
| 65 | 262 / 195 / 805 | 780 | 520 | T7 | ~18 |
| 75 | 302 / 225 / 925 | 900 | 600 | T8 | ~20 |
| 85 | 342 / 255 / 1045 | 1020 | 680 | T9 | ~22 |
| 95 | 382 / 285 / 1165 | 1140 | 760 | T10 | ~24 |

## 5. Wardens (bosses)

**Regular Wardens** (floors ending 1–9) — soloable at-level:
- ATK 5F / DEF 4F / HP 60F · costs 3 energy per attempt
- Reward: **60×F XP, 80×F gold**, one guaranteed rare-loot roll. First-ever kill opens the floor for the whole world.

**Milestone Wardens** (every 10th floor) — group quorum, committed asynchronously via the Guildhall within a 24h window:

| Floor | Warden | ATK/DEF/HP | Quorum | Per-participant reward |
|---|---|---|---|---|
| 10 | Gnarl, the Goblin King | 60/50/900 | 2 | 4,000 XP · 5,000 g |
| 20 | Warlord Skarn | 120/100/1,800 | 3 | 8,000 XP · 10,000 g |
| 30 | The Barrow King | 180/150/2,700 | 4 | 12,000 XP · 15,000 g |
| 40 | Matriarch Vyx | 240/200/3,600 | 5 | 16,000 XP · 20,000 g |
| 50 | **Cindermaw the Wyrm** | 300/250/4,500 | 6 | 20,000 XP · 25,000 g |
| 60 | Jarl Hrimgar | 360/300/5,400 | 7 | 24,000 XP · 30,000 g |
| 70 | Zephyra, the Storm Queen | 420/350/6,300 | 8 | 28,000 XP · 35,000 g |
| 80 | The Pale Huntsman | 480/400/7,200 | 9 | 32,000 XP · 40,000 g |
| 90 | Malgrim, Herald of the King | 540/450/8,100 | 10 | 36,000 XP · 45,000 g |
| 100 | **Vharuk, the Demon King** | 650/550/12,000 | 12 | names carved first on the Stone; prestige reset unlock |

Milestone clears are world events: broadcast in Daily Happenings, names carved on the Stone of the Climb.

## 6. The Forge catalog (what you buy)

One named item per slot per tier; owning the tier's set is the visible badge of your climb. The ladder runs scrap-steel → plasma-tempered → fusion-core, matching the arcanotech setting ([story.md](./story.md)). Prices assume §3 income plus bank interest.

| Tier | Weapon (+ATK) | Shield (+DEF) | Armor (+DEF) | Prices w/s/a (gold) |
|---|---|---|---|---|
| 1 | **Pigsticker**, scrap-steel shiv (+8) | Scrapwood Buckler (+5) | Padded Jerkin (+7) | 250 / 100 / 200 |
| 2 | **Wolfbite**, shock-tip hunting spear (+16) | Ironbound Targe (+10) | Riveted Leather (+14) | 800 / 320 / 640 |
| 3 | **Emberfang**, dwarf-forged plasma axe (+24) | Dwarven Wall, powered tower shield (+15) | Chain Hauberk (+21) | 2,500 / 1,000 / 2,000 |
| 4 | **Thornsong**, elven mono-edge blade (+32) | Elfmirror, light-bending (+20) | Silverthread Mail (+28) | 7,500 / 3,000 / 6,000 |
| 5 | **Oathkeeper**, knight's arc-blade (+40) | Drakescale Barrier (+25) | Wyrmhide Coat (+35) | 22,000 / 9,000 / 18,000 |
| 6 | **Grimcleaver**, giant-slaying thunder maul (+48) | Frostguard emitter (+30) | Dwarven Powerplate (+42) | 60,000 / 24,000 / 48,000 |
| 7 | **Starfall**, storm-cell saber (+56) | Stormwarden's Aegis, deflector (+35) | Stormforged Plate (+49) | 160,000 / 64,000 / 130,000 |
| 8 | **Duskrender**, phase-etched glaive (+64) | Gloomturner, cloak-field (+40) | Nightweave Harness (+56) | 420,000 / 170,000 / 340,000 |
| 9 | **Kingsbane**, demon-steel railblade (+72) | Hellgate Bulwark (+45) | Demonbone Panoply (+63) | 1,100,000 / 440,000 / 880,000 |
| 10 | **Dawnbreaker**, fusion-core blade — the last light of Aldervale (+80) | The Unbroken (+50) | Aegis of the Vale (+70) | 2,800,000 / 1,100,000 / 2,200,000 |

- Early tiers cost ~2–3 days of income; **tiers 8–10 are affordable only through compound bank interest, milestone payouts, and guild perks** — deliberately, like LORD's endgame weapons. Saving *is* the endgame meta.
- The pawn shop buys anything back at a **daily variable rate, 25–55%** (seeded from the world day and said out loud in the shop), scaled by worn durability. (017 §3.8 replaced the flat 40%.)

### Apothecary & Medlab

| Item | Price | Effect |
|---|---|---|
| Medgel | 25 | +25 HP |
| Trauma kit | 120 | +80 HP |
| Trollblood tonic | 600 | full heal, usable mid-fight |
| Energy cell | 200 | +5 ⚡ (max 1/day) |
| Luck charm | 300 | better loot & present rolls until tomorrow |
| Scout optics | 100 | sidekick reveals enemy stats, 3 charges |

## 7. Bank, death, lodge, presents

- **Bank:** deposits free, withdraw anytime, **5%/day compound interest**, credited when you visit the teller. Banked gold survives death and theft — "a lodge for your money."
- **Death** (monster or player, 017 §3.6): lose **40–60% of carried gold**; each paid weapon rolls **20% gone for good**; armor, shield, and shoes lose **half a durability pool** (the guards drag you home and the menders bill you). A held **Weapon Reincarnation Spell** (0.5 DI) cancels all of it and repairs everything — but each *spare* spell you hoard rolls 50% lost on the death it didn't cancel. Respawn at Roothollow. No XP loss.
- **Dawn (022/004):** HP restores to full at the world-day tick, and only there — no daytime trickle. The healing ladder (stew/tent/potions) prices the hours before dawn, per §0.
- **Lodge:** sleeping there makes you unattackable offline — it sells safety, never health (the old +20-at-dawn special case is retired; dawn heals everyone). Price 10 × level gold/night. Skipping it puts you "in the fields" — attackable by anyone (2 PvP attacks/day allotment per attacker; winner takes carried gold + a 5%-of-your-level XP bounty; every kill is published in Daily Happenings). Levels 1–5 get beginner protection: never attackable.
- **Presents:** return after ≥20 hours away → one roll: 40% gold (50 × level) · 25% potion · 15% full energy · 10% rumor (advantage in next fight) · 8% armor-repair token · 2% jackpot (rare item, or bank doubling capped at 1,000 × level). A luck charm improves the roll (the halfling race was retired in 017 phase 009 — doc v4 re-registers those lines as human). A missed day never drops you below baseline — breaks are supposed to feel fine.

## 8. Social economy

- **Gold grants (player → player):** at the bank — send a purse to any player. **10% fee is burned** (gold sink), daily send cap 150 × your level, receiver must be level 5+ or a guildmate. Keeps generosity real and twinking/RMT funnels dull.
- **Letters:** courier post, 5 gold per letter to any player, delivered to their next session. A letter can carry a purse (grant rules apply) or one item (item tier ≤ receiver's tier + 1).
- **The contract board (022/004):** three world jobs a day, seeded from the world day like the pawn rate — the same three lines for every climber. Shapes v1: cull N of a named creature on a named floor · N kills by a weapon class · answer a Warden's horn. Progress counts off kills the engine already scores (no accept step); pays gold + XP as a *bonus on hunting you'd do anyway*, broker's stamp ◈ 10 off the top, occasional repair token; jobs expire at dawn, no rerolls.
- **Taunts:** attaching a one-line message to a PvP kill is free and encouraged — it's LORD's gossip engine.

### Sinks vs. faucets (keep the gold honest)

Faucets: monster gold, boss payouts, presents, interest. Sinks: gear ladder, lodge nights, potions, letters/boards, grant fee, pawn-shop margin, armor lost on death. Interest is the only exponential faucet — it's balanced by the exponential gear ladder pointing at it.

## 9. Combat depth & the counter economy — 017

The 017 overhaul made fights a matchup language and hung four new
drains off the same daily income. `plans/017-combat-depth/plan.md`
§2–3 is the constants ledger (amended in place, dated); this section
is the shape.

- **Damage types & counters:** every class deals one type (warrior
  melee · archer arrow · sorcerer magic); monsters carry
  armor/resist/flying/speed/bulwark traits. Tier rule learned at
  scale: **med tiers barely register at reference gear** — a wall the
  player should FEEL wants the high tier. A hard counter must be
  *risky* (win ≤75%) or a *drag* (≥1.6× easy-prey rounds), never safe
  and quick; the gates (`tests/test_017_bestiary.py`) enforce it on
  every floor 11–100, day-pinned.
- **Speed & chase:** speed tiers decide who closes and who kites;
  ranged-vs-fast is an intended counter, and slow+armor_med is
  prey-grade for archers (so slow armored monsters carry armor_high).
- **Durability & repair:** gear wears per round; the repair bill runs
  **~8–12% of daily income** per band (gate ≤20%).
- **Death economy:** see §7 — the rational death line is
  min(unprotected cost, spell price)/4 days ≈ **12.5% of DI**.
- **Relics:** one dramatic effect + one hard limitation, no permanent
  stats, priced in DI. Consumables are **progression tools, not
  farming tools** (a kill pays ~DI/30; every breaker costs more), and
  each class's wall-push costs the same **0.08–0.12 DI** lane
  (2026-07-28 retune: quivers 0.3→0.2, piercing 0.5→0.35, mage vials
  0.3→0.1).
- **The stacked-drain ceiling:** repairs + the death line + one
  wall-push a day stays **≤40% of daily income** for every class at
  every band (`tests/test_017_death_relics.py`) — the climb always
  nets ≥60%.
- **Faucet cuts:** free luck charms are scarce so bought relics
  matter — alpha spoils 10%, warden rare loot 12%.
- **Faction armory:** economically neutral by construction — no gold
  crosses its boundary, wear rides through; capped at 50 rows, one
  take/day.

## 10. Tuning notes (open)

- Interest 5%/day vs. gear curve is the tightest coupling — tune together or not at all.
- Milestone quorums assume a small early population; make them config so a 10-player world and a 500-player world both work.
- Fade-rule floor (0.25) may need lowering if high-level players farm newbie floors for PvP funding.
- Consider KoL-style energy carryover (cap 2× daily regen) if players resent lost regen overnight; v1 ships without it.
