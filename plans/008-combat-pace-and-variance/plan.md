# 008 — Combat pace & variance: fast early kills, wild specimens, cheap food

Three directives from the 004 follow-up conversation (2026-07-26):

1. Fully healing must always cost less than the gold from one animal.
2. Rounds-per-kill: average ~2.5 on floor 1, growing ~+0.5 per floor to
   a max (~7), instead of today's flat ~4.7–7.5.
3. Keep those *averages* but add real per-kill variability — some
   animals are easy and pay little, some are hard and pay more. That
   spread is what's missing today.

Plus: a cheap partial heal ("food") at ~2 gold for 5 HP.

## 1. Monster HP derived from the at-level player (the pace dial)

Replace `monster_hp = 12F + 25` with an HP budget derived from the
reference at-level player's damage — the same "derived from the
player model" construction the 004 warden retune used:

    d_ref(F)     = 0.75·(3F + 8·tier(F) + reference_hone(F)) − (3F)//2
    R(F)         = min(2.0 + 0.5·F, 7.0)          # target rounds
    monster_hp(F) = round(d_ref(F) · R(F))

Sim-validated (n=3000/floor, at-level, current tier + hone):

| Floor | new HP (old) | archer rounds | no-class rounds | HP lost/kill |
|---|---|---|---|---|
| 1  | 18 (37)     | 1.9 | 3.0 | ~0 / 52 |
| 3  | 31 (61)     | 2.7 | 4.2 | 0.6 / 76 |
| 5  | 53 (85)     | 3.5 | 5.1 | 2.3 / 100 |
| 10 | 131 (145)   | 5.8 | 7.6 | 16 / 160 |
| 20 | 226 (265)   | 5.7 | 7.6 | 45 / 280 |
| 50 | 509 (625)   | 5.5 | 7.6 | 134 / 640 |
| 100| 982 (1225)  | 5.5 | 7.6 | 286 / 1240 |

The class average sits on the requested 2.5 → 7 line (archers ~0.7
under via Treeline Shot, warriors/sorcerers ~0.7 over — that class
texture is fine). Tune the `2.0` intercept during execution if the
class-average drifts; the acceptance gate below is authoritative.

XP and gold per kill are untouched, so the 004/006 progression pacing
(kills per floor, days per tier) does not move — only clicks per kill
and healing spend drop.

## 2. Specimen variance (the interest dial)

At encounter start, roll a specimen for the creature (player-scoped
deterministic RNG, same as everything else):

| Roll | Specimen | HP | ATK | gold | prose tag |
|---|---|---|---|---|---|
| 25% | runt   | ×0.55 | ×1.0 | ×0.6 | "gaunt", "limping" |
| 50% | common | ×1.0  | ×1.0 | ×1.0 | — |
| 20% | tough  | ×1.4  | ×1.0 | ×1.5 | "scarred", "heavy-set" |
| 5%  | alpha  | ×2.0  | ×1.2 | ×2.2 | "an alpha — twice the size" |

- Difficulty and reward correlate (hard pays more), exactly as asked.
- Alphas also get one extra loot-table roll (medgel/luck-charm tier).
- The card headline/prose carries the tag so the player can choose to
  run from an alpha at low HP — variance becomes a decision, not noise.
- The shard's pre-fight whisper (insight-scaled) may call out the
  specimen — ties the sidekick stat to something felt.
- Normalize during execution so E[HP mult] and E[gold mult] are within
  ±5% of 1.0 (the table above is ≈1.02/1.06; nudge runt/tough to land
  it) — the *averages the user set stay the averages*.

## 3. Healing: the invariant and the stew

1. **Invariant (assert in sim gate):** healer's tent full heal (2F)
   ≤ average gold per kill on every floor. Holds by construction
   (2F vs 8F·1.2^(tier−1)) — the assert guards future retunes.
2. **Hunter's stew** — new option at the gate town fire and the Lodge:
   `◈ 2 → +5 HP`, repeatable (each purchase is one click / one act).
   It's the cheap top-up between fights (0.4 g/HP vs medgel's 1 g/HP);
   the tent stays the one-click full reset. No daily cap — it's
   self-limiting by clicks.
3. **Sleep heals.** A night at the Lodge restores **+20 HP** (on top of
   its PvP protection) — applied lazily at the world-day rollover for a
   player whose `lodged_until_day` covered the night, same pattern as
   energy regen. Sleeping rough in the fields heals nothing (one more
   quiet reason to spend the 10×level and be inside — feeds the 007
   "lodge as a place" texture).
4. Medgel/trauma kit/tonic unchanged (they're inventory, usable where
   the tent isn't).

## Acceptance criteria (extend `004-difficulty-review/sim.py`)

- Class-average rounds/kill at-level: within ±0.5 of `min(2.5+0.5(F−1), 7)`
  on floors 1–10; ≤ 8 everywhere.
- Wilds win ≥ 95% and HP/win ≤ 40% of pool on every floor (unchanged).
- Specimen expectation: mean gold/kill and mean rounds within ±5% of
  the no-specimen baseline over 10k fights.
- Heal invariant: 2F ≤ mean gold/kill for F 1–100.
- Days-per-tier still within ±30% of the 6→24 line (income shifts only
  via reduced healing spend — verify, don't assume).
- Warden acceptance unchanged (wardens keep their own derived HP; they
  do NOT take the R(F) budget — a boss should still feel like ~12
  rounds — but re-run the gate since `monster_stats` feeds
  `warden_stats`; decouple by deriving warden HP from the *old* 12F+25
  baseline or an explicit boss-rounds budget).

## Touch points

- `economy.py`: derived `monster_hp`, `SPECIMEN_TABLE`, stew ShopItem
  (or gate-town-local price constant), boss HP budget decoupled from
  wilds HP.
- `engine/combat.py`: specimen roll in `start_encounter`, mults +
  prose tag, alpha loot roll, shard whisper hook.
- `engine/core.py`: stew option in gate-town and lodge scenes.
- `engine/state.py`: +20 HP lodge-night heal in the daily rollover
  (`touch_daily` / lodge check), constant `LODGE_NIGHT_HEAL_HP = 20`
  in `economy.py`.
- Tests: specimen distribution, stew, invariant; sim gate extensions.
- Version bump + marketplace publish per devprocess.
