"""075 — measure the 'speed is a shield' hack, and (after the fix) the
new decaying-but-never-zero pursuit.

Run: ../../../luna/.venv/bin/python sim075.py [quick]

Four measures, matching the plan's sim gates:
1. KITE GRID — HP a faster ranged/magic player loses to grind down a
   tanky monster, across speed leads 0..+5. Gate: no collapse to ~0 at
   a big lead; monotonically decreasing; sorcerer no longer near-free.
2. NEVER ZERO — at a +10 lead, the share of long fights where the
   monster still lands at least one pursuit strike. Gate: large majority.
3. SURVIVAL GRID — at-level archer/sorcerer/warrior across floors,
   playing sensibly vs every wilds encounter: win%, death%, HP lost.
   Gate: ranged death rate near the melee reference (melee is untouched
   by 075 and anchors the 039 band), normal hunts < 2% on floors 1-3.
4. FLYER — a flyer closes within ~1 round, cannot be kited, and the
   archer still beats it (the bow is the designed answer).
"""
import copy
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))   # plugin repo root
sys.path.insert(0, ROOT)

from plugin_linear_ascent import economy                      # noqa: E402
from plugin_linear_ascent.content import schema               # noqa: E402
from plugin_linear_ascent.engine import combat, core, state   # noqa: E402

QUICK = len(sys.argv) > 1 and sys.argv[1] == "quick"
N_KITE = 150 if QUICK else 400
N_SURV = 120 if QUICK else 300
N_ZERO = 150 if QUICK else 400
N_FLY = 150 if QUICK else 400

_TEMPLATES: dict[tuple, dict] = {}


def _template(clazz, floor_no):
    """At-level KITTED template, same loadout law as sim039: current
    tier gear set + reference hone. The 039 death bands assume this."""
    key = (clazz, floor_no)
    if key not in _TEMPLATES:
        p = state.new_player(f"tmpl-{clazz}-{floor_no}")
        core.current_scene(p)
        while p["stage"] == "intro":
            core.apply_choice(p, "1")
        core.apply_choice(p, "human")
        core.apply_choice(p, clazz)
        core.apply_choice(p, "", text=f"tmpl-{clazz}")
        p["level"] = floor_no
        p["unlocked_floor"] = floor_no
        t = economy.gear_tier_for_floor(floor_no)
        for slot in ("weapon", "shield", "armor", "shoes"):
            cands = [g for g in economy.FORGE.values()
                     if g.slot == slot and g.tier == t
                     and not getattr(g, "style", "")
                     and g.line in ("", clazz)]
            if cands:
                best = max(cands, key=lambda g: (g.bonus, g.speed))
                p["gear"][slot] = best.slug
        ref = economy.reference_hone(floor_no)
        p["hone"] = {s: ref for s in economy.HONE_SLOTS}
        path = {"warrior": "blade", "archer": "bow",
                "sorcerer": "staff"}[clazz]
        p["training"][path] = 10          # full rank: all ranged moves
        p["held"] = [p["gear"]["weapon"]]
        _TEMPLATES[key] = p
    return _TEMPLATES[key]


def _player(clazz, floor_no, name, boots=None):
    p = copy.deepcopy(_template(clazz, floor_no))
    p["luna_user"] = p["name"] = name     # fresh RNG stream per fight
    if boots is not None:                 # controlled speed lead
        economy.SHOE_SPEED["_simboots"] = boots
        p["gear"]["shoes"] = "_simboots"
    p["hp"] = state.max_hp(p)
    return p


