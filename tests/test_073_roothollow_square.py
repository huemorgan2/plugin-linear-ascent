"""073 — Roothollow square in districts, three nested doors."""

from plugin_linear_ascent import economy, render
from plugin_linear_ascent.engine import core, state
from plugin_linear_ascent.engine.scene import Scene


def playing(name="Square", world=None):
    p = state.new_player(f"t:{name}")
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1")
    core.apply_choice(p, "human")
    core.apply_choice(p, "warrior")
    core.apply_choice(p, "", name)
    if world is not None:
        p["_world"] = world
    return p


def door(scene, oid):
    return next(o for o in scene.options if o.id == oid)


def test_the_square_walks_climb_market_keep_banner_wire():
    p = playing("order")
    ids = [o.id for o in core.current_scene(p).options]
    assert ids[:6] == ["gate", "board", "forge", "arcanum", "medlab", "pawn"]
    assert ids.index("vault") < ids.index("lodge") < ids.index("sleep_menu")
    assert ids.index("guildhall") < ids.index("school") < ids.index("stone")


def test_three_doors_nest_under_the_one_you_look_for():
    p = playing("solo")
    s = core.current_scene(p)
    assert door(s, "board").nest and door(s, "gate").section == "THE CLIMB"
    assert door(s, "forge").section == "THE MARKET"
    assert door(s, "vault").section == "THE KEEP"
    assert door(s, "guildhall").section == "THE BANNER"
    assert door(s, "stone").section == "THE WIRE"
    assert not door(s, "stone").nest
    assert "hall" not in {o.id for o in s.options}

    p = playing("wired", world={
        "social": True, "inbox_count": 0,
        "faction": {"name": "the agent labs", "hall": {"ok": True}},
    })
    s = core.current_scene(p)
    assert door(s, "hall").nest
    assert door(s, "relay").section == "THE WIRE"
    assert door(s, "stone").nest and not door(s, "stone").section
    assert door(s, "fields").id == "fields"


def test_the_arcanum_says_magic():
    p = playing("mage")
    p["level"] = economy.ARCANUM_LEVEL
    assert door(core.current_scene(p), "arcanum").hint == "magic"


def test_nest_and_section_ride_beside_the_options():
    p = playing("wire")
    d = core.current_scene(p).to_dict()
    assert all("nest" not in o and "section" not in o for o in d["options"])
    assert d["option_section"]["gate"] == "THE CLIMB"
    assert "board" in d["option_nest"]
    back = Scene.from_dict(d)
    assert door(back, "board").nest
    assert door(back, "forge").section == "THE MARKET"


def test_the_card_draws_headers_and_indent():
    p = playing("card", world={
        "social": True,
        "faction": {"name": "the agent labs", "hall": {"ok": True}},
    })
    html = render.render_scene_fragment(core.current_scene(p))
    for head in ("THE CLIMB", "THE MARKET", "THE KEEP",
                 "THE BANNER", "THE WIRE"):
        assert f'class="osect">{head}</div>' in html
    assert html.count('class="orow nest"') == 3
    text = core.current_scene(p).to_text()
    assert "— THE MARKET —" in text
    assert "   2) The contract board" in text
