# 045 — hold and endure

Four player-reported issues, one ship (0.59.0).

## Problem (user report, 2026-08-09)

1. **The shard-scan option is redundant.** Every fight card ends with
   "Ask the shard to scan it" (charges, or XP at zero charges). Since 017
   the free `[i]` dossier already shows name/HP/ATK/DEF/profile/range/drops
   on every fight — the scan's only unique output is the next-intent line.
   A paid row that duplicates a free panel is noise.
2. **Gear in the pack cannot be equipped from the pack.** Clicking a
   weapon/shield in the pack pops "The Forge swaps gear in and out of the
   pack." The swap verb (`wear_*`) exists but is only offered inside the
   Forge/Arcanum scenes. Players expect: click item → promote it to the
   hand — "Use this" (weapon), "Use as shield" (shield).
3. **Armour endurance is invisible.** Since 005/034 armour and shields
   already degrade in proportion to the damage they turn, and mending
   already costs gold + XP at the Forge. But nothing ever shows the
   number: forge cards show only `pay ◈ N · +M DEF`, pack cells show only
   a hairline bar. The player cannot weigh price against endurance
   ("1000 endurance should read costly; 200 cheap"), and cannot see how
   close a piece is to breaking.
4. **Killing an animal strands you on a stub menu.** The victory card
   offers only "Hunt the wilds again", the Warden's keep, and Roothollow —
   while the floor's real menu also has deep hunt, stew, heal, medgel,
   trauma kit, flare answers, and the NPC. On the frontier floor even the
   gate row is absent, so the user sees essentially "hunt again + warden".

## Root cause

1. `engine/combat.py:608` appends the scout row unconditionally;
   the dossier that obsoleted it shipped later and nobody removed it.
2. `engine/core.py:165` — `pack_actions()` returns no action for FORGE
   gear, only the why-string. `_wear_from_pack()` (core.py:1478) is the
   complete implementation but has no caller outside shop scenes.
3. Durability is engine-internal: `item_pool()` / `p["durability"]` are
   never serialized as numbers, only as a 0..1 bar fraction. Wear is
   `6·blocked_by_piece/bonus` pool-units per blow, so the pool unit is
   abstract, not damage.
4. `combat._after_fight_options()` (combat.py:1249) hard-codes 4 rows —
   a second, drifted copy of `core._gate_town_options()` (it also shows
   the wrong keep label after a warden has fallen). All five combat-exit
   cards (victory, driven back, flee, polymorph, sleep-walk) share it.

## Emergency mitigation already taken

None needed — nothing is down; these are UX defects.

## Fix — four phases (details in phase-N/PLAN.md)

- **Phase 1 — remove the shard scan.** Delete option row + handler,
  `economy.scan_xp_cost`, the `scout_optics` shop item + buy branch +
  icon + tips, the `scout_charges` state key, and the prose that lists
  "scans" among XP sinks. Update the 5 test files that exercise it.
- **Phase 2 — promote from the pack.** `pack_actions()` offers
  `wear_<slug>` for pack gear out of fight — label "Use this" (weapon),
  "Use as shield" (shield), "Wear this" (armor), "Wear these" (shoes) —
  dispatched through `_pack_use` to the existing `_wear_from_pack()`.
- **Phase 3 — endurance made visible and priced.** Display unit =
  damage the piece can still turn: `END(item) = item_pool·bonus/6` for
  shield/armor (wear is exactly 6·blocked/bonus pool-units, so the
  displayed number falls by exactly the damage absorbed — the mechanic
  the user asked for already ships; this is a display-layer change with
  zero balance risk and no save migration). Weapons/shoes display their
  pool as swings/strides. Forge cards gain `· END n`; pack tips, cell
  hover and character sheet gain `left/total`; repair rows say what they
  restore. A new test asserts END grows monotonically with price within
  each slot ladder (keen < base < warded), which is the "make the
  numbers work" guarantee — pricing itself is untouched, so the
  difficulty gate is unaffected.
