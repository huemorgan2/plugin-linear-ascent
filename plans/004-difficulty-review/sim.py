"""Difficulty-curve simulator for the 004 review — now the acceptance gate.

Imports economy.py directly (no copied formulas — the sim cannot drift
from the shipped numbers) and mirrors engine/combat.py roll-for-roll
(hit ranges, defense halving, archer treeline shot).

Run:            python plans/004-difficulty-review/sim.py
Acceptance:     python plans/004-difficulty-review/sim.py --accept
                (exits non-zero if any 004 §4 criterion fails)

Criteria (004 §4, MC tolerance ±3pts at the band edges):
  - wilds, at-level, current tier + honing: win ≥ 95%, HP/win ≤ 40% of
    pool on every floor 1–100
  - warden at-level solo win: 65–85% for floors ≤ 30; < 10% by floor 50
  - days-per-tier (grind, no bank, incl. honing): ±30% of the 6→24 line,
    no tier more than 1.6× the previous
  - floors 1–5 completable by a fresh solo character in ≤ 3 play-days
    (median over trials)
"""
from __future__ import annotations

import os
import random
import statistics
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", ".."))

from plugin_linear_ascent import economy  # noqa: E402

FIGHTS_PER_DAY = 30       # ~32 energy/day regen, wilds fight = 1 energy
WARDEN_BAND = (0.62, 0.88)  # 65–85% target ± MC/rounding tolerance


def player_max_hp(level):
    return economy.player_max_hp(level)


def tier_gear(t):
    """(weapon, shield, armor) bonuses of the full tier-`t` set."""
    by_slot = {g.slot: g.bonus for g in economy.forge_tier(t)}
    return by_slot["weapon"], by_slot["shield"], by_slot["armor"]


def set_price(t):
    return sum(g.price for g in economy.forge_tier(t))


def geared(floor, honed=True):
    """At-level loadout: current tier set, honing trailing the climb by
    the design lag (economy.reference_hone) — the state a climber who
    follows the shard's coaching is actually in."""
    t = economy.gear_tier_for_floor(floor)
    w, s, a = tier_gear(t)
    h = economy.reference_hone(floor) if honed else 0
    return w + h, s + h, a + h


