# Game execution — Phase 3: Shared world client

Parent: [001-buildfirst](../../001-buildfirst/plan.md) phase 3 · companion: `worldd/plans/002-execution` phases 1–2.

## Goal

The plugin becomes a thin client of worldd: same game, state now authoritative server-side; two tenants share one world.

## Deliverables

- `backend/remote.py` — `WorldClient(StateBackend)`: HTTPS + HMAC (`X-Ascent-Tenant`, `X-Ascent-Ts`, `X-Ascent-Signature` = HMAC-SHA256(secret, ts.body), `X-Ascent-Api: 1`), httpx.AsyncClient, idempotency keys on every mutation (uuid per intent), retries safe.
- Config: `LUNA_ASCENT_WORLDD_URL` + `LUNA_ASCENT_SHARED_SECRET` via `ctx.get_env`, vault fallback (`plugin_linear_ascent.shared_secret`); backend selection at load: remote if configured, else local.
- Player mapping: plugin passes stable Luna user id; worldd maps (tenant, luna_user) → player.
- Migration: local players export/import to worldd on first remote boot (one-shot, idempotent).
- Server-computed ages/countdowns rendered verbatim (clients never compute time).
- Contract tests: the phase-0/1 `StateBackend` test suite runs against BOTH `local.py` and `remote.py` (against localhost worldd).

## Exit gate

Same test suite green on both backends; in the browser, one player's fight on tenant A is visible in worldd DB; `/state` round-trip drives a full chat fight through localhost worldd; kill/clear events appear for a second player.
