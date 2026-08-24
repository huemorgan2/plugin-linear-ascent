# Phase 2 — ANSI box

## Goal
`waiting for you` draws a nested square: one continuous 1px rail
around the numbers, labels outside, header and four (or fewer)
plain-language rows. `to_text` lists the numbered choices. Clicks
on `.wrow` act.

## Steps
- `render._weekpick_html` + `.weekbox` CSS.
- `Scene.to_text` prints each choice.
- `pane.py` / card script wire `button.wrow`.

## Verification
One `.weekbox`, one `.wrail`, four `data-opt="pick_*"`; header
present; 390px wrap keeps the square complete.

## Rollback
`git revert` this phase.

## Execution status
Done with phase 1 (same working tree).
