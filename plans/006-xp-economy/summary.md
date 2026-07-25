# 006 — execution summary

Status: **complete** (unit + contract + dojo browser-verified 2026-07-24)
Produces version: plugin **0.6.1** (0.6.0 = the mechanic, 0.6.1 = walkthrough
fixes).

## What shipped

Mana is gone. The ✦ meter is now **the XP pool inside the current level**
("aether is crystallized experience"):

- `economy.py` — removed `MANA_*`, `mana_cap`, philtre, scout-mana cost.
  Added `hone_xp` (½ frontier kill), `sleep_xp_cost` (1 kill),
  `scan_xp_cost` (½ kill), `gear_level_req` (band start), `floor_level_req`
  (F−10), `ELF_XP_BONUS` (5%, replaces the elf aether cap).
- `state.py` — `mana_now/spend_mana/gain_mana` and `mana_ts/mana_val`
  removed from new docs; `spend_xp` (floors at 0, never touches level);
  `aether_philtre` dropped from dailies. Legacy docs: old keys preserved,
  never read; stored scenes with `mana` meters key-mapped in
  `Scene.from_dict`.
- `combat.py` — meters carry `xp/xp_need`; Sleep costs the skipped kill's
  XP and awards nothing; scan prefers optics charges, falls back to pool
  XP; elf +5% kill XP. Level-up keeps overflow carry (plan D1).
- `core.py` — hone charges ◈ + ✦ atomically; tier gear gated by level with
  hints and steering refusals; floors gated by level F−10 on top of Warden
  unlocks; philtre purchase branch deleted.
- `render.py`/`sheet.py`/`scene.py` — ✦ bar renders `xp/xp_need` with the
  new tooltip; sheet drops `aether` (xp/xp_to_next already there).
- `plugin.py` — sidekick METERS rule: the word "mana" is banned; teaches
  the pool mechanics (added after the live walkthrough caught the agent
  saying "mana").
- Docs: `vision/economy.md` §1 rewritten; `vision/research.md` §6 XP-model
  survey added.

## Verification

- **Unit**: 76 passed (9 new: pool costs, gates, spend floor, sleep/scan,
  elf bonus, legacy-doc load).
- **Contract (worldd)**: re-vendored; 14 passed against a fresh test DB
  (`ascent_world_test` on the local :5433 Postgres — the old docker DB is
  gone; worldd `.venv` rebuilt with uv/py3.12).
- **Dojo browser run**: `dojo/results/0005-xp-economy-2026-07-24/` (superproject) —
  all 4 scenarios in `tests/006-xp-economy/` PASS, plus death save, mercy
  death (✦/level untouched), idempotent scene reads. One finding fixed
  mid-run (the "mana" slip). QA stack rebuilt from scratch on :8777.

## Deviations from plan

- Floor-gate E2E used frontier 13 (not 12): floor 12 at frontier 11 isn't
  pickable at all (Warden gate fires first) — the level gate needs an
  unlocked floor above level+10.
- Playwright MCP browser was shared with the user's live session (tabs kept
  moving); the run switched to a dedicated headless Chromium driver
  (`drive.py` in the dojo results folder).
