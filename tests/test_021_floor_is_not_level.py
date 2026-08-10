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
# Regenerated again ON PURPOSE for 025 §4 — floors 2-10 only, ATK only:
# band 1 now sells a rung per level, so the at-level climber there is
# better armed and the gate hits back harder. Floor 1 and every floor
# from 11 up are untouched, and the HP column is still the original curve.
# Regenerated ON PURPOSE for 046: every stat rides the pillar
# (1.3^(F−1)), warden HP carries the rise (×1.02^(F−1)) on top.
GOLDEN_WARDENS = [
    (15, 3, 70), (19, 4, 93), (27, 5, 124), (37, 7, 163), (52, 9, 217), (64,
    11, 289), (84, 14, 382), (109, 19, 507), (135, 24, 673), (176, 32, 891),
    (230, 41, 1182), (225, 54, 1566), (229, 70, 2077), (292, 91, 2755),
    (381, 118, 3652), (485, 154, 4843), (631, 200, 6422), (820, 260, 8516),
    (1051, 337, 11292), (1367, 439, 14972), (2604, 570, 19853), (2613, 741,
    26324), (2678, 964, 34907), (3453, 1253, 46286), (4456, 1628, 61376),
    (5791, 2117, 81385), (7474, 2752, 107916), (9649, 3578, 143097), (12545,
    4651, 189747), (16201, 6046, 251604), (30861, 7860, 333627), (28773,
    10218, 442388), (27064, 13283, 586608), (33408, 17268, 777843), (41734,
    22449, 1031419), (52666, 29184, 1367662), (66901, 37939, 1813520),
    (85478, 49320, 2404727), (109624, 64116, 3188667), (140998, 83351,
    4228173), (319371, 108357, 5606558), (310411, 140864, 7434295), (303720,
    183123, 9857876), (393246, 238059, 13071544), (509723, 309477,
    17332866), (660850, 402320, 22983380), (857179, 523017, 30475962),
    (1112559, 679922, 40411127), (1443993, 883898, 53585153), (1875077,
    1149067, 71053914), (4265355, 1493788, 94217489), (4173412, 1941924,
    124932391), (4107049, 2524501, 165660350), (5334465, 3281852,
    219665625), (6930719, 4266407, 291276620), (9003210, 5546329,
    386232796), (11696084, 7210228, 512144688), (15195110, 9373296,
    679103858), (19741705, 12185285, 900491713), (25654061, 15840870,
    1194052013), (58009705, 20593132, 1583312968), (57020264, 26771071,
    2099472997), (56265499, 34802392, 2783901194), (73111068, 45243110,
    3691452983), (95001990, 58816043, 4894866655), (123449740, 76460856,
    6490593186), (160418680, 99399113, 8606526564), (208435251, 129218846,
    11412254225), (270863714, 167984500, 15132649102), (351953434,
    218379850, 20065892708), (791957571, 283893805, 26607373731),
    (780799500, 369061947, 35281377567), (772300693, 479780531,
    46783106655), (1003581212, 623714690, 62034399425), (1304270270,
    810829097, 82257613638), (1694907415, 1054077827, 109073595684),
    (2202575442, 1370301175, 144631587876), (2862097811, 1781391527,
    191781485524), (3719481567, 2315808985, 254302249805), (4833766446,
    3010551681, 337204783240), (10832001888, 3913717185, 447133542576),
    (10704618250, 5087832341, 592899077457), (10609471129, 6614182043,
    786184176708), (13787549735, 8598436656, 1042480218315), (17917880255,
    11177967653, 1382328769486), (23285843458, 14531357948, 1832967948337),
    (30262358915, 18890765333, 2430515499496), (39329527069, 24557994933,
    3222863552331), (51113958821, 31925393412, 4273517070389), (66430097478,
    41503011436, 5666683635337), (148353286571, 53953914867, 7514022500457),
    (146902218017, 70140089327, 9963593835606), (145829484323, 91182116125,
    13211725426012), (189525451862, 118536750963, 17518747914892),
    (246317152331, 154097776251, 23229859735147), (320143496239,
    200327109127, 30802794008804), (416083085733, 260425241865,
    40844504855674), (540757636547, 338552814424, 54159813438626),
    (702824216929, 440118658751, 71815912619617), (913470296403,
    572154256377, 95227900133612),
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
    # 046: the boost must clear the pillar-riding reference (a flat
    # 10,000 was a boost once; at floor 50 it is a 2000× nerf now)
    boost = economy.reference_player_hp(50) * 2
    with mock.patch.object(economy, "reference_player_hp",
                           side_effect=lambda f: boost):
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
        # 025: a rung's threshold is how far INTO its band it sits — T.5
        # still lands at band_start+5, and band 1's new steps one apart
        raw = g.level or (economy.band_start(t) + round((g.rung - t) * 10))
        assert economy.rung_player_level_req(g) == \
            min(raw, economy.LEVEL_CAP), g.slug
        assert economy.rung_floor_req(g) == \
            (raw if raw > economy.LEVEL_CAP else 0), g.slug
