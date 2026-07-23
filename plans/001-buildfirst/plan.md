# Plan 001 — Build First: Linear Ascent

Multi-phase build plan for the Linear Ascent game plugin. Design sources: [vision](../../vision/vision.md) · [story](../../vision/story.md) · [world](../../vision/world.md) · [economy](../../vision/economy.md) · [ideas](../../vision/ideas.md). UI component spec: [../../design/chat_components.md](../../design/chat_components.md).

## Architecture at a glance

```
Luna tenant (plugin-linear-ascent)          Render (shared world)
┌──────────────────────────────┐            ┌──────────────────────┐
│ tools: ascent_scene,         │   HTTPS    │ worldd (FastAPI)     │
│        ascent_choose, ...    │──────────▶ │  - authoritative     │
│ scene renderer (HTML cards)  │  API key   │    player/world state│
│ local cache of own player    │            │  - world-day cron    │
└──────────────────────────────┘            │  - PvP/boss resolver │
                                            │ Postgres             │
                                            └──────────────────────┘
```

- **Phases 0–2 run fully local** (per-tenant state inside the plugin) so the solo game ships early. Phase 3 lifts state into the shared world service; the plugin becomes a thin client. The state schema is designed in Phase 0 to survive that move.
- The **engine is a data-driven state machine**: floors, encounters, items are content files; code only knows scenes, choices, rolls, and ledgers.
- The **agent never free-forms game state**. Tools expose the current scene and accept a choice; handlers refuse out-of-order calls with steering hints (flows live in the tool layer, per project experience — prose rules lose, gates win).

## Tool surface (target)

| Tool | Purpose | Notes |
|---|---|---|
| `ascent_scene` | current scene: location, narration, options, meters | safe to call anytime |
| `ascent_choose` | submit option id from the last scene | rejects stale/unknown options with hint |
| `ascent_character` | sheet: stats, gear, gold, sidekick | read-only |
| `ascent_town` | news feed, Stone of the Climb, boards | read-only |
| `ascent_social` | letters, grants, taunts | phase 4 |
| `ascent_guild` | guild ops, boss commits | phase 5, skill-gated until unlocked |
| `ascent_admin_*` | spawn/teleport/grant for testing | skill-gated, never in production toolset |

Prefix `ascent_` — grep all other plugins for collisions before finalizing (tool names are a global namespace; collisions abort Luna boot).

---

## Phase 0 — Scaffold & foundations (small)

**Goal:** installable empty plugin with the right bones.

- Plugin skeleton `plugin_linear_ascent`, in-code `PluginManifest` as the authoritative version stamp (keep all three stamps in sync — toml-only bumps look like failed upgrades).
- Content format: floors/encounters/items as YAML under `content/`, loaded and validated at startup (schema + collision checks). Floor 1 stub.
- State layer: per-player document store with an interface (`StateBackend`) implemented first as local storage, later by the world-service client — the Phase 3 seam is designed here.
- Deterministic RNG (seeded per player+day) so tests replay; server-side timestamps for all regen/interest math (Luna agents have no clock — never trust model-supplied time).
- Unit test harness + one dojo smoke test.

**Exit:** plugin installs and hot-reloads convergently on QA Luna; `ascent_scene` returns a placeholder scene.

## Phase 1 — Solo core loop (the game exists)

**Goal:** floors 1–10 fully playable solo, all core economy live.

- Character creation flow: race → class → name (stage-aware tools; each step refuses skips).
- Roothollow menus: Forge, Apothecary & Medlab, Lodge, Vault, pawn shop, Stone (read-only stub), tower gate.
- Combat resolver per [economy.md](../../vision/economy.md) §2–3: ATK/DEF/HP math, stand/attack/run, class-specific extra options, potion use mid-fight.
- Energy ⚡ / aether ✦ meters: lazy regen from timestamps; costs per action; energy cell daily limits.
- Death: carried gold gone, armor/shield destroyed, respawn scene in Roothollow.
- Vault: deposits, withdrawals, 5%/day compound interest accrued on visit.
- Presents: ≥20h-away roll on the gift table; luck charm and halfling modifiers.
- Content: tier 1 (floors 1–10) — encounter tables, regular Wardens 1–9, Gnarl solo-tuned fallback (quorum comes in phase 5).
- Sidekick v1: advice on options (insight-scaled accuracy), scout (aether cost), one death-save per day, carried-item slot.
- Balancing instrumentation from day one: per-action log of XP/gold/energy so §9 tuning has data.

**Exit:** a dojo agent creates a character and reaches floor 5+ across simulated days; unit tests cover combat math, interest, death, regen; playtest on a real running Luna (unit tests alone have missed real-Luna bugs before).

## Phase 2 — Chat UI components

**Goal:** the game renders as designed cards, not raw text.

