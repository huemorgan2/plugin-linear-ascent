"""085: standard floormap — the camp menu drawn as the floor's map."""
import pytest
from PIL import Image

from plugin_linear_ascent import render
from plugin_linear_ascent.content import schema
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


def test_map_is_standard_without_a_flag():
    p, s = _at_camp("u-off")
    assert s.map["art"] == "map_001"
    assert s.to_dict()["map"]["art"] == "map_001"
    ids = [o.id for o in s.options]
    assert "hunt" in ids and "gate" in ids and "town" in ids


def test_floor1_maps_only_live_actions():
    p, s = _at_camp("u-on")
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
    s = core.current_scene(p)
    mk = {m["opt"]: m for m in s.map["markers"]}
    assert mk["hunt"]["cost"] == "1 ⚡"
    assert mk["hunt"]["ck"] == "en"
    # the Warden's keep prices the swing on its own screen — no cost chip
    assert "cost" not in mk["keep"]
    assert mk["keep"]["label"] == "BRACKJAW"
    # phase-1b: the base town by its NAME, standing at the tower's foot
    assert mk["town"]["label"] == "ROOTHOLLOW"


def test_chip_cost_wears_pixel_bolt_not_emoji():
    # phase-1c: the chip cost paints the 1-bit bolt glyph like every
    # other energy amount — the raw emoji never reaches the screen.
    p, s = _at_camp("u-bolt")
    s = core.current_scene(p)
    html = render.render_scene_fragment(s)
    i = html.index('class="mkcost')
    frag = html[i:html.index("</span>", i)]
    assert "⚡" not in frag
    assert 'class="eg"' in frag


def test_npc_scene_keeps_rows_no_map():
    # phase-1b bug fix: the Hobb card must NOT re-render the map — its
    # rows are the same _gate_town_options and all got mapped away,
    # locking the player on a card with no menu.
    p, s = _at_camp("u-npc")
    s = core.apply_choice(p, "talk")
    assert s.map is None
    html = render.render_scene_fragment(s)
    assert 'class="mapwrap' not in html
    assert html.count('class="opt') >= 3   # the plain rows are back


def test_mapped_card_sheds_art_and_prose():
    # phase-1b: the mapped card IS the map — no banner, no headline,
    # no support/body prose; the eyebrow bar stays, under the map.
    p, s = _at_camp("u-shed")
    s = core.current_scene(p)
    html = render.render_scene_fragment(s)
    assert 'class="mapwrap' in html
    assert 'class="banner"' not in html
    assert 'class="headline' not in html
    assert 'class="support' not in html
    assert 'class="body' not in html
    assert 'class="eyebrow' in html
    assert html.index('class="mapwrap') < html.index('class="eyebrow')


@pytest.mark.parametrize("floor", range(1, 11))
@pytest.mark.parametrize("legacy_flag", [None, False, True])
def test_all_ten_floors_ignore_legacy_flag(floor, legacy_flag):
    p, _ = _at_camp(f"u-{floor}-{legacy_flag}")
    if legacy_flag is not None:
        p["labs"] = {"floormap": legacy_flag}
    p.update(floor=floor, location="gate_town", level=99, unlocked_floor=11)
    s = core.current_scene(p)
    assert s.map["art"] == f"map_{floor:03d}"
    markers = {m["opt"]: m for m in s.map["markers"]}
    assert set(markers) <= {o.id for o in s.options}
    assert ("hunt_deep" in markers) == (floor >= 4)
    assert markers["keep"]["label"] == schema.load_floors()[floor].warden_name.removeprefix("Warden ").split(",")[0].upper()
    if floor > 1:
        assert schema.load_floors()[floor].gate_town in markers["talk"]["tip"]
    html = render.render_scene_fragment(s)
    assert 'class="mapwrap' in html
    assert 'width="492" height="369"' in html
    for i, o in enumerate(s.options, 1):
        assert html.count(f'data-opt="{o.id}"') == 1
        if o.id in markers:
            assert f'aria-describedby="map-tip-{o.id}"' in html
            assert f'option {i}' in html


@pytest.mark.parametrize("floor", range(1, 11))
def test_every_map_destination_has_one_exact_location_dot(floor):
    p, _ = _at_camp(f"u-dot-{floor}")
    p.update(floor=floor, location="gate_town", level=99, unlocked_floor=11)
    s = core.current_scene(p)
    html = render.render_scene_fragment(s)
    assert html.count('class="mkdot" aria-hidden="true"') == len(s.map["markers"])
    assert '.mk[data-anchor="left"] .mkdot{left:0;}' in render.SCENE_CSS
    assert '.mk[data-anchor="right"] .mkdot{left:100%;}' in render.SCENE_CSS
    assert f"background:{render.GOLD}" in render.SCENE_CSS


@pytest.mark.parametrize("floor", range(1, 11))
def test_all_map_assets_keep_the_native_two_colour_contract(floor):
    path = render._MAPS + f"/map_{floor:03d}_492x369.png"
    with Image.open(path) as image:
        assert image.size == (492, 369)
        assert image.mode == "RGBA"
        assert {colour for _, colour in image.getcolors()} == {
            (0, 0, 0, 255), (217, 217, 211, 255),
        }


def test_floor11_keeps_the_menu():
    p, _ = _at_camp("u-eleven")
    p.update(floor=11, location="gate_town", level=99, unlocked_floor=11)
    s = core.current_scene(p)
    assert s.map is None
    assert {"gate", "hunt", "town"} <= {o.id for o in s.options}
    assert 'class="mapwrap' not in render.render_scene_fragment(s)


def test_hurt_player_heals_stay_rows():
    p, s = _at_camp("u-hurt")
    p["hp"] = 1
    s = core.current_scene(p)
    ids = {o.id for o in s.options}
    assert "stew" in ids and "heal" in ids
    marker_opts = {m["opt"] for m in s.map["markers"]}
    assert "stew" not in marker_opts and "heal" not in marker_opts


def test_map_rides_the_wire_round_trip():
    p, s = _at_camp("u-wire")
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


def test_floor_maps_have_graduated_from_labs():
    p, _ = _at_camp("u-card")
    p["labs"] = {"floormap": True}
    s = core.apply_choice(p, "labs")
    assert "labs_toggle_floormap" not in {o.id for o in s.options}
    assert "floormap" not in labs.FEATURES
    assert "floormap" not in labs.enabled_keys(p)
    core.apply_choice(p, "labs_toggle_floormap")  # old links are harmless
    assert p["labs"]["floormap"] is True
    assert core.apply_choice(p, "labs_back").map is not None
