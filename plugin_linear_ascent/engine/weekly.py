"""022/005 — the weekly strongbox: a week of activity, one chosen reward.

Three counters the game already tracks — kills, warden engagements,
floors gained — sum to activity points. Thresholds (2/4/6) open 1/2/3
reward slots; when the week ticks over the box goes PENDING and the
player picks exactly one reward at the Vault. An unpicked box falls
back to the lowest slot (gold) when the next week closes — never to
nothing. Floors gained needs no hook at all: the box remembers the
frontier it opened at and diffs.
"""

from __future__ import annotations

from .. import economy
from . import state


def week_no() -> int:
    return state.world_day() // 7


def sync(p: dict) -> dict:
    """The doc's strongbox slate; rolls the week over lazily."""
    wk = week_no()
    box = p.get("strongbox")
    if isinstance(box, dict) and box.get("week") == wk:
        return box
    pending = None
    if isinstance(box, dict):
        # an older pending box was never picked — the fallback law:
        # pay the lowest slot now, never let a week rot to nothing.
        old = box.get("pending")
        if old:
            gold = economy.strongbox_gold(max(1, p.get("unlocked_floor", 1)))
            p["gold"] = p.get("gold", 0) + gold
            p.setdefault("_ledger", []).append(
                {"kind": "strongbox", "gold": gold, "xp": 0,
                 "note": "unpicked week — lowest slot"})
            p["strongbox_note"] = (f"an unclaimed strongbox paid out "
                                   f"◈ {gold} — the lowest slot. Pick, "
                                   "next time.")
        slots = _slots(p, box)
        if slots:
            pending = {"week": box["week"], "slots": slots}
    p["strongbox"] = {"week": wk, "kills": 0, "wardens": 0,
                      "floor0": max(1, p.get("unlocked_floor", 1)),
                      "pending": pending}
    return p["strongbox"]


def note(p: dict, key: str) -> None:
    """Bump a weekly counter ('kills' or 'wardens')."""
    box = sync(p)
    box[key] = int(box.get(key, 0)) + 1


def points(p: dict, box: dict | None = None) -> int:
    box = box or sync(p)
    floors = max(0, p.get("unlocked_floor", 1) - box.get("floor0", 1))
    return int(box.get("kills", 0)) + int(box.get("wardens", 0)) + floors


def _slots(p: dict, box: dict) -> int:
    pts = points(p, box)
    return sum(1 for t in economy.STRONGBOX_THRESHOLDS if pts >= t)


def slots(p: dict) -> int:
    return _slots(p, sync(p))


# ── rewards ──────────────────────────────────────────────────────────────
# slot 1: gold lump · slot 2: + aether lump · slot 3: + gear token or
# relic (the real gear-tier token is still a design TODO — the repair
# token stands in, same substitution as the contract board's).

def rewards(p: dict, n_slots: int) -> list[tuple[str, str, str]]:
    """(option id, label, hint) for every open reward."""
    fl = max(1, p.get("unlocked_floor", 1))
    out = [("pick_gold", "The gold lump",
            f"◈ {economy.strongbox_gold(fl)}")]
    if n_slots >= 2:
        out.append(("pick_aether", "The aether lump",
                    f"✦ {economy.strongbox_aether(p['level'])} rested"))
    if n_slots >= 3:
        out.append(("pick_token", "The smith's token", "+1 repair token"))
        out.append(("pick_relic", "The relic", "+1 luck charm"))
    return out


def pick(p: dict, oid: str) -> str:
    """Resolve a pending pick; returns the paid line ('' if refused)."""
    box = sync(p)
    pending = box.get("pending")
    if not pending:
        return ""
    n = int(pending["slots"])
    if not any(o == oid for o, _, _ in rewards(p, n)):
        return ""
    box["pending"] = None
    fl = max(1, p.get("unlocked_floor", 1))
    if oid == "pick_gold":
        gold = economy.strongbox_gold(fl)
        p["gold"] += gold
        p.setdefault("_ledger", []).append(
            {"kind": "strongbox", "gold": gold, "xp": 0, "note": "gold lump"})
        return f"+ ◈ {gold} — the week's gold lump"
    if oid == "pick_aether":
        # rested aether, NOT the bar — spent as bonus XP on kills only,
        # same pool the night slot feeds (never a direct payout).
        amt = economy.strongbox_aether(p["level"])
        p["rested"] = p.get("rested", 0) + amt
        p.setdefault("_ledger", []).append(
            {"kind": "strongbox", "gold": 0, "xp": 0, "note": "aether lump"})
        return f"+ ✦ {amt} rested — it rides your next kills"
    inv = p.setdefault("inventory", {})
    if oid == "pick_token":
        inv["repair_token"] = inv.get("repair_token", 0) + 1
        return "+ 1 repair token — the smith nods"
    inv["luck_charm"] = inv.get("luck_charm", 0) + 1
    return "+ 1 luck charm — the week owed you one"
