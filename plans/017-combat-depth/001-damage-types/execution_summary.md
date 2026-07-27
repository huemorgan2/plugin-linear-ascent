# Phase 001 — Execution summary

Shipped 2026-07-27 on branch `017-combat-depth`
(commit `63f33bf` + dojo/summary follow-up). 224 tests green.

## What landed

- **Typed damage** (`economy.py`): melee/ranged/magic per class; tier
  table Low ×0.75 / Med ×0.50 / High ×0.25 on both the plate (armor)
  and spellguard (resist) axes; magic ignores flat DEF; chip ≥1
  everywhere except melee-vs-flying = 0.
- **Defense profiles** (`engine/combat.py`): derived from traits at
  encounter start (`profile_from_traits`), stored on the encounter,
  named in the opener (`◆ plate Low`), and explained in strike prose
  ("its plate (Low) turns part of the blow").
- **Traits** (`content/schema.py`): tiered armor/resist + flying,
  bulwark, slow, fast; legacy `armored` maps to `armor_med` and is
  lint-forbidden on floors ≤10; `TRAIT_INTRO_FLOOR` staircase enforced.
- **Class starters + doc v2** (`economy.py`, `engine/state.py`):
  rusted_sword / basic_bow / worn_staff; lazy migration on load —
  warriors renamed silently, archers/sorcerers get an armory letter;
  idempotent, leaves bought weapons alone.
- **Floors 1–10 retrofit:** 4 encounters per floor, one new trait per
  floor per the staircase (floor 1 all-plain kindergarten); 10 new
  creatures with generated 1-bit banner art.
- **Class-option edges:** treeline shot loses its double vs Med+ plate;
  sleep refused free vs High spellguard; shield-wall counter 0 vs
  flying.
- **Gates:** `test_017_damage_types.py` (unit + 40-fight matchup sim,
  floors 1–10, all classes) and `test_smoothness.py` (closed-form
  floor 1–100 walk: rounds/risk/income, adjacent ≤25%, band ≤25%,
  trend ≤15%, income never cliffs down).

## Dojo results (local Luna + local worldd, qa007)

- **A — migration:** pre-017 v1 warrior loaded mid-session; pack shows
  "Rusted Sword", DB doc confirmed `version: 2`,
  `gear.weapon: rusted_sword`. Silent, as designed.
- **B — armor intro:** Shellback tortoise opener shows `◆ plate Low`
  under the art; warrior strike prose "its plate (Low) turns part of
  the blow" (4 dmg). Sorcerer (same monster): 16 dmg, no plate note —
  armor ignored. Archer treeline vs King's Guard (armor_med): "Your
  arrow snaps against its plate — 1 damage, no clean gap for a killing
  shot."
- **C — kindergarten:** floor 1 hunts (wolf, boar, goblin) show no
  profile line; the only ◆ on screen is the tactics hint.
- **D — agent:** 25+ ordinary acts added **zero** chat rows (0.17.2
  no-digest holds live). Asked the shard about the tortoise: it
  re-synced and explained plate-vs-melee in voice, correctly noting
  magic ignores plate. One slip: it called the current boar "Brackjaw"
  (the floor-1 boss) — grounding gap, folded into phase 007.

## Learnings (applied to future phase plans)

1. **Dojo navigation:** the floor list is only reachable via
   Roothollow → the tower gate; "Back to the tower gate" from a floor
   returns to that floor's CAMP. Scripted loops that miss this burn
   energy hunting the wrong floor. → noted in 002/003 dojo sections.
2. **Class-swap technique:** for multi-class dojo checks, swap
   `doc.clazz` + `gear.weapon` (and `ascent_world.frontier` for high
   floors, `energy_val`/`hp` for stamina) directly in the local worldd
   DB — much faster than creating three characters. → noted in 002.
3. **◆ glyph collision:** the tactics hint and the profile line share
   the same diamond; at a glance they read as one system. → 003 gives
   profiles their own icons and drops the bare ◆ from the profile line.
4. **Sim thresholds compress:** the drag gate landed at 1.6× plain
   rounds (not the planned 2×) because closed-form sims squash
   variance. → 008's at-scale sim reuses 001's constants verbatim.
5. **Income direction matters:** smoothness on income must allow
   upward steps and only forbid down-cliffs/regressions; rounds/risk
   need `_is_intended` matchup filtering or off-class monsters poison
   the averages. → noted in 008/010.
6. **Baseline churn is expected:** economy changes shift warden
   baselines (`test_008_pace`) — update deliberately with a dated
   note, don't loosen the test. → noted in 010.
7. **Agent grounding:** muted state lines should name the current
   enemy + floor so the sidekick can't misattribute ("Brackjaw" slip).
   → added to 007 task 2.

## Not done here (deliberate)

- Slow/fast are authorable and placed (floors 5, 10) but priceless
  until 002's chase model.
- Profile READABILITY beyond the opener line waits for 003's [i] card.
- Vendor sync + production deploy + publish: shipped with this phase's
  close-out (see repo/worldd commits).
