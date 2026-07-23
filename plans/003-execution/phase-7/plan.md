# Game execution — Phase 7: Hardening & release

Parent: [001-buildfirst](../../001-buildfirst/plan.md) phase 7 · worldd companion phase 5 (deploy).

## Goal

Shippable: soaked, onboarded, packaged, published, and pointed at production worldd.

## Deliverables

- Dojo soak: concurrent accounts, forced deaths, lodge/PvP races; convergent list-before-create paths verified.
- Abuse review pass: grant funnels (burn+caps), alt farming (per-tenant player scoping), fade-rule bypass.
- Onboarding: first 10 minutes scripted tight — character → first fight → first death lesson → bank lesson → lodge lesson (encounter scripting in tier-1 content + sidekick lines).
- Package: `python scripts/package_plugin.py` (luna-plugins kit) → `plugin-linear-ascent-<v>.zip`; three version stamps in sync.
- Publish to marketplaces.com.ai (standing rule) with `LUNA_MP_TOKEN` from `../luna-plugins/.env`; verify index sha256.
- Production wiring: plugin default `LUNA_ASCENT_WORLDD_URL=https://ascent-worldd.onrender.com`; register production tenant via `/admin/tenants`.
- README + marketplace listing with card screenshots from the dojo runs.

## Exit gate

Installed from the marketplace on a clean tenant; a fresh player plays tier 1 end-to-end against production worldd in a real browser.
