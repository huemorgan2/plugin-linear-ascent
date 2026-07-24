# Phase 8 — execution summary (zero-config world signup, 0.2.0)

Status: **shipped**. No env vars anywhere in the player path.

## Done

- **worldd `/v1/enroll`** (public, no auth by design): mints
  `tenant + secret`, idempotent per client-generated `install_id`, IP
  rate-limited (`ASCENT_ENROLL_PER_HOUR`, default 5). Concurrent-enroll race
  resolved by re-reading after insert conflict. Migration
  `004_enroll.sql` adds a partial-unique `install_id` column. 3 new tests;
  worldd suite 13/13 green.
- **Plugin 0.2.0**:
  - `runtime.py` shared holder — tools resolve the backend at call time,
    so joining/leaving the world takes effect instantly, no restart.
  - `routes.py` — `/status`, `/join`, `/disconnect` (bearer-authed) + a
    themed HTML settings page in an iframe `SettingsTab`.
  - Credentials in Luna's vault (`plugin_linear_ascent.world_url/tenant/
    secret/install_id`); resolution: env override → vault → local solo.
  - `install_id` survives disconnect, so rejoin restores the same tenant.
- **Browser-verified on localhost** (real Luna, real clicks):
  solo status → Join → tenant `roys-luna-a4b3f670` minted → chat plays
  against worldd (log shows `/v1/scene`, `/v1/act` under the new tenant,
  zero restarts) → full Luna restart restores world mode from vault →
  disconnect → rejoin returns the same tenant (`existing: true`).
- **Production**: deployed to Render (`dep-d9hh81rtqb8s739isbgg`, live),
  `/v1/enroll` smoke-tested; dev Luna switched to
  `https://ascent-worldd.onrender.com` via the settings page itself
  (tenant `roys-luna-38c3d3d2`). Published `plugin-linear-ascent-0.2.0.zip`
  to the official marketplace; index sha256 verified.

## Landmines hit (for future phases)

- Luna's loader resolves `manifest.routes_module` relative to the plugin
  **class's** `__module__` + `.routes`. Our class lives in `plugin.py`, so
  `__init__.py` now pins `LinearAscentPlugin.__module__ = __name__`.
- `from __future__ import annotations` + a pydantic model defined inside
  `register_routes` makes FastAPI silently treat the request body as a
  query parameter (422 "missing query.body"). Request models must be
  module-level.

## Deliberately not done

- Google OAuth identity — would reintroduce operator provisioning (a
  Google Cloud OAuth app). Enroll + IP rate limit suffices until abuse.
- Per-chat-user credential slots — the world credential is
  per-installation; players are distinguished inside the tenant by Luna
  username, as before.
