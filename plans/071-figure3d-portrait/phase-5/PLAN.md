# Phase 5 — tests, vendor, release, deploy

## Goal
The feature is isolated, tested, vendored, versioned 0.98.0, and
live on ascent-worldd. Default still off.

## Steps
- `tests/test_071_figure3d.py` (plugin) + `worldd/tests/test_071_figure3d.py`.
- Vendor copy of the plugin files that changed.
- Bump `version.py` + `luna-plugin.toml` to 0.98.0.
- Dojo: flask → Figure 3D on → profile canvas breathes → hover a
  slot → colour → off → PNG is back.
- On every game-card mutation, rebind a compatible detached Figure3D stage
  to the replacement card. Drop anything still disconnected: cancel its RAF,
  dispose render targets/materials/renderer, and remove it from the registry.
- Cap the pixel-art idle at 15 FPS and skip frames while the portrait is
  offscreen or the document is hidden.
- Run 20 profile-bearing menu swaps with Figure3D on and confirm interaction
  latency remains flat with no WebGL context-loss warnings.
- `worldd/tools/deploy.sh`.

## Verification
- Plugin 071 tests green; 067 labs still green.
- `/health` game version 0.98.0 after deploy.
- A live climber with the flag off is unchanged.
- After repeated card swaps there is one connected portrait renderer, no
  detached canvas keeps rendering, and the twentieth swap is not materially
  slower than the first.

## Rollback
Revert the deploy (previous Render build). Flag stays inert on old JS.
For the local performance fix, revert the cleanup helper/observer call and
restore the previous `figure3d.js` cache version.

## Execution status
2026-08-24 — In progress. Targeted plugin tests passed (12 across 071 and
067), worldd tests passed (3), and JavaScript syntax checks passed. A formal
dojo scenario now lives at `tests/071-figure3d/01-profile-labs.md`, but its
authenticated Labs/profile walkthrough is blocked by local Gmail-only signup.
The full suites executed but are not green: plugin 1327 passed / 5 failed
(pre-existing 033, 048, 063, and kill3d failures outside 071); worldd 195
passed / 1 failed (`test_leaderboard_marks_only_you`, outside 071). Vendor
sync and the clean plugin/worldd commits are complete and pushed. Deployment
is deferred by explicit user instruction.

2026-08-24 — Fixed a player-blocking Figure3D browser regression: the
MutationObserver recursively remounted the replacement canvas before models
finished loading, which froze the event loop at the loading placeholder. The
canvas is now marked as mounting until the async build completes and `/play`
uses `figure3d.js?v=3`. The formerly hanging isolated harness now loads;
`node --check` and `worldd/tests/test_071_figure3d.py` (3 passed) are green.
Rollback: revert the Figure3D JavaScript and restore the prior module URL.

2026-08-24 — In progress: browser acceptance found that every card swap
leaks the detached portrait's WebGL renderer, two render targets, and RAF
loop. The cleanup regression scenario is written; implementation and the
20-swap browser verification follow.

2026-08-24 — Implemented and locally verified. Compatible replacement cards
reuse the same WebGL stage; obsolete canvases cancel RAF and dispose both
render targets, post materials, and the renderer/context. Rendering is capped
at 15 FPS and pauses offscreen. In a real authenticated `/play` session, 20
menu selections kept the same canvas on all 20, stayed at exactly 1 live /
1 connected renderer, and loaded 0 additional GLBs (resource count 4 → 4).
A direct 20-card mutation stress test averaged 2.3 ms for the first five and
5.4 ms for the last five, with the same canvas throughout; removing the
portrait returned diagnostics to 0 / 0. Targeted worldd checks passed (4),
`node --check` passed, and `/health` returned in 2 ms after stale v5 pages
were unloaded. Deployment remains deferred.
