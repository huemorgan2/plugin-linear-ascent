"""075 — speed is not a shield: the chase never fully stops.

After a ranged or magic action the monster takes a pursuit phase: one
turn always, extra turns by the player's weapon (bow 90%/10%, magic
50%), each landing on p_pursue — a curve that decays with the player's
speed lead but never reaches zero. Flyers get no extra turns and cannot
be backed away from; the bow keeps full power against them at any
distance. Melee rounds keep the classic single close-attempt.
"""

import pytest

from plugin_linear_ascent import economy
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat, core, state, tips


def fresh(name):
    return state.new_player(name)


def create_character(p, race="human", clazz="archer", name="Chase"):
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1")
    core.apply_choice(p, race)
    core.apply_choice(p, clazz)
    core.apply_choice(p, "", text=name)
    _path = {"warrior": "blade", "archer": "bow",
             "sorcerer": "staff"}[clazz]
    _slug = {"warrior": "rusted_sword", "archer": "basic_bow",
             "sorcerer": "worn_staff"}[clazz]
    p["training"][_path] = 6
    p["gear"]["weapon"] = _slug
    p["held"] = [_slug]
    return p


def _player(clazz, floor_no, name):
    p = create_character(fresh(name), clazz=clazz, name=name)
    p["level"] = floor_no
    p["hp"] = economy.player_max_hp(floor_no)
    return p


def _enc(floor_no, enc_id):
    fl = schema.get_floor(floor_no)
    return fl, next(e for e in fl.encounters if e.id == enc_id)


def _start(p, fl, enc, flying=False, mspd=None):
    combat.start_encounter(p, fl, enc)
    e = p["encounter"]
    if flying:
        e["profile"] = economy.profile_from_traits(("fly",))
    if mspd is not None:
        e.setdefault("profile", dict(combat._profile(p)))
        e["profile"]["speed"] = mspd
    return e


# ── the curve ────────────────────────────────────────────────────────────

def test_p_pursue_cap_decay_and_floor():
    # as fast or faster: it keeps up
    assert economy.p_pursue(5, 5) == economy.PURSUE_CAP
    assert economy.p_pursue(3, 7) == economy.PURSUE_CAP
    # strictly decreasing with the lead, never zero
    vals = [economy.p_pursue(5 + a, 5) for a in range(0, 12)]
    assert all(a > b for a, b in zip(vals, vals[1:]))
    assert all(v > 0 for v in vals)
    # asymptotic to the floor, not below it
    assert economy.p_pursue(60, 5) == pytest.approx(economy.PURSUE_FLOOR,
                                                    abs=1e-6)
    assert economy.p_pursue(60, 5) > 0


def test_pursuit_extra_chances_by_weapon():
    assert economy.pursuit_extra_chances("ranged") == (0.90, 0.10)
    assert economy.pursuit_extra_chances("magic") == (0.50,)
    assert economy.pursuit_extra_chances("melee") == ()


# ── the pursuit phase ────────────────────────────────────────────────────

def test_melee_round_keeps_the_single_close_attempt(monkeypatch):
    p = _player("warrior", 1, "melee-chase")
    fl, enc = _enc(1, "grey_wolf")
    _start(p, fl, enc)
    p["encounter"]["gap"] = 3
    monkeypatch.setattr(state, "roll_ok", lambda pl, prob: True)
    combat._pursuit_phase(p)
    # one length only — melee rounds are untouched by 075
    assert p["encounter"]["gap"] == 2


def test_bow_pursuit_crosses_ground_and_strikes(monkeypatch):
    # every roll lands: 3 turns — close 1→0, then two strikes
    p = _player("archer", 1, "bow-chase")
    fl, enc = _enc(1, "grey_wolf")
    _start(p, fl, enc)
    p["encounter"]["gap"] = 1
    p["encounter"]["range"] = "at_range"
    hp0 = p["hp"]
    monkeypatch.setattr(state, "roll_ok", lambda pl, prob: True)
    monkeypatch.setattr(state, "rng_int", lambda pl, lo, hi: hi)
    note = combat._pursuit_phase(p)
    assert p["encounter"]["gap"] == 0
    assert p["encounter"]["range"] == "close"
    assert p["hp"] < hp0
    assert "reaches you" in note
    assert "catches up and hits you" in note


def test_second_pursuit_strike_is_quartered(monkeypatch):
    # the strike arithmetic, pinned directly on _monster_hit
    p = _player("archer", 1, "quarter")
    fl, enc = _enc(1, "grey_wolf")
    _start(p, fl, enc)
    p["encounter"]["range"] = "close"
    p["encounter"]["gap"] = 0
    monkeypatch.setattr(state, "rng_int", lambda pl, lo, hi: hi)
    monkeypatch.setattr(state, "roll_ok", lambda pl, prob: False)  # no dodge
    hp0 = p["hp"]
    h1 = combat._monster_hit(p, halved=True)
    h2 = combat._monster_hit(p, halved=True, quartered=True)
    assert h1["dmg"] > 0
    assert h2["dmg"] == h1["dmg"] // 2
    assert p["hp"] == hp0 - h1["dmg"] - h2["dmg"]