- Implement [chat_components.html](../../design/chat_components.html) as the plugin's rendering layer: scene card, options list, meter bar, event cards (loot, death, letter, boss, happenings).
- Options are clickable AND numbered — plain-text "2" in chat must always work (cards are enhancement, never a gate).
- Constraints from production experience: widgets are cookie-auth-only on hosted Luna; no plugin pip deps for the UI; cache-bust static assets with `?v=<manifest.version>`.
- Follow `vision/ux_guidelines.md` and [world.md](../../vision/world.md) §2 exactly (fonts, tokens, scene grammar).

**Exit:** every message type renders correctly on QA Luna in light of the hosted-widget pitfalls; text-only fallback verified.

## Phase 3 — Shared world service (multiplayer backend)

**Goal:** one world, many Lunas.

- `worldd` FastAPI service + Postgres on Render (same account as scheduler-service). Endpoints mirror the `StateBackend` interface; per-tenant API keys; idempotent writes (players will race).
- Move authoritative player state server-side; plugin keeps a read cache. Migration path for phase-1/2 local players.
- World-day rollover as a Render cron: interest posting, lodge expiry, PvP allotment reset, presents eligibility, daily happenings digest.
- Stone of the Climb: world frontier floor, first-clear records, happenings feed (server-generated, timestamped — clients render ages, never compute them).
- Design every scheduled/timed mechanic to resolve server-side and be *reported* on the player's next session (turns die with their SSE stream — nothing may depend on a live client).

**Exit:** two separate Luna tenants play in the same world; kill/clear events appear in both; world-day cron survives a Postgres restart.

## Phase 4 — Social layer

**Goal:** the LORD drama engine.

- Lodge enforcement + "in the fields" list; PvP attacks vs offline players (2/day, 3⚡), win/loss resolution, loot + XP bounty, beginner protection (levels 1–5).
- Kill news + free taunts in daily happenings.
- The Relay: letters (5g), optional purse/item attachments; town board (25g/day).
- Gold grants at the Vault: 10% burned fee, 150×level daily cap, level-5+ or guildmate receivers; rate limits and audit log (anti-RMT).

**Exit:** dojo scenario with 3 accounts: one skips the lodge, gets killed offline, reads the news, receives a consolation grant and a letter. (Dojo runs must handle approval gates and drive turns via API.)

## Phase 5 — Guilds & milestone bosses

**Goal:** group play and the shared climb.

- Guildhall: found/join/leave, guild board, roster.
- Milestone Warden commits: quorum table from [economy.md](../../vision/economy.md) §5, 24h commit window, server-side resolution when quorum is met (or window lapses), per-participant payouts, names on the Stone, world broadcast.
- Quorums configurable per world size.
- Guild structures v1: one buildable (watchtower: guildmates skipping the lodge are protected N nights/week), raidable by rival guilds.

**Exit:** dojo scenario: 3 accounts clear Gnarl (floor 10) via async commits; frontier advances for a 4th account that never fought.

## Phase 6 — Content build-out & balancing

**Goal:** all 100 floors, tuned.

- Author tiers 2–10: encounter tables, Wardens, floor flavor per [world.md](../../vision/world.md) biomes. Pipeline: generated drafts → human review → schema validation; every floor gets the same anatomy so authoring is templated.
- Balancing passes against telemetry: fights/day distribution, gold faucet/sink ledger, time-per-tier vs. the §4 targets; tune the four coupled knobs together (interest, gear prices, quorums, fade rule).
- Class option decks finalized across all tiers; sidekick night jobs.

**Exit:** economy telemetry within ±25% of design targets for tiers 1–3 with real testers; content lint passes for all 100 floors.

## Phase 7 — Hardening & release

**Goal:** shippable.

- Multi-day dojo soak: concurrent accounts, forced deaths, lodge/PvP races (design list-before-create paths for convergence; add reapers where duplicates can race).
- Abuse review: grant funnels, alt farming, fade-rule bypass.
- Onboarding polish: first 10 minutes scripted tight (character → first fight → first death lesson → bank lesson → lodge lesson).
- Docs, marketplace listing, screenshots of the chat cards.
- Publish to marketplaces.com.ai after push (standing rule), verify install + upgrade on a live tenant via the CDP browser flow.

**Exit:** installed from marketplace on a clean tenant, played end-to-end on tier 1 by someone who isn't us.

---

## Sequencing and gates

Phases 0→1→2 are strictly sequential (engine before UI). Phase 3 can start its service scaffolding in parallel with Phase 2. Phases 4 and 5 depend on 3. Phase 6 content authoring can begin any time after the Phase 0 content format freezes; its balancing half needs 3+.

## Open decisions (resolve before the phase that needs them)

1. **Phase 1:** is class chosen at creation or unlocked at level 5 (first session simplicity)?
2. **Phase 2:** clickable option buttons — supported natively by Luna chat widgets, or do we ship numbered-text-only first?
3. **Phase 3:** one global world vs. world-per-marketplace-region; quorum config default for a small launch population.
4. **Phase 5:** watchtower protection strength (nights/week) — don't let it obsolete the lodge gold sink.
5. **Naming:** in-code slug is `linear_ascent`; confirm marketplace display name ("Linear Ascent") before the Phase 7 listing.
