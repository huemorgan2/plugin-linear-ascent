"""The state machine — every flow gated here, steering hints on refusal.

`current_scene(p)` is idempotent (safe to call anytime).
`apply_choice(p, option_id, text)` validates the option against the
current scene and dispatches. The agent never free-forms game state.
"""

from __future__ import annotations

import datetime as dt

from .. import economy
from ..content import schema
from . import combat, state
from .scene import Meters, Option, Scene


# ── Entry points ─────────────────────────────────────────────────────────

def _stamp(p: dict, scene: Scene) -> Scene:
    """scene_id = the act counter. Every choice bumps it, reads reuse it —
    /pane/peek compares ids, so a chat-driven act refreshes the pane
    while idempotent reads never do. 014: the pack strip rides every
    playing scene the same way."""
    scene.scene_id = f"s{p.get('act_seq', 0)}"
    scene.inventory = _pack_strip(p)
    return scene


def _pack_strip(p: dict) -> list[dict]:
    """014: what the player carries — equipped gear first (hone level in
    the name), then pack items. Rendered under the meters as 1-bit
    icons; empty before the character exists."""
    if p.get("stage") != "playing":
        return []
    strip: list[dict] = []
    for slot in ("weapon", "shield", "armor", "shoes"):
        slug = (p.get("gear") or {}).get(slot)
        g = economy.FORGE.get(slug) if slug else None
        if not g:
            continue
        hone = (p.get("hone") or {}).get(slot, 0)
        cell = {"slug": slug, "kind": slot, "count": 1,
                "equipped": True,
                "name": g.name + (f" +{hone}" if hone else "")}
        # 005: paid gear carries its wear onto the strip — the bar and
        # the hover both read from this one number.
        left = (p.get("durability") or {}).get(slot)
        if left is not None and g.price > 0:
            pool = economy.item_pool(g)
            cell["dur"] = max(0.0, min(1.0, left / pool)) if pool else 1.0
        strip.append(cell)
    pack = p.get("inventory") or {}
    order = sorted(pack.items(),
                   key=lambda kv: (kv[0] not in economy.APOTHECARY, kv[0]))
    for slug, count in order:
        if count <= 0:
            continue
        if slug in economy.APOTHECARY:
            name, kind = economy.APOTHECARY[slug].name, "item"
        elif slug in economy.RELICS:
            name, kind = economy.RELICS[slug].name, "relic"
        elif slug in economy.FORGE:
            g = economy.FORGE[slug]
            name, kind = g.name, g.slot
        else:
            name, kind = slug.replace("_", " "), "item"
        strip.append({"slug": slug, "kind": kind, "count": int(count),
                      "name": name})
    return strip


def current_scene(p: dict) -> Scene:
    state.ensure_current(p)
    state.touch_daily(p)
    ev = _pop_pending_event(p)
    if ev is not None:
        return _stamp(p, ev)
    return _stamp(p, _build_scene(p))


def apply_choice(p: dict, option_id: str, text: str = "") -> Scene:
    from . import social
    state.ensure_current(p)
    state.touch_daily(p)
    p["last_seen"] = state.now().isoformat()
    p["act_seq"] = p.get("act_seq", 0) + 1

    if p["stage"] == "creation_name" and text and not option_id:
        return _stamp(p, _creation_set_name(p, text))
    if p.get("compose_to") and text and not option_id:
        return _stamp(p, social.relay_compose(p, text))
    if p.get("founding_guild") and text and not option_id:
        return _stamp(p, social.guildhall_found(p, text))
    if p.get("faction_donating") and text and not option_id:
        return _stamp(p, social.guildhall_donate(p, text))

    scene = _build_scene(p)
    valid = {o.id for o in scene.options}
    if option_id not in valid:
        # numbered fallback: "1".."9" resolve positionally
        if option_id.isdigit() and 1 <= int(option_id) <= len(scene.options):
            option_id = scene.options[int(option_id) - 1].id
        elif option_id == "attack" and "close_in" in valid:
            # 002: players and the sidekick say "attack" by habit — at
            # range, for steel, that means crossing the ground.
            option_id = "close_in"
        else:
            scene.shard_note = (
                f"That isn't one of the paths in front of us. "
                f"Pick one of: {', '.join(sorted(valid))}.")
            return _stamp(p, scene)
    return _stamp(p, _dispatch(p, option_id))


# ── Pending events (presents, death reports — delivered next session) ───

def _pop_pending_event(p: dict) -> Scene | None:
    if p.get("encounter"):
        return None                      # never interrupt a fight
    ev = _maybe_news(p)
    if ev:
        return ev
    ev = _maybe_present(p)
    if ev:
        return ev
    q = p.get("pending_events") or []
    if q:
        d = q.pop(0)
        p["pending_events"] = q
        return Scene.from_dict(d)
    return None


# ── World news — the Morning Crier (007 §4) ──────────────────────────────

def _maybe_news(p: dict) -> Scene | None:
    """Once per world day, in world mode only: what happened while you
    were gone. Data comes from worldd's injection — never invented."""
    if p["stage"] != "playing":
        return None
    w = p.get("_world") or {}
    if "census" not in w:
        return None
    day = state.world_day()
    if p.get("news_day", -1) >= day:
        return None
    p["news_day"] = day
    return _news_scene(p, w, day)


def _news_scene(p: dict, w: dict, day: int) -> Scene:
    frontier = int(w.get("frontier", 1))
    census = w.get("census") or {}
    by_floor = {int(k): int(v)
                for k, v in (census.get("by_floor") or {}).items()}
    total = int(census.get("total", 0))
    my_floor = p["floor"] if p["floor"] > 0 else frontier
    lines = [
        f"· {total} climber{'s' if total != 1 else ''} on the "
        f"Ascent — {by_floor.get(frontier, 0)} at the frontier "
        f"(floor {frontier}), {by_floor.get(1, 0)} down at floor 1, "
        f"{by_floor.get(my_floor, 0)} on floor {my_floor} with you.",
    ]
    wd = w.get("warden")
    if wd and wd.get("hp_max"):
        pct = max(0, round(100 * int(wd["hp"]) / int(wd["hp_max"])))
        fl = schema.get_floor(int(wd["floor"]))
        blades = len(wd.get("strikers") or [])
        lines.append(
            f"· {fl.warden_name} holds floor {wd['floor']} at {pct}% — "
            + (f"{blades} blade{'s' if blades != 1 else ''} against it."
               if blades else "no blade against it yet."))
    gossip = w.get("gossip") or []
    if gossip:
        lines.append(f"heard around floor {my_floor}:")
        lines += [f"· {g}" for g in gossip[:3]]
    else:
        lines.append(f"· floor {my_floor} was quiet — no news is its "
                     "own kind of news.")
    return Scene(
        eyebrow="ROOTHOLLOW · THE MORNING CRIER",
        headline=f"Day {day} on the Ascent — the frontier stands at "
                 f"floor {frontier}",
        support="What moved while you were away.",
        shard_note=_news_advice(p, w, frontier, wd),
        body_lines=lines,
        options=[Option("town", "Into the square")],
        meters=combat.meters(p),
        event_kind="news",
        banner="roothollow",
    )


def _news_advice(p: dict, w: dict, frontier: int, wd: dict | None) -> str:
    """Where to work today for the fastest climb — honest engine math."""
    req = economy.floor_entry_player_level(frontier)
    if p["level"] < req:
        best = max(1, min(p["unlocked_floor"], p["level"] + 10))
        return (f"Floor {frontier} wants level {req} legs — you are "
                f"level {p['level']}. Fastest climb today: hunt floor "
                f"{best}, full pay, no fade.")
    if wd and wd.get("hp_max"):
        pct = max(0, round(100 * int(wd["hp"]) / int(wd["hp_max"])))
        if pct < 100:
            return (f"The Warden of floor {frontier} is already wounded "
                    f"({pct}%). Strikes at its keep are the fastest way "
                    f"to open floor {frontier + 1} — for everyone.")
        return (f"You are fit for the frontier. Hunt floor {frontier} "
                f"and put strikes into its Warden — the floor above "
                "opens for the whole world.")
    if frontier in economy.MILESTONES:
        ms = economy.MILESTONES[frontier]
        return (f"Floor {frontier} is a milestone keep — {ms.name} falls "
                f"to a war party of {ms.quorum}. Pledge your blade and "
                "rally others.")
    return (f"Hunt near the frontier (floor {frontier}) — that is where "
            "the pay and the progress are.")


