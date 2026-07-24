# 004 — Execution summary (shipped as plugin 0.5.0)

Phases A–C of the review are implemented, sim-verified, and shipped.
Phases D (co-op warden raids) and E (potions / sidekick powers) remain
their own plans, per the review's own execution order.

Run the acceptance gate anytime:

    python3 plans/004-difficulty-review/sim.py --accept

**All four 004 §4 criteria pass** (sim.py now imports economy.py directly
— the gate cannot drift from shipped numbers):

| Criterion | Result |
|---|---|
| Wilds at-level (tier set + honing), floors 1–100 | win ≥ 99%, worst HP/win 36% of pool (cap 40%) |
| Warden at-level solo | 69–80% for floors 5–30 (floors 1–3 gentler by design); decay 58% → 14% → 0.2% across 33→50 |
| Days per tier (grind only, incl. honing) | 5.5 → 22.0 vs the 6→24 line, worst step ×1.38 |
| Floors 1–5, fresh solo char | median 3.0 play-days (148/150 trials ≤ 3) |

## Phase A — hotfix

- **Bare-handed docs healed everywhere.** Instead of per-DB SQL
  migrations, `state.ensure_current()` runs at every engine entry point
  and upgrades old docs in place — local plugin DB and worldd prod alike,
  the moment a doc is next touched. Playing docs get the shiv **plus a
  "letter from the Vault" apology (+◈ 100)** as a pending event.
- **Defensive floor:** `state.gear_bonus` returns the shiv's +5 for an
  empty weapon slot, so no doc can ever fight bare-handed again — this
  also covers dormant docs referenced by PvP power math before they're
  next loaded.
- **Beginner death mercy** (levels 1–3): keep armor and shield, lose half
  carried gold (`BEGINNER_MERCY_MAX_LEVEL`).

## Phase B — curve retune (deviations from the plan's candidates noted)

- **Wardens derive from the at-level player model** (current-tier set,
  honing 2 floors behind) rather than the plan's linear candidate
  `4.2F+2 / 3.2F / 26F+30` — no closed linear form holds the 65–85% band
  across tier jumps; the derived form holds it by construction. HP is
  1.9× monster HP; DEF equals monster DEF; ATK is solved from a damage
  budget (`WARDEN_DMG_BUDGET`). Floors 1–5 ramp the budget in gently
  (the floor-1 gate falls to the bare shiv). Past floor 30, HP (×/40)
  and ATK (×/100) ramps fade solo odds smoothly toward "bring friends".
- **Fade rekeyed to floor progress:** `fade_multiplier(unlocked_floor,
  floor)` — farming ≥6 floors below your own frontier fades, being
  over-leveled on the frontier never does. The §2 death interlock is gone.
- **Gear honing at the Forge:** each equipped piece (all three slots —
  the plan said weapon/armor, but shield honing is needed to close the
  intra-band DEF deficit) can be honed +1 per unlocked floor past the
  band start, ~15% of a frontier day's income per pass. Hone lives on the
  item (reset on purchase), so entering a band with last tier's fully
  honed kit ≈ the new set unhoned — the sawtooth is gone.
- **Monster ATK slope 4.0 → 3.3** (floor 1 barely changes: 6 → 5). Needed
  to meet the ≤40%-of-pool wilds criterion at every floor; without it no
  hone/gear tuning could hold the late game under the cap.
- **Tier prices 3–10 repriced quadratic** (`2·(T−1) days of mid-band
  income`), tiers 1–2 untouched. T10 lands at 1.51M (was 6.1M). The
  plan's optional "keep T10 at ~2× for the savings meta" was dropped —
  it breaks the plan's own ±30% acceptance line; the bank stays an
  accelerator instead of the only viable path.
- **Band income jump:** gold/kill ×1.2 per tier band
  (`BAND_INCOME_JUMP`), compounding to ~5× at the top.

## Phase C — visible multiplayer

- **Letters free** (`LETTER_PRICE 0`, hint shows "free"); notice board
  25 → 10. Grant burn untouched (anti-RMT, not a chat tax).
- **The Muster Roll** — new town scene listing every playing climber:
  race/class, level, power (ATK+DEF), frontier floor, banked-wealth rank
  (rank public, balance private), last seen. Served through the existing
  `_world` injection (`roster`, `roster_count` from worldd) rather than
  the suggested separate `GET /v1/players/roster` endpoint — same data,
  no new auth surface, works over the existing scene/act flow.
- **Happenings get louder:** engine emits `happening` effects for wilds
  deaths and warden first-clears in world mode; worldd writes them to
  `ascent_happenings`, which the town square already surfaces.

## Tests

- Plugin: 65 passed (was 57) — new coverage: backfill + apology,
  bare-hand floor, mercy death, honing buy/reset flow, fade-on-frontier,
  band income jump, warden derivation, free letters, Muster Roll,
  happenings effects.
- worldd: 14 passed (was 13) — new: muster roll over HTTP with
  cross-tenant roster, sorted by frontier floor.
- Acceptance sim: PASS (all four criteria, table above).
