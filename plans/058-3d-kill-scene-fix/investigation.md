# 058 — 3D kill scene: investigation

Roy's five complaints about the shipped floor-1 3D kill scene, traced to code.
Standing law (memory `kill-scene-3d-only-monochrome`): the floor-1 death scene
is 3D ONLY — no GIF pixels anywhere on it — and the WHOLE frame renders in one
tint color on black. Wardens and floors 2+ keep their GIF reels untouched.

File shorthand:
- `fight3d.js` = worldd/static/site/fight3d/fight3d.js (shipped stage)
- `fight2.js`  = research/3d-fight/demo2/fight2.js (the mock roy likes)
- `combat.py`, `render.py`, `pane.py` = plugin_linear_ascent engine files
  (identical line refs in the vendored copy unless noted)

---

## 1. "It waits for the length of the gif" — the delay

There is no literal `setTimeout(gif_duration)` anywhere. The wait is real but
accidental: the first kill downloads ~6.8 MB before anything moves, which on a
home connection takes about as long as the old 9.6 s ending GIF. So it *feels*
like the code waits out the gif.

Where the bytes go:

| fetch | size | where |
|---|---|---|
| human.glb (or elf/giant) | 2.07 MB | fight3d.js `ensureFor()` :273–287 — `Promise.all` of 4 GLBs at kill time |
| human_slash.glb (clip) | 1.72 MB | same Promise.all — geometry discarded at :285, only `animations[0]` kept |
| blade.glb | 0.99 MB | same |
| grey_wolf.glb | 1.05 MB | same |
| victory card fragment | 1.04 MB | render.py :1674–1697 — the ending GIF base64-inlined TWICE (mask-image + -webkit-mask-image, `_fx_data_url` :161–173), uncompressed (no GZipMiddleware in worldd/app/main.py) |

Nothing preloads: the GLBs are fetched only when the kill card appears
(`mountKill` → `await ensureFor(spec)` at fight3d.js:1092), then `liberate()`
fires on a blind `setTimeout(550)` (:1127) whether or not the GL context has
compiled shaders. The mock has no such hitch because demo2 awaits
`loadAssets()` before frame one (fight2.js:1655).

What must change:
- **Preload** the fight3d GLBs when /play loads (idle-time warmup: player +
  weapon for the roster's race/line, all six monster GLBs are small enough or
  fetch on floor entry). Warm the GL context and compile shaders once at load.
- **Stop shipping the slash-clip geometry.** `*_slash.glb` is dead code in both
  mock and site — `liberate()` never calls `play("slash")` (blade → `dur = 0`,
  fight3d.js:893). Don't fetch it at all for blades.
- **Stop inlining the GIF** on kill3d cards (see §2) — the 1.04 MB fragment
  drops to ~15 KB.
- Add GZip/Brotli for text responses in worldd (GLBs are already binary-tight).

## 2. "Remove the code of the old ending scenario"

The old ending = server-side fx GIF pipeline stamped on the victory card. For
floor-1 kill3d cards it must go entirely; for wardens/floors 2+ and the chat
wire it stays.

Removal map:

