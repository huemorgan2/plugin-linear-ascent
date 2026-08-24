# 071 — Labs: the 3D climber in the profile

## Problem (roy, 2026-08-24)
The profile figure is a frozen 100×200 (giant 140×260) 1-bit PNG — one
pose per race, no gear. The slots around it change; the body does not.
Roy wants the portrait to be the **3D-rendered climber**, breathing in
a calm still, wearing and holding what is actually in the slots:

- the race (human / elf / giant) is the body, and it should read like
  the existing 1-bit portrait
- a **staff** is in the hand
- a **sword** hangs on the hip
- a **bow** rides the back
- the **luck charm** sits on the neck
- **boots** on the feet, **armour** on the body, **shield** on the arm
- swapping a weapon changes how it is held (the three rules above)
- hovering a slot icon **highlights** that piece on the body (colour
  is allowed — the only break from 1-bit)
- render is 1-bit, at the portrait's current resolution
- **Labs on/off**. Isolated folder. Drop = delete the folder + the
  flag. Arena (067) stays untouched.

Items through **player level 10** get their own Tripo3D meshes
(text→model + 1-bit-aware texture), generated with the session's
`TRIPO_API_KEY`.

## Root cause / why it is not a patch
The portrait is a static PNG chosen by race (`render._portrait_slug`).
Nothing on the wire describes worn gear as a 3D kit, and nothing on
`/play` mounts a canvas in that slot. Arena/fight3d already has the
1-bit post and the three race rigs, but it is a fight stage that
always puts the lead weapon in the right hand — the opposite of the
hold grammar wanted here. Coupling this to `fight3d.js` would make
the Labs "delete the folder" contract a lie.

## Design — isolation contract (067 law)

- **`p["labs"]["figure3d"]`** — bool, default off. Named only in
  `engine/labs.py`. Empty `floors` = every floor. Off = today's
  `<img class="portrait">`, byte-identical.
- **`engine/figure3d.py`** — payload builder only. Reads slots, writes
  a dict. No combat, no economy change.
- **`Scene.figure3d`** — top-level, optional. Old clients drop it.
- **`worldd/static/site/figure3d/`** — the whole feature: `figure3d.js`,
  `vendor/GLTFLoader.js`, `models/`, `tools/gen_items.py`,
  `catalog.json`. Imports `three` from the page import map. Does **not**
  import `fight3d`. Player GLBs are **copies** of the fight3d rigs
  (they already match the portraits).
- **Promote** = flip the default on, delete the PNG branch, delete the
  flag. **Drop** = delete the folder + `figure3d.py` + the
  `FEATURES` row + three render/webplay lines.

## Hold grammar
Typed by weapon **line**, not by "lead":

| path   | bone        | rest |
|--------|-------------|------|
| blade  | left hip    | hanging, edge down |
| bow    | upper spine | diagonal across the back |
| staff  | right hand  | upright, ferrule near the ground |
| shield | left forearm | face out |
| focus  | left hand / belt | small orb / lens |
| armor  | spine       | chest overlay |
| shoes  | each foot   | one mesh cloned |
| charm  | neck        | pendant on a cord |
| potion / relic in charm slot | belt | flask / pouch |

Two blades: lead on the left hip, the next on the right. Two staffs:
lead in the right hand, the extra on the back. Missing GLB → family
fallback (`blade` / `bow` / `staff` / `shield` / `armor` / `boots` /
`charm`).

## 1-bit (vision/1bit-images.md + fight3d post)
Native canvas **100×200** (giant **140×260**) — the PNG grid. CSS
already sizes `.gearmap .pwrap .portrait` to 258px / 210px phone with
`image-rendering: pixelated`. Post pass: Bayer 8×8, 6-step luminance,
near-side depth ink, transparent stage (the card is black). Designed
for the 1-bit lesson: light-to-mid textures, no photoreal micro-detail,
silhouette that survives the grid.

Hover is the one colour exception: a saturated fragment skips the
Bayer and paints the slot's ink (gold weapon, cyan charm, …).

