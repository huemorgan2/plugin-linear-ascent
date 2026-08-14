#!/usr/bin/env python3
"""009 ui-skin pass — render real engine scenes to cards for screenshots.

Same harness idea as qa_030_shots.py: real engine, real renderer, local.
Writes render_scene() documents to <out>/html; screenshots are taken by
the caller with headless Chrome (no Playwright dependency).

Usage: python tools/qa_009_shots.py <out_dir>
"""

import os
import sys

os.environ.setdefault("ASCENT_DEV_LOCAL", "1")
_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(_HERE, "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))
import conftest  # noqa: E402,F401 — stubs luna_sdk

from plugin_linear_ascent import economy, render  # noqa: E402
from plugin_linear_ascent.engine import core, state  # noqa: E402

OUT = os.path.abspath(sys.argv[1])
HTML = os.path.join(OUT, "html")

WORLD = {
    "frontier": 3,
    "census": {"total": 7, "by_floor": {"1": 3, "3": 3, "2": 1}},
    "warden": {"floor": 3, "hp": 43_000, "hp_max": 100_000,
               "strikers": [{"name": "Asha"}, {"name": "Brand"}],
               "pity": 0, "closes_in_s": 11_520,
               "fallen_by": {"1": "Asha, Brand", "2": "Brand, Okko"}},
    "gossip": ["Asha cleared the drowned barn run without a scratch.",
               "a marsh wolf took a climber's pack on floor 2."],
}


def player(name: str) -> dict:
    p = state.new_player(name)
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1")
    core.apply_choice(p, "human")
    core.apply_choice(p, "warrior")
    core.apply_choice(p, "", text="Seer")
    return p


def snap(name: str, scene) -> None:
    with open(os.path.join(HTML, f"{name}.html"), "w") as f:
        f.write(render.render_scene(scene))
    print("html ", name)


def go(p, slug):
    try:
        return core.apply_choice(p, slug)
    except Exception as e:
        s = core.current_scene(p)
        keys = [o.key for o in (s.options or [])]
        print(f"!! choice {slug!r} failed ({e}); options: {keys}")
        return s


def main() -> None:
    os.makedirs(HTML, exist_ok=True)

    p = player("qa009")
    snap("01-town-square", core.current_scene(p))

    p["_world"] = dict(WORLD)
    p["news_day"] = -1
    snap("02-morning-crier", core.current_scene(p))
    go(p, "news_close")

    snap("03-forge", go(p, "forge"))
    go(p, "back")
    snap("04-school", go(p, "school"))
    go(p, "back")
    p["bank"] = 1_240
    snap("05-vault", go(p, "vault"))
    go(p, "back")
    snap("06-board", go(p, "board"))
    go(p, "back")
    snap("07-lodge", go(p, "lodge"))
    snap("08-keeper-talk", go(p, "talk"))
    go(p, "back")
    go(p, "back")
    snap("09-sleep-menu", go(p, "sleep"))
    go(p, "back")
    snap("10-gate", go(p, "gate"))

    snap("11-reel-beat1", go(p, "floor_1"))
    snap("12-reel-beat2", go(p, "next"))
    snap("13-arrival", go(p, "next"))
    snap("14-npc-talk", go(p, "talk"))

    s = go(p, "hunt")
    if not s.enemy:
        s = go(p, "hunt")
    snap("15-fight", s)

    # lv10 with armour — profile block density
    p2 = player("qa009-lv10")
    p2["level"] = 10
    p2["unlocked_floor"] = 10
    p2["gold"] = 100_000
    p2["hp"] = state.max_hp(p2)
    armor = sorted((g for g in economy.FORGE.values()
                    if g.slot == "armor" and 3 <= g.tier <= 4),
                   key=lambda g: g.tier)
    if armor:
        p2["gear"]["armor"] = armor[0].slug
    snap("16-town-lv10", core.current_scene(p2))
    p2["_world"] = dict(WORLD) | {"frontier": 10}
    snap("17-gate-lv10", go(p2, "gate"))


if __name__ == "__main__":
    main()
