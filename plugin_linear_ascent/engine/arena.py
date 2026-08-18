"""067 phase 2: the Arena — a RECORDER, not a second combat engine.

Combat resolves exactly as it always has (same rolls, same numbers,
same text). When the arena is on for this player and floor
(`labs.enabled(p, "arena", floor)`), the choke points of combat.py call
`record()` and this module turns the round into an ORDERED SCRIPT the
website's arena3d layer plays beat by beat: the player's turn, then the
creature's, each with the number that landed. `payload()` is what rides
`Scene.arena` (a top-level Scene key — old clients drop it).

Everything here is a no-op when the flag is off: `record` returns
before touching the encounter, `payload` returns None.
"""
from __future__ import annotations

from .. import economy
from . import labs, state

FEATURE = "arena"
FRAME_W, FRAME_H = 320, 300      # the arena's frame (the kill scene is 320×112)

# the tile glyph per option id (icons.py keys); attack_<slug> resolves
# by the weapon's path; anything unlisted falls back to a plain focus dot
_TILE_ICON = {
    "attack": None,          # by path
    "close_in": "t_speed",
    "open_distance": "back",
    "create_distance": "back",
    "run": "run",
    "stand": "shield",
    "shield_wall": "shield",
    "sleep_spell": "staff",
    "treeline_shot": "bow",
    "drink_tonic": "trollblood_tonic",
    "flare": "aether",
}
_PATH_ICON = {"blade": "sword", "bow": "bow", "staff": "staff"}
_PATH_LABEL = {"blade": "BLADE", "bow": "BOW", "staff": "MAGIC"}
_TILE_LABEL = {
    "attack": None,          # by path
    "close_in": "CLOSE IN",
    "open_distance": "DISTANCE",
    "create_distance": "DISTANCE",
    "run": "RUN",
    "stand": "STAND",
    "shield_wall": "WALL",
    "sleep_spell": "SLEEP",
    "treeline_shot": "TREELINE",
    "drink_tonic": "TONIC",
    "flare": "FLARE",
}


def enabled(p: dict, floor=None) -> bool:
    """On for this player, on THIS floor. `floor` may be a Floor, an int
    or None (→ read the encounter's floor)."""
    if floor is None:
        e = p.get("encounter") or {}
        floor = e.get("floor")
    if floor is None:
        return False
    fl = getattr(floor, "floor", floor)
    try:
        fl = int(fl)
    except (TypeError, ValueError):
        return False
    return labs.enabled(p, FEATURE, fl)


def begin(p: dict, option_id: str) -> None:
    """Start of a round: clear the script, snapshot the ground."""
    e = p.get("encounter")
    if not e or not enabled(p):
        return
    e["_arena"] = {"opt": option_id,
                   "range0": e.get("range", "close"),
                   "gap0": int(e.get("gap", 0) or 0),
                   "hp0": int(p["hp"]), "foe0": int(e["hp"]),
                   "ev": []}


def record(p: dict, **ev) -> None:
    """Append one beat. Cheap and silent when the arena is off or no
    round has begun (a scene built outside resolve_fight_action)."""
    e = p.get("encounter")
    if not e or not enabled(p):
        return
    a = e.get("_arena")
    if not isinstance(a, dict):
        return
    ev.setdefault("who", "me")
    ev.setdefault("kind", "note")
    a["ev"].append(ev)


# ── the words under the scene ────────────────────────────────────────

