# 035 — the plate pays too

## The report

> "I blocked a massive boar relentless attack, got 0 damage, and degraded
> the armour none."

Two separate faults sat behind one sentence.

**The deploy never happened.** `ascent-worldd` had been frozen on `0.45.1`
since Aug 2. The Render service says `autoDeploy: yes`, but every deploy in
its history carries `trigger: api` — the GitHub push webhook has never fired
for this repo, so `0.45.2` and `0.46.0` both sat on `main` unshipped. The
player was still on the code 034 was written to replace. Fixed out of band
(manual deploy + webhook repair); recorded here because it is why 034 read
as a no-op.

**Armour was never in scope, and that was the wrong call.** 034 §1 made the
shield spend itself on damage turned and deliberately left the plate at a
flat one use per blow, on the grounds that the repair-tax gate had no room.
The result is exactly what was reported: the piece that meets *every* blow
is the one that never visibly moves. A guard that costs the same for a chip
as for a Warden's full swing is not a running cost, it is a rounding error.

## The change

**Both guard pieces are billed by the damage they turn.** `shield_wear`
generalises to `guard_wear(blocked, bonus, total_def, rate)`; `armor_wear`
is the same function at the same rate. The algebra already cancels the
piece's own bonus —

```
wear = round(rate × (blocked × bonus / DEF) ÷ (bonus / 2))
     = round(rate × 2 × blocked / DEF)
```

— so the two slots wear identically per blow, which is the honest reading:
they met the same blow together. The `max(1, …)` floor stays, so a blow that
chips straight through still costs each piece its single point. Nothing
changes for weapon or boots: a swing is a swing, a stride is a stride.

## The recalibration

The gate is `test_repair_tax_stays_under_a_fifth_of_income_every_band`: a
warrior repairing the full kit daily spends ≤20% of that day's income at
every band, with no step-function between bands (|Δ| ≤ 0.10). The tax is
linear in wear events — pools are 1300–4225 and a day is 180 events, so the
`min(1.0, …)` saturation never engages and there is no free headroom.

Measured, at 30 fights × 6 rounds:

| rates | max frac | max step | |
|---|---|---|---|
| S3 A1 — 034, shipped | 0.161 | 0.090 | the baseline |
| S3 A3 @ 20% repair | 0.248 | 0.137 | fails both |
| S3 A3 @ 15% repair | 0.186 | 0.098 | passes, no margin |
| **S3 A3 @ 13% repair** | **0.161** | **0.085** | **chosen** |

`REPAIR_PRICE_PCT` drops `0.20 → 0.13`. This lands the daily bill on exactly
the 034 ceiling (0.161) and slightly *improves* the band step (0.085 vs
0.090) — the player's gold-per-day is unchanged, but the rhythm is not: the
bar now visibly empties, and each visit to the bench is cheaper. That is the
trade the report asked for. Growing pools instead was rejected — it would
have dragged the shield back *below* the pace 034 just gave it.

Life per piece at rate 3: a tier-1 buckler or jerkin runs ~2.4 hunting days
(was ~7 for the plate), a tier-10 piece ~7.8. No piece breaks inside a day
at any band.

## Touches

- `economy.ARMOR_WEAR_RATE` (new), `economy.guard_wear` (generalised from
  `shield_wear`), `economy.armor_wear`, `economy.REPAIR_PRICE_PCT`
- `combat._armor_wear`, `combat._monster_hit`
- `test_017_durability.py` — the gate now counts armour at its rate; the
  repair-price test restates 13%; the blow test asserts both guards scale
- `tests/test_035_the_plate_pays_too.py` — new

Shield Wall is untouched: it is the shield taking the whole blow, and the
plate has nothing to turn.

## Gates

1. Repair tax ≤20% of daily income at every band; no |Δ| > 0.10 step.
2. A heavy blow costs both guard pieces more than a light one; a chip still
   costs each of them exactly 1.
3. No piece breaks inside one hunting day at any band.
4. Full plugin + worldd suites green.
5. Live: deploy verified by `/health` reporting the new version.
