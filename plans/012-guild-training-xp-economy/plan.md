# Plan 012 — Guild Training & the XP Economy

## Why

Player feedback (2026-07-26):

1. **"Once I fill the whole XP bar it zeros it"** — not a bug: the engine
   auto-levels the moment `xp >= xp_need` (`combat._level_ups`), consuming
   the bar and healing. But auto-leveling is the wrong design: **leveling
   up should be bought with gold**, deliberately, at a building.
2. **Add the level-up to the Guildhall** (the guild building already
   exists with faction join/found; "join factions" stays as is).
   First level-up costs ◈ 200; later levels grow exponentially like the
   rest of the game's economy.
3. **Show the level next to the gold** in the meters rail.
4. **Write "XP", not the ✦ star icon** — everywhere the star means XP.
5. **XP is too high** — floor-1 monsters leveled the player twice before
   they had 100 gold. Make XP scarcer than gold **in all places**.

## Design

### A. Training at the Guildhall (manual level-up)

A new **Train** option at the Guildhall. Requirements, both shown plainly:

- **Full XP bar**: `xp >= xp_need(level)` — the bar is the *license* to
  train; gold is the *fee*. XP keeps accumulating past the cap (kills are
  never wasted), the bar just renders full.
- **Gold fee**: `levelup_gold(level)`.

On purchase: `gold -= fee`, `xp -= xp_need(level)`, `level += 1`, wounds
close (full heal — the perk that used to ride the auto-level), ledger
entry `levelup`. One level per click; the option re-renders with the next
fee. Victory scenes nudge when the bar is full ("the Guildhall trains
climbers — ◈ N").

Auto-leveling (`combat._level_ups`) is **removed**.

### B. The fee curve

```
levelup_gold(level) = max(200, round(daily_income(level) / 10) * 10)
```

One day of at-level income per level — literally the growth curve the
rest of the game is priced in (linear × 1.2 per gear band ⇒ exponential
across bands, same shape as forge/hone pricing):

| level | fee ◈ |
|---|---|
| 1→2 | 200 |
| 2→3 | 380 |
| 5→6 | 960 |
| 10→11 | 1,920 |
| 20→21 | 4,800 |
| 30→31 | 8,940 |
| 50→51 | 22,470 |

### C. XP scarcity — XP < gold in all places

| source | XP before | XP after | gold (unchanged) |
|---|---|---|---|
| wilds kill | `12·floor` | **`4·floor`** | `8·floor·1.2^(band−1)` |
| warden kill | `60·floor` | **`25·floor`** | `80·floor` |
| milestone boss | 4,000…40,000 | **`0.3 × gold`** (1,500…15,000) | 5,000…50,000 |

Derived XP prices (hone = 0.5 kill, sleep = 1 kill, scan = 0.5 kill) ride
`xp_per_kill` and scale down automatically — ratios preserved, XP stays a
real spend decision. PvP bounty (5% of `xp_need`) unchanged.

Pacing check: kills to fill the bar at level L on floor L =
`60·L^1.5 / 4L = 15·√L` → 15 kills at L1, ~47 at L10, ~67 at L20.
With the ◈ fee on top, no more two-levels-before-100-gold.

### D. Meters & labels

- `Meters` gains `level`; the rail shows **`LV n`** next to `◈ gold`.
- The ✦ meter reads **`XP 93/170`**; tooltip rewritten (XP fills by
  fighting; full bar + gold at the Guildhall = next level; honing/spells/
  scans still burn it).
- Every ✦-as-XP cost hint/prose becomes `XP n` (scan, sleep, hone).
- `core.py` floor-gate prose "Levels are earned, never bought" must go —
  levels are now literally bought.

### E. Compatibility

Doc-based, no migration. Players with banked XP over the cap simply
train when they can afford it. Old stored scenes lack `meters.level` —
`from_dict` defaults it. worldd runs the same engine via vendor sync;
deploy after merge. Plugin → **0.11.0**.

## Phases

1. **Economy**: `levelup_gold`, XP retune, milestone table. Unit tests.
2. **Engine**: drop `_level_ups`, victory nudge, Guildhall Train option +
   `guild_train` action. Unit tests.
3. **UI**: `Meters.level`, XP label, LV chip, tooltip, hint sweep.
4. **E2E**: scenario `tests/012-guild-training-xp-economy/` — full
   gameplay pass in the browser (hunt → economy feel → train → meters).
5. **Ship**: vendor sync, 0.11.0, publish, deploy.
