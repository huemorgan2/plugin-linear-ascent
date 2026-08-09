"""043: calibrate _KAPPA_TABLE — the bar's lethality share.

For each probe bar B, finds the κ that puts the at-bar reference
warrior's win chance vs a plain `fierce` creature at ~90%, while the
bar-(B−1) player falls below the 85% acceptance line (so /mechanics
reports KILL BAR = B, not B−1). Prints the table to paste into
economy._KAPPA_TABLE plus the neighbours' win rates as evidence.

    python tools/calibrate_bars.py

The fight model mirrors worldd/tools/gen_mechanics.py (itself a mirror
of engine/combat.py): player strikes first, uniform [stat/2, stat]
rolls, chip floor ceil(raw/4), the crossing round, dodge from speed.
"""

from __future__ import annotations

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plugin_linear_ascent import economy as eco  # noqa: E402

RNG = random.Random(0xBA12)
PROBES = [1, 5, 10, 20, 40, 70, 101]
TRAITS = ("fierce",)           # the plain at-floor animal: offset 0
SIMS = 3000
MAX_ROUNDS = 400
WIN_TARGET = 0.90
WIN_ACCEPT = 0.85


def _player(bar: int) -> tuple[int, int, int]:
    atk, dfs = eco._at_level_loadout(bar)
    return atk, dfs, eco.reference_player_hp(bar)


def _creature(bar: int, kappa: float) -> tuple[int, int, int]:
    """creature_stats for a plain fierce animal, κ as a free knob."""
    dfs = 3 * bar
    p_atk, p_def = eco._at_level_loadout(bar)
    p_dmg = max(1, round(0.75 * p_atk) - dfs // 2)
    rounds = min(eco.WILDS_ROUNDS_HARD_MAX, eco.wilds_rounds(bar))
    hp = max(1, round(p_dmg * rounds))
    pool = eco.reference_player_hp(bar)
    per_round = min(kappa * pool / rounds, eco.wilds_round_cap(bar) * pool)
    raw = min(eco.CHIP_DIVISOR * per_round, per_round + p_def // 2)
    return max(1, round(raw / 0.75)), dfs, hp


def _blow(m_atk: int, p_def: int, halved: bool) -> int:
    raw = RNG.randint(m_atk // 2, m_atk)
    dmg = max(max(1, -(-raw // eco.CHIP_DIVISOR)), raw - p_def // 2)
    return dmg // 2 if halved else dmg


def _fight(player_bar: int, monster: tuple[int, int, int], prof) -> bool:
    p_atk, p_def, p_hp = _player(player_bar)
    m_atk, m_def, m_hp = monster
    dodge = eco.dodge_pct(eco.PLAYER_BASE_SPEED, prof["speed"])
    # the crossing: no damage dealt, one halved blow taken
    if not (dodge and RNG.random() < dodge / 100):
        p_hp -= _blow(m_atk, p_def, halved=True)
    if p_hp <= 0:
        return False
    for _ in range(MAX_ROUNDS):
        raw = RNG.randint(p_atk // 2, p_atk)
        m_hp -= eco.typed_damage("melee", raw, m_def, prof)
        if m_hp <= 0:
            return True                          # no counter on the kill
        if not (dodge and RNG.random() < dodge / 100):
            p_hp -= _blow(m_atk, p_def, halved=False)
        if p_hp <= 0:
            return False
    return False


def win_rate(player_bar: int, bar: int, kappa: float,
             sims: int = SIMS) -> float:
    prof = eco.profile_from_traits(TRAITS)
    m = _creature(bar, kappa)
    return sum(_fight(player_bar, m, prof) for _ in range(sims)) / sims


def solve(bar: int) -> tuple[float, float, float, float]:
    """κ with at-bar ≈ WIN_TARGET; nudged up until bar−1 < WIN_ACCEPT."""
    lo, hi = 0.10, 1.60
    for _ in range(14):                          # win falls as κ rises
        mid = (lo + hi) / 2
        if win_rate(bar, bar, mid) > WIN_TARGET:
            lo = mid
        else:
            hi = mid
    kappa = round((lo + hi) / 2, 3)
    under = win_rate(max(1, bar - 1), bar, kappa, 4000)
    while bar > 1 and under >= WIN_ACCEPT:
        kappa = round(kappa + 0.02, 3)
        if win_rate(bar, bar, kappa, 4000) < WIN_ACCEPT:
            kappa = round(kappa - 0.02, 3)       # tolerance exhausted
            break
        under = win_rate(max(1, bar - 1), bar, kappa, 4000)
    at = win_rate(bar, bar, kappa, 4000)
    over = win_rate(bar + 1, bar, kappa, 4000) if bar < eco.BAR_MAX else 1.0
    return kappa, at, under, over


def main() -> None:
    print(f"{'bar':>4} {'kappa':>6} {'at-bar':>7} {'bar-1':>7} {'bar+1':>7}")
    table = {}
    for bar in PROBES:
        kappa, at, under, over = solve(bar)
        table[bar] = kappa
        print(f"{bar:>4} {kappa:>6.3f} {at:>6.1%} {under:>6.1%} "
              f"{over:>6.1%}")
    body = ", ".join(f"{b}: {k:.3f}" for b, k in table.items())
    print(f"\n_KAPPA_TABLE: dict[int, float] = {{{body}}}")


if __name__ == "__main__":
    main()
