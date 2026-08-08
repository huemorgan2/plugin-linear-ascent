"""039 — the climb pays.

The complaint, in the player's words: "in level 6 i'm hunting animals
that can give me the same gols as level 1. this is not the varience
needed. we need that higher levels are higher with variance that some
may kill you. and also give you bigger gains."

Phase 1 gates: from floor 4 the draw distribution itself hardens — prey
fades, runts thin out, the lethal-draw mercy loosens, the reward ceiling
climbs. Content yamls stay untouched and numberless.
"""

import pytest

from plugin_linear_ascent import economy
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat, core, state


def fresh(user="test-user-039"):
    return state.new_player(user)


def choose(p, option="", text=""):
    return core.apply_choice(p, option, text)


def create_character(p, race="human", clazz="warrior", name="Testa"):
    core.current_scene(p)
    while p["stage"] == "intro":                 # 016: through the movie
        choose(p, "1")
    choose(p, race)
    choose(p, clazz)
    choose(p, text=name)
    return p


# ── prey fade ────────────────────────────────────────────────────────────

def test_prey_mult_full_through_three_then_fades_to_a_quarter():
    for f in (1, 2, 3):
        assert economy.prey_weight_mult(f) == 1.0
    assert economy.prey_weight_mult(4) == pytest.approx(0.85)
    assert economy.prey_weight_mult(6) == pytest.approx(0.55)
    assert economy.prey_weight_mult(8) == pytest.approx(0.25)
    assert economy.prey_weight_mult(50) == pytest.approx(0.25)
    # monotone: the tower never sends MORE prey at altitude
    mults = [economy.prey_weight_mult(f) for f in range(1, 30)]
    assert mults == sorted(mults, reverse=True)


def test_hunt_table_fades_only_the_feeble(monkeypatch):
    """On floor 6, feeble-bite draws lose weight; everyone else keeps
    their full content weight (a healthy climber, no rubber band)."""
    monkeypatch.setattr(combat, "would_probably_kill",
                        lambda p, fl, e: False)
    p = create_character(fresh("039-fade"))
    fl = schema.get_floor(6)
    table = dict((slug, w) for w, slug in combat.hunt_table(p, fl))
    fade = economy.prey_weight_mult(6)
    for e in fl.encounters:
        want = e.weight * 100
        if "feeble" in (e.traits or ()):
            want = max(1, round(want * fade))
        assert table[e.id] == want, (e.id, e.traits)


def test_floor_one_table_is_unchanged(monkeypatch):
    monkeypatch.setattr(combat, "would_probably_kill",
                        lambda p, fl, e: False)
    p = create_character(fresh("039-f1"))
    fl = schema.get_floor(1)
    table = dict((slug, w) for w, slug in combat.hunt_table(p, fl))
    for e in fl.encounters:
        assert table[e.id] == e.weight * 100


# ── runt fade ────────────────────────────────────────────────────────────

def test_specimen_table_low_floors_are_the_008_table():
    for f in (1, 2, 3):
        assert economy.specimen_table(f) is economy.SPECIMENS


def test_specimen_weights_sum_to_100_and_runts_fade():
    runts = []
    for f in range(1, 15):
        t = economy.specimen_table(f)
        assert sum(s["weight"] for s in t.values()) == 100, f
        runts.append(t["runt"]["weight"])
    assert runts[:3] == [25, 25, 25]
    assert runts == sorted(runts, reverse=True)      # monotone fade
    assert runts[-1] == 8                            # floor 8+ floor
    # the freed weight goes to the paying end
    t8 = economy.specimen_table(8)
    assert t8["tough"]["weight"] > economy.SPECIMENS["tough"]["weight"]
    assert t8["alpha"]["weight"] > economy.SPECIMENS["alpha"]["weight"]


def test_specimen_mults_and_tags_never_move():
    """Only WEIGHTS are floor-shaped; hp/atk/gold mults and tags are the
    008 constants at every floor."""
    for f in (4, 6, 8, 20):
        for k, s in economy.specimen_table(f).items():
            base = economy.SPECIMENS[k]
            for key in ("hp", "atk", "gold", "tag"):
                assert s[key] == base[key], (f, k, key)


def test_specimen_gold_expectation_follows_the_designed_curve():
    """008's ≈1.0 holds through floor 3; at altitude the roll itself
    pays better — deliberately, monotonically, and boundedly."""
    e = [economy.specimen_gold_expectation(f) for f in range(1, 15)]
    for v in e[:3]:
        assert abs(v - 1.0) <= 0.05
    assert e == sorted(e)                            # monotone climb
    assert e[-1] <= 1.25                             # bounded drift


# ── rubber-band ladder ───────────────────────────────────────────────────

