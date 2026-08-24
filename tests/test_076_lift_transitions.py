"""076 — lift transitions: floor changes carry lift="up"/"down" on the
wire, the card wrapper carries data-lift, the pane ships the overlay,
and both lift GIFs exist. Refusals and same-floor stays carry nothing."""

from __future__ import annotations

from pathlib import Path

import pytest

from plugin_linear_ascent import pane, render
from plugin_linear_ascent.engine import core, state

ART = (Path(__file__).resolve().parents[1] / "plugin_linear_ascent"
       / "content" / "art" / "events")


def playing(name="Lift"):
    p = state.new_player(f"t:{name}")
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1")
    core.apply_choice(p, "human")
    core.apply_choice(p, "warrior")
    core.apply_choice(p, "", name)
    return p


def climber(floor=0, unlocked=5):
    p = playing()
    p["level"] = 99
    p["unlocked_floor"] = unlocked
    for n in range(1, unlocked + 1):
        p["flags"][f"floor_seen_{n}"] = True   # arrival card, no movie
    p["location"] = "town"
    core.apply_choice(p, "town")
    if floor:
        core.apply_choice(p, "gate")
        core.apply_choice(p, f"floor_{floor}")
    return p


# ── the wire ─────────────────────────────────────────────────────────────

def test_gate_pick_up_carries_lift_up():
    p = climber()
    core.apply_choice(p, "gate")
    s = core.apply_choice(p, "floor_2")
    assert s.lift == "up"
    assert s.to_dict()["lift"] == "up"


def test_gate_pick_down_carries_lift_down():
    p = climber(floor=3)
    core.apply_choice(p, "gate")
    s = core.apply_choice(p, "floor_1")
    assert s.lift == "down"


@pytest.mark.reel
def test_first_visit_movie_also_carries_the_ride():
    p = climber()
    p["flags"].pop("floor_seen_2", None)       # floor 2 never seen
    core.apply_choice(p, "gate")
    s = core.apply_choice(p, "floor_2")
    assert s.lift == "up"                      # the movie beat rides too


def test_town_from_a_floor_is_a_ride_down():
    p = climber(floor=2)
    s = core.apply_choice(p, "town")
    assert s.lift == "down"
    assert p["floor"] == 0


def test_town_from_ground_is_not_a_ride():
    p = climber()
    s = core.apply_choice(p, "town")
    assert s.lift == ""


def test_sealed_refusal_carries_no_ride():
    p = climber()
    core.apply_choice(p, "gate")
    s = core.apply_choice(p, "floor_5000")
    assert s.refusal
    assert s.lift == ""


def test_lift_survives_the_stored_scene_round_trip():
    from plugin_linear_ascent.engine.scene import Scene
    p = climber()
    core.apply_choice(p, "gate")
    s = core.apply_choice(p, "floor_2")
    assert Scene.from_dict(s.to_dict()).lift == "up"


# ── the card ─────────────────────────────────────────────────────────────

def test_fragment_carries_data_lift_only_on_a_ride():
    p = climber()
    core.apply_choice(p, "gate")
    s = core.apply_choice(p, "floor_2")
    assert 'data-lift="up"' in render.render_scene_fragment(s)
    quiet = core.apply_choice(p, "town")
    quiet.lift = ""
    assert "data-lift" not in render.render_scene_fragment(quiet)


# ── the pane ─────────────────────────────────────────────────────────────

def test_pane_ships_the_overlay_and_both_gif_urls():
    html = pane.render_pane(api_base="/play/api", web=True)
    assert "liftlay" in html
    assert "/static/fxart/lift_ascent_320x112.gif" in html
    assert "/static/fxart/lift_descent_320x112.gif" in html
    assert "playLift" in html


# ── the art ──────────────────────────────────────────────────────────────

def test_both_lift_gifs_ship_in_the_package():
    for slug in ("lift_ascent", "lift_descent"):
        f = ART / f"{slug}_320x112.gif"
        assert f.is_file(), f
        assert f.stat().st_size > 10_000, f
