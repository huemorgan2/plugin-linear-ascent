# Phase 1 — projection columns + indexes (worldd)

## Goal

No query anywhere in worldd filters or aggregates on `doc->>'…'` without an
index, and no code path fetches more than a bounded set of full player docs
(the viewer's own row, profiles ≤ 80, room-more ≤ 200). Measured: `_roster`,
`_census`, `_rooms`, `_known_names`, `_grant_targets`, `_pvp_targets`,
presence and online each complete in < 10 ms against the local DB, and their
cost is O(result), not O(players).

## Steps

1. **Migration `worldd/migrations/022_player_projections.sql`** — additive
   generated columns on `ascent_players` (Postgres ≥ 12):

   ```sql
   ALTER TABLE ascent_players
     ADD COLUMN IF NOT EXISTS stage text
       GENERATED ALWAYS AS (doc->>'stage') STORED,
     ADD COLUMN IF NOT EXISTS name text
       GENERATED ALWAYS AS (doc->>'name') STORED,
     ADD COLUMN IF NOT EXISTS floor int
       GENERATED ALWAYS AS (greatest(coalesce((doc->>'floor')::int,0),1)) STORED,
     ADD COLUMN IF NOT EXISTS level int
       GENERATED ALWAYS AS (coalesce((doc->>'level')::int,1)) STORED,
     ADD COLUMN IF NOT EXISTS guild text
       GENERATED ALWAYS AS (doc->>'guild') STORED,
     ADD COLUMN IF NOT EXISTS location text
       GENERATED ALWAYS AS (doc->>'location') STORED,
     ADD COLUMN IF NOT EXISTS sleeping boolean
       GENERATED ALWAYS AS ((doc ? 'sleeping')) STORED,
     ADD COLUMN IF NOT EXISTS lodged_until_day int
       GENERATED ALWAYS AS (coalesce((doc->>'lodged_until_day')::int,-1)) STORED,
     ADD COLUMN IF NOT EXISTS bank bigint
       GENERATED ALWAYS AS (coalesce((doc->>'bank')::bigint,0)) STORED;

   CREATE INDEX IF NOT EXISTS ix_players_playing_updated
     ON ascent_players (updated_at DESC) WHERE stage = 'playing';
   CREATE INDEX IF NOT EXISTS ix_players_playing_floor
     ON ascent_players (floor) WHERE stage = 'playing';
   CREATE INDEX IF NOT EXISTS ix_players_playing_name
     ON ascent_players (name) WHERE stage = 'playing';
   CREATE INDEX IF NOT EXISTS ix_faction_ledger_giver
     ON ascent_faction_ledger (tenant, player)
     WHERE amount > 0 AND kind IN ('join_fee','dues','donation');
   ```

   Data preservation: `ALTER … ADD COLUMN GENERATED` computes from the
   existing `doc` — nothing rewritten in `doc`, nothing dropped. The
   engine's exact projection expressions must mirror the Python readers
   they replace (`greatest(coalesce(floor,0),1)` mirrors `_census`,
   `-1` default mirrors `_pvp_targets`' lodge check).

2. **Rewrite the hot readers in `worldd/app/social.py`** to projections:
   - `_roster` → one aggregate for the count + one
     `SELECT name, floor, level, guild, bank, updated_at … WHERE
     stage='playing' ORDER BY floor DESC, bank DESC LIMIT 12` with the
     banked-wealth rank done by a window function — **no doc column in the
     select list, no `json.loads`**.
   - `_census` → `GROUP BY floor` on the projected column.
   - `_known_names`, `_grant_targets` → `SELECT name … LIMIT n`.
   - `_pvp_targets` → SQL filter on `lodged_until_day < $day+1 AND level >
     $protect` over projections; no doc fetch, no Python filtering loop.
   - presence + `online_count` + `_rooms`' 24 h window → keep their SQL but
     filter on `stage='playing'` (projected) so the partial indexes serve
     them; `_rooms` selects only the tile fields it needs (name, level,
     location, floor, guild, sleeping, gear armor via
     `doc#>>'{gear,armor}'` in the select list — narrow, not the whole doc).
   - `_room_key_of` stays Python but receives a narrow record; add a parity
     test: for every doc in a fixture corpus, room key from the narrow
     record == room key from the full doc.
   - `_profiles` keeps full-doc fetch (bounded ≤ 80) but its name filter
     uses `ix_players_playing_name`; the faction-ledger grouped read uses
     the new partial index with a `WHERE tenant/player = ANY(…)` filter
     instead of grouping the whole table.
3. **Convert the stragglers**: the remaining `doc->>'stage'` uses in
   `factions.py`, `adminpage.py`, `era.py`, and `site.py`'s public feed —
   swap to the projected `stage`.
4. **worldd tests**: extend `worldd/tests/` with (a) migration idempotence
   (runs twice), (b) projection parity — insert docs, assert columns match
   `doc` extractions, (c) the reader rewrites return the same shapes as
   before on a seeded fixture (golden comparison against the old Python
   implementations kept in the test file), (d) `EXPLAIN` smoke: the roster
   and census plans contain no Seq Scan on ascent_players when the table
   carries > 1,000 rows (seeded in-test).

## Verification

- Full worldd suite green.
- Re-run the Phase-0 profile script (`/tmp/profile_inject.py` pattern,
  committed as `worldd/tools/profile_act.py`): every rewritten reader
  < 10 ms warm; `inject_world` total < 250 ms before Phase 2's cache
  (hall_board/directory still live at this point).
- `SELECT count(*)` sanity on ascent_players before/after migration —
  identical; spot-check three docs byte-identical.

## Rollback

`git revert` the phase commit. The generated columns and indexes are
harmless to leave (additive, read-only); if removal is ever wanted:
`DROP INDEX …; ALTER TABLE ascent_players DROP COLUMN …` — the `doc`
column is untouched throughout, so no data can be lost. Old code reads
`doc` directly and keeps working against the migrated table.
