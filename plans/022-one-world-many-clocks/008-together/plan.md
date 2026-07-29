# Phase 008 — Together: the flare and assist strikes

Goal: 80% of "fighting side by side" without synchronous combat. Full
shared-round parties (guard/flank/mark) remain their own future plan.

## Tasks

1. The shard flare: at low HP in a fight, burn aether — every **hot**
   climber on the floor (003's 3-minute tier, the only people who can
   actually answer) gets "a red flare — a climber is dying there ·
   Answer the flare" on their next card. The dying player's death timer
   stretches while an answerer is en route. Rescue possible, never
   guaranteed.
   **003 learnings:** the hot tier is served by `social._presence`
   (30s cache, field locations only) — target the flare from the same
   snapshot, don't re-derive; and a torch's status can be ~3 min stale
   (a closed app still reads "hunting"), so the flare must tolerate
   answerers who are already gone.
2. Answering: pays gold + aether and writes a permanent Stone line
   ("Brakka answered a flare on floor 12"). The answerer lands in the
   fight as a rescuer round — monster turns, the flared player gets one
   free disengage.
3. Assist strikes: acting on the same creature/warden as a floor-mate
   within minutes links the logs ("Brakka's axe bit first — your blade
   finishes it"), pays a small bonus over two solo kills, and grants
   both full contract credit. No kill-stealing exists, by construction.
   **004 learning:** contract credit has exactly one entry point —
   `contracts.note_kill(p, enc, dtype)`, called once in
   `combat._victory` for the killer. The assist path must call it once
   for the ASSISTER's doc (their own board view) and must NOT re-call
   it for the killer; `_bump` caps at `need`, but the honest contract
   is one call per participant per kill. 004's acceptance test
   "no double-count with assists later" lands here.
4. Aether cost on the flare so it cannot be spammed; one flare per fight.
5. Lodge long fire (cheap, from the sketch): who sits the fire tonight,
   canned words, stand a stranger a stew. Canned lines only — no free
   chat, no moderation surface.
6. Vendor sync + worldd deploy; version bump + publish.

## Tests / acceptance

- Flare reaches hot players only; once per fight; timer stretch bounded.
- Answer flow: rescuer arrives into the real fight state; both ledgers
  and the Stone line write once.
- Assist math: bonus over two solo kills; contract credit to both; no
  double-dip with rested aether on the same kill.
- Browser walkthrough with two accounts: die without a flare, then be
  saved by one — the second story should feel different.
