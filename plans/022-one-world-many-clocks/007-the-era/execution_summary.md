# Execution summary — Phase 007: the era, the ending, reincarnation

Status: DONE (tests green; deploy/publish deferred to the end of the
022 run, per the run-wide ruling).

## What was built

**Permanent tables** (`worldd/migrations/010_eras.sql`): `ascent_eras`
(one jsonb ledger per finished era) and `ascent_reincarnation` (one row
per climber per era: points, tiers). These two plus `ascent_tenants`
are the only things that survive a reset — auth is not era state.

**`worldd/app/era.py`** — the whole ending in one module:

- `declare_last_siege(conn, active)` — fired from `_warden_fall` the
  moment the Warden of 99 dies (`floor + 1 == 100`). Reuses 006's
  megaphone exactly as the plan's forward-correction said: a
  happenings-kind-`war` Crier line, a Stone line, and a letter to every
  playing climber naming the quorum (`milestone_quorum(100, active)`)
  and the two-day pledge window. No second megaphone was built.
- `close_era(conn, tenant, player, doc, commits)` — hooked into
  `_resolve_boss` when `victory and ms.floor == 100` (the grand siege
  IS the Vharuk milestone, quorum path, commit window and all — the
  warden pool is not involved). Freezes {era, world_day, finisher,
  war party, faction standings, population, the era's Stone (last
  400 lines)} into `ascent_eras`; writes reincarnation rows for every
  playing climber of level ≥ 5 (tiers from the frozen moment:
  `stood_100` = unlocked_floor ≥ 100, `struck_vharuk` = in the
  commits, `final_blow` = the resolver, one per era ever); pushes the
  closing-ceremony scene into every playing doc's `pending_events` —
  including climbers offline during the fall. The resolving player's
  DB row is stale mid-act, so their ceremony and their tier check go
  through the in-memory doc the act will save after us.
- `era_reset(conn)` — deletes every transient table
  (`TRANSIENT_TABLES`, 17 of them), re-seeds frontier 1, and the new
  Stone's first line names the era. The caller owns the transaction.
- `prestige_boot(conn, tenant, player, doc)` — called from
  `game.py::_load_doc` on brand-new docs only: sums the reincarnation
  ledger into `doc["prestige"] = {points, eras, tiers}` and pre-fills
  `doc["rested"]` at the level-1 cap. **The cap law holds for
  everyone, prestige included** (the 005 recommendation, adopted).

**Reset tooling** (`worldd/tools/era_reset.py`): dry-run by default —
runs the real wipe inside a transaction, asserts the permanent tables
did not change row counts, prints the wipe plan, rolls back.
`--execute` additionally requires `ERA_RESET_CONFIRM=yes` in the
environment. Rehearsed against the scratch test DB (would wipe 2,758
players / 29k idempotency rows; rolled back clean; the refusal path
exits 2). Never pointed at production.

**Plugin surfaces** (all reads — prestige is written server-side only):

- `state.prestige(p)` — points or 0.
- `core._door_open(p, lvl)` — Arcanum and Relay open from level 1 for
  any prestige > 0 (option lock, dispatch guard, and scene guard all
  go through it). Echoes were already open to everyone since 013, so
  the plan's "echoes from day 1" perk is a structural no-op — nothing
  to build.
- Sheet: the name carries `✦ × min(points, 3)`; worldd's `_roster`
  stamps the same glyph on the Muster Roll.
- Stone of the Climb: a "THE STONE OF ERAS" section renders
  `w["eras"]` lines (injected by `inject_world`, latest 5) — hidden in
  a first-era world.

## Tests

- `worldd/tests/test_era.py` (4): close_era freezes the ledger and
  reincarnates with exact tiers (tourist below level 5 gets nothing;
  ceremony reaches the offline bystander's row and the finisher's
  in-memory doc, never the stale row); era_reset wipes every transient
  table, keeps the permanent ones byte-count-identical, frontier 1,
  first Stone line names the era; declare_last_siege letters exactly
  the playing docs; prestige_boot points/tiers/rested + roster glyph.
  All direct-connection tests run inside rolled-back transactions —
  the shared test DB is never actually reset.
- `plugin-linear-ascent/tests/test_022_007_era.py` (8): doors open at
  level 1 with prestige and stay locked without; **prestige grants no
  power** (atk/dfs/hp/energy-cap identical against a first-era twin);
  sheet glyph capped at three; Stone of Eras section shows/hides.
- Full suites: 556 plugin + 70 worldd, all green.

## Rulings made while executing

- The level-5 reincarnation bar got its own constant
  (`era.REINCARNATION_MIN_LEVEL`) rather than reusing the grants law's
  `GRANT_MIN_RECEIVER_LEVEL` — same number today, different laws.
- The frozen era keeps the Stone's last 400 lines, not all of them —
  a full era's Stone could be unbounded; 400 covers first clears, the
  war lines and the fall with room to spare at current pace.
- The siege-failure path needed nothing new: `_resolve_boss` already
  refunds pledges and posts "broke a war party" — and v1's "eras
  cannot end in defeat" ruling means failure just regroups.
