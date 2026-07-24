# 004 — Difficulty Review: the curve, the wall, and forcing the party

Review requested after a real playtest: an elf archer lost every fight on
floor 1 against plain animals, lost carried gold and time, and earned
nothing. This document is (a) the post-mortem of that experience,
(b) a sim-backed audit of the whole 100-floor curve against the target
("linear difficulty, no step functions; floor N ≈ a linearly growing
number of days of work; solo early, collaboration mandatory later,
solo ≈ 10× slower than a team of 5 on bosses"), and (c) a phased
recommendation plan.

All numbers below come from `sim.py` in this folder, which mirrors
`engine/combat.py` roll-for-roll (hit ranges, defense halving, archer
treeline shot). Re-run any table with:

    python3 plans/004-difficulty-review/sim.py

## Verdict

| Segment | State |
|---|---|
| Floor 1 as played (no weapon) | **BROKEN — 0% winnable.** Confirmed bug, not tuning. |
| Floors 1–5, post-fix, new chars | Good. 100% win, first gear goal ≈ 1–2 days. |
| Wardens (floor bosses) | **BROKEN.** Designed "soloable at-level"; actual at-level win is 0% from floor 5 on. Needs ~1.8× floor level. |
| Fade rule × warden wall | **BROKEN interlock.** Wardens force over-leveling; fade then cuts rewards to 25%. Mid-game pace ≈ 15× slower than target. |
| Within each 10-floor band | Sawtooth, not linear. Easy at x1–x5, brutal at x8–x9 (33–41% win with the gear you can actually buy), easy again at the next x1. |
| Gear ladder T6–T10 | Exponential prices vs linear income: 37 → 400 grind-days per tier. Only survivable via the bank-interest meta (hidden, idle-flavored). |
| XP pace | Healthy. 5 → 50 fights per level, gentle growth. Keep. |
| Healing / energy pacing | Healthy. Healer's tent at 2×floor keeps income ≈ 175×floor/day. Keep. |
| Single-player framing | Agreed: no real multiplayer pressure exists yet. Milestone quorums are designed but stubbed ("solo-tuned fallback" at floor 10). |

## 0. Post-mortem: the elf archer on floor 1

What the sim says about a level-1 character on floor 1 (wolf/boar:
ATK 6 / DEF 3 / HP 37; player: 52 HP):

| Loadout | Win rate | HP cost per win |
|---|---|---|
| Bare hands (ATK 3) | **0.0%** | — |
| Rusted Shiv +5 (free starter) | 100% | 16 / 52 |
| Pigsticker +8 (first 250g buy) | 100% | 9 / 52 |
| Full tier-1 set | 100% | ~0 |

Bare-handed you deal `max(0, rand(1,3) − 1)` ≈ 1 damage/round into 37 HP
while taking ~3.5/round — mathematically unwinnable. Then death takes all
carried gold (after the one daily shardmind save), so the session reads
exactly as reported: lost money, lost time, zero gold earned.

Root cause: the free starter weapon (Rusted Shiv) was only added in
commit `c4ab270` (2026-07-24) — **after** this playtest — and it is only
granted in `state.new_player()`. **Existing player docs are never
backfilled**: the local DB still holds an elf with
`gear.weapon: None` today. Any character created before the fix, on any
backend (local plugin DB and the worldd production DB), is still
bare-handed and still 0%-winnable. This is a P0 (Phase A below).

## 1. The curve today (at-level archer, full current-tier set)

"entry" = fighting with the previous tier's set (the state you're in when
you reach a band, since the Forge only sells your current band's tier —
`gear_tier_for_floor`). "days+bank" = days to afford the next tier set if
you bank everything daily at 5%/day compound.

| Floor | win% entry | win% geared | HP/win | gold/day | next set | days grind | days+bank |
|---|---|---|---|---|---|---|---|
| 1  | 100% | 100% | 0    | 240    | 1,760     | 7.3  | 7  |
| 9  | **34%** | 98% | 90/148  | 1,586  | 1,760     | 1.1  | 2  |
| 19 | **41%** | 98% | 163/268 | 3,321  | 5,500     | 1.7  | 2  |
| 25 | 84%  | 99.6% | 178/340 | 4,478  | 16,500    | 3.7  | 4  |
| 45 | 91%  | 98.7% | 324/580 | 7,957  | 132,000   | 17   | 13 |
| 65 | 94%  | 98.4% | 467/820 | 11,443 | 930,000   | 81   | 34 |
| 85 | 94%  | 97.5% | 620/1060| 14,790 | 6,100,000 | 412  | 63 |
| 99 | 93%  | 96.4% | 749/1228| 16,959 | 6,100,000 | 360  | 61 |

Three shapes to read out of this:

