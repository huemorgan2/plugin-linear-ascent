# Execution summary — 022 phase 005: nights & weeks

Status: **DONE** (plugin + vendor sync; deploy/publish deferred to the
end of the 022 run per the run agreement).

## What shipped

### The night slot (Lodge, level 6)
- One action per night, chosen at the Lodge, resolved once at the next
  world-day boundary in `state.touch_daily` (the same dawn that closes
  wounds). Switching the plan before dawn is allowed; exactly one
  resolution happens. Away nights don't stack — the plan covered one
  night.
- **Rest** banks rested aether: `p["rested"]`, one night =
  `NIGHT_REST_PCT_OF_BAR` (4%) of the current level bar, capped at
  `RESTED_POOL_CAP_NIGHTS` (3) nights' accrual. The pool pays out in
  exactly one place — `state.rested_bonus`, called from
  `combat._victory` on kill XP at +25% per kill until empty. Contract
  claims and strongbox payouts can't touch it by construction (they
  add to `p["xp"]`/`p["rested"]` directly, never through the kill
  path).
- **Work** pays `NIGHT_WORK_INCOME_PCT` (20%) of
  `daily_income(unlocked_floor)` in carried gold at dawn — 002's own
  anchor, so it re-scales with any future retune for free. The Energy
  cell's 1/day ceiling is untouched (work is gold only). Shift flavor
  (forge shift / bar shift / palisade watch) is day-seeded, same for
  everyone.
- The Crier reads the yield ("the night shift paid ◈ N while you
  slept." / "you wake rested — ✦ N banked toward your next kills.") —
  noticed, never taught. Below level 6 the Lodge shows nothing; the
  square's NEXT line carries the slot (020's machinery).

### The weekly strongbox (Vault, level 10)
- `engine/weekly.py` (new). Three counters the game already tracks:
  kills (bumped where `_victory` scores them), warden engagements
  (same hook moment as 004's horn contract — one definition of
  "engagement"), floors gained (no hook at all: the box remembers the
  frontier it opened at and diffs). Points = kills + keeps + floors,
  one each; thresholds 2/4/6 open 1/2/3 slots.
- At the weekly tick (world_day // 7) the box goes PENDING; the player
  picks **exactly one** reward at the Vault: gold lump (half a hunting
  day at their frontier) → + aether lump (10% of the bar, paid into
  the RESTED pool so it still only rides kills) → + smith's token or
  relic (repair token / luck charm v1). Picking closes the week.
- The fallback law: a pending box never picked auto-pays the lowest
  slot (gold) when the next week closes — an earned week never rots to
  nothing. Idle weeks (points < 2) earn nothing.

## Test state

- 540 plugin tests green (+15 in `test_022_005_nights_weeks.py`).
- 61 worldd tests green after vendor sync.
- Registry guard extended: `NIGHT_SLOT_LEVEL` and `STRONGBOX_LEVEL`
  are covered gate constants with registry entries.

## Interpretation rulings (documented, revisit with telemetry)

- The plan's "thresholds 2/4/6 open slots" is read as summed activity
  points across the three counters, one point per event. Kills make 6
  points trivially for an active week — the thresholds gate the CHOICE
  (which reward), not the size. If that reads too generous, weight the
  counters, don't move the thresholds.
- "Gear-tier token" is the repair token again (same substitution as
  the contract board — one design TODO covers both).
- The fallback gold is priced at the CLAIM-time frontier, not the
  earned week's. Simpler, slightly player-favorable.

## Forward corrections applied

- `007-the-era/plan.md`: the reincarnation perk "pre-filled rested
  pool" now has a concrete target — seed `p["rested"]` (cap semantics
  in `economy.rested_pool_cap`).
- `008-together/plan.md`: "no double-dip with rested aether" pinned to
  the mechanism — rested pays only inside `combat._victory`; the
  assist bonus must not route through it twice.
