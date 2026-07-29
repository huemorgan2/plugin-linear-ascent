# 023 — collect the interest (and the lazy-collectable law)

## The itch

The vault credits interest silently on visit. Nothing to collect, nothing
to come back for — the opposite of the collect badges (0.29.2). The user's
ask: each day of interest should be a LINE you collect, the vault door
should badge the count ("(10) if you didn't connect for 10 days"), and
none of it may cost the server anything for players who left.

## The law (applies to every collectable, now and later)

1. **Lazy, always.** Collectables MATERIALIZE when the doc loads a scene
   (town render / door entry), never on a server tick. A player who quits
   costs zero work; a player who returns pays one cheap catch-up pass.
   This is already how nights, contracts, the strongbox and dawn work —
   interest joins them.
2. **Bounded, always.** Every pile has a cap. The clerk keeps
   `INTEREST_STUB_CAP = 30` stubs — a month of interest, oldest dropped.
   No infinite rewards for the absent (and no unbounded doc growth).
3. **A pile is a pull.** Uncollected interest is SIMPLE (priced off the
   principal as it stood). Collecting re-banks it, so the hand who shows
   up daily still compounds — the compounding IS the daily hook now.
   (This also retires the old exploit: 100 idle days used to compound to
   ~130×; now idle caps at +150% and you must show up to bank it.)

## The cut

- `economy.py`: `INTEREST_STUB_CAP = 30`; interest-rate comment updated.
- `state.py`: `bank_interest_due` → `interest_sync(p)` — materializes
  per-day stubs `{"day", "gold"}` into `p["interest_due"]`, advances
  `bank_day`, enforces the cap. Idempotent within a day.
- `core.py` vault: the auto-credit block dies. Stubs render as lines
  (newest 5 + "…and N older"), one `collect_interest` option pays the
  whole pile into the BANK (ledger kind "interest"), clears it.
- `core.py` town: the vault badge counts stubs + the pending strongbox.
- Tests: rewrite `test_vault_interest_compounds_and_credits_once`;
  new `test_023_interest.py` (accrual, collect, cap, badge, no
  double-materialize, zero-bank silence).

## Explicitly connected (already lazy, no change needed)

- contract claims — materialize via `contracts.sync` on board/town render
- strongbox weeks — `weekly.sync` rolls over lazily, fallback pays out
- night yield — resolved by the dawn pass in `state.py` on next load
- letters — held server-side, badge reads `inbox_count` from the blob

## Not doing

- Per-stub collect taps (10 options would drown the card; the pile is
  the motivation, one collect is the verb)
- Red badge color (the card is monospace text; "(n)" is the signal)
- worldd changes (doc-local feature; vendor sync only)
