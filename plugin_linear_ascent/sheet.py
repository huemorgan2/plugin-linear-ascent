"""Character sheet — computed view of a player doc (Luna-free)."""

from __future__ import annotations

from . import economy
from .engine import state as pstate


def character_sheet(p: dict) -> dict:
    def _piece(slot: str, slug: str | None) -> str:
        if not slug:
            return "—"
        hone = pstate.hone_level(p, slot)
        return economy.FORGE[slug].name + (f" (honed +{hone})" if hone else "")

    gear = {slot: _piece(slot, slug) for slot, slug in p["gear"].items()}
    race = p.get("race") or ""
    return {
        "name": p["name"], "race": p["race"], "class": p["clazz"],
        "level": p["level"], "xp": p["xp"],
        "xp_to_next": max(0, economy.xp_need(p["level"]) - p["xp"]),
        "levelup_fee_gold": economy.levelup_gold(p["level"]),
        "hp": f"{p['hp']}/{pstate.max_hp(p)}",
        "atk": pstate.atk(p), "def": pstate.dfs(p),
        "energy": f"{pstate.energy_now(p)}/{economy.energy_cap(p['level'], race)}",
        "carried_gold": p["gold"], "banked_gold": p["bank"],
        "floor_frontier": p["unlocked_floor"], "gear": gear,
        "inventory": p["inventory"],
    }
