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
LORE_CAP = 160          # 003: the [i] dossier's flavor line — one breath
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
    # 025 §1: the stat archetype — the body and the bite. Legal from floor
    # 1: this is the variance the first floor never had, and it is the
    # difference between four animals and one animal in four costumes.
    "frail", "lean", "sturdy", "hulking",
    "feeble", "fierce", "savage",
}

ARCHETYPE_TRAITS = {"frail", "lean", "sturdy", "hulking",
                    "feeble", "fierce", "savage"}

# 017 §2.3 the intro staircase: the first floor where a rule may appear.
# 025: the staircase governs the DEFENSE axis only. Speed came down to
# floor 1 with the archetypes — being outrun is chase math, not damage,
# and "some of them you have to run from" is the point of the first floor.
TRAIT_INTRO_FLOOR = {
    "armor": 2, "resist": 3, "flying": 4,
    "bulwark": 6,
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
    lore: str = ""      # 003: dossier flavor — optional, ≤ LORE_CAP


@dataclass(frozen=True)
class Npc:
    """030: the floor's one voice — numberless prose, the engine says
    the numbers (warden strength is derived, never authored)."""
    name: str
    role: str
    greet: str
    lore: str
    warn: str


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
    npc: "Npc | None" = None
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
        lore = str(e.get("lore") or "").strip()
        if lore:
            if len(lore) > LORE_CAP:
                raise ContentError(
                    f"{where}/{e['id']}: lore over {LORE_CAP} chars")
            _check_prose(lore, f"{where}/{e['id']}/lore")
        encounters.append(Encounter(
            id=e["id"], name=e["name"], prose=e["prose"],
            weight=int(e.get("weight", 1)), traits=traits, lore=lore))
    if not encounters:
        raise ContentError(f"{where}: no encounters")
    _check_prose(raw["arrival"], f"{where}/arrival")
    _check_prose(raw["warden"]["prose"], f"{where}/warden")

    npc = None
    if raw.get("npc") is not None:
        n_raw = raw["npc"]
        for k in n_raw:
            if k in _FORBIDDEN_NUMERIC_KEYS:
                raise ContentError(
                    f"{where}/npc: economy field {k!r} must not be authored")
        for key in ("name", "role", "greet", "lore", "warn"):
            if not str(n_raw.get(key) or "").strip():
                raise ContentError(f"{where}/npc: missing {key!r}")
        for key in ("greet", "lore", "warn"):
            _check_prose(str(n_raw[key]), f"{where}/npc/{key}")
        npc = Npc(name=str(n_raw["name"]).strip(),
                  role=str(n_raw["role"]).strip(),
                  greet=str(n_raw["greet"]).strip(),
                  lore=str(n_raw["lore"]).strip(),
                  warn=str(n_raw["warn"]).strip())

    matk, mdef, mhp = economy.monster_stats(f)
    watk, wdef, whp = economy.warden_stats(f)
    return Floor(
        floor=f, tier=int(raw["tier"]), biome=raw["biome"], zone=raw["zone"],
        gate_town=raw["gate_town"], arrival=raw["arrival"],
        banner=raw["banner"], encounters=encounters,
        warden_name=raw["warden"]["name"], warden_prose=raw["warden"]["prose"],
        npc=npc,
        monster_atk=matk, monster_def=mdef, monster_hp=mhp,
        warden_atk=watk, warden_def=wdef, warden_hp=whp,
        milestone=economy.MILESTONES.get(f),
    )


_floors: dict[int, Floor] | None = None


def _class_pool_errors(fl: Floor) -> list[str]:
    """008: every class keeps a hunting pool on every floor ≥ 11 —
    at least two encounter types it hits at full damage (no bulwark,
    no speed counter). The sim gate proves the pool wins; this lint
    proves the pool EXISTS before anyone runs a sim."""
    errors = []
    for clazz, dtype in economy.DAMAGE_TYPE.items():
        good = 0
        for e in fl.encounters:
            prof = economy.profile_from_traits(e.traits)
            if dtype == "melee" and prof["flying"]:
                continue
            tier = prof["resist"] if dtype == "magic" else prof["armor"]
            if economy.TIER_MULT[tier] < 1.0 or prof["bulwark"]:
                continue
            if dtype == "ranged" and prof["speed"] >= economy.SPEED_FAST:
                continue
            good += 1
        if good < 2:
            errors.append(
                f"floor {fl.floor}: {clazz} has {good} full-damage "
                "targets — needs ≥2 (008 spread rule)")
    return errors


def _archetype_errors(fl: Floor) -> list[str]:
    """025 §1: a floor is a RANGE of animals. Every floor owes the player
    prey they can farm, a peer, and something that can kill them — and no
    creature may stack a long body on a damage-halving tier, because both
    axes multiply fight length and the product is a slog, not a fight."""
    errors, prey, threat = [], 0, 0
    for e in fl.encounters:
        body, bite = economy._archetype(e.traits)
        prof = economy.profile_from_traits(e.traits)
        if bite == "feeble" or body == "frail":
            prey += 1
        if bite in ("fierce", "savage"):
            threat += 1
        halves = (economy.TIER_MULT[prof["armor"]] <= 0.5
                  or economy.TIER_MULT[prof["resist"]] <= 0.5
                  or prof["bulwark"])
        if body and halves:
            errors.append(
                f"floor {fl.floor}/{e.id}: body trait {body!r} stacked on a "
                "damage-halving profile — both multiply fight length (025)")
        # A blade cannot reach a flying thing (017's one legal zero), so a
        # flyer with a real bite is an unanswerable death for a warrior —
        # not a fight they may lose — until the shop sells the Sky-Hook.
        # The rule reads the shelf: move the hook and this moves with it.
        if (prof["flying"] and bite in ("fierce", "savage")
                and fl.floor < economy.RELICS["sky_hook"].floor):
            errors.append(
                f"floor {fl.floor}/{e.id}: flying + {bite!r} — no melee "
                "counter is on sale this low (025)")
    if not prey:
        errors.append(f"floor {fl.floor}: no prey — every floor owes one "
                      "cheap kill (025 spread rule)")
    if not threat:
        errors.append(f"floor {fl.floor}: nothing here can kill an at-level "
                      "climber (025 spread rule)")
    return errors


def _band_spread_errors(band: list[Floor]) -> list[str]:
    """008: each ten-floor band carries the whole vocabulary — ≥1 bad
    target per class (armor for steel and string, resist for the wand,
    flying for the blade), ≥1 fast, ≥1 slow, ≥1 bulwark."""
    lo, hi = band[0].floor, band[-1].floor
    have: set[str] = set()
    for fl in band:
        for e in fl.encounters:
            prof = economy.profile_from_traits(e.traits)
            if economy.TIER_MULT[prof["armor"]] <= 0.5:
                have.add("armor_med+")
            if economy.TIER_MULT[prof["resist"]] <= 0.5:
                have.add("resist_med+")
            for flag in ("flying", "bulwark"):
                if prof[flag]:
                    have.add(flag)
            if prof["speed"] >= economy.SPEED_FAST:
                have.add("fast")
            if prof["speed"] <= economy.SPEED_SLOW:
                have.add("slow")
    need = {"armor_med+", "resist_med+", "flying", "bulwark",
            "fast", "slow"}
    return [f"band {lo}-{hi}: no {m} encounter (008 spread rule)"
            for m in sorted(need - have)]


def lint_floors() -> list[str]:
    """Strict pass over every floor file. Returns all errors (CI gate)."""
    errors: list[str] = []
    floors: dict[int, Floor] = {}
    for fname in sorted(os.listdir(FLOORS_DIR)):
        if not fname.endswith(".yaml"):
            continue
        try:
            fl = _load_floor_file(os.path.join(FLOORS_DIR, fname))
        except Exception as e:  # noqa: BLE001 — collect, don't abort
            errors.append(str(e))
            continue
        if fl.floor in floors:
            errors.append(f"{fname}: duplicate floor {fl.floor}")
        floors[fl.floor] = fl
        # 025: floors 1-10 carry the archetype spread. Floors 11-100 are
        # still on one stat line per floor — see MUST_BE_DONE_LATER.md.
        if fl.floor <= 10:
            errors.extend(_archetype_errors(fl))
            errors.extend(_class_pool_errors(fl))
            # 030: every tuned floor owes the climber one voice at the
            # gate town. Floors 11-100 stay silent until their art pass.
            if fl.npc is None:
                errors.append(
                    f"floor {fl.floor}: missing npc block (030 — a voice "
                    "in every fields, floors 1-10)")
        # 008: floors ≥ 11 speak the full language — lore on every
        # encounter (the [i] dossier's one breath) and a 4-5 shelf.
        if fl.floor >= 11:
            if not 4 <= len(fl.encounters) <= 5:
                errors.append(
                    f"floor {fl.floor}: {len(fl.encounters)} encounters "
                    "— 008 wants 4-5")
            for e in fl.encounters:
                if not e.lore:
                    errors.append(
                        f"floor {fl.floor}/{e.id}: missing lore (008)")
            errors.extend(_class_pool_errors(fl))
    # band spread: 11-20, 21-30, … — only bands that exist in full
    for lo in range(11, 100, 10):
        band = [floors[n] for n in range(lo, lo + 10) if n in floors]
        if len(band) == 10:
            errors.extend(_band_spread_errors(band))
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
