"""Plan 021 — floor is not level. Zero behaviour change, forever.

Golden values below were captured from the code BEFORE the refactor
(commit a975042). If any of them move, a floor leaked into a level-typed
function (or a retune forgot to update the goldens on purpose).
"""

from __future__ import annotations

import ast
import pathlib
import re
from unittest import mock

import pytest

from plugin_linear_ascent import economy

# warden_stats(f) for f in 1..100.  Regenerated ON PURPOSE for the
# 022/002 grand retune (level cap 30, gear-carried reference player,
# armor→HP): ATK re-derives from the new reference, the HP column is
# byte-identical to the pre-022 curve.
GOLDEN_WARDENS = [
    (15, 3, 70), (16, 6, 93), (20, 9, 116), (26, 12, 139), (36, 15, 162),
    (42, 18, 184), (50, 21, 207), (54, 24, 230), (63, 27, 253), (70, 30, 276),
    (76, 33, 298), (79, 36, 321), (82, 39, 344), (89, 42, 367), (95, 45, 390),
    (102, 48, 412), (109, 51, 435), (116, 54, 458), (122, 57, 481),
    (129, 60, 504), (120, 63, 526), (122, 66, 549), (120, 69, 572),
    (126, 72, 595), (132, 75, 618), (138, 78, 640), (150, 81, 663),
    (150, 84, 686), (162, 87, 709), (168, 90, 732), (170, 93, 773),
    (165, 96, 816), (161, 99, 860), (161, 102, 905), (167, 105, 952),
    (167, 108, 998), (173, 111, 1047), (174, 114, 1097), (180, 117, 1148),
    (182, 120, 1200), (182, 123, 1252), (180, 126, 1306), (180, 129, 1362),
    (185, 132, 1419), (187, 135, 1477), (190, 138, 1534), (195, 141, 1595),
    (198, 144, 1656), (202, 147, 1718), (208, 150, 1782), (208, 153, 1845),
    (207, 156, 1911), (208, 159, 1978), (211, 162, 2046), (215, 165, 2116),
    (220, 168, 2185), (225, 171, 2256), (229, 174, 2329), (235, 177, 2403),
    (239, 180, 2478), (240, 183, 2552), (240, 186, 2630), (241, 189, 2708),
    (245, 192, 2788), (251, 195, 2869), (256, 198, 2949), (260, 201, 3032),
    (265, 204, 3116), (271, 207, 3201), (276, 210, 3288), (278, 213, 3374),
    (277, 216, 3462), (279, 219, 3552), (284, 222, 3644), (289, 225, 3736),
    (293, 228, 3827), (300, 231, 3922), (306, 234, 4017), (311, 237, 4114),
    (316, 240, 4212), (319, 243, 4309), (319, 246, 4409), (320, 249, 4510),
    (325, 252, 4613), (332, 255, 4717), (337, 258, 4819), (344, 261, 4925),
    (349, 264, 5032), (356, 267, 5141), (362, 270, 5250), (364, 273, 5358),
    (364, 276, 5470), (365, 279, 5583), (372, 282, 5697), (380, 285, 5812),
    (385, 288, 5925), (392, 291, 6043), (398, 294, 6161), (404, 297, 6281),
    (411, 300, 6402),
]

# 022/002: gates past LEVEL_CAP live on the FLOOR axis instead.
GOLDEN_GEAR_GATES = {1: 1, 2: 11, 3: 21, 4: 30, 5: 30,
                     6: 30, 7: 30, 8: 30, 9: 30, 10: 30}
GOLDEN_GEAR_FLOOR_GATES = {1: 0, 2: 0, 3: 0, 4: 31, 5: 41,
                           6: 51, 7: 61, 8: 71, 9: 81, 10: 91}

# 022/002: energy_cap left this list — it is gear-tier-typed now.
LEVEL_TYPED = {"player_max_hp", "player_atk", "player_def",
               "xp_need", "levelup_gold"}
FLOOR_NAMES = re.compile(r"^(floor|unlocked_floor|frontier)$")


def test_warden_stats_unchanged():
    for f in range(1, 101):
        assert economy.warden_stats(f) == GOLDEN_WARDENS[f - 1], f"floor {f}"


def test_warden_tuning_reads_the_reference_player():
    base = economy.warden_stats(50)
    with mock.patch.object(economy, "reference_player_hp",
                           side_effect=lambda f: 10_000):
        boosted = economy.warden_stats(50)
    assert boosted[0] > base[0], "warden ATK must derive from reference_player_hp"
    assert boosted[2] == base[2], "HP must not depend on reference_player_hp"


def _calls_with_floor_arg(tree: ast.AST) -> list[str]:
    bad = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        name = (fn.attr if isinstance(fn, ast.Attribute)
                else fn.id if isinstance(fn, ast.Name) else "")
        if name not in LEVEL_TYPED:
            continue
        for arg in node.args:
            if isinstance(arg, ast.Name) and FLOOR_NAMES.match(arg.id):
                bad.append(f"line {node.lineno}: {name}({arg.id})")
    return bad


def test_reference_level_is_the_only_floor_to_level_bridge():
    pkg = pathlib.Path(economy.__file__).parent
    offenders = {}
    for py in sorted(pkg.rglob("*.py")):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        bad = _calls_with_floor_arg(tree)
        if bad:
            offenders[str(py.relative_to(pkg))] = bad
    assert not offenders, (
        "floor-named variables passed to level-typed functions — route "
        f"through economy.reference_level() instead: {offenders}")


def test_gate_and_gear_requirements_unchanged():
    for t in range(1, 11):
        assert economy.gear_player_level_req(t) == GOLDEN_GEAR_GATES[t]
        assert economy.gear_floor_req(t) == GOLDEN_GEAR_FLOOR_GATES[t]
    for f in range(1, 101):
        assert economy.floor_entry_player_level(f) == \
            max(1, min(f - 10, economy.LEVEL_CAP))
    for g in economy.FORGE.values():
        if g.rung < 1:
            continue
        t = int(g.rung)
        raw = g.level or (economy.band_start(t)
                          + (5 if g.rung != t else 0))
        assert economy.rung_player_level_req(g) == \
            min(raw, economy.LEVEL_CAP), g.key
        assert economy.rung_floor_req(g) == \
            (raw if raw > economy.LEVEL_CAP else 0), g.key
