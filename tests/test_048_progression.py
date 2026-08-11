"""048 phase 6 — T5: the intended progression, through the engine.

The bake's closed-form gates (test_048_bake) pin the pace laws; these
sims walk the same script through the REAL scenes — town doors, forge
counters, School fees, defeat cards — so the paper game and the played
game are one game:

- the intended first ten floors: kill income at the leash pace funds
  the whole classroom script (bow, 2nd slot, staff, ranks 2/2/2)
  through the engine's own counters, and by floor 10 every monster
  has a FULL-damage answer in the pack;
- the specialist: training blade at the School whenever the bar
  affords it masters the weapon around body level 10 and the
  master's invitation fires;
- the wrong-weapon lesson: a bow into tower plate loses, and the
  defeat card names the sign and the weapons that answer.

Income is granted at the closed-form leash rate (gold_per_kill /
xp_per_kill per frontier kill, hard bar) — the engine prices are the
thing under test, not the fight rng. Level-up fees stay out of the
ledger: they are the standing sink funded by the wider economy
(contracts, wardens, specimens), exactly as in test_048_bake.
"""

import pytest

from plugin_linear_ascent import economy
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat, core, state


def choose(p, oid="", text=""):
    return core.apply_choice(p, oid, text)


def _classless(uid):
    """The real 048 open: intro, race, name — Rusted Sword, blade 2."""
    p = state.new_player(uid)
    core.current_scene(p)
    while p["stage"] == "intro":
        choose(p, "1")
    choose(p, "human")
    choose(p, "", "Prog")
    assert p["training"] == {"blade": 2, "bow": 0, "staff": 0}
    assert p["held"] == ["rusted_sword"]
    return p


def _to_forge(p):
    if p["location"] == "forge":
        return
    if p["location"] == "school":
        choose(p, "back")
    if p["location"] == "gate_town":
        choose(p, "town")
    choose(p, "forge")
    assert p["location"] == "forge"


def _to_school(p):
    if p["location"] == "school":
        return
    if p["location"] == "forge":
        choose(p, "back")
    if p["location"] == "town":
        choose(p, "gate")
        choose(p, "floor_1")
    choose(p, "school")
    assert p["location"] == "school"


def _grant_kill(p):
    """One frontier kill at the leash (floor = level): the paycheck
    lands, the XP fills the hard bar, overflow is discarded."""
    floor = p["level"]
    p["gold"] += economy.gold_per_kill(floor)
    p["xp"] = min(p["xp"] + economy.xp_per_kill(floor),
                  economy.xp_need(p["level"]))


def _level_up(p):
    """The leash step, fees waived (the standing sink lives outside
    this ledger — see the module docstring)."""
    p["xp"] -= economy.xp_need(p["level"])
    p["level"] += 1
    p["unlocked_floor"] = max(p["unlocked_floor"], p["level"])


def _owned_paths(p):
    return {economy.PATH_OF_LINE.get(economy.FORGE[s].line, "blade")
            for s in (list(p.get("held") or [])
                      + list(p.get("inventory") or {}))
            if s in economy.FORGE}


