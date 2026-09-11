# 086 — Equipment durability bars

## Problem
On 2026-09-11 the user supplied a screenshot of an equipment tile and asked
for a borderless green bar attached to the frame's bottom. Local browser
inspection reproduced a 52px track inside a 60px slot, with its bottom 3px
above the frame's outer edge.

## Root cause
The shared `SCENE_CSS` rule `.slot .dur` sets `left:3px;right:3px;bottom:2px`.
The slot also has a 1px frame, leaving a visible inset on all three edges.
The bar itself already has no border. Both equipment and inventory cells,
including public player sheets, inherit this rule.

## Emergency mitigation
None needed.

## Phase 1 — Attach the durability track to the frame
### Goal
Render the same 3px durability track with its left, right and bottom edges
exactly aligned with the slot's outer frame, with no surrounding border.
### Steps
1. Commit this plan and browser scenarios before implementation.
2. Change the shared CSS in `plugin_linear_ascent/render.py` to offset the
   bar by -1px on left, right and bottom, covering the existing 1px frame.
3. Copy the changed renderer into `worldd/vendor/plugin_linear_ascent/` so
   the website build and future installs inherit the same rule.
4. Verify using existing tests and a real browser; record evidence.
### Verification
- Run existing renderer, equipment-slot and player-avatar tests, followed
  by the plugin full suite; compare failures with the recorded baseline.
- Run worldd full suite only against the isolated `ascent_maps_tests` DB.
- Browser-review green, low and broken bars, equipped/packed/read-only
  slots, and desktop/mobile widths. Inspect frame/track bounds and clicks.
- Use a real QA Luna conversation to render and re-render the gear.
### Rollback
Restore `.slot .dur` to `left:3px;right:3px;bottom:2px;height:3px` and its
background-only declaration in both renderer copies; restart local QA.
After commit, `git revert <implementation-commit>` in the plugin and then
restore the parent's submodule pointer and vendor renderer in a new commit.

## Operational notes
CSS-only: no engine, player data, assets, content or dependency changes.
Preserve all pre-existing dirty files. Local QA is the verification target;
production publication is outside this styling request. Screenshots and
results go in `dojo/results/0063-equipment-durability-bars-2026-09-11/`.
