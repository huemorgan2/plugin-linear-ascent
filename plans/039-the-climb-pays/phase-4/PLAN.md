# 039 phase 4 — ship

## Goal

The rebalance live on linearascent.net and the Luna plugin path, verified
by a production dojo walkthrough, results archived.

## Steps

1. Rebase on the parallel session's latest committed main (038 is in
   flight); resolve `combat.py` overlaps; full plugin suite +
   `sim.py --accept` green on the merged state.
2. Bump `version.py` + `luna-plugin.toml` (next free number at ship
   time), commit, push as huemorgan2.
3. Stash-dance the shared checkout if dirty (006 lesson: the live session
   can regenerate files mid-dance — restore non-conflicting paths with
   `git restore --source=stash@{0}`, keep their newer copies on
   conflicts, retain the stash).
4. `./worldd/tools/vendor_game.sh` → worldd suite green → secret scan →
   outer commit + masked push.
5. Package from clean `git archive HEAD`; attempt marketplace publish
   (endpoint 500 since 2026-08-07 — retry, else note).
6. `render deploys create srv-d9ha3csvikkc73ff5rg0 --confirm --wait` →
   `/health` `game` matches the shipped version.
7. Dojo walkthrough `dojo/01-the-climb-pays.md` on production, fresh
   isolated context.
8. Archive results to `luna/dojo/results/039-the-climb-pays/` via the
   origin/main worktree dance; bump outer gitlink; append execution
   status to all phase PLANs; commit.

## Verification

- `/health` game = shipped version; dojo scenario ALL PASS with evidence.

## Rollback

Redeploy the prior vendor SHA (`render deploys create` after reverting
the outer vendor commit); plugin revert per phase.

## Execution status

_(appended after execution)_
