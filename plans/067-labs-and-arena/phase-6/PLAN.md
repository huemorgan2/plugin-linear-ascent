# 067 phase 6 — the HUD aligned and named, the foe's kind icons, tiles on every live card

## Problem (roy, production 0.92.0 screenshot, 2026-08-18)
1. The two stat slabs are not aligned: the climber's sits at the top-left
   edge, the foe's is pushed down under it (phase 5 stacked them so they
   could not collide on a 320-wide frame). Neither carries a name.
2. The foe's kind (armoured / magic resistance / flying / bulwark) is not
   on the sheet — phase 5 dropped the badges in favour of the [i]; the
   original ask (thread start) had them as coloured icons: the armour
   icon on the DEF, the flying icon, the resistance icon with its level.
3. "No icons at the bottom of the scene": the screenshot is the VICTORY
   card (foe 0/68, "Grave-rat is defeated"). Phase 5 put the tiles inside
   the stage only for `phase == "round"`; victory / death / fled cards
   fell through to the regular row list under the log. And the round's
   tiles carry `later`, so they only fade in after the pane's typewriter
   finishes the body — a wide card with a long body shows a bare stage
   for seconds. Evidence: render.py `_arena_banner_html` (round-only),
   `render_scene_fragment` (`elif scene.options:` catches victory).

## Root cause
Phase 5 was cut to the round card and to a stacked HUD; the original
brief (kind icons, gear line, tiles on every card of the fight) was not
re-read against it.

## Fix
- HUD: one flex row `.ahuds` at `top:.5em`, climber's slab left, foe's
  slab right (right-aligned text), both top-aligned; the row wraps on a
  frame too narrow for both (foe slab drops under, still right-aligned).
  Each slab: `NAME` (bright, uppercase) / `HP ▓▓▓░ n/m` / `ATK n DEF n
  SPEED n`. The climber's slab adds a gear line: one glyph per held
  weapon (lead outlined gold, broken red), armour, shield (broken red),
  each with a data-tip. The foe's name line carries its kind icons
  (flying aether, magic resistance violet + `MR n%`, bulwark gold); the
  armour icon (orange) rides right after `DEF n` when the foe is
  armoured. Icons are the 16×16 t_* glyphs (`_aicon`), tips name them.
- Tiles inside the stage on EVERY live card that has options (round,
  victory, death, fled); the fragment never renders arena options under
  the stage while the arena is live. In-scene tiles drop `later` — they
  render at once; arena3d holds them while the beats play.
- Dojo: new checks — after the first strike the tiles are inside
  `.banner.arena`, visible (rect height > 0, opacity 1) and their art is
  an `<img>`; the HUD carries two `.aname`s; at fight end (victory or
  death) tiles are still inside the stage; a run with an armoured/flying
  foe shows a kind icon (asserted when the foe has one). Desktop 1440 +
  mobile 420 captures for the round and the end card.

## Verification
- `pytest tests/test_067_arena.py tests/test_067_labs.py -q`.
- Dojo `labs-arena` walkthrough green; captures reviewed by eye.
- Production /play after deploy: labs on, floor 6, first strike → names
  top-left/top-right on one line, tiles at the foot of the stage; the
  victory card keeps the tiles.

## Rollback
Revert the phase-6 commit (plugin + worldd), re-vendor 0.92.0, deploy.

## Execution status (2026-08-18)
- Done on plugin main (0.93.0 + this = 0.94.0; the release branch is
  retired — 069 shipped as 0.93.0 from main). render.py: `.ahuds` flex
  row at top .5em, `_astat_html(name/name_extra/def_extra/tail)`,
  `_aicon(tip)`, `_TIP_KIND`, gear line, foe kind icons + `MR n%`,
  armour icon after DEF; tiles inside the stage on every live card
  (round/victory/death/fled), no `later`; `_arena_tile_fallback` dresses
  the end card's borrowed gate-town menu from `arena._TILE_ICON/_LABEL`
  (extended: hunt, hunt_deep, keep, talk, gate, town, forge, heal, stew…).
- Tests: `tests/test_067_arena.py` 13/13 (+3 phase-6), `test_067_labs.py`
  6/6; full suite 1296 pass / 6 pre-existing fails (identical set without
  the change).
- Dojo 0039 (`dojo/results/0039-067p6-arena-hud-2026-08-18/`): 33/33
  (26 + S11×6 + S12); captures 420 + 1440 of the round and the end card.
  One flake seen on the first run: S6 settle 12.1 s under parallel load,
  5–7 s on re-runs.
- Iterated: death-card tiles first took the option label ("THE HEALER'S",
  "LIMP BACK TO") — reverted to the table labels (HEAL / TOWN).
- Not done: a cap on the stage's desktop stretch (760 px) — as phase 5.