- **Phase 4 — full floor menu after a fight.**
  `_after_fight_options()` delegates to `core._gate_town_options(p, fl)`
  (deferred import, same pattern as combat.py:1041), keeps the
  "Hunt the wilds again" label, adds the gate row when a deeper floor is
  unlocked, and passes `option_art=core._gate_town_art(fl)` so the
  victory card keeps its tiles. Fixes all five combat-exit cards and the
  stale keep label at once. The first-clear reel branch and shared-warden
  movie hand-off stay untouched.

## Verification

- Targeted tests per phase (see phase plans), then the full suite:
  `cd plugin-linear-ascent && uv run --project ../luna python -m pytest tests`.
- Difficulty gate `python3 plans/004-difficulty-review/sim.py --accept`
  compared against its result on HEAD before the change (known to drift;
  the comparison, not the absolute PASS, is the gate — see memory note
  2026-08-02).
- Dojo walkthrough against production after deploy (scenarios in
  `tests/045-hold-and-endure/`): no scan row in a fight; pack popup
  equips a shield; forge card shows DEF + END; post-kill card shows the
  full floor menu. Results folder + execution status appended here.

## Operational notes

- Version 0.59.0 in BOTH `version.py` and `luna-plugin.toml`. Live state
  at plan time is already skewed: marketplace serves 0.57.1 while worldd
  vendors 0.58.0 (vendor version.py was bumped out-of-band; plugin HEAD
  still reads 0.57.1). Shipping 0.59.0 to both halves resolves the skew.
- Ship order: plugin tests green → commit plugin → vendor_game.sh →
  commit worldd vendor + submodule pointer → push (huemorgan2) → verify
  Render deploy rolled (`/health` must say `"game":"0.59.0"`; manual
  `render deploys create` if stale) → package + publish 0.59.0 to the
  marketplace (re-check index version immediately before AND after —
  upload sets latest unconditionally) → dojo walkthrough.
- The parallel art session has uncommitted event GIFs in this repo —
  stage only files this plan touches; never `git add -A`.
- `scout_charges` stays as a stale key in live saves; nothing reads it,
  and state.py does not prune unknown sidekick keys. Harmless.

## Execution status

**Shipped 0.59.0** — 2026-08-09/10.

- Phases 1–4 executed and committed in order: `31fa497`, `00cb26f`,
  `c50888c` (+`03724ad`), `66133c0`; per-phase status appended in each
  phase PLAN.md.
- Mid-ship, `origin/main` held the live 043 kill-bar line (0.58.0) that
  this checkout lacked — merged as `4773e1e` (conflicts: two version
  stamps kept at 0.59.0; test_economy took 043's numbers minus the
  scan row). Full suite on the merged tree: **987 passed, 1 skipped,
  0 failed** (the merge also replaced two date-flaky tests that failed
  on both sides before it).
- Difficulty gate: output byte-identical to the live 043 tip
  (`dcf5172`), including its pre-existing `ACCEPTANCE: FAIL (early
  game)` — floors 1–5 median 7.0 mirror-days. 045 adds zero drift
  (display + option-list only). The early-game miss is 043's, was live
  before this ship, and is left for a 043 follow-up.
- Deploy: plugin `4773e1e` pushed (huemorgan2); vendored via
  `worldd/tools/vendor_game.sh`; outer commit `c9c75de` pushed;
  Render auto-deploy was stale so `render deploys create
  srv-d9ha3csvikkc73ff5rg0 --confirm --wait` ran →
  `dep-d9sek2pt0dsc73bihirg` live; `/health` → `"game":"0.59.0"`.
- Marketplace: 0.59.0 packaged (1071 files) and published to
  `official`; index checked immediately before (0.57.1) and after
  (0.59.0, sha256 `af16be23…a472bd8a` == local zip). The 0.57.1→0.59.0
  jump also closes the marketplace-vs-vendor skew.
- Production dojo walkthrough: **7/7 PASS** —
  `dojo/results/045-hold-and-endure-2026-08-10/summary.md` (outer
  repo). No regressions filed.
