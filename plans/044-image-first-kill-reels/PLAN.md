# 044 — image-first kill reels (floor 6 pilot)

## Problem

The 038 mercy reels (photoreal color, text-to-video straight to GIF) read
far worse than the 009 kill reels (`<family>_kill_<type>`, 1-bit Bayer
white-ink). Evidence: side-by-side of the shipped event set — the 009
kills (`boar_kill_melee` … `tortoise_kill_magic`, 18 GIFs) hold their
silhouettes at 320×112; the 038 reels lose the subject in the dither.
Text-to-video gives no checkpoint between prompt and finished GIF: a bad
composition is only discovered after the (slow, paid) video call and the
full frame pipeline.

## Root cause

No validation point before motion. Video models are weaker than image
models at composition, and our 320×112 1-bit grid is brutal to
compositions that were never checked against it. The 009 set survived
because its prompts were tuned over many retakes; 038 scaled the count
without the checkpoint.

## Strategy change (this plan)

Split generation into three gated steps:

1. **Stills.** Generate the opening frame of each kill reel as an image
   (nano-banana-pro, 21:9, the event-gif STYLE: smooth B&W gradients,
   no model-side dithering).
2. **Validate.** Review BOTH forms per still: the raw image and the
   pixelised result of the exact banner post-process (center-crop 20:7 →
   320×112 → level-stretch → Bayer 8×8 → white ink on alpha, tinted 2×
   preview on the panel color). A still must read in both to clear.
3. **Motion.** Cleared stills become image first-frame references for
   image-to-video (Veo path in `generate_event_gifs.py`), then the same
   frame pipeline as today. (Not in this phase.)

## Phase 1 — floor 6 kill stills (this phase)

**Goal.** 18 validated stills: floor 6's six encounters × the three
player classes (warrior/melee, archer/arrow, wizard/magic), each as raw
PNG + 320×112 1-bit PNG + tinted preview, plus contact sheets for
review. Slugs are `<encounter_id>_kill_<type>` keyed to
`content/floors/floor_006.yaml` ids: grave_moth, guano_vole,
silk_broodling, vault_weaver, lane_boar, wrapped_husk.

**Steps.**
- New tool `tools/generate_kill_stills.py` (Gemini image call, floor-6
  scene table, per-class layout beats reusing the 009 cast canon, the
  banner post-process copied from `generate_event_gifs.py`).
- Run: `python tools/generate_kill_stills.py` (key auto-resolved from
  `LUNA_GEMINI_API_KEY` / `../luna/.env`).
- Outputs (all under repo-root `content/`, gitignored like other raw
  art): `content/art/events/stills/raw/<slug>.png`,
  `content/art/events/stills/<slug>_320x112.png`,
  `content/art/events/stills/preview/<slug>_preview.png`,
  `content/art/events/stills/sheet_raw.jpg`, `sheet_pixel.png`.

**Verification.** Human review of the two contact sheets: every still
must show one creature + one defender, bold silhouettes, action in the
central band, and stay readable in the 1-bit preview. Regenerate by slug
until the sheet passes. Engine untouched — no runtime change to verify.

**Rollback.** Delete `content/art/events/stills/` and the tool. Nothing
ships in the plugin zip; no engine code changes in this phase.

## Operational notes

- The engine's 038 kind-based fx resolution (`combat._kill_fx`) does NOT
  fall back to family kill reels for kinded creatures — wiring floor 6
  `<id>_kill_<type>` GIFs into resolution is phase 3 work, alongside the
  what-a-kill-means question for natives (kill reel vs freed reel).
- Warden Duskspin is excluded: wardens have their own
  `warden_slain`/`floorNNN_warden` art path.
