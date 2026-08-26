"""082 phase-1: Labs floormap — the camp menu drawn as the floor's map."""
from plugin_linear_ascent import render
from plugin_linear_ascent.engine import core, floormap, labs, state
from plugin_linear_ascent.engine.scene import Scene

from tests.conftest import make_character


def _at_camp(uid="u-map"):
    p = state.new_player(uid)
    make_character(p)
    core.apply_choice(p, "gate")
    s = core.apply_choice(p, "floor_1")
    while p.get("movie_floor"):
        s = core.apply_choice(p, "1")
    return p, s


def test_flag_off_scene_unchanged():
    p, s = _at_camp("u-off")
    assert s.map is None
    assert s.to_dict()["map"] is None
    ids = [o.id for o in s.options]
    assert "hunt" in ids and "gate" in ids and "town" in ids


def test_flag_on_floor1_maps_the_menu():
    p, s = _at_camp("u-on")
    core.apply_choice(p, "labs")
    core.apply_choice(p, "labs_toggle_floormap")
    s = core.apply_choice(p, "labs_back")
    assert s.map is not None
    assert s.map["art"] == "map_001"
    ids = {o.id for o in s.options}
    marker_opts = [m["opt"] for m in s.map["markers"]]
    # every marker is a live option; no duplicates
    assert set(marker_opts) <= ids
    assert len(marker_opts) == len(set(marker_opts))
    # the core five places ride the map
    for oid in ("gate", "town", "talk", "keep", "hunt"):
        assert oid in marker_opts
    # floor 1 has no deep hunt — no dead marker
    assert "hunt_deep" not in marker_opts


def test_cost_on_chip_rule():
    p, s = _at_camp("u-cost")
    labs.set_flag(p, "floormap", True)
    s = core.current_scene(p)
    mk = {m["opt"]: m for m in s.map["markers"]}
    assert mk["hunt"]["cost"] == "1 ⚡"
    assert mk["hunt"]["ck"] == "en"
    # the Warden's keep prices the swing on its own screen — no cost chip
    assert "cost" not in mk["keep"]
    assert mk["keep"]["label"] == "BRACKJAW"


def test_floor_gate_and_toggle_off():
    p, s = _at_camp("u-gate")
    labs.set_flag(p, "floormap", True)
    assert core.current_scene(p).map is not None
    # feature is gated to floor 1
    assert not labs.enabled(p, "floormap", 2)
    fl2 = type("F", (), {"floor": 2, "warden_name": "X"})()
    assert floormap.payload(p, fl2, core.current_scene(p).options) is None
    labs.set_flag(p, "floormap", False)
    assert core.current_scene(p).map is None


def test_hurt_player_heals_stay_rows():
    p, s = _at_camp("u-hurt")
    labs.set_flag(p, "floormap", True)
    p["hp"] = 1
    s = core.current_scene(p)
    ids = {o.id for o in s.options}
    assert "stew" in ids and "heal" in ids
    marker_opts = {m["opt"] for m in s.map["markers"]}
    assert "stew" not in marker_opts and "heal" not in marker_opts


def test_map_rides_the_wire_round_trip():
    p, s = _at_camp("u-wire")
    labs.set_flag(p, "floormap", True)
    s = core.current_scene(p)
    d = s.to_dict()
    assert d["map"]["art"] == "map_001"
    back = Scene.from_dict(d)
    assert back.map == s.map
    # an old-client dict without the key stays None
    d2 = dict(d)
    del d2["map"]
    assert Scene.from_dict(d2).map is None


def test_render_chip_or_row_never_both():
    p, s = _at_camp("u-render")
    labs.set_flag(p, "floormap", True)
    p["hp"] = 1                      # force leftover rows too
    s = core.current_scene(p)
    html = render.render_scene_fragment(s)
    assert 'class="mapwrap' in html
    for o in s.options:
        assert html.count(f'data-opt="{o.id}"') == 1, o.id
    # mapped chips are .mk buttons, leftovers are .opt rows
    assert 'class="mk"' in html
    mk = {m["opt"]: m for m in s.map["markers"]}
    assert "1 ⚡" in mk["hunt"]["cost"]
    labs.set_flag(p, "floormap", False)
    html_off = render.render_scene_fragment(core.current_scene(p))
    assert 'class="mapwrap' not in html_off and 'class="mk"' not in html_off


def test_labs_card_lists_floor_maps():
    p, s = _at_camp("u-card")
    s = core.apply_choice(p, "labs")
    ids = [o.id for o in s.options]
    assert "labs_toggle_floormap" in ids
    row = next(o for o in s.options if o.id == "labs_toggle_floormap")
    assert "Floor maps" in row.label
    assert "floors 1" in row.hint
