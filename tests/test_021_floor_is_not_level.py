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

# warden_stats(f) for f in 1..100, captured pre-refactor.
GOLDEN_WARDENS = [
    (14, 3, 70), (16, 6, 93), (19, 9, 116), (23, 12, 139), (28, 15, 162),
    (31, 18, 184), (36, 21, 207), (39, 24, 230), (43, 27, 253), (47, 30, 276),
    (48, 33, 298), (50, 36, 321), (52, 39, 344), (56, 42, 367), (60, 45, 390),
    (63, 48, 412), (67, 51, 435), (71, 54, 458), (75, 57, 481), (79, 60, 504),
    (73, 63, 526), (74, 66, 549), (76, 69, 572), (80, 72, 595), (83, 75, 618),
    (87, 78, 640), (91, 81, 663), (94, 84, 686), (98, 87, 709), (101, 90, 732),
    (102, 93, 773), (104, 96, 816), (106, 99, 860), (110, 102, 905),
    (114, 105, 952), (119, 108, 998), (122, 111, 1047), (126, 114, 1097),
    (131, 117, 1148), (134, 120, 1200), (137, 123, 1252), (139, 126, 1306),
    (142, 129, 1362), (146, 132, 1419), (151, 135, 1477), (154, 138, 1534),
    (160, 141, 1595), (164, 144, 1656), (169, 147, 1718), (174, 150, 1782),
    (175, 153, 1845), (177, 156, 1911), (181, 159, 1978), (185, 162, 2046),
    (191, 165, 2116), (195, 168, 2185), (201, 171, 2256), (205, 174, 2329),
    (212, 177, 2403), (216, 180, 2478), (217, 183, 2552), (220, 186, 2630),
    (225, 189, 2708), (229, 192, 2788), (236, 195, 2869), (239, 198, 2949),
    (245, 201, 3032), (251, 204, 3116), (257, 207, 3201), (263, 210, 3288),
    (265, 213, 3374), (268, 216, 3462), (272, 219, 3552), (278, 222, 3644),
    (284, 225, 3736), (289, 228, 3827), (295, 231, 3922), (302, 234, 4017),
    (308, 237, 4114), (314, 240, 4212), (316, 243, 4309), (319, 246, 4409),
    (324, 249, 4510), (330, 252, 4613), (336, 255, 4717), (343, 258, 4819),
    (350, 261, 4925), (356, 264, 5032), (363, 267, 5141), (368, 270, 5250),
    (372, 273, 5358), (376, 276, 5470), (380, 279, 5583), (385, 282, 5697),
    (393, 285, 5812), (400, 288, 5925), (407, 291, 6043), (415, 294, 6161),
    (421, 297, 6281), (428, 300, 6402),
]

GOLDEN_GEAR_GATES = {1: 1, 2: 11, 3: 21, 4: 31, 5: 41,
                     6: 51, 7: 61, 8: 71, 9: 81, 10: 91}

LEVEL_TYPED = {"player_max_hp", "player_atk", "player_def",
               "xp_need", "levelup_gold", "energy_cap"}
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
    for f in range(1, 101):
        assert economy.floor_entry_player_level(f) == max(1, f - 10)
    for g in economy.FORGE.values():
        if g.rung < 1:
            continue
        t = int(g.rung)
        expected = g.level or (economy.band_start(t)
                               + (5 if g.rung != t else 0))
        assert economy.rung_player_level_req(g) == expected, g.key
