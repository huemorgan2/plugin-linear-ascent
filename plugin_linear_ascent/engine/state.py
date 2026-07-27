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
        "version": 2,
        "luna_user": luna_user,
        "stage": "intro",              # intro → creation_race → creation_class → creation_name → playing
        "name": None, "race": None, "clazz": None,
        "level": 1, "xp": 0, "hp": economy.player_max_hp(1),
        "gold": 50, "bank": 0, "bank_day": world_day(),
        "floor": 0, "location": "town",
        "gear": {"weapon": economy.STARTER_WEAPON.slug,
                 "shield": None, "armor": None},
        "hone": {s: 0 for s in economy.HONE_SLOTS},
        "inventory": {},
        "energy_ts": ts, "energy_val": float(economy.ENERGY_BASE_CAP),
        "lodged_until_day": -1,
        "last_seen": ts,
        "news_day": world_day(),       # fresh climbers skip today's crier
        "rng_counter": 0,
        "scene": None,
        "encounter": None,
        "unlocked_floor": 1,
        "flags": {},
        "daily": {"day": world_day(), "pvp_used": 0, "energy_cell": False,
                  "death_save": False},
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


def spend_xp(p: dict, amount: int) -> bool:
    """Burn aether — XP from the current level's pool (006). Never goes
    below 0 and never touches level; the caller shows the refusal."""
    if p["xp"] < amount:
        return False
    p["xp"] -= amount
    return True


# ── Doc upgrades (lazy migration on load — 004 §A.1) ─────────────────────

def ensure_current(p: dict) -> None:
    """Upgrade an older player document in place. Runs at every engine
    entry point, so docs created before a fix are healed on any backend
    (local plugin DB and worldd alike) the next time they're touched."""
    p.setdefault("hone", {s: 0 for s in economy.HONE_SLOTS})
    p.setdefault("news_day", -1)       # 007: existing docs get the crier
    if p["gear"].get("weapon") is None:
        # pre-c4ab270 doc: never received the free starter weapon.
        p["gear"]["weapon"] = economy.STARTER_WEAPON.slug
        if p.get("stage") == "playing":
            from .scene import Option, Scene
            p["gold"] += economy.VAULT_APOLOGY_GOLD
            p.setdefault("pending_events", []).insert(0, Scene(
                eyebrow="ROOTHOLLOW · A LETTER FROM THE VAULT",
                headline="The Vault owes you an apology",
                support="Sealed in gray wax: the gate armory shorted your "
                        "kit on arrival.",
                shard_note="Take it. Institutions apologize so rarely.",
                body_lines=[
                    "▪ a Rusted Shiv, gate-issue — yours all along",
                    f"+ ◈ {economy.VAULT_APOLOGY_GOLD} for the trouble",
                ],
                options=[Option("town", "Pocket it and move on")],
                event_kind="present",
            ).to_dict())
    if p.get("version", 1) < 2:
        # 017 §1: doc v2 — every class carries its OWN basic weapon.
        # Existing docs holding the generic shiv get their class piece;
        # archers/sorcerers see a letter (their weapon visibly changed),
        # the warrior's shiv just grew into its proper name.
        clazz = p.get("clazz")
        if (p.get("stage") == "playing" and clazz in economy.CLASS_STARTERS
                and p["gear"].get("weapon") == economy.STARTER_WEAPON.slug):
            starter = economy.class_starter(clazz)
            p["gear"]["weapon"] = starter.slug
            if clazz in ("archer", "sorcerer"):
                from .scene import Option, Scene
                p.setdefault("pending_events", []).insert(0, Scene(
                    eyebrow="ROOTHOLLOW · A LETTER FROM THE GATE ARMORY",
                    headline="Your own weapon, at last",
                    support="The armory finally sorted its ledgers: "
                            "climbers fight with the weapon of their "
                            "calling, not a spare shiv.",
                    shard_note="It fits your hands. It always should have.",
                    body_lines=[
                        f"▪ {starter.name} — {starter.flavor}",
                        "▪ the basic weapon never breaks, never runs "
                        "out, and is never lost",
                    ],
                    options=[Option("town", "Take it up")],
                    event_kind="present",
                ).to_dict())
        p["version"] = 2


# ── Derived stats ────────────────────────────────────────────────────────

def hone_level(p: dict, slot: str) -> int:
    return int((p.get("hone") or {}).get(slot, 0))


def gear_bonus(p: dict, slot: str) -> int:
    slug = p["gear"].get(slot)
    if not slug:
        # a doc can never be bare-handed again: an empty weapon slot
        # fights with the gate-issue shiv (004 §A.1 defensive floor).
        return economy.STARTER_WEAPON.bonus if slot == "weapon" else 0
    item = economy.FORGE.get(slug)
    base = item.bonus if item else 0
    return base + hone_level(p, slot)


def atk(p: dict) -> int:
    return economy.player_atk(p["level"], gear_bonus(p, "weapon"))


def dfs(p: dict) -> int:
    return economy.player_def(p["level"], gear_bonus(p, "shield"),
                              gear_bonus(p, "armor"), p.get("race") or "")


def faction_buff_pct(p: dict, kind: str) -> int:
    """010: the faction's weekly blessing — {'kind','pct','week'} written
    by worldd's weekly resolution; live only during its week."""
    b = p.get("faction_buff")
    if (isinstance(b, dict) and b.get("kind") == kind
            and b.get("week") == world_day() // 7):
        return max(0, int(b.get("pct", 0)))
    return 0


def max_hp(p: dict) -> int:
    base = economy.player_max_hp(p["level"])
    pct = faction_buff_pct(p, "hp")
    return round(base * (1 + pct / 100)) if pct else base


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
        # 008: a night at the Lodge mends the sleeper. lodged_until_day
        # covering today means last night was spent behind the palisade.
        if (p.get("lodged_until_day", -1) >= day
                and p.get("stage") == "playing"):
            p["hp"] = min(max_hp(p), p["hp"] + economy.LODGE_NIGHT_HEAL_HP)
        p["daily"] = {"day": day, "pvp_used": 0, "energy_cell": False,
                      "death_save": False}


def bank_interest_due(p: dict) -> int:
    """Compound 5%/day since last credit; call when visiting the Vault."""
    days = world_day() - p["bank_day"]
    if days <= 0 or p["bank"] <= 0:
        return 0
    new_total = round(p["bank"] * (1 + economy.BANK_INTEREST_RATE) ** days)
    return new_total - p["bank"]
