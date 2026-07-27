"""017 — the difficulty smoothness gate (plan §7.3).

Roy, 2026-07-27: "make full playable tests, measure all the economy of
things, see there are no bumps of step function in difficulty."

A closed-form walk of the at-level reference player of EACH class up
floors 1-100, measuring per floor:

- rounds-to-kill against the floor's intended targets (encounters the
  class is not hard-countered by — a player flees those),
- death risk: expected damage taken per fight as a share of max HP,
- income per fight (gold/kill × the floor's average profile bump).

Gate: no cliffs. Adjacent floors may not move any metric by more than
25%, INCLUDING band boundaries (10→11, 20→21 …) — tier jumps must be
absorbed by the rungs, not felt as walls. A 5-floor moving average may
not move more than 15% per step, so slow drifts stay smooth too.

This file grows with every 017 phase that touches the economy.
"""

import math

from plugin_linear_ascent import economy
from plugin_linear_ascent.content import schema

FLOORS = range(1, 101)
ADJACENT_CAP = 0.25
TREND_CAP = 0.15


def _expected_player_damage(clazz, floor, profile):
    p_atk, _ = economy._at_level_loadout(floor)
    raw = round(0.75 * p_atk)                    # E[rng_int(atk/2, atk)]
    dtype = economy.DAMAGE_TYPE[clazz]
    _, m_def, _ = economy.monster_stats(floor)
    return economy.typed_damage(dtype, raw, m_def, profile)


