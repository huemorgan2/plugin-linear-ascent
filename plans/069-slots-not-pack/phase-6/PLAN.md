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

## Execution status
- Plugin pytest (worldd venv): 1293 passed, 6 failed, 1 skipped, 1 xfailed —
  the 6 are the pre-existing baseline (test_017_death_relics fire arrow,
  test_017_speed_chase ×2, test_022_002_retune kill xp, test_engine ×2),
  identical before phase 1.
- worldd pytest: 192 passed, 1 failed — `test_web_play.py::
  test_leaderboard_marks_only_you`, fails the same on the pre-vendor tree
  (local DB state), not a 069 regression.
- Dojo `luna/dojo/tests/gear-slots/` (scenario.md, walkthrough.mjs,
  seed.py) on local worldd :8779 → **42/42 PASS**; evidence in
  `dojo/results/0038-069-gear-slots-2026-08-18/` (summary, 13 stills,
  results.json).
- Legacy keys: v11 migration already deletes `hone["weapon"]` and
  rewrites int `oil` — no legacy copies were kept, nothing to drop.
- Version bumped 0.92.0 → **0.93.0** (the other 067 session took 0.92.0);
  vendored from the committed plugin tree (1828648) — not the working
  tree, which carries 067 phase-6 edits in flight; mechanics-data.js
  regenerated. Not deployed.
