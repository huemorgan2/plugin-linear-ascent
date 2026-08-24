# Phase 1 — Labs flag, payload, render hook

## Goal
A player can switch **Figure 3D** on in Labs. The engine then stamps
`Scene.figure3d`; the card draws a canvas in the portrait slot (same
footprint). Off = today's `<img>`. Nothing 3D runs yet.

## Steps
- `engine/labs.py`: add `figure3d` Feature (all floors). Tip text.
- `engine/figure3d.py` (new): `payload(p) -> dict | None`.
- `engine/scene.py`: `figure3d: dict | None`; `to_dict` / `from_dict`.
- `engine/core.py` `_stamp`: `scene.figure3d = figure3d.payload(p)`.
- `render.py` `_profile_html`: when `scene.figure3d` and not
  portrait-locked, emit
  `<canvas class="portrait later figure3d" width W height H
   data-figure3d='…'>` plus a hidden fallback `<img>` of the race PNG.
  Off path unchanged.
- tips: `labs_toggle_figure3d`.
- `tests/test_071_figure3d.py` + extend `test_067_labs.py` for the
  second row.

## Verification
- New doc: `labs == {}`; toggle on → `labs.figure3d is True` and
  `scene.figure3d["race"]` matches the climber.
- Render on: `data-figure3d` + `<canvas class="portrait`.
- Render off: no canvas, `<img class="portrait"` present.
- Wire: `from_dict(to_dict())` keeps `figure3d`; old dict loads as None.
- Mid-fight `labs` still refused.

## Rollback
Revert the commit. Docs carrying `labs.figure3d` load on the old
engine (unknown key kept).

## Execution status
2026-08-24 — Complete in the working tree. `labs.figure3d`, the payload
builder, Scene wire key, stamp hook, canvas/hidden-PNG render path, and Labs
tip are present. Plugin targeted tests passed (12 total with the 067 Labs
coverage); the worldd wiring test suite passed (3 tests).