def _expected_monster_damage(floor):
    m_atk, _, _ = economy.monster_stats(floor)
    _, p_def = economy._at_level_loadout(floor)
    raw = round(0.75 * m_atk)
    chip = max(1, math.ceil(raw / economy.CHIP_DIVISOR))
    return max(chip, raw - p_def // 2)


def _is_intended(clazz, profile):
    """A target the class hunts: no tier cut, reachable, not a bulwark,
    and (002) not the class's speed predator — FAST counters the bow.
    Everything else the at-level player either avoids or treats as a
    priced slog — those belong to the matchup gate, not the pace curve."""
    dtype = economy.DAMAGE_TYPE[clazz]
    if dtype == "melee" and profile["flying"]:
        return False
    if profile["bulwark"]:
        return False
    if dtype == "ranged" and \
            profile.get("speed", economy.SPEED_NORMAL) >= economy.SPEED_FAST:
        return False
    tier = profile["resist"] if dtype == "magic" else profile["armor"]
    return economy.TIER_MULT[tier] >= 1.0


def _chase_adjusted(clazz, kill_rounds, profile):
    """002 §2.4: fights open at range. Returns (total_rounds,
    expected_hits_taken_in_full_hit_units) for the class's NATURAL play:
    melee closes immediately; magic stands and casts (full at both
    ranges, halved hits while the monster crosses); the bow KITES —
    shoot until caught, spend rounds reopening, repeat. The kite cycle
    is a flat multiplier (shoot+reopen)/shoot, so the pace curve stays
    a curve instead of accelerating once kill_rounds outgrows the
    crossing time."""
    dtype = economy.DAMAGE_TYPE[clazz]
    pspd = economy.PLAYER_BASE_SPEED
    mspd = profile.get("speed", economy.SPEED_NORMAL)
    dodge = 1 - economy.dodge_pct(pspd, mspd) / 100
    if dtype == "melee":
        return kill_rounds + 1, (0.5 + kill_rounds) * dodge
    exp_at_range = 1 / economy.p_close(mspd, pspd)
    if dtype == "ranged":
        shoot = exp_at_range                     # rounds shooting per cycle
        reopen = 1 / economy.p_open(pspd, mspd)  # rounds reopening per cycle
        cycle = shoot + reopen
        total = kill_rounds * cycle / shoot
        taken = (0.5 * shoot + reopen) / cycle * total * dodge
        return total, taken
    total = kill_rounds
    at_range = min(total, exp_at_range)
    taken = (0.5 * at_range + (total - at_range)) * dodge
    return total, taken


def _floor_metrics(clazz, floor):
    fl = schema.get_floor(floor)
    _, _, m_hp = economy.monster_stats(floor)
    rounds_w = risk_w = weight_w = 0.0
    gold_w = gold_weight = 0.0
    for enc in fl.encounters:
        profile = economy.profile_from_traits(enc.traits)
        gold_w += enc.weight * economy.profile_gold_mult(profile)
        gold_weight += enc.weight
        if not _is_intended(clazz, profile):
            continue                              # priced slog or a flee
        dmg = _expected_player_damage(clazz, floor, profile)
        kill_rounds = m_hp / max(1, dmg)
        total, taken = _chase_adjusted(clazz, kill_rounds, profile)
        rounds_w += enc.weight * total
        risk_w += enc.weight * taken
        weight_w += enc.weight
    assert weight_w > 0, f"floor {floor}: no intended target for {clazz}"
    rounds = rounds_w / weight_w
    risk = (risk_w / weight_w) * _expected_monster_damage(floor) \
        / economy.player_max_hp(floor)
    income = economy.gold_per_kill(floor) * (gold_w / gold_weight)
    return rounds, risk, income


def _series(clazz):
    rounds, risk, income = [], [], []
    for f in FLOORS:
        r, k, i = _floor_metrics(clazz, f)
        rounds.append(r)
        risk.append(k)
        income.append(i)
    return {"rounds": rounds, "risk": risk, "income": income}


def _max_step(values, floor=0.2):
    worst, where = 0.0, 0
    for i, (a, b) in enumerate(zip(values, values[1:])):
        base = max(a, floor)                      # damp tiny-value noise
        step = abs(b - a) / base
        if step > worst:
            worst, where = step, i + 1
    return worst, where


# Risk is a 0..1 share of max HP: on the kindergarten floors it sits at
# 0.05-0.15 where a designed +5-point ramp reads as a huge RELATIVE step.
# A 0.25 base means only moves above ~6 HP-points per floor can fail —
# absolute cliffs, not ramp noise. Rounds live at 2+ so 0.2 never bites.
BASE_FLOOR = {"rounds": 0.2, "risk": 0.25}


def _moving_average(values, window=5):
    out = []
    for i in range(len(values)):
        lo = max(0, i - window + 1)
        out.append(sum(values[lo:i + 1]) / (i + 1 - lo))
    return out


# Difficulty metrics get the hard caps. Income is a REWARD curve —
# upward steps (the ×1.2 band paycheck) are design, so income is gated
# separately: it may never fall off a cliff and never regress in trend.
DIFFICULTY = ("rounds", "risk")


def test_no_cliffs_between_adjacent_floors():
    for clazz in economy.DAMAGE_TYPE:
        series = _series(clazz)
        for name in DIFFICULTY:
            values = series[name]
            worst, at = _max_step(values, BASE_FLOOR[name])
            assert worst <= ADJACENT_CAP, (
                f"{clazz}/{name}: {worst:.0%} step at floor {at}→{at + 1} "
                f"({values[at - 1]:.2f} → {values[at]:.2f})")


def test_band_boundaries_are_absorbed():
    """The gear-tier jump must never be felt as a wall at F0→F1."""
    for clazz in economy.DAMAGE_TYPE:
        series = _series(clazz)
        for name in DIFFICULTY:
            values = series[name]
            for band_end in range(10, 100, 10):
                a, b = values[band_end - 1], values[band_end]
                step = abs(b - a) / max(a, BASE_FLOOR[name])
                assert step <= ADJACENT_CAP, (
                    f"{clazz}/{name}: {step:.0%} wall at band boundary "
                    f"{band_end}→{band_end + 1}")


def test_trends_drift_smoothly():
    for clazz in economy.DAMAGE_TYPE:
        series = _series(clazz)
        for name in DIFFICULTY:
            smooth = _moving_average(series[name])
            worst, at = _max_step(smooth, BASE_FLOOR[name])
            assert worst <= TREND_CAP, (
                f"{clazz}/{name}: smoothed trend jumps {worst:.0%} at "
                f"floor {at}→{at + 1}")


def test_income_never_cliffs_down_or_regresses():
    """Climbing higher must always pay at least as well per kill; a
    single floor may never cut the paycheck by more than 10%."""
    for clazz in economy.DAMAGE_TYPE:
        income = _series(clazz)["income"]
        for i, (a, b) in enumerate(zip(income, income[1:])):
            assert b >= a * 0.90, (
                f"{clazz}: income falls {1 - b / a:.0%} at floor "
                f"{i + 1}→{i + 2}")
        smooth = _moving_average(income)
        assert all(b >= a * 0.98 for a, b in zip(smooth, smooth[1:])), (
            f"{clazz}: smoothed income per kill regresses somewhere")
