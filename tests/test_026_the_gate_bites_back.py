"""026 — a gate is never free.

The complaint, in the player's words: "why did you remove the cost of
energy on every boss attack, now I can attack without limit", and "I also
liked that you couldn't run when you wanted — sometimes it would follow
you, so there was a price to pay for attacking the boss".

Nothing had been removed. 3 ⚡ still buys a keep fight and the getaway
still rolls — but both hang off the Warden being able to hurt you, and
against a climber whose DEF had outgrown the gate `max(chip, raw − DEF/2)`
paid out the 1-POINT chip. With a 1-point bite the fight had no end
condition at all (one charge = unlimited swings, ~135 rounds to empty the
floor-1 pool) and a failed escape cost 1 HP, which is not a chase.

Two laws close it, and neither touches the damage table — heavier Warden
blows were tried first and measured: a per-round floor at the mean bite
deleted the lower half of the roll, and halving the chip divisor dropped
the deep coordination band from ~60% at-level wins to ~20%.

  1. One charge buys ONE exchange — warden_exchange_rounds, the same
     near-death fight the pool is measured in. Then its guard closes.
  2. A gate never lets you walk: the getaway is capped at 3-in-4 and the
     blow that catches you lands its grip, not a chip.

Amended later by the designer: every swing inside the keep now ALSO costs
COST_WARDEN_STRIKE ⚡ (free swings were the original complaint, and the
round budget alone still let a full exchange run on one charge). The
exchange budget and the getaway law above are unchanged.
"""

import pytest

from plugin_linear_ascent import economy
from plugin_linear_ascent.engine import core, state

from tests.test_022_001_one_list_of_bosses import playing, warden_world
from tests.test_017_damage_types import reference_player


def _at_keep(p, floor=1):
    core.apply_choice(p, "gate")
    core.apply_choice(p, f"floor_{floor}")
    core.apply_choice(p, "keep")
    return p


def _striker(level, floor=1, world=True):
    """A climber in the floor's reference kit at an arbitrary LEVEL — the
    over-geared grinder the hole belonged to."""
    p = playing(world=warden_world(floor) if world else None,
                name=f"striker-{level}")
    p["gear"] = dict(reference_player("warrior", floor)["gear"])
    p["level"] = level
    p["hp"] = state.max_hp(p)
    return p


def _swing_until_it_ends(p, cap=400):
    """Swings with the bar topped up each round — the exchange budget is
    what these tests measure, not the per-swing toll (which has its own
    test below)."""
    rounds = 0
    while p.get("encounter") is not None and rounds < cap:
        p["energy_val"] = state.energy_cap_of(p)
        core.apply_choice(p, "attack")
        rounds += 1
    return rounds


# ── A. one charge, one exchange ──────────────────────────────────────────

@pytest.mark.parametrize("level", [1, 4, 6, 10, 20])
def test_the_keep_fight_always_ends(level):
    """However good the steel, the exchange runs out. Before 026 a level-6
    climber could stand in the floor-1 keep for 135 rounds on one charge —
    that is what "I can attack without limit" meant."""
    p = _striker(level)
    _at_keep(p)
    core.apply_choice(p, "strike")
    rounds = _swing_until_it_ends(p)
    assert p.get("encounter") is None, (level, rounds)
    assert rounds <= economy.warden_exchange_rounds(1)


