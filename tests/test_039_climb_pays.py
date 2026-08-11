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
    choose(p, text=name)
    # 048: the class question is gone — restore the old class FEEL by
    # hand: the path at rank 6 plus that line's basic weapon in hand.
    _path = {"warrior": "blade", "archer": "bow",
             "sorcerer": "staff"}[clazz]
    _slug = {"warrior": "rusted_sword", "archer": "basic_bow",
             "sorcerer": "worn_staff"}[clazz]
    p["training"][_path] = 6
    p["gear"]["weapon"] = _slug
    p["held"] = [_slug]
    return p


def at_gate_town(p, floor=1):
    p["unlocked_floor"] = max(p.get("unlocked_floor", 1), floor)
    p["level"] = max(p["level"], economy.floor_entry_player_level(floor))
    choose(p, "gate")
    return choose(p, f"floor_{floor}")


def pin_specimen(monkeypatch, specimen="common"):
    real = state.rng_pick
    monkeypatch.setattr(state, "rng_pick", lambda p, table: (
        specimen if any(k in economy.SPECIMENS for _, k in table)
        else real(p, table)))


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


# ── the bar clamp (043: it replaced the reward-cap ladder) ───────────────

def test_the_bar_offset_is_clamped_to_the_promise():
    """043: toughness is priced once, by the bar, and the offset clamp
    [−2, +1] IS the old reward cap — the richest draw on a floor can
    only ever be one bar up, so it can never invent pay from nowhere."""
    assert economy.bar_offset(()) == 0
    assert economy.bar_offset(("frail", "feeble")) == -2
    assert economy.bar_offset(("lean", "feeble")) == -2
    assert economy.bar_offset(("hulking", "savage")) == 1   # 2, clamped
    assert economy.BAR_OFFSET_MIN == -2 and economy.BAR_OFFSET_MAX == 1
    for body in ("frail", "lean", "sturdy", "hulking", ""):
        for bite in ("feeble", "fierce", "savage", ""):
            traits = tuple(t for t in (body, bite) if t)
            assert -2 <= economy.bar_offset(traits) <= 1, traits
    # the ladder is floored and capped: floor 1 has no bar-0 prey, and
    # nothing stands above the floor-101 loadout
    assert economy.creature_bar(1, ("frail", "feeble")) == 1
    assert economy.creature_bar(101, ("hulking", "savage")) \
        == economy.BAR_MAX


def test_one_lucky_draw_never_outpays_the_warden_in_the_live_bands():
    """gold_per_kill(F+1) < warden_gold(F) through floor 20 — the clamp
    makes the old cap structural. Past floor 20 the band income jump has
    always outrun warden_gold (pre-existing) — the gate tracks it."""
    for f in range(1, 21):
        assert economy.gold_per_kill(f + 1) < economy.warden_gold(f), f


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
            bar = economy.creature_bar(f, e.traits or ())
            total += w
            pay += w * economy.gold_per_kill(bar) * spec_e
        return pay / total

    assert ev(6) >= 2 * ev(1), (ev(1), ev(6))
    # and the bottom rises with the floor: floor 6's worst possible kill
    # (lowest-bar draw, runt) beats floor 1's worst by ≥ 50%
    def worst(f):
        fl = schema.get_floor(f)
        return min(economy.gold_per_kill(economy.creature_bar(
            f, e.traits or ())) for e in fl.encounters) \
            * economy.SPECIMENS["runt"]["gold"]
    assert worst(6) >= 1.5 * worst(1), (worst(1), worst(6))


# ═══ phase 2 — the deep hunt (⚡2, floor 4+) ═════════════════════════════

def test_deep_option_absent_on_floor_three_present_on_four():
    p = create_character(fresh("039-gate3"))
    s = at_gate_town(p, 3)
    assert not any(o.id == "hunt_deep" for o in s.options)
    p2 = create_character(fresh("039-gate4"))
    s = at_gate_town(p2, 4)
    row = next(o for o in s.options if o.id == "hunt_deep")
    assert "2 ⚡" in row.hint                     # the price is on the row


def test_deep_hunt_spends_two_and_marks_the_encounter():
    p = create_character(fresh("039-spend"))
    at_gate_town(p, 5)
    before = state.energy_now(p)
    choose(p, "hunt_deep")
    assert before - state.energy_now(p) == economy.COST_WILDS_DEEP == 2
    e = p["encounter"]
    assert e is not None and e["deep"] is True
    assert "never hunted thin" in e["prose"]     # the opener says so
    assert {"kind": "energy", "gold": 0, "xp": 0,
            "note": "wilds deep"} in p["_ledger"]


