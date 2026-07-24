# Phase 8 — Zero-config world signup (0.2.0)

## Goal

Kill every env var. A player installs the plugin from the marketplace and
joins the shared world with one click from a settings page — no provisioning
by the world operator, no secrets to copy, nothing to type.

## Design

- **worldd** gains a public, IP-rate-limited `POST /v1/enroll`
  (`{install_id, name_hint}` → `{tenant, secret}`). Idempotent per
  `install_id`, so re-joining always restores the same tenant (and all its
  players' progress). Migration 004 adds `ascent_tenants.install_id`.
- **Plugin** gains:
  - `runtime.py` — a shared mutable holder (`state["remote"]/["local"]`)
    read by the tools at call time, so the backend switches live.
  - `routes.py` — `/status`, `/join`, `/disconnect` plus a self-contained
    HTML settings page served at `/api/p/plugin-linear-ascent/ui/settings/`.
  - A `SettingsTab` (iframe) in the manifest; credentials live in Luna's
    encrypted vault under `plugin_linear_ascent.*` (self-owned, no grant
    prompt). `install_id` survives disconnect on purpose.
- Resolution order at `on_load`: env override (dev) → vault → local solo.
- Default world URL baked in: `https://ascent-worldd.onrender.com`.
  "Advanced" field allows custom servers.

## Explicitly rejected

Google OAuth signup — requires provisioning a Google Cloud OAuth app
(consent screen, client secret, redirect URIs), i.e. exactly the manual
step this phase exists to remove. Identity can be layered on later if
abuse appears; the enroll endpoint + IP rate limit is enough for now.

## Steps

1. worldd: migration 004, `/v1/enroll`, tests (mint→play, idempotency,
   validation).
2. Plugin: runtime holder, vault resolution, routes + settings tab, 0.2.0.
3. Browser-verify on localhost: solo → join → play against worldd →
   restart persistence → disconnect → rejoin (same tenant).
4. Deploy worldd to Render, switch the dev Luna to production via the
   settings page (real user flow), publish 0.2.0 to the marketplace.