def _maybe_present(p: dict) -> Scene | None:
    if p["stage"] != "playing":
        return None
    last = dt.datetime.fromisoformat(p["last_seen"])
    away_h = (state.now() - last).total_seconds() / 3600
    p["last_seen"] = state.now().isoformat()
    if away_h < economy.PRESENT_AWAY_HOURS:
        return None
    # 009: luck is a DAY now (charm-bought) — the racial bonus retired
    # with the halfling listing.
    lucky = p["flags"].get("luck_day") == state.world_day()
    table = list(economy.PRESENT_TABLE)
    if lucky:
        table = [(w + (5 if k in ("jackpot", "gold") else 0), k)
                 for w, k in table]
    kind = state.rng_pick(p, table)
    lines: list[str] = []
    if kind == "gold":
        amt = 50 * p["level"]
        p["gold"] += amt
        lines.append(f"+ ◈ {amt} in a knotted purse")
    elif kind == "potion":
        p["inventory"]["medgel"] = p["inventory"].get("medgel", 0) + 1
        lines.append("▪ a medgel, still sealed")
    elif kind == "full_energy":
        state.gain_energy(p, 99)
        lines.append("▪ your limbs hum — energy restored")
    elif kind == "rumor":
        p["flags"]["rumor_day"] = state.world_day()
        lines.append("▪ a rumor: your next fight starts in your favor")
    elif kind == "repair_token":
        p["inventory"]["repair_token"] = p["inventory"].get("repair_token", 0) + 1
        lines.append("▪ an armor-repair token")
    else:  # jackpot
        gain = min(p["bank"], 1000 * p["level"])
        if gain > 0:
            p["bank"] += gain
            lines.append(f"◈ the Vault matched your savings: +{gain} banked")
        else:
            p["inventory"]["luck_charm"] = p["inventory"].get("luck_charm", 0) + 1
            lines.append("▪ a luck charm, warm to the touch")
    return Scene(
        eyebrow="ROOTHOLLOW · YOUR DOORSTEP",
        headline="Something waited for you",
        support="Come back after a day away and the village leaves you things.",
        shard_note="I watched them leave it. No tricks this time.",
        body_lines=lines,
        options=[Option("town", "Take it and head into the square")],
        meters=combat.meters(p),
        event_kind="present",
        banner="present",
    )


# ── Scene builder (by stage/location) ────────────────────────────────────

def _build_scene(p: dict) -> Scene:
    if p["stage"] == "intro":
        return _intro_scene(p)
    if p["stage"] == "creation_race":
        return _creation_race_scene(p)
    if p["stage"] == "creation_class":
        return _creation_class_scene(p)
    if p["stage"] == "creation_name":
        return _creation_name_scene(p)
    if p.get("encounter"):
        fl = schema.get_floor(p["encounter"]["floor"])
        return combat.fight_scene(p, fl)
    from . import social
    loc = p["location"]
    if loc == "muster":
        # The Muster Roll is retired; saved docs may still stand there.
        p["location"] = loc = "town"
    builders = {
        "town": _town_scene, "forge": _forge_scene,
        "arcanum": _arcanum_scene, "medlab": _medlab_scene,
        "lodge": _lodge_scene, "vault": _vault_scene, "pawn": _pawn_scene,
        "stone": _stone_scene, "gate": _gate_scene,
        "gate_town": _gate_town_scene,
        "relay": social.relay_scene, "fields": social.fields_scene,
        "guildhall": social.guildhall_scene, "grants": social.grant_scene,
        "boss_keep": _boss_keep_scene,
        "warden_keep": _warden_keep_scene,
    }
    return builders.get(loc, _town_scene)(p)


def _boss_keep_scene(p: dict) -> Scene:
    from . import social
    fl = schema.get_floor(max(1, p["floor"]))
    return social.boss_scene(p, fl)


def _warden_keep_scene(p: dict) -> Scene:
    from . import social
    fl = schema.get_floor(max(1, p["floor"]))
    return social.warden_scene(p, fl)


def _dispatch(p: dict, oid: str) -> Scene:
    if p["stage"] == "intro":
        # 016: Next steps through the movie; the title card's "begin"
        # (past the last story beat) walks to the tower gate.
        step = p.get("intro_step", 0)
        if step < len(_INTRO_MOVIE):
            p["intro_step"] = step + 1
            return _intro_scene(p)
        p["stage"] = "creation_race"
        return _creation_race_scene(p)
    if p["stage"] == "creation_race":
        return _creation_pick_race(p, oid)
    if p["stage"] == "creation_class":
        return _creation_pick_class(p, oid)
    if p["stage"] == "creation_name":
        return _creation_name_scene(p)     # name comes as text
    if p.get("encounter"):
        fl = schema.get_floor(p["encounter"]["floor"])
        return combat.resolve_fight_action(p, fl, oid)
    return _dispatch_location(p, oid)


# ── Creation ─────────────────────────────────────────────────────────────

# 016: the intro movie — one scene per story beat, comic-book pacing.
# Each step is (fx slug, headline, body lines); the card/pane typewriter
# does the "text written gradually" part, the single Next option does the
# rest. There is deliberately NO skip — every climber sees the story once.
# fx slugs with split art (intro+loop gifs) settle from their action beat
# into an ambient loop; the renderer handles the swap.
_INTRO_MOVIE: list[tuple[str, str, list[str]]] = [
    ("intro_aldervale", "The world that was", [
        "Aldervale was whole once — and it was never primitive.",
        "Human river-ports under blinking signal towers. Elven woods "
        "lit from within. Dwarven forges splitting atoms beneath the "
        "mountains.",
        "Magic and machine were one craft there. They called it aether.",
    ]),
    ("intro_theft", "The theft", [
        "Then Vharuk, the Demon King, rose from below.",
        "He did not burn the world. He stole it — realm by realm, torn "
        "out of the ground with everyone still on it.",
    ]),
    ("intro_tower", "The Ascent", [
        "He welded what he took into a tower of a hundred floors — "
        "black iron, grav-engines, chains of aether.",
        "Every floor is a captured realm. The people below gave it the "
        "only name that fits: the Ascent.",
    ]),
    ("intro_warden", "The Wardens", [
        "On every floor, a Warden holds the lift to the next — half "
        "beast, half war-machine.",
        "And on the hundredth floor, in a citadel half throne room, "
        "half reactor core, the Demon King sits with the whole world "
        "stacked beneath him.",
    ]),
    ("intro_refugee", "You", [
        "You were on one of those floors.",
        "Your home is up there now — locked behind a hundred Wardens. "
        "You walked out of the wreckage with a rusted shiv and fifty "
        "coins.",
        "That makes you what everyone here is: a refugee. And a climber.",
    ]),
    ("intro_roothollow", "Roothollow", [
        "At the tower's foot stands the last free settlement: Roothollow.",
        "Tarps over titanium. A plasma forge next to a horse trough. "
        "Refugees of every stolen realm, all of them climbers now.",
        "Every climb starts here — and every dead climber wakes here. "
        "The tower does not get to keep you.",
    ]),
    ("intro_stone", "No one climbs alone", [
        "When a Warden falls, the lift opens for everyone — every "
        "climber, everywhere.",
        "And the names of those who did it are cut into the Stone of "
        "the Climb, lit from within by aether.",
    ]),
    ("intro_shard", "The shardmind", [
        "At the gate, a shard of old Aldervale will choose you — a "
        "machine spirit that remembers the world as it was.",
        "It will scout ahead of you, carry what you cannot lose, and "
        "drag you back from death.",
        "It is speaking to you right now.",
    ]),
    ("intro_muster", "The muster", [
        "The great Wardens do not fall to one blade.",
        "Climbers pledge at the keep, and when enough have gathered, "
        "they break it — together. Floor by floor. Warden by Warden. "
        "All the way to the throne.",
    ]),
]

_ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"]


def _intro_scene(p: dict) -> Scene:
    step = p.get("intro_step", 0)
    if step < len(_INTRO_MOVIE):
        fx, headline, body = _INTRO_MOVIE[step]
        return Scene(
            eyebrow=f"THE STORY SO FAR · {_ROMAN[step]}",
            headline=headline,
            body_lines=body,
            options=[Option("next", "Next")],
            fx=fx,
        )
    return Scene(
        eyebrow="LINEAR ASCENT",
        headline="Climb the Ascent. Cast down the Demon King.",
        support="One hundred floors between Roothollow and the throne.",
        options=[Option("begin", "Walk to the tower gate")],
        banner="title",
        fx="ascent_title",
    )


