# Phase 007 — World & agent: armory, matchup moment, town

Goal: the shared-world and sidekick pieces — faction armory donations
(worldd), the one remaining agent beat, and town readability.

## Tasks

1. **Faction armory (worldd):**
   - Migration: `ascent_armory` table (tenant, player, item slug,
     durability fraction, deposited_at).
   - Endpoints (HMAC, idempotent like the ledger): deposit, list, take
     (member-only, admin can purge); caps (e.g. 50 items/faction).
     **Executed as effects, not endpoints (2026-07-28):** the desk is
     an engine scene since 015, so deposit/take ride the
     `execute_effects` pipeline (`armory_deposit` / `armory_take`)
     and the shelf rides `inject_world` — same HMAC, same
     doc-in-flight semantics, zero new HTTP surface.
   - 006 retro (EV first): write the armory's exploit inequality in
     this plan BEFORE coding — a donate/take round-trip must never
     beat the pawn shop (donate full, take, pawn at a good
     `pawn_rate` day = free arbitrage unless takes are member-gated
     with a cooldown or the fraction rides through untouched). State
     the inequality, then pick the caps.
     **Stated (2026-07-28):** no gold ever enters or leaves through
     the armory — deposit moves `(slug, wear-fraction)` from the doc
     into the row, take moves the SAME pair back, so
     `value(round-trip) − value(never-donated) = 0` for any
     `pawn_rate` path: arbitrage is impossible by construction.
     Remaining abuse surfaces and their caps: storage (armory as a
     bottomless pack) → 50 rows per faction; vacuuming (one member
     draining the shelf) → one take per player per world day,
     member-only both ways; laundering (worn in, fresh out) →
     forbidden by the same fraction-rides-through rule the 005 retro
     demands. Donor name stays on the row for the audit.
   - Plugin: pawn scene gains "donate to the armory" for faction
     members; 015 desk gets an ARMORY section (list + take).
   - 005 retro: the "durability fraction" column is live now —
     deposit moves the item's `durability_pack` stash into the row
     (× `economy.item_pool(g)`), take restores it. An armory donation
     must never launder a worn piece back to full.
2. **Matchup moment (plan §5):** first fight per monster TYPE whose
   profile hard-counters the player's class → one moment nudge via
   `send_muted_message` (flag per type in the doc); silence invited,
   VOICE rules attached. No other messaging (0.17.2 stays).
   001 retro: ground the agent — every muted state line must name the
   CURRENT enemy and floor explicitly (in the 001 dojo the sidekick
   called a feral boar "Brackjaw" because the state line let it guess).
3. **Town readability:** locked rows with unlock levels for Arcanum /
   Relay / Fields / non-day-1 areas ("🔒 Arcanum — level 6"); **Tower
   Gate moves to the top** as "The Tower Gate — leave town and climb".
   004 note: the Arcanum row + refusal line already shipped in 0.21.0
   — this task is now only Relay/Fields/other locked rows + the gate
   reorder.
   006 retro: the Forge page is LONG now (gear prose + locked rung +
   six relic-shelf rows before the options). While reordering town,
   collapse any shop shelf past ~8 prose rows into a `<details>`
   block (the [i]-dossier pattern, zero JS) — readability is this
   task's charter, and the shops are where it strains first.
4. **Shop owned-state (004 dojo carryover):** a rung you already own
   stays fully buyable — mark it ("✓ worn") or drop it from the rack
   so the two buyable rows are always NEW steps. Same `_rack` helper,
   one branch.
5. Vendor sync + **worldd deploy with migration** + version bump +
   publish.

## Tests / acceptance

- worldd: endpoint tests (deposit/list/take, caps, non-member refusal,
  idempotency keys); migration up on a copy of prod schema.
- Plugin unit: donate flow, desk ARMORY fragment, matchup-flag logic
  (fires once per type, never for soft counters, never twice).
- Dojo: donate a worn sword, take it with a second member account;
  fight the first flyer as warrior and see exactly one sidekick tip;
  verify the town list order and locked rows as a fresh player.
  005 retro (hard rule): the pane replays the scene payload CACHED in
  the doc — after any DB edit, drive one navigation click before
  reading the screen; after any plugin render change, restart Luna by
  port-kill (8765) the same way worldd is killed by 8600.
  006 retro: drive rare paths by `jsonb_set` on the live doc
  (encounter atk 999 / hp 1 / flags) instead of long natural fights —
  006 covered the whole death matrix in minutes this way. And check
  option ICONS in every dojo screenshot: new item families need the
  `_opt_gear_icon` hook wired separately from the pack strip (006's
  relic rows shipped naked until the screenshot caught it).

Exit: all green, published, worldd migrated + deployed,
`execution_summary.md`.