def test_deep_hunt_refuses_short_energy_without_lying():
    p = create_character(fresh("039-short"))
    at_gate_town(p, 5)
    p["energy_val"] = 1                          # short for deep, not spent
    p["energy_ts"] = state.now().isoformat()
    s = choose(p, "hunt_deep")
    assert p.get("encounter") is None
    assert state.energy_now(p) == 1              # nothing was taken
    assert "⚡ 2" in s.shard_note


def test_deep_table_drops_prey_and_skips_the_rubber_band(monkeypatch):
    monkeypatch.setattr(combat, "would_probably_kill",
                        lambda p, fl, e: True)   # band would cut EVERYTHING
    p = create_character(fresh("039-deeptable"))
    fl = schema.get_floor(6)
    table = dict((slug, w) for w, slug in combat.hunt_table(p, fl, deep=True))
    for e in fl.encounters:
        if {"feeble", "frail"} & set(e.traits or ()):
            assert e.id not in table, f"prey {e.id} drawn on a deep hunt"
        else:
            assert table[e.id] == e.weight * 100  # full weight — no mercy


def test_deep_specimens_have_no_runts():
    assert economy.DEEP_SPECIMENS["runt"]["weight"] == 0
    assert sum(s["weight"] for s in economy.DEEP_SPECIMENS.values()) == 100
    for k, s in economy.DEEP_SPECIMENS.items():   # mults/tags shared
        base = economy.SPECIMENS[k]
        assert all(s[key] == base[key] for key in ("hp", "atk", "gold", "tag"))
    # 300 seeded deep draws: never a runt, never a feeble opponent
    for i in range(300):
        p = create_character(fresh(f"039-draw-{i}"))
        p["unlocked_floor"], p["floor"] = 6, 6
        fl = schema.get_floor(6)
        enc_id = state.rng_pick(p, combat.hunt_table(p, fl, deep=True))
        enc = next(e for e in fl.encounters if e.id == enc_id)
        assert not {"feeble", "frail"} & set(enc.traits or ())
        combat.start_encounter(p, fl, enc, "wilds", deep=True)
        assert p["encounter"]["specimen"] != "runt", i


def test_deep_primes_atk_and_speed_never_hp(monkeypatch):
    pin_specimen(monkeypatch, "common")
    fl = schema.get_floor(5)
    enc = next(e for e in fl.encounters if "feeble" not in (e.traits or ()))

    def fight(deep):
        p = create_character(fresh(f"039-prime-{deep}"))
        p["unlocked_floor"] = 5
        combat.start_encounter(p, fl, enc, "wilds", deep=deep)
        e = p["encounter"]
        return e["atk"], e["profile"]["speed"], e["hp"]

    atk0, spd0, hp0 = fight(False)
    atk1, spd1, hp1 = fight(True)
    assert atk1 == round(atk0 * economy.DEEP_ATK_MULT)
    assert spd1 == spd0 + economy.DEEP_SPEED_BONUS
    assert hp1 == hp0, "deep must scare, not stall — HP never moves"


def test_deep_pays_the_premium_and_the_dossier_promises_it(monkeypatch):
    pin_specimen(monkeypatch, "common")
    monkeypatch.setattr(state, "rng_jitter", lambda p, base, pct: base)
    fl = schema.get_floor(5)
    enc = schema.Encounter(id="_d", name="Thing", weight=1,
                           prose="A thing arrives.", traits=())

    def kill(deep):
        p = create_character(fresh(f"039-pay-{deep}"))
        p["training"]["blade"] = 10   # 048: the probe is the payout —
        p["unlocked_floor"], p["level"] = 5, 10   # room in the XP bar
        combat.start_encounter(p, fl, enc, "wilds", deep=deep)
        promised = combat._drop_ranges(p, fl)
        p["encounter"]["range"] = "close"
        p["encounter"]["hp"] = 1
        g0, x0 = p["gold"], p["xp"]
        combat.resolve_fight_action(p, fl, "attack")
        return p["gold"] - g0, p["xp"] - x0, promised

    gold0, xp0, prom0 = kill(False)
    gold1, xp1, prom1 = kill(True)
    mult = economy.deep_reward_mult(5)
    assert gold1 == round(gold0 * mult)
    assert xp1 == round(xp0 * mult)
    # the dossier's promise scales with the payout — same math, no drift
    assert prom1["gold"][0] == round(prom0["gold"][0] * mult)
    assert prom1["gold"][1] == round(prom0["gold"][1] * mult)
    assert prom0["gold"][0] <= gold0 <= prom0["gold"][1]
    assert prom1["gold"][0] <= gold1 <= prom1["gold"][1]


def test_normal_hunt_is_untouched_by_the_deep_flag():
    p = create_character(fresh("039-normal"))
    at_gate_town(p, 5)
    before = state.energy_now(p)
    choose(p, "hunt")
    assert before - state.energy_now(p) == economy.COST_WILDS_FIGHT == 1
    assert p["encounter"]["deep"] is False
