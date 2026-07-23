# Game execution — Phase 4: Social layer

Parent: [001-buildfirst](../../001-buildfirst/plan.md) phase 4 · companion: `worldd/plans/002-execution` phase 3.

## Goal

The LORD drama engine in chat: offline PvP, kill news, letters, grants, boards.

## Deliverables

- `ascent_social` tool: inbox (letters render as letter cards), send letter (5g, purse/item attach rules), grants at the Vault (10% burn, 150×level cap, L5+/guildmate), town board post (25g).
- PvP through the tower gate/fields: `pvp targets` list (server-provided), attack (2/day, 3⚡), result card; defender's next session gets the full death-report story card; taunt line attachment.
- Lodge enforcement live: skip lodge → "in the fields" (server truth); beginner protection L1–5.
- Daily Happenings + Stone: town scenes render the server feed (one line per event, names violet, deltas right-aligned).
- Death reports, presents, letters all delivered as "pending events" on next session (turns die with SSE — nothing depends on a live client).

## Exit gate

3-account drama in real browsers/tenants: A skips lodge, B kills A offline (news + Stone), A returns to a death-report card, C sends grant + letter, A reads both in chat. Ledger reconciles every gold movement.
