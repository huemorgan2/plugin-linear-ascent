# 039 — the climb pays (higher floors must be higher)

## Problem

Player report (2026-08-08, playing at floor 6): *"we wanted variance but now
in level 6 I'm hunting animals that can give me the same gold as level 1.
This is not the variance needed. Higher levels should be higher — with
variance that some may kill you — and give bigger gains."*

The numbers agree. Evidence, measured on 0.51.1 HEAD:

- `gold_per_kill(floor) = 8·floor·1.2^(tier−1)` and floors 1–10 are all
  band 1, so floor 6's base is 48 vs floor 1's 8 — the *base* scales.
  What doesn't scale is the **mix**:
- Floor 6's roster weights 5/12 of all draws to `frail+feeble` prey
  (grave moth 3, guano vole 2). A feeble+frail kill pays threat mult
  `0.45 × 0.6 = 0.27` → 48 × 0.27 ≈ **13 gold**. The 25%-likely runt
  specimen multiplies gold by 0.45 → ≈ **6 gold, below a floor-1 common
  wolf (8)**. One energy either way.
- Danger exists in content (`lean+savage` vault weaver) but the 025 §5
  rubber band cuts any probably-lethal draw to **20% weight at every
  floor** — the tower protects a floor-6 climber exactly as tenderly as a
  floor-1 one — and `REWARD_MULT_CAP = 6.0` is flat, so the upside never
  grows either.
- Hunting is a flat `⚡1` everywhere. There is no way to *choose* danger.

So the climb flattens: floors change costume, but the hunt's
risk/reward distribution barely moves. Variance today is mostly
**downward** (prey and runts drag the pay toward floor-1 money) while the
upward tail is rubber-banded and capped.

## Root cause

025 built the archetype range (right) but tuned its knobs as **constants**
(wrong): prey share, runt share, rubber-band cut, and reward cap are all
floor-independent. The floor number raises the baseline creature, not the
*shape* of the draw. And 004's energy model prices every fight at 1 ⚡, so
the player can never trade energy for risk.

## The fun being bought

The game's core read is already on the card: the opener names the body,
the bite, and the specimen before you commit, and running is legal. What's
missing is a reason to *care* about the read. This plan makes altitude
mean something:

- **Floors 1–3 are the nursery.** Prey is common, the rubber band is
  tight, death is nearly impossible. Learn the read cheaply.
- **From floor 4 the tower stops apologizing.** Prey thins out (the easy
  meat has been hunted), runts get rarer, lethal draws stay in the deck at
  real weight, and the reward ceiling climbs. The read starts deciding
  whether you walk home.
- **The deep hunt is the danger dial.** From floor 4, spend ⚡2 to leave
  the lit paths on purpose: no prey, no rubber band, primed opponents —
  harder in ATK and SPEED, *not* HP (fights must get scarier, not
  longer) — and pay that clearly beats the safe path per energy… while
  you live.

## Fix, in phases

- **Phase 1 — the floor shapes the draw** (economy.py + hunt_table):
  prey fade, runt fade, floor-laddered rubber band, floor-laddered reward
  cap. Content yamls untouched, still numberless.
- **Phase 2 — the deep hunt** (⚡2, floor 4+): new gate-town option, prey
  and rubber band excluded, prime modifier (ATK/speed up, HP flat),
  specimen table without runts, pay premium.
- **Phase 3 — calibration**: extend the 017 fight sim with per-floor EV
  and death-rate tables for both hunts; retune the 004 acceptance gate
  (its targets are stale — it already fails on untouched HEAD) and set
  the new targets from the sim, then make the gate green.
- **Phase 4 — ship**: version bump, tests, vendor into worldd, deploy,
  dojo walkthrough, results archive.

## Verification (whole plan)

- Sim (phase 3) proves, per floor 1–10 at at-level loadouts:
  - normal-hunt EV(gold/⚡) strictly increases with floor, and floor 6 EV
    ≥ 2.5× floor 1 (today ≈ flat-to-noisy);
  - a floor-6 kill's 10th-percentile pay > a floor-1 median kill (no more
    "floor-1 money at floor 6");
  - deep-hunt per-⚡ EV 1.25–1.4× normal on the same floor, with an
    at-level kitted death rate ≈ 8–15% per fight (dangerous, not
    suicidal); normal-hunt death rate < 2% on floors 1–3.
- Dojo scenario (dojo/01-the-climb-pays.md) walks a real browser session
  on both hunts and checks option gating, energy costs, prime opener
  copy, and that pay on floor 6 visibly beats floor 1.

## Operational notes

- **Coordination**: the parallel session owns 038 (mercy revamp,
  combat.py + floor yamls, in flight). 039 changes economy.py knobs,
  hunt_table, and the option surface — overlap is `combat.py`
  (hunt_table, start_encounter) only. Rebase on their latest committed
  main before each phase; use 038's mercy vocabulary in any new
  user-facing copy (a "kill" is a cure/freeing now).
- **Rollback**: every phase is a plain revert of its commit; no
  migrations, no state-shape changes. Deployed rollback = redeploy prior
  vendor SHA per the 006 ritual.
- All numbers below are **opening bids** — phase 3's sim owns the final
  values; the plan commits the shape, not the digits.

## Execution status

**Complete** — all 4 phases executed and deployed 2026-08-08. Phase
commits `9d49612` (floor-shaped draw), `1a36a1e` (deep hunt),
`27220c0` (calibration — deep ladder {4:1.3, 5:1.6, 6:1.9, 7:2.8,
8:2.8, 9:3.0, 10:3.4}, gates repinned, sim039 PASS at N=600),
`aac7330` (0.52.0). Live on production (deploy
`dep-d9rg9tegekts739q8hhg`, /health game 0.52.0). Production dojo
walkthrough 13/13 PASS —
`dojo/results/039-the-climb-pays-2026-08-08/` in the outer repo, one
documented deviation (no at-level floor-6 account; sim + unit tests
cover those claims). Per-phase details in each phase PLAN.md.
