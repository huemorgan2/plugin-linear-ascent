"""078 Phase 3 — art ships as versioned static URLs, never base64.

The law: with an art base set, no rendered fragment carries a
data:image/png or data:image/gif payload — every banner, event GIF,
portrait and gear icon is a {base}/<relpath>?v={version} URL whose file
exists on disk. With the base unset, the legacy inline behavior is
untouched (fixtures and unwired hosts keep working). The generated SVG
glyphs (icons.py) and the VGA font stay inline by design.
"""

import os
import re

import pytest

from plugin_linear_ascent import render
from plugin_linear_ascent.engine import state
from plugin_linear_ascent.engine.scene import Scene
from plugin_linear_ascent.version import VERSION

BASE = "/static/laart"


@pytest.fixture
def art_base():
    render.set_art_base(BASE)
    yield
    render.set_art_base("")


def _fresh_player():
    p = state.new_player("t:art-test")
    p.update(stage="playing", name="Arty", race="human", clazz="warrior")
    return p


def _scenes():
    yield Scene(eyebrow="FLOOR 1 · TEST", headline="A banner scene",
                banner="roothollow", event_kind="")
    yield Scene(eyebrow="FLOOR 1 · TEST", headline="A kill",
                fx="kill", event_kind="loot")
    yield Scene(eyebrow="FLOOR 1 · TEST", headline="A death",
                banner="death", fx="death", event_kind="death")


def test_fragments_carry_zero_inline_raster_art(art_base):
    for scene in _scenes():
        html = render.render_scene_fragment(scene)
        assert "data:image/png" not in html
        assert "data:image/gif" not in html


def test_art_urls_are_versioned_and_resolve_to_files(art_base):
    urls = set()
    for scene in _scenes():
        urls.update(re.findall(
            re.escape(BASE) + r"/([a-z0-9_\-/.]+)\?v=([0-9.]+)",
            render.render_scene_fragment(scene)))
    assert urls, "expected at least one static art URL in the corpus"
    root = os.path.join(os.path.dirname(render.__file__), "content", "art")
    for rel, v in urls:
        assert v == VERSION
        assert os.path.exists(os.path.join(root, rel)), rel


def test_unset_base_restores_inline_art():
    render.set_art_base("")
    scene = Scene(eyebrow="FLOOR 1 · TEST", headline="Inline again",
                  banner="roothollow")
    html = render.render_scene_fragment(scene)
    assert "data:image/png;base64," in html
    assert BASE not in html


def test_set_art_base_flips_existing_caches():
    render.set_art_base("")
    inline = render._banner_data_url("roothollow")
    assert inline and inline[0].startswith("data:image/png")
    render.set_art_base(BASE)
    try:
        url = render._banner_data_url("roothollow")
        assert url and url[0].startswith(BASE + "/banners/")
        assert f"?v={VERSION}" in url[0]
    finally:
        render.set_art_base("")


def test_portraits_and_gear_ride_the_base_too(art_base):
    art = render._portrait_art("human")
    assert art and art[0].startswith(BASE + "/portraits/")
    gear = render._gear_art_url("rusted_sword", "icons")
    if gear is not None:               # art file optional per-slug
        assert gear.startswith(BASE + "/")
