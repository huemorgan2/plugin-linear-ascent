# Phase 006 — The war's face

Goal: the siege is legible at a glance. "Please coordinate" becomes "we're
so close, get in here."

## Tasks

1. Warden card during a siege: HP bar, the silence countdown ("the wound
   closes in 3h 12m — keep striking"), hot-striker roll ("Kettle, Brakka
   +24 struck this hour"), faction damage standings.
2. The silence window mechanics from 002 wired to UX: wounds persist only
   while strikes land inside `W(F)`; full close on silence; pity ramp
   line when it happens ("the Warden heals — but slower than before").
3. `Sound the horn` — one tap letters every guildmate with the floor and
   the countdown; Crier lines at wound thresholds (75/50/25%) tower-wide.
4. Presence integration (003): the keep shows hot strikers; the gate
   shows "the war is on floor 47" when a wound is open.
5. Stone lines for first blood, biggest cut, and the fall (finisher named
   first — the SAO clearing-group fame line).
6. Vendor sync + worldd deploy; version bump + publish.

## Tests / acceptance

- Countdown truth: card countdown equals worldd's window state within
  cache TTL; a wound that closes resets the bar and writes the pity line.
- Horn letters exactly the faction roster, once per member per wound.
- Crier fires each threshold once per wound.
- Browser walkthrough with two accounts: open a wound, watch the bar and
  the striker roll from both sides, let it close on silence.
