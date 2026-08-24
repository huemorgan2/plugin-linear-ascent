"""074 — Gmail recovery never blocks the player profile."""

from plugin_linear_ascent import pane, render
from plugin_linear_ascent.engine.scene import Meters, Scene


def _profile(*, figure3d: bool = False) -> str:
    scene = Scene(
        eyebrow="E",
        headline="H",
        meters=Meters(10, 10, 5, 24, 0, 100, 0, race="human"),
    )
    # Old worldd instances may still attach this runtime flag. It must no
    # longer affect the shared renderer.
    scene.portrait_locked = True
    if figure3d:
        scene.figure3d = {"race": "human", "px": [100, 200]}
    return render._profile_html(scene)


def test_gmail_state_never_replaces_regular_or_3d_profile():
    regular = _profile()
    figure = _profile(figure3d=True)

    assert 'class="portrait' in regular
    assert "Connect Gmail" not in regular
    assert 'class="portrait later figure3d"' in figure
    assert "Connect Gmail" not in figure


def test_recovery_strip_is_opt_in_and_outside_game_pane():
    unlinked = pane.render_pane(web=True, gmail_recovery=True)
    linked = pane.render_pane(web=True, gmail_recovery=False)
    luna = pane.render_pane()

    visible = '<div id="gmail-recovery" class="gmail-recovery">'
    hidden = '<div id="gmail-recovery" class="gmail-recovery" hidden>'
    assert visible in unlinked
    assert hidden in linked
    assert hidden in luna
    assert unlinked.index('id="gmail-recovery"') > unlinked.index(
        'id="community"')
    assert "recover this player" in unlinked.lower()
    assert 'href="/auth/google/start"' in unlinked
