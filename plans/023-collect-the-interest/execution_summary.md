# 023 — execution summary

Shipped as **0.29.3** (same release train as 0.29.2's collect badges).

## What landed

- `state.interest_sync(p)` — materializes one interest stub per elapsed
  day (`{"day", "gold"}` in `p["interest_due"]`), priced off the
  principal as it stood, capped at `economy.INTEREST_STUB_CAP = 30`
  (oldest dropped). Runs lazily from the town render and the vault —
  absent players cost the server nothing, returning players pay one
  cheap catch-up pass. `state.interest_collect(p)` banks the pile.
- The vault's silent auto-credit is gone. The card shows the newest 5
  stubs (+ "…N older"), one `collect_interest` option pays the whole
  pile into the bank (ledger kind "interest").
- The town's vault door badges stubs + the pending strongbox:
  10 days away = "The Vault (10)", exactly the ask.
- Economy ruling: uncollected interest is SIMPLE; collecting re-banks
  it, so daily hands still compound. This retired the idle exploit
  (100 absent days used to compound ~130×; the ceiling is now a month
  of simple interest, and you must show up to bank it).

## Verification

- `tests/test_023_interest.py` — 6 tests: per-day accrual, idempotence
  within a day, the 30-stub cap, collect-then-compound, the town badge
  round-trip, empty-bank silence, the 5-line card cap.
- `test_engine.py::test_vault_interest_lands_as_stubs_and_collects_once`
  rewritten from the old auto-credit test.
- Full suites green: 587 plugin, 76 worldd (vendored).

## Notes for later

- Other collectables audited and already lazy (contracts, strongbox,
  night yield, letters) — no changes needed; the plan records the law
  (lazy, bounded, a pile is a pull) for anything added next.
- If a "collect at the door" one-tap (collecting from the square
  without entering the vault) is ever wanted, `interest_collect` is
  already scene-independent.