def test_rubber_band_loosens_with_altitude():
    assert economy.rubber_band_cut(1) == economy.RUBBER_BAND_CUT
    assert economy.rubber_band_cut(3) == economy.RUBBER_BAND_CUT
    assert economy.rubber_band_cut(4) == 0.35
    assert economy.rubber_band_cut(6) == 0.35
    assert economy.rubber_band_cut(7) == 0.50
    assert economy.rubber_band_cut(100) == 0.50
    cuts = [economy.rubber_band_cut(f) for f in range(1, 30)]
    assert cuts == sorted(cuts)                      # never re-tightens


def test_lethal_draws_keep_more_weight_on_high_floors(monkeypatch):
    """The same lethal draw keeps 20% of its weight on floor 1 and 50%
    on floor 7 — the tower stops apologizing."""
    monkeypatch.setattr(combat, "would_probably_kill",
                        lambda p, fl, e: True)
    p = create_character(fresh("039-band"))
    for f, cut in ((1, 0.20), (7, 0.50)):
        fl = schema.get_floor(f)
        table = dict((slug, w) for w, slug in combat.hunt_table(p, fl))
        fade = economy.prey_weight_mult(f)
        for e in fl.encounters:
            w = e.weight * 100
            if "feeble" in (e.traits or ()):
                w = max(1, round(w * fade))
            assert table[e.id] == max(1, round(w * cut)), (f, e.id)


# ── reward-cap ladder ────────────────────────────────────────────────────

def test_reward_cap_climbs_and_never_exceeds_the_archetype_ceiling():
    assert economy.reward_mult_cap(1) == 6.0
    assert economy.reward_mult_cap(3) == 6.0
    assert economy.reward_mult_cap(4) == 6.5
    assert economy.reward_mult_cap(6) == 7.5
    assert economy.reward_mult_cap(100) == 7.5
    caps = [economy.reward_mult_cap(f) for f in range(1, 40)]
    assert caps == sorted(caps)
    assert max(caps) == economy.REWARD_MULT_CAP_CEIL == 7.5
    # 7.5 sits just over hulking·savage = 7.2 — the ladder's top rung
    # uncaps every real archetype without inventing pay from nowhere
    assert max(economy.BODY_ROUNDS.values()) \
        * max(economy.BITE_PAY.values()) == pytest.approx(7.2)


def test_one_lucky_draw_never_outpays_the_warden_in_the_live_bands():
    """cap · gold_per_kill < warden_gold through floor 20. Past floor 20
    the band income jump has always outrun warden_gold (pre-existing,
    documented on reward_mult_cap) — the gate tracks, not hides, it."""
    for f in range(1, 21):
        assert (economy.reward_mult_cap(f) * economy.gold_per_kill(f)
                < economy.warden_gold(f)), f


def test_kill_reward_mult_is_floor_aware():
    hulk = ("hulking", "savage")
    assert economy.kill_reward_mult(1, hulk) == 6.0     # floor-1 cap binds
    assert economy.kill_reward_mult(6, hulk) == pytest.approx(7.2)
    # prey pays the same misery everywhere — the cap never binds it
    assert economy.kill_reward_mult(1, ("frail", "feeble")) \
        == economy.kill_reward_mult(9, ("frail", "feeble"))


# ── the headline number ──────────────────────────────────────────────────

def test_floor_six_expected_pay_leaves_floor_one_far_behind():
    """Coarse EV over the raw content roster (no rubber band, healthy
    climber): expected gold per draw on floor 6 ≥ 2× floor 1 already
    with opening bids; phase 3's sim owns the final ≥ 2.5×."""
    def ev(f):
        fl = schema.get_floor(f)
        fade = economy.prey_weight_mult(f)
        spec_e = economy.specimen_gold_expectation(f)
        total, pay = 0, 0.0
        for e in fl.encounters:
            w = e.weight * 100
            if "feeble" in (e.traits or ()):
                w = max(1, round(w * fade))
            threat = economy.kill_reward_mult(f, e.traits or ())
            total += w
            pay += w * economy.gold_per_kill(f) * threat * spec_e
        return pay / total

    assert ev(6) >= 2 * ev(1), (ev(1), ev(6))
    # and the bottom rises with the floor: floor 6's worst possible kill
    # (weakest threat draw, runt) beats floor 1's worst by ≥ 50%
    def worst(f):
        fl = schema.get_floor(f)
        return min(economy.kill_reward_mult(f, e.traits or ())
                   * economy.gold_per_kill(f) for e in fl.encounters) \
            * economy.SPECIMENS["runt"]["gold"]
    assert worst(6) >= 1.5 * worst(1), (worst(1), worst(6))
