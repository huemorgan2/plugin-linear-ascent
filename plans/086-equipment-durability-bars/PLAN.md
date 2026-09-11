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

## Execution status — 2026-09-11

Implemented in the shared renderer and the identical website vendor copy.
The 3px track covers the frame's bottom edge; no padding or surrounding
border remains. Browser measurements for the actual game and for green,
low, broken, packed and read-only fixtures show zero left/right/bottom
offset at desktop, 390px and 320px. The live equipment popup still works.

Targeted checks: 53 passed, 1 failed. Full plugin suite: 1,441 passed,
9 failed, 1 skipped, 1 xfailed. All nine failing tests were rerun with the
original renderer and reproduced, so they are baseline failures.

Real QA Luna conversation completed: `show me my equipment` used
`ascent_character`; `show me the scene` referred to the existing pane;
`refresh my current scene` used `ascent_scene`. The pane and equipment
popup rendered. Stored gear, durability, HP, coins, energy and action
sequence matched before/after refresh. A routine daily gift was reported.

The supplemental worldd suite was interrupted after slow progress; it is
not reported as a full pass. No service logic changed. Required browser
and plugin validation is complete; broader service-suite validation
remains incomplete. No production deploy was performed.