1. **Sawtooth inside every band.** Floors x1–x5 with fresh gear are a
   cruise (≈100%, low HP cost); floors x8–x9 with that same gear cost
   60% of your HP pool per fight and the "entry" column shows what the
   next band feels like the day you arrive: a 33–41% coin flip. Hardest
   right before the next tier unlocks, trivial right after — the exact
   step function the design says to avoid. Cause: within a band the
   player gains +3 ATK/+2 DEF per level while monsters gain +4 ATK /
   +3 DEF / +12 HP per floor; only the tier jump (+8 weapon) resets the
   gap, and it's locked until the next band.
2. **Grind-days per tier are exponential** (prices ×~2.7/tier, income
   linear): 1.7 → 2 → 4 → 8 → 17 → 37 → 82 → 188 → 400. Target shape
   (vision §4 *and* the user's spec) is linear, ~6 → ~24.
3. **The bank is a hidden mandatory meta.** With disciplined daily
   banking the tail compresses to 22 → 34 → 48 → 63 days/tier —
   near-linear increments, close to target! But a player who doesn't
   discover "deposit everything, wait" pays a 6× penalty, and the
   endgame becomes idle-waiting rather than playing.

## 2. The warden wall (the real pacing bug)

Design says regular wardens (5F / 4F / 60F) are "soloable at-level."
Simulated at-level with the current tier set:

| Warden floor | at-level win | level actually needed (~60% win) |
|---|---|---|
| 1 | 100% | 1 |
| 5 | **0%** | 8 (1.6×) |
| 9 | **0%** | 16 (1.8×) |
| 15 | **0%** | 27 (1.8×) |
| 25 | **0%** | 46 (1.8×) |
| 45 | **0%** | 84 (1.9×) |

A warden has 5× a monster's HP and 25% more ATK; at-level you deal
~7/round into 300 HP (floor 5) while it deals ~8/round into your 100.
You must reach ~1.8× the floor's level to pass — and every floor gates
the next, so the *entire game* is played over-leveled.

Now the interlock: the **fade rule** (`fade_multiplier`) cuts XP and gold
to `max(0.25, 1 − 0.1·(level − floor − 5))`. At the forced equilibrium
`level ≈ 1.8×floor`, the gap exceeds the floor from floor ~16 on, so
**everything pays 25% forever**: gold/kill drops from 8F to 2F (the
healer costs 2F — margins near zero), and leveling to the next warden
takes ~87·√F fights per floor (~15 days *per floor* at floor 25, ~20 at
floor 50). Two tuning systems each fine alone, but together they punish
the exact behavior the wardens require. This — not the forge prices —
is the main reason the game feels like a wall.

## 3. Target curve, formalized

From the request, the shape to hit:

- **days(F) grows linearly, no cliffs**: floor 1 ≈ easy/2 days of play,
  each floor a bit more than the last. In tier terms: ~6 days in tier 1
  rising ~+2/tier to ~24 in tier 10 (matches vision §4's intent).
- **Income jumps when you enter a band** (~1.2× for the same work),
  *after* you've re-geared — gearing costs more each band and takes
  proportionally longer.
- **Solo viable through the first bands** (floors 1–~30); collaboration
  clearly *rewarded* from ~30 and effectively *required* from ~40 —
  a solo player pays ~10× the time a coordinated team of 5 pays on
  bosses.
- **Complexity arrives in layers**: base loop first; potions and
  sidekick powers as mid-game unlocks, not day-one noise.

## 4. Recommendations (phased)

### Phase A — hotfix, ship immediately (P0)

1. **Backfill the starter weapon.** Migration over `ascent_players`
   (local plugin DB *and* worldd prod DB): if `gear.weapon` is null,
   set `rusted_shiv`. Plus a defensive fallback in `state.gear_bonus`:
   an empty weapon slot returns the shiv's +5 instead of 0, so no doc
   can ever be bare-handed again. Verify prod worldd actually runs a
   build containing `c4ab270` before calling this closed.
2. **Beginner death mercy.** Levels 1–3: death keeps armor/shield and
   takes half (not all) carried gold. Beginner PvP protection already
   exists to level 5; this extends the same idea to PvE so a bad first
   hour can't spiral. (Refund/apology present for existing players is a
   nice touch: a "letter from the Vault" with ~100 gold.)

### Phase B — curve retune (the core of this review)

1. **Make wardens soloable at-level through floor ~30.** Candidate:
   `ATK 4.2F+2 / DEF 3.2F / HP 26F+30` (≈1.05× monster ATK, ~2.2×
   monster HP), then a scaling term past floor 30 (e.g. HP
   `×(1 + (F−30)/40)` for F>30) so solo odds decay smoothly toward
   "bring friends" instead of a cliff. Constants are candidates —
   acceptance criteria below are authoritative; tune with `sim.py`.
2. **Key the fade rule to floor progress, not level.** Fade when
   fighting far below your `unlocked_floor` (farming newbie floors),
   never for being over-leveled on your own frontier floor. This breaks
   the death interlock in §2 while keeping the anti-farming purpose.
3. **Flatten the intra-band sawtooth with gear honing.** At the Forge:
   "hone" weapon/armor +1 per unlocked floor past the band start, priced
   ~15% of a day's income each. Turns the +8 tier step into 8 small
   steps, adds a linear gold sink, and makes every floor clear feel like
   +power. (Alternative: sell the next tier early at a 25% markup —
   weaker fix, keeps the step.)
4. **Reprice tiers 6–10 from exponential to quadratic.** Formula:
   `set_price(T+1) ≈ 0.7 × daily_income(mid-band T) × (4 + 2T)` where
   daily income ≈ 175×floor. Keeps early tiers as-is, lands late tiers
   around 150k–320k instead of 0.9M–6.1M, and makes days-in-tier land on
   the 6→24 line *without* requiring the bank meta. Bank interest then
   becomes an accelerator (and stays the endgame savings toy) rather
   than the only viable path. If we want "saving is the endgame meta" to
   survive, keep T10 alone at ~2× the formula.
5. **Band income jump.** Multiply gold/kill by `1.2^(tier−1)`. Same work,
   visibly better pay each band — the "1.2× after you gear up" feel —
   compounding to ~5× by the top. Fold this into the §4.4 price formula
   (they're coupled; tune together).

**Acceptance criteria (sim-verified before merge):**

- At-level, current tier + honing: wilds win ≥ 95% and HP/win ≤ 40% of
  pool on **every** floor 1–100 (no x9 spikes).
- Warden at-level solo win: 65–85% for floors ≤ 30; < 10% by floor 50.
- Days-per-tier (grind, no bank): within ±30% of the 6→24 line;
  no tier more than 1.6× the previous.
- Floor 1–5 completable by a fresh solo character in ≤ 3 play-days.

### Phase C — make the world visibly multiplayer

1. **Drop the letter fee** (`LETTER_PRICE 5 → 0`). Talking must be free
   if collaboration is the game. Keep the grant burn (10%) — that's an
   anti-RMT sink, not a chat tax. Notice board 25 → 10.
2. **The Muster Roll.** A new place in Roothollow's square listing every
   climber: name, race/class, level, power (ATK+DEF), banked-wealth rank,
   highest floor, last seen. Needs a worldd endpoint
   (`GET /v1/players/roster`) plus a scene in the plugin. Seeing "31
   climbers, 4 above floor 20" is the strongest possible "you are not
   alone" signal — and feeds PvP/guild ambition.
3. Surface Daily Happenings more aggressively (deaths, warden first
   clears, milestone attempts already exist as concepts) on the town
   square scene.

### Phase D — collaboration as a mechanic (floors 30+)

**Co-op warden raids.** For floors ≥ 40, a warden attempt opens a 24h
strike window with a shared HP pool; any player on that floor commits
3⚡ per strike (async, LORD-style — no live session needed). The warden
regenerates ~8%/hour, so one player chipping alone fights the regen and
needs ~10× the strikes a 5-person day does — the 10× solo handicap
falls out of the regen math instead of a hard gate. Milestone quorums
(already designed, quorum 2→12) ride the same machinery; the floor-10
"solo-tuned fallback" gets replaced by a real quorum-2 fight. Class
complementarity: a warrior strike raises the pool's DEF-shred, an archer
opens each window with a first-strike bonus, a sorcerer strike slows
regen — so a mixed team is worth more than 5 of one class.

### Phase E — layered complexity (unlocks, not day-one)

1. **Combat potions** (Apothecary, unlock floor ~15): haste draught
   (extra strike this round), stoneskin (halve damage 3 rounds) — priced
   as consumable % of daily income.
2. **Sidekick power shop** (unlock floor ~20, "the Shard Lattice"):
   buy the shardmind one active ability, class-complementary, mana-gated
   (sidekick mana exists already as `sidekick.insight` scaffolding):
   - archer → **Lift-High**: knocks a melee enemy back, re-enabling
     Treeline Shot once per fight (3✦);
   - warrior → **Overdrive Plate**: +50% DEF for 2 rounds (3✦);
   - sorcerer → **Aether Well**: refund the next spell's cost (2✦).
   One equipped power in v1; power strength scales with insight.

## 5. What is already right (don't touch)

- XP curve (`60·L^1.5`, 5→50 fights/level) — the one curve that already
  matches "deepens but never explodes."
- Energy pacing (24 cap, ~32/day) and session shape.
- Healer's tent at 2×floor — it's what keeps net income ≈ 175×floor.
- Death rules *above* level 3 (carried-gold loss + armor break is the
  right LORD-flavored sting once you can afford it).
- The 1/day shardmind death-save — great mercy mechanic, keep as the
  hook for the Phase A mercy extension.

## Suggested execution order

Phase A alone unblocks real playtesting (it's a data fix + ~10 lines).
Phase B is the review's core and is fully sim-verifiable before any
browser test. C is small and mostly worldd. D and E are their own
plans once B has landed and been felt in play.
