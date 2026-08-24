"""075 — measure the 'speed is a shield' hack, and (after the fix) the
new decaying-but-never-zero pursuit.

Run: ../../../luna/.venv/bin/python sim075.py
(or any venv with the plugin importable)

Reports HP a faster ranged/magic player loses to grind down a tanky
monster, across speed leads. Today: the loss collapses toward 0 as the
lead grows (the hack). After the fix: it should stay in a survivable
band, decay monotonically, and never hit 0.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))   # plugin repo root
sys.path.insert(0, ROOT)

from plugin_linear_ascent import economy                      # noqa: E402
from plugin_linear_ascent.content import schema               # noqa: E402
from plugin_linear_ascent.engine import combat, core, state   # noqa: E402

SHOE = 0   # set per run below


def _fresh(name):
    return state.new_player(name)


def _character(clazz, name):
    p = _fresh(name)
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1")
    core.apply_choice(p, "human")
    core.apply_choice(p, clazz)
    core.apply_choice(p, "", text=name)
    path = {"warrior": "blade", "archer": "bow", "sorcerer": "staff"}[clazz]
    slug = {"warrior": "rusted_sword", "archer": "basic_bow",
            "sorcerer": "worn_staff"}[clazz]
    p["training"][path] = 10                     # full rank: all ranged moves
    p["gear"]["weapon"] = slug
    p["held"] = [slug]
    return p


def _player(clazz, floor_no, name):
    p = _character(clazz, name)
    p["level"] = floor_no
    p["hp"] = economy.player_max_hp(floor_no)
    return p


def kite_measure(clazz, enc_id, floor_no, mob_hp=4000, rounds=60, n=400):
    fl = schema.get_floor(floor_no)
    enc = next(e for e in fl.encounters if e.id == enc_id)
    total_dmg = 0
    pspd = mspd = 0
    for seed in range(n):
        p = _player(clazz, floor_no, f"{clazz}-{enc_id}-{seed}")
        economy.SHOE_SPEED["_simboots"] = SHOE
        p["gear"]["shoes"] = "_simboots"
        p["hp"] = 10_000                          # never die — just count HP
        combat.start_encounter(p, fl, enc)
        e = p["encounter"]
        pspd, mspd = economy.player_speed(p), e["profile"]["speed"]
        e["hp"] = mob_hp
        hp0 = p["hp"]
        for _ in range(rounds):
            if p["encounter"] is None:
                break
            rng = p["encounter"].get("range", "close")
            gap = p["encounter"].get("gap", 1)
            if rng == "close":
                combat.resolve_fight_action(p, fl, "open_distance")
            elif clazz == "archer" and gap < economy.GAP_MAX:
                combat.resolve_fight_action(p, fl, "create_distance")
            else:
                combat.resolve_fight_action(p, fl, "attack")
        total_dmg += hp0 - p["hp"]
    economy.SHOE_SPEED.pop("_simboots", None)
    return pspd, mspd, total_dmg / n


if __name__ == "__main__":
    floor = 6
    enc = "wrapped_husk"                           # slow, tanky
    print(f"floor {floor} · {enc} · player max HP "
          f"{economy.player_max_hp(floor)}")
    for boots in (0, 1, 2, 4):
        SHOE = boots
        for clazz in ("archer", "sorcerer"):
            pspd, mspd, dmg = kite_measure(clazz, enc, floor)
            print(f"  boots+{boots}  {clazz:9s} "
                  f"adv={pspd - mspd:+d}  HP lost/kill = {dmg:6.1f}")