def _creation_race_scene(p: dict) -> Scene:
    return Scene(
        eyebrow="THE TOWER GATE · FIRST LIGHT",
        headline="A shard of old Aldervale chooses you",
        support="Every climber is bonded to a shardmind. Yours just woke up.",
        shard_note="I remember this gate when it was a mountain. Tell me "
                   "what you are, refugee.",
        body_lines=["The registrar's slate wants your line first."],
        options=[Option(r, r.capitalize(), economy.RACES[r].split(":")[0])
                 for r in economy.RACES],
        banner="gate",
    )


def _creation_pick_race(p: dict, oid: str) -> Scene:
    p["race"] = oid
    p["stage"] = "creation_class"
    return _creation_class_scene(p)


def _creation_class_scene(p: dict) -> Scene:
    return Scene(
        eyebrow="THE TOWER GATE · REGISTRAR",
        headline=f"A {p['race']} — and how do you fight?",
        support="Class shapes which options appear when it matters.",
        options=[Option(c, c.capitalize(), economy.CLASSES[c].split(":")[0])
                 for c in economy.CLASSES],
    )


def _creation_pick_class(p: dict, oid: str) -> Scene:
    p["clazz"] = oid
    # 017 §1: the gate issues the weapon of your calling — warriors a
    # rusted sword, archers a basic bow (arrows never run out),
    # sorcerers a worn staff. It never breaks and is never lost.
    p["gear"]["weapon"] = economy.class_starter(oid).slug
    p["stage"] = "creation_name"
    return _creation_name_scene(p)


def _creation_name_scene(p: dict) -> Scene:
    return Scene(
        eyebrow="THE TOWER GATE · REGISTRAR",
        headline="Your name, for the Stone",
        support="Say it in chat — two to twenty-four letters the granite "
                "can hold.",
        shard_note="Choose one you'd want carved where everyone reads it.",
        options=[],
        awaits_text="the character's name",
    )


def _creation_set_name(p: dict, text: str) -> Scene:
    name = text.strip()
    if not (2 <= len(name) <= 24):
        s = _creation_name_scene(p)
        s.shard_note = "Two to twenty-four letters. The mason charges by " \
                       "the stroke."
        return s
    p["name"] = name
    p["stage"] = "playing"
    p["location"] = "town"
    s = _town_scene(p)
    s.headline = f"Welcome to Roothollow, {name}"
    s.support = ("Tarps over titanium, a plasma forge next to a horse "
                 "trough. Home.")
    s.shard_note = ("We carry ◈ 50 and a rusted shiv — the Forge's cheapest "
                    "real blade wants ◈ 250. The tower gate first: hunt "
                    "floor 1 until steel is affordable.")
    return s


# ── Roothollow ───────────────────────────────────────────────────────────

def _town_scene(p: dict) -> Scene:
    w = p.get("_world") or {}
    lines = []
    for h in (w.get("happenings") or [])[:5]:
        lines.append(f"· {h}")
    # 007 town readability: the gate leads — leaving town is THE verb —
    # and every not-yet area reads its unlock level from the square
    # (the Arcanum set the pattern in 004).
    opts = [
        Option("gate", "The Tower Gate", "leave town and climb"),
        Option("forge", "The Forge", "gear"),
        Option("arcanum", "The Arcanum",
               "mage gear" if p["level"] >= economy.ARCANUM_LEVEL
               else f"🔒 level {economy.ARCANUM_LEVEL}"),
        Option("medlab", "Apothecary & Medlab", "potions"),
        Option("lodge", "The Lodge",
               f"◈ {economy.LODGE_PRICE_PER_LEVEL * p['level']}/night"),
        Option("vault", "The Vault", "bank"),
        Option("pawn", "Pawn shop", "sell"),
        # 012: the Guildhall is core — training (buying levels) lives
        # there, so it must exist even without a connected world.
        Option("guildhall", "The Guildhall",
               p.get("guild") or "training"),
        Option("stone", "Stone of the Climb", "news"),
    ]
    if w:
        inbox = w.get("inbox_count", 0)
        opts.append(Option(
            "relay", "The Relay Office",
            (f"{inbox} letter{'s' if inbox != 1 else ''}" if inbox
             else "post") if p["level"] >= economy.RELAY_LEVEL
            else f"🔒 level {economy.RELAY_LEVEL}"))
        opts.append(Option(
            "fields", "The fields",
            "pvp" if p["level"] >= economy.FIELDS_LEVEL
            else f"🔒 level {economy.FIELDS_LEVEL}"))
    return Scene(
        eyebrow="ROOTHOLLOW · THE SQUARE",
        headline=f"Roothollow — floor {max(1, p['unlocked_floor'])} is the "
                 "frontier",
        support="The last free settlement. Everything starts and restarts here.",
        body_lines=lines,
        options=opts,
        meters=combat.meters(p),
        banner="roothollow",
    )


def _dispatch_location(p: dict, oid: str) -> Scene:
    from . import social
    loc = p["location"]

    # global navigation
    if oid == "town":
        p["location"] = "town"
        p["floor"] = 0
        return _town_scene(p)
    town_menus = ("forge", "arcanum", "medlab", "lodge", "vault", "pawn",
                  "stone", "gate", "relay", "fields", "guildhall")
    if loc == "town" and oid in town_menus:
        if oid == "arcanum" and p["level"] < economy.ARCANUM_LEVEL:
            s = _town_scene(p)
            s.shard_note = (
                "The Arcanum's door reads the hand on it — it wants "
                f"level {economy.ARCANUM_LEVEL}. Climb first; the "
                "star-charts will keep.")
            return s
        # 007: the other locked doors follow the Arcanum's grammar —
        # a level, a reason, no scene change.
        if oid == "relay" and p["level"] < economy.RELAY_LEVEL:
            s = _town_scene(p)
            s.shard_note = (
                "The Relay clerk sorts post for names the Stone knows — "
                f"level {economy.RELAY_LEVEL} first. Letters keep.")
            return s
        if oid == "fields" and p["level"] < economy.FIELDS_LEVEL:
            s = _town_scene(p)
            s.shard_note = (
                "The fields take climbers who can take a hit back — "
                f"level {economy.FIELDS_LEVEL}. The tower first.")
            return s
        p["location"] = oid
        return _build_scene(p)
    if oid == "back":
        p["location"] = "town" if loc in town_menus + ("grants",) \
            else p["location"]
        return _build_scene(p)
    if oid == "vault" and loc == "grants":
        p["location"] = "vault"
        return _vault_scene(p)
    if oid == "grants" and loc in ("vault", "grants"):
        p["location"] = "grants"
        return social.grant_scene(p)

    if loc == "forge":
        return _forge_buy(p, oid)
    if loc == "arcanum":
        return _arcanum_buy(p, oid)
    if loc == "medlab":
        return _medlab_buy(p, oid)
    if loc == "lodge":
        return _lodge_action(p, oid)
    if loc == "vault":
        return _vault_action(p, oid)
    if loc == "pawn":
        return _pawn_action(p, oid)
    if loc == "gate":
        return _gate_pick(p, oid)
    if loc == "gate_town":
        return _gate_town_action(p, oid)
    if loc == "relay":
        return social.relay_action(p, oid)
    if loc == "fields":
        return social.fields_action(p, oid)
    if loc == "guildhall":
        return social.guildhall_action(p, oid)
    if loc == "grants":
        return social.grant_action(p, oid)
    if loc == "boss_keep":
        return social.boss_action(p, schema.get_floor(max(1, p["floor"])), oid)
    if loc == "warden_keep":
        return social.warden_action(
            p, schema.get_floor(max(1, p["floor"])), oid)
    return _build_scene(p)


# ── Forge & Arcanum (004: rungs, lines, shoes, off-class) ───────────────

