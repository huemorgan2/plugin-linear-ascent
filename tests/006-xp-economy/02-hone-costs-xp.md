# Scenario 02 — Honing charges gold AND experience

## Setup
Character past a couple of floor-1/2 fights with some gold and some XP
banked in the pool. Frontier at floor ≥ 2 (so the honing bench is open:
hone cap = unlocked_floor − band start).

## Steps
1. Go to the Forge with hone available (unlocked_floor ≥ 2), note the meter
   rail values (◈ and ✦).
2. Read the hone option hint.
   - **Expect:** hint shows **both** prices, e.g. `◈ 9 + ✦ 12`
     (✦ = half a frontier kill's XP).
3. Buy one hone pass.
   - **Expect:** confirmation line; gold down by the ◈ price AND the ✦
     meter down by the ✦ price. Level unchanged.
4. Drain the pool (hone repeatedly or spend otherwise) until XP < hone cost,
   then try to hone again.
   - **Expect:** refusal with a shard note quoting the ✦ shortfall.
     Gold NOT charged. Level and pool unchanged (pool never negative).
5. Fight one more wilds fight and check the pool grows again.

## Pass
Both currencies charged together; refusal is atomic (neither charged);
pool floors at 0; level never moves from spending.
