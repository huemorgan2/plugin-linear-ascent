# Phase 002 — Speed & the chase

Goal: the two-state range model (at_range / close) with speed driving
kiting, fleeing, catching, and the small log-decay dodge. Depends on
001 (profiles exist; slow/fast traits already authorable).

## Tasks

1. `economy.py`: speed scale (slow 3 / normal 5 / fast 7, alpha +1;
   player base 5 + shoes bonus — shoes themselves ship in 004, the
   hook lands now); chase formulas from plan §2.4 (p_close, open
   distance, flee, dodge% = min(12, round(7·log2(1+a)))).
2. `engine/combat.py`:
   - `encounter["range"] = "at_range"` on start; melee players may
     *Close in* (free −50% monster hit while crossing); monster closes
     per p_close at end of at-range rounds; monster hits −50% at range.
   - Bow ×0.6 close-quarters penalty; magic full at both.
   - New options: **Close in** (melee, at range), **Open distance**
     (any, close) — wired through `resolve_fight_action`.
   - Flee uses the speed curve (replaces flat 0.60).
   - Dodge roll before every incoming hit, physical and magic; the
     miss line names the dodge ("you slip the blow — speed tells").
3. Fight prose: range state named in every scene note ("it circles at
   distance" / "it is on top of you") — no numbers needed pre-003.
4. Content: audit floors 1–10 for slow/fast placement (first fast =
   floor 5 per the staircase).
5. Vendor sync + deploy; version bump + publish.

## Tests / acceptance

- Unit: every branch of the range machine (close-in, open-distance
  success/fail, p_close bounds, flee bounds, dodge cap).
- **Chase sim gate:** 10k-fight sims — measured close/flee/dodge rates
  within ±5% of formulas; archer-vs-slow kite wins ≥85% at level;
  archer-vs-fast forced close ≥80% by round 2; dodge never exceeds 12%.
- Regression: warrior floor-1 experience effectively unchanged (opens
  at range → close-in round is strictly additive flavor; sim asserts
  rounds-to-kill within +1 of today).
- Dojo: kite a slow bulwark as archer; get run down by a wolf; flee a
  slow monster successfully.

Exit: all green, published, worldd synced, `execution_summary.md`.
