"""Renderer: every card type produces valid, escaped, banner-bearing HTML."""

from plugin_linear_ascent.engine import core, state
from plugin_linear_ascent.render import render_scene, _banner_data_url


def make_player():
    p = state.new_player("render-test")
    core.current_scene(p)
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
    assert 'class="rail"' in html                   # status meters


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
                 "gate", "greenreach", "death", "present", "gnarl"):
        assert _banner_data_url(slug), f"missing banner: {slug}"
