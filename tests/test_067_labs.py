"""067 phase 1: Labs — the flag, the flask, the card."""
from plugin_linear_ascent import icons, pane, render
from plugin_linear_ascent.engine import core, labs, state
from plugin_linear_ascent.engine.scene import Scene

from tests.conftest import make_character


def _playing():
    p = state.new_player("u-labs")
    make_character(p)
    return p


def test_new_doc_has_labs_and_old_doc_heals():
    p = state.new_player("u1")
    assert p["labs"] == {}
    q = state.new_player("u2")
    del q["labs"]
    state.ensure_current(q)
    assert q["labs"] == {}
    q["labs"] = "junk"
    state.ensure_current(q)
    assert q["labs"] == {}


def test_enabled_respects_floor_gate():
    p = state.new_player("u3")
    assert not labs.enabled(p, "arena")
    labs.set_flag(p, "arena", True)
    assert labs.enabled(p, "arena")
    assert labs.enabled(p, "arena", 6) and labs.enabled(p, "arena", 7)
    assert not labs.enabled(p, "arena", 5)
    assert not labs.enabled(p, "arena", 8)
    assert not labs.enabled(p, "nope")


def test_labs_card_toggles_and_returns():
    p = _playing()
    s = core.apply_choice(p, "labs")
    assert s.headline == "The Labs"
    ids = [o.id for o in s.options]
    assert "labs_toggle_arena" in ids and "labs_back" in ids
    row = next(o for o in s.options if o.id == "labs_toggle_arena")
    assert row.label.endswith("off")
    assert s.labs == []
    s = core.apply_choice(p, "labs_toggle_arena")
    assert p["labs"]["arena"] is True
    row = next(o for o in s.options if o.id == "labs_toggle_arena")
    assert row.label.endswith("ON")
    assert s.labs == ["arena"]
    html = render.render_scene_fragment(s)
    assert 'data-labs="arena"' in html
    s = core.apply_choice(p, "labs_toggle_arena")
    assert p["labs"]["arena"] is False
    s = core.apply_choice(p, "labs_back")
    assert s.headline != "The Labs"
    assert not s.refusal


def test_labs_refused_mid_fight():
    p = _playing()
    core.apply_choice(p, "gate")
    core.apply_choice(p, "floor_1")
    if p.get("movie_floor"):
        core.apply_choice(p, "skip")
    core.apply_choice(p, "hunt")
    assert p["encounter"]
    s = core.apply_choice(p, "labs")
    assert s.refusal
    assert p["encounter"]


def test_wire_round_trip_keeps_labs_and_arena():
    s = Scene(eyebrow="x", headline="y", labs=["arena"], arena={"v": 1})
    d = s.to_dict()
    back = Scene.from_dict(d)
    assert back.labs == ["arena"] and back.arena == {"v": 1}
    d.pop("labs"); d.pop("arena")
    old = Scene.from_dict(d)
    assert old.labs == [] and old.arena is None


def test_pane_has_flask_button():
    html = pane.render_pane()
    assert 'id="labsbtn"' in html
    assert icons.icon_data_url("flask") in html
    assert "__laAct('labs')" in html
