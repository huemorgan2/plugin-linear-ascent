"""020 — the climb ahead: every gate in the game, one declarative table.

The registry is a VIEW over the live constants (economy.py, engine/social.py)
— never a second copy of the numbers. Surfaces render from it: the square's
NEXT line, the Stone's ladder, locked rows, level-up announcements, the
character sheet. Closing things (protections that expire) are first-class:
the two most expensive surprises in the game are not features arriving.

Grammar, everywhere the ladder renders:
    +  opens      −  closes      ▲  changes the rules
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from . import economy
from .economy import rung_player_level_req


@dataclass(frozen=True)
class Unlock:
    id: str          # "found_guild" — matches the option id where one exists
    gate: str        # "level" | "floor"
    at: int          # the threshold
    effect: str      # "opens" | "closes" | "changes"
    title: str       # "raise your own banner"
    where: str       # the location that hosts it
    why: str         # one line, the game's voice, numbers included
    cost: str = ""   # "◈ 500"


_GLYPH = {"opens": "+", "closes": "−", "changes": "▲"}


@lru_cache(maxsize=1)
def registry() -> tuple[Unlock, ...]:
    """Built lazily (engine.social imports this module) and cached —
    every threshold is read from its owning constant."""
    from .engine import social

    out: list[Unlock] = [
        # ── level, opens ──
        Unlock("relay", "level", economy.RELAY_LEVEL, "opens",
               "the Relay Office", "the square",
               "letters between climbers — free to write, gold rides along"),
        Unlock("found_guild", "level", social.FOUND_MIN_LEVEL, "opens",
               "raise your own banner", "guildhall",
               "you set the join fee and dues, and steward the store",
               f"◈ {social.GUILD_FOUND_FEE}"),
        Unlock("fields", "level", economy.FIELDS_LEVEL, "opens",
               "the fields", "the square",
               f"ambush other climbers — {economy.COST_PVP_ATTACK} ⚡ a raid, "
               f"{economy.PVP_ATTACKS_PER_DAY} a day"),
        Unlock("arcanum", "level", economy.ARCANUM_LEVEL, "opens",
               "the Arcanum", "the square",
               "staves, focuses and caster relics behind the reading door"),
        Unlock("board", "level", economy.BOARD_LEVEL, "opens",
               "the contract board", "the square",
               f"{economy.BOARD_JOBS_PER_DAY} world jobs a day — the same "
               "three for every climber, paid in gold and XP"),
        Unlock("night_slot", "level", economy.NIGHT_SLOT_LEVEL, "opens",
               "the night slot", "the lodge",
               "one action a night — rest toward your next kills, or "
               "work a shift for coin at dawn"),
        Unlock("strongbox", "level", economy.STRONGBOX_LEVEL, "opens",
               "the weekly strongbox", "the vault",
               "a week of kills, keeps and floors opens slots — pick "
               "ONE reward at the tick"),
        Unlock("carry3", "level", economy.CARRY3_LEVEL, "opens",
               "the third carry slot", "the School",
               "a veteran's grip — three weapons into every fight",
               f"{economy.CARRY3_XP} XP + coin"),
        # ── level, closes — the protections that expire ──
        Unlock("mercy_ends", "level",
               economy.BEGINNER_MERCY_MAX_LEVEL + 1, "closes",
               "beginner's mercy ends", "the tower",
               "a death starts costing gear and a bite of carried gold"),
        Unlock("pvp_immunity_ends", "level",
               economy.BEGINNER_PROTECTION_MAX_LEVEL + 1, "closes",
               "ambush immunity ends", "the fields",
               "other climbers can ambush you back — the Lodge is the shield"),
        # 031 §8: past this level a death is no accident of bookkeeping
        Unlock("pardon_ends", "level",
               economy.DEATH_NO_PARDON_LEVEL, "closes",
               "the pardon ends", "the tower",
               "death scatters 90% of carried gold and shakes a stack "
               "loose from your pack"),
    ]
    # ── gear tiers: a level gate up to the cap, the WORLD's floor past
    # it (022/002 — the cap can never strand a tier) ──
    for t in range(2, 11):
        freq = economy.gear_floor_req(t)
        if freq:
            out.append(Unlock(
                f"gear_tier_{t}", "floor", freq, "opens",
                f"tier-{t} steel", "forge",
                f"when the war opens floor {freq}, the tier-{t} rack "
                "answers to any capped hand"))
        else:
            out.append(Unlock(
                f"gear_tier_{t}", "level", economy.gear_player_level_req(t),
                "opens", f"tier-{t} steel", "forge",
                f"the tier-{t} rack at the Forge answers to your hand"))
    # ── 025 §4: band 1's per-level rungs. One entry a level, not one per
    # slot — the ladder answers "what does level 4 sell me" without
    # becoming a catalogue. This is the complaint that opened 025, so it
    # belongs on the Stone and in the level-up announcement. ──
    band1: dict[int, list] = {}
    for g in economy.FORGE.values():
        if g.style or g.slot == "shoes" or not 1 < g.rung < 2:
            continue
        band1.setdefault(rung_player_level_req(g), []).append(g)
    for lvl, items in sorted(band1.items()):
        lo = min(g.price for g in items)
        hi = max(g.price for g in items)
        out.append(Unlock(
            f"band1_rung_{lvl}", "level", lvl, "opens",
            "new steel on the racks", "forge",
            f"the next rung of blade, guard and coat — and each cut keen "
            f"or warded if you'd rather trade upkeep for bite",
            f"◈ {lo:,}–{hi:,}"))
    # ── the shoes ladder's explicit gates (level to the cap, floor past) ──
    for g in sorted((g for g in economy.FORGE.values()
                     if g.slot == "shoes" and g.level),
                    key=lambda g: g.level):
        freq = economy.rung_floor_req(g)
        out.append(Unlock(
            f"shoes_{g.slug}", "floor" if freq else "level",
            freq or g.level, "opens",
            g.name, "forge",
            f"+{g.speed} speed — the chase, the getaway and the small dodge",
            f"◈ {g.price:,}"))
    # ── the energy cap rides the gear band now (022/002), so its
    # announcements sit on the same gates as the tiers themselves ──
    for t in range(2, 11):
        freq = economy.gear_floor_req(t)
        out.append(Unlock(
            f"energy_cap_tier_{t}", "floor" if freq else "level",
            freq or economy.gear_player_level_req(t), "changes",
            "the energy cap grows", "forge",
            f"⚡ cap rises to {economy.energy_cap(t)} with tier-{t} steel "
            "on your back — one more hunt a day"))
    # ── floor, opens: the relic shelves (bands only, never named loot) ──
    shelf: dict[int, int] = {}
    for r in economy.RELICS.values():
        shelf[r.floor] = shelf.get(r.floor, 0) + 1
    for fl in sorted(shelf):
        if fl <= 1:
            continue
        n = shelf[fl]
        out.append(Unlock(
            f"relics_floor_{fl}", "floor", fl, "opens",
            "new relics reach the shelves", "the shops",
            f"{n} relic{'s' if n != 1 else ''} join the racks at floor {fl}"))
    # ── floor, changes: honing cap reset per gear band ──
    for t in range(2, 11):
        fl = economy.band_start(t)
        out.append(Unlock(
            f"hone_reset_{t}", "floor", fl, "changes",
            "the honing cap resets", "forge",
            f"band {t} opens a fresh bench — honing counts from floor {fl}"))
    # ── floor, changes: milestone Wardens with their quorum (022/002:
    # the N(F) curve can raise the war party above the table's floor) ──
    for m in economy.MILESTONES.values():
        out.append(Unlock(
            f"milestone_{m.floor}", "floor", m.floor, "changes",
            f"{m.name} holds floor {m.floor}", "the keep",
            f"no solo kill — a war party of "
            f"{economy.milestone_quorum(m.floor)} pledges "
            f"{economy.COST_BOSS_COMMIT} ⚡ each at the Guildhall"))
    return tuple(out)


def met(p: dict, u: Unlock) -> bool:
    if u.gate == "level":
        return p["level"] >= u.at
    return p["unlocked_floor"] >= u.at


def _distance(p: dict, u: Unlock) -> int:
    now = p["level"] if u.gate == "level" else p["unlocked_floor"]
    return u.at - now


def ahead(p: dict, limit: int = 0) -> list[Unlock]:
    """Unmet gates, nearest first, level before floor at equal distance,
    stably grouped by (gate, at) for rendering. A threshold that CLOSES
    something reads first inside its group: the racks arriving are the
    pleasant news, and the fold is capped."""
    todo = [u for u in registry() if not met(p, u)]
    todo.sort(key=lambda u: (_distance(p, u),
                             0 if u.gate == "level" else 1,
                             u.at,
                             {"closes": 0, "opens": 1, "changes": 2}[u.effect]))
    return todo[:limit] if limit else todo


def just_reached(p: dict, old_level: int, old_floor: int) -> list[Unlock]:
    """What this level-up / floor-open changed — for announcements."""
    out = []
    for u in registry():
        old = old_level if u.gate == "level" else old_floor
        now = p["level"] if u.gate == "level" else p["unlocked_floor"]
        if old < u.at <= now:
            out.append(u)
    out.sort(key=lambda u: ({"opens": 0, "closes": 1, "changes": 2}[u.effect],
                            u.at))
    return out


def for_option(oid: str):
    """The registry entry behind an option id, so a locked row and the
    ladder can never disagree on the reason."""
    for u in registry():
        if u.id == oid:
            return u
    return None


def glyph(u: Unlock) -> str:
    return _GLYPH[u.effect]


_PLAIN = {
    "relay": "you can send letters to other players — writing is free, "
             "and you can attach gold",
    "found_guild": "you can start your own guild — you pick the join fee "
                   "and the weekly dues, and you run its shared store",
    "arcanum": "a second weapon shop opens (the Arcanum) — it sells "
               "staves, focuses and relics for sorcerers",
    "night_slot": "you get one action each night — sleep to heal and "
                  "fight better tomorrow, or work a shift and get paid "
                  "gold in the morning",
    "strongbox": "the weekly strongbox opens — the monsters you kill and "
                 "the floors you clear during the week earn you a pick of "
                 "ONE reward when the week ends",
    "carry3": "you can carry a third weapon into fights (buy the "
              "training at the School)",
    "mercy_ends": "WARNING — from now on, dying can cost you your "
                  "equipment and part of the gold you carry",
    "pvp_immunity_ends": "WARNING — from now on, other players can attack "
                         "you in the fields; sleeping at the Lodge keeps "
                         "you safe",
    "pardon_ends": "WARNING — from now on, dying drops 90% of the gold "
                   "you carry and one stack of items from your pack",
}


def plain(u: Unlock) -> str:
    """The same fact as u.why, in plain English — for the level-up box,
    where a player must understand what just changed without knowing
    the game's slang."""
    if u.id in _PLAIN:
        return _PLAIN[u.id]
    if u.id == "fields":
        return (f"you can attack other players in the fields — a raid "
                f"costs {economy.COST_PVP_ATTACK} energy, up to "
                f"{economy.PVP_ATTACKS_PER_DAY} raids a day")
    if u.id == "board":
        return (f"the contract board opens — {economy.BOARD_JOBS_PER_DAY} "
                "jobs a day that pay gold and XP; every player sees the "
                "same jobs")
    if u.id.startswith("gear_tier_"):
        t = int(u.id.rsplit("_", 1)[1])
        return f"the Forge will now sell you tier-{t} equipment"
    if u.id.startswith("band1_rung_"):
        return ("the shops sell the next step up of weapon, shield and "
                "armor — each also comes in a 'keen' cut (hits harder, "
                "wears out faster) or a 'warded' cut (lasts longer)")
    if u.id.startswith("shoes_"):
        g = economy.FORGE.get(u.id[len("shoes_"):])
        sp = f" (+{g.speed} speed)" if g is not None else ""
        return (f"new boots at the Forge{sp} — you get faster: better at "
                "chasing, escaping and dodging")
    if u.id.startswith("energy_cap_tier_"):
        t = int(u.id.rsplit("_", 1)[1])
        return (f"your energy cap rises to {economy.energy_cap(t)} once "
                f"you wear tier-{t} armor — enough for one more fight "
                "each day")
    if u.id.startswith("relics_floor_"):
        return "new relics (one-use battle items) are for sale in the shops"
    if u.id.startswith("hone_reset_"):
        return ("you can sharpen your equipment at the Forge again — the "
                "sharpening limit starts fresh for this band of floors")
    if u.id.startswith("milestone_"):
        return ("a boss holds this floor — you cannot kill it alone; a "
                "group must pledge energy together at the Guildhall")
    return u.why