def _rack(p: dict, items: list, opts: list, lines: list) -> None:
    """One gear ladder in a shop: the last two buyable rungs as options,
    then the NEXT rung as a LOCKED row with its unlock level — every shop
    answers 'what am I saving for' by itself (004 §3.1, 019 rows).
    019: the worn rung stays on the rack — spares exist to be donated to
    the faction armory, so owning a piece never hides it from the shop."""
    lvl = p["level"]
    buyable = [g for g in items if economy.rung_player_level_req(g) <= lvl]
    nxt = next((g for g in items if economy.rung_player_level_req(g) > lvl), None)
    worn = p["gear"].get(items[0].slot) if items else None
    # the two newest steps stay, and the worn rung keeps its row even
    # when it sits below them — a spare is always on sale
    show = [g for g in buyable if g.slug != worn][-2:]
    if worn and any(g.slug == worn for g in buyable) \
            and all(g.slug != worn for g in show):
        show.append(next(g for g in buyable if g.slug == worn))
        show.sort(key=lambda g: g.rung)
    for g in show:
        stat = ("+{} spd".format(g.speed) if g.slot == "shoes"
                else ("+{} ATK".format(g.bonus) if g.slot == "weapon"
                      else "+{} DEF".format(g.bonus)))
        hint = (f"◈ {g.price:,} · worn — buy a spare"
                if g.slug == worn else f"◈ {g.price:,}")
        opts.append(Option(f"buy_{g.slug}", g.name, hint))
        flavor = f", {g.flavor}" if g.flavor else ""
        lines.append(f"{g.name}{flavor} — {stat}")
    if nxt is not None:
        stat = (f"+{nxt.speed} spd" if nxt.slot == "shoes"
                else f"+{nxt.bonus}")
        opts.append(Option(
            f"buy_{nxt.slug}", nxt.name,
            f"🔒 level {economy.rung_player_level_req(nxt)} · ◈ {nxt.price:,}",
            locked=True))
        lines.append(f"{nxt.name} — {stat}, the rung you're saving for")


def _wearable_pack(p: dict) -> list:
    """Paid gear riding in the pack that could be worn instead."""
    out = []
    for slug in p.get("inventory") or {}:
        g = economy.FORGE.get(slug)
        if g and g.slot in ("weapon", "shield", "armor", "shoes") \
                and (p["inventory"].get(slug) or 0) > 0:
            out.append(g)
    return sorted(out, key=lambda g: (g.slot, g.rung))


def _relic_rows(p: dict, shop: str, opts: list, lines: list) -> None:
    """006 §3.7: the shop's relic shelf — every row names the one
    dramatic effect AND the one hard limitation (the law, out loud).
    007 (006 retro): on a page already past ~8 prose rows the shelf
    folds into a <details> block — ▣ opens the fold, ▣. closes it;
    the renderer draws the summary, to_text draws a plain divider."""
    stock = economy.relic_stock(shop, p["unlocked_floor"],
                                p.get("clazz") or "")
    if not stock:
        return
    fold = len(lines) > 8
    lines.append(f"▣ the relic shelf — {len(stock)} on the wall"
                 if fold else "— the relic shelf —")
    for r in stock:
        price = economy.relic_price(r.slug, p["unlocked_floor"])
        owned = p["inventory"].get(r.slug, 0)
        hint = f"◈ {price:,}" + (f" · ×{r.count}" if r.count > 1 else "")
        opts.append(Option(f"buy_{r.slug}", r.name, hint))
        lines.append(f"{r.name} — {r.effect}. The catch: {r.limit}."
                     + (f" (you hold {owned})" if owned else ""))
    if fold:
        lines.append("▣.")


def _relic_buy(p: dict, slug: str, scene_fn) -> Scene:
    r = economy.RELICS[slug]
    if p["unlocked_floor"] < r.floor:
        s = scene_fn(p)
        s.shard_note = (f"The {r.name} waits behind the counter until "
                        f"floor {r.floor} stands open to you.")
        return s
    if r.clazz and (p.get("clazz") or "") != r.clazz:
        s = scene_fn(p)
        s.shard_note = f"The {r.name} is {r.clazz}'s work — not yours."
        return s
    if r.hold1 and p["inventory"].get(slug, 0) >= 1:
        s = scene_fn(p)
        s.shard_note = (f"You hold a {r.name} already — its kind "
                        "suffers no company. One, exactly.")
        return s
    price = economy.relic_price(slug, p["unlocked_floor"])
    if p["gold"] < price:
        s = scene_fn(p)
        s.shard_note = (f"The {r.name} is ◈ {price:,} and you carry "
                        f"◈ {p['gold']:,}.")
        return s
    p["gold"] -= price
    p["inventory"][slug] = p["inventory"].get(slug, 0) + r.count
    combat._ledger(p, "buy", gold=-price, note=slug)
    s = scene_fn(p)
    s.body_lines.insert(0, (f"+ {r.name}"
                            + (f" ×{r.count}" if r.count > 1 else "")
                            + f" — {r.effect}. The catch: {r.limit}."))
    return s


def _forge_scene(p: dict) -> Scene:
    clazz = p.get("clazz") or ""
    opts, lines = [], []
    # weapons: your own line at the Forge — staves live at the Arcanum
    if clazz in ("warrior", "archer"):
        _rack(p, economy.weapon_line(clazz), opts, lines)
    elif clazz == "sorcerer":
        lines.append("The smith nods at your staff and points across "
                     "the square: staves and focuses live at the Arcanum.")
    if clazz != "sorcerer":
        # shields serve warrior and archer; the caster's guard is the
        # Arcanum's focus (same slot, different shop)
        _rack(p, economy.gear_rungs("shield"), opts, lines)
    _rack(p, economy.gear_rungs("armor"), opts, lines)
    _rack(p, economy.gear_rungs("shoes"), opts, lines)
    # 004 §3.2: the off-class rack — the other physical line, one rung
    # back, at triple price. A tool for a bad matchup, never a build.
    off_lines = {"warrior": ("archer",), "archer": ("warrior",),
                 "sorcerer": ("warrior", "archer")}.get(clazz, ())
    for line in off_lines:
        g = economy.off_class_offer(line, p["level"])
        if g:
            price = economy.off_class_price(g)
            opts.append(Option(f"buy_{g.slug}", g.name,
                               f"◈ {price:,} · off-class"))
            lines.append(f"{g.name} — not your weapon: ×3 the coin, "
                         "half the bite, and one shot in four goes wide")
    if clazz != "archer":
        opts.append(Option(
            "buy_arrow_pack", "Arrow pack",
            f"◈ {economy.ARROW_PACK_PRICE} · {economy.ARROW_PACK_SIZE} "
            "arrows"))
    _relic_rows(p, "forge", opts, lines)      # 006: quivers and tools
    for g in _wearable_pack(p):
        if p["gear"].get(g.slot) != g.slug:
            opts.append(Option(f"wear_{g.slug}", f"Wear {g.name}",
                               "from your pack"))
    cap = economy.max_hone(p["unlocked_floor"])
    price = economy.hone_price(p["unlocked_floor"])
    hone_xp = economy.hone_xp(p["unlocked_floor"])
    for slot in economy.HONE_SLOTS:
        slug = p["gear"].get(slot)
        lvl = state.hone_level(p, slot)
        item = economy.FORGE.get(slug or "")
        # off-class gear never hones (004 §3.2)
        if slot == "weapon" and item is not None and item.line \
                and clazz and item.line != clazz:
            continue
        if slug and lvl < cap:
            name = economy.FORGE[slug].name
            opts.append(Option(f"hone_{slot}", f"Hone {name} +{lvl + 1}",
                               f"◈ {price:,} + {hone_xp} XP"))
    # 005: the repair bench — every worn PAID piece on the body gets a
    # row; price scales with the missing fraction, XP mirrors honing.
    for slot in economy.DURABILITY_SLOTS:
        g = economy.FORGE.get(p["gear"].get(slot) or "")
        left = (p.get("durability") or {}).get(slot)
        if not g or g.price <= 0 or left is None:
            continue
        pool = economy.item_pool(g)
        if left >= pool:
            continue
        rprice = economy.repair_price(g, 1 - left / pool)
        opts.append(Option(
            f"repair_{slot}",
            f"Repair {g.name}" + (" — broken" if left <= 0 else ""),
            f"◈ {rprice:,} + {hone_xp} XP"))
    if cap > 0:
        honed = ", ".join(
            f"{slot} +{state.hone_level(p, slot)}"
            for slot in economy.HONE_SLOTS if state.hone_level(p, slot))
        lines.append(f"Honing bench: up to +{cap} per piece this band"
                     + (f" — yours: {honed}" if honed else ""))
    opts.append(Option("back", "Back to the square"))
    tier = economy.gear_tier_for_floor(p["unlocked_floor"])
    return Scene(
        eyebrow="ROOTHOLLOW · THE FORGE",
        headline=f"Tier {tier} steel, scrap to plasma",
        support="Blades, bows, plate and boots. The locked rung is the "
                "one you're saving for.",
        body_lines=lines,
        options=opts,
        meters=combat.meters(p),
        banner="forge",
    )


