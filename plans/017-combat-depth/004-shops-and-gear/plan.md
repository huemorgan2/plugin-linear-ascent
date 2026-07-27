# Phase 004 — Shops & gear: rungs, lines, shoes, Arcanum

Goal: the buying game. Second rungs, three class weapon lines, the
shoes ladder, the Arcanum, always-visible locked next tiers, off-class
stopgap gear.

## Tasks

1. `economy.py`:
   - Generate the full 3-line × 20-rung weapon table (warrior names
     stay; bow/staff names authored — a naming table, flavor per band),
     mid-rung rule: bonus midpoint, price geometric mean (plan §3.1).
   - Shields ×20 rungs (warrior+archer), focuses ×10 (Arcanum),
     armor ×20 (shared), shoes ×5 (plan §3.3 table).
   - Level gates: rung T at band_start(T), T.5 at band_start(T)+5.
   - Off-class purchase: ×3 price, ×0.5 damage, 25% miss, arrow packs
     (10) for non-archer bows.
2. `engine/core.py`:
   - Forge scene: class-aware line display; **next locked rung greyed
     with "🔒 name — level N"**; shoes section.
   - New location `arcanum` (unlock level 6, locked row in town before
     that); staff/focus/mage-relic stock.
   - Gear slot `shoes` end-to-end (equip, pack, pawn).
3. `engine/state.py`: doc v2 additions — `gear.shoes`, off-class arrow
   counts in inventory.
4. `pane.py`: sheet shows shoes + speed; shop rows use 32×32 icons.
   003 retro: build shop rows on a STRUCTURED payload (like
   `scene.enemy`), not prose lines — cheaper to render and to test. If
   a row needs expandable detail (stats, lore), use a styled
   `<details>` like the dossier: zero JS, zero card-action plumbing.
5. Vendor sync + deploy; version bump + publish.

## Tests / acceptance

- Unit: table generation invariants (monotone prices, midpoint bonuses,
  gate levels); off-class math (miss consumes round, monster answers);
  arcanum gating; shoes speed feed into 002 formulas.
- 002 retro: the speed hook already exists — fill `economy.SHOE_SPEED`
  (empty dict shipped in 002) and `player_speed()` picks it up; the
  chase-rate tests in `test_017_speed_chase.py` will exercise it free.
  Kite/flee sims must be re-run WITH shoes: +2 speed vs a fast (7)
  monster flips p_open from 0.05 to 0.35 — check that doesn't trivialize
  the archer-counter before shipping.
- **Economy sim gate:** days-to-afford curve stays within the 004-era
  6→24 days-in-tier line with mid rungs included; off-class gear is
  never income-positive vs in-class (sim proves "stopgap not build").
- Content lint unaffected (no numbers in content).
- 003 retro: tests that assert on rendered HTML must dodge escaping —
  `can't` renders `can&#x27;t`; assert apostrophe-free substrings.
- Dojo: as archer — see the bow line (not blades), buy Cobbled Boots,
  see the locked next rung with its level; as warrior pre-L6 — see the
  locked Arcanum row in town.

Exit: all green, published, worldd synced, `execution_summary.md`.
