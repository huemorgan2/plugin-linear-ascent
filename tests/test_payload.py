"""Tool payloads (009: the pane is the display — no cards, no embeds)."""

import json

from plugin_linear_ascent import plugin as plugmod
from plugin_linear_ascent.engine.scene import Option, Scene
from plugin_linear_ascent.render import render_scene


def scene():
    return Scene(
        eyebrow="TEST", headline="A test scene", support="",
        body_lines=["A grey wolf pads out of the fencerows."],
        options=[Option("fight", "Fight")],
    )


def test_payload_is_text_only():
    d = json.loads(plugmod.build_payload(scene()))
    assert "embed_iframe" not in d
    assert "grey wolf" in d["scene_text"]


def test_payload_points_at_the_pane():
    d = json.loads(plugmod.build_payload(scene()))
    assert "Linear Ascent pane" in d["instructions"]
    assert "NEVER repeat the scene text" in d["instructions"]


def test_voice_rules_ride_along():
    ins = json.loads(plugmod.build_payload(scene()))["instructions"]
    assert "never repeat, summarize, or re-list" in ins
    assert "EMPTY message" in ins            # silence is sanctioned
    assert "GOOD flavor" in ins              # calibration examples ride along
    assert "engine decides everything" in ins  # shared rules intact


def test_legacy_cards_still_report_height_to_host():
    html = render_scene(scene())
    assert "luna:embed:height" in html
    assert "ResizeObserver" in html