def _act(p, fl):
    """One sensible round for the class in hand.

    NOTE (075 finding): the pre-075 optimal archer play — re-extend to
    gap 3 every time the monster closes a pace, shoot ×1.5 — becomes a
    TREADMILL under pursuit: the monster re-closes most rounds, so the
    archer never shoots and the fight never ends. The sensible play now
    is to shoot from wherever you stand and only step out when caught.
    That is the design working as intended (step-backs are a tool, not
    a stance), and it is what we simulate."""
    e = p["encounter"]
    flying = combat._profile(p).get("flying")
    dtype = combat._damage_type(p)
    caught = e.get("range", "close") == "close"
    if caught and not flying and _faster(p) and dtype == "ranged":
        combat.resolve_fight_action(p, fl, "create_distance")
    elif caught and not flying and _faster(p) and dtype == "magic":
        combat.resolve_fight_action(p, fl, "open_distance")
    else:
        combat.resolve_fight_action(p, fl, "attack")


def _faster(p):
    return economy.player_speed(p) > combat._mspd(p)


def _fight(p, fl, enc, mob_hp=None, rounds=80):
    """Run one fight to the end. Returns (outcome, hp_lost, n_rounds)
    where outcome is 'win', 'death', or 'timeout'."""
    combat.start_encounter(p, fl, enc)
    if mob_hp is not None:
        p["encounter"]["hp"] = mob_hp
    hp0 = p["hp"]
    for r in range(rounds):
        if p["encounter"] is None:
            break
        _act(p, fl)
    died = bool(p["daily"].get("death_save"))
    if died:
        return "death", hp0, r + 1
    if p["encounter"] is None:
        return "win", hp0 - p["hp"], r + 1
    return "timeout", hp0 - p["hp"], rounds


# ── 1. the kite grid ─────────────────────────────────────────────────────

# each class grinds the slow tank its weapon can actually kill:
# bow vs magic_resist = x0.5, magic vs armoured = x1.0 (both speed 3)
KITE_TARGET = {"archer": "wrapped_husk", "sorcerer": "vault_weaver"}


def kite_grid():
    floor = 6
    fl = schema.get_floor(floor)
    maxhp = economy.player_max_hp(floor)
    print(f"\n1. KITE GRID — floor {floor}, slow (3) tanks "
          f"{KITE_TARGET}, 4000-HP grind, {N_KITE} fights/cell, "
          f"player max HP {maxhp}")
    print(f"   {'lead':>5} {'archer HP lost':>15} {'sorcerer HP lost':>17}"
          f"   (HP pool pinned huge; lost = chip taken over the kill)")
    out = {}
    for boots in (0, 1, 2, 3, 5):
        row = {}
        for clazz in ("archer", "sorcerer"):
            enc = next(e for e in fl.encounters
                       if e.id == KITE_TARGET[clazz])
            tot, kills = 0, 0
            for seed in range(N_KITE):
                p = _player(clazz, floor, f"k{boots}{clazz}{seed}",
                            boots=boots)
                p["hp"] = 10_000               # never die — just count HP
                res, lost, _ = _fight(p, fl, enc, mob_hp=4000, rounds=250)
                if res == "win":
                    tot += lost
                    kills += 1
            row[clazz] = tot / max(1, kills)
            row[clazz + "_kill%"] = 100 * kills / N_KITE
        adv = 5 + boots - 3
        out[adv] = row
        print(f"   {adv:+5d} {row['archer']:15.1f} {row['sorcerer']:17.1f}"
              f"   (kill% a:{row['archer_kill%']:.0f} "
              f"s:{row['sorcerer_kill%']:.0f})")
    return out


# ── 2. never zero ────────────────────────────────────────────────────────

def never_zero():
    floor, enc_id = 6, "wrapped_husk"
    fl = schema.get_floor(floor)
    enc = next(e for e in fl.encounters if e.id == enc_id)
    hitters = 0
    for seed in range(N_ZERO):
        p = _player("archer", floor, f"z{seed}", boots=8)   # adv +10
        p["hp"] = 100_000
        _, lost, _ = _fight(p, fl, enc, mob_hp=4000, rounds=200)
        hitters += 1 if lost > 0 else 0
    adv = 5 + 8 - 3
    print(f"\n2. NEVER ZERO — adv +{adv}, 4000-HP grind, {N_ZERO} runs: "
          f"monster landed >=1 hit in {100 * hitters / N_ZERO:.0f}% of runs")
    return hitters / N_ZERO


