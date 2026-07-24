"""Payload fork (056 standalone cards) + embed height-reporting script."""

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


def test_card_posted_payload_has_no_embed():
    d = json.loads(plugmod.build_payload(scene(), card_posted=True))
    assert "embed_iframe" not in d
    assert "grey wolf" in d["scene_text"]
    assert "ALREADY posted" in d["instructions"]


def test_fallback_payload_keeps_inline_embed():
    d = json.loads(plugmod.build_payload(scene(), card_posted=False))
    assert d["embed_iframe"].startswith("<!doctype html>")
    assert "ALREADY rendered" in d["instructions"]


def test_voice_rules_in_both_payloads():
    for posted in (True, False):
        d = json.loads(plugmod.build_payload(scene(), card_posted=posted))
        ins = d["instructions"]
        assert "never repeat, summarize, or re-list" in ins
        assert "EMPTY message" in ins            # silence is sanctioned
        assert "GOOD flavor" in ins              # calibration examples ride along
        assert "engine decides everything" in ins  # shared rules intact


def test_cards_report_height_to_host():
    html = render_scene(scene())
    assert "luna:embed:height" in html
    assert "ResizeObserver" in html
