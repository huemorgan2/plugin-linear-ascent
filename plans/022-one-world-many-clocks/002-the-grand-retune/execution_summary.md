# Phase 002 — The Grand Retune: execution summary

Status: **done** (deploy + version bump deferred to the end of the 022
run, per the agreed batching). 499 plugin tests + 55 worldd tests green.

## What shipped

One tuning pass over one set of constants, as planned:

- **`LEVEL_CAP = 30`**, `XP_NEED_BASE` 60 → 24. An all-energy hunter
  caps in ~22 days (gated 14–35 in `test_022_002_retune`). At cap the
  guildhall refuses with a line worth reading and ✦ is pure currency.
- **Gear carries growth**: weapon whole rungs `30T − 22` (anchored at
  the old tier-1 value of 8 so the first hour is untouched), shields
  `10T − 5`, armor `16T − 9`; `HONE_WEIGHT` {weapon 3, shield 2,
  armor 2}; **armor feeds max HP** at `GEAR_HP_PER_ARMOR = 4`; energy
  cap re-keyed to the gear band (`ENERGY_BASE_CAP + tier − 1`). Gear
  share of at-level ATK ≥ 60% from floor 50 (76.9% at 100).
- **Gates past the cap become floor gates**: tiers 4–10 and the deep
  shoe rungs ask for level 30 *plus* a frontier the war has earned
  (`gear_floor_req` / `rung_floor_req`); the Forge refuses deep steel
  with "the smith won't sell steel the tower hasn't earned".
- **The coordination curve** (research §4): `R100 = max(min(50, .5A),
  .10A)`; `N(F) = 1` for F ≤ 30 else `max(2, ceil(R100^((F−30)/70)))`;
  pool = `N × 8` honest strike-fight units; regen a single constant
  fraction (`SUSTAINED_FIGHTS_PER_HOUR / 16` ≈ 2.78%/hr — breakeven at
  N/2 by algebra, every floor); silence window 6h → 30h linear over
  floors 31–90; pity −3% per fully-closed wound. Milestone quorums ride
  the same curve via `milestone_quorum(floor, active)`.
- **The 001 banked-bar burst is closed structurally**: the largest bar
  is ~11 fights, every deep pool is ≥ 16 fights in the same units —
  gated numerically for A ∈ {reference, 200, 1k, 10k}.

## What we learned (the expensive lessons)

1. **The paper budget had drifted 70 points from the real fight.**
   `WARDEN_DMG_BUDGET = 1.07` claimed "win 65–85% through floor 30" in
   a comment from the 004 era — the measured at-level win rate was
   **0–36%** (and 100% of naive sims *looked* like wins because the
   daily death save ends the fight with the player at 1 HP and the
   encounter cleared — the sim's win predicate has to check the death
   event, not the encounter slot). The chip rule (013) and the range
   crossing had moved reality; nothing gated it. Retuned to **0.82,
   measured**: floors 5–29 win 59–88%, band average 76%, floors 1–4
   ramp ≥ 88%. `test_022_002_retune` now pins the real rate forever.
2. **Chip damage means deep survival is bought with HP, not DEF.**
   Monster chip (`raw/4`) ignores DEF, so at `GEAR_HP_PER_ARMOR = 3`
   the warrior's true prey win rate sagged to 78% by floor 93; at 4 the
   whole 80–100 band holds 86–95%. 4 is the measured value.
3. **A sim harness that re-implements a formula rots.** The 017
   bestiary harness pinned `p["hp"] = player_max_hp(floor)` — after the
   retune that was *half* the real pool at depth (floor-as-level, no
   armor HP). Harnesses must read `state.max_hp(p)`. Related: 20 sims
   put ±10% noise on an 80% gate (floor 95 read 75% while its true rate
   was 87%) — the at-scale bestiary now runs 40, same as floors 1–10.
4. **Two honest exceptions written into old laws**: wilds HP may dip
   ≤ ~2.2% on the two floors after a deep band start (the reference
   re-hones from zero on fresh steel); warden ATK re-derives (floor-1
   warden 14 → 15) while the **HP column is pinned byte-identical** to
   the pre-022 curve — the retune moved who the warden is tuned
   against, never how big a boss is.
5. **Edge truths worth keeping**: at N = 2 (floor 31, small worlds) one
   sustained blade exactly *breaks even* — zero net progress, and the
   silence window eats the wound when he sleeps; a world of one gets
   the authored table quorum, never the curve's.

## The era model (codified, modeled — not yet measured)

`test_022_002_retune` walks A = 200 / 1,000 / 10,000 through a
documented arithmetic: solo band ~30 days, then per deep floor
`max(1.5 organize-days, 1.2N ÷ (A/7))` — weekly rally appetite, +20%
bar overhead tied to the live regen-during-window constants. All three
populations land ≈ 135–137 days (4.5 months) inside the 120–180 gate.
The model exists so a constant change that reshapes the era turns a
gate red; real-era telemetry must eventually calibrate it (logged in
`we_have_to_continue_this.md`).

## Deliberately regenerated pins

`GOLDEN_WARDENS` (100 tuples), `GOLDEN_GEAR_GATES` + new floor-gate
golden, the 008 pace baseline, the economy design tables, the 017 shop
tables (mids moved with the rescale), and the shoes ladder (capped
levels + floor gates). `energy_cap` left the 021 level-typed AST guard
— it is gear-tier-typed now.

## Files

`economy.py` (the pass), `engine/state.py` (gear band, energy cap,
weighted hone, armor HP), `engine/social.py` (cap refusal, quorum),
`engine/core.py` (floor-gated racks + purchases, census quorum),
`engine/combat.py`, `sheet.py`, `engine/tips.py`, `unlocks.py`,
`worldd/app/social.py` (census-passed warden + quorum), tests as above
plus new `tests/test_022_002_retune.py` (13 gates).
