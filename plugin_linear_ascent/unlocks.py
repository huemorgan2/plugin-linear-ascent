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
        Unlock("receive_grants", "level", economy.GRANT_MIN_RECEIVER_LEVEL,
               "opens", "receiving grants", "the vault",
               "other climbers can send you gold at the Vault"),
        Unlock("arcanum", "level", economy.ARCANUM_LEVEL, "opens",
               "the Arcanum", "the square",
               "staves, focuses and caster relics behind the reading door"),
        Unlock("board", "level", economy.BOARD_LEVEL, "opens",
               "the contract board", "the square",
               f"{economy.BOARD_JOBS_PER_DAY} world jobs a day — the same "
               "three for every climber, paid in gold and XP"),
        # ── level, closes — the protections that expire ──
        Unlock("mercy_ends", "level",
               economy.BEGINNER_MERCY_MAX_LEVEL + 1, "closes",
               "beginner's mercy ends", "the tower",
               "a death starts costing gear and a bite of carried gold"),
        Unlock("pvp_immunity_ends", "level",
               economy.BEGINNER_PROTECTION_MAX_LEVEL + 1, "closes",
               "ambush immunity ends", "the fields",
               "other climbers can ambush you back — the Lodge is the shield"),
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
    stably grouped by (gate, at) for rendering."""
    todo = [u for u in registry() if not met(p, u)]
    todo.sort(key=lambda u: (_distance(p, u),
                             0 if u.gate == "level" else 1,
                             u.at,
                             {"opens": 0, "closes": 1, "changes": 2}[u.effect]))
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
