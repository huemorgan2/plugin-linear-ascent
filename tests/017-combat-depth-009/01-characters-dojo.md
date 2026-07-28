# 017 phase 009 — dojo run: races, migration letter, typed kill FX

Real-browser test against the local QA stack (Luna :8765, worldd :8600,
docker `ascent-postgres` :5434, tenant qa007). Screenshots archived in
`plans/017-combat-depth/009-characters-and-movies/dojo/`.

## Preconditions (the 008 stale-vendor lesson)

1. `bash worldd/tools/vendor_game.sh` — the TURN runs in worldd's
   vendored engine; without the sync the browser tests 008 logic.
2. Restart worldd AND Luna — `render._fx_data_url` is lru_cached, so a
   Luna that booted before the kill GIFs landed caches the misses.
3. Kill FX art on disk: `pytest tests/test_017_characters.py -k ships`
   must be green first.

## Checks

1. **Creation: three races.** Fresh player (reset qa doc) — the
   registrar's slate offers exactly Human / Elf / Dwarf, no Halfling.
   Click by `button.opt[data-opt="dwarf"]` etc.
2. **Migration letter.** Set the qa doc `race='halfling', version=3`
   via docker psql, reload — the REGISTRAR letter renders once
   (headline "The Stone re-registers your line"), then never again;
   doc reads `race='human', version=4`.
3. **Typed kill endings.** Kill a floor-1/2 wilds monster as each
   class (teleport helper from 008 sets class+gear) and read the
   victory card's fx: warrior → `_kill_melee`, archer → `_kill_arrow`,
   sorcerer → `_kill_magic`. Three visibly different endings.
4. **Intro movie reshoots.** `plans/016-intro-movie/movie.html` — the
   refugee and muster scenes show the showcase cast; the dwarf looms
   two heads over the other two.

## Tools

- `plans/017-combat-depth/008-bestiary-at-scale/dojo/teleport.py
  <floor> [clazz]` — reference loadout on any floor as any class.
- Energy refills: set `energy_val` (float) — it pairs with
  `energy_ts`; `energy` alone does nothing.

## Results (2026-07-28, all PASS)

Preconditions held: vendor_game.sh synced, worldd + Luna restarted
(Luna restart mattered — `_fx_data_url` lru-caches misses).

1. **Three races.** Fresh doc walked the full intro movie (9 scenes +
   title) to the registrar's slate: exactly Human / Elf / Dwarf, no
   Halfling (`009-04-three-races.png`). Clicking "halfling" is a no-op
   (invalid option). Bonus: the reshoot scenes played in-game — scene V
   shows the three-character refugee walk, scene IX the muster with the
   giant dwarf looming (`009-02`, `009-03`).
2. **Migration letter.** Doc regressed to `race=halfling, version=3`
   via psql; reload rendered "ROOTHOLLOW · A LETTER FROM THE REGISTRAR /
   The Stone re-registers your line" (`009-08-registrar-letter.png`).
   After folding it: doc reads `human|4`, reload shows the square, the
   letter never re-fires.
3. **Typed kill endings.** Same floor, three classes, three different
   endings — each verified in the browser AND by the scene doc's fx:
   warrior → `wolf_kill_melee` (`009-05`), archer → `rat_kill_arrow`
   (`009-06`), sorcerer → `boar_kill_magic` (`009-07`). The victory
   card visibly holds the killer-over-monster tableau per type.
4. **Movie reshoots.** Verified in-game (check 1); movie.html reads the
   same events dir live.

Notes for the next phase: the pane iframe is index 3 of 4 on
`/p/linear-ascent` (brain/talk/voice come first) — select by src
containing `plugin-linear-ascent`. After editing the doc in psql,
reload the IFRAME and wait ~3s before clicking; clicks issued in the
same evaluate as the reload land on the stale scene.
