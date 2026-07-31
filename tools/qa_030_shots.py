#!/usr/bin/env python3
"""030 visual pass — render real engine scenes to cards, screenshot them.

The full dojo stack (worldd + QA Luna) needs the Postgres this machine no
longer has; this harness drives the SAME engine and the SAME renderer the
pane ships, locally: build a player, click through the real apply_choice
paths, write render_scene() documents, photograph them with Playwright.

Usage: python tools/qa_030_shots.py <out_dir>
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

OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else
                      os.path.join(ROOT, "..", "dojo", "results",
                                   "0030-qa"))
HTML = os.path.join(OUT, "html")
SHOTS = os.path.join(OUT, "screenshots")

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


def main() -> None:
    for d in (HTML, SHOTS):
        os.makedirs(d, exist_ok=True)

    # ── level 1 ─────────────────────────────────────────────────────
    p = player("qa030-lv1")
    snap("01-town-square-rags", core.current_scene(p))

    p["_world"] = dict(WORLD)
    p["news_day"] = -1
    snap("02-morning-crier", core.current_scene(p))
    core.apply_choice(p, "news_close")

    p["bank"] = 1_240
    snap("03-vault-strip", core.apply_choice(p, "vault"))
    core.apply_choice(p, "back")

    core.apply_choice(p, "lodge")
    snap("04-keeper-talk", core.apply_choice(p, "talk"))
    core.apply_choice(p, "back")

    snap("05-gate-floor-tiles", core.apply_choice(p, "gate"))

    snap("06-reel-beat1-world", core.apply_choice(p, "floor_1"))
    snap("07-reel-beat2-warden", core.apply_choice(p, "next"))
    snap("08-arrival", core.apply_choice(p, "next"))

    snap("09-npc-talk", core.apply_choice(p, "talk"))

    s = core.apply_choice(p, "hunt")
    if not s.enemy:
        s = core.apply_choice(p, "hunt")
    snap("10-fight-enemy-plate", s)

    # ── level ~10 ───────────────────────────────────────────────────
    p2 = player("qa030-lv10")
    p2["level"] = 10
    p2["unlocked_floor"] = 10
    p2["gold"] = 100_000
    p2["hp"] = state.max_hp(p2)
    armor = sorted((g for g in economy.FORGE.values()
                    if g.slot == "armor" and 3 <= g.tier <= 4),
                   key=lambda g: g.tier)
    if armor:
        p2["gear"]["armor"] = armor[0].slug
    snap("11-town-lv10-chain", core.current_scene(p2))

    p2["_world"] = dict(WORLD) | {"frontier": 10}
    snap("12-gate-lv10", core.apply_choice(p2, "gate"))
    core.apply_choice(p2, "floor_9")
    while p2.get("movie_floor"):
        core.apply_choice(p2, "1")
    s = core.apply_choice(p2, "hunt")
    if not s.enemy:
        s = core.apply_choice(p2, "hunt")
    snap("13-fight-floor9", s)

    # fallen-keep reel beat (floor 2 fell to the war party)
    p3 = player("qa030-fallen")
    p3["unlocked_floor"] = 3
    p3["_world"] = dict(WORLD)
    core.apply_choice(p3, "gate")
    core.apply_choice(p3, "floor_2")
    snap("14-reel-fallen-keep", core.apply_choice(p3, "next"))

    # ── photograph ──────────────────────────────────────────────────
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        # reduced-motion sidesteps the typewriter so cards paint whole
        page = browser.new_page(viewport={"width": 720, "height": 1200},
                                device_scale_factor=2,
                                reduced_motion="reduce")
        for name in sorted(os.listdir(HTML)):
            if not name.endswith(".html"):
                continue
            page.goto("file://" + os.path.join(HTML, name))
            page.wait_for_timeout(600)
            page.screenshot(
                path=os.path.join(SHOTS, name[:-5] + ".png"),
                full_page=True)
            print("shot ", name[:-5])
        browser.close()


if __name__ == "__main__":
    main()