Calm motion: the rig's idle clip if present, plus a slow spine/head
breathe (fight3d's `breathe` sine, ~0.4 Hz). No turntable.

## Models (Tripo)
`figure3d/tools/gen_items.py` — resumable, key from
`research/3d-fight/3d models/.env` (`TRIPO_API_KEY`) or the env.
Pipeline per item (same as `gen_models.py`): text-to-model
(`face_limit` 2000, `smart_low_poly`) → texture prompted for the
1-bit band → `models/items/<slug>.glb`. No rig. 67 plain forge
pieces with `rung_player_level_req <= 10` plus `luck_charm`.
Keen/warded reuse the plain mesh (tint later if we want). Starter
blade/bow/staff already exist; they are copied in as family
fallbacks and also generated under their slugs.

Player bodies are **not** regenerated — the fight3d Tripo rigs
(`human.glb` / `elf.glb` / `giant.glb`) were built to the portraits.

## Fix — phases
1. **Labs + payload + render hook** — flag, `figure3d.py`,
   `Scene.figure3d`, canvas slot when on, `<img>` when off.
   `phase-1/PLAN.md`.
2. **The 1-bit portrait stage** — `figure3d/` folder, JS, idle
   breathe, race body, hold grammar on family fallbacks.
   `phase-2/PLAN.md`.
3. **Tripo items through level 10** — generator, catalog, GLBs.
   `phase-3/PLAN.md`.
4. **Hover highlight + worn overlay** — slot hover colours the
   matching mesh; armour/boots/charm/shield attach from the catalog.
   `phase-4/PLAN.md`.
5. **Tests + vendor + 0.98.0** — pytest, dojo, bump, vendor copy.
   `phase-5/PLAN.md`. Then deploy (roy: do it).

## Verification (whole plan)
- Labs off: profile HTML has `<img class="portrait">`, no
  `data-figure3d`, no canvas. Pixel-compare against HEAD for a
  stock climber.
- Labs on: canvas 100×200 (giant 140×260), `data-figure3d` JSON
  lists race + worn slugs; switching a weapon updates the hold;
  hover on the sword slot tints the hip blade; charm on the neck;
  boots on the feet.
- `p["labs"]["figure3d"]` round-trips. Mid-fight Labs still refused
  (067). Arena path untouched.
- 67+1 GLBs in `figure3d/models/items/` (or family fallback if a
  Tripo task fails — catalog records it).
- Plugin suite: new `test_071_figure3d.py` green; 067 labs tests
  updated for the second row.
- `/play` loads `figure3d.js` once next to arena3d. WebGL-dead:
  the PNG portrait is shown.

## Rollback
One commit per phase. Revert in reverse. The flag is inert without
the JS. Deleting `worldd/static/site/figure3d/` returns every player
to the PNG the moment the script 404s (canvas stays, JS degrades to
the fallback `<img>`).

## Execution status
Plan written 2026-08-24.

2026-08-24 — implementation and targeted verification:
- Phases 1–3 are complete in the working tree: the Labs-gated payload and
  canvas path, isolated stage, generator, catalog, player rigs, 68 item
  meshes, and family fallbacks are present.
- Phase 4 is implemented, including slot tagging, hold grammar, and hover
  colour. Its authenticated player-browser check remains outstanding.
- Targeted checks passed: plugin `test_071_figure3d.py` +
  `test_067_labs.py` (12 passed); worldd `test_071_figure3d.py` (3 passed);
  `node --check` passed for the Figure 3D module and GLTF loader.
- The required browser dojo was attempted against local worldd. Local account
  creation is Gmail-only, while OAuth fails there and legacy password sign-in
  cannot create a new account. The authenticated Labs/profile flow is blocked
  pending test credentials or a narrowly scoped local test-auth path.
- Deployment is intentionally deferred: the user explicitly requested no
  deploy. The plugin and the vendored/static worldd bundle are committed and
  pushed; only the authenticated browser acceptance remains pending.
- 2026-08-24 — follow-up browser regression: the isolated Figure3D harness
  froze before `DOMContentLoaded`. Its mutation observer recursively remounted
  the replacement WebGL canvas while models were loading, starving rendering.
  The mount is now guarded through the asynchronous build and the `/play`
  module URL is cache-bumped to `v=3`. The harness now loads all three race
  headings; `node --check` and the three worldd 071 tests pass. Deployment
  remains deferred.
