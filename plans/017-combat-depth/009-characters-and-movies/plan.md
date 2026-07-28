# Phase 009 — Characters, races, movies, kill FX

Goal: the cast matches the canon — three showcase characters (male elf
ARCHER, female human WARRIOR, giant dwarf WIZARD), halflings migrated,
dwarves rendered as giants everywhere, kill FX per damage type.

Can start in parallel any time after 001 (needs the bestiary names and
the damage-type kill hooks only).

## Tasks

1. **Race migration** (`engine/state.py` doc v4 — 005 took v3): 
   halfling → closest race, default human (an in-world pending-event
   letter explains the change and the retired luck bonus); creation
   menu drops halfling; `RACES` table updated. Luck-day flag/charm
   mechanics unaffected.
   005 retro: version-pinning tests break on every bump — assert
   `version >= N`, not `== N` (005 tripped 017's `== 2`).
2. **Art canon:** all character prompts updated to the three showcase
   characters + the giant-dwarf scale rule (two heads taller, wider —
   `vision/story.md` is canon). Creation scene blurbs re-checked.
3. **Intro movie:** regenerate the refugee/climber scenes with the
   three characters (Veo pipeline, `plans/016-intro-movie/` tooling);
   the dwarf must visibly loom.
4. **Kill FX ×3 (floors 1–3 first — approved staging):** each floor
   1–3 monster family gets melee/arrow/magic kill variants; `_kill_fx`
   picks by the landing damage type; renderer skips missing art
   silently (later floors ride 008 batches).
5. Icons/consistency pass: 16×16/32×32 1-bit constraint audit on
   everything 003–006 added.
   003 retro: trait icons ship as CSS-mask SVG data-URLs built from
   grids in `icons.py` (`test_017_info_card.py` asserts 16-wide grids
   and valid masks) — the audit extends those tests, not eyeballs.
   004 retro: the gear set now has weapon/bow/staff/focus/shoes/arrows
   glyphs and `icon_key` resolves weapons BY LINE (FORGE lookup) —
   audit that every catalog line/slot maps to a non-fallback glyph
   (`test_017_shops.py::test_weapon_icons_follow_the_line` is the
   pattern to extend), and that no new item kind ships wearing the
   pack crate.
   006 retro: 11 relic glyphs live in `icons.py` (`_RELIC_ICON` maps
   the four quivers onto one shared grid; strip potion borrows the
   draught glass) — the audit must cover BOTH icon surfaces: pack
   strip (`icon_key`) AND shop option rows (`render._opt_gear_icon`),
   which resolve independently. Assert every `economy.RELICS` slug
   returns a non-"pack" key through each path.
6. Vendor sync + deploy; version bump + publish.

## Tests / acceptance

- Unit: migration (halfling docs of each class), `_kill_fx` type
  selection, creation menu has exactly 3 races.
- Migration soak: run `ensure_current` over a snapshot of every player
  doc shape in the shared world (worldd export) — zero errors.
- Art review: side-by-side frames in the summary — dwarf scale is
  unmistakable; movie plays in `movie.html`.
- Dojo: create a character (3 races only); kill a wolf as each class
  and see three different endings.
  007 retro: click by `button.opt[data-opt="<id>"]`, not label text
  (labels embed key digits and [i] glyphs). If a kill FX rides a
  worldd effect, remember act-scenes render before effects land —
  one extra navigation before asserting state. And the ▣ fold marker
  exists now (`render.py` + `scene.to_text`): if the creation or
  post-kill scenes run long, fold, don't trim.
  008 retro (STALE-VENDOR TRAP — this one bit): the game TURN runs in
  worldd's vendored engine; Luna's editable plugin install only
  renders. Run `worldd/tools/vendor_game.sh` + restart local worldd
  BEFORE the dojo run, or you browser-test stale logic while unit
  tests lie green (008's first floor-15 fight had art but no
  lore/traits for exactly this reason). Kill FX + migration both live
  engine-side — same trap. Dojo mechanics that carry over: the
  teleport helper (`plans/.../008-.../dojo/teleport.py`) drops the
  reference player on any floor as any class — use it to reach each
  class's kill quickly; energy is `energy_val`/`energy_ts` (a regen
  pair, not a counter) when a refill is needed.

Exit: all green, published, worldd synced, `execution_summary.md`.
