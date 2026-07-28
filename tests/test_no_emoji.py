"""010.1 — emoji are banned from every surface.

The design language is 1-bit pixel art: anything pictorial must be a
16×16 (or 32×32) 1-bit mask glyph, never an emoji. The engine may emit
⚡ and 🔒 as one-character semantic markers, but the renderer must swap
them for mask glyphs and the text surface must speak in words. No other
emoji may exist anywhere in the source.
"""

import os

from plugin_linear_ascent.engine import core, state
from plugin_linear_ascent.render import render_scene

# The two marker characters the renderer is contracted to swap.
_MARKERS = {"⚡", "🔒"}

# Characters browsers render as colored emoji (curated: the plane-1
# pictographs plus the common Misc-Symbols with default emoji
# presentation). Everything here is forbidden in any player-visible
# output; in source only the two markers are tolerated.
_EMOJI_SINGLETONS = {0x26A1, 0x2728, 0x274C, 0x2757, 0x2B50, 0x2764,
                     0x26BD, 0x26C4, 0x2615, 0x26EA, 0x26F2, 0x26F5,
                     0x26FA, 0x26FD, 0x2648, 0x2705, 0x270A, 0x270B,
                     0x2753, 0x2795, 0xFE0F}


def _emoji_in(text: str) -> list[str]:
    return [ch for ch in text
            if ord(ch) >= 0x1F000 or ord(ch) in _EMOJI_SINGLETONS]


def _player():
    p = state.new_player("no-emoji-test")
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1")
    core.apply_choice(p, "elf")
    core.apply_choice(p, "archer")
    core.apply_choice(p, "", "Renda")
    return p


def test_the_town_card_renders_glyphs_not_emoji():
    # Level 1 town: the Arcanum/Relay/fields rows are locked — the exact
    # rows that used to print 🔒 — and the meters rail carries the bolt.
    p = _player()
    html = render_scene(core.current_scene(p))
    assert not _emoji_in(html), _emoji_in(html)
    assert 'class="eg"' in html          # the 1-bit lock/bolt glyphs


def test_the_floor_card_renders_the_bolt_glyph():
    p = _player()
    core.apply_choice(p, "gate")
    core.apply_choice(p, "floor_1")
    html = render_scene(core.current_scene(p))
    assert not _emoji_in(html), _emoji_in(html)
    assert 'class="eg"' in html          # "1 ⚡" hunt hint → bolt glyph


def test_the_text_surface_speaks_words():
    p = _player()
    town = core.current_scene(p).to_text()
    assert not _emoji_in(town), _emoji_in(town)
    assert "locked" in town              # 🔒 level N → locked level N
    core.apply_choice(p, "gate")
    core.apply_choice(p, "floor_1")
    floor = core.current_scene(p).to_text()
    assert not _emoji_in(floor), _emoji_in(floor)
    assert "energy" in floor             # 1 ⚡ → 1 energy


def test_no_stray_emoji_anywhere_in_source():
    # Only the two renderer-contracted markers are tolerated in source;
    # tooltips and agent guidance are text-only surfaces, so tips.py and
    # plugin.py may not even carry the markers.
    root = os.path.join(os.path.dirname(__file__), "..",
                        "plugin_linear_ascent")
    marker_free = {"tips.py", "plugin.py"}
    for dirpath, _dirs, files in os.walk(root):
        if "content" + os.sep + "art" in dirpath:
            continue
        for fname in files:
            if not fname.endswith((".py", ".yaml", ".html", ".js")):
                continue
            path = os.path.join(dirpath, fname)
            text = open(path, encoding="utf-8").read()
            bad = [ch for ch in _emoji_in(text) if ch not in _MARKERS]
            assert not bad, (path, bad)
            if fname in marker_free:
                stray = [ch for ch in _MARKERS if ch in text]
                assert not stray, (path, stray)
