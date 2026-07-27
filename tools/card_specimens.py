#!/usr/bin/env python3
"""Render one specimen of every card type to /tmp/ascent-cards.html.

Visual QA for phase 2: open in a browser at real width and read them.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tests"))
import conftest  # installs the luna_sdk stub  # noqa: E402

from plugin_linear_ascent.engine import core, state  # noqa: E402
from plugin_linear_ascent.render import render_scene  # noqa: E402

OUT = "/tmp/ascent-cards.html"


def player():
    p = state.new_player("specimen")
    core.current_scene(p)
    while p.get("stage") == "intro":     # 016: the intro movie beats
        core.apply_choice(p, "1")
    core.apply_choice(p, "elf")
    core.apply_choice(p, "sorcerer")
    core.apply_choice(p, "", "Vael")
    return p


def main() -> None:
    cards: list[tuple[str, str]] = []
    p = player()

    cards.append(("creation (race)", render_scene(
        core.current_scene(state.new_player("s2")))))
    cards.append(("town", render_scene(core.current_scene(p))))
    core.apply_choice(p, "forge")
    cards.append(("forge", render_scene(core.current_scene(p))))
    core.apply_choice(p, "back")
    core.apply_choice(p, "vault")
    p["bank"] = 500
    p["bank_day"] = state.world_day() - 3
    cards.append(("vault + interest", render_scene(core.current_scene(p))))
    core.apply_choice(p, "back")
    core.apply_choice(p, "gate")
    s = core.apply_choice(p, "floor_1")
    cards.append(("floor arrival (banner)", render_scene(s)))
    s = core.apply_choice(p, "hunt")
    cards.append(("combat opener", render_scene(s)))
    # forced victory for the loot card
    p["encounter"]["hp"] = 1
    from plugin_linear_ascent.content import schema
    from plugin_linear_ascent.engine import combat
    s = combat.resolve_fight_action(p, schema.get_floor(1), "attack")
    cards.append(("victory / loot", render_scene(s)))
    # 017/003: dossier specimens — the [i] card on an armored, a flying
    # and a fast monster, rendered open (details open attr injected) so
    # the sheet is read at a glance without a click.
    from plugin_linear_ascent.content import schema as _schema
    from plugin_linear_ascent.engine import combat as _combat
    for floor_no, enc_id, label in ((10, "kings_guard", "armored"),
                                    (4, "glare_moth", "flying"),
                                    (5, "downs_courser", "fast")):
        p3 = player()
        p3["level"] = floor_no
        p3["unlocked_floor"] = floor_no
        fl = _schema.get_floor(floor_no)
        enc = next(e for e in fl.encounters if e.id == enc_id)
        s = _combat.start_encounter(p3, fl, enc)
        html = render_scene(s).replace("<details class=\"dx\">",
                                       "<details class=\"dx\" open>")
        cards.append((f"dossier open — {label} ({enc_id})", html))
    # death card
    p2 = player()
    p2["daily"]["death_save"] = True
    p2["gold"] = 340
    p2["gear"]["armor"] = "padded_jerkin"
    core.apply_choice(p2, "gate")
    core.apply_choice(p2, "floor_1")
    core.apply_choice(p2, "hunt")
    p2["hp"] = 1
    p2["encounter"]["atk"] = 999
    s = core.apply_choice(p2, "attack")
    cards.append(("death", render_scene(s)))

    blocks = []
    for title, html in cards:
        srcdoc = html.replace("&", "&amp;").replace('"', "&quot;")
        blocks.append(
            f'<h3 style="color:#8b93a7;font:12px monospace">{title}</h3>'
            f'<iframe srcdoc="{srcdoc}" style="width:520px;height:540px;'
            f'border:0"></iframe>')
    with open(OUT, "w") as f:
        f.write('<html><head><meta charset="utf-8"></head>'
                '<body style="background:#0b0e14;display:grid;'
                'grid-template-columns:1fr 1fr;gap:8px">'
                + "".join(blocks) + "</body></html>")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
