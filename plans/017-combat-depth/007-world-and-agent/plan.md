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
2. **Matchup moment (plan §5):** first fight per monster TYPE whose
   profile hard-counters the player's class → one moment nudge via
   `send_muted_message` (flag per type in the doc); silence invited,
   VOICE rules attached. No other messaging (0.17.2 stays).
3. **Town readability:** locked rows with unlock levels for Arcanum /
   Relay / Fields / non-day-1 areas ("🔒 Arcanum — level 6"); **Tower
   Gate moves to the top** as "The Tower Gate — leave town and climb".
4. Vendor sync + **worldd deploy with migration** + version bump +
   publish.

## Tests / acceptance

- worldd: endpoint tests (deposit/list/take, caps, non-member refusal,
  idempotency keys); migration up on a copy of prod schema.
- Plugin unit: donate flow, desk ARMORY fragment, matchup-flag logic
  (fires once per type, never for soft counters, never twice).
- Dojo: donate a worn sword, take it with a second member account;
  fight the first flyer as warrior and see exactly one sidekick tip;
  verify the town list order and locked rows as a fresh player.

Exit: all green, published, worldd migrated + deployed,
`execution_summary.md`.
