# Phase 005 — Durability & repair: execution summary

Shipped in plugin v0.22.0. All 329 plugin tests green, 48 worldd tests
green, full dojo pass (see `tests/017-combat-depth-005/`).

## What was built

- **economy.py** — `durability_pool(T)`, `item_pool(g)` (rung-aware),
  `repair_price(item, missing_frac)` (20% of price × missing, floor 1),
  `DURABILITY_SLOTS`; broken shoes halve their speed bonus in
  `player_speed`.
- **state.py** — doc v3: `durability` (per-slot uses left, staged —
  a slot gets an entry only on its first PAID purchase) and
  `durability_pack` (wear stashed per-item when a piece is unequipped,
  so re-equipping never resets it). Migration gives pre-005 docs FULL
  pools on paid gear they already wear. Helpers `durability_max`,
  `is_broken`, `wear_gear`; `gear_bonus` halves when broken.
- **combat.py** — wear hooks: weapon per swing (incl. treeline shot and
  the off-class miss path), shield+armor per blow taken, shoes per
  chase action (close/open/run). One "gives out" line the round a piece
  breaks, never again. Dry-quiver bow reversion stashes the bow's wear.
- **core.py** — Forge repair rows (price + XP quoted, honing-grammar
  refusals), one-line durability teaching on each slot's first paid
  buy, purchase/wear-from-pack move wear with the item, pawn offers pay
  × the durability fraction.
- **render.py / sheet / tips** — gold/red hairline bar under worn
  equipped icons with "N% — repair at the Forge" hover; sheet says
  "(worn N%)" / "(BROKEN)"; tips for `repair_*` rows.
- **004 retro item closed**: a non-caster holding a focus is explicitly
  blessed in a comment (only BUYING is class-gated); the dojo warrior
  ran a Glass Bead Focus through wear + blows and it behaved as a
  shield.

## The big tuning decision

The planned pool curve (`240/(1+0.3(T−1))` — "better gear wears
faster") **failed the ≤20%-of-income economy gate by up to 14×**. Kit
prices run 3–14 *days* of income; pools that burn in under a day make
daily repair cost 15–20% of the *kit price*, i.e. up to 2.8× daily
income at T10 — and T5+ pools (≤109 uses) broke inside one hunting day
(≈180 events). Shipped `1300·(1+0.25(T−1))` instead: pools GROW with
tier, a piece lasts ≥3 hunting days (~a week at level), and the
running-cost intent survives in the gold-per-use, which still rises
with tier. Tax lands at ~8% of daily income (T1) → ~12% (T10), smooth
between bands (gate asserts ≤20% everywhere and ≤10 pp between bands).
A companion gate (`test_power_still_costs_more_per_swing`) pins the
intent: repair gold per use strictly rises across the ten tiers.

## Verification

- `tests/test_017_durability.py` — 28 tests: pool/pricing math, staged
  onboarding, per-event wear hooks, broken halving (weapon + boots),
  break-line-once, repair flow incl. XP refusal, wear stash/restore on
  swap, pawn × wear, v2→v3 migration, pack-strip fraction, sheet text,
  repair-tax gate, never-repairs-still-wins gate, archer-kiting wear
  gate (≤3× warrior per kill).
- Dojo (real browser, fresh worldd bind): teaching line, live
  migration, 30% gold bar + hover, repair ◈35+12 XP → "made whole",
  off-class arrows 10→7 with bow wear 3 and focus wear 2, shoe wear
  on Run. See `tests/017-combat-depth-005/01-durability-dojo.md`.

## Learnings for later phases

1. **Cost gates before flavor curves.** The pre-plan's pool direction
   sounded right and was off by an order of magnitude. Any phase that
   adds a recurring cost (006 death losses, 008 higher-band tuning)
   must compute the cost as a fraction of `daily_income` at EVERY band
   in the plan itself, not during execution.
2. **The pane replays the cached scene payload.** DB edits to the doc
   don't show until a scene rebuild, and Luna loads plugin render code
   at serve start. Dojo rule: after ANY plugin-side render change,
   restart Luna by port-kill (8765) exactly like worldd (8600), and
   drive one navigation click before reading the screen.
3. **Wear lives on the item, not the slot.** `durability_pack` (stash
   on unequip) closed an infinite-free-repair exploit that the plan
   never mentioned. 006's death/relic logic must move these stashes
   consistently when gear is lost or reincarnated.
4. **`item_pool(g)` not `durability_pool(g.tier)`** — mid-rungs carry
   their step in `rung`; using `tier` gave every mid the whole-tier
   pool (caught by a unit test on the first run).
