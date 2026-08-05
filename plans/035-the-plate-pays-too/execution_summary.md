# 035 — execution summary

Shipped as `0.47.0`. Live on `ascent-worldd` (`/health` → `"game":"0.47.0"`).

## What the report actually contained

> "did u deploy the change that degrades the armour relatively to the attack
> it blocks. cuz right now i blocked a massive boar relentless attack got 0
> damage and degraded the armour non"

Three separate truths, and only the third was a design question.

**1. It was not deployed.** `ascent-worldd` had been serving `0.45.1` since
Aug 2. `autoDeploy` reads `yes` and `autoDeployTrigger` reads `commit`, the
repo and branch are correct — but every deploy in the service's history
carries `trigger: api`, and `GET /repos/huemorgan2/luna-linear-ascent/hooks`
returns an empty list. GitHub has never notified Render for this repo. So
`0.45.2` and `0.46.0` both sat on `main` unshipped and the player was still
running the code 034 was written to replace. See "the deploy pipeline".

**2. The zero-degradation reading was correct, and it was Shield Wall.** On
`0.45.1` the `shield_wall` branch had no `_wear` call in it at all — a
perfect block that cost the shield nothing, every time. 034 fixed exactly
that. Reproduced on `0.47.0`: shield wall now spends 6 uses and still takes
no damage.

**3. Armour was out of 034's scope, and that was the wrong call.** 034 §1
left the plate at a flat point per blow because the repair-tax gate had no
headroom. The consequence is the one reported: the piece that meets *every*
blow was the only one that never moved.

## The change

`economy.shield_wear` generalises to `guard_wear(blocked, bonus, total_def,
rate)`, with `shield_wear` and `armor_wear` as named wrappers at
`SHIELD_WEAR_RATE` and the new `ARMOR_WEAR_RATE` (both 3). The piece's own
bonus cancels out of the algebra —

```
wear = round(rate × (blocked × bonus / DEF) ÷ (bonus / 2))
     = round(rate × 2 × blocked / DEF)
```

— so shield and plate spend the same on a blow they met together, which is
the honest reading. The `max(1, …)` floor survives: a blow that chips
straight through still costs each piece exactly one point.

Shield Wall deliberately stays shield-only — the shield took the whole blow
and the plate had nothing to turn. Verified by test.

## The recalibration

`REPAIR_PRICE_PCT` 0.20 → 0.13. The tax is linear in wear events (pools are
1300–4225 against ~180 rounds a day, so the `min(1.0, …)` saturation never
engages) and the gate was already near-saturated, so tripling the plate's
event count had to be paid for on the price side.

| rates | max frac | max step |
|---|---|---|
| S3 A1 @ 20% — 034, shipped | 0.161 | 0.090 |
| S3 A3 @ 20% | 0.248 | 0.137 |
| S3 A3 @ 15% | 0.186 | 0.098 |
| **S3 A3 @ 13% — chosen** | **0.161** | **0.085** |

Same gold a day, a cheaper bench visit far more often, and a bar that moves
where the player can see it. Growing pools instead was rejected: it would
have dragged the shield back below the pace 034 had just given it.

## Verified against the real engine, not just the model

Simulated play at every band (30 resolved fights per band, attack loop):

| tier | rounds/fight | guard uses/round |
|---|---|---|
| 1 | 3.5 | 0.73 |
| 5 | 8.4 | 2.31 |
| 8 | 6.9 | 2.39 |
| 10 | 14.5 | 2.69 |

Measured per-round guard wear lands **below** the 3.0 the gate test models
at every band, so the coded gate is conservative rather than optimistic.

Recomputing the daily bill from these measured numbers instead of the
6-round anchor, 035 is cheaper than 034 at every band:

| tier | 034 (flat plate, 20%) | 035 (billed plate, 13%) |
|---|---|---|
| 1 | 0.042 | 0.032 |
| 5 | 0.134 | 0.121 |
| 8 | 0.153 | 0.140 |
| 10 | 0.374 | 0.358 |

### Known, pre-existing, out of scope

Tier 10 measures 0.358 of daily income — over the 20% gate. This is **not**
035: the same measurement puts 034 at 0.374, and the cause is that deep
fights run ~14.5 rounds where `daily_income` and the gate test both anchor
on 6. The gate test passes because it uses the 6-round anchor. Either the
anchor or `daily_income` needs revisiting for the deep bands; that is a
plan of its own. 035 moves the number in the right direction.

Reproduced scenario on `0.47.0`, tier-1 warrior with buckler and jerkin:

| blow | plate spends |
|---|---|
| graze (DEF/8) | 1 |
| even blow (DEF/2) | 3 |
| full swing (DEF) | 6 |
| Warden swing (3×DEF) | 18 |

Full repair on a padded jerkin: ◈26, was ◈40.

## Tests

- `tests/test_035_the_plate_pays_too.py` — new (14)
- `tests/test_017_durability.py` — the gate counts armour at its rate; the
  repair-price test restates 13%; the mid-day-break gate is now measured in
  guard events rather than rounds; the blow test asserts both guards scale
- Plugin suite: **874 passed**, 1 pre-existing failure
  (`test_026::test_a_caught_getaway_costs_real_blood_not_a_chip`, verified
  failing identically at `HEAD` before these changes)
- worldd suite: **119 passed**

## The deploy pipeline

Root cause: the repo has no webhook and Render's GitHub App evidently does
not have access to `huemorgan2/luna-linear-ascent`, so no push has ever
reached Render. Render's own configuration is correct and needs no change.

Deploys for `0.46.0` and `0.47.0` were triggered through the Render API
(`POST /v1/services/srv-d9ha3csvikkc73ff5rg0/deploys`), which works and is
the interim path. The durable fix needs one browser action — either
reconnecting the repo on the service in the Render dashboard, or granting
the Render GitHub App access to this repo under GitHub → Settings →
Applications. Neither is scriptable from here (the Render dashboard and
GitHub are both unauthenticated in this browser, and an OAuth token cannot
list or modify App installations).

A GitHub Actions fallback that calls a service-scoped Render deploy hook on
push to `main` is the alternative; it needs the hook URL, which is only
visible in the dashboard.
