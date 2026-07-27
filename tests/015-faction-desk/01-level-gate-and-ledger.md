# 015 / 01 — Founding gate + the ledger

Browser E2E on QA Luna (pane at the Linear Ascent sidebar section).

## Steps

1. With a character below level 4, open the GAME tab and walk to the
   Guildhall (town → Guildhall).
2. Read the scene: there must be NO "Raise a new banner" option; a line
   must say the hall charters banners for level 4+ climbers.
3. Open the COMMUNITY tab. A panel titled THE LEDGER must list existing
   factions (at most 10), each row showing sigil, name, members, store.
4. Type part of a faction name in the FIND input. The list must filter
   to matches as served by the server (not client-side only — watch the
   network call).

## Pass

- No founding option below level 4; hint line present.
- Ledger renders ≤10 rows in ANSI panel style (monospace, block borders).
- Search round-trips to the server and filters.

## Fail

- "Raise a new banner" visible below level 4, or founding succeeds via
  API for a level-3 character.
- Ledger missing, unstyled, or search does nothing.
