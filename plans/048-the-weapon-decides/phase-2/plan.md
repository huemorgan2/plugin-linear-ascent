# Phase 2 — trained ranks in the swing + migration

Goal: the rank shape lives on every player doc and drives the roll
of the held weapon; legacy docs migrate. Classes STILL gate
actions — only the roll changes. Rank 6 ≈ old feel: live players
feel no nerf (new players get blade 2 and feel the ladder).

## Tests first (red) — append to test_048_the_weapon_decides.py

1. Formulas: `TRAIN_MISS_PCT(R) == max(0, round(25-2.5R))` and
   `TRAIN_ROLL_FLOOR(R) == (30+4R)/100` for R 0..10.
2. Costs: `train_xp` 20/57/104/160/224/294/371/453/540/632;
   `train_gold(R, front) == round(8*pillar(front)*R)`.
3. New docs: `new_player` → after creation
   `p["training"] == {"blade":2,"bow":0,"staff":0}` (any class —
   class only sets which path via migration-equivalent grant; see
   note below).
4. Swing (seeded RNG, monkeypatched `random`): at rank 0 a roll
   below miss threshold yields a miss event; damage bounded in
   `[floor(R)*ATK_eff, ATK_eff]`; rank 5 → no old-feel change
   (min swing 50%, miss 12.5%→ round(12.5)=13%? — assert exact
   formula values, feel-equivalence asserted as floor .50 vs old
   .50).
   NOTE: `TRAIN_MISS_PCT(5)=13`, old system had 0 miss on-class.
   The "rank 5 ≈ today" anchor from the plan holds for the FLOOR
   only; the no-miss point is rank 10. On-class docs migrate to 6
   (miss 10%). Flag in summary: live players DO gain a 10% miss
   they did not have. Mitigation decided in plan: keep — training
   to 10 is the new consistency game. Assert what ships.
5. Migration: a doc with `clazz:"archer"`, no `training` → on
   first `current_scene` load: `training {"bow":6, others 0}`,
   one-time card mentioning "School" + "Bow — trained rank 6",
   shown exactly once.

## Code (green)

- `state.py`: `training` in `new_player`; `ensure_training(p)`
  migration hook (called from core.current_scene entry) using
  `PATH_OF_LINE`-style map {warrior:blade, archer:bow,
  sorcerer:staff}; migration card flag `p["flags"]["school_migrated"]`.
- `economy.py`: `TRAIN_MISS_PCT`, `TRAIN_ROLL_FLOOR`, `train_xp`,
  `train_gold`, `PATH_OF_LINE`.
- `combat.py` `_player_hit`: resolve held weapon line → path →
  rank; roll `uniform(floor*atk, atk)`; miss chance first (eats
  the round, monster answers); miss text names the hand (S5 text
  lands ph 5, a plain version now).

## Green =

new tests + full suite. Watch: any test asserting exact damage
ranges `[ATK/2, ATK]` now sees `[0.54*ATK, ATK]` at rank 6 — fix
by pinning training to 5 in those tests via helper kwarg
(`training={"blade":5}`) to preserve their meaning; list them in
the summary.

Commit: `048 phase 2: trained ranks drive the swing + migration`.
