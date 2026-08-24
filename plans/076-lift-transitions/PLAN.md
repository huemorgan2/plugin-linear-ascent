# 076 — Lift transitions (ride the elevator between floors)

## Problem

Changing floors is instant: the player clicks a `floor_N` row at the gate (or
"Return to Roothollow") and the new place card just replaces the old one.
There is no sense of riding the tower lift. Roy asked (2026-08-24): when the
player climbs UP through the gate, play the ascending-elevator animation;
when the player goes DOWN to a lower floor or back to Roothollow, play the
descending one — screen darkens, the animation plays, and the new place
appears behind it.

The two animations already exist (this plan's prerequisite, generated
2026-08-24 via `tools/generate_event_gifs.py`, slugs `lift_ascent` /
`lift_descent`):

- `plugin_linear_ascent/content/art/events/lift_ascent_320x112.gif`
- `plugin_linear_ascent/content/art/events/lift_descent_320x112.gif`

Both are white-ink-on-alpha, 320x112, 61 frames @ ~12fps (~5.1s), play once.
They are in the plugin only — NOT yet vendored into
`worldd/vendor/plugin_linear_ascent/`, so the deployed site cannot serve them
today.

## Root cause

Not a defect — a missing feature. No transition layer exists in the pane, and
the direction of a floor change is not on the wire (scenes carry `location`
but no up/down signal).

### Follow-up defect found in browser acceptance

The GIF is currently the CSS mask on `.car` itself. Its transparent pixels
therefore reveal the destination card, making the elevator frame look
transparent instead of like a solid display. The destination ordering is
already correct: `showScene` inserts `d.fragment` before `playLift()` mounts
the overlay, so the arriving card initializes beneath the animation.

## Fix — two phases

### Phase 1 — plugin: direction on the wire + pane overlay

**Goal.** Every act response that changes the player's floor carries
`lift: "up" | "down"`; the `/play` pane shows a full-screen darkened overlay
playing the correct lift GIF once (~5.2s) while the new place card is already
rendered behind it, then fades out. No overlay on refusals, page load,
re-sync, or peek.

**Steps.**

1. `engine/scene.py` — add optional field `lift: str = ""` to `Scene`
   (`scene.py:83-200`), emit in `to_dict` (`scene.py:370`) only when non-empty,
   accept in `from_dict` (`scene.py:436`). Follows the existing
   forward-compat pattern (`_known()` drops unknown fields on old clients).
2. `engine/core.py` — set the field at the only two places a floor changes:
   - `_gate_pick` success path (`core.py:3350-3352`): capture
     `old = p["floor"]` before assignment; on the returned scene set
     `lift = "up" if n > old else "down"` (equal floors: leave empty).
     Applies to both the first-visit `_floor_movie_scene` and the normal
     `_floor_arrival_scene` returns.
   - `option == "town"` return-to-Roothollow (`core.py:1419-1428`): set
     `lift = "down"` only when `p["floor"] > 0` before the reset (entering
     the square from ground level is not a ride).
   Refusal paths (`core.py:3336-3348`) stay untouched — no `lift`.
3. `render.py` — emit `data-lift="{scene.lift}"` on the card wrapper next to
   `data-loc` (`render.py:2629-2666`), only when set.
