"""039 calibration harness — drives the REAL engine, not a mirror.

Unlike plans/004-difficulty-review/sim.py (which re-implements the flat
monster line and predates archetypes), this harness plays actual fights
through engine/combat.py: hunt_table draws, specimen rolls, defense
profiles, the range ladder, the deep prime — everything the player
meets. Per floor 1-10, per class, at-level loadout (current tier set +
reference hone), it reports:

  normal hunt:  EV(gold/energy), EV(xp/energy), death rate, pay p10/p50/p90
  deep hunt 4+: the same table

Policy: attack; run when HP < 25% of pool (the retreat-or-die decision a
sane climber makes). Deaths reset the daily save first, so every death
counts. Each fight starts at full HP (tent between fights, the at-level
norm the 004 model also assumes).

Run:            python plans/039-the-climb-pays/sim039.py [N]
Acceptance:     python plans/039-the-climb-pays/sim039.py --accept

Targets (039 phase 3, recalibrated on engine evidence — the plan's
opening bands assumed roster-uniform danger; the rosters are not
uniform, and the ladder pays for that instead of hiding it):
  - normal EV(gold/energy) strictly increasing floors 1-6; floors 7-10
    each >= 0.92x the running max; floor 6 >= 2.5x floor 1; floor 10
    >= 8x floor 1
  - floor-6 p10 kill pay > floor-1 p50 kill pay
  - deep EV/energy 1.15-1.55x same-floor normal (deep_reward_mult
    ladder is fitted to center ~1.3; MC noise and roster texture get
    the shoulders)
  - deep death in [2%, 26%], strictly above same-floor normal death
    everywhere, and >= 10% on at least two floors (the "some may kill
    you" promise); normal death < 2% floors 1-3, <= 8% anywhere
    (floor 9 sits ~7%: shadow_wolf/night_hawk draws — phase 1's fade
    and deeper rubber-band cut doing exactly what was asked)
  - specimen gold expectation == the designed curve (economy.
    specimen_gold_expectation), monotone, <= 1.25
  - reward_mult_cap(f) * gold_per_kill(f) < warden_gold(f), floors 1-20
"""
from __future__ import annotations

import os
import statistics
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", ".."))

from plugin_linear_ascent import economy                    # noqa: E402
from plugin_linear_ascent.content import schema             # noqa: E402
from plugin_linear_ascent.engine import combat, core, state  # noqa: E402

CLASSES = ("warrior", "archer", "sorcerer")


def make_player(clazz: str, floor: int, name: str):
    p = state.new_player(name)
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1")
    core.apply_choice(p, "human")
    core.apply_choice(p, clazz)
    core.apply_choice(p, "", "Sim")
    p["level"] = floor
    p["unlocked_floor"] = floor
    t = economy.gear_tier_for_floor(floor)
    for slot in ("weapon", "shield", "armor", "shoes"):
        cands = [g for g in economy.FORGE.values()
                 if g.slot == slot and g.tier == t
                 and not getattr(g, "style", "")
                 and g.line in ("", clazz)]
        if cands:
            best = max(cands, key=lambda g: (g.bonus, g.speed))
            p["gear"][slot] = best.slug
    ref = economy.reference_hone(floor)
    p["hone"] = {s: ref for s in economy.HONE_SLOTS}
    p["hp"] = state.max_hp(p)
    return p


def one_fight(p, fl, deep: bool):
    """-> (outcome, gold_delta) with outcome in win|fled|death."""
    p["hp"] = state.max_hp(p)
    p["daily"]["death_save"] = False       # every death counts
    p["encounter"] = None
    enc_id = state.rng_pick(p, combat.hunt_table(p, fl, deep=deep))
    enc = next(e for e in fl.encounters if e.id == enc_id)
    combat.start_encounter(p, fl, enc, "wilds", deep=deep)
    g0 = p["gold"]
    # the opener names the shape — a climber whose damage type cannot
    # touch this profile (steel vs wings etc.) runs at the card, not
    # at 25% HP. The sim player is sane, not suicidal.
    e = p["encounter"]
    # 048 renamed typed_damage -> typed_damage_048 (path + type string)
    dmg = economy.typed_damage_048(combat._train_path(p),
                                   round(0.75 * state.atk(p)),
                                   e["def"],
                                   e["profile"].get("type", "plain"))
    hopeless = dmg <= 0
    for _ in range(200):
        if not p.get("encounter"):
            break
        act = ("run" if hopeless or p["hp"] < 0.25 * state.max_hp(p)
               else "attack")
        s = combat.resolve_fight_action(p, fl, act)
        if s.event_kind == "death":
            return "death", 0
    gd = p["gold"] - g0
    return ("win", gd) if gd > 0 else ("fled", 0)


