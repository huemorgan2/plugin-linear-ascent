"""Renderer: every card type produces valid, escaped, banner-bearing HTML."""

from plugin_linear_ascent.engine import core, state
from plugin_linear_ascent.render import render_scene, _banner_data_url


def make_player():
    p = state.new_player("render-test")
    core.current_scene(p)
    while p["stage"] == "intro":                # 016: through the movie
        core.apply_choice(p, "1")
    core.apply_choice(p, "halfling")
    core.apply_choice(p, "archer")
    core.apply_choice(p, "", "Renda")
    return p


def test_town_card_has_banner_and_options():
    p = make_player()
    html = render_scene(core.current_scene(p))
    assert "data:image/png;base64" in html          # roothollow banner inlined
    assert "ROOTHOLLOW" in html
    assert 'class="opt"' in html
    assert 'class="rail' in html                    # status meters


def test_fight_card_and_escaping():
    p = make_player()
    core.apply_choice(p, "gate")
    core.apply_choice(p, "floor_1")
    core.apply_choice(p, "hunt")
    s = core.current_scene(p)
    s.body_lines.append("<script>alert(1)</script>")
    html = render_scene(s)
    assert "<script>alert(1)" not in html           # escaped
    assert "&lt;script&gt;" in html


def test_death_card_has_stripe():
    p = make_player()
    p["daily"]["death_save"] = True
    core.apply_choice(p, "gate")
    core.apply_choice(p, "floor_1")
    core.apply_choice(p, "hunt")
    p["hp"] = 1
    p["encounter"]["atk"] = 999
    s = core.apply_choice(p, "attack")
    html = render_scene(s)
    assert "border-left:3px solid" in html          # event stripe
    assert _banner_data_url("death")                # death banner exists


def test_all_referenced_banners_exist():
    for slug in ("roothollow", "forge", "medlab", "lodge", "vault", "stone",
                 "gate", "greenreach", "death", "present", "gnarl", "title"):
        assert _banner_data_url(slug), f"missing banner: {slug}"


def test_intro_movie_card_shows_scene_art_at_own_size():
    # 016: a fresh player opens on the movie's first beat, 320x200 art
    p = state.new_player("intro-render")
    html = render_scene(core.current_scene(p))
    assert "THE STORY SO FAR · I" in html
    assert "aspect-ratio:320/200" in html
    assert "data:image/gif;base64" in html


def test_intro_movie_split_scene_carries_the_swap():
    # 016: the theft's action gif plays once, then swaps to its loop
    p = state.new_player("intro-render-2")
    core.current_scene(p)
    html = render_scene(core.apply_choice(p, "next"))   # scene II: theft
    assert "THE STORY SO FAR · II" in html
    assert 'data-swap="data:image/gif;base64' in html
    assert 'data-swap-ms="' in html


def test_title_card_still_closes_the_movie():
    p = state.new_player("intro-render-3")
    core.current_scene(p)
    while p.get("intro_step", 0) < 9:
        scene = core.apply_choice(p, "next")
    html = render_scene(scene)
    assert "LINEAR ASCENT" in html
    assert "aspect-ratio:320/200" in html               # title art, not 320x112
    # 011: the title screen animates — GIF mask instead of the static PNG
    assert "data:image/gif;base64" in html
