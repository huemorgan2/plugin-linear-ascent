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


def test_enabled_respects_floor_gate(monkeypatch):
    # the arena graduated (100floors); the gate semantics live on via a
    # synthetic floor-gated feature
    monkeypatch.setitem(labs.FEATURES, "trial",
                        labs.Feature("trial", "Trial", "x", frozenset({6, 7})))
    p = state.new_player("u3")
    assert not labs.enabled(p, "trial")
    labs.set_flag(p, "trial", True)
    assert labs.enabled(p, "trial")
    assert labs.enabled(p, "trial", 6) and labs.enabled(p, "trial", 7)
    assert not labs.enabled(p, "trial", 5)
    assert not labs.enabled(p, "trial", 8)
    assert not labs.enabled(p, "nope")


def test_arena_graduated_out_of_labs():
    assert "arena" not in labs.FEATURES
    p = state.new_player("u3b")
    p["labs"]["arena"] = True          # stale key on an old player doc
    assert not labs.enabled(p, "arena")
    assert labs.enabled_keys(p) == []
    labs.set_flag(p, "arena", False)   # guard: unknown key is a no-op
    assert p["labs"]["arena"] is True


def test_labs_card_toggles_and_returns():
    p = _playing()
    s = core.apply_choice(p, "labs")
    assert s.headline == "The Labs"
    ids = [o.id for o in s.options]
    assert "labs_toggle_figure3d" in ids
    assert "labs_toggle_arena" not in ids            # graduated (100floors)
    assert "labs_back" in ids
    row = next(o for o in s.options if o.id == "labs_toggle_figure3d")
    assert row.label.endswith("off")
    assert s.labs == []
    s = core.apply_choice(p, "labs_toggle_figure3d")
    assert p["labs"]["figure3d"] is True
    row = next(o for o in s.options if o.id == "labs_toggle_figure3d")
    assert row.label.endswith("ON")
    assert s.labs == ["figure3d"]
    html = render.render_scene_fragment(s)
    assert 'data-labs="figure3d"' in html
    s = core.apply_choice(p, "labs_toggle_figure3d")
    assert p["labs"]["figure3d"] is False
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
