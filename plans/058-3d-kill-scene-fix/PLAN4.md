# PLAN4 — make the 3D kill scene right

From investigation.md. Five workstreams, ordered so the scene is testable
after each. Law throughout: floor-1 death scene is 3D only, whole frame one
tint on black; wardens/floors 2+ untouched.

## A. Kill the wait

1. fight3d.js: drop `*_slash.glb` from the blade fetch set (dead code — the
   swing is procedural). Fetch set for a blade kill becomes player + blade +
   monster (~4.1 MB → after rigged monsters, similar).
2. fight3d.js: preload at module init on /play — after DOM idle
   (`requestIdleCallback`), fetch the GLBs for the player's race/line and all
   six monster GLBs into the loader cache; create the GL context and compile
   both shader programs against a dummy frame so the first kill starts hot.
3. mountKill: replace the blind 550 ms liberate timer with "assets ready +
   one rendered frame", min 550 ms for pacing.
4. worldd/app/main.py: add GZipMiddleware (text/html/json only, minimum size
   1 KB).

## B. Remove the old ending scenario (plugin change)

1. combat.py wild-victory: when kill3d is stamped, set `fx=None`. `_kill_fx`
   stays for wardens/first_clear/chat.
2. render.py: kill3d cards emit a bare `.banner` (aspect 320/112, #000, no
   mask, no inlined GIF). Keep `data-kill3d`/`data-tint`; add
   `data-fx="/static/.../{slug}.gif"` URL for the JS failure fallback.
3. fight3d.js mountKill: nothing to blank; on failure paint the fallback via
   CSS mask + tint from data-fx (same look as the old reel).
4. Tests: update test_kill3d.py — wild floor-1 victory asserts fx None +
   kill3d present; warden path still asserts fx.

## C. Background scenery, one-color (GL spritesheet)

1. Build script research/3d-fight/make_bg_sheets.py: demo2/backgrounds/{id}.gif
   → vertical 24-frame spritesheet PNG (320×2688, 1-bit) →
   worldd/static/site/fight3d/backgrounds/{id}.png (~20–40 KB each).
2. fight3d.js post shader: new `tBG` + `uBGFrame` uniforms; background branch
   (`a < 0.03`, not outline) samples the sheet — white → uInk, black → black.
   Frame advances every 100 ms, 2.4 s loop. Body branch already uInk.
   Whole frame = {uInk, black} by construction.
3. Load the sheet per creature id in ensureFor; missing sheet → black
   background (today's look), never a GIF.

## D. Readable ink (dark grey fix)

fight3d.js: before setting uInk, lift ink luminance to a floor (HSL L ≥ 0.55).
Server tints untouched. Runt `#5b5952` → readable warm grey; common already
bright; tough/alpha unchanged.

## E. Monsters walk on bones

1. Finish gen_monster_clips.py (running — 5/6 rigged, ember_shade walk left).
2. Copy `models/monsters/{id}/50_walk.glb` → site monsters/{id}.glb.
3. fight3d.js tripoMonster: AnimationMixer playing the baked walk clip;
   run-in = clip with timeScale ∝ travel speed; idle = paused frame +
   breathe; attack = procedural lunge layered, eased transitions; use
   SkeletonUtils-style clone or single live scene (no `clone(true)` on
   skinned meshes) — vendor SkeletonUtils.js.
4. Size fixes: feral_boar h 1.9, mock `wide` values.

## Verify & ship

- Harness screenshots per creature × specimen tint (incl. runt) at run-in /
  impact / freed beats; confirm one-color frames and moving legs.
- Local game kill on localhost:8890 end-to-end; screenshot.
- pytest (plugin), bump (coordinate: another session owns 0.78.0 uncommitted
  — release as 0.79.0 after theirs or independently if clear), vendor, commit,
  push, deploy.sh, package+publish. Fully authorized, no asking.
