# Phase 6 — Tests, dojo, release

## Goal
Suite green, dojo `luna/dojo/tests/gear-slots/` walked with evidence,
game 0.92.0 vendored and committed. Not deployed unless roy says so.

## Steps
- Full plugin pytest via worldd venv; worldd suite.
- Dojo scenario (see PLAN.md §Verification) on local 8777, results in
  `dojo/results/NNNN-069-gear-slots-<date>/`.
- Drop legacy `hone["weapon"]` / int-oil copies from `ensure_current`
  once dojo passes.
- Bump 0.92.0, vendor, regen, commit; append Execution status to every
  phase PLAN.md.

## Verification
Per PLAN.md §Verification.

## Rollback
Revert the release commit; older vendored game stays in place.
