#!/usr/bin/env python3
"""031 visual pass — the punch-list scenes, photographed.

Same harness shape as qa_030_shots: real engine, real renderer, real
apply_choice paths, Playwright photographs. One shot per punch item:
the ident header + slot pack + paper (town), the Forge card wall, the
lodge evening (JOB OFFER / ACTIVITY / band), Wick with his face, the
plain floor list vs the in-floor art choice, the Warden keep, the
archer's free shooting at range, and the death card that now bills you.

Usage: python tools/qa_031_shots.py <out_dir>
"""

import os
import sys

os.environ.setdefault("ASCENT_DEV_LOCAL", "1")
_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(_HERE, "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))
import conftest  # noqa: E402,F401 — stubs luna_sdk

from plugin_linear_ascent import render  # noqa: E402
from plugin_linear_ascent.engine import core, state  # noqa: E402

OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else
                      os.path.join(ROOT, "..", "dojo", "results",
                                   "0031-qa"))
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
               "war chest at 45% — the cut to fallen floors rises at "
               "dusk.", "a marsh wolf took a climber's pack on floor 2."],
}


def player(name: str, race="human", clazz="warrior",
           pname="Seer") -> dict:
    p = state.new_player(name)
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1")
    core.apply_choice(p, race)
    core.apply_choice(p, clazz)
    core.apply_choice(p, "", text=pname)
    return p


def snap(name: str, scene) -> None:
    with open(os.path.join(HTML, f"{name}.html"), "w") as f:
        f.write(render.render_scene(scene))
    print("html ", name)


def main() -> None:
    for d in (HTML, SHOTS):
        os.makedirs(d, exist_ok=True)

    # ── §1 §3 §4 §12: town — ident header, slot pack, the paper ─────
    p = player("qa031-town", race="elf", clazz="archer", pname="Vael")
    p["level"], p["gold"] = 5, 1_234
    p["inventory"]["medgel"] = 2
    p["inventory"]["arrows"] = 14
    p["_world"] = dict(WORLD)
    p["news_day"] = -1
    snap("01-town-ident-pack-paper", core.current_scene(p))
    core.apply_choice(p, "news_close")

    # ── §14: the Forge card wall ────────────────────────────────────
    f = player("qa031-forge")
    f["level"], f["gold"], f["unlocked_floor"] = 6, 50_000, 6
    core.apply_choice(f, "forge")
    core.apply_choice(f, "buy_pigsticker")   # a worn rung + a wear row
    core.apply_choice(f, "buy_ashwood_bow")
    f["durability"]["weapon"] = 2            # a repair row under the wall
    snap("02-forge-card-wall", core.current_scene(f))

    # ── §10 §11: the lodge evening ──────────────────────────────────
    lp = player("qa031-lodge")
    lp["level"], lp["gold"] = 3, 400
    snap("03-lodge-evening", core.apply_choice(lp, "lodge"))

    # ── §9: Wick, face and story ────────────────────────────────────
    snap("04-wick-talk", core.apply_choice(lp, "talk"))
    core.apply_choice(lp, "back")

    # ── §13: floor list plain, the art on the in-floor choice ───────
    g = player("qa031-gate")
    g["_world"] = dict(WORLD)
    snap("05-gate-floor-list-plain", core.apply_choice(g, "gate"))
    core.apply_choice(g, "floor_1")
    while g.get("movie_floor"):
        core.apply_choice(g, "1")
    snap("06-infloor-hunt-vs-keep", core.current_scene(g))

    # ── §5 §6: the keep — every swing 3⚡, drops in the dossier ─────
    snap("07-warden-keep", core.apply_choice(g, "keep"))

    # ── §7: the archer shoots free at range ─────────────────────────
    a = player("qa031-range", race="elf", clazz="archer", pname="Vael")
    a["gear"]["shoes"] = "cobbled_boots"
    core.apply_choice(a, "gate")
    core.apply_choice(a, "floor_1")
    while a.get("movie_floor"):
        core.apply_choice(a, "1")
    s = core.apply_choice(a, "hunt")
    if not s.enemy:
        s = core.apply_choice(a, "hunt")
    snap("08-archer-at-range", s)

    # ── §8: death now costs — the level-1 tax ───────────────────────
    dpl = player("qa031-death")
    dpl["gold"] = 900
    core.apply_choice(dpl, "gate")
    core.apply_choice(dpl, "floor_1")
    while dpl.get("movie_floor"):
        core.apply_choice(dpl, "1")
    s = core.apply_choice(dpl, "hunt")
    if not s.enemy:
        s = core.apply_choice(dpl, "hunt")
    dpl["hp"] = 1
    dpl["encounter"]["atk"] = 999
    snap("09-death-pays-the-tax", core.apply_choice(dpl, "attack"))

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
