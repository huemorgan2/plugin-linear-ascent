"""051 the postbox — the pane carries the feedback switch, the overlay,
and the admin desk, on both doors."""

from plugin_linear_ascent import pane


def test_pane_carries_the_postbox():
    html = pane.render_pane("/api/p/plugin-linear-ascent")
    assert 'id="fbbtn"' in html                 # FEEDBACK on the sound bar
    assert 'id="fbadmin"' in html               # hidden until unread says so
    assert 'id="fbpanel"' in html and 'id="fblight"' in html
    assert "/pane/feedback/unread" in html      # badge poll wired
    assert "/pane/feedback/create" in html
    assert "/pane/feedback/admin" in html
    from plugin_linear_ascent import icons
    assert icons.icon_data_url("postbox") in html   # the envelope inlined


def test_web_door_gets_the_same_postbox():
    html = pane.render_pane("/play/api", web=True)
    assert 'id="fbbtn"' in html
    assert 'id="fbadmin"' in html
    assert "/pane/feedback/thread" in html


def test_postbox_js_defines_what_showscene_calls():
    # showScene lights the badge via fbPoll() — the module must exist
    html = pane.render_pane("/api/p/plugin-linear-ascent")
    assert "let fbPolled = false" in html
    assert "async function fbPoll" in html