def _forge_hone(p: dict, slot: str) -> Scene:
    slug = p["gear"].get(slot)
    cap = economy.max_hone(p["unlocked_floor"])
    lvl = state.hone_level(p, slot)
    if not slug or lvl >= cap:
        return _forge_scene(p)
    price = economy.hone_price(p["unlocked_floor"])
    xp_cost = economy.hone_xp(p["unlocked_floor"])
    if p["gold"] < price:
        s = _forge_scene(p)
        s.shard_note = (f"A honing pass costs ◈ {price:,} + {xp_cost} XP; "
                        f"you carry ◈ {p['gold']:,}.")
        return s
    if p["xp"] < xp_cost:
        s = _forge_scene(p)
        s.shard_note = (f"The bench takes {xp_cost} XP of what you've "
                        f"learned along with the coin — you carry "
                        f"{p['xp']} XP. Hunt first.")
        return s
    p["gold"] -= price
    state.spend_xp(p, xp_cost)
    p["hone"][slot] = lvl + 1
    combat._ledger(p, "hone", gold=-price, xp=-xp_cost,
                   note=f"{slot} +{lvl + 1}")
    s = _forge_scene(p)
    s.body_lines.insert(0, (f"+ {economy.FORGE[slug].name} honed to "
                            f"+{lvl + 1} — the edge sings on the stone "
                            f"(− {xp_cost} XP)"))
    return s


def _forge_repair(p: dict, slot: str) -> Scene:
    """005: mend a worn piece — 20% of its price × the missing fraction,
    plus the honing bench's XP ask. Same refusal grammar as honing."""
    g = economy.FORGE.get(p["gear"].get(slot) or "")
    left = (p.get("durability") or {}).get(slot)
    if not g or g.price <= 0 or left is None:
        return _forge_scene(p)
    pool = economy.item_pool(g)
    if left >= pool:
        return _forge_scene(p)
    price = economy.repair_price(g, 1 - left / pool)
    xp_cost = economy.hone_xp(p["unlocked_floor"])
    if p["gold"] < price:
        s = _forge_scene(p)
        s.shard_note = (f"Mending the {g.name} costs ◈ {price:,} + "
                        f"{xp_cost} XP; you carry ◈ {p['gold']:,}.")
        return s
    if p["xp"] < xp_cost:
        s = _forge_scene(p)
        s.shard_note = (f"The smith takes {xp_cost} XP of what you've "
                        f"learned along with the coin — you carry "
                        f"{p['xp']} XP. Hunt first.")
        return s
    p["gold"] -= price
    state.spend_xp(p, xp_cost)
    p["durability"][slot] = pool
    combat._ledger(p, "repair", gold=-price, xp=-xp_cost, note=slot)
    s = _forge_scene(p)
    s.body_lines.insert(0, (f"+ {g.name} made whole on the anvil — "
                            f"every use back in it (− {xp_cost} XP)"))
    return s


def _gear_purchase(p: dict, g, scene_fn) -> Scene:
    """Shared buy path for the Forge and the Arcanum: level gate,
    off-class ×3 pricing, equip + old piece to the pack."""
    clazz = p.get("clazz") or ""
    off = bool(g.line) and clazz and g.line != clazz
    req = economy.rung_player_level_req(g)
    price = economy.off_class_price(g) if off else g.price
    if p["level"] < req:
        s = scene_fn(p)
        s.shard_note = (f"{g.name} answers to level {req} hands — you are "
                        f"level {p['level']}. The Guildhall trains climbers "
                        "with a full XP bar and the fee in gold.")
        return s
    if p["gold"] < price:
        s = scene_fn(p)
        s.shard_note = f"{g.name} wants ◈ {price:,}; you carry ◈ {p['gold']:,}. " \
                       "The Vault pays interest for a reason."
        return s
    old = p["gear"].get(g.slot)
    if old == g.slug:
        # 019: a spare of the piece you wear — straight to the pack,
        # fresh pool, nothing on your body moves. Wear in the pack is
        # tracked per slug: a fresh copy only claims the key when no
        # stashed copy holds it (the armory takes donations as-is).
        p["gold"] -= price
        p["inventory"][g.slug] = p["inventory"].get(g.slug, 0) + 1
        p.setdefault("durability_pack", {}).setdefault(
            g.slug, economy.item_pool(g))
        combat._ledger(p, "buy", gold=-price, note=f"{g.slug} (spare)")
        s = scene_fn(p)
        s.body_lines.insert(0, (f"+ {g.name} — a spare for the pack "
                                "(the armory takes donations)"))
        return s
    p["gold"] -= price
    p["gear"][g.slot] = g.slug
    if g.slot in p.get("hone", {}):
        p["hone"][g.slot] = 0        # honing lives on the item it honed
    # 005: wear lives on the item too — stash the old piece's remaining
    # uses with the pack (it comes back as worn as it left), fresh pool
    # on the new one.
    old_dur = (p.get("durability") or {}).pop(g.slot, None)
    if old and old_dur is not None:
        p.setdefault("durability_pack", {})[old] = old_dur
    p.setdefault("durability", {})[g.slot] = economy.item_pool(g)
    if g.slot == "shoes":
        note = f"+ {g.name} laced on (+{g.speed} speed)"
    else:
        stat = "ATK" if g.slot == "weapon" else "DEF"
        note = f"+ {g.name} equipped ({g.slot} +{g.bonus} {stat})"
    if off:
        note += " — off-class: half the bite, one in four goes wide"
    if old and economy.FORGE[old].price > 0:
        p["inventory"][old] = p["inventory"].get(old, 0) + 1
        note += f" — your {economy.FORGE[old].name} goes to your pack"
    elif old:
        note += f" — the {economy.FORGE[old].name} goes in the scrap bin"
    # 005 staged onboarding: the slot's FIRST paid piece teaches wear
    # in one line, then never again.
    flag = f"dur_taught_{g.slot}"
    if not p["flags"].get(flag):
        p["flags"][flag] = True
        note += (" — paid gear wears with use; the Forge repairs it "
                 "for a fraction of its price")
    combat._ledger(p, "buy", gold=-price, note=g.slug)
    s = scene_fn(p)
    s.body_lines.insert(0, note)
    return s


def _wear_from_pack(p: dict, slug: str, scene_fn) -> Scene:
    g = economy.FORGE.get(slug)
    if not g or (p.get("inventory") or {}).get(slug, 0) <= 0:
        return scene_fn(p)
    old = p["gear"].get(g.slot)
    p["inventory"][slug] -= 1
    if p["inventory"][slug] <= 0:
        del p["inventory"][slug]
    p["gear"][g.slot] = slug
    if g.slot in p.get("hone", {}):
        p["hone"][g.slot] = 0
    # 005: swap the wear along with the piece — no fresh pool for free.
    stash = p.setdefault("durability_pack", {})
    old_dur = (p.get("durability") or {}).pop(g.slot, None)
    if old and old_dur is not None:
        stash[old] = old_dur
    if g.price > 0:
        p.setdefault("durability", {})[g.slot] = stash.pop(
            slug, economy.item_pool(g))
    note = f"+ {g.name} back on"
    if old and economy.FORGE.get(old) and economy.FORGE[old].price > 0:
        p["inventory"][old] = p["inventory"].get(old, 0) + 1
        note += f" — the {economy.FORGE[old].name} goes to your pack"
    s = scene_fn(p)
    s.body_lines.insert(0, note)
    return s


