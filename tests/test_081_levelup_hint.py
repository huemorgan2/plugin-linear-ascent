"""081 phase-4 — the level-1 explainer box: live computed numbers
(xp_need(1)=24, levelup_gold(1)=60), gone from the wire at level 2."""

from plugin_linear_ascent import economy, render
from plugin_linear_ascent.engine.scene import Meters, Scene


def _scene(level, xp=0):
    return Scene(eyebrow="E", headline="H",
                 meters=Meters(10, 10, 5, 24, xp, economy.xp_need(level),
                               0, level=level, atk=12, dfs=6))


def test_level1_box_quotes_the_computed_numbers():
    html = render._profile_html(_scene(1, xp=7))
    assert 'class="lvlhint"' in html
    assert 'data-hint="levelup"' in html
    assert f"XP 7/{economy.xp_need(1)}" in html
    assert f"◈ {economy.levelup_gold(1):,}" in html
    assert "Guildhall" in html
    assert 'aria-label="close"' in html
    # the folklore numbers stay out of the copy
    assert economy.xp_need(1) == 24 and economy.levelup_gold(1) == 60


def test_level2_and_up_never_render_the_box():
    for lvl in (2, 3, 10):
        assert "lvlhint" not in render._profile_html(_scene(lvl)), lvl
