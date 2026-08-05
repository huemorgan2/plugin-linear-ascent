"""022/004 — the contract board: three world jobs a day.

One board for the whole tower. Jobs are seeded from the world DAY (the
pawn broker's pattern, `economy.pawn_rate`) plus the live frontier, so
every climber reads the same three lines and can talk about them over
the fire. There is no accept step and no new bookkeeping: progress is
counted off the kills the engine already scores — do the work, collect
before dawn. Jobs expire at the world-day tick and never reroll.

Determinism note: the cull's floor is a function of the frontier, so if
a Warden falls MID-day the board shifts with the world. That is a
feature at the fire ("the board turned over when Threshold-9 fell") and
a small unfairness to half-finished culls — logged in the continue doc.
"""

from __future__ import annotations

import random

from .. import economy
from ..content import schema
from . import state


def board(day: int, frontier: int) -> list[dict]:
    """The day's three jobs — pure function of (day, frontier)."""
    rng = random.Random(f"ascent-board-{day}")
    fr = max(1, int(frontier))
    jobs: list[dict] = []

    # A — the cull: N of a named creature on a named floor near the front
    fa = max(1, fr - rng.randrange(0, min(3, fr)))
    fl = schema.get_floor(fa)
    enc = rng.choice(fl.encounters)
    n = rng.randrange(3, 6)
    jobs.append({
        "id": f"d{day}-cull-{enc.id}",
        "kind": "cull", "floor": fa, "enc": enc.id, "need": n,
        "title": f"Cull {n} {enc.name}s on floor {fa}",
        "gold": max(1, round(economy.gold_per_kill(fa) * n
                             * economy.CONTRACT_CULL_GOLD_MULT)),
        "xp": max(1, round(economy.xp_per_kill(fa) * n
                           * economy.CONTRACT_CULL_XP_MULT)),
    })

    # B — steelwork: N kills with a weapon class, any floor. Priced off
    # the tower's waist so it pays the mid-climb without minting gold
    # for frontier hands doing what they'd do anyway. The job carries
    # its pricing floor: pay_for caps it at each hand's reach (0.29.1).
    dtype = rng.choice(("melee", "ranged", "magic"))
    n2 = rng.randrange(5, 9)
    fb = max(1, round(fr * 0.6))
    word = {"melee": "steel", "ranged": "arrows", "magic": "spellwork"}
    jobs.append({
        "id": f"d{day}-class-{dtype}",
        "kind": "class", "dtype": dtype, "need": n2, "floor": fb,
        "title": f"{n2} kills by {word[dtype]}, any floor",
        "gold": max(1, round(economy.gold_per_kill(fb) * n2
                             * economy.CONTRACT_CLASS_GOLD_MULT)),
        "xp": max(1, round(economy.xp_per_kill(fb) * n2
                           * economy.CONTRACT_CLASS_XP_MULT)),
    })

    # C — answer the horn: one Warden engagement. 034 §3 retired the echo
    # bout, so "any keep" now means the ONE keep that still has a Warden
    # in it — the live front. board_for drops this job for hands that
    # cannot enter that floor, rather than posting work they cannot do.
    jobs.append({
        "id": f"d{day}-warden",
        "kind": "warden", "need": 1, "floor": fr,
        "title": f"Answer the horn at floor {fr} — fight the Warden",
        "gold": max(1, round(economy.warden_gold(fr)
                             * economy.CONTRACT_WARDEN_MULT)),
        "xp": max(1, round(economy.warden_xp(fr)
                           * economy.CONTRACT_WARDEN_MULT)),
    })

    # occasional gear-tier token: one job some days carries a repair
    # token on top (seeded — the same job for everyone).
    if rng.random() < economy.CONTRACT_TOKEN_CHANCE:
        rng.choice(jobs)["token"] = "repair_token"
    return jobs


def board_for(p: dict) -> list[dict]:
    """The board as THIS doc sees it: world frontier when a world is
    attached, the player's own frontier in local dev (a world of one).

    034 §3: the horn job needs a living Warden, and after the echo bout
    was retired there is exactly one — at the frontier. A hand that
    cannot walk through that floor's gate cannot answer it, so the job
    comes off their board instead of sitting there uncompletable.
    """
    w = p.get("_world") or {}
    frontier = int(w.get("frontier") or 0) or max(1, p.get("unlocked_floor", 1))
    jobs = board(state.world_day(), frontier)
    if not can_answer_the_horn(p, frontier):
        jobs = [j for j in jobs if j["kind"] != "warden"]
    return jobs


