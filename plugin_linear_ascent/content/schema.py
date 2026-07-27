"""Content loader — floors as YAML, numbers computed, never authored.

Validation gates (002 workstream C): schema fields, unique ids, positive
weights, prose caps, NO economy numbers in content (they derive from
economy.py formulas), banned out-of-world vocabulary.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

import yaml

from .. import economy

FLOORS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "floors")

PROSE_CAP = 260
BANNED_WORDS = (
    "plugin", "tool", "llm", "ai model", "database", "server", "api",
    "click", "button", "json", "yaml",
)
_FORBIDDEN_NUMERIC_KEYS = {"atk", "def", "hp", "xp", "gold", "damage", "price"}
# Encounter traits: qualitative flags the engine turns into numbers
# (economy.py profile_from_traits) — content stays prose-only.
# 017 §2.2: armor/resist tiers, flying, bulwark, speed. Legacy "armored"
# maps to armor_med and is only legal on floors > 10 until phase 008
# migrates them.
ALLOWED_TRAITS = {
    "armor_low", "armor_med", "armor_high",
    "resist_low", "resist_med", "resist_high",
    "flying", "bulwark", "slow", "fast",
    "armored",  # legacy — lint forbids it on floors ≤ 10
}

# 017 §2.3 the intro staircase: the first floor where a rule may appear.
# Floor 1 is kindergarten — no traits at all. Lint enforces both.
TRAIT_INTRO_FLOOR = {
    "armor": 2, "resist": 3, "flying": 4, "fast": 5,
    "bulwark": 6, "slow": 6,
}


def _trait_family(trait: str) -> str:
    if trait.startswith("armor_") or trait == "armored":
        return "armor"
    if trait.startswith("resist_"):
        return "resist"
    return trait


class ContentError(ValueError):
    pass


@dataclass(frozen=True)
class Encounter:
    id: str
    name: str
    prose: str
    weight: int
    traits: tuple[str, ...] = ()


@dataclass(frozen=True)
class Floor:
    floor: int
    tier: int
    biome: str
    zone: str
    gate_town: str
    arrival: str
    banner: str
    encounters: list[Encounter]
    warden_name: str
    warden_prose: str
    # computed (economy.py — never authored)
    monster_atk: int = 0
    monster_def: int = 0
    monster_hp: int = 0
    warden_atk: int = 0
    warden_def: int = 0
    warden_hp: int = 0
    milestone: "economy.MilestoneBoss | None" = None


def _check_prose(text: str, where: str) -> None:
    if len(text) > PROSE_CAP:
        raise ContentError(f"{where}: prose over {PROSE_CAP} chars")
    low = text.lower()
    for w in BANNED_WORDS:
        # whole words only: "clicking mandibles" is in-world; "click 2" is not
        if re.search(rf"\b{re.escape(w)}\b", low):
            raise ContentError(f"{where}: banned word {w!r}")


def _load_floor_file(path: str) -> Floor:
    raw = yaml.safe_load(open(path))
    where = os.path.basename(path)
    for key in ("floor", "tier", "biome", "zone", "gate_town", "arrival",
                "banner", "encounters", "warden"):
        if key not in raw:
            raise ContentError(f"{where}: missing {key!r}")
    for k in raw:
        if k in _FORBIDDEN_NUMERIC_KEYS:
            raise ContentError(
                f"{where}: economy field {k!r} must not be authored")
    f = int(raw["floor"])
    encounters: list[Encounter] = []
    seen: set[str] = set()
    for e in raw["encounters"]:
        for k in e:
            if k in _FORBIDDEN_NUMERIC_KEYS:
                raise ContentError(
                    f"{where}/{e.get('id')}: economy field {k!r} authored")
        if e["id"] in seen:
            raise ContentError(f"{where}: duplicate encounter id {e['id']!r}")
        seen.add(e["id"])
        if int(e.get("weight", 1)) <= 0:
            raise ContentError(f"{where}/{e['id']}: weight must be positive")
        traits = tuple(e.get("traits") or ())
        for t in traits:
            if t not in ALLOWED_TRAITS:
                raise ContentError(f"{where}/{e['id']}: unknown trait {t!r}")
            if t == "armored" and f <= 10:
                raise ContentError(
                    f"{where}/{e['id']}: legacy trait 'armored' — floors "
                    "1-10 use the 017 tier traits")
            intro = TRAIT_INTRO_FLOOR.get(_trait_family(t))
            if intro is not None and f < intro:
                raise ContentError(
                    f"{where}/{e['id']}: trait {t!r} before its intro "
                    f"floor {intro} (017 staircase)")
        _check_prose(e["prose"], f"{where}/{e['id']}")
        encounters.append(Encounter(
            id=e["id"], name=e["name"], prose=e["prose"],
            weight=int(e.get("weight", 1)), traits=traits))
    if not encounters:
        raise ContentError(f"{where}: no encounters")
    _check_prose(raw["arrival"], f"{where}/arrival")
    _check_prose(raw["warden"]["prose"], f"{where}/warden")

    matk, mdef, mhp = economy.monster_stats(f)
    watk, wdef, whp = economy.warden_stats(f)
    return Floor(
        floor=f, tier=int(raw["tier"]), biome=raw["biome"], zone=raw["zone"],
        gate_town=raw["gate_town"], arrival=raw["arrival"],
        banner=raw["banner"], encounters=encounters,
        warden_name=raw["warden"]["name"], warden_prose=raw["warden"]["prose"],
        monster_atk=matk, monster_def=mdef, monster_hp=mhp,
        warden_atk=watk, warden_def=wdef, warden_hp=whp,
        milestone=economy.MILESTONES.get(f),
    )


_floors: dict[int, Floor] | None = None


def lint_floors() -> list[str]:
    """Strict pass over every floor file. Returns all errors (CI gate)."""
    errors: list[str] = []
    seen: set[int] = set()
    for fname in sorted(os.listdir(FLOORS_DIR)):
        if not fname.endswith(".yaml"):
            continue
        try:
            fl = _load_floor_file(os.path.join(FLOORS_DIR, fname))
        except Exception as e:  # noqa: BLE001 — collect, don't abort
            errors.append(str(e))
            continue
        if fl.floor in seen:
            errors.append(f"{fname}: duplicate floor {fl.floor}")
        seen.add(fl.floor)
    return errors


def load_floors(force: bool = False) -> dict[int, Floor]:
    """Runtime loader: a bad floor file must not brick the whole game.

    Invalid files are skipped (the strict gate is lint_floors / tests);
    players simply can't climb past the last valid floor.
    """
    global _floors
    if _floors is None or force:
        floors: dict[int, Floor] = {}
        for fname in sorted(os.listdir(FLOORS_DIR)):
            if not fname.endswith(".yaml"):
                continue
            try:
                fl = _load_floor_file(os.path.join(FLOORS_DIR, fname))
            except Exception:  # noqa: BLE001
                continue
            if fl.floor not in floors:
                floors[fl.floor] = fl
        _floors = floors
    return _floors


def get_floor(n: int) -> Floor:
    floors = load_floors()
    if n not in floors:
        raise ContentError(f"floor {n} has no content")
    return floors[n]


def max_content_floor() -> int:
    return max(load_floors())
