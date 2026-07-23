"""Player document + time/meter math.

The player is ONE JSON document (JSONB row locally, worldd row later).
All regen/interest math derives from server timestamps — never from
model-supplied time. World-day is a pure function of UTC time.
"""

from __future__ import annotations

import datetime as dt

from .. import economy

WORLD_DAY_UTC_HOUR = 6
_EPOCH = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)


def now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def world_day(at: dt.datetime | None = None) -> int:
    """Day number since epoch, rolling at WORLD_DAY_UTC_HOUR."""
    at = at or now()
    shifted = at - dt.timedelta(hours=WORLD_DAY_UTC_HOUR)
    return (shifted - _EPOCH.replace(hour=0)).days


def new_player(luna_user: str) -> dict:
    ts = now().isoformat()
    return {
        "version": 1,
        "luna_user": luna_user,
        "stage": "creation_race",      # creation_race → creation_class → creation_name → playing
        "name": None, "race": None, "clazz": None,
        "level": 1, "xp": 0, "hp": economy.player_max_hp(1),
        "gold": 50, "bank": 0, "bank_day": world_day(),
        "floor": 0, "location": "town",
        "gear": {"weapon": None, "shield": None, "armor": None},
        "inventory": {},
        "energy_ts": ts, "energy_val": float(economy.ENERGY_BASE_CAP),
        "mana_ts": ts, "mana_val": float(economy.MANA_BASE_CAP),
        "lodged_until_day": -1,
        "last_seen": ts,
        "rng_counter": 0,
        "scene": None,
        "encounter": None,
        "unlocked_floor": 1,
        "flags": {},
        "daily": {"day": world_day(), "pvp_used": 0, "energy_cell": False,
                  "aether_philtre": False, "death_save": False},
        "sidekick": {"insight": 1, "carried": None, "scout_charges": 0},
        "telemetry_day": world_day(),
    }


# ── Meters (lazy regen) ──────────────────────────────────────────────────

def _regen(val: float, ts_iso: str, cap: int, minutes_per_point: int,
           at: dt.datetime) -> float:
    ts = dt.datetime.fromisoformat(ts_iso)
    elapsed_min = max(0.0, (at - ts).total_seconds() / 60.0)
    return min(float(cap), val + elapsed_min / minutes_per_point)


def energy_now(p: dict, at: dt.datetime | None = None) -> int:
    at = at or now()
    cap = economy.energy_cap(p["level"], p.get("race") or "")
    return int(_regen(p["energy_val"], p["energy_ts"], cap,
                      economy.ENERGY_REGEN_MIN, at))


def mana_now(p: dict, at: dt.datetime | None = None) -> int:
    at = at or now()
    cap = economy.mana_cap(p["level"], p.get("race") or "")
    return int(_regen(p["mana_val"], p["mana_ts"], cap,
                      economy.MANA_REGEN_MIN, at))


def spend_energy(p: dict, amount: int, at: dt.datetime | None = None) -> bool:
    at = at or now()
    cap = economy.energy_cap(p["level"], p.get("race") or "")
    cur = _regen(p["energy_val"], p["energy_ts"], cap,
                 economy.ENERGY_REGEN_MIN, at)
    if cur < amount:
        return False
    p["energy_val"] = cur - amount
    p["energy_ts"] = at.isoformat()
    return True


def gain_energy(p: dict, amount: int, at: dt.datetime | None = None) -> None:
    at = at or now()
    cap = economy.energy_cap(p["level"], p.get("race") or "")
    cur = _regen(p["energy_val"], p["energy_ts"], cap,
                 economy.ENERGY_REGEN_MIN, at)
    p["energy_val"] = min(float(cap), cur + amount)
    p["energy_ts"] = at.isoformat()


def spend_mana(p: dict, amount: int, at: dt.datetime | None = None) -> bool:
    at = at or now()
    cap = economy.mana_cap(p["level"], p.get("race") or "")
    cur = _regen(p["mana_val"], p["mana_ts"], cap,
                 economy.MANA_REGEN_MIN, at)
    if cur < amount:
        return False
    p["mana_val"] = cur - amount
    p["mana_ts"] = at.isoformat()
    return True


def gain_mana(p: dict, amount: int, at: dt.datetime | None = None) -> None:
    at = at or now()
    cap = economy.mana_cap(p["level"], p.get("race") or "")
    cur = _regen(p["mana_val"], p["mana_ts"], cap,
                 economy.MANA_REGEN_MIN, at)
    p["mana_val"] = min(float(cap), cur + amount)
    p["mana_ts"] = at.isoformat()


# ── Derived stats ────────────────────────────────────────────────────────

def gear_bonus(p: dict, slot: str) -> int:
    slug = p["gear"].get(slot)
    if not slug:
        return 0
    item = economy.FORGE.get(slug)
    return item.bonus if item else 0


def atk(p: dict) -> int:
    return economy.player_atk(p["level"], gear_bonus(p, "weapon"))


def dfs(p: dict) -> int:
    return economy.player_def(p["level"], gear_bonus(p, "shield"),
                              gear_bonus(p, "armor"), p.get("race") or "")


def max_hp(p: dict) -> int:
    return economy.player_max_hp(p["level"])


def next_roll(p: dict) -> int:
    """Advance and return the RNG counter."""
    p["rng_counter"] += 1
    return p["rng_counter"]


# ── Player-scoped deterministic rolls ────────────────────────────────────

def _key(p: dict) -> str:
    return p.get("luna_user", "?")


def rng_int(p: dict, lo: int, hi: int) -> int:
    from . import rng
    return rng.roll_int(_key(p), world_day(), next_roll(p), lo, hi)


def rng_jitter(p: dict, base: int, pct: float) -> int:
    from . import rng
    return rng.roll_pct_jitter(_key(p), world_day(), next_roll(p), base, pct)


def rng_pick(p: dict, table: list[tuple[int, str]]) -> str:
    from . import rng
    return rng.weighted_pick(_key(p), world_day(), next_roll(p), table)


def roll_ok(p: dict, prob: float) -> bool:
    from . import rng
    return rng.roll(_key(p), world_day(), next_roll(p)) < prob


def touch_daily(p: dict) -> None:
    """Reset per-day counters when the world day advanced."""
    day = world_day()
    if p["daily"].get("day") != day:
        p["daily"] = {"day": day, "pvp_used": 0, "energy_cell": False,
                      "aether_philtre": False, "death_save": False}


def bank_interest_due(p: dict) -> int:
    """Compound 5%/day since last credit; call when visiting the Vault."""
    days = world_day() - p["bank_day"]
    if days <= 0 or p["bank"] <= 0:
        return 0
    new_total = round(p["bank"] * (1 + economy.BANK_INTEREST_RATE) ** days)
    return new_total - p["bank"]