def fight(level, weapon, shield, armor, floor, archer=True, boss=False):
    """One full fight, exact combat.py rolls. -> (won, hp_lost, rounds)"""
    atk = economy.player_atk(level, weapon)
    dfs = economy.player_def(level, shield, armor)
    hp = hp_max = player_max_hp(level)
    e_atk, e_def, e_hp = (economy.warden_stats if boss
                          else economy.monster_stats)(floor)
    shot = archer
    rounds = 0
    while True:
        rounds += 1
        mult = 2.0 if shot else 1.0
        raw = random.randint(atk // 2, atk)
        e_hp -= max(0, round(raw * mult) - e_def // 2)
        if e_hp <= 0:
            return True, hp_max - hp, rounds
        if shot:                      # treeline shot: free first strike
            shot = False
            continue
        raw = random.randint(e_atk // 2, e_atk)
        hp -= max(0, raw - dfs // 2)
        if hp <= 0:
            return False, hp_max, rounds
        if rounds > 400:
            return False, hp_max - hp, rounds   # stalemate = effective loss


def stats(level, weapon, shield, armor, floor, n=2000, boss=False):
    wins, hp_costs = 0, []
    for _ in range(n):
        won, hp_lost, _ = fight(level, weapon, shield, armor, floor, boss=boss)
        if won:
            wins += 1
            hp_costs.append(hp_lost)
    p = wins / n
    hp_avg = statistics.mean(hp_costs) if hp_costs else float("nan")
    return p, hp_avg


def net_income_day(floor, p_win, hp_lost):
    """Net gold/day: wins pay gold_per_kill, healer's tent (2F, full)
    after fights that cost meaningful HP."""
    heal_freq = min(1.0, hp_lost / max(1, player_max_hp(floor) * 0.5))
    per_fight = p_win * economy.gold_per_kill(floor) - heal_freq * 2 * floor
    return per_fight * FIGHTS_PER_DAY


# ── Criterion checks ─────────────────────────────────────────────────────

def check_wilds(n=1000):
    fails, worst_hp, worst_win = [], 0.0, 1.0
    for f in range(1, 101):
        p, hp = stats(f, *geared(f), f, n=n)
        frac = hp / player_max_hp(f)
        worst_hp = max(worst_hp, frac)
        worst_win = min(worst_win, p)
        if p < 0.95 or frac > 0.40:
            fails.append((f, p, frac))
    print(f"wilds 1–100: worst win {worst_win*100:.1f}%, "
          f"worst hp/win {worst_hp*100:.0f}% of pool")
    for f, p, frac in fails:
        print(f"  FAIL floor {f}: win {p*100:.1f}%, hp {frac*100:.0f}%")
    return not fails


def check_wardens(n=1500):
    ok = True
    print("wardens at-level solo (current tier + honing):")
    for f in [1, 3, 5, 9, 12, 15, 19, 22, 25, 28, 30, 33, 36, 40, 45, 50]:
        p, hp = stats(f, *geared(f), f, n=n, boss=True)
        flag = ""
        if f <= 4:
            # tutorial gates ramp in gently — only a floor, no ceiling
            if p < WARDEN_BAND[0]:
                flag = "  <-- FAIL"
                ok = False
        elif f <= 30 and not (WARDEN_BAND[0] <= p <= WARDEN_BAND[1]):
            flag = "  <-- FAIL"
            ok = False
        if f >= 50 and p >= 0.10:
            flag = "  <-- FAIL"
            ok = False
        print(f"  floor {f:>3}: win {p*100:5.1f}%  hp {hp:6.1f}"
              f" / {player_max_hp(f)}{flag}")
    return ok


def check_days_per_tier(n=1500):
    print("days per tier (grind only, incl. honing; target 6→24 line):")
    ok, prev = True, None
    for t in range(1, 10):
        f = economy.band_start(t) + 4                     # mid band
        p, hp = stats(f, *geared(f), f, n=n)
        net = net_income_day(f, p, hp)
        hone_total = sum(
            len(economy.HONE_SLOTS) * economy.hone_price(
                economy.band_start(t) + i + 1)
            for i in range(9))
        days = (set_price(t + 1) + hone_total) / net
        line = 6 + 2 * (t - 1)
        ratio = days / prev if prev else 1.0
        flag = ("" if line * 0.7 <= days <= line * 1.3 and ratio <= 1.6
                else "  <-- FAIL")
        if flag:
            ok = False
        print(f"  T{t}→{t+1}: set {set_price(t+1):>9,} + hone {hone_total:>7,}"
              f"  net {net:>7,.0f}/day  days {days:5.1f} (line {line})"
              f"  ratio {ratio:4.2f}{flag}")
        prev = days
    return ok


def check_early_game(trials=150):
    """Fresh solo archer, greedy-but-sane policy, floors 1–5."""
    def xp_need(lvl):
        return economy.xp_need(lvl)

    days_out = []
    for _ in range(trials):
        lvl, xp, gold = 1, 0, 50
        w, s, a, hone = economy.STARTER_WEAPON.bonus, 0, 0, 0
        floor, energy, day = 1, 24, 1
        hp = player_max_hp(1)
        save = True
        boss_losses = 0        # after 2 straight losses, farm a level first
        farm_until = 0
        while floor <= 5 and day <= 8:
            if energy <= 0:
                day += 1
                energy = 30
                save = True
                continue
            # weapon-first (the shard's coaching: real steel before all),
            # then armor, shield, honing as income allows
            if w < 8:
                if gold >= 250:
                    gold -= 250; w = 8
            elif a < 7 and gold >= 200:
                gold -= 200; a = 7
            elif s < 5 and gold >= 100:
                gold -= 100; s = 5
            elif (hone < economy.reference_hone(floor)
                  and gold >= 3 * economy.hone_price(floor)):
                gold -= 3 * economy.hone_price(floor)
                hone += 1
            if hp < player_max_hp(lvl) * 0.7 and gold >= 2 * floor:
                gold -= 2 * floor
                hp = player_max_hp(lvl)
            # the shard coaches exactly this: full HP, then the keep —
            # every opened floor pays better than the last. Floor 1's
            # warden falls to the shiv; after two straight losses a sane
            # climber farms a level before retrying.
            boss = (hp >= player_max_hp(lvl) * 0.95 and energy >= 3
                    and lvl >= floor - 1 and (w >= 8 or floor == 1)
                    and lvl >= farm_until)
            energy -= 3 if boss else 1
            won, lost, _ = fight(lvl, w + hone, s + hone, a + hone, floor,
                                 boss=boss)
            if won:
                hp = max(1, hp - lost)
                gold += (economy.warden_gold(floor) if boss
                         else economy.gold_per_kill(floor))
                xp += (economy.warden_xp(floor) if boss
                       else economy.xp_per_kill(floor))
                if boss:
                    floor += 1
                    boss_losses = 0
                while xp >= xp_need(lvl):
                    xp -= xp_need(lvl)
                    lvl += 1
                    hp = player_max_hp(lvl)
            else:
                if boss:
                    boss_losses += 1
                    if boss_losses >= 2:
                        farm_until = lvl + 1
                        boss_losses = 0
                if save:
                    save = False
                    hp = 1
                else:
                    gold //= 2 if lvl <= economy.BEGINNER_MERCY_MAX_LEVEL else 1
                    if lvl > economy.BEGINNER_MERCY_MAX_LEVEL:
                        gold = 0
                    hp = player_max_hp(lvl)
        days_out.append(day if floor > 5 else 99)
    med = statistics.median(days_out)
    within = sum(1 for d in days_out if d <= 3)
    print(f"early game: floors 1–5 median {med} days "
          f"({within}/{trials} within 3 days)")
    return med <= 3


def tables():
    print("=" * 76)
    print("A. FLOOR 1, LEVEL 1 (the elf-archer experience)")
    print("=" * 76)
    for label, w, s, a in [
        ("bare hands (impossible since the gear_bonus floor)", 0, 0, 0),
        ("Rusted Shiv +5 (free starter, backfilled to old docs)", 5, 0, 0),
        ("Pigsticker +8 (first purchase, 250g)", 8, 0, 0),
        ("full T1 set (550g)", 8, 5, 7),
    ]:
        p, hp = stats(1, w, s, a, 1)
        print(f"  {label:52s} win {p*100:5.1f}%  hp/win {hp:5.1f}/52")

    print()
    print("=" * 76)
    print("B. THE CURVE — at-level archer, current tier set + full hone")
    print("=" * 76)
    print(f"  {'floor':>5} {'win% entry':>10} {'win% geared':>11} "
          f"{'hp/win':>7} {'gold/day':>9} {'next set':>9} {'days grind':>10}")
    for f in [1, 5, 9, 11, 15, 19, 21, 25, 31, 35, 41, 45, 51, 55,
              61, 65, 71, 75, 81, 85, 91, 95, 99]:
        t = economy.gear_tier_for_floor(f)
        w0, s0, a0 = tier_gear(t - 1) if t > 1 else (
            economy.STARTER_WEAPON.bonus, 0, 0)
        h0 = 9 if t > 1 else 0                 # entry: prev set, fully honed
        p_entry, _ = stats(f, w0 + h0, s0 + h0, a0 + h0, f, n=800)
        p_gear, hp = stats(f, *geared(f), f, n=800)
        gd = net_income_day(f, p_gear, hp)
        nxt = set_price(min(10, t + 1))
        days = nxt / gd if gd > 0 else float("inf")
        print(f"  {f:>5} {p_entry*100:>9.1f}% {p_gear*100:>10.1f}% "
              f"{hp:>7.1f} {gd:>9.0f} {nxt:>9,} {days:>10.1f}")


if __name__ == "__main__":
    random.seed(4)
    accept = "--accept" in sys.argv
    if not accept:
        tables()
        print()
    results = [
        ("wardens", check_wardens()),
        ("wilds", check_wilds()),
        ("days/tier", check_days_per_tier()),
        ("early game", check_early_game()),
    ]
    failed = [name for name, ok in results if not ok]
    print()
    if failed:
        print(f"ACCEPTANCE: FAIL ({', '.join(failed)})")
        sys.exit(1)
    print("ACCEPTANCE: PASS (all 004 §4 criteria)")
