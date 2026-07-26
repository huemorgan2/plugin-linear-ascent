# Scenario 1 — Mandatory world: auto-enroll, honest failure, no silent solo

## Setup
- QA Luna with plugin-linear-ascent loaded, NO `LUNA_ASCENT_*` env vars,
  NO vault credentials (fresh install), NO `ASCENT_DEV_LOCAL`.
- worldd reachable (local `uvicorn app.main:app --port 8600` or the
  Render instance).

## Steps
1. Open the settings tab → Linear Ascent. Expect: status shows
   **Shared world** (auto-enrolled at startup) OR, if enrollment hasn't
   landed yet, a "connect" affordance — never a bare "Solo (local)"
   presented as the normal mode.
2. In chat: `play linear ascent`. Expect the intro/title card. Confirm
   in worldd (`GET /admin/world` or the DB) that a player row exists
   for a freshly minted tenant — the game is running on the world, not
   on the local SQLite backend.
3. Stop worldd (or point the plugin at an unreachable URL via a fresh
   join). In chat: `show my scene`. Expect the **"The lift is down"**
   scene with a retry option — NOT a working private-world scene, and
   NOT an exception. The agent should empathize, not improvise a game.
4. Restart worldd. Click/choose the retry option. Expect the real
   current scene to come back with state intact.

## Pass criteria
- No path lands the player in local solo play without `ASCENT_DEV_LOCAL`.
- Outage is honest (named scene), recovery is one click.
- Enrollment is idempotent: restarting Luna keeps the same tenant.

## Scenario 1b — local character migration
- Prepare an install that played locally (dev flag on, character
  created, some gold), then remove the flag and restart with worldd up.
- Expect: the world now has that character (same name/level/gold);
  playing continues seamlessly. If a world character already existed,
  the world one wins.
