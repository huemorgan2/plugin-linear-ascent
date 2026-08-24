"""071: Labs figure3d — the 3D climber payload.

Isolation: this module only builds a dict the website's figure3d.js
reads. Off (or unknown) = None. No combat, no economy change. Dropping
the Labs feature deletes this file and the figure3d/ folder.
"""
from __future__ import annotations

from .. import economy
from . import labs

KEY = "figure3d"
_PX = {"giant": (140, 260)}
_DEFAULT_PX = (100, 200)
_RACES = frozenset({"human", "elf", "giant"})


def _path_of(slug: str) -> str:
    g = economy.FORGE.get(slug)
    if g and g.slot == "weapon":
        return economy.PATH_OF_LINE.get(g.line or "", "blade")
    if g and g.slot == "shield":
        return "focus" if g.line == "sorcerer" else "shield"
    if g:
        return g.slot
    if slug == "luck_charm":
        return "charm"
    if slug in economy.CHARM_KINDS:
        return "potion"
    return "item"


def sheet(p: dict) -> dict | None:
    """3D kit from worn gear. No labs gate — the viewer decides."""
    if p.get("stage") != "playing":
        return None
    race = p.get("race") or "human"
    if race not in _RACES:
        race = "human"
    worn: dict[str, str | None] = {}
    paths: dict[str, str] = {}
    for sl in economy.SLOTS:
        slug = economy.slot_item(p, sl.key)
        worn[sl.key] = slug
        if slug:
            paths[slug] = _path_of(slug)
    lead = (p.get("gear") or {}).get("weapon") or worn.get("weapon")
    w, h = _PX.get(race, _DEFAULT_PX)
    return {
        "v": 1,
        "race": race,
        "lead": lead,
        "worn": worn,
        "paths": paths,
        "px": [w, h],
    }


def payload(p: dict) -> dict | None:
    if not labs.enabled(p, KEY):
        return None
    return sheet(p)