def _forge_buy(p: dict, oid: str) -> Scene:
    if oid.startswith("hone_") and oid.removeprefix("hone_") in \
            economy.HONE_SLOTS:
        return _forge_hone(p, oid.removeprefix("hone_"))
    if oid.startswith("repair_") and oid.removeprefix("repair_") in \
            economy.DURABILITY_SLOTS:
        return _forge_repair(p, oid.removeprefix("repair_"))
    if oid == "buy_arrow_pack":
        if p["gold"] < economy.ARROW_PACK_PRICE:
            s = _forge_scene(p)
            s.shard_note = (f"A pack of arrows is ◈ "
                            f"{economy.ARROW_PACK_PRICE} and you carry "
                            f"◈ {p['gold']:,}.")
            return s
        p["gold"] -= economy.ARROW_PACK_PRICE
        p["inventory"]["arrows"] = (p["inventory"].get("arrows", 0)
                                    + economy.ARROW_PACK_SIZE)
        combat._ledger(p, "buy", gold=-economy.ARROW_PACK_PRICE,
                       note="arrow_pack")
        s = _forge_scene(p)
        s.body_lines.insert(0, f"+ {economy.ARROW_PACK_SIZE} arrows — "
                            f"{p['inventory']['arrows']} in the quiver")
        return s
    if oid.startswith("wear_"):
        return _wear_from_pack(p, oid.removeprefix("wear_"), _forge_scene)
    slug = oid.removeprefix("buy_")
    if slug in economy.RELICS and economy.RELICS[slug].shop == "forge":
        return _relic_buy(p, slug, _forge_scene)
    g = economy.FORGE.get(slug)
    if not g:
        return _forge_scene(p)
    if g.line == "sorcerer":
        s = _forge_scene(p)
        s.shard_note = "The smith shrugs: caster's work. The Arcanum " \
                       "sells the staves and the focuses."
        return s
    return _gear_purchase(p, g, _forge_scene)


# ── The Arcanum (004 §3.4) ───────────────────────────────────────────────

def _arcanum_scene(p: dict) -> Scene:
    if p["level"] < economy.ARCANUM_LEVEL:
        p["location"] = "town"
        s = _town_scene(p)
        s.shard_note = (f"The Arcanum wants level {economy.ARCANUM_LEVEL} "
                        "hands. Climb first.")
        return s
    clazz = p.get("clazz") or ""
    opts, lines = [], []
    if clazz == "sorcerer":
        _rack(p, economy.weapon_line("sorcerer"), opts, lines)
        _rack(p, economy.gear_rungs("shield", "sorcerer"), opts, lines)
    else:
        # 004 §3.2: staves off the rack, one rung back, triple coin —
        # focuses answer only to a caster's hand.
        g = economy.off_class_offer("sorcerer", p["level"])
        if g:
            opts.append(Option(f"buy_{g.slug}", g.name,
                               f"◈ {economy.off_class_price(g):,} · "
                               "off-class"))
            lines.append(f"{g.name} — not your weapon: ×3 the coin, "
                         "half the bite, and one cast in four fizzles")
        lines.append("The focuses behind the counter won't wake for "
                     "you — caster's gear, caster's hand.")
    _relic_rows(p, "arcanum", opts, lines)    # 006: the mage relics
    opts.append(Option("back", "Back to the square"))
    return Scene(
        eyebrow="ROOTHOLLOW · THE ARCANUM",
        headline="Star-charts, staves and patient glass",
        support="The shop hums a half-tone above silence. The "
                "shopkeeper's eyes are the only bright thing in it.",
        body_lines=lines,
        options=opts,
        meters=combat.meters(p),
        banner="arcanum",
    )


def _arcanum_buy(p: dict, oid: str) -> Scene:
    if oid.startswith("wear_"):
        return _wear_from_pack(p, oid.removeprefix("wear_"), _arcanum_scene)
    slug = oid.removeprefix("buy_")
    if slug in economy.RELICS and economy.RELICS[slug].shop == "arcanum":
        return _relic_buy(p, slug, _arcanum_scene)
    g = economy.FORGE.get(slug)
    if not g:
        return _arcanum_scene(p)
    if g.line != "sorcerer":
        s = _arcanum_scene(p)
        s.shard_note = "The shopkeeper tilts her head: steel is the " \
                       "smith's trade. The Forge is across the square."
        return s
    if g.slot == "shield" and (p.get("clazz") or "") != "sorcerer":
        # 005 design decision: only BUYING a focus is class-gated. One
        # already owned (class change, hand-me-down) keeps working as a
        # shield and may be honed/repaired — it's the wearer's guard
        # now, and durability taxes it like any other paid piece.
        s = _arcanum_scene(p)
        s.shard_note = ("The focus goes dark in your hand — it answers "
                        "only to a caster.")
        return s
    return _gear_purchase(p, g, _arcanum_scene)


# ── Medlab ───────────────────────────────────────────────────────────────

def _medlab_scene(p: dict) -> Scene:
    opts = [Option(f"buy_{i.slug}", i.name,
                   f"◈ {i.price}" + (f" · {i.note}" if i.note else ""))
            for i in economy.APOTHECARY.values()]
    inv = [f"{economy.APOTHECARY[k].name} ×{v}"
           for k, v in p["inventory"].items() if k in economy.APOTHECARY]
    lines = ["you carry: " + ", ".join(inv)] if inv else []
    _relic_rows(p, "apothecary", opts, lines)  # 006: the life-guards
    opts.append(Option("back", "Back to the square"))
    return Scene(
        eyebrow="ROOTHOLLOW · APOTHECARY & MEDLAB",
        headline="Gels, stims, and honest odds",
        support="The lamp hums. The shelves are stocked. The prices are firm.",
        body_lines=lines,
        options=opts,
        meters=combat.meters(p),
        banner="medlab",
    )


def _medlab_buy(p: dict, oid: str) -> Scene:
    slug = oid.removeprefix("buy_")
    if slug in economy.RELICS and economy.RELICS[slug].shop == "apothecary":
        return _relic_buy(p, slug, _medlab_scene)
    item = economy.APOTHECARY.get(slug)
    if not item:
        return _medlab_scene(p)
    daily = p["daily"]
    if slug == "energy_cell" and daily.get("energy_cell"):
        s = _medlab_scene(p)
        s.shard_note = "One cell a day. Your heart is not a reactor."
        return s
    if p["gold"] < item.price:
        s = _medlab_scene(p)
        s.shard_note = f"That's ◈ {item.price} and you carry ◈ {p['gold']}."
        return s
    p["gold"] -= item.price
    combat._ledger(p, "buy", gold=-item.price, note=slug)
    note = f"+ {item.name}"
    if slug == "energy_cell":
        daily["energy_cell"] = True
        state.gain_energy(p, 5)
        note += " — ⚡ +5"
    elif slug == "luck_charm":
        p["flags"]["luck_day"] = state.world_day()
        note += " — fortune leans your way until tomorrow"
    elif slug == "scout_optics":
        p["sidekick"]["scout_charges"] += 3
        note += " — your shard can scan 3 enemies"
    else:
        p["inventory"][slug] = p["inventory"].get(slug, 0) + 1
    s = _medlab_scene(p)
    s.body_lines.insert(0, note)
    return s


# ── Lodge ────────────────────────────────────────────────────────────────

def _eat_stew(p: dict, scene_fn) -> Scene:
    """008: the cheap partial heal — ◈ 2 for +5 HP, repeatable."""
    if p["gold"] < economy.STEW_PRICE:
        s = scene_fn(p)
        s.shard_note = (f"The stew costs ◈ {economy.STEW_PRICE} and the pot "
                        "keeper doesn't run tabs.")
        return s
    if p["hp"] >= state.max_hp(p):
        s = scene_fn(p)
        s.shard_note = "You're whole. Save the coin for when you're not."
        return s
    p["gold"] -= economy.STEW_PRICE
    p["hp"] = min(state.max_hp(p), p["hp"] + economy.STEW_HEAL_HP)
    combat._ledger(p, "stew", gold=-economy.STEW_PRICE)
    s = scene_fn(p)
    s.body_lines.insert(0, f"+ {economy.STEW_HEAL_HP} HP — hot, thick, and "
                           "mostly what the pot keeper claims it is.")
    return s


def _lodge_scene(p: dict) -> Scene:
    price = economy.LODGE_PRICE_PER_LEVEL * p["level"]
    lodged = p["lodged_until_day"] >= state.world_day() + 1
    opts = []
    if not lodged:
        opts.append(Option("sleep", "Pay for the night", f"◈ {price}"))
    if p["hp"] < state.max_hp(p):
        opts.append(Option("stew", "Hunter's stew",
                           f"◈ {economy.STEW_PRICE} · +{economy.STEW_HEAL_HP} HP"))
    opts.append(Option("back", "Back to the square"))
    return Scene(
        eyebrow="ROOTHOLLOW · THE LODGE",
        headline="Sleep behind the palisade" if not lodged
                 else "Your bunk is paid through tonight",
        support="Skip the lodge and you sleep in the fields — where anyone "
                "may find you.",
        body_lines=[f"A night costs ◈ {price}. Banked gold can't buy it — "
                    "carry coin.",
                    f"A proper bed mends +{economy.LODGE_NIGHT_HEAL_HP} HP "
                    "by dawn. The fields mend nothing."],
        options=opts,
        meters=combat.meters(p),
        banner="lodge",
    )


