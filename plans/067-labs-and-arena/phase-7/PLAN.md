# 067 phase 7 — tiles as the pack's cells, HUD lines on black, 20-cell bars (roy, 2026-08-18)

## Goal
1. The stage's tiles ARE the pack's cells: a 60px black box (no border),
   the 42px `.picon` mask in ART ink (`.gw` art when it ships, the 16×16
   glyph otherwise) — same size, colour, icon as the profile pack. `[n]
   LABEL` sits under the box on black, the [i] outside it. One line along
   the foot of the stage, half a line up.
2. The HUD slabs have no box: black rides only behind each text line;
   the scene shows between lines. Half a line of margin left/right/top.
3. Both HP bars are 20 cells (were 10) — twice the width, finer grain.

## Steps
- render.py: `_arena_tiles_html` → `.abox > .picon[.gw]` in ART/DIM,
  `{atk}` badge in the box; `_abar` → `_blocks(hp, cap, 20)`; CSS:
  `.astat` transparent + `.astat>div` black fit-content, `.ahuds`
  inset .5em, `@container (max-width:600px)` 12px slabs; tiles CSS →
  no gradient, `bottom:.5em`, `.abox` 60px, `.picon` 42px, no border,
  `.info` outside the box.
- worldd `arena3d.js` `setBar`: cell count read from the drawn bar
  (20 now); `ARENA3D_URL ?v=3`.
- Tests: `test_067_arena.py` phase-5 dress test → `.abox`/`.picon gw`,
  40 bar cells; dojo labs-arena: S5/S11 selectors take `.picon`, HUD
  side margin ≤ 12px.

## Verification
- pytest `tests/test_067_arena.py tests/test_067_labs.py`; dojo 0040;
  captures at 1440 + 420 reviewed.

## Rollback
Revert the phase-7 commits (plugin + worldd), re-vendor 0.94.0, deploy.

## Execution status (2026-08-18)
- Done. `test_067_arena.py` 13/13, `test_067_labs.py` 6/6; full suite 1296
  pass / 6 pre-existing fails. Dojo 0040 33/33 (after selector update).
- Iterated on captures: the [i] and the ATK badge overlapped at the box's
  corner → [i] moved outside (16px gutter), ATK to the top-left; on a 420
  phone the 20-cell bars pushed the foe slab under → 12px slabs below a
  600px stage.
- Game 0.95.0.
