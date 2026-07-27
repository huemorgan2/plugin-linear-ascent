# Phase 005 — Durability & repair

Goal: power becomes a running cost. Paid gear wears; the Forge repairs
for gold + a few XP; broken never means helpless.

## Tasks

1. `economy.py`: `pool(T) = round(240 / (1 + 0.3·(T−1)))`; repair price
   = 20% of item price × missing fraction; repair XP =
   `hone_xp(frontier)`.
2. `engine/state.py`: doc v2 — `durability: {slot: uses_left}` set on
   purchase (per-slot staged activation: slots without a paid item have
   no entry and no UI); helpers `wear(p, slot)`, `is_broken`.
3. `engine/combat.py`: wear hooks — weapon per attack, shield/armor per
   hit taken, shoes per chase action (002's flee/open/close); broken =
   bonus halved, with a one-line fight note the first round it applies.
4. `engine/core.py`: Forge repair option (price + XP quoted, refusal if
   XP short — same grammar as honing); buy scene teaches durability in
   one line on the first paid purchase per slot.
5. `pane.py` + `render.py`: durability bar under equipped items
   (16×16 wrench icon, hover text "90% — repair at the Forge").
   003 retro: the wrench grid already exists in `icons.py` (shipped
   with the 003 icon set as a CSS-mask data-URL) — reuse `_ticon`,
   don't add a second icon path.
6. Pawn (from 006 if not yet landed): worn gear pays × durability
   fraction — coordinate ordering with 006.
7. Vendor sync + deploy; version bump + publish.

## Tests / acceptance

- Unit: pool math per tier; wear hooks fire exactly once per event;
  broken halving; repair pricing incl. partial wear; staged activation
  (no durability UI before first paid item).
- **Economy sim gate:** reference at-level play — repair spend ≤20% of
  income at every band; a player who never repairs still clears their
  intended matchups (broken ≠ bricked) with the basic weapon.
  002 retro: rounds-per-fight now differ hard by class — a kiting
  archer took 23 rounds on a slow bulwark in the dojo (vs ~6 for a
  warrior trade). Per-attack weapon wear must be simmed per class with
  the chase-aware loops (`test_017_speed_chase.py`), or bow durability
  costs will silently tax the archer's whole playstyle.
- Migration: v1→v2 docs get full durability on existing gear.
- Dojo: buy a Pigsticker, grind it down, watch the bar, repair it —
  confirm the teaching line and the hover text.

Exit: all green, published, worldd synced, `execution_summary.md`.