def _lodge_action(p: dict, oid: str) -> Scene:
    if oid == "stew":
        return _eat_stew(p, _lodge_scene)
    if oid != "sleep":
        return _lodge_scene(p)
    price = economy.LODGE_PRICE_PER_LEVEL * p["level"]
    if p["gold"] < price:
        s = _lodge_scene(p)
        s.shard_note = "Not enough carried coin. The fields it is — unless " \
                       "you visit the Vault."
        return s
    p["gold"] -= price
    p["lodged_until_day"] = state.world_day() + 1
    combat._ledger(p, "lodge", gold=-price)
    s = _lodge_scene(p)
    s.headline = "Your bunk is paid through tonight"
    s.body_lines.insert(0, "+ one safe night. Nothing finds you here — and "
                           f"the bed gives back {economy.LODGE_NIGHT_HEAL_HP}"
                           " HP by dawn.")
    return s


# ── Vault ────────────────────────────────────────────────────────────────

def _vault_scene(p: dict) -> Scene:
    interest = state.bank_interest_due(p)
    lines = []
    if interest > 0:
        p["bank"] += interest
        combat._ledger(p, "interest", gold=interest)
        lines.append(f"+ ◈ {interest:,} interest credited "
                     f"({int(economy.BANK_INTEREST_RATE * 100)}%/day, compounded)")
    p["bank_day"] = state.world_day()
    lines.append(f"banked ◈ {p['bank']:,} · carried ◈ {p['gold']:,}")
    opts = []
    if p["gold"] > 0:
        opts += [Option("deposit_all", "Deposit everything", f"◈ {p['gold']:,}"),
                 Option("deposit_half", "Deposit half", f"◈ {p['gold'] // 2:,}")]
    if p["bank"] > 0:
        opts.append(Option("withdraw_all", "Withdraw everything",
                           f"◈ {p['bank']:,}"))
    if p.get("_world"):
        opts.append(Option("grants", "The grants desk", "send gold"))
    opts.append(Option("back", "Back to the square"))
    return Scene(
        eyebrow="ROOTHOLLOW · THE VAULT",
        headline="A lodge for your money",
        support="Deposits survive death, theft, and bad decisions. "
                "Interest compounds daily.",
        body_lines=lines,
        options=opts,
        meters=combat.meters(p),
        banner="vault",
    )


def _vault_action(p: dict, oid: str) -> Scene:
    if oid == "deposit_all" and p["gold"] > 0:
        combat._ledger(p, "deposit", gold=-p["gold"])
        p["bank"] += p["gold"]
        p["gold"] = 0
    elif oid == "deposit_half" and p["gold"] > 0:
        half = p["gold"] // 2
        combat._ledger(p, "deposit", gold=-half)
        p["bank"] += half
        p["gold"] -= half
    elif oid == "withdraw_all" and p["bank"] > 0:
        combat._ledger(p, "withdraw", gold=p["bank"])
        p["gold"] += p["bank"]
        p["bank"] = 0
    return _vault_scene(p)


# ── Pawn shop ────────────────────────────────────────────────────────────

def _pawn_frac(p: dict, g) -> float:
    """005: worn gear pays × its remaining durability fraction. The
    broker checks the stash the pack carries; unworn gear is 1.0."""
    left = (p.get("durability_pack") or {}).get(g.slug)
    if left is None or g.price <= 0:
        return 1.0
    pool = economy.item_pool(g)
    return max(0.0, min(1.0, left / pool)) if pool else 1.0


def _pawn_offer(p: dict, g) -> int:
    # 006 §3.8: the broker's daily mood replaces the flat 40%.
    rate = economy.pawn_rate(state.world_day())
    return int(g.price * rate * _pawn_frac(p, g))


def _pawn_relic_offer(p: dict, slug: str) -> int:
    rate = economy.pawn_rate(state.world_day())
    return int(economy.relic_price(slug, p["unlocked_floor"]) * rate)


def _pawn_scene(p: dict) -> Scene:
    rate = economy.pawn_rate(state.world_day())
    gear_in_pack = [k for k in p["inventory"] if k in economy.FORGE]
    relics_in_pack = [k for k in p["inventory"] if k in economy.RELICS]
    opts = []
    lines = [f"The broker pays {round(rate * 100)}% today. Tomorrow is "
             "another mood."]
    for slug in gear_in_pack:
        g = economy.FORGE[slug]
        offer = _pawn_offer(p, g)
        frac = _pawn_frac(p, g)
        worn = f", worn to {round(frac * 100)}%" if frac < 1.0 else ""
        opts.append(Option(f"sell_{slug}", f"Sell {g.name}", f"◈ {offer:,}"))
        lines.append(f"{g.name} ×{p['inventory'][slug]}{worn} — "
                     f"offers ◈ {offer:,}")
    # 006 §3.8: the pawn always buys ANYTHING — relics included.
    for slug in relics_in_pack:
        r = economy.RELICS[slug]
        offer = _pawn_relic_offer(p, slug)
        opts.append(Option(f"sell_{slug}", f"Sell {r.name}", f"◈ {offer:,}"))
        lines.append(f"{r.name} ×{p['inventory'][slug]} — offers ◈ {offer:,}")
    if not gear_in_pack and not relics_in_pack:
        lines.append("Nothing in your pack the broker wants today.")
    # 007: members can route a piece PAST the broker to the faction
    # racks — no gold moves, the wear rides with it (the EV law).
    w = p.get("_world") or {}
    if w.get("faction") and w.get("armory") is not None:
        cap = int(w.get("armory_cap", 50))
        rack = w.get("armory") or []
        donatable = [k for k in gear_in_pack
                     if economy.FORGE[k].price > 0]
        if donatable:
            lines.append(f"Or skip the broker: the "
                         f"{w['faction'].get('name', 'faction')} armory "
                         f"racks hold {len(rack)}/{cap}.")
            for slug in donatable:
                g = economy.FORGE[slug]
                opts.append(Option(f"donate_{slug}",
                                   f"Donate {g.name} to the armory",
                                   "no coin — the banner keeps it"))
    opts.append(Option("back", "Back to the square"))
    return Scene(
        eyebrow="ROOTHOLLOW · PAWN SHOP",
        headline=f"{round(rate * 100)} on the hundred, no haggling",
        support="The broker has seen everything twice and paid less for it "
                "both times.",
        body_lines=lines,
        options=opts,
        meters=combat.meters(p),
    )


def _pawn_action(p: dict, oid: str) -> Scene:
    if oid.startswith("donate_"):
        return _pawn_donate(p, oid.removeprefix("donate_"))
    slug = oid.removeprefix("sell_")
    if slug in p["inventory"] and slug in economy.FORGE:
        g = economy.FORGE[slug]
        offer = _pawn_offer(p, g)
        p["inventory"][slug] -= 1
        if p["inventory"][slug] <= 0:
            del p["inventory"][slug]
            (p.get("durability_pack") or {}).pop(slug, None)
        p["gold"] += offer
        combat._ledger(p, "pawn", gold=offer, note=slug)
        s = _pawn_scene(p)
        s.body_lines.insert(0, f"+ ◈ {offer:,} for the {g.name}")
        return s
    if slug in p["inventory"] and slug in economy.RELICS:
        offer = _pawn_relic_offer(p, slug)
        p["inventory"][slug] -= 1
        if p["inventory"][slug] <= 0:
            del p["inventory"][slug]
        p["gold"] += offer
        combat._ledger(p, "pawn", gold=offer, note=slug)
        s = _pawn_scene(p)
        s.body_lines.insert(0,
                            f"+ ◈ {offer:,} for the "
                            f"{economy.RELICS[slug].name}")
        return s
    return _pawn_scene(p)


