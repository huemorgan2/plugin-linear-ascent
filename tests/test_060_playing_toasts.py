"""060 — the Playing button speaks: notices from the tower's pulse.

The pane ships the toast strip (a caret at the ▶ playing button, an ✕
top right, gone after 3 s, several stack), the closed-panel fetch on a
moved head (scope=both), and the two switches — world / faction —
remembered in localStorage, both on by default.
"""

from plugin_linear_ascent import pane


def test_pane_ships_the_toasts_and_the_switches():
    html = pane.render_pane()
    # the strip and its parts
    assert "#plytoasts" in html
    assert ".plytoast:first-child::after" in html     # the caret
    assert 'class="x" aria-label="close"' in html      # the ✕
    assert "PLY_TOAST_MS = 3000" in html
    assert "PLY_TOAST_MAX = 4" in html
    assert "flex-direction:column-reverse" in html     # they stack
    # the closed panel asks once per moved head, both scopes at once
    assert "scope=both&since=" in html
    assert "ply.seen = ply.head" in html
    # the switches
    assert "la_ply_world" in html and "la_ply_faction" in html
    assert 'data-ply="sw:' in html
    assert "v === null ? true" in html                # default on
    assert "notices" in html