def _entry_line(u: Unlock) -> str:
    cost = f" ({u.cost})" if u.cost else ""
    return f"{glyph(u)} {u.title}{cost} — {u.why}"


def next_line(p: dict) -> str:
    """The square's footer: the nearest threshold with everything it
    brings — including any protection that dies with it."""
    nxt = ahead(p, 1)
    if not nxt:
        return ""
    gate, at = nxt[0].gate, nxt[0].at
    group = [u for u in ahead(p) if u.gate == gate and u.at == at]
    bits = []
    for u in group[:3]:
        cost = f" ({u.cost})" if u.cost else ""
        lead = {"opens": "", "closes": "and ", "changes": "and "}[u.effect]
        verb = {"opens": "", "closes": " — ", "changes": " — "}[u.effect]
        bits.append(f"{lead}{u.title}{cost}{verb}"
                    + (u.why if u.effect != "opens" else ""))
    label = "LEVEL" if gate == "level" else "FLOOR"
    return f"NEXT — {label} {at}: " + " · ".join(b.rstrip(" —") for b in bits)


def climb_ahead_lines(p: dict, limit: int = 8) -> list[str]:
    """The Stone's fold: the whole ladder, grouped by threshold,
    + / − / ▲ per entry, capped so a level-1 player never reads
    floor 91's gear band."""
    rows = ahead(p, limit)
    if not rows:
        return ["the ladder is yours — nothing above you is sealed"]
    lines: list[str] = []
    seen: set[tuple[str, int]] = set()
    for u in rows:
        key = (u.gate, u.at)
        if key not in seen:
            seen.add(key)
            label = "LEVEL" if u.gate == "level" else "FLOOR"
            lines.append(f"{label} {u.at}")
        lines.append(f"  {_entry_line(u)}")
    if len(ahead(p)) > limit:
        lines.append("  …and the tower keeps the rest")
    return lines


def protections_active(p: dict) -> list[str]:
    """The expiring shields currently over the player — for the sheet."""
    out = []
    if p["level"] <= economy.BEGINNER_MERCY_MAX_LEVEL:
        out.append(f"beginner's mercy — PvE deaths keep your gear "
                   f"(ends at level {economy.BEGINNER_MERCY_MAX_LEVEL + 1})")
    if p["level"] <= economy.BEGINNER_PROTECTION_MAX_LEVEL:
        out.append(f"ambush immunity — no PvP against you (ends at level "
                   f"{economy.BEGINNER_PROTECTION_MAX_LEVEL + 1})")
    return out
