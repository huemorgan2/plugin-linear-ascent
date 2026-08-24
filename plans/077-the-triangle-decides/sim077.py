"""077 — the win/lose grid: does the triangle decide the fight?

Run: ../../../luna/.venv/bin/python sim077.py [quick]

Every class vs every monster type on floor 6, at levels -2/at/+2,
N fights per cell (thousands total), real engine, post-075 policy
(shoot in place, step out only when caught), no healing, no fleeing,
80-round cap. A 'timeout' is a stall — in real play that is a flee.

Gates (roy's law):
- right weapon at-level: win >= 90%
- glance cells (bow-vs-armoured, magic-vs-magic_resist): win <= 5%
  at-level AND at +2 (brute force does not clear a glance)
- zero cell (blade-vs-fly): win == 0 at every level
- half cells (0.5/0.6) at +2: win >= 90% (brute force allowed)
- right weapon at-level: death <= 5% (correct play stays survivable)
"""
import copy
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)

from plugin_linear_ascent import economy                      # noqa: E402
from plugin_linear_ascent.content import schema               # noqa: E402
from plugin_linear_ascent.engine import combat, core, state   # noqa: E402

QUICK = "quick" in sys.argv[1:]
N = 100 if QUICK else 300
FLOOR_NO = 6
ENC_OF_TYPE = {"fly": "grave_moth", "armoured": "vault_weaver",
               "magic_resist": "wrapped_husk", "plain": "guano_vole"}
PATH_OF = {"warrior": "blade", "archer": "bow", "sorcerer": "staff"}

_TEMPLATES: dict[tuple, dict] = {}


def _template(clazz, level):
    key = (clazz, level)
    if key not in _TEMPLATES:
        p = state.new_player(f"t77-{clazz}-{level}")
        core.current_scene(p)
        while p["stage"] == "intro":
            core.apply_choice(p, "1")
        core.apply_choice(p, "human")
        core.apply_choice(p, clazz)
        core.apply_choice(p, "", text=f"t77-{clazz}")
        p["level"] = level
        p["unlocked_floor"] = max(level, FLOOR_NO)
        t = economy.gear_tier_for_floor(level)
        for slot in ("weapon", "shield", "armor", "shoes"):
            cands = [g for g in economy.FORGE.values()
                     if g.slot == slot and g.tier == t
                     and not getattr(g, "style", "")
                     and g.line in ("", clazz)]
            if cands:
                best = max(cands, key=lambda g: (g.bonus, g.speed))
                p["gear"][slot] = best.slug
        p["hone"] = {s: economy.reference_hone(level)
                     for s in economy.HONE_SLOTS}
        p["training"][PATH_OF[clazz]] = 10
        p["held"] = [p["gear"]["weapon"]]
        _TEMPLATES[key] = p
    return _TEMPLATES[key]


def _player(clazz, level, name):
    p = copy.deepcopy(_template(clazz, level))
    p["luna_user"] = p["name"] = name
    p["hp"] = state.max_hp(p)
    return p


def _act(p, fl):
    """Post-075 sensible play: shoot in place, step out when caught."""
    e = p["encounter"]
    flying = combat._profile(p).get("flying")
    dtype = combat._damage_type(p)
    caught = e.get("range", "close") == "close"
    faster = economy.player_speed(p) > combat._mspd(p)
    if caught and not flying and faster and dtype == "ranged":
        combat.resolve_fight_action(p, fl, "create_distance")
    elif caught and not flying and faster and dtype == "magic":
        combat.resolve_fight_action(p, fl, "open_distance")
    else:
        combat.resolve_fight_action(p, fl, "attack")


def cell(clazz, mtype, level):
    fl = schema.get_floor(FLOOR_NO)
    enc = next(e for e in fl.encounters if e.id == ENC_OF_TYPE[mtype])
    w = d = t = 0
    rounds_on_win = []
    for seed in range(N):
        p = _player(clazz, level, f"c{clazz}{mtype}{level}{seed}")
        combat.start_encounter(p, fl, enc)
        r = 0
        for r in range(80):
            if p["encounter"] is None:
                break
            _act(p, fl)
        if p["daily"].get("death_save"):
            d += 1
        elif p["encounter"] is None:
            w += 1
            rounds_on_win.append(r + 1)
        else:
            t += 1
    avg_r = sum(rounds_on_win) / max(1, len(rounds_on_win))
    return {"win": w / N, "death": d / N, "timeout": t / N, "rounds": avg_r}


def main():
    print(f"077 grid — floor {FLOOR_NO}, {N} fights/cell, "
          f"GLANCE_MULT={economy.GLANCE_MULT}")
    grid = {}
    print(f"   {'matchup':<28} {'L-2':>18} {'at-level':>18} {'L+2':>18}")
    for clazz in ("warrior", "archer", "sorcerer"):
        path = PATH_OF[clazz]
        for mtype in ("fly", "armoured", "magic_resist", "plain"):
            mult = economy.TYPE_MULT[mtype][path]
            row = []
            for level in (FLOOR_NO - 2, FLOOR_NO, FLOOR_NO + 2):
                c = grid[(clazz, mtype, level)] = cell(clazz, mtype, level)
                row.append(f"{100 * c['win']:3.0f}%w "
                           f"{100 * c['death']:3.0f}%d "
                           f"[{c['rounds']:4.1f}r]")
            print(f"   {path:>6} vs {mtype:<12} (x{mult:g}) "
                  + " ".join(f"{r:>18}" for r in row))

    at, p2 = FLOOR_NO, FLOOR_NO + 2
    checks = [
        ("right weapon at-level wins >=90% "
         "(bow-fly, staff-armoured, blade-magic_resist, all-plain)",
         all(grid[k]["win"] >= 0.90 for k in [
             ("archer", "fly", at), ("sorcerer", "armoured", at),
             ("warrior", "magic_resist", at),
             ("warrior", "plain", at), ("archer", "plain", at),
             ("sorcerer", "plain", at)])),
        ("glance cells win <=5% at-level",
         grid[("archer", "armoured", at)]["win"] <= 0.05
         and grid[("sorcerer", "magic_resist", at)]["win"] <= 0.05),
        ("glance cells win <=5% even at +2 (no brute force)",
         grid[("archer", "armoured", p2)]["win"] <= 0.05
         and grid[("sorcerer", "magic_resist", p2)]["win"] <= 0.05),
        ("zero cell (blade-vs-fly) win == 0 at every level",
         all(grid[("warrior", "fly", lv)]["win"] == 0
             for lv in (at - 2, at, p2))),
        ("half cells at +2 win >=90% (brute force allowed)",
         all(grid[k]["win"] >= 0.90 for k in [
             ("warrior", "armoured", p2), ("archer", "magic_resist", p2),
             ("sorcerer", "fly", p2)])),
        ("right weapon at-level death <=5%",
         all(grid[k]["death"] <= 0.05 for k in [
             ("archer", "fly", at), ("sorcerer", "armoured", at),
             ("warrior", "magic_resist", at)])),
    ]
    print()
    fails = 0
    for name, ok in checks:
        print(("  OK   " if ok else "  FAIL ") + name)
        fails += 0 if ok else 1
    print("077 ACCEPTANCE: " + ("PASS" if not fails else f"FAIL ({fails})"))
    return fails


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
