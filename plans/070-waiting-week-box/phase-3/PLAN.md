# Phase 3 — Tests, dojo, release

## Goal
Suite green on the 070 contracts, dojo walked, game 0.97.0 vendored.
Not deployed unless roy says so.

## Steps
- `tests/test_070_waiting_week_box.py`; update 022/029.
- Dojo `luna/dojo/tests/waiting-week-box/`.
- Bump 0.97.0, `worldd/tools/vendor_game.sh`.

## Verification
Per PLAN.md §Verification.

## Rollback
Revert the release commit.

## Execution status
Done 2026-08-23. Tests + 0.97.0 + vendor. Dojo scenario written;
live worldd walk not run this session.
