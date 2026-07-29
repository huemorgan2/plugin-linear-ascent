# 024 — The First Gate

## The complaint

> "who cares it's over 1000 — that's impossible for one player!"

Floor 1's shared Warden shows **1,064 HP** (1,032 after one closing). The
floor-1 solo Warden is 70 HP. The first gate in the game reads as a wall,
and for a lone climber it very nearly is one.

## What's actually wrong

Two separate mistunings, both from 022/002, both invisible on paper
because each was checked in isolation.

### 1. The pool ignores the floor inside the solo band

`world_warden_hp(F) = N(F) × 8 × strike_fight_damage(F)`, and `N(F) = 1`
for every floor up to 30. `8` is a flat constant written for the
coordination floors — so floor 1 asks the same **eight near-death
fights** as floor 30, against a body 15.2× its solo Warden's HP
(floor 30's ratio: 8.8×). The first gate anyone meets is the worst-tuned
point in the tower.

### 2. The wound heals faster than a body does

This is the real blocker. Pool regen is 2.78%/h — **29.6 HP/h at floor 1**
— and `warden_silence_hours(F)` is `None` in the solo band, so full regen
is the only closer. A 50%-open floor-1 wound closes in ~4.5 hours.

But a player's HP refills **only at dawn** (022/004). A strike-fight is
defined as fighting to one round from death and withdrawing. So a lone
climber's honest cadence is *one strike per day*, and the pool restores
~710 HP in that day. Solo net progress in the band is negative for
anyone who can't chain fights within hours — the exact opposite of what
`world_warden_regen_hourly`'s docstring claims ("in the solo band a
single sustained blade always gains", "a solo campaign can span
sessions").

The 8-fights-per-bar parity (25⚡ ÷ 3⚡ = 8 strikes = one pool) was the
design's proof that the band is soloable. It only holds for a player who
never needs to heal.

## The fix

Three changes in `economy.py` §5b, one in worldd, one in the keep card.

### A. Ramp the pool across the solo band

```
warden_pool_fights(F) = 8                        for F ≥ 30
                      = 2 + 6·(F−1)/29           below      (fractional)
pool_unit(F)          = max(strike_fight_damage(g) for g ≤ F)  for F ≤ 30
                      = strike_fight_damage(F)                 above
```

Floor 1 → 2 fights (**266 HP**), a straight line to 8 by floor 30. Two at
the bottom, not one, on purpose: you must come back to finish it, which
is how the shared-Warden mechanic teaches itself — you return and find
your own wound still open.

**Both pieces earn their shape** (found by auditing all 30 floors, not by
design):

- *Fractional, not whole, fights.* Rounding the ramp to integers put
  **+35–40% cliffs on floors 14, 17, 21 and 25** — a climber crossing
  one of those floors met a Warden nearly half again as deep as the last
  for no reason he could see. The effort curve is what he feels, and it
  must rise one honest step per floor.
- *A monotone unit.* `strike_fight_damage` rides integer round counts, so
  it can dip a floor: floor 3's pool came out **under** floor 2's (306 vs
  308), and floor 27 under floor 26. A tower may not step backwards on
  the way up. Deep floors keep the raw unit, where neighbouring pools are
  an order of magnitude apart and a dip cannot show.

The one large step left — **+40% at floor 8** — is the at-level reference
kit changing gear band, not the ramp. The effort curve runs straight
through it (3.24 → 3.45 fights), which is the number that matters.

Floors 30–100 are **numerically unchanged**: every acceptance gate in
022/002 (deep-band solo impossibility, the banked-bar burst, the era
length) reads floors ≥ 31 only.

### B. The solo band's healer is silence, not a trickle

- `world_warden_regen_hourly(F) = 0` for F ≤ 30.
- `warden_silence_hours(F) = 30.0` for F ≤ 30 (was `None`).

A wound now survives **a day and a night** — long enough for the climber
to heal at dawn and come back — but a tower that forgets a Warden for a
full day finds it whole, and pays the 3% pity for it. Deep floors keep
today's trickle and their 6→30h window exactly.

### C. Pay tracks the work

`world_warden_reward_mult` must read `warden_pool_fights(F)`, not the
flat 8 — otherwise floor 1 pays 8 pools for 2 fights of work. The
docstring's parity ("payout per energy at parity with the solo-tuned
warden") holds by construction again.

### D. Live pools resize on read

Stored rows freeze `hp_max` (022/002), so production's floor-1 Warden
would keep its 1,032 forever. Add `WARDEN_POOL_TUNE`; `_warden_now`
resizes any row stamped with an older tune, **keeping the wound's depth
as a fraction** — nobody's strikes are erased, they just cut a smaller
body. Writes stamp the current tune. No row is deleted, no data lost.

### E. Say how many fights are left

The card shows `1,032/1,032 HP` and nothing about the eight-visit
structure, which is why it reads as hopeless. Add a line — `≈2 full
fights left to close` — and an `[i]` on `Join the fight` explaining that
damage persists, that withdrawing still counts, and that the wound
closes if the tower forgets it.

## Acceptance

- Floor 1's pool is 266 HP: two at-level fights, 6⚡, and ≤ one energy bar.
- The ramp is monotonic, reaches 8 at floor 30, and floors 31–100 keep
  today's exact numbers (asserted against the old formula).
- **No floor in 1–30 is weaker than the floor below it**, and the effort
  curve is a straight 2 → 8 fights with no step worth a whole fight.
- Solo band: regen is 0, silence > 24h — a wound survives the dawn a
  climber needs.
- Reward per energy at floor 1 matches the solo-tuned Warden.
- A legacy warden row (old `hp_max`, no tune stamp) resizes on read with
  its wound fraction intact, and the next strike stamps the new tune.
- The keep card states the fights left and carries an `[i]`.
- Both suites green; every 022 acceptance gate still passes untouched.
