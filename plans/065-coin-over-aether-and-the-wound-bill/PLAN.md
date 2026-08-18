# 065 — coin over aether, the wound bill, the frozen finisher

## Problem (roy, 2026-08-18, floor 6 deep, level 9, staff)
1. "Some of the times I get more XP than gold — it happens too many
   times." Card: Vault boar, 42 XP / 20 gold.
2. "Health is never an issue: 516 HP, it costs less than 20 coin to
   recuperate all of it. I want to fear losing HP."
3. "The explosion effect got stuck and every attack still shows it."
   Screenshot: the 3D finisher frozen mid-burst on the kill card.

## Root causes
1. **The 012 law "XP is always below the kill's gold" is broken from
   floor 5.** 048 raised XP_PER_KILL_SLOPE 2.4→3.0 (School sink) while
   gold rides the income pillar × the fading young-tower bounty. Means
   (xp / gold): f5 29/31, f6 36/37, **f7 44/43, f8 52/50, f9 59/57,
   f10 67/66**, f11 74/75 — the curves cross. On top: gold jitters
   ±50% (xp ±25%), and a runt (25% of spawns) pays ×0.45 gold with
   FULL xp. Result: XP > gold on roughly half of floor-5..11 kills.
2. **The tent is a flat running cost.** `healer_tent_price(floor)` =
   ◈5 × income_pillar → f6 ◈15, f9 ◈30 for a FULL heal, whatever the
   wound; the law was "tent < one kill". A 516-HP bar refills for
   less than half a kill's gold; the potions (medgel ◈25/+25 HP) are
   dearer than the tent per HP, so nothing about HP costs anything.
3. **fight3d.js `magicFx` asks `mCenterNow()` every frame until its
   smoke clears (~1.4 s), but the caster's hit lands at 0.44 s and the
   non-native monster is removed (`monster = null`) 0.3 s later.**
   `mCenterNow()` then throws on `monster.group`; the throw is inside
   `frame()` before the render, every frame → the canvas freezes on
   the last drawn frame (the burst ring at life≈0.3 — exactly the
   screenshot). Staff kills of pressed/wrongmade prey, every time.

## Fix (three phases, one plugin release + one worldd commit)

### Phase 1 — coin over aether (economy + combat)
- `economy.KILL_GOLD_OVER_XP = 1.25`: `gold_per_kill(bar)` becomes
  `max(anchor × income_pillar × bounty, xp_per_kill(bar) × 1.25)`. The
  floor rule bites on floors 5–12 (bounty band and its tail); from 13
  the pillar is above it again. `base_gold_per_kill` (the price/fee
  anchor) is untouched — the extra is pocket coin like the bounty.
- Specimens scale XP as they scale HP (runt ×0.55, tough ×1.4, alpha
  ×2.0): the easy kill teaches less. Expected XP per kill moves +1.7%
  (weights 25/50/20/5) — the pace law holds.
- The kill law, enforced where the numbers are rolled: after every
  multiplier, `gold = max(gold, xp + 1)` on a wilds kill. Wardens keep
  their own tables (gold ≫ xp already).
- Bounty label stays for floors ≤ 10.

### Phase 2 — the wound bill (economy + core + combat death card)
- `economy.TENT_FULL_KILLS = 6`; `tent_full_price(floor) = 6 ×
  base_gold_per_kill(floor)`; `healer_tent_price(floor, hp, hp_max)`
  = `ceil(full × missing / hp_max)`, min 1 when wounded. The tent
  charges by the wound: f6 (◈24 base) a full bar ◈144, half a bar
  ◈72, a 10% scratch ◈15 (≈ today's flat price). f1: full ◈48.
- Rows: gate-town "The healer's tent" hint `pay ◈ N · +M HP` (the
  actual bill for THIS wound); the death card the same.
- `daily_income`'s running-cost term keeps its ◈5×pillar/3 estimate
  (`tent_running_cost`) so no price ladder shifts.
- Tips/mechanics text that says "5 × floor" / "full" updated.

### Phase 3 — the frozen finisher (worldd/static/site/fight3d/fight3d.js)
- `mCenterNow()` returns the last known centre when the monster is
  gone (cache on every successful call, reset on `resetStage`).
- `frame()`: each effect's `update` runs inside try/catch — a broken
  effect is dropped, never the frame.

## Verification
- tests/test_065_coin_over_aether.py: means gold ≥ 1.25×xp on floors
  1–30; a floor-6 wilds kill (100 rolls, all specimens) never writes
  gold < xp; runt xp < common xp; the tent bill scales with the wound
  and the gate-town row shows the bill; the death card's tent price
  is the full bill; a full-HP player sees no tent row.
- test_013 heal tests rewritten to the new law; test_039 warden gate
  (gold_per_kill(F+1) < warden_gold(F)) still holds (checked: max
  ratio f12 116 vs 1156).
- fight3d: node --check; headless Chrome on gallery.html with a staff
  kill: the loop is alive 3 s after impact (canvas frame counter
  advances) — if SwiftShader WebGL is unavailable, code review only,
  stated in the status.
- Full plugin suite; worldd suite untouched (static JS).

## Rollback
`git revert` the plugin commit and the worldd commit. No state
migration: gold/xp already banked stay; the tent reprices live.

## Execution status
- Done 2026-08-18. Plugin a3e6ae8 (game 0.88.0), root e320db5.
- Phase 1: `KILL_GOLD_OVER_XP = 1.25` floors `gold_per_kill`
  (f5 31→36, f9 57→74, f11 75→92; f13+ unchanged); specimen HP scale
  rides XP; wilds kills clamp `gold = max(gold, xp + 1)` after every
  multiplier. Warden gate (gold(F+1) < warden_gold(F)) holds to f20.
- Phase 2: `healer_tent_price(floor, hp, hp_max)` = ceil(6 × base gold
  × missing/max); f6 whole bar ◈144 (was ◈15), f9 ◈288 (was ◈30);
  gate row `pay ◈ N · +M HP`; death card quotes the whole bar;
  `tent_running_cost` keeps daily_income (no ladder moved).
- Phase 3: fight3d.js — `mCenterNow` caches the last centre and never
  throws on a banished foe; effect updates try/catch in `frame()` and
  `resetStage()`. Verified by code review + `node --check`; headless
  Chrome/SwiftShader renders the stage but never reaches the impact
  frame inside a bounded run, so no before/after screenshot.
- Tests: test_065 6/6; plugin suite 1226 pass, 6 pre-existing failures
  (verified failing on HEAD before my change; day-dependent draws +
  the concurrent session's combat work); worldd 190 pass, 1
  pre-existing (test_leaderboard_marks_only_you).
- Local 8777 restarted on 0.88.0. Not deployed, not published.
