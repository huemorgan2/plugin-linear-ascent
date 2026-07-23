# Plugin Phase 5 — execution summary (guilds + milestone bosses)

Status: **complete**.

## Built

- Guildhall: found a guild (◈500, name via chat text), join, leave, roster; guild tag shown in scenes.
- Milestone keeps: floors 10/20/…/100 route the gate to the boss keep; pledge (5⚡ escrow) with quorum progress dots; resolution and result cards handled by worldd in the same transaction as the completing pledge.
- Stone of the Climb shows frontier + boss inscriptions from `_world`.

## Verified

Engine unit tests (keep routing, pledge cost, guild flows) and the worldd two-player Gnarl quorum integration test: pledges from two tenants, single resolution, rewards to both, frontier raised world-wide, names carved on the Stone.
