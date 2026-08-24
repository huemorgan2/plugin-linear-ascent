"""063 — the game says "magic", never "mage".

The caster line is "caster", the shop is "the Arcanum", the gear is
"magic". Guard: no whole-word "mage" in any town scene a fresh
character can render, nor in the shipped content, tips or renderer."""

import os
import re

from plugin_linear_ascent import economy, render
from plugin_linear_ascent.engine import core, tips
from tests.test_057_weapon_art import create_character, fresh

MAGE = re.compile(r"\bmages?\b", re.I)
PKG = os.path.dirname(os.path.abspath(render.__file__))


def test_no_town_scene_says_mage():
    p = create_character(fresh("Wordsmith"))
    p["level"] = max(p.get("level", 1), economy.ARCANUM_LEVEL)
    for loc in ("town", "forge", "arcanum", "medlab", "board", "profile"):
        p["location"] = loc
        html = render.render_scene(core.current_scene(p))
        assert not MAGE.search(html), (loc, MAGE.search(html).group())


def test_no_shipped_text_says_mage():
    hits = []
    for root, _, files in os.walk(PKG):
        for fn in files:
            if fn.endswith((".py", ".yaml", ".yml", ".toml", ".md")):
                path = os.path.join(root, fn)
                for i, line in enumerate(open(path, encoding="utf-8"), 1):
                    if MAGE.search(line):
                        hits.append(f"{os.path.relpath(path, PKG)}:{i}")
    assert not hits, hits


def test_the_arcanum_door_hint_is_magic():
    p = create_character(fresh("Doorman"))
    p["level"] = economy.ARCANUM_LEVEL
    p["location"] = "town"
    s = core.current_scene(p)
    door = next(o for o in s.options if o.id == "arcanum")
    assert door.hint == "magic"


def test_tips_never_say_mage():
    for oid in ("arcanum", "forge", "medlab", "gate", "board"):
        assert not MAGE.search(tips.option_tip(oid) or ""), oid
