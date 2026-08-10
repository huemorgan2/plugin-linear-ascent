# 046 — the test plan (prove the climb, floor by floor)

Companion to plan.md. The five failure modes Roy named become five
measurable gates, run against a SIMULATED climb of the whole tower by
different player personas. Every gate failure emits a structured issue
(floor, persona, metric, value vs bound) — the list Roy reads to fix
fundamentals, not a pass/fail smoke.

## The simulator (tools/sim046.py)

One headless player-day loop over the REAL economy functions — no HTTP,
no engine state machine, no LLM. A persona is a policy over the real
action menu; a day is energy-budget accounting; a fight is the
gen_mechanics Monte-Carlo model (same one that already mirrors
engine/combat.py). Deterministic seed per (persona, run).

Simulated per day: energy spent (fights / warden strikes / deep hunts),
gold and XP earned (kills, jobs, night work, interest), purchases
(rungs, hones, training, sleep), floor attempts. Recorded per floor:
days-on-floor, gold flow by source, power deltas, action mix, win% at
entry and exit.

Personas (minimum set — each exists to reach a different failure area):

| persona | policy | designed to expose |
|---|---|---|
| optimal | spends every ⚡, buys best power/gold first | the intended pace curve (baseline) |
| casual | 30 min/day: ~1/3 of ⚡, sleeps in fields | pace cliffs felt hardest, rut depth |
| skinflint | never buys until forced by a wall | weapon-starvation recovery (issue 1) |
| hoarder | banks gold, buys whole tiers late | interest-vs-climb exploit, cliff jumps |
| sprinter | rushes gates at minimum win%, dies often | death spiral, stuck-with-no-ladder |
| jobber | prefers tavern jobs/night work over fights | significance of non-combat income (issue 4) |
| off-class | archer/sorcerer policies vs ground/flying mix | class-conditional walls |

Runs: 100 floors × 7 personas × 3 seeds ≈ minutes of wall-clock (pure
arithmetic + cached Monte-Carlo win tables). Output: one JSONL of
per-floor records + a rendered report table; pytest gates read the
JSONL.

## Gate 1 — always a rung to buy (weapon starvation)

*"No weapon progression capability if they get stuck on the floor."*

- **G1a ladder-never-empty**: for every floor F and every simulated
  stuck state (win% at next gate < 60%), there exists a purchasable
  power step (rung, mid-rung, hone, training) priced ≤ 3 days of
  at-floor income. Assert for all 100 floors × personas.
- **G1b the step works**: buying that step raises next-gate win% by a
  measurable amount (≥ 2pp) — a ladder of placebo steps fails the gate.
- **G1c stuck-state escape time**: from the skinflint/sprinter's worst
  recorded state per floor, days-to-unstuck ≤ 2 × the floor's design
  days. No state may exist where the shop, hone and training are all
  exhausted while the gate is still < 85% winnable (that is a hard
  dead-end — file as CRITICAL).

## Gate 2 — the rut detector (days of nothing but grinding)

*"A massive routine of killing monsters and gathering coin for days."*

- **Rut metric**: consecutive days where > 85% of spent ⚡ goes to the
  same action type AND no progression event fires (no purchase, no
  level, no gate attempt, no unlock, no story beat).
- **G2a**: max rut length ≤ 2 days for optimal/casual on every floor
  1–30; ≤ 3 days on 31–100 (the discount makes floors longer — length
  must be filled with CHOICE, not repetition).
- **G2b menu breadth**: on every floor, count distinct meaningful
  actions actually taken by the optimal persona across its stay
  (fight / deep hunt / warden strike / job / hone / train / faction /
  story). Assert ≥ 4 distinct types on every floor's action mix.
