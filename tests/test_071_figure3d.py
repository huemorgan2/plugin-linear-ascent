"""071: Labs figure3d — flag, payload, render hook, isolation."""
from plugin_linear_ascent import render
from plugin_linear_ascent.engine import core, figure3d, labs, state
from plugin_linear_ascent.engine.scene import Scene

from tests.conftest import make_character


def _playing(race="human"):
    p = state.new_player("u-fig")
    make_character(p)
    p["race"] = race
    return p


def test_off_by_default_no_payload():
    p = _playing()
    assert not labs.enabled(p, "figure3d")
    assert figure3d.payload(p) is None
    s = core.current_scene(p)
    assert s.figure3d is None
    html = render.render_scene_fragment(s)
    assert "data-figure3d" not in html
    assert "<canvas" not in html
    assert 'class="portrait later"' in html
    assert "figure3d-fallback" not in html


def test_on_stamps_payload_and_canvas():
    p = _playing("elf")
    labs.set_flag(p, "figure3d", True)
    assert labs.enabled(p, "figure3d")
    spec = figure3d.payload(p)
    assert spec["v"] == 1
    assert spec["race"] == "elf"
    assert spec["px"] == [100, 200]
    assert "worn" in spec and "weapon" in spec["worn"]
    s = core.current_scene(p)
    assert s.figure3d["race"] == "elf"
    html = render.render_scene_fragment(s)
    assert "data-figure3d" in html
    assert 'canvas class="portrait later figure3d"' in html
    assert "figure3d-fallback" in html
    assert "figure3d" in (s.labs or [])


def test_giant_uses_taller_grid():
    p = _playing("giant")
    labs.set_flag(p, "figure3d", True)
    assert figure3d.payload(p)["px"] == [140, 260]


def test_worn_paths_follow_the_slots():
    p = _playing("human")
    p["held"] = ["rusted_sword", "basic_bow"]
    p["gear"]["weapon"] = "rusted_sword"
    p["gear"]["shoes"] = "cobbled_boots"
    p["gear"]["charm"] = "luck_charm"
    p["charm_slot"] = True
    p["slots"] = 2
    labs.set_flag(p, "figure3d", True)
    spec = figure3d.payload(p)
    assert spec["worn"]["weapon"] == "rusted_sword"
    assert spec["worn"]["weapon2"] == "basic_bow"
    assert spec["worn"]["shoes"] == "cobbled_boots"
    assert spec["worn"]["charm"] == "luck_charm"
    assert spec["paths"]["rusted_sword"] == "blade"
    assert spec["paths"]["basic_bow"] == "bow"
    assert spec["paths"]["cobbled_boots"] == "shoes"
    assert spec["paths"]["luck_charm"] == "charm"
    assert spec["lead"] == "rusted_sword"


def test_wire_round_trip():
    s = Scene(eyebrow="x", headline="y", figure3d={"v": 1, "race": "elf"})
    back = Scene.from_dict(s.to_dict())
    assert back.figure3d == {"v": 1, "race": "elf"}
    d = s.to_dict()
    d.pop("figure3d")
    assert Scene.from_dict(d).figure3d is None


def test_labs_card_has_the_row():
    p = _playing()
    s = core.apply_choice(p, "labs")
    ids = [o.id for o in s.options]
    assert "labs_toggle_figure3d" in ids
    s = core.apply_choice(p, "labs_toggle_figure3d")
    assert p["labs"]["figure3d"] is True
    row = next(o for o in s.options if o.id == "labs_toggle_figure3d")
    assert row.label.endswith("ON")
