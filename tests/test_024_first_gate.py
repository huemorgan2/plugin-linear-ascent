"""024 — the first gate.

The complaint: floor 1's shared Warden showed 1,064 HP, "impossible for
one player". Two mistunings sat behind it — a pool sized by a constant
written for the coordination floors, and a regen trickle that outran the
only healing a climber has (dawn). These gates pin the fix and pin that
floors 31+ came through it numerically untouched.
"""

from plugin_linear_ascent import economy
from plugin_linear_ascent.engine import core, tips

from tests.test_022_001_one_list_of_bosses import (playing, warden_world)


# ── A. the pool ramps across the solo band ───────────────────────────────

def test_first_gate_is_two_fights_not_eight():
    pool = economy.world_warden_hp(1)
    unit = economy.strike_fight_damage(1)
    assert economy.warden_pool_fights(1) == 2
    assert round(pool / unit) == 2
    # and it fits inside a single energy bar, with room to spare
    bar = economy.energy_cap(economy.gear_tier_for_floor(1)) \
        // economy.COST_WARDEN_ATTEMPT
    assert pool / unit <= bar


def test_the_pool_no_longer_dwarfs_its_own_warden():
    """The old flat 8 made floor 1 the worst-tuned point in the tower:
    15.2× its solo Warden's body, against 8.8× at floor 30. Nothing in
    the solo band may read that much worse than the band's top."""
    top = economy.world_warden_hp(30) / economy.warden_stats(30)[2]
    for fno in range(1, 30):
        if fno % 10 == 0:
            continue
        ratio = economy.world_warden_hp(fno) / economy.warden_stats(fno)[2]
        assert ratio <= top * 1.1, (fno, ratio, top)


def test_the_ramp_climbs_to_the_coordination_band():
    fights = [economy.warden_pool_fights(f) for f in range(1, 101)]
    assert fights == sorted(fights), "the ramp must never step back"
    assert fights[0] == economy.WARDEN_POOL_FIGHTS_MIN
    for fno in range(30, 101):
        assert economy.warden_pool_fights(fno) == economy.WARDEN_POOL_FIGHTS


# ── the climb 1–30 is a climb: monotone, and linear in EFFORT ────────────

def test_no_floor_in_the_band_is_weaker_than_the_floor_below():
    """The dip 024 found: floor 3's pool came out UNDER floor 2's (306 vs
    308) because the fight unit rides integer round counts, and floor 27
    under floor 26. A tower may not step backwards on the way up."""
    pools = [economy.world_warden_hp(f) for f in range(1, 31)]
    assert pools == sorted(pools), pools


def test_the_effort_curve_is_a_straight_line_two_to_eight():
    """What the climber actually feels is FIGHTS, not HP. One honest step
    per floor, 2 at the first gate to 8 at the soft floor — no cliffs
    (rounding the ramp to whole fights put +35–40% steps on 14, 17, 21
    and 25) and no plateaus."""
    effort = [economy.world_warden_hp(f) / economy.strike_fight_damage(f)
              for f in range(1, 31)]
    assert effort[0] == 2.0
    assert abs(effort[-1] - 8.0) < 0.25
    step = (8.0 - 2.0) / 29
    for fno, (a, b) in enumerate(zip(effort, effort[1:]), start=1):
        # the raw unit rides integer round counts and can wobble a
        # fraction of a fight between neighbours; what must never happen
        # is a backslide a climber could feel
        assert -0.1 < b - a < 3 * step, (fno, a, b)
    for fno, want in enumerate(effort, start=1):
        expected = 2.0 + step * (fno - 1)
        assert abs(want - expected) < 0.5, (fno, want, expected)


def test_the_pool_itself_never_cliffs_beyond_the_gear_ladder():
    """Pool jumps track the reference kit: the one big step left (+40% at
    floor 8) is the at-level loadout changing gear band, not the ramp —
    and the effort curve stays smooth straight through it."""
    for fno in range(2, 31):
        prev = economy.world_warden_hp(fno - 1)
        jump = (economy.world_warden_hp(fno) - prev) / prev
        assert jump <= 0.40, (fno, jump)


def test_floors_31_plus_are_numerically_untouched():
    """Every 022/002 acceptance gate reads floors 31+. The retune must
    not have moved a single one of those numbers."""
    for active in (None, 200, 1_000, 10_000):
        for fno in range(31, 101):
            old = max(1, round(economy.required_strikers(fno, active)
                               * 8 * economy.strike_fight_damage(fno)))
            assert economy.world_warden_hp(fno, active) == old, (fno, active)
            assert economy.world_warden_regen_hourly(fno) == \
                economy.SUSTAINED_FIGHTS_PER_HOUR / 16


# ── B. the solo band's healer is silence, not a trickle ──────────────────

def test_a_solo_wound_outlives_the_dawn_the_climber_needs():
    """A body heals at dawn and nowhere else, so a lone climber's honest
    cadence is one strike a day. A wound that closes faster than that is
    a wound one player can never finish."""
    for fno in (1, 12, 30):
        assert economy.world_warden_regen_hourly(fno) == 0.0
        assert economy.warden_silence_hours(fno) > 24.0


def test_deep_floors_keep_their_trickle_and_their_window():
    for fno in (31, 45, 90):
        assert economy.world_warden_regen_hourly(fno) > 0
    assert economy.warden_silence_hours(31) == economy.WARDEN_SILENCE_MIN_H
    assert economy.warden_silence_hours(90) == economy.WARDEN_SILENCE_MAX_H


def test_one_climber_can_actually_close_the_first_gate():
    """The whole point. Two full fights, six energy, and the wound is
    still there when he comes back healed — so the gate falls to one
    player inside two dawns."""
    pool = economy.world_warden_hp(1)
    per_fight = economy.strike_fight_damage(1)
    fights = -(-pool // per_fight)
    assert fights <= 2
    assert fights * economy.COST_WARDEN_ATTEMPT \
        <= economy.energy_cap(1, "human")
    # nothing heals between his visits but a full day of neglect
    healed_overnight = economy.world_warden_regen_hourly(1) * pool * 12
    assert healed_overnight == 0


# ── C. pay tracks the work ───────────────────────────────────────────────

def test_a_two_fight_gate_does_not_pay_for_eight():
    assert economy.world_warden_reward_mult(1) == \
        economy.warden_pool_fights(1)
    # per-energy parity with the solo-tuned warden it replaced
    pool_gold = economy.warden_gold(1) * economy.world_warden_reward_mult(1)
    fights = economy.world_warden_hp(1) / economy.strike_fight_damage(1)
    per_fight = pool_gold / fights
    assert abs(per_fight - economy.warden_gold(1)) < 1


# ── E. the card says what the bar is measured in ─────────────────────────

def _keep(hp=None, floor=1):
    p = playing("Kettle", world=warden_world(floor, hp=hp))
    core.apply_choice(p, "gate")
    core.apply_choice(p, f"floor_{floor}")
    return core.apply_choice(p, "keep")


def test_the_keep_card_counts_the_fights_left():
    s = _keep()
    body = " ".join(s.body_lines)
    assert "full fights left to close" in body
    assert f"{economy.world_warden_hp(1):,}" in body


def test_the_last_fight_is_announced_as_the_last():
    s = _keep(hp=economy.strike_fight_damage(1) - 5)
    body = " ".join(s.body_lines)
    assert "1 full fight left to close" in body


def test_joining_the_fight_carries_a_tip():
    s = _keep()
    strike = next(o for o in s.options if o.id == "strike")
    tip = tips.option_tip(strike.id)
    assert tip
    for phrase in ("stays cut", "full fights", "closes"):
        assert phrase in tip
