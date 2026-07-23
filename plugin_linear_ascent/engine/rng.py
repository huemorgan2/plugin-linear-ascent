"""Deterministic RNG — seeded per (player, world_day, counter).

Tests replay exactly; the counter lives in the player document so every
roll advances the stream. Never use wall-clock or `random` module state.
"""

from __future__ import annotations

import hashlib


def roll(player_key: str, world_day: int, counter: int) -> float:
    """Uniform [0, 1) from a stable hash."""
    h = hashlib.sha256(
        f"{player_key}:{world_day}:{counter}".encode()).digest()
    return int.from_bytes(h[:8], "big") / 2 ** 64


def roll_int(player_key: str, world_day: int, counter: int,
             lo: int, hi: int) -> int:
    """Inclusive integer roll."""
    return lo + int(roll(player_key, world_day, counter) * (hi - lo + 1))


def roll_pct_jitter(player_key: str, world_day: int, counter: int,
                    base: int, pct: float) -> int:
    """base ±pct jitter (e.g. XP ±25%, gold ±50%)."""
    r = roll(player_key, world_day, counter)          # 0..1
    factor = 1.0 + pct * (2.0 * r - 1.0)              # 1±pct
    return max(1, round(base * factor))


def weighted_pick(player_key: str, world_day: int, counter: int,
                  table: list[tuple[int, str]]) -> str:
    total = sum(w for w, _ in table)
    x = roll(player_key, world_day, counter) * total
    acc = 0.0
    for w, kind in table:
        acc += w
        if x < acc:
            return kind
    return table[-1][1]
