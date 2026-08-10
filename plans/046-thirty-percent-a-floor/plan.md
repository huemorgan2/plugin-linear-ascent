# 046 — thirty percent a floor (the exponential tower)

## Problem

Designer verdict (2026-08-10, reading /mechanics): *"the monsters'
difficulty did not increase dramatically. We need a 30% increase of
difficulty every floor — exponential: 1, 1.3, 1.3², 1.3³ … Difficulty
is HP vs attack, damage, speed. And it has to match the level
progression and the weapons power progression."*

Why the tower reads flat: 043 anchored every monster to the reference
player's loadout — correct relatively, but the backbone itself is
LINEAR:

- `player_atk = 3·level + weapon`, weapon ladder `30·T − 22`
- `DEF = 3·bar`, warden HP base `12·F + 25`, monster ATK solved from
  a linear HP pool

So floor 100 is only ~30× floor 1 in raw stats. The designer wants
`1.3^99 ≈ 1.9 × 10¹¹`. The *relative* machinery of 043 (bars, kill-bar
Monte Carlo, body/bite shares, κ) is right and stays; the *scale* it
multiplies must become exponential.

## The rule being bought

One master law — the **pillar exponential growth** — stated once, and
every other growth constant defined RELATIVE to it:

```
PILLAR = 1.3                    # the pillar exponential growth
pillar(B) = PILLAR ** (B - 1)   # B = bar/floor/level, 1-indexed
```

| param | default | growth/floor | governs |
|---|---|---|---|
| `PILLAR` | 1.3 | ×1.30 | monster & player stats, gear, prices |
| `PACE_DISCOUNT` | 1.04 | ×(1.3∕1.04) ≈ ×1.25 | all income + xp/kill — discounted OFF the pillar so days-per-floor grow ×1.04 |
| `WARDEN_RISE` | 1.02 | ×(1.3·1.02) ≈ ×1.33 | warden threat — added ON TOP of the pillar so gates outgrow their floor's monsters |
| `WARDEN_RECUP` | R100(A)^(1∕70) | ×1.06–1.07 | the recuperation wall past floor 30 — growth of the striker quorum the regen enforces; DERIVED from the weekly-active census A, anchored so floor 100 = 10% of actives in one day |

Every power-bearing stat is `(its floor-1 anchor) × pillar(B)`,
rounded. Floor 1 keeps today's exact numbers — the first hour is
untouched.

- **Per-stat, not per-composite.** Monster HP ×1.3/floor AND monster
  ATK ×1.3/floor (DEF, player ATK/DEF/HP, gear the same). The
  /mechanics columns must visibly step ×1.3 — that is the deliverable
  the designer will read. (Effective fight "power" HP×DMG therefore
  grows ×1.69/floor; irrelevant to feel, because the player grows by
  the same law.)
- **Speed stays on the 1–10 scale.** Dodge/gap/flee are ratio-based
  and scale-free; speed remains the texture axis (profiles, alphas,
  shoes), not part of the exponential.
- **Relative balance is preserved by construction.** If every stat on
  both sides carries the same `pillar(B)`, the 043 fight math (uniform
  rolls, `raw − DEF/2`, chip `raw/4`, pool shares κ, body/bite,
  WARDEN_DMG_BUDGET) is homogeneous — win rates and rounds-to-kill are
  unchanged. Kill bar B on floor B stays ~90%, verified, not assumed.

Reference multipliers: F5 ×2.9 · F10 ×10.6 · F20 ×146 · F30 ×2 015 ·
F50 ×3.8×10⁵ · F70 ×7.3×10⁷ · F100 ×1.9×10¹¹.

## Mechanism

### 1. The player backbone (economy.py §2)

- `player_atk(L, w) = round(3 · pillar(min(L, cap))) + w`
- `player_def` likewise: `round(2 · pillar(L)) + shield + armor`
- `player_max_hp = round(52 · pillar(L)) + GEAR_HP_PER_ARMOR · armor`
  (anchored so L1 unkitted = 52 HP and floor-1 kitted = 80, exactly
  today)
