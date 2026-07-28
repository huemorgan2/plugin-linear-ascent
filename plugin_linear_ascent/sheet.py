"""Character sheet — computed view of a player doc (Luna-free)."""

from __future__ import annotations

from . import economy, unlocks
from .engine import state as pstate


def character_sheet(p: dict) -> dict:
    def _piece(slot: str, slug: str | None) -> str:
        if not slug:
            return "—"
        g = economy.FORGE[slug]
        hone = pstate.hone_level(p, slot)
        name = g.name + (f" (honed +{hone})" if hone else "")
        # 005: the sheet names the wear the pack strip draws.
        left = (p.get("durability") or {}).get(slot)
        if left is not None and g.price > 0:
            pool = economy.item_pool(g)
            if left <= 0:
                name += " (BROKEN — half strength)"
            elif pool and left < pool:
                name += f" (worn to {round(100 * left / pool)}%)"
        return name

    gear = {slot: _piece(slot, slug) for slot, slug in p["gear"].items()}
    at_cap = p["level"] >= economy.LEVEL_CAP
    return {
        "name": p["name"], "race": p["race"], "class": p["clazz"],
        "level": p["level"], "xp": p["xp"],
        "xp_to_next": (0 if at_cap
                       else max(0, economy.xp_need(p["level"]) - p["xp"])),
        "levelup_fee_gold": (0 if at_cap
                             else economy.levelup_gold(p["level"])),
        "hp": f"{p['hp']}/{pstate.max_hp(p)}",
        "atk": pstate.atk(p), "def": pstate.dfs(p),
        "energy": f"{pstate.energy_now(p)}/{pstate.energy_cap_of(p)}",
        "carried_gold": p["gold"], "banked_gold": p["bank"],
        "floor_frontier": p["unlocked_floor"], "gear": gear,
        "inventory": p["inventory"],
        # 020: the ladder as data — Luna answers "what's next for me"
        # and "what do I lose at level N" from this, never by guessing.
        "next_unlocks": [
            {"at": f"{u.gate} {u.at}", "effect": u.effect,
             "title": u.title, "why": u.why, "cost": u.cost,
             "where": u.where}
            for u in unlocks.ahead(p, limit=6)],
        "protections_active": unlocks.protections_active(p),
    }
