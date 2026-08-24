# 077 — Execution summary

Executed 2026-08-24 (roy), immediately after 075 landed. Shipped as
**0.101.0** on `main`. All three phases in one pass.

## What shipped

### The glance (economy.py)
- `GLANCE_MULT = 0.015` and both glance cells follow it:
  bow-vs-armoured and staff-vs-magic_resist go `0.15 → 0.015`.
- Glance cells lose the `max(1)` chip floor — a glance may do
  **nothing at all**. Half and full cells keep the ≥1 chip law; the
  single legal zero stays blade-vs-fly.
- The value was sim-fitted, not guessed: the plan opened at 0.04, but
  the staff ignores DEF so a sorcerer still ground out 20–47% of
  glance wins across level bands; 0.02 left 7% at +2 levels; 0.015
  stalls every band. A kitted at-level glance hit still shows a 1–2
  scratch — futility, not a bug.

### The steering line (combat.py)
`_steer_wrong_weapon()` — after **2** wasted attack rounds on a
glance/zero matchup the fight card says it plainly:
- bow: "Your arrows barely mark its plate. Use a blade or magic — or run."
- staff: "Your spells slide off it. Use a blade or a bow — or run."
- blade (vs a flyer): "Your blade cannot reach it. Use a bow or magic — or run."
A piercing arrow resets the counter (it is a real answer to plate —
the archer's designed out, existing 006 rule, untouched). The counter
lives on the transient encounter dict; no state migration.

### Copy (render.py)
- Armoured: "heavy plate. A blade cuts at half strength, arrows all
  but bounce off, magic goes through in full."
- Magic-resist: "spells barely scratch it. A blade cuts in full,
  arrows at half strength."
All other surfaces (dossier answer words, "MR n%", strike prose) are
multiplier-driven and followed the new value with no edits —
`answer_word(0.015)` already reads "glance", 0-damage strikes already
say "glances off … nothing lands".

### What was deliberately NOT built
No monster-ATK crank (the first draft's "Lever B"). 075's pursuit is
the damage engine that makes a stall cost blood, and there is no
"reachable glance" to crank — both glance cells sit on slow (speed 3)
tanks, and the fast wrong-matchup (blade-vs-fly) is a true zero where
fleeing is the only end. Verified by gate instead of built twice.

## The grid flipped (sim077.py — 10,800 fights, real engine)

Floor 6, 300 fights/cell, kitted players at levels −2/at/+2, post-075
policy (shoot in place, step out when caught), no healing, no fleeing,
80-round cap. win% / death% [avg rounds on win]:

```
matchup                          L-2            at-level        L+2
blade vs fly        (x0)       0%w 100%d      0%w 100%d      0%w 100%d
blade vs armoured   (x0.5)    69%w  31%d     82%w  18%d     92%w   8%d
blade vs mag_resist (x1)     100%w   0%d    100%w   0%d    100%w   0%d
bow   vs fly        (x1)     100%w   0%d    100%w   0%d    100%w   0%d
bow   vs armoured   (x0.015)   0%w   0%d      0%w   0%d      0%w   0%d
bow   vs mag_resist (x0.5)   100%w   0%d    100%w   0%d    100%w   0%d
staff vs fly        (x0.6)   100%w   0%d    100%w   0%d    100%w   0%d
staff vs armoured   (x1)     100%w   0%d    100%w   0%d    100%w   0%d
staff vs mag_resist (x0.015)   0%w   0%d      0%w   0%d      0%w   0%d
(plain: 100% win for all three classes at every level)
```

All six acceptance gates PASS:
- right weapon at-level ≥90% win ✓ (all 100%)
- glance cells ≤5% win at-level ✓ and at +2 ✓ (all 0% — brute force
  does not clear a glance)
- zero cell 0% win at every level ✓
- half cells at +2 ≥90% ✓ (92–100%)
- right-weapon at-level death ≤5% ✓ (0%)

Compare the pre-075/pre-077 baseline in the PLAN: every weapon beat
every type ≥90%, even 2 levels under. The texture roy asked for is
now visible in one row: **blade vs armoured** (a half cell) reads
69% → 82% → 92% by level — at your edge you pick right or you bleed;
a +2 cushion buys comfort, never a free glance.

Notes on how a "loss" looks per cell:
- **bow-vs-armoured**: a stall — the archer outpaces the speed-3 tank,
  so nobody dies in 80 rounds; the fight simply cannot be won. In real
  play that is a flee (or piercing arrows). The steering line names it
  by round 2.
- **staff-vs-magic_resist**: same stall; the sorcerer escapes when
  caught.
- **blade-vs-fly**: the no-flee sim policy is suicidal on purpose —
  100% death for the stubborn. The flyer cannot be hurt or escaped-from
  by standing there; fleeing is the designed end.

## Regressions checked
- Full pytest: **1362 passed** — the same 4 failures as before 077
  (3× `test_kill3d`, 1× clazz-gate), all pre-existing on main or from
  the concurrent kill3d/avatar work; none from 077.
- sim039 (150/class): floor-by-floor EV and death rates are
  numerically identical to the post-075 run (normal death <2% floors
  1–3, ≤8% everywhere ✓). The glance change does not move hunt
  economics: the sane policy already ran at the card when the opener
  read hopeless. The 6 pre-existing acceptance drifts (EV curve +
  deep bands, present in the pre-075 baseline too) remain — filed as
  economy re-tune follow-up, not caused here.

## Tests
- New `tests/test_077_triangle.py` — 6 tests: glance value +
  floorlessness, glance-cannot-grind math at-level and +2, steering
  line fires on round 2 for all three weapons, never for the right
  weapon, piercing arrows reset the stall.
- Updated pins: `test_048_the_weapon_decides.py` (table cells, glance
  damage values, focus math), `test_017_damage_types.py` (glance rows;
  "everything chips ≥1" is now "half/full chip ≥1 — glances are
  exempt", which is the point of the plan).

## Follow-ups
- **Dojo browser walkthrough covering 075+077 together** (bow an
  armoured monster: futility + steering + bleed + flee; sword a flyer;
  right-weapon wins) — required before calling the pair
  player-verified.
- Deep-hunt floors 9–10 death (29.3% vs the old 26% cap, inherited
  from 075) and the older EV-curve drift — one economy re-tune plan.
- No deploy (per plan: not unless roy says so).
