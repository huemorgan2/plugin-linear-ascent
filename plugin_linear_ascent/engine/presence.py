"""042: the presence layer — who stands where you stand.

worldd injects `doc["_world"]["rooms"]`: a dict keyed by ROOM KEY, each
value a list of player tiles. The engine resolves its own room AFTER the
move (the injection ran before the act, but a walk only changes which
key is read — the payload carries every room on the viewer's floor plus
the town). Local solo mode has no rooms and the grid simply stays off.

Room keys (the worldd builder mirrors these exactly):
- town rooms: the location string verbatim ("town", "forge", "vault"…)
- floor rooms: "gate_town:12", "warden_keep:12", "boss_keep:12",
  "memorial:12" — scoped, a camp on 3 is not a camp on 9
- the banner hall: "hall:<faction>" — members only
- sleepers are placed in the room they sleep in ("lodge" or "fields"),
  never in a "sleeping" room of their own

Tile entries ride the wire as {opt, name, level, race, armor, sleeping,
gold, energy} — opt is "pv:<name>", the click that opens the profile.
"""

from __future__ import annotations

FLOOR_ROOMS = ("gate_town", "warden_keep", "boss_keep", "memorial")
ROOM_CAP = 21                  # 3 rows of 7 — the first batch; the card
                               # says MORE N PLAYERS for the rest

# The grid's header names the room. Town rooms the plain way, floor
# rooms by their floor number; anything unlisted falls back to the
# location word itself.
_ROOM_NAMES = {"town": "THE SQUARE", "forge": "THE FORGE",
               "vault": "THE VAULT", "school": "THE SCHOOL",
               "lodge": "THE LODGE", "fields": "THE FIELDS",
               "arcanum": "THE ARCANUM", "apothecary": "THE APOTHECARY",
               "board": "THE CONTRACT BOARD", "pawn": "THE PAWN SHOP",
               "relay": "THE RELAY OFFICE", "stone": "THE STONE",
               "guildhall": "THE GUILDHALL", "hall": "THE BANNER HALL"}


def room_title(p: dict) -> str:
    """'PLAYERS ON FLOOR 12' out in the tower, 'PLAYERS NOW IN THE
    FORGE' around town."""
    key = room_key(p)
    if not key:
        return "PLAYERS HERE"
    loc = key.split(":", 1)[0]
    if loc in FLOOR_ROOMS:
        return f"PLAYERS ON FLOOR {max(1, int(p.get('floor') or 1))}"
    name = _ROOM_NAMES.get(loc, f"THE {loc.upper()}")
    return f"PLAYERS NOW IN {name}"


def room_key(p: dict) -> str:
    """The viewer's room key, '' when no room holds them."""
    if p.get("stage") != "playing":
        return ""
    loc = str(p.get("location") or "")
    if not loc:
        return ""
    if loc == "sleeping":
        loc = str((p.get("sleeping") or {}).get("where") or "lodge")
    if loc in FLOOR_ROOMS:
        return f"{loc}:{max(1, int(p.get('floor') or 1))}"
    if loc == "hall":
        g = str(p.get("guild") or "")
        return f"hall:{g}" if g else ""
    return loc


def players_here(p: dict) -> list[dict]:
    """The grid for the viewer's current room — self excluded, awake
    first, then level desc, capped at ROOM_CAP."""
    w = p.get("_world") or {}
    rooms = w.get("rooms")
    if not isinstance(rooms, dict):
        return []
    key = room_key(p)
    if not key:
        return []
    me = p.get("name")
    out = []
    for t in rooms.get(key) or []:
        if not isinstance(t, dict) or not t.get("name"):
            continue
        if t["name"] == me:
            continue
        tile = dict(t)
        tile.setdefault("opt", f"pv:{tile['name']}")
        out.append(tile)
    out.sort(key=lambda t: (bool(t.get("sleeping")),
                            -int(t.get("level", 1) or 1),
                            str(t.get("name", ""))))
    return out[:ROOM_CAP]


def mount(p: dict, scene) -> None:
    """Hang the grid under the options of an ordinary room card. Scenes
    that brought their own grid (warden boards, memorials) keep it;
    fights and event cards stay clean."""
    if scene.players_here:
        return
    if p.get("stage") != "playing" or p.get("encounter"):
        return
    if scene.enemy or scene.event_kind:
        return
    tiles = players_here(p)
    if tiles:
        scene.players_here = tiles
        scene.players_title = room_title(p)
        # the TRUE room population, shipped beside the capped tiles —
        # the card turns the difference into MORE N PLAYERS
        counts = (p.get("_world") or {}).get("rooms_n") or {}
        n = int(counts.get(room_key(p)) or 0)
        # counts include the viewer; the grid never does
        scene.players_total = max(len(tiles), n - 1)


def valid_opts(scene) -> set[str]:
    """The grid's click targets — unioned into apply_choice's valid set."""
    return {str(t.get("opt", "")) for t in (scene.players_here or [])
            if t.get("opt")}
