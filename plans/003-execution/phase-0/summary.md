# Phase 0 — execution summary

Status: **complete** (browser-verified 2026-07-23, ~00:20 local)

## What was built

- `plugin_linear_ascent/` package, loading as `plugin-linear-ascent v0.1.0` on the QA Luna:
  - `economy.py` — all §1–§8 formulas + Forge/Apothecary/milestone tables as code (content never carries numbers)
  - `engine/scene.py` — the Scene/Option/Meters renderer contract with `to_text()` fallback
  - `engine/rng.py` + `state.py` helpers — deterministic SHA256 (player, world-day, counter) rolls
  - `engine/state.py` — player document, lazy meter regen from timestamps, world-day, vault interest
  - `engine/core.py` — full state machine (creation → town menus → gate → floors), steering refusals
  - `engine/combat.py` — combat resolver, class options, death/death-save, victory/loot
  - `content/schema.py` — YAML loader with lint (prose caps, banned words, no authored numbers) + computed stats; floors 1–10 (Greenreach) authored
  - `backend/base.py` + `local.py` — StateBackend seam; local impl on `ascent_players`/`ascent_ledger` (JSONB doc + append-only ledger)
  - Tools registered: `ascent_scene`, `ascent_choose`, `ascent_character` (no collisions; `ascent_` grep clean)
- Tests: 22 unit tests green (economy vs design tables, creation gates, combat, death, interest, regen, content lint) with a `luna_sdk` stub conftest.

## QA stack

- QA Luna: `luna/` submodule, fresh DB `luna_ascent` in the existing `luna-postgres` container, `.env` copied from the sibling checkout (auth mode normalized), UI built to `ui/dist`, serving on **:8777** (8765/8766 were held by other local Lunas). Owner `roy`, onboarding force-completed via SQL.
- Plugin loaded via symlink `luna/plugins/plugin_linear_ascent`.

## Browser evidence (exit gate)

Real chat on localhost:8777, Claude Opus 4.6 driving:
- "play linear ascent" → `ascent_scene` chip → creation scene relayed verbatim.
- Typed `2` → Elf (numbered fallback works); `2` → Sorcerer; free-text name → Roothollow arrival with meters rail (HP 52/52 ⚡24/24 ✦10/11 — elf mana cap +1 correct).
- Gate → Floor 1 → hunt (1⚡ deducted) → grey wolf (ATK 6/DEF 3, formula-correct) → "cast the sleep spell" mapped to the class option → +6 XP (half of 12, correct), fight ended.

## Deviations / notes

- Phase 0 plan called for a placeholder scene; the real engine + tier-1 content shipped instead (phase 1 mostly complete at the engine level as a result).
- Fixed during test: shard hint claimed ◈ 50 buys a blade (cheapest is ◈ 250).
- Sidekick occasionally invents light flavor ("wardens have work worth doing") — harmless, polish in phase 7 prompt text.
- Server restart required for tool changes (in-tree symlink path) — as documented.
