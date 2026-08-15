"""027: the notice board — everything that WAITS for the player, in words.

0.29.2 put a `(n)` after a door's name and hoped the player would guess. They
didn't: the Lodge's `(1)` reads exactly like the Vault's, and one of them is
money while the other is a night still unplanned. So the count stops being
prose glued into a label (it is `Option.badge`, a blue chip now) and every
count gets a SENTENCE at the top of the card: the verb, the room, the number,
and what it is worth.

The law from 023 stands — a notice is a finished claim, never mere
availability. A badge that is always on is a badge nobody reads.

Entries: {door, opt, n, kind, text}
  door  the town door it belongs to ("vault") — the badge projection sums these
  opt   the option id that takes you there (the notice row is a shortcut)
  n     the count on the chip; 0 means "one thing, no number worth showing"
  kind  "collect" — gold/goods with your name on them
        "plan"    — a slot that expires if you ignore it (the Lodge)
"""

from __future__ import annotations

from .. import economy
from . import contracts, state, weekly


def _forge_notices(p: dict) -> list[dict]:
    """A free mend in the pack, and steel that is fighting at half."""
    out: list[dict] = []
    tokens = int((p.get("inventory") or {}).get("repair_token", 0))
    if tokens:
        out.append({
            "door": "forge", "opt": "forge", "n": tokens, "kind": "collect",
            "text": (f"The Forge — {tokens} repair token"
                     f"{'s' if tokens != 1 else ''} in your pack; a full "
                     "mend costs nothing"),
        })
    broken = []
    for slot in ("weapon", "shield", "armor", "shoes"):
        slug = (p.get("gear") or {}).get(slot)
        g = economy.FORGE.get(slug) if slug else None
        if not g:
            continue
        left = (p.get("durability") or {}).get(slot)
        if left is not None and left <= 0:
            broken.append(g.name)
    if broken:
        out.append({
            "door": "forge", "opt": "forge", "n": len(broken),
            "kind": "collect",
            "text": (f"The Forge — {', '.join(broken)} broken; you fight at "
                     "half strength until it is mended"),
        })
    return out


def _guildhall_notices(p: dict) -> list[dict]:
    """A level is bought, not earned: a full bar plus the fee in hand is a
    level sitting on the shelf."""
    if p["level"] >= economy.LEVEL_CAP:
        return []
    fee = economy.levelup_gold(p["level"])
    if p["xp"] < economy.xp_need(p["level"]) or p["gold"] < fee:
        return []
    return [{
        "door": "guildhall", "opt": "guildhall", "n": 1, "kind": "levelup",
        "text": (f"The Guildhall — your bar is full and the fee is in hand: "
                 f"LEVEL {p['level'] + 1} for ◈ {fee:,}"),
    }]


def _hall_notices(p: dict, w: dict) -> list[dict]:
    """032 §9: a steward with an unentered week gets a blue bar on the
    square. Members don't — nudging is a body line at the hall, not a
    town-wide claim. No hall key (older worldd) → no notice."""
    fac = w.get("faction")
    if not isinstance(fac, dict) or not isinstance(fac.get("hall"), dict):
        return []
    if fac.get("role") != "steward":
        return []
    if (fac.get("week") or {}).get("entered"):
        return []
    return [{
        "door": "hall", "opt": "hall", "n": 0, "kind": "plan",
        "text": "the week stands unentered at your hall",
    }]


def pending(p: dict, w: dict | None = None) -> list[dict]:
    """Everything waiting, in the order a player should care about it."""
    if p.get("stage") != "playing":
        return []
    w = w or p.get("_world") or {}
    out: list[dict] = []

    stubs = state.interest_sync(p)
    if stubs:
        total = sum(int(s.get("gold", 0)) for s in stubs)
        out.append({
            "door": "vault", "opt": "vault", "n": len(stubs),
            "kind": "collect",
            "text": (f"The Vault holds {len(stubs)} interest stub"
                     f"{'s' if len(stubs) != 1 else ''} — ◈ {total:,} to the "
                     "bank the moment you collect"),
        })
    if p["level"] >= economy.STRONGBOX_LEVEL \
            and weekly.sync(p).get("pending"):
        out.append({
            "door": "vault", "opt": "vault", "n": 1, "kind": "collect",
            "text": "The Vault — last week's strongbox is unopened; pick "
                    "one reward before this week rolls",
        })
    if p["level"] >= economy.BOARD_LEVEL:
        done = [j for j in contracts.board_for(p) if contracts.claimable(p, j)]
        if done:
            gold = sum(int(j.get("gold", 0)) for j in done)
            out.append({
                "door": "board", "opt": "board", "n": len(done),
                "kind": "collect",
                "text": (f"The contract board — {len(done)} job"
                         f"{'s' if len(done) != 1 else ''} finished and "
                         f"unpaid; ◈ {gold:,} plus XP at the desk"),
            })
    if w:
        letters = int(w.get("inbox_count") or 0)
        # 040: no level gate — held post (a grant's gold rides in a
        # letter) must reach a level-1 climber too; the letter itself
        # opens the Relay door (core._town_scene).
        if letters:
            out.append({
                "door": "relay", "opt": "relay", "n": letters,
                "kind": "collect",
                "text": (f"The Relay Office — {letters} letter"
                         f"{'s' if letters != 1 else ''} held for you, "
                         "some with gold enclosed"),
            })
    out.extend(_forge_notices(p))
    out.extend(_guildhall_notices(p))
    out.extend(_hall_notices(p, w))
    # The plan row sits last and speaks a different verb: nothing here is
    # collected, it is DECIDED, and dawn decides it for you if you don't.
    if p["level"] >= economy.NIGHT_SLOT_LEVEL \
            and (p.get("night") or {}).get("day") != state.world_day():
        out.append({
            "door": "lodge", "opt": "lodge", "n": 0, "kind": "plan",
            "text": "The Lodge — tonight is unplanned. One action a night: "
                    "rest it to bank aether, work it for coin. Dawn "
                    "settles it either way.",
        })
    return out


def doors(p: dict, w: dict | None = None) -> dict[str, int]:
    """The badge projection: how many things wait behind each door. Built
    from the same list the notice board reads, so a chip and a sentence can
    never disagree."""
    n: dict[str, int] = {}
    for item in pending(p, w):
        n[item["door"]] = n.get(item["door"], 0) + max(1, int(item["n"]))
    return n
