# How to build nice 1-bit images

Everything learned across demoimages4_1bit → demoimages9 (labs 1–10),
iterating on `floor001_goblin_straggler_fighter_sword` at the game's
native 320x112 banner grid.

## The headline lesson

**Don't extract 1-bit from a greyscale render with filters — have the
model DESIGN the dither as art, then only enforce the grid.**

This is how the existing game banners (`tools/generate_banners.py`,
e.g. `content/art/banners/arcanum_320x112.png`) were made, and it beats
every filter formula we tried:

1. Prompt nano-banana-pro for **1-bit pixel art directly**: "STRICTLY
   two colors: pure black and pure white — every midtone rendered as
   ordered Bayer dithering. FULL OF designed gradients: sky fading from
   dense white dither to black, glow ramps radiating from every light
   source, gradient pools of light on the ground, atmospheric depth
   where far things dissolve into sparse dither. Figures as SOLID BLACK
   SILHOUETTES with crisp readable outlines."
2. Post-process is only enforcement: center-crop to 20:7, LANCZOS
   downscale to 320x112, `autocontrast(cutoff=1)`, Bayer 8x8 ordered
   dither with threshold `(BAYER[y%8][x%8]+0.5)/64`.

The gradients survive because they are *designed shapes* (glow ramps,
silhouettes, dither fields), not photographic midtones fighting the
threshold. Result: demoimages9 `__1bit_t12_banner.png` from
`__original_v4.jpg`.

Known residual: the model paints fine-grain dither that interferes
slightly with the 320x112 grid after downscale — grittier than the
hand-chunky arcanum look. If needed, prompt for "large chunky dither
pixels".

## What the source image must have

Filter quality is capped by the source. In order of impact:

- **Tonal separation by design**: dark figures on a light background
  (or vice versa) survives any conversion; equal-tone figure/background
  survives none. Prompting "characters in DARK tones, background in
  LIGHT tones" fixed more than any filter.
- **Flat micro-texture**: photoreal grass/rock texture becomes dither
  noise. Prompt "flatten fine photoreal micro-texture into simple
  shaded surfaces".
- **Designed gradients**: a flat one-color sky dies in 1-bit; a sky
  with a glow gradient reads as art. Ask for gradients explicitly.
- **Interior detail mostly does not survive** at 320x112 — a figure is
  ~40px tall; crosshatch inside a dark figure reads as noise or
  vanishes. Silhouette + readable pose is what carries.