- Levels ≈ floors below the cap, so a level is worth ×1.3 — level
  progression matches the tower by construction. Past 30 the level
  term freezes and steel alone climbs (unchanged 043 doctrine; monsters
  derive from `_at_level_loadout`, which includes the frozen term, so
  the match is automatic).

### 2. The weapons power progression (§6, _FORGE_ROWS)

- Reference weapon at floor F: `8 · pillar(F)` (floor-1 Pigsticker = 8,
  today's anchor). Shields anchor at 5, armor at 7.
- Tier T's base bonus = the law read at the band start:
  `weapon(T) = round(8 · pillar(band_start(T)))` — the tier step becomes
  ×1.3¹⁰ ≈ ×13.8 instead of +30. `_FORGE_ROWS` bonuses are regenerated
  from the law (names, flavor, mid-rungs, styles untouched).
- `_step_bonus` (band-1 rungs) becomes GEOMETRIC interpolation, so each
  rung is ×1.3^(1/1) per floor-step, not a linear slice.
- Honing becomes multiplicative: hone +1 ≈ +9% per step per weight
  point (calibrated so `reference_hone`'s 2-floor lag costs the same
  relative edge as today), replacing flat `HONE_WEIGHT × hone`.
  Simplest form: `bonus × (1.3 ** (hone_floors × slot_share))` — exact
  constants solved in implementation so the bar-B loadout lands on
  `8 · pillar(B)`.

### 3. Monsters and wardens (§3, §5)

- Derived stats (wilds HP from player damage × rounds, ATK from
  κ-share of the reference pool) inherit the exponential automatically
  once §1–2 land. No change to κ, BODY_ROUNDS, BITE_COST,
  WILDS_ROUND_CAP, rubber band — all are shares, scale-free.
- Explicit linear laws converted:
  - `DEF = 3·bar` → `round(3 · pillar(bar))`
  - Legacy `monster_stats` / `MONSTER_ATK_SLOPE` (only
    content/schema.py:214 still reads it) — re-derive or delete.
- **The warden rise.** Wardens grow at `PILLAR × WARDEN_RISE` — the
  rise multiplies onto the monster exponent, so a gate pulls away from
  its own floor's wilds by ×1.02 per floor, compounding:
  - `_boss_hp_base = 12·F + 25` →
    `round(37 · pillar(F) · WARDEN_RISE ** (F - 1))` — the wall
    thickens exponentially against your kill speed. Relative premium
    over today's `WARDEN_HP_MULT`: ×1.2 at F10, ×1.8 at F30, ×7.1 at
    F100.
  - ATK stays SHARE-based (`WARDEN_DMG_BUDGET` of the reference pool):
    a strike remains survivable at every floor, so the strike-fight
    unit — and solo gates on floors 1–30 — keep working; the rise is
    paid in strikes/time, not in unwinnable fights. A second knob
    `WARDEN_RISE_ATK` (default 1.0) exists if lethality should climb
    too — raising it erodes solo viability below floor 30, so it
    stays 1.0 in this plan.
  - Warden gold/xp ride the income law × `WARDEN_RISE^(F−1)` — the
    longer gate pays for its extra time.
  - Retire `WARDEN_HP_RAMP` / `WARDEN_ATK_RAMP` — the rise IS the
    ramp, now on every floor instead of only past 30.
- **The recuperation wall (`WARDEN_RECUP`, floors 31+).** Warden HP
  recuperates, and the recuperation speed is what forces coordination.
  The 022/024/025 machinery is kept and NAMED as the fourth law:
  - Three regimes, unchanged: siege floors (≤ 10) never regen — every
    wound is permanent; solo band (11–30) has no regen, only the 30 h
    silence window; from floor 31 the pool heals a constant
    **2.78%/hour** (breakeven at N(F)∕2 sustained strikers). The
    FRACTION is flat; the absolute HP/hour rides the pillar-scaled
    pool automatically, so recuperation speed is itself exponential.
  - The wall's growth is the param: `N(F) = ceil(R100^((F−30)∕70))`,
    i.e. the striker quorum grows ×`WARDEN_RECUP` = R100^(1∕70) per
    floor (≈ ×1.068 at A = 1000). `R100 = max(min(50, 0.5·A),
    0.10·A)` with **A = players active in the last 7 days** (census
    window pinned here; small worlds pay a higher share, capped at 50
    strikers).
  - GAP TO FIX: worldd's `_census` (app/social.py) counts every
    `stage='playing'` account with NO activity window — a dead
    account inflates A forever. Add the 7-day filter on the doc's
    `last_seen` (already stamped on every action):
    `AND (doc->>'last_seen')::timestamptz > now() - interval
    '7 days'`. The plugin side (`census.total` → `active` → economy)
    needs no change.
  - What the algebra buys, verified by the 046 projection: solo
    STALLS permanently from floor 31 (net rate exactly 0 at N = 2);
    ≤ N∕2 strikers lose ground forever; the floor-100 kill takes
    exactly N = 10% of actives each committing one banked energy bar
    (24 ⚡ = 8 strike-fights = one pool share) — dead within the hour,
    same day by construction. Sustained-only play (no banked bars)
    needs 1.25·N for a same-day kill, 36 h at N.
  - Client payloads: the floor-100 pool is ~9.2×10¹⁶ HP — PAST the
    JS safe-integer line (9×10¹⁵). Pool state ships as a
    fraction-of-max plus a server-formatted string, never a raw int.

### 4. The pace discount — time is exponential too

Income does NOT ride the full pillar: `PACE_DISCOUNT` is subtracted
from the monster exponential (a division of growth bases), and the
wedge between the two exponents is exactly the calendar:

```
PACE_DISCOUNT = 1.04            # discounted off the pillar
income(B) = (PILLAR / PACE_DISCOUNT) ** (B - 1)   # ≈ 1.25^(B−1)
days(B)   = d0 * PACE_DISCOUNT ** (B - 1)         # by construction
```

Time-per-floor = cost ÷ income/day. Costs ride the full `pillar(B)`;
ALL income rides the discounted `income(B)` — so days-to-afford floor
B's kit grows ×1.04/floor, exponential by construction, floor 1
untouched. The throttle is purely economic: energy, fight length, and
win rates never move, so a fight still FEELS at-level while the wallet
falls exponentially behind the shop.

- `gold_per_kill(bar)` → floor-1 anchor × `income(bar)`; same for
  night-work/strongbox/flare gold (wardens: §3, rise included).
  Retire `BAND_INCOME_JUMP`.
- Prices keep their day-formulas but read the exponential days:
  forge set(T) ≈ `days₀ · PACE_DISCOUNT^(band_start(T)−1)` of tier
  income, training "one day of at-level income", hone/mend/sleep
  pillar-priced against discounted earnings — every sink inherits the
  wedge from the two exponents, none is hand-tuned.
- **XP carries the same discount** or players out-level the slower
  floors: `xp_per_kill(bar)` → anchor × `income(bar)` shape (with
  043's linear-in-bar factor), `xp_need` untouched — time-to-level L
  ≈ time-on-floor L, so level ≈ floor stays true to the cap.
- Bank interest is a rate — untouched, but it now compounds against
  exponential prices; audit that hoarding a band doesn't beat
  climbing (interest cap already exists from 023).
- Past floor 30 the shared-warden siege curve
  (`N(F) = R100^((F−30)/70)` strikers) is ALREADY exponential and
  composes on top of the economic pace — no change there.

Reference (d₀ ≈ 0.3 days at floor 1): PACE_DISCOUNT 1.03 → total
climb ~6 months, floor 100 ~6 days · **1.04 → ~1 year, floor 100
~2 weeks (chosen)** · 1.05 → ~2 years, floor 100 ~39 days. One
constant to retune after the /mechanics regen.

### 5. Numbers the eye can read

- Server side Python ints — exact at any floor.
- Client/UI: format all gold/HP/ATK/DEF ≥ 10 000 as 12.4K / 3.1M /
  1.9B / 2.4T (one shared formatter in render.py + site JS). Floor-100
  monster HP ~10¹²–10¹³ stays far under JS's 9×10¹⁵ safe-integer line;
  the formatter keeps ledgers and cards readable.
- /mechanics: regenerate via `tools/gen_mechanics.py`; add a
  **Difficulty ×** column (`pillar(F)`, formatted) so the 1 → 1.3 →
  1.69 … ladder is explicit on the page that triggered this plan.

## What does NOT change

Rounds-to-kill, win probabilities, kill bars, energy, speed/dodge,
class matchups (tier multipliers), body/bite texture, drops/specimen
weights, story, `xp_need`. Fight FEEL is untouched; the numbers climb
the pillar (×1.3) per floor and the calendar climbs `PACE_DISCOUNT`
(×1.04) per floor.

## Phases

1. **The law + the player** — `pillar()`, §1 backbone, §2 gear ladder
   regen (bonuses only), geometric rungs/honing. Unit tests updated.
2. **The monsters and the gates** — §3 conversions, `WARDEN_RISE`,
   retire ramps, kill legacy `monster_stats` path.
3. **The price of everything** — §4 pace-discount sweep: income →
   `income(bar)`, XP discount, retire `BAND_INCOME_JUMP`, reprice
   `_FORGE_ROWS` from the discount, interest-vs-climb audit.
4. **The readable number** — shared K/M/B/T formatter (render.py,
   site JS), /mechanics Difficulty column, `gen_mechanics.py` regen.
5. **Prove it** — acceptance below, full pytest, dojo production run.

## Acceptance

1. **The 30% law**: for every floor F ≥ 5, common-monster
   `HP(F+1)/HP(F)` and `ATK(F+1)/ATK(F)` ∈ [1.25, 1.35] (rounding
   slack); at F ≥ 20 within [1.29, 1.31]. Floor 100 common HP / floor 1
   common HP ∈ [1.6×10¹¹, 2.3×10¹¹]. Same check for reference player
   ATK/HP and reference weapon bonus.
2. **Relative feel unchanged**: /mechanics Monte Carlo — kill bar for
   the common specimen on floor B is still B (±1 where 043 already
   tolerated it), win ≈ 90% (accept ≥ 85%), floors 1–100.
3. **Pace exponential**: simulated days-to-afford floor F's reference
   kit (sustained 32 fights/day) grows ×PACE_DISCOUNT ± rounding per
   floor; total climb lands within 20% of the chosen table row;
   level ≈ floor still true through 30 in the same simulation;
   floor-1 stats and prices byte-identical to 0.59.0.
4. **The warden rise**: `warden HP ÷ same-floor common-monster HP`
   grows ×WARDEN_RISE per floor (×1.8 relative premium at F30, ×7.1
   at F100); every warden on floors 1–30 still solo-winnable at-level
   in the Monte Carlo (strike survivability preserved on all floors).
5. **The recuperation wall**: regen 0 through floor 30; from 31, one
   sustained striker never reduces the pool (solo stalls, does not
   win); floor 100 with A ≥ 500 weekly actives falls to exactly
   ⌈0.10·A⌉ strikers bursting banked bars inside one day, and does
   NOT fall to ⌈0.05·A⌉; pool values in every payload arrive as
   fraction + formatted string (no raw ints past 2⁵³).
6. **No overflow artifacts**: floor-100 ledger, card, and /mechanics
   render formatted values; no scientific notation or negative
   wraparound anywhere in the UI.

## Risks / decisions taken

- **Per-stat ×1.3** chosen over "composite power ×1.3" (which would be
  ×~1.14 per stat) — the designer's own example (1, 1.3, 1.3²…) is
  about the numbers a floor shows, and both sides scale together so
  feel is unaffected. Flag: fights *between* floors polarize — a
  monster 5 floors up now out-stats you ×3.7, 10 floors up ×13.8.
  That IS the requested dramatic increase; the rubber band and gate
  leash (`floor_entry_player_level`) already fence it.
- **PvP / social**: cross-floor player gaps widen the same way. The
  ladder/PvP already keys off nearby floors; anything that matches
  across >5 floors should be band-restricted (audit in phase 2).
- **Rounding at the bottom**: floors 1–4 have single-digit stats;
  anchoring floor 1 exactly and rounding `pillar()` per stat keeps them
  byte-identical (acceptance 3).
- **Frozen level term past 30**: its share of player power decays to
  zero; harmless because monsters are derived from the same reference
  loadout, but the level-30 body's *unkitted* HP share shrinks — the
  046 exponential makes deep-floor survival even more gear-bought than
  043 did. That is the stated doctrine ("steel alone").
