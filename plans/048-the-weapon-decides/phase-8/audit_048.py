"""048 phase 8 — three-question audit.

One monster of each sign (the shipped flip table, all floor 4):
glare_moth (fly), lamptree_wight (armoured), lamp_eater (magic_resist).
For each: the fair path and the countered path at ranks 0/5/10.
Q1 can I lose?  -> winrate
Q2 can I tell why?  -> verdict lines + defeat cause captured
Q3 can I change it? -> the lever named on the card
"""
import sys

sys.path.insert(0, "tests")
import conftest  # noqa: F401  (stubs luna_sdk)
import test_017_damage_types as t17

from plugin_linear_ascent import economy
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat, state

CLAZZ_OF_PATH = {"blade": "warrior", "bow": "archer", "staff": "sorcerer"}
FLOOR = 4
N = 200

fl = schema.get_floor(FLOOR)
ENC = {e.id: e for e in fl.encounters}
CASES = [
    ("glare_moth", "fly", "bow", "blade"),
    ("lamptree_wight", "armoured", "staff", "bow"),
    ("lamp_eater", "magic_resist", "blade", "staff"),
]


def sim(path, rank, enc, seed):
    clazz = CLAZZ_OF_PATH[path]
    p = t17.reference_player(clazz, FLOOR, rank=rank)
    p["held"] = [p["gear"]["weapon"]]     # real docs heal this on load
    p["luna_user"] = f"audit-{path}-{rank}-{enc.id}-{seed}"
    rounds = 0
    orig = state.world_day
    state.world_day = lambda at=None: t17._SIM_DAY
    death_lines = None
    try:
        combat.start_encounter(p, fl, enc)
        verdict = combat._verdict(p)
        while p["encounter"] is not None and rounds < 60:
            rounds += 1
            can_open = economy.player_speed(p) > combat._mspd(p)
            if path == "bow" and can_open and \
                    p["encounter"].get("range", "close") == "close":
                s = combat.resolve_fight_action(p, fl, "open_distance")
            else:
                s = combat.resolve_fight_action(p, fl, "attack")
            if s.event_kind == "death" or p["hp"] <= 0:
                death_lines = list(s.body_lines)
                return False, verdict, death_lines
        return p["encounter"] is None, verdict, None
    finally:
        state.world_day = orig


for enc_id, sign, fair, wrong in CASES:
    enc = ENC[enc_id]
    print(f"=== {enc_id} ({sign}) — traits {enc.traits} ===")
    for path in (fair, wrong):
        for rank in (0, 5, 10):
            wins = 0
            sample_verdict = sample_death = None
            for s in range(N):
                won, verdict, death = sim(path, rank, enc, s)
                wins += won
                if sample_verdict is None:
                    sample_verdict = verdict
                if death and sample_death is None:
                    sample_death = death
            tag = "FAIR " if path == fair else "WRONG"
            print(f"  {tag} {path:5s} rank {rank:2d}: "
                  f"win {wins / N:.2f}")
            if rank == 5 and sample_verdict:
                for ln in sample_verdict:
                    print(f"      verdict: {ln}")
            if sample_death:
                for ln in sample_death[:3]:
                    print(f"      death: {ln}")
                sample_death = None
    print()