def test_pursuit_never_runs_once_in_reach(monkeypatch):
    # at close range the normal counter speaks — pursuit stays silent
    p = _player("archer", 1, "close-quiet")
    fl, enc = _enc(1, "grey_wolf")
    _start(p, fl, enc)
    p["encounter"]["range"] = "close"
    p["encounter"]["gap"] = 0
    monkeypatch.setattr(state, "roll_ok", lambda pl, prob: True)
    assert combat._pursuit_phase(p) == ""


def test_a_fatal_pursuit_strike_ends_the_fight(monkeypatch):
    p = _player("archer", 1, "fatal")
    fl, enc = _enc(1, "grey_wolf")
    _start(p, fl, enc)
    p["encounter"]["gap"] = 1
    p["encounter"]["range"] = "at_range"
    p["encounter"]["hp"] = 10_000
    p["hp"] = 1
    monkeypatch.setattr(state, "roll_ok", lambda pl, prob: True)
    monkeypatch.setattr(state, "rng_int", lambda pl, lo, hi: hi)
    combat.resolve_fight_action(p, fl, "attack")
    # the chase caught up and the blow landed — the death path ran
    # (death save: hp back to 1, encounter cleared)
    assert p["encounter"] is None
    assert p["daily"].get("death_save")


# ── flyers: the one exemption ────────────────────────────────────────────

def test_flyer_gets_no_extra_pursuit_turns(monkeypatch):
    p = _player("archer", 1, "fly-one-turn")
    fl, enc = _enc(1, "grey_wolf")
    _start(p, fl, enc, flying=True)
    p["encounter"]["gap"] = 3
    p["encounter"]["range"] = "at_range"
    monkeypatch.setattr(state, "roll_ok", lambda pl, prob: True)
    combat._pursuit_phase(p)
    # one turn only: 3 → 2, never the bow's 2nd/3rd
    assert p["encounter"]["gap"] == 2


def test_flyer_hides_and_refuses_the_distance_rows():
    p = _player("archer", 1, "fly-no-row")
    fl, enc = _enc(1, "grey_wolf")
    _start(p, fl, enc, flying=True)
    s = combat.fight_scene(p, fl)
    ids = [o.id for o in s.options]
    assert "create_distance" not in ids
    assert "open_distance" not in ids
    # a raw id is refused in plain words, no turn spent
    gap0, hp0 = p["encounter"].get("gap"), p["hp"]
    s2 = combat.resolve_fight_action(p, fl, "create_distance")
    assert any("in the air" in ln for ln in s2.body_lines)
    assert p["encounter"].get("gap") == gap0 and p["hp"] == hp0
    p["encounter"]["range"] = "close"
    p["encounter"]["gap"] = 0
    s3 = combat.resolve_fight_action(p, fl, "open_distance")
    assert any("in the air" in ln for ln in s3.body_lines)
    assert p["hp"] == hp0


def test_bow_hits_full_power_on_a_flyer_up_close(monkeypatch):
    dealt = {}
    for label, flying, gap in (("fly_close", True, 0),
                               ("fly_far", True, 1),
                               ("ground_close", False, 0)):
        p = _player("archer", 1, f"fly-dmg-{label}")
        fl, enc = _enc(1, "grey_wolf")
        _start(p, fl, enc, flying=flying)
        p["encounter"]["gap"] = gap
        p["encounter"]["range"] = "close" if gap == 0 else "at_range"
        p["encounter"]["hp"] = 10_000
        monkeypatch.setattr(state, "rng_int", lambda pl, a, b: b)
        monkeypatch.setattr(state, "roll_ok", lambda pl, prob: False)
        hp0 = p["encounter"]["hp"]
        combat.resolve_fight_action(p, fl, "attack")
        dealt[label] = hp0 - p["encounter"]["hp"]
    # vs a flyer the cramped-close penalty is waived: close == far
    assert dealt["fly_close"] == dealt["fly_far"]
    # vs a grounded monster the ×0.5 close penalty still applies
    assert dealt["ground_close"] < dealt["fly_close"]


# ── plain English gate ───────────────────────────────────────────────────

BANNED = ("bowwork", "give ground", "gap is armor", "parting blow",
          "speed tells", "kite", "length", "toll", " rake")


def test_no_jargon_in_the_touched_copy():
    from plugin_linear_ascent import render
    surfaces = [tips._TIPS[k] for k in
                ("close_in", "open_distance", "create_distance", "run")]
    surfaces += [render._TIP_SPD, render._TIP_KIND["fly"]]
    for text in surfaces:
        low = text.lower()
        for word in BANNED:
            assert word not in low, f"jargon {word!r} in: {text[:60]}…"
