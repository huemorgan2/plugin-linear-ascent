# Phase 4 — the write path (worldd)

## Goal

`_save_doc` (measured 156 ms per act) drops under 30 ms local without
changing what is stored: same doc, same ledger rows, same updated_at
semantics.

## Steps

1. **Measure first** (`worldd/tools/profile_act.py` gains a save
   breakdown): how much is the doc UPDATE vs the per-row ledger INSERT
   loop vs commit latency. Numbers before touching anything.
2. **Batch the ledger**: replace the per-entry `execute` loop with one
   `executemany` (acts commonly carry several ledger entries — one round
   trip each today).
3. **Bind JSONB natively**: pass the doc through asyncpg's jsonb codec
   (`set_type_codec`) instead of `json.dumps` → text → server-side cast.
   Skip if measurement shows it's noise.
4. **Confirm the Phase-1 columns don't tax the write**: 9 generated
   columns + 3 partial indexes recompute on every UPDATE — the profile
   from step 1 runs before AND after Phase 1 lands, and the delta is
   recorded in this file's execution status. Budget: ≤ 10 ms added. If
   exceeded, narrow the indexes (drop `ix_players_playing_name` first —
   `_profiles` tolerates a scan of 80 names) before shipping.
5. **Tests**: ledger batching preserves row order and content (golden
   fixture: one act writing 3 entries → identical table state).

## Verification

- Full worldd suite green.
- Profiler: save ≤ 30 ms local p95; act p95 still < 80 ms with Phases 1–2
  in place.

## Rollback

`git revert` the phase commit — the loop and text binding return. No
schema involvement.
