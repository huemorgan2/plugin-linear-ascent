# Plan 002 — Generate the Whole Game (plugin side)

Successor to [001-buildfirst](../001-buildfirst/plan.md): 001 defines the build order (phases 0–7); this plan defines how ALL the game's material gets produced — code, 100 floors of content, the full art set, and the service integration — and what "the whole game" means as a deliverable. The service half lives in the companion repo: `luna-linear-ascent/worldd/plans/001-worldd`.

Design sources: [vision](../../vision/vision.md) · [story](../../vision/story.md) · [world](../../vision/world.md) · [economy](../../vision/economy.md) · [ideas](../../vision/ideas.md) · [chat components](../../design/chat_components.md) · [banner styleguide](../../design/pixel_art.md).

## Deliverable

A marketplace-installable `plugin-linear-ascent` where a fresh player can: create a character, grind floors 1–100 across months of real days, bank/shop/lodge in Roothollow, die and recover, fight Wardens solo and milestone Wardens with others, PvP, message and grant gold, guided throughout by the shardmind (the Luna agent) — with every arrival rendered as a 1-bit banner card.

## Workstreams

Workstreams run in parallel where 001's sequencing allows; each has its own generator + acceptance gate.

### A. Engine code (001 phases 0–1, 4–5)

Hand-written, not generated: state machine, combat resolver, ledgers, regen math, death, vault interest, presents, PvP resolution, quorum commits. The engine knows only scenes/choices/rolls/ledgers — all game data comes from content files. Tool layer gates every flow (out-of-order calls refused with steering hints). `StateBackend` interface from day one: local impl first, `worldd` client in phase 3 — same tests run against both.

### B. Chat UI (001 phase 2)

Port [chat_components.html](../../design/chat_components.html) into the plugin renderer: one `Scene → card` function, ANSI discipline (one mono size, `█░` meters, `[n]` keys, no rounded corners), typewriter on newest card only, banners full-bleed. Text-only fallback always works ("2" in plain chat = option 2). Assets cache-busted `?v=<manifest.version>`.

### C. Content generation — the 100 floors

The big generated artifact. Pipeline:

1. **Schema freeze (with 001 phase 0):** YAML per floor — `floor.yaml` (meta, encounter table, warden), `mobs/*.yaml`, `items/*.yaml`. Every numeric field derivable from [economy.md](../../vision/economy.md) formulas is COMPUTED by the loader, not authored — content files carry only names, prose, option flavor, and deviations. That keeps 100 floors balance-safe by construction.
2. **Tier template:** each tier (10 floors) = 1 biome flavor pack + ~4 mob families + regular-warden flavor + 1 milestone Warden + ~2 signature items, per [world.md](../../vision/world.md) §biomes. Floor N inherits its tier pack; only boss floors get bespoke prose.
3. **Generation:** LLM drafts per tier from a fixed prompt (biome brief + story bible + banned-word list from ux_guidelines), emitted directly as schema-valid YAML.
4. **Lint gate (automated):** schema validation, name collisions, prose length caps, vocabulary lint (no out-of-world jargon), economy fields absent (must be computed), option-id stability.
5. **Human pass:** read the tier as rendered cards in the dojo, not as YAML. Fix voice, ship.
6. **Order:** tier 1 hand-tuned during 001 phase 1 (it IS the template); tiers 2–3 next (they get real playtesting); tiers 4–10 batch-generated once telemetry confirms tiers 1–3 land within ±25% of economy targets.

### D. Art generation — the banner set

Pipeline already built: [tools/generate_banners.py](../../tools/generate_banners.py) (Gemini → crop → 320×112 → Bayer 1-bit → white ink on alpha), styleguide in [pixel_art.md](../../design/pixel_art.md).

- Starter 13 (done, iterate on review): village buildings, greenreach, gnarl, death, present.
- Per remaining tier: 1 zone banner + 1 milestone Warden banner ≈ 18 more, generated alongside the tier's content batch (same brief feeds both prompts).
- Acceptance: review as a sheet, tinted on `--panel`; regenerate by slug until every banner reads at a glance.

### E. Sidekick (shardmind) behaviors

Prompted behaviors + tools, not free-form: advice accuracy scaled by insight stat, scout (✦ cost), one death-save/day, carried-item slot, night jobs (phase 6). The agent NEVER mutates state directly — every effect is a tool call the engine validates. Voice rules come from the story bible; whispers render in the aether-striped block.

### F. Multiplayer integration (001 phases 3–5)

Plugin becomes a thin client of `worldd` (companion repo): `StateBackend` swaps to the HTTP client, server-computed ages/countdowns everywhere (agents have no clock), all timed mechanics resolve server-side and are REPORTED on next session (turns die with their SSE stream). Contract is pinned in `worldd/plans/001-worldd` — plugin and service version the API together (`X-Ascent-Api: 1`).

### G. Balancing & telemetry

Per-action log (XP/gold/energy per fight, per day, per tier) from 001 phase 1 onward. Weekly tuning pass against [economy.md](../../vision/economy.md) §9 targets: fights/level ≈ 5√L, daily income ≈ 200F, tier pace vs. §4 table. The four coupled knobs (interest, gear prices, quorums, fade rule) move together or not at all.

### H. Release

001 phase 7 unchanged: multi-day dojo soak, abuse review, scripted first-10-minutes, marketplace listing with card screenshots, publish to marketplaces.com.ai after push, live-tenant verify via CDP browser.

## Schedule (maps to 001 phases)

| Step | Workstreams | Gate |
|---|---|---|
| 1 | A: engine core + C1 schema freeze + tier-1 hand content | dojo agent reaches floor 5+; combat/interest/death unit-tested |
| 2 | B: UI cards + D: starter banners wired | every card type renders on QA Luna; text fallback verified |
| 3 | F: worldd client + service live (companion plan) | two tenants share one world |
| 4 | A: social + E: sidekick v1 | 3-account dojo drama scenario passes |
| 5 | A: guilds/quorums | async Gnarl clear by 3 accounts |
| 6 | C: tiers 2–10 generated + D: 18 tier banners + G: tuning | content lint green for 100 floors; tiers 1–3 telemetry within ±25% |
| 7 | H: hardening + release | installed from marketplace, played by someone who isn't us |

## Risks / standing constraints

- Tool namespace: `ascent_*` — grep all plugins before boot (collisions abort Luna).
- Three version stamps stay in sync; in-code `PluginManifest` is authoritative.
- Hosted widgets: cookie-auth only, no pip deps in UI path.
- Content generation may drift from voice — the lint gate catches structure, only the rendered-card human pass catches tone. Budget it per tier, don't skip it.
- `content/art/banners/raw/` (model originals) stays out of git — regenerable, 26 MB and growing.
