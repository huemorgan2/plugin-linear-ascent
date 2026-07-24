"""Difficulty-curve simulator for the 004 review.

Mirrors engine/combat.py math exactly (hit rolls, defense halving,
treeline shot) and economy.py numbers. Monte Carlo over full fights,
then derives days-of-work per tier the way a player experiences it.

Run:  python plans/004-difficulty-review/sim.py
"""
from __future__ import annotations

import random
import statistics

# economy.py formulas (copied so the sim is standalone)
def player_atk(level, weapon): return 3 * level + weapon
def player_def(level, shield, armor): return 2 * level + shield + armor
def player_max_hp(level): return 40 + 12 * level
def monster_stats(floor): return 4 * floor + 2, 3 * floor, 12 * floor + 25
def warden_stats(floor): return 5 * floor, 4 * floor, 60 * floor
def xp_need(level): return round(60 * level ** 1.5)
def xp_per_kill(floor): return 12 * floor
def gold_per_kill(floor): return 8 * floor

# forge: tier -> (weapon+, shield+, armor+, set price)
FORGE = {
    0: (5, 0, 0, 0),                         # rusted shiv (free)
    1: (8, 5, 7, 550), 2: (16, 10, 14, 1760), 3: (24, 15, 21, 5500),
    4: (32, 20, 28, 16500), 5: (40, 25, 35, 49000), 6: (48, 30, 42, 132000),
    7: (56, 35, 49, 354000), 8: (64, 40, 56, 930000),
    9: (72, 45, 63, 2420000), 10: (80, 50, 70, 6100000),
}

FIGHTS_PER_DAY = 30       # ~32 energy/day regen, wilds fight = 1 energy
# healing: the gate-town healer's tent fully heals for 2 x floor gold,
# so worst case (heal after every fight) costs 2F per fight.


def fight(level, weapon, shield, armor, floor, archer=True, boss=False):
    """One full fight, exact combat.py rolls. -> (won, hp_lost, rounds)"""
    atk = player_atk(level, weapon)
    dfs = player_def(level, shield, armor)
    hp = hp_max = player_max_hp(level)
    e_atk, e_def, e_hp = (warden_stats if boss else monster_stats)(floor)
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


def stats(level, weapon, shield, armor, floor, n=4000, boss=False):
    wins, hp_costs = 0, []
    for _ in range(n):
        won, hp_lost, _ = fight(level, weapon, shield, armor, floor, boss=boss)
        if won:
            wins += 1
            hp_costs.append(hp_lost)
    p = wins / n
    hp_avg = statistics.mean(hp_costs) if hp_costs else float("nan")
    return p, hp_avg


def gold_day(p_win, hp_lost, floor):
    """Net gold/day: wins pay 8F avg, healer's tent (2F, full) after each
    fight that cost meaningful HP. Deaths ignored (death_save 1/day)."""
    heal_freq = min(1.0, hp_lost / max(1, player_max_hp(floor) * 0.5))
    per_fight = p_win * gold_per_kill(floor) - heal_freq * 2 * floor
    return per_fight * FIGHTS_PER_DAY


def days_with_bank(target, income_day, rate=0.05):
    """Days to afford `target` banking all income at 5%/day compound."""
    bal, d = 0.0, 0
    while bal < target and d < 10000:
        bal = bal * (1 + rate) + income_day
        d += 1
    return d


print("=" * 76)
print("A. FLOOR 1, LEVEL 1 (the elf-archer experience)")
print("=" * 76)
for label, w, s, a in [
    ("bare hands (pre-fix docs — what the user played)", 0, 0, 0),
    ("Rusted Shiv +5 (new characters after c4ab270)", 5, 0, 0),
    ("Pigsticker +8 (first purchase, 250g)", 8, 0, 0),
    ("full T1 set (550g)", 8, 5, 7),
]:
    p, hp = stats(1, w, s, a, 1)
    print(f"  {label:52s} win {p*100:5.1f}%  hp/win {hp:5.1f}/52")

print()
print("=" * 76)
print("B. THE CURVE — at-level player (L=F), archer, full gear set")
print("   entry = previous tier set (just reached band), geared = current tier")
print("=" * 76)
hdr = (f"  {'floor':>5} {'win% entry':>10} {'win% geared':>11} "
       f"{'hp/win':>7} {'gold/day':>9} {'next set':>9} "
       f"{'days grind':>10} {'days+bank':>9}")
print(hdr)
for F in [1, 5, 9, 11, 15, 19, 21, 25, 31, 35, 41, 45, 51, 55,
          61, 65, 71, 75, 81, 85, 91, 95, 99]:
    T = (F - 1) // 10 + 1
    w0, s0, a0, _ = FORGE[T - 1]
    w1, s1, a1, _ = FORGE[T]
    p_entry, _ = stats(F, w0, s0, a0, F)
    p_gear, hp = stats(F, w1, s1, a1, F)
    gd = gold_day(p_gear, hp, F)
    nxt = FORGE[min(10, T + 1)][3]
    days = nxt / gd if gd > 0 else float("inf")
    dbank = days_with_bank(nxt, gd)
    print(f"  {F:>5} {p_entry*100:>9.1f}% {p_gear*100:>10.1f}% "
          f"{hp:>7.1f} {gd:>9.0f} {nxt:>9,} {days:>10.1f} {dbank:>9}")

print()
print("=" * 76)
print("C. REGULAR WARDENS solo, at-level, current-tier set (design: soloable)")
print("=" * 76)
for F in [1, 5, 9, 15, 25, 35, 45, 55, 65, 75, 85, 95]:
    T = (F - 1) // 10 + 1
    w1, s1, a1, _ = FORGE[T]
    p, hp = stats(F, w1, s1, a1, F, n=2000, boss=True)
    print(f"  floor {F:>3}: win {p*100:5.1f}%   hp cost {hp:6.1f}"
          f" / {player_max_hp(F)}")

print()
print("=" * 76)
print("D. XP pace — fights per level at-level (should grow gently)")
print("=" * 76)
for L in [1, 5, 10, 20, 40, 60, 80, 99]:
    f = xp_need(L) / xp_per_kill(L)
    print(f"  level {L:>3}: {f:5.1f} fights to level up")
