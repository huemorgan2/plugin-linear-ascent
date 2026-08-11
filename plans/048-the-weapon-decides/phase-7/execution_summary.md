# Phase 7 — execution summary

Commits: plugin `3c0eb0b` — `048 phase 7: content retagged to types`;
worldd `mechanics: path×rank ledger + TRAINING tab` (parent repo).
Full suite 1061 passed (test_034_worldd excluded as baseline-red),
1 skipped, 1 xfailed.

## What shipped

- **T7 tests** (test_048_retag.py, 18 tests, red-first): native
  vocabulary enforced (legacy armor_*/resist_*/flying/fast/slow
  REJECTED by the linter), one type trait per monster, no YAML carries
  a legacy trait, the intro staircase survives in type words, the
  classroom census, the ≥2 pool rule measured.
- **schema.py**: ALLOWED_TRAITS = the native set; `_check_traits`
  (vocabulary + staircase + one-type-per-monster) runs on every floor
  load; TRAIT_INTRO_FLOOR = {armoured 2, magic_resist 3, fly 4,
  bulwark 6}; `_class_pool_errors` restored to ≥2 via
  `economy.type_of`.
- **economy.py**: `type_of(traits)` is the native reader (fly >
  magic_resist > armoured > plain); profile_from_traits and
  creature_stats read it; `type_from_traits` survives for
  doc-migration tests only — no runtime caller.
- **The retag** (phase-7/retag.py, idempotent, assert-counted): 100
  files, 320 trait lines rewritten; mechanical map (flying→fly,
  resist_*→magic_resist, armor_*/armored→armoured, fast/slow deleted —
  speed rides the type) + 18 hand flips + 1 bite soften, each with its
  flavor and law written in the script's docstring.
- **The measured pool gate** (test_017_damage_types) restored to ≥2 —
  both places now match the schema lint, closing the phase-5 note.
- **worldd /mechanics**: fight model speaks 048 (path×rank: miss
  chance + roll floor per rank, TYPE_MULT triangle, rank-8 gap draw
  gate); FLOORS tab shows TYPE sign column, HITS ⚔/➶/✦ per path,
  young-tower bounty on the floor headers; new TRAINING tab (rank
  costs with cumulative XP and the fits-the-bar column, miss/worst-
  swing curves, rank gates, School merchandise, mastery teeth); sim
  takes path + rank (0–10, default the rank-6 reference) instead of a
  class dropdown; the dead off-class weapon tax removed from the page.
  Regen ran against the sibling 048 plugin (ASCENT_GAME_PATH) — the
  vendor is still 047; the release-day regen re-runs post-vendor per
  the release flow.

## Census law — amended (design decision, flagging for roy)

The plan's N8 said "every floor 1–10 spawns all three signs." Floor 1
carries no flyable flavor and floors 1–3 ARE the 017 intro staircase
(plain → plate on 2 → spellguard on 3 → wings on 4). Shipped law:
**floors 4–10 carry all three signs; floors 1–3 keep the staircase**
(floor 1 all plain, floor 2 ⊆ {plain, armoured}, floor 3 ⊆ {plain,
armoured, magic_resist}). Pinned in test_classroom_floors_spawn_every_sign.

## The flip table (the deliberate part)

| Floor | Monster | Flip | Why |
|---|---|---|---|
| 4 | lamptree_wight | armoured | classroom sign; above-bar danger fight — costs no path its pool (glade_stag reverted to plain: it was blade's 2nd measured farmable) |
| 5 | downs_courser | fly, bite dropped | classroom; fierce+fly illegal below sky_hook@6 |
| 6 | vault_weaver | armoured | chitin-plated; above-bar |
| 7 | rabid_boar | armoured | tusk-plate; above-bar |
| 8 | greywell_ogre | armoured | slab-plates; above-bar |
| 9 | shadow_wolf | armoured | classroom sign on the at-bar danger fight (pylon_adder reverted: armoured at ×0.5 is sub-80% for blade even a bar down) |
| 10 | courier_hound | savage→fierce | blade/staff's 2nd measured farmable — lean+fierce steps one bar down |
| 24 | marsh_ghoul_crew | plain | pool rule |
| 42/47 | mirage_wisp / pale_fire | fly | pool rule |
| 72/74 | night_mare / skirmish_shade | armoured | pool rule |
| 100 | crown_regalia / kings_shadow | armoured / fly | pool rule |
| 45/57/62/75 | kiln_salamander, spray_wolf, hold_drake, black_crake | plain | pool second pass — bulwarks don't count and each is its band's only bulwark |

## Errors found and fixed

- **retag.py was not idempotent**: already-native type traits fell
  into `kept`, so a re-run appended duplicates (`[feeble, fly, fly]`)
  and plain flips could not strip. Fix: native types route into
  `natives` so every run re-decides the one type. Verified: third run
  rewrites 0 lines.
- **13 legacy-fixture failures** after the linter flip: tests built
  profiles from ("flying",), ("armor_med",) etc., which now read as
  plain — silent premise deaths surfaced as assertion failures.
  Swapped to native literals in test_017_damage_types,
  test_048_visible, test_048_the_weapon_decides, test_025.
- **The measured ≥2 gate is stricter than the lint**: the lint counts
  ×1.0 targets; the gate counts winrate ≥80%, which excludes at-bar
  and above-bar shapes. Floors 4, 9, 10 each had a classroom flip (or
  a pre-existing roster) that left one path a single measured
  farmable; fixed by moving the sign to an already-unfarmable monster
  (4, 9) or softening a bite (10).

## Learnings

1. **Retag scripts must be idempotent in the target vocabulary.** A
   rewrite that only recognizes the OLD names corrupts on re-run.
   Route already-native tokens through the same decision as mapped
   ones; verify with a run that must rewrite 0 lines.
2. **A sign is a tax — put it on monsters nobody farms.** armoured at
   ×0.5 drops blade below the 80% farm line even one bar down. When a
   census demands a sign on a floor, ride it on the at/above-bar
   danger fight, never on a sub-bar farm target.
3. **Lint ≥2 and measured ≥2 are different laws.** The lint counts
   triangle answers; the gate counts winnable fights. Design to the
   measured one — it subsumes the lint.
4. **The mechanics regen needs the sibling plugin until vendor day**
   (ASCENT_GAME_PATH); the release flow's post-vendor regen stays
   mandatory or the page carries stale numbers (the 0ee2aee lesson).