def test_the_charge_buys_the_fight_the_pool_is_measured_in():
    """One function, so the fight a player is SOLD and the unit the pool
    is priced in can never drift apart."""
    for floor in range(1, 31):
        n = economy.warden_exchange_rounds(floor)
        _p_atk, p_def = economy._at_level_loadout(floor)
        w_atk, _w_def, _hp = economy.warden_stats(floor)
        w_dmg = max(1, round(0.75 * w_atk) - p_def // 2)
        assert n == max(1, (economy.reference_player_hp(floor) - 1) // w_dmg)
        assert economy.strike_fight_damage(floor) % n == 0


def test_the_guard_closing_is_not_a_defeat_and_keeps_the_wound():
    """Driven back is the third exit, beside the kill and the death: the
    ⚡ bought the exchange, and every point cut stays cut."""
    p = _striker(8)
    _at_keep(p)
    before = p["_world"]["warden"]["hp"]
    core.apply_choice(p, "strike")
    for _ in range(economy.warden_exchange_rounds(1)):
        if p.get("encounter") is None:
            break
        s = core.apply_choice(p, "attack")
    assert p.get("encounter") is None
    assert p["hp"] > 0, "the guard closing must not read as a death"
    dealt = next(x["damage"] for x in p["_effects"]
                 if x["kind"] == "warden_strike")
    assert 0 < dealt
    said = " ".join([s.headline, s.support] + list(s.body_lines))
    assert "stays cut" in said
    assert "Driven back" in s.headline or "guard closes" in said


def test_every_swing_at_a_warden_costs_energy():
    """031 §5: the walk is free, the fight is free to JOIN — the swing
    alone carries the whole tax, COST_WARDEN_STRIKE ⚡ each, flat on
    every floor. The wounds-stay-cut pool is what makes this fair: the
    gate is a multi-bar siege, not a single-bar sprint. A dry bar
    refuses the swing BEFORE the round is spent — no venom tick, no
    counter-blow, no round against the exchange budget."""
    p = _striker(1)
    _at_keep(p)
    before = state.energy_now(p)
    core.apply_choice(p, "strike")
    assert state.energy_now(p) == before, "joining the fight is free"
    core.apply_choice(p, "close_in")     # the crossing is not a swing
    at_close = state.energy_now(p)
    assert at_close == before
    core.apply_choice(p, "attack")
    assert state.energy_now(p) == at_close - economy.COST_WARDEN_STRIKE

    # dry bar: the swing is refused and nothing else is spent
    p["energy_val"] = 0
    hp = p["hp"]
    rounds = p["encounter"].get("rounds", 0)
    s = core.apply_choice(p, "attack")
    assert p.get("encounter") is not None
    assert p["hp"] == hp, "a refused swing must not eat a counter-blow"
    assert p["encounter"].get("rounds", 0) == rounds
    assert "⚡" in " ".join(s.body_lines)


@pytest.mark.parametrize("level", [1, 4, 6, 10, 20])
def test_nobody_takes_a_gate_in_one_standing(level):
    """The other half of the law, and the half the round budget alone
    could not carry: a level-10 blade on the floor-1 gate deals three
    at-level fights' worth inside one 19-round exchange, so a 3.2-fight
    pool fell to a single charge. One charge may cut at most ONE fight
    unit — over-levelling buys efficiency (fewer rounds, less blood, less
    risk), never the gate itself."""
    p = _striker(level)
    _at_keep(p)
    pool = p["_world"]["warden"]["hp"]
    core.apply_choice(p, "strike")
    _swing_until_it_ends(p)
    dealt = next(x["damage"] for x in p["_effects"]
                 if x["kind"] == "warden_strike")
    assert dealt < pool, f"one charge emptied the whole gate ({dealt}/{pool})"
    # the unit, plus at most the one blow that crossed it
    assert dealt <= 2 * economy.pool_unit(1), (level, dealt)


def test_a_gate_costs_at_least_three_charges_from_anyone():
    """3.2 fight-units deep means 3.2 charges — ~10 ⚡, a half-bar, for the
    strongest blade in the tower as much as for the weakest."""
    for level in (1, 6, 20):
        p = _striker(level)
        charges = 0
        while (p["_world"]["warden"]["hp"] > 0) and charges < 20:
            _at_keep(p)
            p["hp"] = state.max_hp(p)          # count charges, not deaths
            p["energy_val"] = 24
            core.apply_choice(p, "strike")
            _swing_until_it_ends(p)
            charges += 1
        assert charges >= 3, (level, charges)


def test_a_local_bout_is_not_bounded_only_the_shared_gate_is():
    """The cap is the shared pool's law — one charge, one fight-unit of a
    body that remembers. A personal/echo bout has no pool to measure and
    no world effect, so it still runs to a conclusion."""
    p = _striker(1, world=False)
    _at_keep(p)
    core.apply_choice(p, "strike")
    assert p.get("encounter") is not None
    assert not p["encounter"].get("shared")
    _swing_until_it_ends(p)
    assert p.get("encounter") is None


# ── B. the chase came back ───────────────────────────────────────────────

def test_a_warden_always_gets_a_chance_to_follow_you_out():
    """Speed decides the getaway everywhere in the tower; against a gate
    it only ever improves your odds to 3-in-4."""
    fast = economy.SPEED_NORMAL + 6
    assert economy.p_flee(fast, economy.SPEED_NORMAL) > economy.WARDEN_FLEE_MAX
    assert 0.0 < economy.WARDEN_FLEE_MAX < 1.0
    p = _striker(10)
    _at_keep(p)
    core.apply_choice(p, "strike")
    caught = 0
    for _ in range(40):
        if p.get("encounter") is None:
            _at_keep(p)
            p["energy_val"] = 24
            core.apply_choice(p, "strike")
        if p.get("encounter") is None:
            break
        p["hp"] = state.max_hp(p)          # we are counting escapes, not deaths
        p["encounter"]["rounds"] = 0       # ...and not exchanges either
        p["encounter"]["hp"] = p["encounter"]["hp_max"]
        s = core.apply_choice(p, "run")
        if p.get("encounter") is not None:
            caught += 1
            said = " ".join([s.support or ""] + list(s.body_lines or []))
            assert "cuts off your line" in said, said
    assert caught >= 4, f"a Warden let a climber walk 40 times ({caught})"


def test_a_caught_getaway_costs_real_blood_not_a_chip():
    """The price of the attempt — 6% of your own body at least, whatever
    you are wearing. This is the "sometimes it would follow you" the keep
    had lost."""
    p = _striker(10)
    _at_keep(p)
    core.apply_choice(p, "strike")
    least = economy.warden_grab_damage(state.max_hp(p))
    assert least > 1
    caught = 0
    for _ in range(40):
        if p.get("encounter") is None:
            # the getaway worked — walk back in and try again; the rolls
            # are day-seeded, so one lucky escape must not fail the test
            _at_keep(p)
            p["energy_val"] = 24
            core.apply_choice(p, "strike")
        if p.get("encounter") is None:
            break
        p["hp"] = state.max_hp(p)
        p["encounter"]["rounds"] = 0
        before = p["hp"]
        core.apply_choice(p, "run")
        if p.get("encounter") is not None:
            caught += 1
            assert before - p["hp"] >= least, (before - p["hp"], least)
            break
    assert caught, "40 attempts and it never once cut off the line"


def test_the_grab_scales_with_the_body_it_grabs():
    assert economy.warden_grab_damage(800) > economy.warden_grab_damage(80)
    assert economy.warden_grab_damage(80) == \
        round(economy.WARDEN_GRAB_SHARE * 80)
    assert economy.warden_grab_damage(1) >= 1


def test_the_wilds_keep_the_open_getaway():
    """The law is about war machines. A fast climber can still walk away
    from the grass at up to 95%, and nothing in the wilds grabs."""
    assert economy.p_flee(economy.SPEED_NORMAL + 6,
                          economy.SPEED_NORMAL) > economy.WARDEN_FLEE_MAX
    p = _striker(6, world=False)
    core.apply_choice(p, "gate")
    core.apply_choice(p, "floor_1")
    for _ in range(20):
        core.apply_choice(p, "hunt")
        e = p.get("encounter")
        if e is None:
            p["energy_val"] = 24
            continue
        assert e["kind"] == "wilds"
        assert "rounds" not in e or e["kind"] != "warden"
        rounds = _swing_until_it_ends(p, cap=60)
        assert rounds < 60, "a wilds fight must still run to a conclusion"
        break


# ── C. the wound is measured from where you joined it ────────────────────

def test_a_strike_reports_only_what_this_blade_cut():
    """Found while bounding the exchange, and much worse than the thing it
    was found next to: a shared fight reported `hp_max − hp`, and hp_max is
    the BODY'S SIZE, not where the blade joined. So a climber walking into
    a gate already cut to 200/426 was credited with the other 226 on his
    first swing — every wounded gate fell in one or two charges, whoever
    turned up."""
    p = _striker(1)
    p["_world"]["warden"]["hp"] = 200
    _at_keep(p)
    core.apply_choice(p, "strike")
    e = p["encounter"]
    assert e["hp"] == 200 and e["hp_max"] == 426    # the body is still 426
    core.apply_choice(p, "close_in")
    for _ in range(3):
        if p.get("encounter") is None:
            break
        core.apply_choice(p, "attack")
    while p.get("encounter") is not None:
        p["hp"] = state.max_hp(p)
        core.apply_choice(p, "run")
    dealt = next(x["damage"] for x in p.get("_effects", [])
                 if x["kind"] == "warden_strike")
    assert 0 < dealt <= 60, f"credited with the whole wound ({dealt})"


def test_the_bar_still_shows_the_body_not_the_visit():
    """The fix must not shrink the Warden in the fight card — the war bar,
    the scan and the "bites deep" line all read the body's real size."""
    p = _striker(1)
    p["_world"]["warden"]["hp"] = 200
    _at_keep(p)
    s = core.apply_choice(p, "strike")
    assert s.enemy["hp"] == 200
    assert s.enemy["hp_max"] == 426


# ── D. nothing tuned against the reference moved ─────────────────────────

def test_no_pool_and_no_win_rate_was_disturbed():
    """026 adds a round budget and a getaway ceiling. It must not have
    moved a single number the 022/024 gates were tuned on — the walls
    standing in production stay exactly as deep as the climbers left
    them, and no tune stamp has to churn."""
    assert economy.WARDEN_POOL_TUNE == 3
    assert economy.world_warden_hp(1) == 426
    assert economy.pool_unit(1) == 133
    assert 3 <= economy.world_warden_hp(1) / economy.pool_unit(1) <= 4


def test_the_effort_curve_is_still_one_straight_line():
    effort = [economy.world_warden_hp(f) / economy.pool_unit(f)
              for f in range(1, 31)]
    assert effort == sorted(effort), effort


def test_the_exchange_never_shortens_below_a_real_fight():
    """A charge that bought two rounds would be a swindle at 3 ⚡."""
    for floor in range(1, 101):
        assert economy.warden_exchange_rounds(floor) >= 5, floor
