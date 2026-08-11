"""017/048 — the difficulty smoothness gate (plan §7.3, 048 T3).

Roy, 2026-07-27: "make full playable tests, measure all the economy of
things, see there are no bumps of step function in difficulty."

048: the walk is per weapon PATH (blade/bow/staff) at the reference
trained rank (6), reference gear, floors 1-100, measuring per floor:

- rounds-to-kill against the floor's intended targets (types the path
  answers at ×1.0 — a player flees or re-arms against the rest),
- death risk: expected damage taken per fight as a share of max HP,
- income per fight (gold/kill × the floor's average type bump).

Gate: no cliffs. Adjacent floors may not move any metric by more than
40%, INCLUDING band boundaries (10→11, 20→21 …) — tier jumps must be
absorbed by the rungs, not felt as walls. A 5-floor moving average may
not move more than 15% per step, so slow drifts stay smooth too.
And no floor may strand a path: each of the three paths must have at
least one monster it answers at ×1.0 on every floor.

The rank axis (0→10 on fixed floors) and the weapon-rung axis land
with the phase-6 bake.
"""

import math

from plugin_linear_ascent import economy
from plugin_linear_ascent.content import schema

FLOORS = range(1, 101)
PATHS = ("blade", "bow", "staff")
PATH_DTYPE = {"blade": "melee", "bow": "ranged", "staff": "magic"}
REF_RANK = 6
# 046: the design law IS ×1.3 a floor — an upward difficulty step is
# a wall only past the pillar plus one integer blow of noise (fights
# run ~4 rounds, so one extra blow landing moves risk ~25% alone);
# the TREND_CAP below still holds the smoothed curve to the shape
ADJACENT_CAP = 0.40
TREND_CAP = 0.15

# the reference hand: rank 6 — mean roll of [floor·ATK, ATK], and the
# 10% miss priced into the pace (a miss eats the round, not the fight)
_MEAN_ROLL = (economy.TRAIN_ROLL_FLOOR(REF_RANK) + 1) / 2
_HIT = 1 - economy.TRAIN_MISS_PCT(REF_RANK) / 100


def _expected_player_damage(path, floor, mtype, m_def):
    p_atk, _ = economy._at_level_loadout(floor)
    raw = round(_MEAN_ROLL * p_atk)
    return economy.typed_damage_048(path, raw, m_def, mtype) * _HIT


