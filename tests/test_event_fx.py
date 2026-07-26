"""011 event animations — kill GIFs, gate open, title.

The engine tags scenes with an fx slug; the renderer swaps the static
banner for the animated white-ink GIF (same mask + tint grammar).
"""

from plugin_linear_ascent.engine import combat
from plugin_linear_ascent.engine.scene import Scene
from plugin_linear_ascent.render import render_scene_fragment


def test_kill_fx_maps_creature_families():
    assert combat._kill_fx({"id": "feral_boar"}, "Feral Boar", False) == "boar_kill"
    assert combat._kill_fx({"id": "goblin_straggler"}, "Goblin", False) == "goblin_kill"
    assert combat._kill_fx({"id": "grey_wolf"}, "Grey Wolf", False) == "wolf_kill"


def test_kill_fx_matches_warden_by_name():
    fx = combat._kill_fx({"id": ""}, "Warden Brackjaw", True)
    assert fx == "brackjaw_kill"


def test_first_clear_without_specific_art_opens_the_gate():
    assert combat._kill_fx({"id": "rust_shade"}, "Rust Shade", True) == "ascent_open"
    assert combat._kill_fx({"id": "rust_shade"}, "Rust Shade", False) == ""


def test_fragment_embeds_animated_gif_for_fx():
    scene = Scene(eyebrow="E", headline="H", event_kind="loot",
                  fx="boar_kill", scene_id="s1")
    html = render_scene_fragment(scene)
    assert "data:image/gif;base64," in html
    assert "mask-image" in html


def test_fx_wins_over_static_banner():
    scene = Scene(eyebrow="E", headline="H", banner="roothollow",
                  fx="ascent_title", scene_id="s2")
    html = render_scene_fragment(scene)
    assert "data:image/gif;base64," in html
    assert "data:image/png;base64," not in html


def test_unknown_fx_falls_back_to_static_banner():
    scene = Scene(eyebrow="E", headline="H", banner="roothollow",
                  fx="no_such_animation", scene_id="s3")
    html = render_scene_fragment(scene)
    assert "data:image/png;base64," in html


def test_fx_survives_the_doc_round_trip():
    scene = Scene(eyebrow="E", headline="H", fx="wolf_kill", scene_id="s4")
    assert Scene.from_dict(scene.to_dict()).fx == "wolf_kill"
