# Phase 3 — arena3d.js: the persistent turn-based stage

## Goal
On an arena card the website mounts a 320×300 one-color 3D scene in the
banner slot: player and monster face each other in idle stances, the
event script plays beat by beat (player turn → return → monster turn),
floating texts and HUD ride over the canvas, the log accumulates under
it. The scene persists across card swaps for the same fight.

## Steps
- `worldd/static/site/fight3d/fight3d.js`: `initGL` → `createStage({W,H,
  canvasClass})` returning the GL bundle; the kill scene keeps calling
  it with 320×112. `export {createStage, load, loadBG, ensureFor,
  buildPlayer, tripoMonster, burst, banishFx, arrowFx, magicFx,
  MONSTERS3D, PLAYERS3D, STRIKES, FLOOR_FRAC, warmFor}`. Effects take
  a `scene` argument (default `GL.scene`). No behaviour change for
  `.card[data-kill3d]`.
- `worldd/static/site/fight3d/arena3d.js` (new): 
  - observer on `#game` for `.card[data-arena]:not([data-a3d-done])`;
  - stage 320×300 (`VH` scaled so the figures keep the kill-scene
    pixel height; floor line at 0.91 of 300 → same ground), BG from
    `backgrounds300/<id>.png` (24 frames of 300 rows);
  - `Fight` singleton keyed on `foe.id + me.race:line`; on a new card
    of the same fight: re-attach the canvas, apply the new script;
    on a new fight: rebuild;
  - layout: player left x≈−0.9, monster right x≈+0.9 at gap 0;
    gap 1..3 → player slides back 0.35/gap (walk-back animation on
    `move:open|back`), monster steps forward on `foe move close`;
  - turn machine (`async play(events)`): for each event — strike
    (approach → swing/shoot/cast → impact/miss → return to mark),
    floating text spawner (HTML `.afloat` absolutely positioned over
    the head: `-XX HP` red on black rising 900 ms; `BLOCKED N` grey;
    `MISS` white with a 6-jitter shake 1 s), log line appended with
    a 120 ms delay after the beat; options stay disabled
    (`.arena-opts.busy`) until the script has played, then enable;
  - HUD: `.ahud.left` (HP bar, SPD, DEF, ATK, weapon icons, shield /
    armor icons with broken state) `.ahud.right` (name, HP bar, DEF,
    SPD, type icon: fly / armoured / magic-resist tier / regular);
    HP bars tween on each hp change;
  - victory: last event `die` → `banishFx` beat (reuse) then the
    card's own kill3d handling stays off (arena owns the slot; the
    card sets `data-arena` and NOT `data-kill3d` when arena is on).
  - death / fled: fade to black.
- CSS: appended to `SCENE_CSS` in render.py (`.banner.arena`, `.ahud`,
  `.afloat`, `.atile`, `.arena-opts`, `.alog`) — plugin owns the card
  grammar; JS ships none.
- `worldd/app/webplay.py`: import map unchanged; add `<script
  type="module" src="/static/site/fight3d/arena3d.js?v=1">`; bump
  `fight3d.js?v=13`.

## Verification
- `worldd/tests`: webplay HTML contains both scripts; `node --check`
  both modules; kill3d card path still mounts (existing tests).
- Dojo (phase 5).

## Rollback
Remove the arena3d script tag; revert fight3d.js (kill scene works
without the exports).