- Beware washed-out renders: emphasizing linework/lightness in the
  prompt can silently kill the gradients ("use the FULL greyscale
  range, deep and moody, not pale" restores them).

## Filter formulas ranked (when you must convert greyscale)

All start: center-crop to 20:7 → LANCZOS to 320x112 → median-3 →
autocontrast(cutoff=2). Bayer 8x8 ordered dither at the end.

1. **Retinex silhouette (best general formula)** — demoimages7/t10/t11:
   `n = luma / gaussian_blur(luma, 16)`; `n < 0.65` → pure black;
   else map to a bright band (`150..255`, or `120..255` to let
   background gradients show). Large dark regions flatten to their
   local average (stay bright); small locally-dark blobs — the
   characters — go solid black. Robust even on moody dark scenes.
2. **Rim-light boost (dark-mode alternative)** — demoimages5:
   high-pass `luma - blur(8)`, keep only ≥10, ×2.5, add onto
   gamma-2.0-crushed base. Preserves rim-lit outlines in dark scenes.
3. **Sobel line art** (for outlined/toon sources): edges at 2x grid,
   max-pool 2x2, threshold ~260 (after autocontrast), despeckle
   (drop black pixels with <2 black neighbours), plus solid fill for
   `tone < 40`. Crisp but tangles when the background is busy.
4. **Gentle lines**: average-pool the gradient instead of max-pool and
   let strength modulate the dither darkness (`v = bg*(1-s)`) — soft,
   but on light sources the lines drop below visibility. A narrow
   sweet spot; hard to tune per image.
5. **Naive autocontrast+Bayer**: baseline; drowns figures in noise.

## Dead ends (tested, rejected)

- **CLAHE / local contrast equalization**: amplifies texture noise.
- **Floyd–Steinberg**: washes everything to even grey speckle; ordered
  Bayer reads far better at this scale.
- **Posterize bands**: crushes creatures into the terrain.
- **Hard black floor (luma < T → black)**: large dark terrain becomes
  solid black masses that absorb the characters (demoimages6).
- **Gamma lift of background + dark silhouette split by threshold**:
  cannot separate characters from equally-dark terrain — only
  locality (retinex) can.
- **White interior edge lines inside dark figures**: dilutes the
  silhouette mass; figures wash out.
- **Blur before Sobel**: kills thin ink lines entirely (near-empty
  output).
- **Pixel-compositing players into scenes** (paste + mask): looks
  glued; model re-render with both references integrates properly.

## Mechanics worth keeping

- Work at 2x the target grid for edge detection, then pool down —
  edges computed at target res are sub-pixel and vanish.
- Max-pool preserves/thickens lines; average-pool softens them.
  Choose per goal.
- Despeckle binary output: drop black pixels with fewer than 2 black
  neighbours (8-neighbourhood) — removes texture speckle cheaply.
- To thicken model ink lines before downscale: `MinFilter(9)` at full
  res (dilate dark), then downscale.
- Save every model render versioned (`__original_vN.jpg`) — model
  calls are non-deterministic; an overwritten good render is gone.
- Judge on a fixed small set of hard cases (busy cave scene, small
  dark creature, giant + weapon) and iterate one variable at a time.
- Shared BAYER8 matrix and the review convention: save at 2x NEAREST
  (640x224) so the chunky pixels are visible in review.

## Closeups (single-creature encounter shots)

**Role: the closeup IS the encounter banner — always the monster
alone.** The staged player-vs-monster scenes exist only as first
frames for the kill movies; they never ship as encounter art.

The recipe that works (`plans/049-monster-image-remake/gen_floor1.py`
CLOSEUP_PROMPT, floor1/closeups/):

- **Reference in, redesign out.** Feed the existing scene render as
  the reference and ask for a close-up of the creature alone — "Keep
  the creature's exact design from the reference", "NO human
  characters". The model keeps identity while recomposing.
- **Composition**: huge in the frame, mid-advance toward the viewer,
  dramatic three-quarter angle, low camera, wide horizontal frame.
  The floor's landscape behind it dissolving into sparse dither.
- **Demand 3D shading, and kill the silhouette wording.** This was
  the hard-won part, in three attempts:
  1. "SOLID BLACK SILHOUETTE with white rim contour" → clean shape,
     zero interior detail.
  2. Adding "rich interior dither shading" to a "dark figure" →
     still near-flat: fine dark-on-dark dither dies at 320x112.
  3. What works: drop "dark"/"silhouette" entirely and describe the
     figure as a lit 3D form — "FULLY 3D-SHADED in dither, NOT a flat
     silhouette: one strong directional light models the volume like
     a 3D render translated to 1-bit; lit side in dense white dither
     to near-white highlights, shadow side to solid black, and every
     muscle/fur mass rolling through LARGE CHUNKY dither midtones —
     big bold tonal steps that survive heavy downscaling."
- Keep "dark contour line around the body" and "eyes as white points"
  — the shape still needs an edge, and the eyes carry the menace.
- Same grid enforcement as everything else; nothing special.
- Failure modes: an occasional "model returned text, not an image"
  refusal — just retry, it is intermittent. Smoke/shade creatures
  (no solid anatomy) shade poorly — expect the weakest results there.

## Movies (the liberation animation technique)

Frame-by-frame model edits (image N -> prompt -> image N+1) hold the
scene together but give only ~6 stills. For a real animation, generate
a VIDEO and re-dither every frame
(`plans/049-monster-image-remake/gen_floor1_movie.py`):

1. **Veo image-to-video, same Gemini key.** The scene's 1-bit style
   render is the first frame; the prompt describes the whole beat in
   order: the weapon-specific kill first (sword slash for sword, arrow
   for bow, bolt for wand — the weapon the player actually carries),
   then the canonical Liberation Dissolve from
   `plans/049-monster-image-remake/floor1/LIBERATION.md`, ending on
   the original small animal at its true size. Tell it to keep the
   1-bit dither style and hold the camera fixed.
   - REST: `POST {GEMINI_ROOT}/models/{veo}:predictLongRunning` with
     `instances[0] = {prompt, image:{bytesBase64Encoded, mimeType}}`,
     `parameters = {aspectRatio: "16:9"}`; poll the returned operation
     every 15s until `done`, then download the video URI (append
     `key=`). ~1–2 min per 8s clip.
   - Model ids are key-dependent — list models and filter for `veo`
     first. This key exposes only `veo-3.1-*-preview`.
2. **mp4 -> mpg**: the venv's `imageio_ffmpeg.get_ffmpeg_exe()`
   bundles ffmpeg — no system install needed
   (`ffmpeg -i in.mp4 -c:v mpeg2video -q:v 4 -an out.mpg`).
3. **mp4 -> 1-bit GIF**: read frames with `imageio`, sample down to
   ~10fps (~96 frames per 8s), run EVERY frame through the same grid
   enforcement as stills (crop 20:7 → 320x112 → autocontrast → Bayer),
   assemble with per-frame duration `step/fps`, hold the last frame
   ~1.5s on the freed animal.

Veo keeps the dither style and scene continuity well; the sword arc,
particle dissolve, and the small animal all read after re-dithering.
The Bayer grid is re-applied per frame, so dither "boils" between
frames — at 10fps it reads as texture, not noise.

## Recommended production pipeline (049)

1. Two-reference scene assembly (demoimages4): scene + player renders
   → model integrates the character into the scene.
2. Banner-style 1-bit re-render (this file, headline lesson): model
   redraws the composite as designed 1-bit dither art with silhouette
   figures and gradient light.
3. Grid enforcement: crop 20:7 → 320x112 → autocontrast(cutoff=1) →
   Bayer 8x8 → white ink on alpha (game spec, as in
   `tools/generate_banners.py to_1bit`).
