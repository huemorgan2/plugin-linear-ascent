"""022/005 — the weekly reward: a week of activity, one chosen prize.

Three counters the game already tracks — kills, warden engagements,
floors gained — sum to activity points. Thresholds (2/4/6) open 1/2/3
reward ranks; when the week ticks over the box goes PENDING and the
player picks exactly one reward from the waiting-for-you board. An
unpicked box falls back to gold when the next week closes — never to
nothing. Floors gained needs no hook at all: the box remembers the
frontier it opened at and diffs.

070: the chooser left the Vault. Player-facing copy is plain English
(weekly.HEADER / choices / pick receipts). Internal keys stay
`strongbox` / `pick_*` so existing docs keep loading.
"""

from __future__ import annotations

from .. import economy
from . import state


HEADER = ("You have a reward from last week. Choose one. "
          "You only get one.")

# title, sentence — locked in 070. Amounts ride `hint`, not these lines.
_CHOICE: dict[str, tuple[str, str]] = {
    "pick_gold": (
        "Gold",
        "About as much as half a day's hunting. It is added to the "
        "gold you are carrying.",
    ),
    "pick_aether": (
        "Extra XP",
        "Your next fights will give extra experience, until this "
        "bonus runs out.",
    ),
    "pick_token": (
        "Free repair",
        "The Forge will fully repair one piece of gear you are "
        "wearing, for free.",
    ),
    "pick_relic": (
        "Luck charm",
        "You will find better loot while you wear it. It goes into "
        "your pack. Put it in the charm slot on your profile to "
        "use it.",
    ),
}


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
        # pay gold now, never let a week rot to nothing.
        old = box.get("pending")
        if old:
            gold = economy.strongbox_gold(max(1, p.get("unlocked_floor", 1)))
            p["gold"] = p.get("gold", 0) + gold
            p.setdefault("_ledger", []).append(
                {"kind": "strongbox", "gold": gold, "xp": 0,
                 "note": "unpicked week — lowest slot"})
            p["strongbox_note"] = (
                f"You did not choose a reward in time, so the gold "
                f"(◈ {gold}) was added to what you are carrying.")
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


def choices(p: dict, n_slots: int) -> list[dict]:
    """Open rewards as notice rows: opt, n, title, text, hint."""
    fl = max(1, p.get("unlocked_floor", 1))
    ids = ["pick_gold"]
    if n_slots >= 2:
        ids.append("pick_aether")
    if n_slots >= 3:
        ids.extend(["pick_token", "pick_relic"])
    out = []
    for i, oid in enumerate(ids, 1):
        title, text = _CHOICE[oid]
        if oid == "pick_gold":
            hint = f"◈ {economy.strongbox_gold(fl)}"
        elif oid == "pick_aether":
            hint = f"✦ {economy.strongbox_aether(p['level'])}"
        else:
            hint = ""
        out.append({"opt": oid, "n": i, "title": title,
                    "text": text, "hint": hint})
    return out


def rewards(p: dict, n_slots: int) -> list[tuple[str, str, str]]:
    """(option id, title, hint) — kept for older callers."""
    return [(c["opt"], c["title"], c["hint"] or c["text"])
            for c in choices(p, n_slots)]


def pick(p: dict, oid: str) -> str:
    """Resolve a pending pick; returns the receipt ('' if refused)."""
    box = sync(p)
    pending = box.get("pending")
    if not pending:
        return ""
    n = int(pending["slots"])
    if not any(c["opt"] == oid for c in choices(p, n)):
        return ""
    box["pending"] = None
    fl = max(1, p.get("unlocked_floor", 1))
    if oid == "pick_gold":
        gold = economy.strongbox_gold(fl)
        p["gold"] += gold
        p.setdefault("_ledger", []).append(
            {"kind": "strongbox", "gold": gold, "xp": 0, "note": "gold lump"})
        line = (f"You chose the gold. ◈ {gold} has been added to the "
                "gold you are carrying.")
    elif oid == "pick_aether":
        amt = economy.strongbox_aether(p["level"])
        p["rested"] = p.get("rested", 0) + amt
        p.setdefault("_ledger", []).append(
            {"kind": "strongbox", "gold": 0, "xp": 0, "note": "aether lump"})
        line = (f"You chose extra experience. Your next fights will "
                f"give more XP until ✦ {amt} runs out.")
    else:
        inv = p.setdefault("inventory", {})
        if oid == "pick_token":
            inv["repair_token"] = inv.get("repair_token", 0) + 1
            line = ("You chose a free repair. Take it to the Forge to "
                    "mend one piece of gear you are wearing.")
        else:
            inv["luck_charm"] = inv.get("luck_charm", 0) + 1
            line = ("You chose a luck charm. It is in your pack. Put it "
                    "in the charm slot on your profile to use it.")
    p["strongbox_note"] = line
    return line
