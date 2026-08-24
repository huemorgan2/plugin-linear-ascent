# Phase 2 — world snapshot cache + scene-needs slimming (worldd)

## Goal

An act performs **zero** viewer-independent world recomputation: it reads a
process-local snapshot rebuilt at most once per TTL, single-flight. Measured:
`inject_world` ≤ 15 ms warm on the local DB; queries per act ≤ 10; the same
act sequence returns byte-identical fragments before/after (modulo snapshot
age ≤ TTL).

## Steps

1. **`worldd/app/worldcache.py`** — one module, one pattern (the existing
   `_presence_cache` / `_feed_cache` house style, generalized):
   - `async def snapshot(conn) -> dict` returns
     `{frontier, hall_board, factions_hall, factions_total, guild_dir,
       faction_banners, faction_colors, happenings, stone, eras, roster,
       roster_count, census, rooms, rooms_n, warden, fallen}` — every
     section of `inject_world` that does not depend on the viewer.
   - TTL 10 s (constant `WORLD_TTL_S`), stale-while-revalidate: an expired
     snapshot is served while ONE coroutine rebuilds (an `asyncio.Lock`
     guards the rebuild — single-flight; no thundering herd on expiry).
   - Explicit invalidation hooks where staleness is user-visible inside one
     click: `_raise_frontier` and warden-fall paths call
     `worldcache.invalidate()` so a fresh floor shows immediately.
   - Presence keeps its own 30 s cache and hot-window rule (untouched —
     its TTL must stay under the 3-minute hot window per 022 §003).
2. **`inject_world` becomes assembly, not computation**: merge the snapshot
   with the per-viewer live sections — faction panel + armory (members),
   inbox count, letters, pvp targets, grant targets, known names, profiles,
   attendance/dues resolution. All of these are post-Phase-1 indexed
   point reads.
3. **Scene-needs slimming.** Add a needs map keyed by the option/scene
   family (mirror of what `render.py` actually reads from `_world`):
   e.g. a gate or fight card renders no roster, no guild directory, no pvp
   targets; the Guildhall renders the hall sections; the square renders
   rooms + happenings. `inject_world(option=…)` skips assembling sections
   the arriving scene cannot render. Conservative default: unknown option →
   full injection (correctness first). The map lives beside the renderer's
   consumption sites with a test asserting every `_world[…]` key read in
   render.py appears in the map.
4. **Peek/feed paths reuse the snapshot** where they overlap
   (`feed_head`, online, presence already cached — no change).
5. **Tests**: snapshot single-flight (two concurrent expired readers → one
   rebuild), TTL respected, invalidation hook forces rebuild, equality of
   injected `_world` before/after for a seeded fixture and a matrix of
   scene families, needs-map completeness gate.

## Verification

- Full worldd suite green.
- `worldd/tools/profile_act.py`: act p95 < 80 ms local over 50 mixed
  clicks (menu, fight, guildhall, square), warm; queries/act ≤ 10 (count
  via the timing wrapper).
- Two-browser dojo spot-check: player A kills a warden / frontier rises →
  player B's next click (≤ 10 s later or immediately post-invalidation)
  shows it — the multiplayer freshness contract still holds.

## Rollback

`git revert` the phase commit — `inject_world` returns to live computation
(slow but correct). The cache module is self-contained; no schema or data
involvement.

## Execution status — 2026-08-24

DONE. `worldd/app/worldcache.py` landed: TTL 10 s, single-flight,
stale-while-revalidate, `invalidate()` on frontier raises (warden fall,
boss resolve, post-commit in run_act). inject_world rides the snapshot;
fight rounds (gated on an ACTIVE encounter — "attack_<Name>" outside one
is a PvP initiation and keeps the full read) skip letters/names/
pvp_targets/grant_targets/profiles. TTL is env-tunable
(`ASCENT_WORLD_TTL_S`); the test suite runs with 0 (build-per-read, no
staleness) while `test_078_worldcache.py` pins the production TTL and its
laws (6 tests). Warm inject_world: 2–4 ms, 13 queries; rebuild at 10k:
270–500 ms in background, once per 10 s at most. Leaderboard keeps you
visible below the top-200 cut (own row rides along).