def _pawn_donate(p: dict, slug: str) -> Scene:
    """007: hand a paid piece to the faction racks. No gold, ever —
    the wear stash travels WITH the piece (a worn copy leaves first,
    so the racks can never launder wear away)."""
    w = p.get("_world") or {}
    g = economy.FORGE.get(slug)
    if (g is None or g.price <= 0 or slug not in p["inventory"]
            or not w.get("faction") or w.get("armory") is None):
        return _pawn_scene(p)
    if len(w.get("armory") or []) >= int(w.get("armory_cap", 50)):
        s = _pawn_scene(p)
        s.shard_note = "The armory racks are full — nothing fits."
        return s
    from . import social
    p["inventory"][slug] -= 1
    if p["inventory"][slug] <= 0:
        del p["inventory"][slug]
    uses = (p.get("durability_pack") or {}).pop(slug, None)
    social._effect(p, "armory_deposit", slug=slug, uses_left=uses)
    combat._ledger(p, "armory_give", gold=0, note=slug)
    s = _pawn_scene(p)
    s.body_lines.insert(
        0, f"The {g.name} goes to the "
           f"{w['faction'].get('name', 'faction')} racks — the banner "
           "keeps it now.")
    return s


# ── Stone of the Climb ───────────────────────────────────────────────────

def _stone_scene(p: dict) -> Scene:
    w = p.get("_world") or {}
    frontier = max(p["unlocked_floor"], w.get("frontier", 0))
    lines = [
        f"{p['name'] or 'A climber'} — highest floor opened: "
        f"{p['unlocked_floor']}",
    ]
    for s in (w.get("stone") or [])[:8]:
        lines.append(f"✦ {s}")
    lines.append("The lift opens for everyone when a Warden falls.")
    return Scene(
        eyebrow="ROOTHOLLOW · STONE OF THE CLIMB",
        headline=f"The frontier stands at floor {frontier}",
        support="Old granite, names lit from within by aether.",
        body_lines=lines,
        options=[Option("back", "Back to the square")],
        meters=combat.meters(p),
        banner="stone",
    )


# ── Tower gate & floors ──────────────────────────────────────────────────

def _gate_scene(p: dict) -> Scene:
    top = min(p["unlocked_floor"], schema.max_content_floor())
    opts = []
    for n in range(1, top + 1):
        fl = schema.get_floor(n)
        opts.append(Option(f"floor_{n}", f"Floor {n} — {fl.zone}",
                           fl.gate_town))
    opts.append(Option("back", "Back to the square"))
    return Scene(
        eyebrow="ROOTHOLLOW · THE TOWER GATE",
        headline=f"{top} floor{'s' if top > 1 else ''} stand open",
        support="Pick any opened floor. The grind pays best near your level.",
        options=opts,
        meters=combat.meters(p),
        banner="gate",
    )


def _gate_pick(p: dict, oid: str) -> Scene:
    if not oid.startswith("floor_"):
        return _gate_scene(p)
    n = int(oid.removeprefix("floor_"))
    if n > p["unlocked_floor"] or n > schema.max_content_floor():
        s = _gate_scene(p)
        s.shard_note = f"Floor {n} is still sealed. A Warden holds every lift."
        return s
    req = economy.floor_entry_player_level(n)
    if p["level"] < req:
        s = _gate_scene(p)
        s.shard_note = (f"The lift is open, but floor {n} wants level {req} "
                        f"legs — you are level {p['level']}. Climb closer "
                        "to your weight first.")
        return s
    p["floor"] = n
    p["location"] = "gate_town"
    fl = schema.get_floor(n)
    return Scene(
        eyebrow=f"FLOOR {n} · {fl.biome.upper()} · {fl.gate_town.upper()}",
        headline=f"{fl.gate_town} — the floor's last safe fire",
        support="A healer, a rumor bench, and the wilds beyond the wire.",
        body_lines=[fl.arrival],
        options=_gate_town_options(p, fl),
        meters=combat.meters(p),
        banner=fl.banner,
    )


def _gate_town_options(p: dict, fl) -> list[Option]:
    heal_price = economy.HEALER_TENT_PER_FLOOR * fl.floor
    opts = [Option("hunt", "Hunt the wilds", "1 ⚡")]
    if p["hp"] < state.max_hp(p):
        opts.append(Option("stew", "Hunter's stew",
                           f"◈ {economy.STEW_PRICE} · +{economy.STEW_HEAL_HP} HP"))
        opts.append(Option("heal", "The healer's tent", f"◈ {heal_price}"))
        # 014: the pack heals finally have a mouth — usable at the camp
        # fire (the tonic stays the only MID-fight heal, per 013).
        for slug in ("medgel", "trauma_kit"):
            have = p["inventory"].get(slug, 0)
            if have:
                item = economy.APOTHECARY[slug]
                amount = int(item.effect.rsplit("_", 1)[1])
                opts.append(Option(f"use_{slug}", f"Use a {item.name}",
                                   f"+{amount} HP · {have} left"))
    opts.append(Option("keep", f"The Warden's keep — {fl.warden_name}", "3 ⚡"))
    opts.append(Option("town", "Return to Roothollow"))
    return opts


def _gate_town_scene(p: dict) -> Scene:
    fl = schema.get_floor(max(1, p["floor"]))
    return Scene(
        eyebrow=f"FLOOR {fl.floor} · {fl.biome.upper()} · {fl.gate_town.upper()}",
        headline=f"{fl.gate_town}",
        support="The fire is small but honest. Beyond the wire, the wilds.",
        options=_gate_town_options(p, fl),
        meters=combat.meters(p),
    )


def _gate_town_action(p: dict, oid: str) -> Scene:
    fl = schema.get_floor(max(1, p["floor"]))
    if oid == "hunt":
        if not state.spend_energy(p, economy.COST_WILDS_FIGHT):
            s = _gate_town_scene(p)
            s.shard_note = ("You're spent — ⚡ regenerates one point every "
                            "45 minutes. Rest, bank, or read the Stone.")
            return s
        table = [(e.weight, e.id) for e in fl.encounters]
        enc_id = state.rng_pick(p, table)
        enc = next(e for e in fl.encounters if e.id == enc_id)
        combat._ledger(p, "energy", note="wilds")
        return combat.start_encounter(p, fl, enc, "wilds")
    if oid == "heal":
        price = economy.HEALER_TENT_PER_FLOOR * fl.floor
        if p["gold"] < price:
            s = _gate_town_scene(p)
            s.shard_note = f"The healer wants ◈ {price} you don't carry."
            return s
        p["gold"] -= price
        p["hp"] = state.max_hp(p)
        combat._ledger(p, "heal", gold=-price)
        s = _gate_town_scene(p)
        s.body_lines.insert(0, "+ patched to full. The needle was clean. Probably.")
        return s
    if oid == "stew":
        return _eat_stew(p, _gate_town_scene)
    if oid.startswith("use_"):
        slug = oid.removeprefix("use_")
        item = economy.APOTHECARY.get(slug)
        if not (item and item.effect.startswith("heal_")
                and p["inventory"].get(slug, 0) > 0):
            return _gate_town_scene(p)
        if p["hp"] >= state.max_hp(p):
            s = _gate_town_scene(p)
            s.shard_note = "You're whole. Keep it sealed for when you're not."
            return s
        p["inventory"][slug] -= 1
        if p["inventory"][slug] <= 0:
            del p["inventory"][slug]
        amount = int(item.effect.rsplit("_", 1)[1])
        before = p["hp"]
        p["hp"] = min(state.max_hp(p), p["hp"] + amount)
        combat._ledger(p, "use", note=slug)
        s = _gate_town_scene(p)
        s.body_lines.insert(0, f"+ {p['hp'] - before} HP — the "
                               f"{item.name.lower()} does its work.")
        return s
    if oid == "keep":
        w = p.get("_world") or {}
        # milestone keeps run the quorum flow in the shared world
        if fl.milestone and w:
            from . import social
            p["location"] = "boss_keep"
            return social.boss_scene(p, fl)
        # 007 §3: the live frontier Warden is ONE shared monster
        wd = w.get("warden") if w else None
        if wd and wd.get("floor") == fl.floor:
            from . import social
            p["location"] = "warden_keep"
            return social.warden_scene(p, fl)
        # below the frontier (or local dev play): the per-player echo bout
        if not state.spend_energy(p, economy.COST_WARDEN_ATTEMPT):
            s = _gate_town_scene(p)
            s.shard_note = "A Warden takes 3 ⚡ you don't have. The wilds " \
                           "cost less."
            return s
        return combat.start_encounter(p, fl, None, "warden")
    if oid == "gate":
        p["location"] = "gate"
        return _gate_scene(p)
    return _gate_town_scene(p)