def test_the_intended_first_ten_floors():
    """N8's script, played: bow by ~3, 2nd slot, staff by ~5, ranks
    2/2/2 — every purchase through the real counter, funded by leash
    kills alone (plus the gate's ◈50), no farming, no wall."""
    p = _classless("048-t5-first-ten")
    landed = {}
    kills = 0
    while p["level"] < 11 and kills < 5_000:
        kills += 1
        _grant_kill(p)
        need = economy.xp_need(p["level"])
        # the script, in priority order, each step the moment the
        # engine's own gates (coin, bar room, slots) open for it
        if "bow" not in landed and p["gold"] >= economy.BASIC_WEAPON_PRICE:
            _to_forge(p)
            choose(p, "buy_basic_bow")
            assert "basic_bow" in (p["held"] + list(p["inventory"])), \
                "the counter refused a funded buy"
            landed["bow"] = p["level"]
        elif ("carry2" not in landed and "bow" in landed
                and economy.CARRY2_XP <= need
                and p["xp"] >= economy.CARRY2_XP
                and p["gold"] >= economy.CARRY2_GOLD):
            _to_school(p)
            choose(p, "buy_carry2")
            assert p["slots"] == 2, "the School refused a funded slot"
            landed["carry2"] = p["level"]
            _to_forge(p)
            choose(p, "wear_basic_bow")     # promote — free slot keeps both
            assert set(p["held"]) == {"rusted_sword", "basic_bow"}
        elif ("carry2" in landed
                and p["training"]["bow"] < 2
                and (cost := economy.train_xp(p["training"]["bow"] + 1))
                <= need and p["xp"] >= cost
                and p["gold"] >= economy.train_gold(
                    p["training"]["bow"] + 1, p["unlocked_floor"])):
            _to_school(p)
            want = p["training"]["bow"] + 1
            choose(p, "train_bow")
            assert p["training"]["bow"] == want
            landed[f"bow_rank{want}"] = p["level"]
        elif ("staff" not in landed and p["training"]["bow"] >= 2
                and p["gold"] >= economy.BASIC_WEAPON_PRICE):
            _to_forge(p)
            choose(p, "buy_worn_staff")
            assert "worn_staff" in p["inventory"], \
                "the counter refused a funded staff"
            landed["staff"] = p["level"]
        elif ("staff" in landed
                and p["training"]["staff"] < 2
                and (cost := economy.train_xp(p["training"]["staff"] + 1))
                <= need and p["xp"] >= cost
                and p["gold"] >= economy.train_gold(
                    p["training"]["staff"] + 1, p["unlocked_floor"])):
            _to_school(p)
            want = p["training"]["staff"] + 1
            choose(p, "train_staff")
            assert p["training"]["staff"] == want
            landed[f"staff_rank{want}"] = p["level"]
        elif p["xp"] >= need:
            _level_up(p)

    # the whole classroom, on schedule — the "~3"/"~5" of the plan are
    # ceilings; the bounty may land them earlier, never later
    assert landed.get("bow", 99) <= 3, landed
    assert landed.get("carry2", 99) <= 4, landed
    assert landed.get("staff", 99) <= 6, landed
    assert landed.get("staff_rank2", 99) <= 10, landed
    assert p["training"]["bow"] >= 2 and p["training"]["staff"] >= 2
    assert p["gold"] >= 0

    # and the point of it all: every monster on floors 1–10 now has a
    # FULL-damage answer among the weapons carried or packed
    owned = _owned_paths(p)
    assert owned == {"blade", "bow", "staff"}
    for n in range(1, 11):
        fl = schema.get_floor(n)
        for enc in fl.encounters:
            mtype = economy.type_from_traits(enc.traits)
            best = max(economy.TYPE_MULT[mtype][path] for path in owned)
            assert best == 1.0, (
                f"floor {n} {enc.id} ({mtype}): best owned answer "
                f"×{best} — the classroom kit left a hole")


def test_the_specialist_masters_blade_by_level_ten():
    """N3 through the School's own door: train blade whenever the bar
    affords the next rank — mastery lands around body level 10 and
    the master's invitation fires."""
    p = _classless("048-t5-specialist")
    p["gold"] = 10**6          # fees are not under test here — pace is
    kills = 0
    while p["training"]["blade"] < 10 and kills < 5_000:
        kills += 1
        _grant_kill(p)
        need = economy.xp_need(p["level"])
        nxt = p["training"]["blade"] + 1
        cost = economy.train_xp(nxt)
        if cost <= need and p["xp"] >= cost:
            _to_school(p)
            choose(p, "train_blade")
            assert p["training"]["blade"] == nxt, \
                "the School refused a funded rank"
        elif p["xp"] >= need:
            _level_up(p)
    assert p["training"]["blade"] == 10
    assert 9 <= p["level"] <= 12, (
        f"blade 10 landed at body level {p['level']} — "
        "mastery must be a level-10-sized achievement")
    assert p["flags"].get("invited_blade"), "the invitation never fired"


def test_the_school_door_opens_both_ways():
    """The T5 sim found the generic back-handler eating the School's
    door — the student was locked in. Back goes to the gate camp."""
    p = _classless("048-t5-door")
    _to_school(p)
    choose(p, "back")
    assert p["location"] == "gate_town"


def test_a_bow_into_plate_loses_and_the_card_teaches(monkeypatch):
    """The wrong-weapon lesson: arrows into the kings_guard's tower
    plate glance (×0.15); the climber falls, and the defeat card
    names the plate AND both weapons that answer it."""
    monkeypatch.setattr(state, "roll_ok", lambda p, prob: False)
    monkeypatch.setattr(state, "rng_int", lambda p, lo, hi: hi)
    p = _classless("048-t5-lesson")
    p["training"]["bow"] = 6
    p["gear"]["weapon"] = "basic_bow"
    p["held"] = ["basic_bow"]
    p["inventory"]["arrows"] = 30
    p["level"], p["unlocked_floor"] = 10, 10
    fl = schema.get_floor(10)
    enc = next(e for e in fl.encounters if e.id == "kings_guard")
    combat.start_encounter(p, fl, enc, "wilds")
    p["encounter"]["range"] = "close"
    s = None
    for _ in range(12):
        if not p["encounter"]:
            break
        p["hp"] = 1                      # the next hit lands the lesson
        s = combat.resolve_fight_action(p, fl, "attack")
    assert s is not None and s.event_kind == "death", \
        "the glancing bow somehow won"
    text = " ".join(list(s.body_lines or []) + [s.headline or "",
                                                s.support or ""])
    assert "plate turned your arrows" in text
    assert "Steel halves it" in text and "staff bites full" in text
