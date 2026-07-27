# Phase 007 — World & agent: armory, matchup moment, town

Goal: the shared-world and sidekick pieces — faction armory donations
(worldd), the one remaining agent beat, and town readability.

## Tasks

1. **Faction armory (worldd):**
   - Migration: `ascent_armory` table (tenant, player, item slug,
     durability fraction, deposited_at).
   - Endpoints (HMAC, idempotent like the ledger): deposit, list, take
     (member-only, admin can purge); caps (e.g. 50 items/faction).
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

Exit: all green, published, worldd migrated + deployed,
`execution_summary.md`.