4. `pane.py` — the overlay:
   - CSS beside `#fblight` (`pane.py:294-299`): `#liftlay` —
     `position:fixed;inset:0;z-index:140;background:#000000cc;display:flex;
     align-items:center;justify-content:center;opacity:0;transition:opacity
     .35s;pointer-events:none`, `.on{opacity:1}`. z-140 sits above `#fblight`
     (130) and `#latoast` (120). Background is translucent black so the new
     place is dimly visible behind — "the new place appears in the back".
   - Inside: one div, GIF as alpha mask over tint (the house pattern,
     `render.py:2371-2374`): `width:min(92vw,640px);aspect-ratio:320/112;
     background-color:#8b93a7` (DIM — the slugs' generator tint);
     `mask-image:url('/static/fxart/lift_ascent_320x112.gif?t='+Date.now())`.
     The `?t=` nonce restarts the one-shot GIF from frame 0 every ride — the
     proven mechanism (`worldd/static/site/site.js:201-214`,
     `worldd/static/intro-movie/index.html:123-126`). Full filename with the
     `_320x112` suffix — bare slugs 404 on `/static/fxart/`
     (known `fight3d.js` degrade bug; do not copy it).
   - JS in `showScene` (`pane.py:444-465`): after `game.innerHTML =
     d.fragment`, read the card's `data-lift`; if `"up"`/`"down"`, mount
     `#liftlay` with the matching GIF, add `.on`, then after `LIFT_MS = 5200`
     remove `.on` (0.35s fade reveals the new place) and remove the node.
     A new ride while one is playing replaces the overlay (fresh nonce).
     Triggered only from act responses inside `showScene` — the initial
     `pane/scene` load and `peek` re-sync never pass `data-lift` because the
     stored scene is re-rendered only on transition acts; guard anyway by
     playing only when `d.event_kind` comes from an act (the `call('/act')`
     path), not from the boot fetch.
5. Version: `plugin_linear_ascent/version.py` → `0.99.1`.
6. Targeted tests, then full plugin suite (`pytest plugin-linear-ascent/tests`):
   - `tests/test_076_lift_transitions.py` (new; model on
     `test_event_fx.py:24` and `test_071_figure3d.py`):
     - gate pick to a higher floor → scene dict has `lift == "up"`
     - gate pick to a lower floor → `"down"`
     - `town` from a floor > 0 → `"down"`; from floor 0 → no `lift` key
     - sealed/underlevel refusal → no `lift` key
     - `render_scene_fragment` of a lifted scene contains `data-lift="up"`
     - pane JS contains `liftlay` and both `lift_*_320x112.gif` URLs
   - both event GIFs exist in `content/art/events/` (existence probe like
     `combat.py:28`).

**Verification.**
- `pytest tests/test_076_lift_transitions.py` green, then full suite green.
- Local worldd (`uvicorn app.main:app` in `worldd/`, after Phase-2 vendor or
  with the plugin installed editable): in `/play`, ride floor 1 → floor 2:
  screen darkens, ascending lift plays once, fades, floor-2 camp behind.
  Ride down and "Return to Roothollow": descending lift. Refused gate
  (sealed): toast only, no overlay.

**Rollback.** `git revert` of the phase commit in `plugin-linear-ascent`
(single commit). The `lift` field is optional-on-the-wire: old clients drop
it (`_known()`), so a plugin-only revert is safe at any point.

### Phase 2 — worldd: vendor, coded tests, dojo, deploy

**Goal.** The deployed site serves both GIFs and plays the transitions;
dojo scenario recorded PASS.

**Steps.**

1. Vendor: `bash worldd/tools/vendor_game.sh` (rsync mirrors the whole
   package — the two GIFs land in
   `worldd/vendor/plugin_linear_ascent/content/art/events/` and serve
   immediately at `/static/fxart/lift_{ascent,descent}_320x112.gif` via the
   fxart mount, `worldd/app/main.py:55-60`). Both live system and
   provisioning path are this one step — the vendor dir is committed.
2. worldd tests (`worldd/tests/`):
   - extend `test_web_play.py`: act that changes floor returns a fragment
     containing `data-lift`; `/play` HTML contains `liftlay`.
   - static-asset existence for both GIFs (pattern: `test_site.py:59`).
   - run the full worldd suite.
3. Dojo scenario `luna/dojo/tests/lift-transitions/scenario.md` (five
   sections, model: `labs-figure3d/scenario.md`):
   - Preconditions: local worldd on :8000 with the 0.99.1 plugin vendored;
     a player at Roothollow with gate access to floor ≥ 2.
   - Scenario: square → gate → ride up (screenshot mid-overlay), wait for
     fade (screenshot), ride down, return to Roothollow, attempt a sealed
     floor.
   - Expected: correct direction GIF each way; overlay darkens but the
     arriving place is visible behind; overlay gone ≤ 7s after click; play
     is not blocked afterwards; refusal shows no overlay.
   - Fail: wrong direction; overlay never fades; place swaps with no
     animation; animation replays on reload/peek; 404 on either fxart URL.
   - Verify: `curl -sI /static/fxart/lift_ascent_320x112.gif` → 200;
     fragment HTML of the act response carries `data-lift`; browser console
     free of errors during the ride.
   - Run it; write `dojo/results/NNNN-076-lift-transitions-<date>/`
     (summary.md, PASS/FAIL table, screenshots). Regressions filed, not
     quietly fixed.
4. Commit (secret-scan first, house message shape:
   `0.99.1: lift transitions (076); vendor 0.99.1; dojo NNNN …; plugin
   pointer <sha>`), push, deploy via `worldd/tools/deploy.sh` (it hard-fails
   on a version mismatch between plugin and vendor — bump + vendor happened
   together), poll to live.
5. Post-deploy verification (part of the deploy): both fxart URLs return 200
   on production; one real ride up + down on production `/play`.

**Verification.** Steps 2, 3 and 5 above are the proof: suites green, dojo
PASS with screenshots, production URLs 200 + live ride observed.

**Rollback.** Revert the worldd commit (vendor delta + tests) and redeploy
the previous version via `deploy.sh`; the plugin revert is Phase 1's
rollback. The GIF files themselves are additive and harmless to leave.

## Operational notes

- The working tree already carries unrelated uncommitted edits
  (`worldd/app/webplay.py`, `worldd/tests/test_web_play.py`,
  `worldd/vendor/plugin_linear_ascent/{pane,render}.py`, untracked `luna/`).
  Commit this plan's changes separately; do not sweep those in.
- `lift_ascent`/`lift_descent` raw takes are archived at
  `plugin-linear-ascent/content/art/events/raw/` (outside the package, not
  shipped) — reshoot with
  `python3 tools/generate_event_gifs.py lift_ascent lift_descent --force`.
- Overlay length: the GIFs run ~5.1s + 1.5s final-frame hold baked into the
  file; `LIFT_MS = 5200` starts the fade as the hold begins. If a longer
  hold is wanted later, tune the constant only — no regeneration needed.
- The 038 mercy-reel precedent shows Chromium shares animation clocks for
  identical image URLs — the `?t=` nonce is load-bearing; keep it.

## Follow-up — opaque animation stage

**Goal.** Both ascent and descent rides display inside an opaque black
320:112 stage. The destination remains mounted first beneath the overlay, so
its art, Figure3D portrait, wiring, and reveal effects can load while the lift
animation acts as the transition loader.

**Steps.**
1. Change `#liftlay .car` into an opaque black positioned container.
2. Add `.car .ink` as the full-size DIM-coloured layer that receives the GIF
   mask. Transparent GIF pixels now show the black stage, not the destination.
3. Keep `game.innerHTML = d.fragment` before `playLift()` and add a regression
   assertion for that ordering.
4. Verify ascent and descent in a real browser: black stage behind the GIF,
   destination card present underneath during the ride, and final destination
   immediately usable after the fade.

**Verification.**
- Targeted 076 tests assert the `.ink` layer, opaque `.car`, and destination-
  before-overlay ordering.
- Browser screenshots cover both directions mid-animation and after fade.
- No overlay on boot, peek, reload, or refusal.

**Rollback.** Revert the `.car`/`.ink` CSS and DOM change. The lift direction
wire field and destination scene remain unaffected.

## Execution status — opaque loader follow-up (2026-08-24)

- Implemented an opaque black `.car` stage with a separate masked `.ink`
  layer in plugin source and the local worldd vendor.
- Preserved and regression-tested destination-first ordering:
  `game.innerHTML = d.fragment` runs before `playLift()`, while the destination
  wiring and effects continue beneath the overlay.
- Targeted plugin verification: `11 passed`.
- Targeted worldd verification: `2 passed` (`-k 076`).
- Full plugin suite: `1356 passed, 1 skipped, 1 xfailed, 4 failed`; all four
  failures are the already-recorded unrelated class/kill3d failures from the
  original 076 dojo run.
- Local browser: ascent and descent both PASS. Each showed a 640x224 opaque
  `rgb(0, 0, 0)` stage, the correct nonce-bearing GIF on `.ink`, destination
  `data-loc` present during the overlay, removal in about 5.6 seconds, and an
  immediately usable destination. No console or network errors.
- Deployment was not performed.

## Execution status (2026-08-24, original plan — not the opaque-stage follow-up)

- Phase 1 (plugin): committed 898015b, version 0.99.1. Targeted tests
  10/10; full suite 1342 passed, 4 pre-existing failures filed
  (test_033 treeline, test_048 no_clazz, test_kill3d ×2 — reproduced at
  pre-076 HEAD 0c734e7).
- Dojo 0047 (local): 21/21 PASS, screenshots in
  `dojo/results/0047-076-lift-transitions-2026-08-24/`.
- Phase 2 (worldd): committed 588b712 — vendor re-cut from plugin
  committed HEAD (the prior vendor was a stale 0.99.0 cut), two 076
  tests added to test_web_play.py. test_names / presence / social_api /
  leaderboard failures were shared-:5434-DB contention from a concurrent
  pytest run — 32/32 pass on an isolated database (3× for test_names).
  Not a 074 regression.
- Deploy: dep-da681pojo6nc73c5dnvg, 0.97.3 → 0.99.1 live.
- Post-deploy: both fxart GIFs 200 image/gif (163831 / 152630 bytes) on
  production; dojo walkthrough re-run against production — 21/21 PASS
  (ascent + descent rides observed, reload quiet, refusal rideless).