def can_answer_the_horn(p: dict, frontier: int) -> bool:
    """Can this hand reach the one keep that still holds a Warden?"""
    return (int(p.get("unlocked_floor", 1)) >= frontier
            and int(p.get("level", 1))
            >= economy.floor_entry_player_level(frontier))


# ── progress — counted off kills the engine already scores ──────────────

def sync(p: dict) -> dict:
    """The doc's progress slate; wiped at the world-day tick (expiry)."""
    day = state.world_day()
    c = p.get("contracts")
    if not isinstance(c, dict) or c.get("day") != day:
        c = {"day": day, "got": {}, "claimed": []}
        p["contracts"] = c
    return c


def _bump(p: dict, job: dict) -> None:
    c = sync(p)
    if job["id"] in c["claimed"]:
        return
    got = int(c["got"].get(job["id"], 0))
    if got < job["need"]:
        c["got"][job["id"]] = got + 1


def note_kill(p: dict, enc: dict, dtype: str) -> None:
    """Score one wilds kill against the day's board (called from the
    victory path — assists must NOT route here twice, 022/008)."""
    for job in board_for(p):
        if job["kind"] == "cull" and enc.get("id") == job["enc"] \
                and enc.get("floor") == job["floor"]:
            _bump(p, job)
        elif job["kind"] == "class" and dtype == job["dtype"]:
            _bump(p, job)


def note_warden(p: dict) -> None:
    """A Warden engagement — counted when the fight OPENS: showing up
    at the keep is the job, win or bleed."""
    for job in board_for(p):
        if job["kind"] == "warden":
            _bump(p, job)


def pay_for(p: dict, job: dict) -> tuple[int, int]:
    """What THIS hand collects for a job. One board for the whole tower,
    but jobs priced off floors a climber cannot reach yet (the class job
    at the tower's waist, the warden bounty at the frontier) pay at the
    hand's own reach + 2 instead — a bonus, never frontier gold
    teleported down to floor 1. This is the guard that let the board
    open at level 2 (0.29.1); culls need no cap (the kill must happen ON
    the named floor, and the entry leash gates that)."""
    reach = max(1, int(p.get("unlocked_floor", 1))) + 2
    fj = int(job.get("floor", 0))
    if not fj or fj <= reach:
        return (job["gold"], job["xp"])
    if job["kind"] == "class":
        return (max(1, round(economy.gold_per_kill(reach) * job["need"]
                             * economy.CONTRACT_CLASS_GOLD_MULT)),
                max(1, round(economy.xp_per_kill(reach) * job["need"]
                             * economy.CONTRACT_CLASS_XP_MULT)))
    if job["kind"] == "warden":
        return (max(1, round(economy.warden_gold(reach)
                             * economy.CONTRACT_WARDEN_MULT)),
                max(1, round(economy.warden_xp(reach)
                             * economy.CONTRACT_WARDEN_MULT)))
    return (job["gold"], job["xp"])


def got(p: dict, job: dict) -> int:
    c = sync(p)
    return min(int(c["got"].get(job["id"], 0)), job["need"])


def claimable(p: dict, job: dict) -> bool:
    c = sync(p)
    return got(p, job) >= job["need"] and job["id"] not in c["claimed"]


def claim(p: dict, job: dict) -> tuple[int, int]:
    """Pay the job out (reach-capped, broker's stamp off the top);
    returns (gold, xp) actually paid. Caller writes the ledger line and
    the scene."""
    c = sync(p)
    if not claimable(p, job):
        return (0, 0)
    c["claimed"].append(job["id"])
    pay_gold, pay_xp = pay_for(p, job)
    gold = max(0, pay_gold - economy.BOARD_PRICE)
    p["gold"] += gold
    from . import state as pstate
    pay_xp = pstate.gain_xp(p, pay_xp)
    if job.get("token"):
        inv = p.setdefault("inventory", {})
        inv[job["token"]] = inv.get(job["token"], 0) + 1
    return (gold, pay_xp)