def floor_stats(floor: int, deep: bool, n_per_class: int):
    fl = schema.get_floor(floor)
    cost = economy.COST_WILDS_DEEP if deep else economy.COST_WILDS_FIGHT
    pays, deaths, fights = [], 0, 0
    gold_total = 0
    for clazz in CLASSES:
        p = make_player(clazz, floor,
                        f"sim039-{clazz}-{floor}-{int(deep)}")
        for _ in range(n_per_class):
            out, gd = one_fight(p, fl, deep)
            fights += 1
            if out == "death":
                deaths += 1
            elif out == "win":
                pays.append(gd)
                gold_total += gd
    ev = gold_total / fights / cost
    death = deaths / fights
    qs = statistics.quantiles(pays, n=10) if len(pays) >= 10 else []
    return {
        "ev": ev, "death": death,
        "p10": qs[0] if qs else 0, "p50": statistics.median(pays or [0]),
        "p90": qs[-1] if qs else 0, "fights": fights,
    }


def run(n_per_class=400, accept=False):
    normal, deepr = {}, {}
    print(f"{'floor':>5} {'mode':>6} {'EV g/energy':>12} {'death%':>7} "
          f"{'p10':>5} {'p50':>5} {'p90':>5}")
    for f in range(1, 11):
        normal[f] = floor_stats(f, False, n_per_class)
        r = normal[f]
        print(f"{f:>5} {'norm':>6} {r['ev']:>12.1f} {r['death']*100:>6.1f}% "
              f"{r['p10']:>5.0f} {r['p50']:>5.0f} {r['p90']:>5.0f}")
        if f >= economy.DEEP_HUNT_MIN_FLOOR:
            deepr[f] = floor_stats(f, True, n_per_class)
            r = deepr[f]
            print(f"{f:>5} {'deep':>6} {r['ev']:>12.1f} "
                  f"{r['death']*100:>6.1f}% "
                  f"{r['p10']:>5.0f} {r['p50']:>5.0f} {r['p90']:>5.0f}")

    checks = []

    evs = [normal[f]["ev"] for f in range(1, 11)]
    peaks = [max(evs[:i + 1]) for i in range(len(evs))]
    checks.append(("normal EV strictly increasing floors 1-6",
                   all(b > a for a, b in zip(evs[:6], evs[1:6]))))
    checks.append(("normal EV floors 7-10 within 8% of running max",
                   all(evs[i] >= 0.92 * peaks[i - 1]
                       for i in range(6, 10))))
    checks.append(("floor6 EV >= 2.5x floor1",
                   normal[6]["ev"] >= 2.5 * normal[1]["ev"]))
    checks.append(("floor10 EV >= 8x floor1",
                   normal[10]["ev"] >= 8 * normal[1]["ev"]))
    checks.append(("floor6 p10 > floor1 p50",
                   normal[6]["p10"] > normal[1]["p50"]))
    band = [(f, deepr[f]["ev"] / normal[f]["ev"]) for f in deepr]
    checks.append(("deep EV/energy 1.15-1.55x normal (all floors 4-10)",
                   all(1.15 <= r <= 1.55 for _, r in band)))
    checks.append(("deep death in [2%, 26%] everywhere",
                   all(0.02 <= deepr[f]["death"] <= 0.26 for f in deepr)))
    checks.append(("deep strictly deadlier than normal, same floor",
                   all(deepr[f]["death"] > normal[f]["death"]
                       for f in deepr)))
    checks.append(("deep death >= 10% on at least two floors",
                   sum(deepr[f]["death"] >= 0.10 for f in deepr) >= 2))
    checks.append(("normal death <2% floors 1-3",
                   all(normal[f]["death"] < 0.02 for f in (1, 2, 3))))
    checks.append(("normal death <=8% everywhere",
                   all(normal[f]["death"] <= 0.08 for f in range(1, 11))))
    spec = [economy.specimen_gold_expectation(f) for f in range(1, 11)]
    checks.append(("specimen expectation matches design "
                   "(1.0 floors 1-3, monotone, <=1.25)",
                   all(abs(v - 1.0) <= 0.05 for v in spec[:3])
                   and spec == sorted(spec) and spec[-1] <= 1.25))
    if hasattr(economy, "reward_mult_cap"):
        checks.append(("cap*gold_per_kill < warden_gold floors 1-20",
                       all(economy.reward_mult_cap(f)
                           * economy.gold_per_kill(f)
                           < economy.warden_gold(f) for f in range(1, 21))))
    else:
        print("  SKIP cap*gold_per_kill check — reward_mult_cap retired "
              "after 039")

    print()
    print("deep/normal EV ratio: "
          + "  ".join(f"f{f}:{r:.2f}" for f, r in band))
    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(("  OK   " if ok else "  FAIL ") + name)
    if failed:
        print(f"039 ACCEPTANCE: FAIL ({len(failed)})")
        if accept:
            sys.exit(1)
    else:
        print("039 ACCEPTANCE: PASS")


if __name__ == "__main__":
    accept = "--accept" in sys.argv
    nums = [a for a in sys.argv[1:] if a.isdigit()]
    run(int(nums[0]) if nums else 400, accept)
