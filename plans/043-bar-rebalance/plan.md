# 043 — the bar rebalance (a floor is a promise about its monsters)

## Problem

Designer verdict (2026-08-08, reading the /mechanics ledger): *"even at
level 5 I can kill some monsters with a 90% chance — that's too easy.
Monsters on each floor must be significantly harder, but with large
variability."* Measured on 0.56.0:

- **No minimum bar.** 81 monsters on floors 1–30 are 90%-killable more
  than 2 levels below their floor. Floor 5 still holds level-1 kills
  (blind cave-fish), floor 10 a level-3 wolf. Cause: `frail`/`feeble`
  archetypes scale HP/bite down without any floor-relative floor.
- **The teens sag.** Floor 16's kill levels are {10, 10, 10, 13} — its
  hardest monster dies three levels early and nothing sits at-floor.
  Reference gear (rungs → tiers + honing) grows faster than the linear
  `3.3·floor` monster curve.
- **Floors 1–3 taper backwards.** Floor 2 has five KL-1 monsters (83% of
  spawns), floor 3 four — trivial kills should thin out as you climb.
- **Pay ignores toughness.** Gold/XP key off the floor plus bolt-on
  multipliers (BODY_ROUNDS × BITE_PAY), so a floor's weakling and its
  terror pay from the same base. And XP overall is ~40% too generous —
  the level bar fills in a day at every level (see /mechanics LEVELS).

## The rule being bought

One ladder, the **bar**, 1–101: bar B = the design's reference loadout of
floor B (level `min(B, 30)`, rung `reference_rung(B)`, hone
`reference_hone(B)`). Below 30 the bar climbs mostly by levels; above,
entirely by steel. Then, per floor F:

1. Every monster is anchored to a **target bar** `T = clamp(F + offset,
   1, 101)` with `offset ∈ {−2 … +1}` read from its archetype traits:
   body `frail/lean −1, sturdy 0, hulking +1`, bite `feeble −1,
   fierce 0, savage +1`, sum clamped to [−2, +1].
2. **Anchored means measured**: the bar-T reference player beats it
   ~90% of the time (85% acceptable), one bar lower falls meaningfully
   short. Verified by the /mechanics Monte-Carlo, not by eye.
3. **The taper**: floor 1 is mostly bar 1; floor 2 keeps ~3 bar-1
   monsters, floor 3 one, floor 4+ none below F−2 (the offset clamp
   makes this structural). Every floor keeps 1–2 monsters at F+1.
4. **Pay follows the bar, not the floor**: `xp_per_kill(T)`,
   `gold_per_kill(T)`. The old threat multipliers retire — toughness is
   priced once, by the anchor. Armor/resist/flying/bulwark still pay
   their premium (`profile_gold_mult`), specimens still roll.
5. **XP −40% globally**: `XP_PER_KILL_SLOPE 4 → 2.4`, wardens and
   milestones cut the same way. Training prices stay — levelling slows.

## Mechanism

`creature_stats(floor, traits)` re-derives from the anchor instead of
stacking multipliers:

- `DEF = 3·T` (unchanged law, bar-indexed).
- Body sets the fight's **length**: `rounds = wilds_rounds(T) ×
  {frail .6, lean .8, — 1.0, sturdy 1.35, hulking 1.7}`, capped at 11.
- `HP = (expected bar-T player damage/round vs DEF) × rounds` — so the
  at-bar fight lasts by design, and a −2 monster melts for an at-floor
  climber.
- Bite sets the fight's **cost**: over the whole fight the monster deals
  `κ(bite) × reference_player_hp(T)` — calibrated κ ≈ .73–.81 by bar,
  ×{feeble .85, fierce 1.0, savage 1.1} (simulation puts 90% at bar T;
  the
  chip floor keeps even feeble prey lethal to a climber two bars low).
  ATK inverts from cost/rounds through the damage rule, exactly as
  BITE_COST did.
- Short bodies therefore hit harder per round at equal total cost —
  texture survives, lethality is anchored.

Content stays numberless: the YAML keeps saying `lean, savage`; the
engine now reads it as "bar F+0 … just faster". Floors 2–3 get a trait
retouch (fewer feeble/frail entries) for the taper; a 100-floor audit
fixes rosters missing an F+1 threat or spawning 4 identical offsets.

## What this does NOT touch

Wardens' stat law (already bar-ish via `_at_level_loadout`), milestone
bosses, specimen tables, deep hunt, energy, prey spawn fade, death law,
the forge ladder. The /mechanics page swaps KILL LV for KILL BAR (1–101)
and its simulator picks a bar instead of a level.

## The on-ramp (added during execution)

Bar 1 is defined as "level 1 in floor-1 reference steel" — so a fresh
climber must BE bar 1, or the floor eats every newcomer before their
first coin (measured: starter shiv + no armor won ~0% of floor-1
fights against the calibrated κ). Two moves close it:

- the gate issues the whole kit at creation: `gate_buckler` (5) and
  `gate_jerkin` (7) match the rung-1.0 forge bonuses — tier 0, never
  sold, never wear, worth nothing pawned. Doc v6 grants them to any
  older doc with a bare slot. Fresh HP starts at the armored pool.
- `WILDS_BAR1_SOFT = 0.75` softens ONLY bar-1 fight cost (the fresh
  weapon is 5 vs the reference 8); bars 2+ are the honest ladder.
  Measured: fresh prey 92–98%, at-bar ~90%, floor-1 savage 79%
  (band-warned), the F+1 hulk walls — and ≥3 of floor 1's six table
  weights stay uncut for a full-HP fresh character.

The /mechanics kill bar reads the FAIR class per shape — physical
(bow for flyers) unless armor out-halves resist, then the staff —
never magic's DEF-shaving shortcut against unarmored shapes.

## Acceptance

- /mechanics regenerated: every floor's kill bars lie in
  {F−2 … F+1} (±1 bar of Monte-Carlo wobble tolerated at the edges);
  floor 2 ≈ 3 bar-1 monsters, floor 3 ≈ 1, floor 4+ zero below F−2;
  each floor ≥ 1 monster at bar ≥ F, ≥ 1 at F+1 where the roster allows.
- XP/kill down 40% at every floor; gold on a floor now spreads with
  toughness (a bar F+1 terror out-pays a bar F−2 snack ~2.5×).
- `lint_floors()` clean; plugin + worldd suites green; vendor synced.