- **G2c**: report (don't gate) the "texture calendar": for each decile
  of the climb, the % of days containing anything besides
  kill-and-collect. This table goes to Roy — if deep floors read 95%
  grind, that's a content gap (fundamental, not tunable).

## Gate 3 — no step functions (the 30% promise)

*"Unable to progress without an irregular investment — a cliff, not
×1.3."*

- **G3a pace smoothness**: days-on-floor(F+1) ÷ days-on-floor(F) for
  the optimal persona ∈ [0.9, 1.25] for every F (target ×1.04; the
  band tolerates Monte-Carlo noise). Any floor > 1.25 = a cliff issue
  with its cause attached (price jump / win% wall / XP wall).
- **G3b band seams**: explicitly test floors 10→11, 20→21, …, 90→91
  (tier boundaries, where the old ×13.8 price step hides) and 30→31
  (level cap + first regen wall) and 21 (warden tier profiles). The
  mid-rung ladder must smooth every seam to the same [0.9, 1.25] band.
- **G3c marginal-power price**: cost of +1pp win chance at the next
  gate, as days of income, must be monotone-smooth in F (no floor
  where the only remaining step costs 5× the previous floor's step).
- **G3d win% continuity**: kill-bar Monte-Carlo — at-bar win% on every
  floor ∈ [85, 95]; bar−1 win% ∈ [55, 80]. A floor where bar−1
  collapses to 20% is a wall even if at-bar holds.

## Gate 4 — everything stays significant

*"Jobs add nothing; kills don't get you there; the next weapon isn't
worth the work."*

Everything is asserted as a SHARE of the player's current economy —
shares are scale-free, so these gates hold at floor 3 and floor 93
alike or they fail loudly:

- **G4a jobs matter**: tavern job / night work payout ∈ [20%, 60%] of
  a day's at-floor fight income, every floor. (Under the pace discount
  both must ride `income(bar)` — a forgotten linear job table fails
  this gate immediately at depth.)
- **G4b kills fund the climb**: at-frontier kill income alone must
  fund the floor's design progression (next steps affordable within
  the pace-law days) — if a persona must farm 10 floors down or bank
  interest to advance, fail.
- **G4c the next weapon is felt**: every rung/mid-rung purchase = +X%
  player ATK with X ∈ [4%, 15%] at every floor (rounding erosion at
  huge numbers can silently shrink steps — assert the RATIO, not the
  int). Same for hone steps ≥ 1%.
- **G4d nothing pays dust**: no reward surface (specimen bonus, deep
  hunt, strongbox, flare, warden pay, interest) falls below 5% of its
  floor's daily income — below that it reads as an insult and should
  either scale or be retired. Report each surface's share-by-floor
  curve.

## Gate 5 — the disbelief audit (flag, don't fix)

*"A tavern job paying trillions of coins breaks the world."*

Not a numeric gate — an AUDIT with a completeness test:

- **G5a the ledger of fictions**: enumerate every gold- or
  XP-denominated surface the player SEES (job flavor text, sleep
  price, mend, ferry, faction dues, training fee, shop prices, warden
  bounty). For each: its floor-1, floor-50, floor-100 value and a
  world-logic verdict {holds / strains / breaks} with one line of
  why. The pytest gate asserts every surface in the codebase appears
  in the audit table (grep-driven completeness — an unreviewed new
  surface fails CI), not that the fiction holds.
- **G5b known breaks to log now** (pre-seeded verdicts for Roy):
  - Tavern jobs: a barkeep paying ◈2T for a night's washing-up =
    BREAKS. Candidate fictions (Roy's call): jobs become Guild
    contracts priced per floor; or pay in scrip/letters-of-credit; or
    a currency re-denomination each band (copper→silver→…), pure
    display.
  - Sleep price: STRAINS (accepted by Roy — "that is fine"); indicate
    in flavor ("beds this high cost what they cost").
  - Bank interest on exponential balances: STRAINS mechanically (see
    plan.md interest audit), holds fictionally.
  - Monster anatomy: a floor-90 moth with 400B HP — holds only if
    bestiary copy never states physical comparisons; audit copy.
- **G5c denomination check**: if Roy picks re-denomination, the
  formatter (K/M/B/T) is replaced by currency tiers — the audit
  carries a mock of both so the choice is made once, seen twice.

## Issue pipeline (so Roy can fix fundamentals)

Every gate failure appends to `plans/046-thirty-percent-a-floor/
issues.md`: `[gate] floor F, persona P: metric=value (bound), cause
hypothesis, tunable-vs-fundamental`. Tunable = a constant in
economy.py fixes it (κ probe, price, cap). Fundamental = needs design
(content gap at depth, fiction break, missing mechanic) — these are
Roy's queue, raised, never auto-fixed.

## What is deliberately NOT simulated

Multiplayer sieges (the recup wall is already proven by algebra +
projection in plan.md — a population simulator is a separate effort if
ever needed), PvP, factions' social layer, real LLM story beats. The
simulator's story/faction actions are stubs that only consume time and
pay their listed rewards — enough for rut/significance math, nothing
more.

## Execution order

1. Build `tools/sim046.py` + persona policies; verify optimal persona
   reproduces plan.md's pace table (the simulator is itself under
   test: total climb within 20% of the chosen PACE_DISCOUNT row).
2. Wire gates G1–G4 as `tests/test_046_balance_sim.py` (slow-marked;
   runs on demand and pre-release, not every CI pass).
3. Write the G5 audit generator + completeness gate
   (`tests/test_046_disbelief_audit.py`).
4. Run the full matrix, produce `issues.md`, hand the fundamental pile
   to Roy; tune the tunables; re-run to green.
5. Regenerate /mechanics; the sim's per-floor table joins it as an
   unlinked page (the same ledger Roy already reads).
