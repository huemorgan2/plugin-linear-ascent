"""Kills-per-floor progression table (004 follow-up, live economy).

For each floor: the level giving >=50% solo warden win (current tier +
reference hone), the frontier kills needed to get there from the previous
floor's state (XP for levels + hone burn, gold for gear + honing —
each kill pays both, so kills = max of the two), and days at ~30
fights/day.

Run:  python3 plans/004-difficulty-review/progression_table.py
"""
from __future__ import annotations

import math
import random

from sim import economy, fight, geared, set_price

FIGHTS_PER_DAY = 30


def avg_rounds(level, floor, n=400):
    """Mean combat rounds to kill a wilds monster (won fights only)."""
    w, s, a = geared(floor)
    rounds = [r for won, _, r in
              (fight(level, w, s, a, floor) for _ in range(n)) if won]
    return sum(rounds) / max(1, len(rounds))


def warden_win(level, floor, n=400):
    w, s, a = geared(floor)
    return sum(fight(level, w, s, a, floor, boss=True)[0]
               for _ in range(n)) / n


def min_level(floor):
    lo, hi = max(1, floor - 2), 3 * floor + 80
    if warden_win(hi, floor) < 0.5:
        return None                       # not soloable at any sane level
    while lo < hi:
        mid = (lo + hi) // 2
        if warden_win(mid, floor) >= 0.5:
            hi = mid
        else:
            lo = mid + 1
    return lo


def main():
    random.seed(4)
    show = set(range(1, 101))
    level, xp, cum = 1, 0.0, 0.0
    print(f"{'floor':>5} {'need lvl':>8} {'kills XP':>8} {'kills gold':>10}"
          f" {'kills':>6} {'rounds':>6} {'days':>5} {'cum':>6}  note")
    for F in range(1, 101):
        need = min_level(F)
        if need is None:
            print(f"{F:>5} {'—':>8}  solo wall: no level wins 50%+ "
                  f"(group content by design)")
            break

        # XP side: level up to `need`, plus hone burn (3 slots × ✦ cost)
        k_xp = 0
        hone_burn = len(economy.HONE_SLOTS) * economy.hone_xp(F)
        pool = xp - hone_burn
        lvl = level
        while lvl < need:
            pool += economy.xp_per_kill(F)
            k_xp += 1
            while pool >= economy.xp_need(lvl):
                pool -= economy.xp_need(lvl)
                lvl += 1

        # gold side: honing every floor, the tier set at each band start
        cost = len(economy.HONE_SLOTS) * economy.hone_price(F)
        tier = economy.gear_tier_for_floor(F)
        if F == economy.band_start(tier) and tier > 1:
            cost += set_price(tier)
        net = economy.gold_per_kill(F) - 2 * F * 0.8   # healer's tent
        k_gold = math.ceil(cost / net) if net > 0 else 10**9

        kills = max(k_xp, k_gold)
        p = warden_win(need, F, n=600)
        attempts = 1 / max(p, 0.05)
        days = (kills + 3 * attempts) / FIGHTS_PER_DAY
        cum += days
        # carry state forward: do the kills, take the warden reward
        pool += max(0, kills - k_xp) * economy.xp_per_kill(F)
        pool += economy.warden_xp(F)
        while pool >= economy.xp_need(lvl):
            pool -= economy.xp_need(lvl)
            lvl += 1
        level, xp = lvl, pool

        if F in show:
            note = ""
            if economy.is_milestone(F):
                note = f"milestone (quorum {economy.MILESTONES[F].quorum} by design)"
            elif need > F + 2:
                note = f"over-level +{need - F}"
            rounds = avg_rounds(need, F)
            print(f"{F:>5} {need:>8} {k_xp:>8} {k_gold:>10}"
                  f" {kills:>6} {rounds:>6.1f} {days:>5.1f} {cum:>6.1f}  {note}")
    print(f"\n(30 fights/day ≈ full energy; warden attempt = 3⚡ × expected"
          f" attempts at the listed level)")


if __name__ == "__main__":
    main()
