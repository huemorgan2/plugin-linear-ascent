"""Owned weapon instances and the three-cell deck shared by every host.

The rules live in the game package. The wiki and simulator consume this
catalog; neither is an alternative resolver or ownership store.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import json
import math
import os
from pathlib import Path

from .. import economy

RULESET = "collection-v1"
GRADES = ("Common", "Rare", "Epic", "Legendary")
MATERIALS = (("Wood", "Raw Metal"), ("Hardwood", "Steel"),
             ("Meteorite", "Starforged Steel"), ("Mythic Threads", "Shard Matter"))
_SKIP = ({12, 13, 22, 23}, {32, 33, 42, 43},
         {52, 53, 62, 63}, {82, 83, 92, 93})


@lru_cache(maxsize=1)
def catalog() -> dict:
    return json.loads((Path(__file__).parents[1] / "content/collection.json").read_text())


@lru_cache(maxsize=1)
def families() -> dict:
    return {w["id"]: w for w in catalog()["weapons"]}


def enabled(p: dict) -> bool:
    return p.get("ruleset") == RULESET


def enrollment_open() -> bool:
    return os.environ.get("ASCENT_RULESET", "") == RULESET


def locked(p: dict) -> bool:
    return bool(p.get("encounter") or (p.get("group") or {}).get("committed")
                or p.get("expedition") or p.get("movie_floor"))


def floor_for(grade: str, level: int) -> int:
    gi = GRADES.index(grade)
    if type(level) is not int or not 0 <= level <= 20:
        raise ValueError("Weapon level must be 0–20")
    return [f for f in range(1 + gi * 25, 26 + gi * 25)
            if f not in _SKIP[gi]][level]


def stats(item: dict) -> dict:
    legacy = item.get("legacy")
    if legacy:
        g = economy.FORGE[legacy["slug"]]
        attack = economy.honed_bonus(g.bonus, legacy["hone"])
        pool = max(1, economy.item_pool(g))
        return dict(attack=attack, maximum=pool, floor=max(1, legacy["floor"]),
                    path=economy.PATH_OF_LINE.get(g.line, "blade"), name=g.name)
    family = families()[item["family"]]
    floor = floor_for(item["grade"], item["level"])
    attack = round(economy.honed_bonus(economy._reference_bonus(floor, "weapon"),
                                      economy.reference_hone(floor)) * family["factor"])
    pool = round(1300 * (1 + .025 * (floor - 1)) * family["end"])
    return dict(attack=max(1, attack), maximum=max(1, pool), floor=floor,
                path=family["path"].lower(), name=family["name"])


def mint(p: dict, family: str, grade: str = "Common", source: str = "craft",
         *, receipt: str = "") -> dict:
    """Create exactly one owned instance. Hosts validate purchases first."""
    f = families()[family]
    if grade not in GRADES or source not in ("craft", "shop", "drop", "starter"):
        raise ValueError("Unknown acquisition source or grade")
    if receipt:
        prior = (p.get("item_receipts") or {}).get(receipt)
        if prior:
            return p["collection"][prior]
    settings = f["acquisition"][grade]
    key = "craft" if source == "starter" else source
    seq = int(p.get("item_sequence", 0)) + 1
    iid = hashlib.sha256(f"{p['luna_user']}:{seq}".encode()).hexdigest()[:32]
    if iid in p.setdefault("collection", {}):
        raise ValueError("Weapon sequence would overwrite ownership")
    item = dict(id=iid, family=family, grade=grade,
                level=settings[key + "Level"], source=source,
                provenance={"receipt": receipt, "owner": p["luna_user"]})
    maximum = stats(item)["maximum"]
    item.update(durability=math.ceil(maximum * settings[key + "DurabilityPct"] / 100),
                maximum=maximum)
    p["item_sequence"] = seq
    p["collection"][iid] = item
    if receipt:
        p.setdefault("item_receipts", {})[receipt] = iid
    return item


def reconcile(p: dict) -> dict:
    owned = p.get("collection") or {}
    deck = p.get("deck") or []
    errors = []
    if len(deck) != 3:
        errors.append("Deck must have exactly three cells")
    ids = [x for x in deck if x is not None]
    if len(ids) != len(set(ids)):
        errors.append("The same instance occupies more than one cell")
    if any(x not in owned for x in ids):
        errors.append("Deck refers to an unowned weapon")
    if p.get("active_weapon") and p["active_weapon"] not in ids:
        errors.append("Active weapon is outside the deck")
    for iid, item in owned.items():
        if iid != item.get("id") or not 0 <= item.get("level", -1) <= 20:
            errors.append("Invalid weapon identity or level")
        if not 0 <= item.get("durability", -1) <= item.get("maximum", -1):
            errors.append("Invalid weapon condition")
    return dict(ok=not errors, errors=errors, owned=len(owned), selected=len(ids))


def set_slot(p: dict, cell: int, iid: str | None) -> None:
    if not enabled(p) or locked(p):
        raise ValueError("Choose your three weapons before the fight or expedition")
    if type(cell) is not int or not 0 <= cell < 3:
        raise ValueError("Choose weapon slot 1, 2 or 3")
    if iid is not None:
        if iid not in p["collection"]:
            raise ValueError("That weapon does not belong to you")
        if iid in p["deck"] and p["deck"][cell] != iid:
            raise ValueError("That weapon is already in your deck")
        item = p["collection"][iid]
        if not item.get("legacy") and p.get("unlocked_floor", 1) < floor_for(item["grade"], 0):
            raise ValueError(f"{item['grade']} weapons open on floor {floor_for(item['grade'], 0)}")
    p["deck"][cell] = iid
    if p.get("active_weapon") not in p["deck"]:
        p["active_weapon"] = next((x for x in p["deck"] if x), None)
    project_legacy(p)


def _legacy_item(p: dict, slug: str, where: str, index: int) -> dict:
    from . import state
    g = economy.FORGE[slug]
    family = {"blade": "breach", "bow": "hawkeye", "staff": "ember"}.get(
        economy.PATH_OF_LINE.get(g.line, "blade"), "breach")
    item = mint(p, family, receipt=f"migration:{where}:{slug}:{index}")
    # A compatibility item keeps its old power and ownership, not an
    # approximate grade conversion which could erase an earned advantage.
    hone = state.hone_level(p, "weapon", slug)
    pool = max(1, economy.item_pool(g))
    lead = where == "held" and slug == p["gear"].get("weapon")
    condition = (p.get("durability", {}).get("weapon", pool) if lead
                 else p.get("durability_pack", {}).get(slug, pool))
    item.update(source="legacy", level=min(20, max(0, hone)),
                durability=max(0, min(pool, int(condition))), maximum=pool,
                legacy=dict(slug=slug, hone=hone, oil=state.oil_left(p, slug),
                            floor=max(1, int((g.tier - 1) * 10 + 1)), location=where))
    return item


def migrate(p: dict, slot_receipts: list[dict] | None = None) -> dict:
    """Idempotent conversion. A preview calls this on a deep copy only."""
    from . import state
    if enabled(p):
        return p["collection_migration"]
    if p.get("stage") != "playing" or p.get("encounter") or p.get("movie_floor"):
        return dict(status="deferred", reason="Finish creation or the current legacy encounter first")
    before_slots = max(1, min(3, int(p.get("slots", 1))))
    archive = {k: deepcopy(p.get(k)) for k in
               ("held", "gear", "inventory", "durability", "durability_pack", "hone", "oil", "slots")}
    p.update(collection={}, deck=[None, None, None], active_weapon=None,
             item_sequence=0, item_receipts={},
             group=None, expedition=None, xp_reserve=int(p.get("xp_reserve", 0)))
    p.setdefault("materials", {})
    p.setdefault("utility_tools", {})
    held = list(p.get("held") or [p["gear"].get("weapon")])
    for i, slug in enumerate(held):
        if slug in economy.FORGE and economy.FORGE[slug].slot == "weapon":
            item = _legacy_item(p, slug, "held", i)
            if i < 3:
                p["deck"][i] = item["id"]
            if slug == p["gear"].get("weapon") and i < 3:
                p["active_weapon"] = item["id"]
    for slug, count in list(p.get("inventory", {}).items()):
        if slug in economy.FORGE and economy.FORGE[slug].slot == "weapon":
            for i in range(max(0, int(count))):
                _legacy_item(p, slug, "pack", i)
            del p["inventory"][slug]
    p["active_weapon"] = p["active_weapon"] or next((x for x in p["deck"] if x), None)
    refund = dict(gold=0, xp=0, basis="recorded receipts")
    receipts = slot_receipts if slot_receipts is not None else p.get("school_slot_receipts")
    for slot, gold, xp in ((2, 30, 60), (3, 200, 500)):
        if before_slots < slot:
            continue
        matching = [r for r in receipts or [] if r.get("kind") == "train" and r.get("note") == f"carry {slot}"]
        if matching:
            # One purchase per slot; duplicated imported receipts cannot
            # multiply compensation. The first historical purchase wins.
            refund["gold"] += max(0, -int(matching[0].get("gold", 0)))
            refund["xp"] += max(0, -int(matching[0].get("xp", 0)))
        else:
            refund["gold"] += gold
            refund["xp"] += xp
            refund["basis"] = "includes capped original minimum fee where receipt missing"
    p["ruleset"] = RULESET
    p["slots"] = 3
    p["gold"] += refund["gold"]
    state.gain_xp(p, refund["xp"])
    receipt = dict(id=RULESET, status="applied", legacy=archive,
                   refund=refund, count=len(p["collection"]))
    p["collection_migration"] = receipt
    p.setdefault("_ledger", []).append(dict(kind="slot_refund", gold=refund["gold"],
                                            xp=refund["xp"], note=RULESET))
    if not reconcile(p)["ok"]:
        raise ValueError("Collection migration failed ownership reconciliation")
    return receipt


def preview(p: dict, slot_receipts: list[dict] | None = None) -> dict:
    copy = deepcopy(p)
    result = migrate(copy, slot_receipts)
    return dict(result=result, reconciliation=reconcile(copy) if enabled(copy) else None,
                document=copy)


def sync(p: dict) -> None:
    if enabled(p):
        p["slots"] = 3
        return
    if enrollment_open():
        migrate(p)


def active(p: dict) -> dict | None:
    return (p.get("collection") or {}).get(p.get("active_weapon"))


def project_legacy(p: dict) -> None:
    """Compatibility pointers, never a second ownership container."""
    items = [p["collection"][i] for i in p["deck"] if i]
    p["held"] = [i["legacy"]["slug"] for i in items if i.get("legacy")]
    lead = active(p)
    if lead and lead.get("legacy"):
        p["gear"]["weapon"] = lead["legacy"]["slug"]
        p.setdefault("durability", {})["weapon"] = lead["durability"]
    for item in items:
        if item.get("legacy") and item is not lead:
            p.setdefault("durability_pack", {})[item["legacy"]["slug"]] = item["durability"]


def capture_legacy_wear(p: dict) -> None:
    item = active(p)
    if not item or not item.get("legacy") or p.get("group"):
        return
    if p["gear"].get("weapon") == item["legacy"]["slug"]:
        item["durability"] = min(item["maximum"], max(0, int(p.get("durability", {}).get("weapon", item["durability"]))))


def public_deck(p: dict) -> list[dict | None]:
    out = []
    for iid in p.get("deck", []):
        item = (p.get("collection") or {}).get(iid)
        if not item:
            out.append(None)
        else:
            out.append({k: item[k] for k in ("id", "family", "grade", "level", "durability", "maximum")})
    return out


def upgrade_quote(item: dict) -> dict | None:
    if item.get("legacy") or item["level"] >= 20:
        return None
    family = families()[item["family"]]
    gi = GRADES.index(item["grade"])
    level = item["level"] + 1
    floor = floor_for(item["grade"], level)
    q = 0
    for n in range(level + 1):
        q = max(q + 1, math.ceil((1, 3, 8, 20)[gi] * 1.18 ** n))
    gold = math.ceil((125, 47.5, 53.5, 47.5)[gi] * 1.3 ** (floor - 1) * family["cost"])
    return dict(level=level, floor=floor, gold=gold,
                materials={name: q * ratio for name, ratio in zip(MATERIALS[gi], family["recipe"])})


def card(p: dict, item: dict) -> dict:
    info = stats(item)
    family = families()[item["family"]]
    art = family["artByGrade"][item["grade"]]
    if item.get("legacy"):
        image = f"weapons/large/{item['legacy']['slug']}_100x160.png"
    elif art["source"] == "collection":
        image = art["file"]
    else:
        image = f"weapons/large/{art['slug']}_100x160.png"
    quote = upgrade_quote(item)
    return {**{k: item[k] for k in ("id", "family", "grade", "level", "durability", "maximum", "source")},
            **info, "image": image, "effect": "Original honing retained" if item.get("legacy") else family["effect"],
            "description": family["description"], "quote": quote,
            "can_afford": bool(quote and p["gold"] >= quote["gold"] and all(
                p.get("materials", {}).get(k, 0) >= n for k, n in quote["materials"].items())),
            "selected": item["id"] in p.get("deck", []),
            "active": item["id"] == p.get("active_weapon")}


def payload(p: dict) -> dict:
    return dict(deck=list(p["deck"]), items=[card(p, i) for i in p["collection"].values()],
                locked=locked(p), materials=dict(p.get("materials", {})),
                gold=p["gold"], xp_reserve=p.get("xp_reserve", 0),
                selected=p.get("collection_selected"), screen=bool(p.get("collection_view")))


def scene(p: dict):
    from .scene import Scene, Option
    from .combat import meters
    opts = []
    selected = p.get("collection_selected")
    if selected in p["collection"] and not locked(p):
        item = p["collection"][selected]
        for cell in range(3):
            opts.append(Option(f"deck:{cell}:{selected}", f"Set in weapon slot {cell + 1}"))
        if selected in p["deck"]:
            opts.append(Option(f"unslot:{p['deck'].index(selected)}", "Return to collection"))
    opts.append(Option("collection_back", "Back"))
    return Scene(eyebrow="YOUR WEAPON COLLECTION", headline="Three weapons. Your choice.",
        support="Choose any three weapons before a hunt. Each weapon keeps its own level and condition.",
        body_lines=(["Your weapons stay committed until this fight or expedition ends."] if locked(p) else []),
        options=opts, meters=meters(p), collection=payload(p))


def handle(p: dict, oid: str):
    """Small public action surface; None means another engine subsystem."""
    if not enabled(p):
        return None
    if oid == "collection":
        p["collection_view"] = True
        return scene(p)
    if oid == "collection_back" and p.get("collection_view"):
        from .core import _build_scene
        p.pop("collection_view", None)
        p.pop("collection_selected", None)
        return _build_scene(p)
    if oid.startswith("inspect:"):
        iid = oid.partition(":")[2]
        if iid in p["collection"]:
            p["collection_view"] = True
            p["collection_selected"] = iid
            return scene(p)
        return None
    if not p.get("collection_view"):
        return None
    if oid.startswith(("deck:", "unslot:")):
        try:
            parts = oid.split(":")
            if parts[0] == "deck" and len(parts) == 3:
                set_slot(p, int(parts[1]), parts[2])
            elif parts[0] == "unslot" and len(parts) == 2:
                set_slot(p, int(parts[1]), None)
            else:
                raise ValueError("Choose a weapon from your collection")
        except ValueError as exc:
            s = scene(p)
            s.refusal = str(exc)
            return s
        return scene(p)
    return None
