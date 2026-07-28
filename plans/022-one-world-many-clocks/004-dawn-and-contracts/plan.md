# Phase 004 — Dawn & contracts (clocks I)

Goal: the first two new clocks. Dawn: you sleep, you heal. Daily: three
jobs on the board. Nothing before level 4 (the ladder in the main plan §9);
announcements ride plan 020's "what opens next" line.

Prerequisite: **plan 020** (gate registry) for the reveals; **002** for
final prices (contracts pay in gold/XP whose meaning 002 sets).

## Tasks

1. Nightly rejuvenation: HP restores to full at the world-day boundary —
   and only there. No daytime trickle, so the potion sink survives whole:
   mid-session healing still costs gold and still buys time. Replaces the
   Lodge's +20-at-dawn special case; the dawn line reads "dawn — your
   wounds have closed". Noticed, never taught.
2. Contract board in Roothollow (the unused `BOARD_PRICE` finally works):
   three contracts seeded per world day — same seed pattern as the pawn
   rate so the whole world sees one board and can talk about it.
3. Contract shapes v1: N kills of a named creature on a named floor / N
   kills with a weapon class / one warden engagement. Progress counted
   off the existing combat ledger — no new bookkeeping.
4. Payouts: gold + XP priced against 002's daily income, occasional
   gear-tier token; expire at the world-day tick; no rerolls.
5. Gate registry entries: board at level 4; the square's NEXT line
   carries it before then.
6. Economy law written into `vision/economy.md`: **gold buys time, never
   power** (with the Energy cell and potions as the worked examples).
7. Vendor sync + worldd deploy; version bump + publish.

## Tests / acceptance

- Dawn heal fires exactly once per world day; a player at 6 HP mid-day
  stays at 6 HP until dawn or a paid heal.
- Board determinism: same world day ⇒ same three contracts for every
  player; expiry at tick.
- Contract credit from a normal hunt, no double-count with assists later.
- Sink check: simulated mid-session damage still routes gold to
  stew/medgel at pre-phase rates.
