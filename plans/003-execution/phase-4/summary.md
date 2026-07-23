# Plugin Phase 4 — execution summary (social client)

Status: **complete** (engine-side; worldd executes the effects — see worldd phase 3 summary).

## Built

- `engine/social.py`: Relay Office (inbox, compose via chat text, enclosed-gold collection), the Fields (PvP target list, 3⚡ + 2/day caps, beginner protection surfaced), Vault grants desk (burn/cap math shown to the player), guildhall scenes, milestone keep pledge flow.
- Effects contract: engine appends to `doc["_effects"]` (send_letter, collect_gold, grant, pvp_attack, boss_commit, letters_seen); the host executes them. Local mode simply never injects `_world`, so social options vanish — one engine, two modes, no flags.
- `pending_events`: death reports / boss results queued into the victim's doc are delivered as full-screen cards before their next scene.

## Verified

8 engine unit tests (options gated by world presence, costs, caps, compose flow, pending-event delivery) + worldd integration tests exercising the same surface over signed HTTP.
