# Phase 005 — Nights & weeks (clocks II)

Goal: the night slot at the Lodge and the weekly strongbox at the Vault.
One decision per night; one chosen reward per week. Deliberately shallow —
the variety is the feature.

## Tasks

1. Night slot at the Lodge: one action per night, chosen before or on
   return — **rest** (bank rested aether: capped pool, spent as bonus XP
   on kills only, never on contract or strongbox payouts) or **work**
   (gold at dawn, flavoured by the site: forge shift, bar shift).
   Professions with ranks stay deferred; the slot is their future socket.
   **004 learning:** the contract exclusion is already structural —
   contract payouts route through `contracts.claim` (direct `p["xp"] +=`),
   never the kill path, so a rested bonus hooked on the kill path can't
   leak into them. Keep it that way; add a test that pins it.
2. Rested numbers: modest bonus (not WoW's 200% — XP is the scarce
   resource and the climb is the game), pool cap of a few days' accrual.
3. Work numbers: a night pays a meaningful fraction of a hunting day and
   never raises the Energy cell's 1/day ceiling (the cell cap is the
   whole safety mechanism for offline gold).
4. Weekly strongbox at the Vault: three counters the game already tracks
   — kills, floors gained, warden engagements — thresholds 2/4/6 open
   slots; at the weekly tick the player picks **exactly one** reward
   (gold lump / aether lump / gear-tier token / relic). Personal, distinct
   from the faction weekly.
   **004 learnings:** count warden engagements where 004 already does —
   `contracts.note_warden` fires at `combat.start_encounter(kind=
   "warden")`, the OPEN, win or bleed; reuse that hook (or its call
   site), don't invent a second definition of "engagement". And the
   "gear-tier token" reward slot has NO real item yet — 004 shipped a
   repair token in its place; design the real token here or keep the
   substitution deliberately.
5. Gate registry: night slot at level 6, strongbox at level 10.
6. Vendor sync + worldd deploy; version bump + publish.

## Tests / acceptance

- One night action per night, enforced; rest pool caps; rested bonus
  applies to kill XP only.
- Work income lands at dawn, scales with 002's tables, cell stays 1/day.
- Strongbox: thresholds open slots; picking one closes the week; unpicked
  weeks fall back to the lowest slot, never to nothing.
- Ladder check: a level-5 player sees the night slot only as a NEXT line.
