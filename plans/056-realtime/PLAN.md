# 056 — realtime: the Playing tab

A live window into the tower, riding the polling the game already
does. A new button on the bottom sound bar called **Playing**,
wearing a live counter of players online right now. Tapping it
opens an overlay with the world's pulse: who entered the game, who
leveled, who struck a warden, who founded/joined/left/was kicked
from a faction, who died, who lay down to sleep in the open
fields, who sent up a flare or blew the horn for help. If you have
a faction, a second tab adds your faction's finer grain — the
floors your people are entering, the weapons they just bought. If
you have no faction, that tab is a doorway: join one, here's the
Guildhall.

## The mechanism (all of it)

Every open client already GETs `/pane/peek` every 2 seconds
(`pane.py:560` → `webplay.py:141`) to notice scene changes. We add
two integers to that existing payload:

- `online` — players whose `ascent_players.updated_at` is within
  5 minutes, computed behind the same 30s in-process cache as
  `_presence()` (`app/social.py:322`).
- `feed_head` — the id of the newest happening, from an in-process
  variable updated at every emit (no DB read on quiet ticks).

The client keeps the last feed id it has seen. Only when the panel
is **open** and `feed_head` moved does it fetch
`GET /pane/playing/feed?scope=&since=<id>` (≤50 rows, one indexed
`WHERE id > $1` query). Closed panel ⇒ the two ints are the entire
cost. Latency is 0–2 s — indistinguishable from push for a feed.

No new connections, no SSE/websockets, no Redis, no new infra.
At 5,000 concurrent the peek traffic already exists (~2,500 tiny
req/s); the feed endpoint is hit only by open panels on actual
news. Knobs if the box ever strains: peek every 3 s, raise asyncpg
`max_size` past 10. Both one-liners.

## What exists already (build on it, don't duplicate it)

- `ascent_happenings` (`worldd/migrations/003_social.sql:16`) — the
  world feed table: `(id, world_day, kind, line, floor, created_at)`,
  kinds `climb|faction|pvp|era`. Already written on: death
  (`engine/combat.py:1755` → `app/social.py:930`), faction join
  (`app/social.py:851`), faction rename, warden falls, era turns.
- `execute_effects` (`worldd/app/social.py:791`) — every game act's
  side effects flow through one ladder; the single emit point.
  `run_act` (`app/game.py:163`) wraps it in the act's transaction.
- The 60s badge loop (`pane.py:1013`) — cold-path precedent; the
  design rule at `pane.py:982` ("badges never ride the 2s hot
  path") stays true: we add ints to peek, not queries.
- The sound bar (`pane.py:1290-1306`) + the feedback overlay panel
  (`#fbpanel`, CSS `pane.py:171-180`) — the Playing button and
  panel copy this exact pattern.
- The homepage online counter (`static/site/site.js:22`) — same
  number, now shown in-game.

## Data model (one migration: `worldd/migrations/019_realtime.sql`)

Widen the existing feed rather than invent a second one:

```sql
ALTER TABLE ascent_happenings
  ADD COLUMN actor   TEXT,          -- display name
  ADD COLUMN faction TEXT,          -- faction slug, NULL = none
  ADD COLUMN scope   TEXT NOT NULL DEFAULT 'world',  -- world|faction
  ADD COLUMN meta    JSONB;         -- {floor, level, item, ...}
CREATE INDEX ha_scope_id   ON ascent_happenings (scope, id DESC);
CREATE INDEX ha_faction_id ON ascent_happenings (faction, id DESC)
  WHERE scope = 'faction';
```

- `scope='world'`: everyone sees it. The homepage feed keeps
  reading exactly what it reads today — unchanged.
- `scope='faction'`: only that faction's tab (floor entries,
  weapon buys — grain that would drown the world feed).
