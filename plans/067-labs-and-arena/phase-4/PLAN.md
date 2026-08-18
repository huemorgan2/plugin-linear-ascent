# Phase 4 — 320×300 backgrounds for the 14 floor-6/7 creatures

## Goal
`worldd/static/site/fight3d/backgrounds300/<id>.png` exists for the 14
ids (320×7200, 24 frames of 320×300, 1-bit), generated from new 1:1
stills cropped to 16:15 with the ground on the lower third.

## Steps
- `research/3d-fight/gen_bg_floors.py`: `--size WxH` (default 320x112);
  for 320×300 request aspect `1:1`, center-crop to 16:15, STAGE prompt
  reworded ("ground fills the lower third, sky/ceiling above");
  stills to `bg_stills_300/`, gifs to `bg_gifs_300/`.
- `demo2/gen_backgrounds.py`: W,H parametric (`set_size(w,h)`).
- `make_bg_sheets.py`: `--size 320x300 --src bg_gifs_300 --out
  backgrounds300`.
- Run for the 14 ids; review sheet.

## Verification
- `python - <<< PIL check`: 14 files, each 320×7200 mode 1/L.
- arena3d loads `backgrounds300/<id>.png` (dojo).

## Rollback
Delete `backgrounds300/`; arena3d falls back to a black ground.

## Execution status
Done 2026-08-18 — commit 0b9ef6d + regen commit. 14 sheets 320×7200 1-bit in `worldd/static/site/fight3d/backgrounds300/`. First pass: 6/14 stills came back letterboxed (Gemini drew a cinematic strip inside the square → black bands on stage); prompt hardened ("fills the whole canvas, no letterbox / bars / border"), the 6 regenerated, all sheets rebuilt and eyeballed frame 0.
