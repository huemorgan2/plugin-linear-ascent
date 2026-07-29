# Execution summary — 022 phase 004: dawn & contracts

Status: **DONE** (plugin + vendor sync; deploy/publish deferred to the
end of the 022 run per the run agreement).

## What shipped

### The dawn law
- `state.touch_daily`: HP restores to FULL at the world-day boundary —
  and only there. The Lodge's +20-at-dawn special case is deleted
  (`LODGE_NIGHT_HEAL_HP` removed from economy); the Lodge now sells the
  one thing dawn doesn't: not being found. Copy updated in both lodge
  scenes.
- `p["daily"]["dawn_healed"]` records whether dawn actually closed
  anything; the Morning Crier opens with "dawn — your wounds have
  closed." when it did. Noticed, never taught — no tutorial line
  anywhere.
- The potion sink survives whole: no daytime trickle, stew/tent/potion
  prices untouched, gated by `test_mid_session_healing_still_costs_the_
  pre_phase_rates`.

### The contract board
- `engine/contracts.py` (new): `board(day, frontier)` is a pure
  function seeded from the world day (`random.Random(f"ascent-board-
  {day}")` — the pawn broker's pattern), so the whole tower reads one
  board. Three shapes v1:
  - **cull** — N (3–5) of a named creature on a floor within 2 of the
    frontier; pays 0.8× the kills' raw gold + half-weight XP.
  - **class** — N (5–8) kills by steel/arrows/spellwork, any floor;
    priced off the tower's waist (0.6× frontier).
  - **warden** — answer any keep's horn once; counted at the fight's
    OPEN (showing up is the job); pays half frontier warden pay.
  - ~25% of days one job carries a repair token on top (seeded — the
    same job for everyone).
- No accept step, no new bookkeeping: progress is counted off the kills
  `combat._victory` already scores (`contracts.note_kill`) and warden
  opens in `combat.start_encounter` (`contracts.note_warden`). The
  progress slate lives in `p["contracts"]` and is wiped at the day tick
  — unfinished work expires, no rerolls.
- The board is a town location (`board` option in the square, scene +
  claim flow in core). Claims pay gold + XP minus the broker's stamp —
  `BOARD_PRICE` (◈ 10) finally works, off the top of every payout.
- Gate registry: `board` opens at level 4; the square's NEXT line and
  the level-up announcements carry it automatically (020's machinery).
  Below 4 the option renders locked with the standard shard-note
  refusal.

### The economy law
- `vision/economy.md` gained §0: **gold buys time, never power**, with
  the Energy cell and the healing ladder as the worked examples and a
  designer's test for any new sink. §7 documents the dawn law; §8's
  stale "town notice board" bullet replaced by the real contract board.

## Test state

- 525 plugin tests green (+17 in `test_022_004_contracts.py`; the four
  lodge-heal tests in `test_008_pace.py` rewritten to the dawn law).
- 61 worldd tests green after vendor sync.
- Registry guard extended: `BOARD_LEVEL` is a covered gate constant;
  the level-3→4 bundle is now founding + board + mercy-ends (opens
  before closes).

## Decisions worth remembering

- **Warden engagements count at the open, not the win** — the horn
  contract is about showing up; a bleed-out still honors it. 005's
  strongbox "warden engagements" counter should reuse this hook.
- **Claim pays through `contracts.claim` (direct `p["xp"] +=`), not
  the kill path** — so 005's rested-aether bonus (kill XP only) is
  structurally excluded from contract payouts for free.
- **The board rides the live frontier**, so a mid-day Warden fall
  reshuffles it (flavor, but voids half-finished culls) — logged in
  we_have_to_continue_this.md with the honest fix.
- The "gear-tier token" is a repair token for now — the real item is a
  design TODO shared with 005's strongbox.

## Forward corrections applied

- `005-nights-and-weeks/plan.md`: rested-aether exclusion is already
  structural; strongbox counters can reuse the contracts hooks.
- `008-together/plan.md`: assist contract credit must route through
  `contracts.note_kill` exactly once per participant.
