"""059 — the level-up card is a white box in plain English.

"LEVEL N CLIMBERS CAN:" frames every line; each unlock says what the
player can DO now, without the game's slang. The ▛ markers render as
a bordered callout in both hosts.
"""

from plugin_linear_ascent import economy, render, unlocks
from plugin_linear_ascent.engine import core, social
from tests.test_020_visible_gates import playing, town


def _train(p, to_level):
    p["level"] = to_level - 1
    p["xp"] = economy.xp_need(p["level"])
    p["gold"] = economy.levelup_gold(p["level"]) + 10
    town(p)
    core.apply_choice(p, "guildhall")
    return core.apply_choice(p, "guild_train")


def test_the_card_is_a_titled_box():
    s = _train(playing(), 2)
    assert s.body_lines[0] == "▛ LEVEL 2 CLIMBERS CAN:"
    assert s.body_lines[-1] == "▛."
    assert "You are now LEVEL 2" in s.body_lines[1]
    assert "health" in s.body_lines[1]
    body = "\n".join(s.body_lines)
    assert "burns it into your frame" not in body
    assert "Wounds close" not in body


def test_the_box_renders_white_with_the_title():
    s = _train(playing(), 2)
    html = render.render_scene(s)
    assert '<div class="callout">' in html
    assert 'class="callouth type">LEVEL 2 CLIMBERS CAN:' in html
    assert "▛ LEVEL" not in html and ">▛.<" not in html
    assert f".callout{{border:1px solid {render.BRIGHT}" in html


def test_level_four_speaks_plainly():
    s = _train(playing(), 4)
    body = "\n".join(s.body_lines)
    assert "start your own guild" in body
    assert "WARNING" in body and "dying can cost you your equipment" in body


def test_every_unlock_has_a_plain_line():
    for u in unlocks.registry():
        text = unlocks.plain(u)
        assert text and text != u.why or u.id.startswith(
            ("relics_floor_", "hone_reset_", "milestone_")), u.id
    # dynamic ids fill their numbers
    assert "tier-3" in unlocks.plain(unlocks.for_option("gear_tier_3"))
    e = unlocks.for_option("energy_cap_tier_2")
    assert str(economy.energy_cap(2)) in unlocks.plain(e)
    assert "keen" in unlocks.plain(next(
        u for u in unlocks.registry() if u.id.startswith("band1_rung_")))
