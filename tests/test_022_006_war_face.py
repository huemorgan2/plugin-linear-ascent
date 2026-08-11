"""022/006 — the war's face: the siege legible at a glance.

Card-side tests: the HP bar, the countdown, the hour roll, faction
standings, the pity line watermark, the horn's gating and dedupe, and
the gate's "the war is on floor N" line. The server half (threshold
Crier lines, horn letters, Stone lines) lives in worldd's
test_war_face.py.
"""

import datetime as dt

from plugin_linear_ascent import economy
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import core, social, state


def fresh():
    return state.new_player("test-user-022-006")


def choose(p, option="", text=""):
    return core.apply_choice(p, option, text)


def create_character(p, race="human", clazz="warrior", name="Testa"):
    core.current_scene(p)
    while p["stage"] == "intro":
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


def _ago(minutes):
    return (state.now() - dt.timedelta(minutes=minutes)).isoformat()


def wounded_warden(p, floor=1, hp=430, hp_max=1000, pity=0,
                   closes_in_s=11520, strikers=None):
    p["_world"] = {
        "frontier": floor,
        "census": {"total": 5, "by_floor": {str(floor): 3}},
        "warden": {
            "floor": floor, "hp": hp, "hp_max": hp_max, "pity": pity,
            "closes_in_s": closes_in_s,
            "strikers": strikers if strikers is not None else [
                {"name": "Kettle", "dmg": 320, "ts": _ago(10),
                 "guild": "House Ash"},
                {"name": "Brakka", "dmg": 180, "ts": _ago(50),
                 "guild": "House Oak"},
                {"name": "Vex", "dmg": 70, "ts": _ago(200),
                 "guild": "House Ash"},
            ]},
    }
    return p


def keep_scene(p, floor=1):
    return social.warden_scene(p, schema.get_floor(floor))


# ── The card ─────────────────────────────────────────────────────────────

def test_card_shows_bar_countdown_roll_and_standings():
    # 025 §3: floors 1-10 are siege floors with no silence window at all,
    # so the countdown line lives above the siege band now.
    p = wounded_warden(create_character(fresh()), floor=12)
    s = keep_scene(p, floor=12)
    body = "\n".join(s.body_lines)
    assert "43%" in body and "430" in body
    assert "█" in body and "·" in body
    assert "the wound closes in 3h 12m — keep striking" in body
    # the hour roll: Kettle and Brakka struck inside the hour, Vex not
    assert "Kettle, Brakka struck this hour" in body
    # standings: House Ash 390 > House Oak 180
    ash = body.index("House Ash — 390 cut")
    oak = body.index("House Oak — 180 cut")
    assert ash < oak


def test_bar_never_lies_at_the_edges():
    assert social._war_bar(1000, 1000) == "█" * 10
    assert social._war_bar(0, 1000) == "·" * 10
    assert social._war_bar(5, 1000).count("█") == 1     # alive shows
    assert social._war_bar(995, 1000).count("·") == 1   # wounded shows


def test_full_warden_has_no_countdown():
    p = wounded_warden(create_character(fresh()), hp=1000, hp_max=1000,
                       closes_in_s=None, strikers=[])
    s = keep_scene(p)
    body = "\n".join(s.body_lines)
    assert "closes in" not in body
    assert "first strike is yours" in body


def test_wound_close_writes_the_pity_line_once():
    p = wounded_warden(create_character(fresh()))
    keep_scene(p)                                   # watermark pity 0
    p["_world"]["warden"].update(hp=970, hp_max=970, pity=1,
                                 closes_in_s=None)
    s = keep_scene(p)
    body = "\n".join(s.body_lines)
    assert "The wound has CLOSED" in body
    assert "3%" in body
    assert "healed 1 time" in body                  # the standing scar
    s = keep_scene(p)                               # seen — no repeat
    assert "The wound has CLOSED" not in "\n".join(s.body_lines)


# ── The horn ─────────────────────────────────────────────────────────────

def test_horn_needs_a_banner_and_an_open_wound():
    p = wounded_warden(create_character(fresh()))
    s = keep_scene(p)
    assert not any(o.id == "horn" for o in s.options)   # no guild
    p["guild"] = "House Ash"
    s = keep_scene(p)
    assert any(o.id == "horn" for o in s.options)
    p["_world"]["warden"].update(hp=1000, hp_max=1000)  # wound closed
    s = keep_scene(p)
    assert not any(o.id == "horn" for o in s.options)


def test_horn_emits_once_per_wound():
    p = wounded_warden(create_character(fresh()))
    p["guild"] = "House Ash"
    fl = schema.get_floor(1)
    s = social.warden_action(p, fl, "horn")
    assert any(e["kind"] == "horn" and e["floor"] == 1
               for e in p.get("_effects", []))
    assert any("horn rings" in ln for ln in s.body_lines)
    n = len(p["_effects"])
    s = social.warden_action(p, fl, "horn")             # re-tap
    assert len(p.get("_effects", [])) == n              # nothing new
    assert any("has sounded" in ln for ln in s.body_lines)
    # a NEW wound (pity moved) frees the horn again
    p["_world"]["warden"]["pity"] = 1
    social.warden_action(p, fl, "horn")
    assert len(p["_effects"]) == n + 1


# ── The gate and the Crier ───────────────────────────────────────────────

def test_gate_names_the_war_when_a_wound_is_open():
    p = wounded_warden(create_character(fresh()))
    choose(p, "gate")
    s = core.current_scene(p)
    assert any("the war is on floor 1" in ln and "43%" in ln
               for ln in s.body_lines)
    p["_world"]["warden"].update(hp=1000)               # whole again
    s = core._gate_scene(p)
    assert not any("the war is on" in ln for ln in s.body_lines)


def test_crier_carries_the_countdown():
    p = wounded_warden(create_character(fresh()))
    w = p["_world"]
    paper = core._paper_payload(p, w, state.world_day())
    body = "\n".join(paper["items"])
    assert "43%" in body
    assert "closes in 3h 12m" in body      # 030 redo: headline-short
