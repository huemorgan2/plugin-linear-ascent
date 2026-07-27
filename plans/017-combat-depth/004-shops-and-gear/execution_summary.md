# Phase 004 — execution summary

**Shipped:** plugin 0.21.0 (marketplace), worldd vendor synced +
deployed (commit `a631d61`, deploy `dep-d9ju1bkvikkc73fj26rg`).
Plugin repo: `e050c18` on `017-combat-depth`, fast-forwarded to main.

## What was built

- **The catalog** (`economy.py`): three weapon lines × 19 rungs
  (10 whole + 9 mids; warrior names kept, bow/staff naming tables
  authored), mids at midpoint bonus / geometric-mean price; shields
  and armor ×19; focuses ×10 (whole rungs only); shoes ×5 with
  explicit levels. `GearItem` grew `line / rung / speed / level`;
  helpers `gear_rungs`, `weapon_line`, `rung_level_req`,
  `off_class_offer`, `off_class_price`. `SHOE_SPEED` — the empty dict
  002 shipped — is now filled from the catalog and `player_speed()`
  picks it up with zero extra wiring (the 002 retro bet paid off).
- **Shops** (`engine/core.py`): class-aware Forge (your line racked,
  the other physical line's previous rung at ×3 as the off-class
  offer, arrow packs for non-archers, wear-from-pack rows, shoes
  ladder); the `_rack` helper shows the last two buyable rungs + the
  next locked one as "🔒 name — level N (+stat, ◈ price)". The
  Arcanum: new town row, locked under level 6 with its own refusal
  line, staves + focuses inside, off-class staff offer for
  non-casters, focuses refused to them outright.
- **Off-class combat** (`engine/combat.py`): damage type follows the
  WEAPON's line (falls back to class), ×0.5 damage, 1-in-4 wide,
  bows burn arrows for non-archers, dry quiver re-equips the class
  starter with a one-line note that also advertises the Forge.
- **State**: `gear.shoes` slot, lazily migrated (`ensure_current`).
- **Icons/render**: shop rows carry 32×32 1-bit gear icons; bow,
  staff and focus got their own glyphs (dojo catch — everything drew
  the sword); `icon_key` resolves weapons by line. Arcanum banner
  generated (both content roots + vendor).
- **Tips**: rung-aware buy tips, arrow pack, wear rows, arcanum town
  row, arrows item.

## Verification

- 301 plugin tests green — `tests/test_017_shops.py` (43 tests):
  catalog invariants, gates, off-class math, both shop scenes,
  buy/wear flows, hone exclusion, off-class combat incl. the flyer
  case, chase sims re-run WITH shoes (treads make the fast race even
  but not free; boots walk away from the slow bulwark), and the
  economy gates — days-to-afford smooth and bounded, no price wall
  between adjacent rungs, off-class never income-positive.
- 48 worldd tests green (one 002-era fix: solo keep now opens with
  `close_in`, the test wanted `attack`; assert accepts either).
- Dojo 058 (`luna/dojo/results/058-017-phase004-shops/`): 5 scenarios
  A-E all pass in a real browser — locked Arcanum row + refusal,
  warrior/archer/sorcerer racks, boots purchase, focus purchase,
  and the full off-class-bow-vs-flyer fight through the dry quiver.

## Learnings for later phases

1. **"Address already in use" is silent death.** My worldd restart
   failed to bind and the OLD engine kept serving — the first dojo
   pass tested stale code and only the missing lock rows exposed it.
   Kill by port (`lsof -ti :8600 | xargs kill -9`), then verify the
   NEW pid's log before trusting the browser. Added to every future
   phase's dojo step.
2. **Icons are content too.** New item categories need their glyphs
   in the same commit — the unit suite can't see that a bow draws as
   a sword; only the screenshot can. Budget an icon pass whenever a
   phase adds item kinds (005 durability pips, 006 relics).
3. **Grammar templates with joined names**: any template around
   `guard_name`-style compounds needs singular/plural branches.
   Sweep prose templates when 005/006 add gear-name sentences.
4. **Owned rungs stay buyable** and a leftover off-class focus works
   (and hones) once equipped — both fine, both flagged: shop
   owned-state polish → phase 007, focus wear/hone rules → 005.
