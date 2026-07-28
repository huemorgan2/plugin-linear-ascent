# Phase 002 — The Grand Retune

Goal: tune the system once, for all (Roy's rule). Level cap, gear as the
power ladder, and the warden coordination curve are one spreadsheet pass
over the same constants — never three.

## Tasks

1. `economy.py`: `LEVEL_CAP = 30`; XP curve compressed so the cap arrives
   in the first weeks; at cap the ✦ bar is pure currency (spells, scans,
   honing — all existing sinks). Guildhall refuses training at cap with a
   line worth reading.
2. Gear carries growth: weapon bonus rescaled from `8 × T` toward
   `~30 × T`; armor gains an HP contribution (max HP is 100% level today
   and would flatline at 400); honing weight per step raised to match;
   energy cap re-keyed off gear band instead of `level // 10`.
3. Re-key the three gates renamed in 021 from player level to floor where
   the cap would strand them (`gear_player_level_req` tiers 4–10).
4. The coordination curve, population-adaptive:
   `R100 = max(min(50, 0.5×A), 0.10×A)`; `N(F) = 1` for F ≤ 30, else
   `ceil(R100^((F−30)/70))`. Derive `HP(F) ≈ N(F) × 8` strike-fights,
   `regen(F)` such that `< N(F)/2` sustained strikers lose ground, and
   the silence window `W(F)` ~6h at 31 → 24h+ at 90. Pity ramp: each
   fully-closed wound −3% max HP, permanent.
5. Monster/warden re-derivation rides `reference_level()` from 021 — the
   reference player caps at 30; verify `warden_stats` follows.
6. Milestone quorums re-seated on the same N(F) curve.
7. Sim script (004-style) committed as a pytest gate: reference player
   floors 1–100 and reference worlds A = 200 / 1,000 / 10,000 through the
   siege curve.
8. Vendor sync + worldd deploy; version bump + publish.

## Tests / acceptance

- Sim gates: era length lands 4–6 months at all three A values; solo
  wardens 1–30 win 60–85% at-level; floor 31+ solo net progress
  mathematically impossible; gear share of at-level ATK ≥ 60% by floor 50.
- Cap edge: a capped player's kill XP flows to the pool/sinks, never a
  level; tiers 4–10 purchasable at cap on the right floors.
- No orphaned `level // 10` reads (grep gate).