- Retention: the in-process world-day rollover runs once a day
  already; add
  `DELETE FROM ascent_happenings WHERE scope='faction' AND created_at < now() - interval '14 days'`.
  World rows stay (small, and Stone/era history reads them).
  Additive only — never destroys existing production data.

## Events emitted (all via `execute_effects` / existing handlers)

| Event | Emit from | Scope |
|---|---|---|
| entered the game | first act of the day — `factions.py:185 record_attendance` already detects it | world |
| level up | new effect from `engine/social.py:913` (drillmaster) | world |
| warden strike | `_fx_warden_strike` `social.py:1352` — throttle: first strike per player per warden | world |
| warden fall | already written (`social.py:1668`) | world |
| died | already written (`combat.py:1755`) — add actor/floor meta | world |
| sleeping in the fields | new effect from `core.py:2258 sleep_fields` | world |
| faction found | `_fx_faction_found` `social.py:974` (today writes nothing) | world |
| faction join | already written `social.py:851` | world |
| faction leave | `social.py:869` (today writes nothing) | world |
| faction kick | `_fx_faction_kick` `social.py:996` | world |
| flare sent / answered | `_fx_flare` `social.py:1516`, `_fx_flare_answer` | world |
| horn blown | `_fx_horn` `social.py:1461` | world |
| war-party pledge | `_fx_boss_commit` `social.py:1794` | world |
| entering floor N | new effect on floor change (`engine/state.py` climb) | faction |
| bought a weapon | new effect from `core.py:1595 _gear_purchase` | faction |

Engine side: each new one is a single
`_effect(p, {"kind": "happening", ...})` call
(`engine/social.py:24`) carrying the new fields — the pure-engine /
worldd split stays clean.

## Client (all in `pane.py`, patterned on the feedback panel)

1. Sound bar: `<button class="sndbtn" id="plybtn">▶ <span id="plycount">–</span></button>`
   before `#fbbtn`. Counter repaints from every peek; brief pulse
   on change.
2. `#plypanel` overlay (clone of `#fbpanel` CSS): header
   "PLAYING — N on the floors", two tabs **World | Faction**.
3. World tab: reverse-chron lines, relative timestamps, floor tag;
   prepends new rows when the cursor advances; DOM capped at 100.
4. Faction tab: `scope='faction' AND faction=$mine` merged with
   world rows whose actor is a faction-mate. No faction ⇒ the tab
   renders: "You climb alone. Join a faction at the Guildhall on
   any milestone floor — or found your own." with a button that
   deep-links to the Guildhall scene.
5. Nothing runs while `document.hidden` (same rule as peek).

## Server endpoints

- `feed_head` + `online` ints added to the `/pane/peek` payload
  (web `webplay.py:141`, Luna twin `routes.py:293`, HMAC twin
  `main.py:158`).
- `GET /pane/playing/feed?scope=world|faction&since=<id>` — same
  three doors, same auth guards as every pane route; faction scope
  403s unless the caller is a member (server checks membership,
  never trusts a client-claimed faction).
- Rate limiting: the existing per-account token bucket covers it.

## Order of work

1. Migration `019_realtime.sql` (additive only).
2. Emit pass: new `_effect(...)` calls in the engine + handler
   lines in `execute_effects`.
3. Peek piggyback (head + online caches) + `/pane/playing/feed`.
4. Pane UI: button, counter, panel, two tabs, join-a-faction CTA.
5. Tests: worldd (docker `ascent-postgres`) — feed scoping,
   faction 403, head-cache behavior, retention delete; plugin —
   new effects emitted on level-up / buy / sleep-fields / climb.
6. Release: bump, vendor, commit, push, deploy, publish.

## Future note (out of scope)

If sub-second push ever matters (a real chat in this panel), the
same table + cursor feeds an SSE stream with an in-process fan-out
— safe while `numInstances: 1` holds. Nothing in this plan would
be thrown away. Multi-instance would additionally need Redis-class
pub/sub. Neither is planned.
