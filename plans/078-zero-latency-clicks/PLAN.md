# 078 — Zero-latency clicks (world snapshot, projections, static art)

## Problem

Every click in `/play` — a menu row, an attack, a shop tab — takes seconds.
Roy reported it 2026-08-24 ("attacks takes 4 seconds every menu takes a few
seconds — this is html it should be super snappy"). Measured the same day on
local worldd (:8600, Postgres 16.14 on :5434, 891 players / 556 playing):

- `GET /health`: 4 ms — server and DB baseline are fine.
- `POST /play/api/act` (gate/town menu swap): **1.1–2.6 s**, response
  **653,632 bytes**, every click, uncached.
- Breakdown of one act: engine `apply_choice` 0 ms, HTML render 1–8 ms,
  JSON 2–10 ms, `_save_doc` 156 ms, **`social.inject_world` 1,109 ms**.
- `inject_world` fires **35 queries per act**. The worst —
  `SELECT doc, updated_at FROM ascent_players WHERE doc->>'stage'='playing'`
  (`social._roster`) — fetches **every playing player's full JSON doc**
  (556 docs, ~4 MB) and parses each in Python, per click; 4.9 s cold,
  ~300 ms warm. Siblings (`_census`, `_rooms`, `_pvp_targets`,
  `_grant_targets`, `_known_names`, presence, online) all filter on
  `doc->>'stage'` — an unindexed JSONB extraction — several also pulling
  whole docs.
- Of the 653 KB response, **648 KB is one element**: the scene banner GIF
  base64-inlined as a CSS mask (`render.py` `_fx_data_url` /
  `_banner_data_url` and 23 sibling call sites). The browser can never
  cache it; it re-downloads, re-parses and re-decodes the same art every
  click. Gzip is on but base64 image data barely compresses.

At 10,000 playing players the roster scan alone becomes ~88 MB fetched and
JSON-parsed **per click**. The current shape does not survive growth.

## Root cause

Two independent design debts, not one bug:

1. **The world is recomputed from scratch inside every act.**
   `inject_world` rebuilds viewer-independent state — Muster Roll, census,
   rooms, hall board, guild directory, happenings, stone, eras — with
   full-table JSONB scans and Python-side doc parsing, although that state
   is identical for every viewer and changes on the order of seconds, not
   clicks. Only presence/online/feed have caches (30 s / 30 s / 2 s — the
   proven house pattern, applied to 3 of ~15 sections).
2. **Art rides inside the HTML.** Every banner, event GIF, gear icon,
   portrait and sigil is base64-inlined into each fragment so the card
   works on any host without a network fetch. That decision predates the
   website `/play`; the deployed site has a static mount (`/static/fxart`)
   sitting unused for banners.

Nothing here needs React or a client rewrite: the fragment-swap client
spends 1–8 ms per card. The engine is instant. The seconds are the world
recompute and the payload.

## Fix — five phases

- **Phase 1 — projection columns + indexes.** Additive generated columns
  on `ascent_players` (stage, name, floor, level, guild, location,
  sleeping, lodged_until_day, bank) + partial indexes; every hot query
  rewritten to indexed SQL over projections; full-doc fetches survive only
  where bounded (profiles ≤ 80, room-more ≤ 200, the viewer's own row).
- **Phase 2 — world snapshot cache.** One single-flight, TTL-bounded
  snapshot of all viewer-independent world state; acts read the snapshot;
  per-viewer sections stay live but are post-Phase-1 cheap. Scene-needs
  slimming stops injecting sections the arriving card never renders.
- **Phase 3 — all images to static URLs.** `render.py` emits
  `{art_base}/…` URLs instead of data URLs at all 25 call sites; worldd
  mounts the vendored `content/art` tree; the Luna host serves the same
  tree through the plugin's own router; one-shot GIFs keep their frame-0
  nonce; ambient loops and stills cache cleanly. Payload target ≤ 30 KB.
- **Phase 4 — write path.** `_save_doc` (156 ms): batch the ledger
  inserts, bind JSONB natively, measure the UPDATE, confirm indexes don't
  bloat the write.
- **Phase 5 — scale proof + dojo.** Seed 10,000 synthetic players locally,
  benchmark p50/p95 act latency and payload, run the dojo scenario with
  latency assertions, then (on explicit request) deploy with post-deploy
  verification.

Phases 1–2 are worldd-owned; Phase 3 spans plugin + worldd (vendor);
plan lives here with the plugin per house precedent (076).

## Performance budgets (the plan's definition of done)

| Metric | Today | Budget |
|---|---|---|
| act server time, local p95 | 1.1–2.6 s | < 80 ms |
| act response size (menu card) | 653 KB | < 30 KB |
| queries per act | 35 | ≤ 10, none full-scan |
| click-to-painted-card, local browser | seconds | < 300 ms |
| roster/census cost at 10k players | ~88 MB fetch + parse | one indexed aggregate, snapshot-amortized |

## Verification

Each phase carries its own gate (see phase files). Plan-level:

- `pytest worldd/tests` and `pytest plugin-linear-ascent/tests` green
  (modulo the four pre-existing failures filed in dojo 0047).
- The Phase-5 benchmark script prints the budget table with measured
  numbers; every row inside budget.
- Dojo scenario `tests/078-zero-latency-clicks/01-snappy-clicks.md` PASS
  with a numbered results folder.

## Operational notes

- Postgres 16.14 local; Render production also ≥ 12 — `GENERATED ALWAYS AS
  … STORED` is available. The ALTER rewrites the table once (~14 MB local —
  instant; at production size still small). **Additive only; no column or
  table drops; player docs are never rewritten** (devprocess data rule).
- Migration slot: `worldd/migrations/022_player_projections.sql`.
- `doc->>'stage'` call sites to convert: social.py ×16, factions.py ×1,
  adminpage.py ×1, era.py ×1.
- The snapshot cache is per-process (uvicorn runs one worker on Render
  today). If workers ever scale out, each holds its own ≤10 s-stale
  snapshot — acceptable by design; note it in ops docs.
- Art tree being published: banners 1.0 MB, creatures 4.2 MB, events 63 MB,
  gear 840 KB, weapons 680 KB, portraits 20 KB (1,102 PNG + 315 GIF). The
  events dir is already public at `/static/fxart` — this widens the same
  door, no new exposure class. The font (24 KB WOFF) is not an image and
  stays inline so chat cards keep rendering offline.
- The `?t=` nonce on one-shot GIFs is load-bearing (038: Chromium shares
  animation clocks for identical URLs). Nonced URLs defeat the HTTP cache
  by design — acceptable: one-shots play on kills/rides, not menu clicks.
- The working tree carries unrelated in-flight edits (adminpage, feedback,
  figure3d, 077 triangle work). Commit each phase scoped to its own files.

## Execution status — 2026-08-24

Phases 1–4 executed and verified; phase 5 scale proof + dojo complete
(deploy pending explicit request). Act p95 at 10,517 players: 8.2 ms
server-side, ≤ 133 ms browser click-to-paint (budget 300 ms). Payloads
5–17.4 KB on the wire (budget 30 KB), zero inline raster art. Dojo
0050 PASS. Full worldd suite green (215); plugin suite green but for 4
pre-existing failures from other workstreams. Details per phase below
their own PLAN.md files.
