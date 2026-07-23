# Game execution — Phase 0: Scaffold & foundations

Parent: [001-buildfirst](../../001-buildfirst/plan.md) phase 0 · [002-full-game](../../002-full-game/plan.md) workstream A/C1.

## Goal

Installable plugin with the right bones: manifest, content format + computing loader, `StateBackend` seam, deterministic RNG, `ascent_scene` returning a placeholder scene on a real QA Luna.

## Deliverables

- `plugin_linear_ascent/` package:
  - `__init__.py` — `LinearAscentPlugin(LunaPlugin)`, `PluginManifest(name="plugin-linear-ascent", version=0.1.0)`; registers `ascent_scene`, `ascent_choose`, `ascent_character` in `on_load` (per-user state tables created `checkfirst=True`)
  - `luna-plugin.toml` — kept in sync with the in-code manifest (all three stamps: toml, manifest, and the version constant)
  - `engine/` — `scene.py` (Scene/Option dataclasses per the renderer contract), `state.py` (PlayerState document), `rng.py` (deterministic: seeded SHA256(player_id, world_day, counter))
  - `content/` — YAML schema v1: `floors/floor_001.yaml` stub (meta, encounter table, warden), `schema.py` loader that VALIDATES and COMPUTES all economy numbers from formulas (content carries only names/prose/flavor — economy.md §3 formulas in `economy.py`)
  - `backend/` — `StateBackend` protocol (ensure_player, get_state, apply_action...); `local.py` impl on plugin-owned SQL tables (`ascent_players`, `ascent_ledger` — namespaced, JSONB docs)
- Unit test harness (`tests/` with luna_sdk stub, following personality-template pattern)
- Symlink into QA Luna `plugins/`; server restart registers tools

## Constraints (from project experience)

- Tool prefix `ascent_` — grep all other plugins for collisions first (global namespace; collisions abort boot).
- Import `luna_sdk` only, never `luna.*`.
- Server timestamps for all time math — never model-supplied time.

## Exit gate (browser)

QA Luna boots with the plugin loaded (`plugin.loaded` in log); in the chat UI, asking to play calls `ascent_scene` (tool chip visible) and a placeholder Roothollow scene comes back. Unit tests green.