| site | what happens today | change |
|---|---|---|
| combat.py:1517 | `fx=_kill_fx(...)` set on every wild victory card | when the card gets `kill3d` (:1521–1527), set `fx=None` — no GIF slug on the card at all |
| combat.py:64–111 | `_kill_fx`, `_BREED_FX_VERB`, `_KILL_FAMILIES` | KEEP — wardens, first_clear, chat wire law still use it |
| render.py:1674–1697 | banner emitter: base64 GIF doubled into mask-image styles | for kill3d cards emit a bare `.banner` div (aspect-ratio 320/112, background #000, no mask, no data URL). fight3d.js:1077 needs `.banner` as the mount slot — keep the class |
| render.py:1871–1877 | adds `data-kill3d` + `data-tint` | KEEP; add `data-fx` slug (URL, not data-URI) so the JS can paint the GIF as a fallback when WebGL/model fails |
| fight3d.js:1071–1130 | `mountKill` blanks the fx reel + `restoreGif()` on failure | simplify: nothing to blank anymore; fallback = set `background-image: url(data-fx)` with the tint filter, only on failure |
| tests | test_kill3d.py pins tint; test suite has fx assertions on wild kills | update: wild floor-1 victory cards assert `fx is None` + `kill3d` set |

The GIF files themselves stay on disk — wardens and the fallback path still
read them.

## 3. "The 3D scene has a black background — the mock had animated scenery"

### What the mock does (demo2) — the full description

**The two-layer trick.** The stage is one 320×112 pixel grid shown at 4×
nearest-neighbor: an `<img>` playing an animated background GIF, and a
transparent-clear WebGL canvas directly on top (demo2/index.html:54–57, plain
DOM order, no z-index). Renderer `alpha:true`, clear color (0,0,0,0)
(fight2.js:96–99). Both layers land on the identical device-pixel grid, so
character dither and background dither read as one printed plate.

**The backgrounds** (gen_backgrounds.py) are made in two stages:
1. A nano-banana-pro still per creature: strictly pure black + pure white,
   every midtone as ordered Bayer dither, empty stage, flat ground line filling
   the lower quarter, light from top-left, floor-1 Fencerows fiction.
2. Local animation: the still is collapsed to a 320×112 continuous-tone
   density field, then 24 frames of (a) height-ramped sinusoidal wind shear
   (0.7–2.4 px, wraps for a perfect loop), (b) glow-mask pulse ±8%, (c) for
   fire scenes, three seeded noise fields cos²-blended into flicker — then
   re-dithered every frame through a FIXED screen-space 8×8 Bayer matrix.
   Untouched pixels never boil. Output: 24-frame 100 ms/frame GIF, 320×112,
   opaque white-on-black P-mode, ~13–17 KB. Seven exist in
   research/3d-fight/demo2/backgrounds/ ({id}.gif + {id}_still.png).

**How characters composite over it** (post shader, fight2.js:141–227): three
fragment classes keyed on offscreen alpha —
- background (`a < 0.03`): transparent (GIF shows), except a Bayer-dithered
  90% black ring where a 4-neighbor is body → the silhouette outline that
  keeps figures readable against bright scenery;
- mid-alpha (shadow catcher at 0.85, miasma/fog discs at ~0.45): alpha
  binarized per Bayer cell → pure-black dither, never grey blending;
- body (`a ≥ 0.97`): opaque white-or-black ink, GIF fully occluded inside the
  silhouette.

**The shading** that makes bodies read at 55 px: perceptual luminance →
gamma 0.4545 lift → `smoothstep(0.03, 0.95)` → **6-step posterize** →
8×8 Bayer fill. Six flat tone bands make the dither look like designed plates,
not noise. Low-key split lighting (ambient 0.18, key 6.0 monster-side, rim
10.0 behind) leaves a big dark camera-side mass so the silhouette carries the
information. Half-pixel depth ink: only the *near* side of a depth step inks,
so creases stay exactly 1 px. A kicker sliver — contour pixels whose
view-space normal faces screen-right render solid white — separates figure
from ink. Shadows and smoke go through the mid-alpha branch and come out as
the same black-dither vocabulary.

**Site status:** all of the shader/lighting/camera above is already ported
verbatim into fight3d.js (v=4), with the ink through `uInk` instead of white.
What was NOT ported is the background layer: the canvas sits on a bare black
`.banner`. My first attempt put the raw white GIFs back under the canvas —
that broke the one-color law and roy killed it.

### How to bring the scenery back WITHOUT breaking the one-color law

The demo2 background GIFs are white-on-black and opaque, so they cannot sit
under the canvas as-is (white ≠ tint) and CSS-tinting an `<img>` under a
canvas whose body pixels are opaque would still be two elements to keep in
sync. Correct approach: **move the background INTO the GL frame.**

- Decode each 24-frame GIF into a spritesheet PNG (320×2688 = 24 stacked
  frames, 1-bit, ~20–40 KB) at build time — script in research/3d-fight.
- fight3d.js post shader: sample the sheet at
  `frame = floor(mod(time, 2.4) / 0.1)` behind everything. Background branch
  becomes: white sheet pixel → `vec4(uInk, 1)`, black sheet pixel →
  `vec4(0,0,0,1)`; body/shadow/outline branches unchanged except body white →
  `uInk` (already done). The whole frame is then literally two values: uInk
  and black — the law holds by construction.
- The silhouette outline ring already exists and is what keeps characters
  readable over lit scenery.
- One sheet per floor-1 creature id, shipped under
  worldd/static/site/fight3d/backgrounds/ (PNG spritesheets, NOT gifs — the
  law bans GIF pixels, and these are GL textures anyway).
- Fallback path (no WebGL): the tinted fx GIF via CSS mask, as today's
  failure path.

Roy asked for "3 for each level — with that level scenery" — read as: scenery
loops per creature/scene on floor 1 (the seven demo2 loops cover all floor-1
ids + warden; warden unused). Floors 2+ have no 3D scene, so nothing to do.

## 4. "Sometimes the color is dark grey"

Cause found: the tint is specimen-driven, not creature-driven —
`_banner_tint(slug, variant)` render.py:104–116:

| specimen | tint | share of kills (economy.py:469–503) |
|---|---|---|
| common/"" | `#d9d9d3` ART near-white grey | 50% |
| runt | `#5b5952` FAINT **dark grey** | 25% |
| tough | `#d967c8` violet | 20% |
| alpha | `#f5b825` gold | 5% |

So 25% of floor-1 kills ink the whole scene in `#5b5952` — nearly invisible on
black — and 50% in a flat grey-white. That was tolerable on a masked GIF
(the mask kept shape regardless of ink brightness); on a full-frame 3D scene
the dark ink kills the image.

Fix: keep the specimen semantics but **brighten the ink for the 3D scene**.
Options:
- (a) map in fight3d.js only: lift any ink below a luminance floor (e.g.
  min-luma 0.55 in HSL space) before setting `uInk`. GIF banners elsewhere
  keep their exact hexes; only the 3D frame brightens. No server change,
  no test churn.
- (b) change `_VARIANT_TINT` server-side — rejected: it would alter every
  banner across the game.

Choose (a). Concretely: runt `#5b5952` → lifted to a readable warm grey
(~`#a8a49a`), common `#d9d9d3` stays (already bright), tough/alpha untouched.

## 5. "You didn't animate the 3D characters — they need bones and feet"

### What the mock does that the site doesn't

The player is NOT the problem — `buildPlayer` in fight3d.js is a near-verbatim
copy of the mock (byte-identical GLBs, same distance-driven gait: `gaitPh`
advances by actual Δx / leg length, thighs swing in world Z via `swingZ`,
airborne calf bends, torso lean, arm counter-swing, footfall bob, breathe,
and the 4 STRIKES full-body keyframe tables with impact at phase 0.75,
random arc per kill). Feet plant because phase is driven by travel.

The monster IS the problem. The mock's monsters are rigged Quaternius GLBs on
an `AnimationMixer`: real `Gallop`/`Rat_Run` leg cycles crossfaded in at
liberate, `Attack`/`Attack_Headbutt`/`Rat_Attack` clips shuffled per kill,
0.15 s crossfades, anticipation squash (22% over 0.18 s), knockback,
lane_wolf as a 3-dog staggered pack. The shipped `tripoMonster`
(fight3d.js:589–676) is a rigless mesh: sine bob + nose see-saw + one canned
0.28 s lunge — the shipped monster GLBs contain **zero skins and zero clips**
(they are the raw Tripo `10_textured.glb` meshes). That's why the mock "seems
way better": its monsters actually walk.

### The fix — Tripo rigging (in progress)

Tripo rig model `v2.5-20260210` rigs non-humanoids. Pipeline
(research/3d-fight/3d models/gen_monster_clips.py, running now): per creature
`POST /animations/rig` (rig_type quadruped/biped) → `POST /animations/retarget`
(`preset:quadruped:walk` — the only quadruped preset — or `preset:walk` for
bipeds; `bake_animation:true, animate_in_place:true`) → self-contained
animated `50_walk.glb` (~0.9–1.5 MB, geometry + texture + one walk clip).
~35 credits each; balance ~3700.

Status: grey_wolf ✓, feral_boar ✓, hedge_rat ✓, lane_wolf ✓,
goblin_straggler rig ✓ walk pending, ember_shade pending.

Client work needed in fight3d.js:
- Replace the six `monsters/{id}.glb` with the rigged `50_walk.glb` files.
- `tripoMonster`: add an `AnimationMixer`; play the walk clip during the run-in
  (timeScale matched to travel speed so feet plant), idle = clip paused at a
  standing frame + the existing breathe scale, attack = KEEP the procedural
  lunge layered on top (no attack preset was baked), eased in/out instead of
  mode-snapping.
- Skinned meshes break under `gltf.scene.clone(true)` — either stop cloning
  (one live scene per creature, like demo2's shared-src approach) or vendor
  `SkeletonUtils.js`. Site vendor/ has only three.module.js + GLTFLoader +
  BufferGeometryUtils today.
- Minor reads-smaller fixes while in there: feral_boar h 1.55 → 1.9,
  restore mock `wide` values.

## Cross-cutting facts

- Local game for roy: localhost:8890 (uvicorn on ascent-postgres :5434,
  running). Harness: http.server :8997 → /fight3d/test.html; screenshots via
  scratchpad shot3d.mjs.
- Concurrent session owns uncommitted 0.78.0 plugin work (core.py school,
  version.py) — do not touch/commit their files; live is 0.78.0.
- Plugin changes here: combat.py (fx=None on kill3d), render.py (bare banner,
  data-fx), tests. Static-only changes (fight3d.js, GLBs, spritesheets) need
  no plugin bump.