# ── 3. the survival grid ─────────────────────────────────────────────────

def survival_grid():
    print(f"\n3. SURVIVAL GRID — at-level, every wilds encounter, "
          f"{N_SURV} fights/class/floor, no healing, no fleeing")
    print(f"   {'floor':>5} {'class':>9} {'win%':>6} {'death%':>7} "
          f"{'timeout%':>9} {'HP lost/win':>12} {'maxHP':>6}")
    out = {}
    for floor_no in (2, 6, 10):
        fl = schema.get_floor(floor_no)
        encs = list(fl.encounters)
        maxhp = economy.player_max_hp(floor_no)
        for clazz in ("warrior", "archer", "sorcerer"):
            w = d = t = 0
            lost_on_win = []
            for seed in range(N_SURV):
                enc = encs[seed % len(encs)]
                p = _player(clazz, floor_no, f"s{floor_no}{clazz}{seed}")
                res, lost, _ = _fight(p, fl, enc)
                if res == "win":
                    w += 1
                    lost_on_win.append(lost)
                elif res == "death":
                    d += 1
                else:
                    t += 1
            avg = sum(lost_on_win) / max(1, len(lost_on_win))
            out[(floor_no, clazz)] = (w, d, t, avg)
            print(f"   {floor_no:>5} {clazz:>9} {100 * w / N_SURV:5.0f}% "
                  f"{100 * d / N_SURV:6.1f}% {100 * t / N_SURV:8.1f}% "
                  f"{avg:12.1f} {maxhp:6d}")
    return out


# ── 4. the flyer ─────────────────────────────────────────────────────────

def flyer_check():
    floor = 6
    fl = schema.get_floor(floor)
    fly = [e for e in fl.encounters
           if "fly" in tuple(getattr(e, "traits", ()) or ())]
    if not fly:
        print("\n4. FLYER — no flyer on floor 6; skipped")
        return
    enc = fly[0]
    print(f"\n4. FLYER — floor {floor} {enc.id}, {N_FLY} fights each")
    for clazz in ("archer", "sorcerer"):
        w = d = 0
        rounds_at_range = 0
        total_rounds = 0
        for seed in range(N_FLY):
            p = _player(clazz, floor, f"f{clazz}{seed}")
            combat.start_encounter(p, fl, enc)
            hp0 = p["hp"]
            r = 0
            for r in range(80):
                if p["encounter"] is None:
                    break
                if p["encounter"].get("range") == "at_range":
                    rounds_at_range += 1
                combat.resolve_fight_action(p, fl, "attack")
            total_rounds += r + 1
            if p["daily"].get("death_save"):
                d += 1
            elif p["encounter"] is None:
                w += 1
        print(f"   {clazz:9s} win {100 * w / N_FLY:3.0f}%  "
              f"death {100 * d / N_FLY:4.1f}%  "
              f"rounds spent far away: "
              f"{100 * rounds_at_range / max(1, total_rounds):.0f}% "
              f"(it closes fast)")


if __name__ == "__main__":
    print(f"constants: CAP={economy.PURSUE_CAP} BASE={economy.PURSUE_BASE} "
          f"FLOOR={economy.PURSUE_FLOOR} DECAY={economy.PURSUE_DECAY} "
          f"extras={economy.PURSUIT_EXTRA}")
    sections = [a for a in sys.argv[1:] if a in
                ("kite", "zero", "survival", "flyer")]
    if not sections or "kite" in sections:
        kite_grid()
    if not sections or "zero" in sections:
        never_zero()
    if not sections or "survival" in sections:
        survival_grid()
    if not sections or "flyer" in sections:
        flyer_check()