def _cap(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def _weapon_word(path: str) -> str:
    return {"blade": "blade", "bow": "bow", "staff": "magic"}.get(path, path)


def _text(ev: dict, foe: str, me: str) -> str:
    who, kind = ev.get("who"), ev.get("kind")
    if ev.get("text"):
        return ev["text"]
    if kind == "strike" and who == "me":
        w = _weapon_word(ev.get("path", "blade"))
        out = ev.get("outcome")
        if out == "miss":
            return (f"{me} misses the {w} attack because skill level is "
                    f"{ev.get('rank', 0)} of 10 (miss chance "
                    f"{ev.get('miss_pct', 0)}%).")
        if out == "glance":
            why = ev.get("why") or "its hide turns the blow"
            return f"{me}'s {w} attack lands for 0 — {why}."
        line = f"{me} hits with the {w} for {ev.get('dmg', 0)} damage"
        if ev.get("blocked"):
            line += f" ({ev['blocked']} taken by its DEF)"
        if ev.get("why"):
            line += f" — {ev['why']}"
        return line + "."
    if kind == "strike" and who == "foe":
        out = ev.get("outcome")
        if out == "dodged":
            return f"{foe} attacks — {me} dodges it (speed)."
        if out == "netted":
            return f"{foe} thrashes in the net — its turn is spent."
        if out == "veiled":
            return f"{foe} strikes where {me} was — the veil holds."
        if out == "none":
            return f"{foe} has no answer at this range."
        dmg, blocked = int(ev.get("dmg", 0)), int(ev.get("blocked", 0))
        if dmg <= 0:
            return (f"{foe} attacks for {ev.get('raw', 0)} — "
                    f"BLOCKED {blocked}: nothing gets through.")
        if blocked > 0:
            return (f"{foe} hits {me} for {dmg} damage — "
                    f"{blocked} blocked by DEF.")
        return f"{foe} hits {me} for {dmg} damage."
    if kind == "move" and who == "me":
        what = ev.get("what")
        gap = ev.get("gap")
        return {
            "close_in": f"{me} closes the gap.",
            "open": f"{me} steps back — {gap} length(s) between them.",
            "back": f"{me} gives ground on purpose — {gap} length(s) now.",
            "open_fail": f"{me} tries to open distance — no gap opens.",
            "run_ok": f"{me} breaks away.",
            "run_fail": f"{me} runs — the way out is cut off.",
            "stand": f"{me} braces behind the guard.",
            "wall": f"{me} raises the shield wall.",
        }.get(what, f"{me}: {what}.")
    if kind == "move" and who == "foe":
        what = ev.get("what")
        return {
            "close": f"{foe} closes the gap — it is on {me} now.",
            "advance": f"{foe} eats a length — {ev.get('gap')} between them.",
            "hold": f"{foe} comes on across open ground.",
        }.get(what, f"{foe}: {what}.")
    if kind == "die":
        return f"{foe} is defeated." if who == "foe" else f"{me} falls."
    return ev.get("text", "")


# ── the HUD facts ────────────────────────────────────────────────────

def _armoured(e: dict, prof: dict) -> bool:
    """The DEF badge: an armoured type, or a DEF that is high against
    its own bar (roy: 'if its def/hp is high then we say its armoured')."""
    if prof.get("type") == "armoured":
        return True
    hp_max = max(1, int(e.get("hp_max", 1)))
    return int(e.get("def", 0)) / hp_max >= 0.06


def _me(p: dict) -> dict:
    lead = p["gear"].get("weapon") or ""
    weapons = []
    for slug in ([lead] if lead else []) + [
            s for s in (p.get("held") or []) if s != lead]:
        g = economy.FORGE.get(slug)
        if not g:
            continue
        path = economy.PATH_OF_LINE.get(g.line, "blade")
        weapons.append({
            "slug": slug, "name": g.name, "path": path,
            "lead": slug == lead,
            "rank": int((p.get("training") or {}).get(path, 0)),
            "bonus": economy.honed_bonus(g.bonus, state.hone_level(p, "weapon"))
            if slug == lead else g.bonus,
            "broken": bool(state.is_broken(p, "weapon")) if slug == lead
            else False,
        })
    guard = {}
    for slot in ("shield", "armor", "shoes"):
        slug = p["gear"].get(slot)
        g = economy.FORGE.get(slug or "")
        if g:
            guard[slot] = {"slug": slug, "name": g.name,
                           "bonus": state.gear_bonus(p, slot),
                           "broken": bool(state.is_broken(p, slot))}
    lvl = int(p.get("level", 1))
    return {
        "hp": max(0, int(p["hp"])), "hp_max": state.max_hp(p),
        "atk": state.atk(p), "atk_base": economy.player_atk(lvl, 0),
        "def": state.dfs(p), "def_base": economy.player_def(lvl, 0, 0),
        "spd": economy.player_speed(p),
        "race": p.get("race") or "", "line": _line_of(p),
        "name": p.get("name") or "You",
        "weapons": weapons, "guard": guard,
    }


def _line_of(p: dict) -> str:
    from .combat import _damage_type, _LINE_OF_DTYPE
    return _LINE_OF_DTYPE.get(_damage_type(p), "blade")


def _foe(p: dict) -> dict:
    from .combat import _foe_id, _profile
    e = p["encounter"]
    prof = _profile(p)
    t = prof.get("type", "plain")
    return {
        "id": _foe_id(e), "name": e["name"],
        "hp": max(0, int(e["hp"])), "hp_max": int(e["hp_max"]),
        "atk": int(e["atk"]), "def": int(e["def"]),
        "spd": int(prof.get("speed", economy.SPEED_NORMAL)),
        "type": t, "flying": bool(prof.get("flying")),
        "armoured": _armoured(e, prof),
        # magic resistance as the share of a staff blow the sign eats
        "resist_pct": (round((1 - economy.TYPE_MULT[t]["staff"]) * 100)
                       if t == "magic_resist" else 0),
        "bulwark": bool(prof.get("bulwark")),
        "breed": e.get("breed", ""), "specimen": e.get("specimen", ""),
        "kind": e.get("kind", "wilds"),
    }


# 067 phase 5: the tile shows the ITEM's own face — the charm the
# use_ row spends, the arrows the nock_ row nocks; spells and the
# treeline shot ride the weapon that casts/looses them.
_USE_ITEM = {
    "throw_net": "entangling_net", "use_hook": "sky_hook",
    "use_strip": "strip_potion", "use_curse": "curse_scroll",
    "use_polymorph": "polymorph_dust", "use_veil": "veil_draught",
    "use_apple": "golden_apple", "use_severing": "severing_word",
    "drink_tonic": "trollblood_tonic",
}
_WEAPON_ROWS = ("sleep_spell", "treeline_shot", "shield_wall", "stand")


def tile(option_id: str, p: dict) -> dict:
    """The tile face for an option — icon key + short label + the art
    slug (067 phase 5: the render draws the item's own 30×48 face when
    it ships; the icon key is the fallback glyph). attack rows read the
    weapon; everything else the table."""
    lead = (p.get("gear") or {}).get("weapon") or ""
    if option_id == "attack":
        from .combat import _train_path
        path = _train_path(p)
        return {"icon": _PATH_ICON.get(path, "sword"),
                "label": _PATH_LABEL.get(path, "ATTACK"), "art": lead}
    if option_id.startswith("attack_"):
        slug = option_id.removeprefix("attack_")
        g = economy.FORGE.get(slug)
        path = economy.PATH_OF_LINE.get(g.line, "blade") if g else "blade"
        return {"icon": _PATH_ICON.get(path, "sword"),
                "label": _PATH_LABEL.get(path, "ATTACK"), "art": slug}
    if option_id.startswith("nock_") or option_id.startswith("drink_"):
        slug = option_id.split("_", 1)[1]
        slug = _USE_ITEM.get(option_id, slug)
        return {"icon": slug, "label": slug.replace("_", " ").upper()[:12],
                "art": slug}
    if option_id in _USE_ITEM:
        slug = _USE_ITEM[option_id]
        return {"icon": slug,
                "label": _TILE_LABEL.get(option_id)
                or slug.replace("_", " ").upper()[:12], "art": slug}
    if option_id.startswith("use_"):
        slug = option_id.split("_", 1)[1]
        return {"icon": slug, "label": slug.replace("_", " ").upper()[:12],
                "art": slug}
    art = ""
    if option_id in _WEAPON_ROWS:
        art = (p.get("gear") or {}).get("shield") or "" \
            if option_id in ("shield_wall", "stand") else lead
    return {"icon": _TILE_ICON.get(option_id) or "focus",
            "label": _TILE_LABEL.get(option_id) or
            option_id.replace("_", " ").upper()[:12], "art": art}


def _synth_move(a: dict, e: dict, p: dict) -> dict | None:
    """The player's turn when no strike was recorded — the option says
    what was tried; the ground before/after says what came of it."""
    opt = a.get("opt", "")
    r0, g0 = a.get("range0"), a.get("gap0", 0)
    r1, g1 = e.get("range", "close"), int(e.get("gap", 0) or 0)
    if opt in ("close_in", "attack") and r0 == "at_range" and r1 == "close":
        return {"who": "me", "kind": "move", "what": "close_in", "gap": 0}
    if opt == "open_distance":
        if r1 == "at_range" and r0 != "at_range":
            return {"who": "me", "kind": "move", "what": "open", "gap": g1}
        return {"who": "me", "kind": "move", "what": "open_fail", "gap": g1}
    if opt == "create_distance":
        if g1 > g0:
            return {"who": "me", "kind": "move", "what": "back", "gap": g1}
        return None
    if opt == "run":
        return {"who": "me", "kind": "move", "what": "run_fail", "gap": g1}
    if opt == "stand":
        return {"who": "me", "kind": "move", "what": "stand", "gap": g1}
    if opt == "shield_wall":
        return {"who": "me", "kind": "move", "what": "wall", "gap": g1}
    return None


def payload(p: dict, floor, phase: str = "round",
            options=(), note: str = "") -> dict | None:
    """What rides Scene.arena. Called by fight_scene / _victory / _death /
    the run-away card while `p["encounter"]` still holds the foe."""
    e = p.get("encounter")
    if not e or not enabled(p, floor):
        return None
    a = e.pop("_arena", None)
    events: list[dict] = []
    start = None
    if isinstance(a, dict):
        start = {"me_hp": int(a.get("hp0", p.get("hp", 0)) or 0),
                 "foe_hp": int(a.get("foe0", e.get("hp", 0)) or 0),
                 "range": a.get("range0", "close"),
                 "gap": int(a.get("gap0", 0) or 0)}
        events = list(a.get("ev") or [])
        first_me = next((x for x in events if x.get("who") == "me"), None)
        if first_me is None:
            mv = _synth_move(a, e, p)
            if mv:
                events.insert(0, mv)
        elif first_me.get("kind") == "strike" and a.get("opt") == "run":
            pass
    if phase == "victory":
        events.append({"who": "foe", "kind": "die"})
    elif phase == "death":
        events.append({"who": "me", "kind": "die"})
    elif phase == "fled":
        events.insert(0, {"who": "me", "kind": "move", "what": "run_ok"})
    foe, me = _foe(p), _me(p)
    for ev in events:
        ev["text"] = _text(ev, foe["name"], me["name"])
    return {
        "v": 1,
        "w": FRAME_W, "h": FRAME_H,
        "floor": int(getattr(floor, "floor", floor) or 0),
        "phase": phase,
        "foe": foe,
        "me": me,
        "range": {"state": e.get("range", "close"),
                  "gap": int(e.get("gap", 0) or 0)
                  if e.get("range") == "at_range" else 0},
        "start": start,
        "events": events,
        "log": [ev["text"] for ev in events if ev.get("text")],
        "note": note,
        "tiles": {o.id: tile(o.id, p) for o in options},
    }