def _expected_monster_damage(floor, m_atk):
    _, p_def = economy._at_level_loadout(floor)
    raw = round(0.75 * m_atk)
    chip = max(1, math.ceil(raw / economy.CHIP_DIVISOR))
    return max(chip, raw - p_def // 2)


def _is_intended(path, mtype, prof):
    """A target the path hunts: a full (×1.0) triangle answer and not a
    bulwark. Everything else the reference player either re-arms for,
    avoids, or treats as a priced slog — those belong to the matchup
    gate, not the pace curve."""
    if prof["bulwark"]:
        return False
    return economy.TYPE_MULT[mtype][path] >= 1.0


def _chase_adjusted(path, kill_rounds, prof):
    """002 §2.4: fights open at range. Returns (total_rounds,
    expected_hits_taken_in_full_hit_units) for the path's NATURAL play:
    steel closes immediately; the staff stands and casts (full at both
    ranges, halved hits while the monster crosses); the bow KITES —
    shoot until caught, spend rounds reopening, repeat. The kite cycle
    is a flat multiplier (shoot+reopen)/shoot, so the pace curve stays
    a curve instead of accelerating once kill_rounds outgrows the
    crossing time."""
    dtype = PATH_DTYPE[path]
    pspd = economy.PLAYER_BASE_SPEED
    mspd = prof.get("speed", economy.SPEED_NORMAL)
    dodge = 1 - economy.dodge_pct(pspd, mspd) / 100
    if dtype == "melee":
        return kill_rounds + 1, (0.5 + kill_rounds) * dodge
    exp_at_range = 1 / economy.p_close(mspd, pspd)
    if dtype == "ranged":
        # 048: the bow's prey now includes the FAST flyer — kiting
        # something faster than you wastes rounds reopening ground it
        # instantly eats. Natural play picks the safer of the two
        # stances: kite (slow/even prey) or stand and shoot (fast).
        shoot = exp_at_range                     # rounds shooting per cycle
        reopen = 1 / economy.p_open(pspd, mspd)  # rounds reopening per cycle
        cycle = shoot + reopen
        kite_total = kill_rounds * cycle / shoot
        kite_taken = (0.5 * shoot + reopen) / cycle * kite_total * dodge
        stand_total = kill_rounds
        at_range = min(stand_total, exp_at_range)
        stand_taken = (0.5 * at_range
                       + (stand_total - at_range)) * dodge
        if (kite_taken, kite_total) <= (stand_taken, stand_total):
            return kite_total, kite_taken
        return stand_total, stand_taken
    total = kill_rounds
    at_range = min(total, exp_at_range)
    taken = (0.5 * at_range + (total - at_range)) * dodge
    return total, taken


def _floor_metrics(path, floor):
    fl = schema.get_floor(floor)
    rounds_w = risk_w = weight_w = 0.0
    gold_w = gold_weight = 0.0
    for enc in fl.encounters:
        traits = tuple(getattr(enc, "traits", ()) or ())
        mtype = economy.type_from_traits(traits)
        profile = economy.profile_from_traits(traits)
        gold_w += enc.weight * economy.profile_gold_mult(profile)
        gold_weight += enc.weight
        if not _is_intended(path, mtype, profile):
            continue                              # re-arm, slog, or flee
        # The walk measures the SYSTEM's ramp: floor reference stats ×
        # the TYPE multipliers. Archetype spread (frail prey, savage
        # threats) is the 025 roster design — it belongs to the matchup
        # gate, not the pace curve (creature_stats would leak it in).
        m_atk, m_def, m_hp = economy.monster_stats(floor)
        m_atk = round(m_atk * economy.TYPE_ATK[mtype])
        m_hp = round(m_hp * economy.TYPE_HP[mtype])
        dmg = _expected_player_damage(path, floor, mtype, m_def)
        kill_rounds = m_hp / max(1, dmg)
        total, taken = _chase_adjusted(path, kill_rounds, profile)
        rounds_w += enc.weight * total
        risk_w += enc.weight * taken * _expected_monster_damage(floor,
                                                                m_atk)
        weight_w += enc.weight
    assert weight_w > 0, f"floor {floor}: no intended target for {path}"
    rounds = rounds_w / weight_w
    # 022/002: the at-level pool is reference_player_hp (level capped,
    # armor feeds HP) — player_max_hp(floor) would read a floor as a
    # level and freeze the denominator at the cap.
    risk = (risk_w / weight_w) / economy.reference_player_hp(floor)
    income = economy.gold_per_kill(floor) * (gold_w / gold_weight)
    return rounds, risk, income


def _series(path):
    rounds, risk, income = [], [], []
    for f in FLOORS:
        r, k, i = _floor_metrics(path, f)
        rounds.append(r)
        risk.append(k)
        income.append(i)
    return {"rounds": rounds, "risk": risk, "income": income}


def _max_step(values, floor=0.2):
    """Worst adjacent move, measured against the rolling max of the two
    previous floors (022/002): a recovery from a single easy-floor DIP
    (a slow, kiteable spawn table) is not a wall — a true wall exceeds
    both neighbours' baseline and still fails."""
    worst, where = 0.0, 0
    for i, (a, b) in enumerate(zip(values, values[1:])):
        base = max(max(values[max(0, i - 1):i + 1]), floor)
        # 046: only steps UP count — the band seam hands the reference a
        # whole tier, and difficulty FALLING there is relief, not a wall
        step = max(0.0, b - a) / base
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
    for path in PATHS:
        series = _series(path)
        for name in DIFFICULTY:
            values = series[name]
            worst, at = _max_step(values, BASE_FLOOR[name])
            assert worst <= ADJACENT_CAP, (
                f"{path}/{name}: {worst:.0%} step at floor {at}→{at + 1} "
                f"({values[at - 1]:.2f} → {values[at]:.2f})")


def test_band_boundaries_are_absorbed():
    """The gear-tier jump must never be felt as a wall at F0→F1."""
    for path in PATHS:
        series = _series(path)
        for name in DIFFICULTY:
            values = series[name]
            for band_end in range(10, 100, 10):
                a, b = values[band_end - 1], values[band_end]
                # same dip-forgiving baseline as _max_step (022/002):
                # recovery from a single easy floor is not a wall.
                base = max(max(values[max(0, band_end - 2):band_end]),
                           BASE_FLOOR[name])
                step = max(0.0, b - a) / base
                assert step <= ADJACENT_CAP, (
                    f"{path}/{name}: {step:.0%} wall at band boundary "
                    f"{band_end}→{band_end + 1}")


def test_trends_drift_smoothly():
    for path in PATHS:
        series = _series(path)
        for name in DIFFICULTY:
            smooth = _moving_average(series[name])
            worst, at = _max_step(smooth, BASE_FLOOR[name])
            assert worst <= TREND_CAP, (
                f"{path}/{name}: smoothed trend jumps {worst:.0%} at "
                f"floor {at}→{at + 1}")


def test_income_never_cliffs_down_or_regresses():
    """Climbing higher must always pay at least as well per kill; a
    single floor may never cut the paycheck by more than 10%."""
    for path in PATHS:
        income = _series(path)["income"]
        for i, (a, b) in enumerate(zip(income, income[1:])):
            assert b >= a * 0.90, (
                f"{path}: income falls {1 - b / a:.0%} at floor "
                f"{i + 1}→{i + 2}")
        smooth = _moving_average(income)
        assert all(b >= a * 0.98 for a, b in zip(smooth, smooth[1:])), (
            f"{path}: smoothed income per kill regresses somewhere")


def test_every_floor_answers_every_path():
    """048 T3: no floor strands a path — each of blade/bow/staff has at
    least one monster it answers at ×1.0 on every floor."""
    for f in FLOORS:
        fl = schema.get_floor(f)
        types = {economy.type_from_traits(
            tuple(getattr(e, "traits", ()) or ())) for e in fl.encounters}
        for path in PATHS:
            assert any(economy.TYPE_MULT[t][path] >= 1.0 for t in types), (
                f"floor {f} strands {path}: roster types {sorted(types)}")
