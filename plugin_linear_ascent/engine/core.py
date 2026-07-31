"""The state machine — every flow gated here, steering hints on refusal.

`current_scene(p)` is idempotent (safe to call anytime).
`apply_choice(p, option_id, text)` validates the option against the
current scene and dispatches. The agent never free-forms game state.
"""

from __future__ import annotations

import datetime as dt

from .. import economy, unlocks
from ..content import schema
from . import combat, contracts, notices, state, weekly
from .scene import Meters, Option, Scene


# ── Entry points ─────────────────────────────────────────────────────────

# 027: the notice board rides every room in Roothollow, not just the
# square — walking into the Forge should still tell you the Vault is
# holding your money. The climb itself stays clean: no notices at the gate,
# in the wilds or inside a keep, where the only thing that matters is the
# thing trying to kill you.
_NOTICE_ROOMS = ("town", "forge", "arcanum", "medlab", "lodge", "vault",
                 "pawn", "stone", "guildhall", "board", "relay", "fields",
                 "grants")


def _stamp(p: dict, scene: Scene) -> Scene:
    """scene_id = the act counter. Every choice bumps it, reads reuse it —
    /pane/peek compares ids, so a chat-driven act refreshes the pane
    while idempotent reads never do. 014: the pack strip rides every
    playing scene the same way. 027: so does the notice board, in town."""
    scene.scene_id = f"s{p.get('act_seq', 0)}"
    scene.inventory = _pack_strip(p)
    if (not scene.notices and not scene.enemy
            and p.get("location") in _NOTICE_ROOMS):
        scene.notices = notices.pending(p)
    # 027: every pack cell carries what it can do HERE — the strip stops
    # being a hover-only display and becomes the place you use a thing.
    for cell in scene.inventory:
        acts, why = pack_actions(p, cell["slug"])
        if acts:
            cell["acts"] = [{"opt": o.id, "label": o.label, "hint": o.hint}
                            for o in acts]
        if why:
            cell["why"] = why
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


# 027: what a carried thing can do, right where you stand. The pack strip
# was hover-text for three versions and salves piled up in it because the
# only mouth that ate one was a menu row at the camp fire. Now every cell
# answers two questions: what can I do with this here, and if nothing —
# where can I?
#
# The law that does NOT change: the trollblood tonic is still the only heal
# that goes down mid-fight (013). Everything else waits for the fight to
# end, and the popup says so instead of leaving the player guessing.
PACK_USE_IDS = ("use_medgel", "use_trauma_kit", "use_luck_charm")


def pack_actions(p: dict, slug: str) -> tuple[list[Option], str]:
    """(actions, why-not) for one pack slug in the player's current
    situation. Actions are ordinary option ids — the engine gains no verb
    it did not already validate."""
    if p.get("stage") != "playing":
        return [], ""
    inv = p.get("inventory") or {}
    have = int(inv.get(slug, 0))
    fighting = bool(p.get("encounter"))
    item = economy.APOTHECARY.get(slug)

    if fighting:
        # In a fight the pack offers exactly what the fight offers: the
        # relic and quiver rows the encounter already earned.
        from . import tips
        opts = []
        for o in combat._relic_options(p):
            oslug = (o.id.removeprefix("nock_") if o.id.startswith("nock_")
                     else tips._FIGHT_RELIC.get(o.id, ""))
            if oslug == slug:
                opts.append(o)
        if slug == "trollblood_tonic" and have:
            opts.append(Option("drink_tonic", "Drink trollblood tonic",
                               "full heal"))
        if opts:
            return opts, ""
        if item and item.effect.startswith("heal_"):
            return [], ("Both hands are busy — only the trollblood tonic "
                        "goes down mid-fight. This keeps until it's over.")
        return [], "Nothing this one can do in the middle of this."

    # The salves: a number in the effect string ("heal_25"). The tonic's
    # "heal_full" is a fight item and answers below.
    if item and item.effect.startswith("heal_") \
            and item.effect != "heal_full" and have:
        amount = int(item.effect.rsplit("_", 1)[1])
        if p["hp"] >= state.max_hp(p):
            return [], ("You're whole. Keep it sealed for when you're "
                        "not — it heals the same at any level.")
        return [Option(f"use_{slug}", f"Use a {item.name}",
                       f"+{amount} HP · {have} left")], ""
    if slug == "luck_charm" and have:
        if p["flags"].get("luck_day") == state.world_day():
            return [], "Fortune already leans your way today."
        return [Option("use_luck_charm", "Break the luck charm",
                       f"better loot till tomorrow · {have} left")], ""
    if slug == "trollblood_tonic" and have:
        return [], "Saved for a fight — it is the only heal that works in one."
    if slug == "repair_token":
        return [], "The Forge spends it: one full mend, free."
    if slug in economy.RELICS:
        return [], "Carried into the fight — it offers itself when it can act."
    if slug in economy.FORGE:
        return [], "The Forge swaps gear in and out of the pack."
    return [], ""


def _pack_use(p: dict, oid: str) -> Scene | None:
    """027: a pack action taken from the strip — legal in any room, never
    in a fight. Returns None when the id isn't a pack action."""
    if oid not in PACK_USE_IDS or p.get("encounter"):
        return None
    slug = oid.removeprefix("use_")
    acts, why = pack_actions(p, slug)
    if not any(o.id == oid for o in acts):
        s = _build_scene(p)
        s.shard_note = why or "Nothing happens."
        return s
    if slug == "luck_charm":
        p["flags"]["luck_day"] = state.world_day()
        note = ("+ the charm cracks in your fist — fortune leans your way "
                "until tomorrow")
    else:
        item = economy.APOTHECARY[slug]
        amount = int(item.effect.rsplit("_", 1)[1])
        before = p["hp"]
        p["hp"] = min(state.max_hp(p), p["hp"] + amount)
        note = (f"+ {p['hp'] - before} HP — the {item.name.lower()} does "
                "its work.")
    p["inventory"][slug] -= 1
    if p["inventory"][slug] <= 0:
        del p["inventory"][slug]
    combat._ledger(p, "use", note=slug)
    s = _build_scene(p)
    s.body_lines.insert(0, note)
    return s


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

    # 027: two surfaces act from OUTSIDE the menu — the pack popup and the
    # notice board. Their ids are validated by the engine that owns them,
    # not by the row list, so they work from any room.
    used = _pack_use(p, option_id)
    if used is not None:
        return _stamp(p, used)

    # 030 Phase 5: the paper's ✕ — closing the Crier stamps the same
    # news_day guard the delivery keys on, so closed stays closed until
    # dawn. Valid wherever the paper shows, hence outside the row list.
    if option_id == "news_close":
        p["news_day"] = state.world_day()
        return _stamp(p, _build_scene(p))

    # 030 Phase 8: mid-reel every click is the next beat ("skip" cuts to
    # the arrival card). A stray id ("hunt" sent before the arrival card)
    # advances the frame instead of erroring — the reel only runs one
    # direction and nothing can wedge against it.
    if p.get("movie_floor"):
        return _stamp(p, _floor_movie_advance(p, option_id))

    scene = _build_scene(p)
    if p.get("location") in _NOTICE_ROOMS and not scene.enemy:
        doors = {nt["opt"] for nt in notices.pending(p)}
        if option_id in doors and option_id not in {o.id for o in scene.options}:
            # the notice row is a shortcut to the door: walk to the square
            # and open it, exactly as a player would with two clicks.
            p["location"] = "town"
            return _stamp(p, _dispatch(p, option_id))

    # 027: a picture tile is a row — the sigil grid's ids are as valid as
    # any option's, they just look like what they choose.
    valid = ({o.id for o in scene.options}
             | {str(g.get("opt", "")) for g in scene.gallery})
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

def _news_paper(p: dict) -> dict | None:
    """030 Phase 5: the Morning Crier is a PAPER pinned to the square,
    not an interstitial — it rides the town card until its ✕
    (news_close) stamps news_day. Data comes from worldd's injection —
    never invented."""
    if p["stage"] != "playing":
        return None
    w = p.get("_world") or {}
    if "census" not in w:
        return None
    day = state.world_day()
    if p.get("news_day", -1) >= day:
        return None
    return _paper_payload(p, w, day)


def _paper_payload(p: dict, w: dict, day: int) -> dict:
    frontier = int(w.get("frontier", 1))
    census = w.get("census") or {}
    by_floor = {int(k): int(v)
                for k, v in (census.get("by_floor") or {}).items()}
    total = int(census.get("total", 0))
    my_floor = p["floor"] if p["floor"] > 0 else frontier
    items = []
    # 022/004: noticed, never taught — the heal already happened in
    # touch_daily; the Crier only says what the body already knows.
    if p.get("daily", {}).get("dawn_healed"):
        items.append("dawn — your wounds have closed.")
    # 022/005: the night slot settled at the same boundary.
    ny = p.get("daily", {}).get("night_yield")
    if ny and ny.get("kind") == "work":
        items.append(f"the night shift paid ◈ {ny['gold']} while "
                     "you slept.")
    elif ny and ny.get("kind") == "rest":
        items.append(f"you wake rested — ✦ {ny['aether']} banked "
                     "toward your next kills.")
    # 030: headlines, not paragraphs — the sheet is small and every
    # item is clamped to two lines. Say it short.
    items.append(
        f"{total} climber{'s' if total != 1 else ''} on the Ascent · "
        f"{by_floor.get(frontier, 0)} at the frontier ({frontier}) · "
        f"{by_floor.get(my_floor, 0)} on floor {my_floor} with you")
    wd = w.get("warden")
    if wd and wd.get("hp_max"):
        pct = max(0, round(100 * int(wd["hp"]) / int(wd["hp_max"])))
        fl = schema.get_floor(int(wd["floor"]))
        blades = len(wd.get("strikers") or [])
        line = (f"{fl.warden_name} — {pct}% · floor {wd['floor']} · "
                + (f"{blades} blade{'s' if blades != 1 else ''}"
                   if blades else "no blades yet"))
        # 022/006: the clock rides the news when a wound is open
        if pct < 100 and wd.get("closes_in_s") is not None:
            from . import social as _social
            line += (" · closes in "
                     f"{_social._fmt_countdown(wd['closes_in_s'])}")
        items.append(line)
    gossip = w.get("gossip") or []
    if gossip:
        items += [g for g in gossip[:3]]
    else:
        items.append(f"floor {my_floor} was quiet — no news is its "
                     "own kind of news.")
    return {
        "headline": f"Day {day} on the Ascent — the frontier stands at "
                    f"floor {frontier}",
        "items": items,
        "closable": True,
    }


def _quorum(p: dict, floor: int) -> int:
    """022/002: the milestone war party rides the N(F) curve, sized to
    the live census when a world is attached."""
    w = p.get("_world") or {}
    active = int((w.get("census") or {}).get("total", 0)) or None
    return economy.milestone_quorum(floor, active)


# ── Presence (022 §003) — who is on the floor RIGHT NOW ──────────────────
# Data helpers live in state.py (combat needs them too); the prose
# assemblies below are the town-side surfaces.

def _presence_gate_hint(p: dict, floor: int) -> str:
    """' · 3 hot · 2 camps' for the gate list; '' when the floor is
    empty or the world is dark."""
    hot, camped = state.presence_counts(p, floor)
    parts = []
    if hot:
        parts.append(f"{hot} hot")
    if camped:
        parts.append(f"{camped} camp{'s' if camped != 1 else ''}")
    return (" · " + " · ".join(parts)) if parts else ""


def _presence_floor_lines(p: dict, floor: int) -> list[str]:
    """The floor card's presence block: the headline count, the named
    torches, and the deltas since last look."""
    if "presence" not in (p.get("_world") or {}):
        return []
    hot, camped = state.presence_counts(p, floor)
    lines: list[str] = []
    if hot > 1:
        lines.append(f"{hot} blades hot on this floor.")
    elif camped:
        lines.append(f"{camped} camp{'s' if camped != 1 else ''} "
                     "within the hour — embers, not company.")
    for t in state.presence_torches(p, floor)[:6]:
        lines.append(f"· {t.get('name', 'a climber')}'s torch — "
                     f"{t.get('status', 'on the move')}")
    lines += state.presence_delta_lines(p, floor)
    return lines


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
                f"to a war party of {_quorum(p, frontier)}. Pledge your "
                "blade and rally others.")
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
    # 030 Phase 8: mid-movie a refresh replays the current beat; the
    # Skip on the card is how a player cuts it short.
    if p.get("movie_floor"):
        return _floor_movie_scene(p)
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
        "board": _board_scene,
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
    if p.get("movie_floor"):
        return _floor_movie_advance(p, oid)
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
        support="Two to twenty-four letters the granite can hold.",
        shard_note="Choose one you'd want carved where everyone reads it.",
        options=[],
        awaits_text="the character's name",
        ask={"kind": "text", "max": 24, "label": "your name",
             "placeholder": "what the Stone should carve",
             "submit": "CARVE IT"},
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

def _door_open(p: dict, lvl: int) -> bool:
    """022/007: reincarnated hands open the convenience doors (Arcanum,
    Relay) from level 1 — prestige buys time, never power. Everything
    else keeps its level."""
    return p["level"] >= lvl or state.prestige(p) > 0


def _town_waiting(p: dict, w: dict) -> dict[str, int]:
    """0.29.2/027: collect badges — how many things WAIT behind each door.
    One projection of engine/notices.py, so a chip and the notice board's
    sentence can never disagree. A badge is a finished claim or an expiring
    slot, never mere availability (a badge that's always on is a badge
    nobody reads)."""
    return notices.doors(p, w)


def _town_scene(p: dict) -> Scene:
    w = p.get("_world") or {}
    lines = []
    # 030 Phase 5: the raw happenings dump is gone — the same news arrives
    # once, typeset, on the Crier's paper below.
    paper = _news_paper(p)
    # 020: the nearest unlock — and any protection that dies with it —
    # always readable from the square. The full ladder is at the Stone.
    nxt = unlocks.next_line(p)
    if nxt:
        lines.append(nxt)
    waiting = _town_waiting(p, w)

    def _b(door: str) -> int:
        return int(waiting.get(door, 0))

    # 007 town readability: the gate leads — leaving town is THE verb —
    # and every not-yet area reads its unlock level from the square
    # (the Arcanum set the pattern in 004).
    opts = [
        Option("gate", "The Tower Gate", "leave town and climb"),
        Option("forge", "The Forge", "gear", badge=_b("forge")),
        Option("arcanum", "The Arcanum",
               "mage gear" if _door_open(p, economy.ARCANUM_LEVEL)
               else f"🔒 level {economy.ARCANUM_LEVEL}",
               locked=not _door_open(p, economy.ARCANUM_LEVEL)),
        Option("medlab", "Apothecary & Medlab", "potions"),
        Option("board", "The contract board",
               "three jobs a day" if p["level"] >= economy.BOARD_LEVEL
               else f"🔒 level {economy.BOARD_LEVEL}",
               locked=p["level"] < economy.BOARD_LEVEL,
               badge=_b("board")),
        Option("lodge", "The Lodge",
               f"◈ {economy.LODGE_PRICE_PER_LEVEL * p['level']}/night",
               badge=_b("lodge")),
        Option("vault", "The Vault", "bank", badge=_b("vault")),
        Option("pawn", "Pawn shop", "sell"),
        # 012: the Guildhall is core — training (buying levels) lives
        # there, so it must exist even without a connected world.
        Option("guildhall", "The Guildhall",
               p.get("guild") or "training", badge=_b("guildhall")),
        Option("stone", "Stone of the Climb", "news"),
    ]
    if w:
        inbox = w.get("inbox_count", 0)
        opts.append(Option(
            "relay", "The Relay Office",
            (f"{inbox} letter{'s' if inbox != 1 else ''}" if inbox
             else "post") if _door_open(p, economy.RELAY_LEVEL)
            else f"🔒 level {economy.RELAY_LEVEL}",
            locked=not _door_open(p, economy.RELAY_LEVEL),
            badge=_b("relay")))
        opts.append(Option(
            "fields", "The fields",
            "pvp" if p["level"] >= economy.FIELDS_LEVEL
            else f"🔒 level {economy.FIELDS_LEVEL}",
            locked=p["level"] < economy.FIELDS_LEVEL))
    return Scene(
        eyebrow="ROOTHOLLOW · THE SQUARE",
        headline=f"Roothollow — floor {max(1, p['unlocked_floor'])} is the "
                 "frontier",
        support="The last free settlement. Everything starts and restarts here.",
        # the sidekick still reads the day's paper and says where the
        # climb is — advice belongs to the shard, news to the Crier.
        shard_note=(_news_advice(p, w, int(w.get("frontier", 1)),
                                 w.get("warden")) if paper else ""),
        body_lines=lines,
        options=opts,
        meters=combat.meters(p),
        banner="roothollow",
        paper=paper,
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
                  "stone", "gate", "relay", "fields", "guildhall", "board")
    if loc == "town" and oid in town_menus:
        if oid == "arcanum" and not _door_open(p, economy.ARCANUM_LEVEL):
            s = _town_scene(p)
            s.shard_note = (
                "The Arcanum's door reads the hand on it — it wants "
                f"level {economy.ARCANUM_LEVEL}. Climb first; the "
                "star-charts will keep.")
            return s
        # 007: the other locked doors follow the Arcanum's grammar —
        # a level, a reason, no scene change.
        if oid == "relay" and not _door_open(p, economy.RELAY_LEVEL):
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
        if oid == "board" and p["level"] < economy.BOARD_LEVEL:
            s = _town_scene(p)
            s.shard_note = (
                "The board hangs work for names it trusts — level "
                f"{economy.BOARD_LEVEL} first. The jobs will keep; "
                "new ones every dawn.")
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
    if loc == "board":
        return _board_action(p, oid)
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
    lvl, ufl = p["level"], p["unlocked_floor"]

    def _open(g):
        return (economy.rung_player_level_req(g) <= lvl
                and economy.rung_floor_req(g) <= ufl)

    buyable = [g for g in items if _open(g)]
    nxt = next((g for g in items if not _open(g)), None)
    worn = p["gear"].get(items[0].slot) if items else None
    # the two newest steps stay, and the worn rung keeps its row even
    # when it sits below them — a spare is always on sale
    show = [g for g in buyable if g.slug != worn][-2:]
    if worn and any(g.slug == worn for g in buyable) \
            and all(g.slug != worn for g in show):
        show.append(next(g for g in buyable if g.slug == worn))
        show.sort(key=lambda g: g.rung)
    def _stat(g):
        return ("+{} spd".format(g.speed) if g.slot == "shoes"
                else ("+{} ATK".format(g.bonus) if g.slot == "weapon"
                      else "+{} DEF".format(g.bonus)))

    for g in show:
        hint = (f"◈ {g.price:,} · worn — buy a spare"
                if g.slug == worn else f"◈ {g.price:,}")
        opts.append(Option(f"buy_{g.slug}", g.name, hint))
        flavor = f", {g.flavor}" if g.flavor else ""
        lines.append(f"{g.name}{flavor} — {_stat(g)}")
        # 025 §4: the newest rung is also a CHOICE — the same steel cut
        # keen (sharper, spends itself) or warded (patient). Older rungs
        # stay one row so the rack never becomes a catalogue.
        if g is show[-1]:
            for v in economy.gear_styles(g):
                opts.append(Option(f"buy_{v.slug}", v.name,
                                   f"{economy.STYLE_WORD[v.style]} · "
                                   f"◈ {v.price:,}"))
                lines.append(f"{v.name} — {_stat(v)}, {v.flavor}")
    if nxt is not None:
        stat = (f"+{nxt.speed} spd" if nxt.slot == "shoes"
                else f"+{nxt.bonus}")
        # 022/002: past the level cap the gate is the WORLD's floor,
        # not your level — the locked row says which one bars it.
        freq = economy.rung_floor_req(nxt)
        gate = (f"floor {freq}" if freq > p["unlocked_floor"]
                else f"level {economy.rung_player_level_req(nxt)}")
        opts.append(Option(
            f"buy_{nxt.slug}", nxt.name,
            f"🔒 {gate} · ◈ {nxt.price:,}", locked=True))
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
        g = economy.off_class_offer(line, p["level"], p["unlocked_floor"])
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
    # 0.29.4: a held repair token adds a FREE row per worn piece — the
    # token finally spends where its name promised.
    tokens = p["inventory"].get("repair_token", 0)
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
        if tokens > 0:
            opts.append(Option(
                f"token_{slot}",
                f"Mend {g.name} with a token",
                f"free — {tokens} held"))
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


def _forge_token_mend(p: dict, slot: str) -> Scene:
    """0.29.4: spend an armor-repair token — one worn piece made whole,
    no gold, no XP. The token's whole identity."""
    g = economy.FORGE.get(p["gear"].get(slot) or "")
    left = (p.get("durability") or {}).get(slot)
    if (not g or g.price <= 0 or left is None
            or p["inventory"].get("repair_token", 0) <= 0):
        return _forge_scene(p)
    pool = economy.item_pool(g)
    if left >= pool:
        return _forge_scene(p)
    p["inventory"]["repair_token"] -= 1
    if p["inventory"]["repair_token"] <= 0:
        del p["inventory"]["repair_token"]
    p["durability"][slot] = pool
    combat._ledger(p, "repair", note=f"{slot} (token)")
    s = _forge_scene(p)
    s.body_lines.insert(0, f"+ {g.name} made whole — the smith takes "
                        "the token and asks nothing else")
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
    freq = economy.rung_floor_req(g)
    if freq > p["unlocked_floor"]:
        # 022/002: deep steel waits for the WORLD to climb there
        s = scene_fn(p)
        s.shard_note = (f"{g.name} is floor-{freq} work — the war has "
                        f"only opened floor {p['unlocked_floor']}. The "
                        "smith won't sell steel the tower hasn't earned.")
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
    if oid.startswith("token_") and oid.removeprefix("token_") in \
            economy.DURABILITY_SLOTS:
        return _forge_token_mend(p, oid.removeprefix("token_"))
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
    if not _door_open(p, economy.ARCANUM_LEVEL):
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
        g = economy.off_class_offer("sorcerer", p["level"],
                                    p["unlocked_floor"])
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


def _night_shift(day: int) -> str:
    """The night's work site — deterministic flavor, same for everyone."""
    return economy.NIGHT_SHIFTS[day % len(economy.NIGHT_SHIFTS)]


def _lodge_scene(p: dict) -> Scene:
    price = economy.LODGE_PRICE_PER_LEVEL * p["level"]
    lodged = p["lodged_until_day"] >= state.world_day() + 1
    opts = []
    if not lodged:
        opts.append(Option("sleep", "Pay for the night", f"◈ {price}"))
    if p["hp"] < state.max_hp(p):
        opts.append(Option("stew", "Hunter's stew",
                           f"◈ {economy.STEW_PRICE} · +{economy.STEW_HEAL_HP} HP"))
    body = [f"A night costs ◈ {price}. Banked gold can't buy it — "
            "carry coin.",
            # 022/004: dawn heals everyone everywhere — the Lodge
            # sells the one thing dawn doesn't: not being found.
            "Dawn closes wounds wherever you lie. The palisade "
            "is about who can FIND you before it does."]
    # 022/005: the night slot — one action per night, resolved at dawn.
    # 0.29.1: below the level it is SHOWN and locked — a visible door is
    # a reason to climb; an invisible one is nothing.
    if p["level"] < economy.NIGHT_SLOT_LEVEL:
        body.append("The night slot — one action a night: rest by the "
                    "fire or take a shift for coin at dawn.")
        opts.append(Option("night_slot", "The night slot",
                           f"🔒 level {economy.NIGHT_SLOT_LEVEL}",
                           locked=True))
    if p["level"] >= economy.NIGHT_SLOT_LEVEL:
        day = state.world_day()
        shift = _night_shift(day)
        night = p.get("night") or {}
        plan = night.get("choice") if night.get("day") == day else None
        if plan == "rest":
            body.append("Tonight: rest by the fire — the pool banks at "
                        "dawn.")
        elif plan == "work":
            body.append(f"Tonight: {shift} — coin at dawn.")
        else:
            body.append("No plan for tonight yet. One action a night — "
                        "rest it or work it.")
        if plan != "rest":
            opts.append(Option(
                "night_rest", "Tonight: rest",
                f"✦ {economy.night_rest_aether(p['level'])} banked at dawn"))
        if plan != "work":
            opts.append(Option(
                "night_work", f"Tonight: {shift}",
                f"◈ {economy.night_work_gold(max(1, p['unlocked_floor']))} "
                "at dawn"))
    # 022/008: the long fire — canned words only, no free chat.
    fire = (p.get("_world") or {}).get("fire")
    if fire is not None:
        body.append("▣ THE LONG FIRE")
        for f in fire[:5]:
            body.append(f"· {f.get('name', 'a climber')} — "
                        f"\u201c{f.get('word', '')}\u201d")
        if not fire:
            body.append("· embers and no company — say a word, someone "
                        "will read it")
        opts.append(Option("fire_word", "Sit the fire, say a word",
                           "canned words — the fire keeps five"))
        if any(f.get("name") and f.get("name") != p.get("name")
               for f in fire):
            opts.append(Option(
                "fire_stew", "Stand a stranger a stew",
                f"◈ {economy.FIRE_STEW_GOLD} · a letter with it"))
    # 030 Phase 6: the keeper has a mouth — how coin moves under this roof.
    opts.append(Option("talk", "Talk to the keeper", "free"))
    opts.append(Option("back", "Back to the square"))
    return Scene(
        eyebrow="ROOTHOLLOW · THE LODGE",
        headline="Sleep behind the palisade" if not lodged
                 else "Your bunk is paid through tonight",
        support="Skip the lodge and you sleep in the fields — where anyone "
                "may find you.",
        body_lines=body,
        options=opts,
        meters=combat.meters(p),
        banner="lodge",
    )


def _keeper_scene(p: dict) -> Scene:
    """030 Phase 6: the keeper tells stories of glory — how climbers
    under this roof turned nights of work into fortunes, over time.
    Every number is read off economy.py at build time; the prose
    rotates so a second ask is not a replay. This is the keeper's
    room — no shard chatter in it."""
    day = state.world_day()
    shift = _night_shift(day)
    work = economy.night_work_gold(max(1, p["unlocked_floor"]))
    rest = economy.night_rest_aether(p["level"])
    tellings = (
        [f"“Okko came through that door in rags — couldn't pay for a "
         "bunk, slept in the fields twice and got robbed twice. Then "
         f"she learned the night slot: take {shift}, ◈ {work} on the "
         "board at dawn, every dawn. A season of nights and she walked "
         "out in plate she paid for herself. Coin isn't found here — "
         "it's earned in rows, night after night.”"],
        [f"“Brand never swung harder than anyone. He just slept "
         f"smarter. A night by my fire banks ✦ {rest}, and it rides "
         f"out at +{round(economy.RESTED_XP_BONUS_PCT * 100)}% a kill "
         "till the pool runs dry — "
         f"{economy.RESTED_POOL_CAP_NIGHTS} nights' worth it holds, no "
         "more. He rested, he killed rested, he leveled a floor ahead "
         "of climbers twice his arm. Glory is a schedule.”"],
        [f"“Asha kept every coin she won in the Vault — "
         f"{round(economy.BANK_INTEREST_RATE * 100)}% a day it pays, "
         "stubs at dawn, regular as bells. Little numbers. She let "
         "them stack a hundred days while the fools carried their "
         "purses into the wilds and fed the grave-robbers. Her stubs "
         "bought the Guild a war banner. Patience is a weapon too.”"],
        [f"“Old Vell hauled every rusted blade back off the floors "
         "and sold on the broker's good days only — he pays "
         f"{round(economy.pawn_rate(day) * 100)}% of forge price "
         "today, and his mood IS the day. Vell read the moods a "
         "year straight and drank free the rest of his life. Spoils "
         "are wages, if you sell them like a merchant and not like "
         "a beggar.”"],
    )
    n = int(p["flags"].get("keeper_told", 0))
    p["flags"]["keeper_told"] = n + 1
    body = list(tellings[n % len(tellings)])
    if not p["flags"].get("met_keeper"):
        p["flags"]["met_keeper"] = True
        body.insert(0, "The keeper sets down the ledger and looks you "
                       "over once — a new name for the book.")
    return Scene(
        eyebrow="ROOTHOLLOW · THE LODGE",
        headline="The keeper leans on the counter",
        support="Ask again — there is always another way coin moves "
                "through this room.",
        body_lines=body,
        options=[Option("talk", "Ask for another telling", "free"),
                 Option("back", "Back to the square")],
        meters=combat.meters(p),
        banner="lodge",
    )


def _lodge_action(p: dict, oid: str) -> Scene:
    if oid == "talk":
        return _keeper_scene(p)
    if oid == "stew":
        return _eat_stew(p, _lodge_scene)
    if oid == "fire_word":
        # 022/008: pick tonight's canned line deterministically — no
        # free text, nothing to moderate.
        word = economy.FIRE_WORDS[
            state.rng_int(p, 0, len(economy.FIRE_WORDS) - 1)]
        from . import social
        social._effect(p, "fire_word", word=word)
        s = _lodge_scene(p)
        s.shard_note = f"You say it to the fire: \u201c{word}\u201d"
        return s
    if oid == "fire_stew":
        fire = (p.get("_world") or {}).get("fire") or []
        other = next((f["name"] for f in fire
                      if f.get("name") and f["name"] != p.get("name")), "")
        if not other:
            return _lodge_scene(p)
        if p["gold"] < economy.FIRE_STEW_GOLD:
            s = _lodge_scene(p)
            s.shard_note = (f"A stranger's stew is ◈ "
                            f"{economy.FIRE_STEW_GOLD} you don't carry.")
            return s
        p["gold"] -= economy.FIRE_STEW_GOLD
        from . import social
        social._effect(p, "fire_stew", to_name=other)
        combat._ledger(p, "fire_stew", gold=-economy.FIRE_STEW_GOLD,
                       note=other)
        s = _lodge_scene(p)
        s.shard_note = (f"A bowl goes across the fire to {other}. "
                        "They'll find the word with their post.")
        return s
    if oid == "night_slot" or (oid in ("night_rest", "night_work")
                               and p["level"] < economy.NIGHT_SLOT_LEVEL):
        s = _lodge_scene(p)
        s.shard_note = (f"The keeper plans nights for level "
                        f"{economy.NIGHT_SLOT_LEVEL} names. Climb — "
                        "the fire will still be here.")
        return s
    if oid in ("night_rest", "night_work"):
        p["night"] = {"day": state.world_day(),
                      "choice": "rest" if oid == "night_rest" else "work"}
        s = _lodge_scene(p)
        s.shard_note = ("The night is planned. Dawn settles it — one "
                        "action a night, no more.")
        return s
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
    s.body_lines.insert(0, "+ one safe night. Nothing finds you here "
                           "before dawn does its work.")
    return s


# ── The contract board (022 §004) ────────────────────────────────────────

def _board_scene(p: dict) -> Scene:
    """Three world jobs, the same three for every climber. No accept
    step: do the work, collect before dawn."""
    day = state.world_day()
    jobs = contracts.board_for(p)
    lines = []
    opts = []
    for job in jobs:
        n, need = contracts.got(p, job), job["need"]
        c = contracts.sync(p)
        if job["id"] in c["claimed"]:
            tail = "PAID"
        elif n >= need:
            tail = "done — collect below"
        else:
            tail = f"{n}/{need}"
        bonus = " · +1 repair token" if job.get("token") else ""
        # 0.29.1: the card shows what THIS hand collects (reach-capped),
        # never a frontier price a level-2 climber won't be paid.
        gold, xp = contracts.pay_for(p, job)
        lines.append(f"· {job['title']} — ◈ {gold} + "
                     f"{xp} XP{bonus} · {tail}")
        if contracts.claimable(p, job):
            opts.append(Option(f"claim_{job['id']}", f"Collect: {job['title']}",
                               f"◈ {max(0, gold - economy.BOARD_PRICE)}"))
    lines.append(f"The broker's stamp is ◈ {economy.BOARD_PRICE}, off the "
                 "top of every payout. Jobs expire at dawn — no rerolls.")
    opts.append(Option("back", "Back to the square"))
    return Scene(
        eyebrow="ROOTHOLLOW · THE CONTRACT BOARD",
        headline=f"Three jobs, day {day}",
        support="One board for the whole tower — every climber is reading "
                "these same three lines.",
        body_lines=lines,
        options=opts,
        meters=combat.meters(p),
        banner="roothollow",
    )


def _board_action(p: dict, oid: str) -> Scene:
    if oid.startswith("claim_"):
        jid = oid[len("claim_"):]
        for job in contracts.board_for(p):
            if job["id"] == jid and contracts.claimable(p, job):
                gold, xp = contracts.claim(p, job)
                combat._ledger(p, "contract", gold=gold, xp=xp,
                               note=job["title"])
                s = _board_scene(p)
                token = job.get("token")
                s.body_lines.insert(
                    0, f"+ ◈ {gold} + {xp} XP — the broker stamps the "
                       "job PAID"
                       + (" and slides a repair token across." if token
                          else "."))
                return s
    return _board_scene(p)


# ── Vault ────────────────────────────────────────────────────────────────

def _vault_scene(p: dict) -> Scene:
    # 023: interest lands as daily STUBS you collect, never a silent
    # credit — the pile is the reason to come back.
    stubs = state.interest_sync(p)
    lines = []
    lines.append(f"carried ◈ {p['gold']:,}")
    opts = []
    if stubs:
        if len(stubs) > 5:
            lines.append(f"…{len(stubs) - 5} older interest stubs, and:")
        for st in stubs[-5:]:
            lines.append(f"· day {st['day']} — ◈ {st['gold']:,} interest, "
                         "uncollected")
        total = sum(st["gold"] for st in stubs)
        opts.append(Option(
            "collect_interest",
            f"Collect interest ({len(stubs)} "
            f"stub{'s' if len(stubs) != 1 else ''})",
            f"◈ {total:,} to the bank"))
    # 022/005: the weekly strongbox. 0.29.1: below the level it is
    # SHOWN and locked — the clerk polishes a box you can't open yet.
    if p["level"] < economy.STRONGBOX_LEVEL:
        lines.append(f"the weekly strongbox — 🔒 level "
                     f"{economy.STRONGBOX_LEVEL}. Kills, keeps and "
                     "floors gained fill it; every week you pick one "
                     "reward from what you earned.")
    if p["level"] >= economy.STRONGBOX_LEVEL:
        box = weekly.sync(p)
        note = p.pop("strongbox_note", None)
        if note:
            lines.append(note)
        pts = weekly.points(p, box)
        n = weekly.slots(p)
        lines.append(f"strongbox — this week: {box['kills']} kills · "
                     f"{box['wardens']} keeps · "
                     f"{max(0, p['unlocked_floor'] - box['floor0'])} floors "
                     f"= {pts} points, {n} slot{'s' if n != 1 else ''} open "
                     f"(thresholds {'/'.join(map(str, economy.STRONGBOX_THRESHOLDS))}).")
        pending = box.get("pending")
        if pending:
            lines.append(f"last week's box is OPEN — {pending['slots']} "
                         "slot(s). Pick exactly one.")
            for o, label, hint in weekly.rewards(p, pending["slots"]):
                opts.append(Option(o, label, hint))
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
                "Interest lands daily as stubs — collect them and it "
                "compounds.",
        body_lines=lines,
        options=opts,
        meters=combat.meters(p),
        banner="vault",
        # 030 Phase 4: the deposit is a SHELF, not a sentence — one big
        # number over the strongbox art. The ◈ paints into the coin glyph
        # card-side; the text surface reads the line as written.
        strip={"art": "vault_interior",
               "text": f"DEPOSITED: ◈ {p['bank']:,}"},
    )


def _vault_action(p: dict, oid: str) -> Scene:
    if oid == "collect_interest":
        total = state.interest_collect(p)
        s = _vault_scene(p)
        if total > 0:
            combat._ledger(p, "interest", gold=total)
            s.body_lines.insert(0, f"+ ◈ {total:,} interest banked — the "
                                "clerk stamps every stub")
        return s
    if oid.startswith("pick_") and p["level"] >= economy.STRONGBOX_LEVEL:
        line = weekly.pick(p, oid)
        s = _vault_scene(p)
        if line:
            s.body_lines.insert(0, line + ". The box shuts for the week.")
        return s
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


def _pawn_sundry(p: dict, slug: str) -> tuple[str, int]:
    """Name and offer for the pack's small stuff — potions off their
    shop price, the repair token off its fixed worth."""
    rate = economy.pawn_rate(state.world_day())
    if slug == "repair_token":
        return ("repair token",
                max(1, int(economy.REPAIR_TOKEN_VALUE * rate)))
    it = economy.APOTHECARY[slug]
    return (it.name, max(1, int(it.price * rate)))


def _pawn_scene(p: dict) -> Scene:
    rate = economy.pawn_rate(state.world_day())
    gear_in_pack = [k for k in p["inventory"] if k in economy.FORGE]
    relics_in_pack = [k for k in p["inventory"] if k in economy.RELICS]
    # 006 §3.8: the pawn always buys ANYTHING — so potions and tokens
    # get a row too (0.29.4: they used to be invisible here, which read
    # as the broker refusing).
    sundries = [k for k in p["inventory"]
                if k in economy.APOTHECARY or k == "repair_token"]
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
    for slug in relics_in_pack:
        r = economy.RELICS[slug]
        offer = _pawn_relic_offer(p, slug)
        opts.append(Option(f"sell_{slug}", f"Sell {r.name}", f"◈ {offer:,}"))
        lines.append(f"{r.name} ×{p['inventory'][slug]} — offers ◈ {offer:,}")
    for slug in sundries:
        name, offer = _pawn_sundry(p, slug)
        opts.append(Option(f"sell_{slug}", f"Sell {name}", f"◈ {offer:,}"))
        lines.append(f"{name} ×{p['inventory'][slug]} — offers ◈ {offer:,}")
    if not gear_in_pack and not relics_in_pack and not sundries:
        lines.append("Empty pack. The broker buys ANYTHING you carry — "
                     "gear, relics, potions, tokens. Come back heavier.")
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
    if slug in p["inventory"] and (slug in economy.APOTHECARY
                                   or slug == "repair_token"):
        name, offer = _pawn_sundry(p, slug)
        p["inventory"][slug] -= 1
        if p["inventory"][slug] <= 0:
            del p["inventory"][slug]
        p["gold"] += offer
        combat._ledger(p, "pawn", gold=offer, note=slug)
        s = _pawn_scene(p)
        s.body_lines.insert(0, f"+ ◈ {offer:,} for the {name}")
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
    # 022/007: the Stone of Eras — the wars that already ended, kept
    # forever, readable in every era.
    eras = w.get("eras") or []
    if eras:
        lines.append("▣ THE STONE OF ERAS")
        for e in eras[:5]:
            lines.append(f"· {e}")
    # 020: the personal ladder — the whole climb ahead, grouped by
    # threshold. + opens, − closes, ▲ changes the rules.
    lines.append("▣ THE CLIMB AHEAD")
    # 025 §4: band 1 sells a rung a level now, so the fold carries a few
    # more rungs of ladder before it says "and the tower keeps the rest".
    lines.extend(unlocks.climb_ahead_lines(p, limit=14))
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
        # 020: an open floor above your legs is a LOCKED row that names
        # its level — not a live row that refuses after the click.
        req = economy.floor_entry_player_level(n)
        m = economy.MILESTONES.get(n)
        if p["level"] < req:
            hint = f"🔒 level {req} legs"
        else:
            hint = fl.gate_town
        if m is not None:
            hint += f" · war party of {_quorum(p, n)}"
        # 022/003: who is up there right now — "Floor 12 · 3 hot · 2 camps"
        hint += _presence_gate_hint(p, n)
        opts.append(Option(f"floor_{n}", f"Floor {n} — {fl.zone}",
                           hint, locked=p["level"] < req))
    opts.append(Option("back", "Back to the square"))
    # 022/006: an open wound is news at the gate itself — "the war is
    # on floor 47" before anyone picks a floor.
    lines = []
    wd = (p.get("_world") or {}).get("warden") or {}
    if wd and int(wd.get("hp", 0)) < int(wd.get("hp_max", 0)):
        pct = max(0, round(100 * int(wd["hp"]) / max(1, int(wd["hp_max"]))))
        lines.append(f"the war is on floor {wd['floor']} — the Warden "
                     f"stands at {pct}%")
    return Scene(
        eyebrow="ROOTHOLLOW · THE TOWER GATE",
        headline=f"{top} floor{'s' if top > 1 else ''} stand open",
        support="Pick any opened floor. The grind pays best near your level.",
        body_lines=lines,
        options=opts,
        meters=combat.meters(p),
        banner="gate",
    )


# ── 030 Phase 8: the floor movie ─────────────────────────────────────────
# A 2-3 beat scripted entry on the 016 intro pattern (fx + headline +
# body + Next), exactly once per floor per character. Floors with loop
# GIFs (1-10, law 1) animate; everywhere else the fx slug misses and the
# still banner carries the beat — one code path, only the motion differs.

def _floor_movie_scene(p: dict) -> Scene:
    n = int(p["movie_floor"])
    fl = schema.get_floor(n)
    beat = int(p.get("movie_beat", 0))
    if beat == 0:
        body = [fl.arrival]
        npc = getattr(fl, "npc", None)
        if npc is not None:
            body.append(npc.lore)
        return Scene(
            eyebrow=f"FLOOR {n} · {fl.zone.upper()} · I",
            headline=f"{fl.biome} — {fl.zone}",
            body_lines=body,
            options=[Option("next", "Next"),
                     Option("skip", "Skip")],
            fx=f"floor{n}_world",
            banner=fl.banner,
        )
    w = p.get("_world") or {}
    frontier = int(w.get("frontier", p["unlocked_floor"]))
    if frontier > n:
        # the warden fell — same art under the shared demise treatment,
        # and the text names WHO, when the world remembers.
        names = ((w.get("warden") or {}).get("fallen_by")
                 or {}).get(str(n), "")
        by = (f"Broken by {names}." if names
              else "Broken by a war party of climbers.")
        return Scene(
            eyebrow=f"FLOOR {n} · THE KEEP · II",
            headline=f"{fl.warden_name} has already fallen",
            body_lines=[f"{fl.warden_name} held this lift once. {by}",
                        "The lift above runs free. The floor is yours "
                        "to hunt."],
            options=[Option("next", "Next"),
                     Option("skip", "Skip")],
            fx="warden_fall",
            banner=f"warden_{n:03d}",
        )
    return Scene(
        eyebrow=f"FLOOR {n} · THE KEEP · II",
        headline=f"{fl.warden_name} holds the lift",
        body_lines=[fl.warden_prose,
                    f"{fl.warden_name} — ATK {fl.warden_atk} · DEF "
                    f"{fl.warden_def} · {fl.warden_hp:,} HP. The stair "
                    "stays shut while it stands."],
        options=[Option("next", "Next"),
                 Option("skip", "Skip")],
        fx=f"floor{n}_warden",
        banner=f"warden_{n:03d}",
    )


def _floor_movie_advance(p: dict, oid: str = "next") -> Scene:
    """Next steps a beat; Skip (on every beat) cuts straight to the
    arrival card. Either way the floor counts as seen — the movie
    plays once, skipped or watched."""
    n = int(p["movie_floor"])
    beat = int(p.get("movie_beat", 0))
    if oid != "skip" and beat < 1:
        p["movie_beat"] = beat + 1
        return _floor_movie_scene(p)
    p["flags"][f"floor_seen_{n}"] = True
    p.pop("movie_floor", None)
    p.pop("movie_beat", None)
    return _floor_arrival_scene(p, n)


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
    # 030 Phase 8: the first time a character sets foot on a floor —
    # old name or new — the floor introduces itself: a short movie,
    # once per floor, skippable on every beat.
    if not p["flags"].get(f"floor_seen_{n}"):
        p["movie_floor"], p["movie_beat"] = n, 0
        return _floor_movie_scene(p)
    return _floor_arrival_scene(p, n)


def _floor_arrival_scene(p: dict, n: int) -> Scene:
    fl = schema.get_floor(n)
    lines = [fl.arrival]
    lines += _presence_floor_lines(p, n)
    # 020: the floor BELOW a milestone warns at the gate, before the
    # ⚡ is spent — this floor's own Warden is one thing, the next is a
    # war party's work.
    m = economy.MILESTONES.get(n + 1)
    if m is not None:
        lines.append(f"▲ Word from above: {m.name} holds floor {n + 1}. "
                     f"No solo kill — a war party of {_quorum(p, n + 1)} "
                     f"pledges {economy.COST_BOSS_COMMIT} ⚡ each at the "
                     "Guildhall.")
    return Scene(
        eyebrow=f"FLOOR {n} · {fl.biome.upper()} · {fl.gate_town.upper()}",
        headline=f"{fl.gate_town} — the floor's last safe fire",
        support="A healer, a rumor bench, and the wilds beyond the wire.",
        body_lines=lines,
        options=_gate_town_options(p, fl),
        meters=combat.meters(p),
        banner=fl.banner,
    )


def _live_flare(p: dict) -> dict | None:
    """022/008: the floor's open flare, if it is someone else's and
    still unanswered — the only state an answerer may act on."""
    fw = (p.get("_world") or {}).get("flare")
    if fw and not fw.get("own") and not fw.get("answered_by"):
        return fw
    return None


def _gate_town_options(p: dict, fl) -> list[Option]:
    heal_price = economy.HEALER_TENT_PER_FLOOR * fl.floor
    opts = [Option("hunt", "Hunt the wilds", "1 ⚡")]
    if _live_flare(p):
        opts.insert(0, Option("answer_flare", "Answer the flare",
                              "1 ⚡ · run toward the light"))
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
    # 030 Phase 6: the floor's one voice — floors without an npc block
    # (11-100, until their art pass) simply have no talk row.
    npc = getattr(fl, "npc", None)
    if npc is not None:
        opts.append(Option("talk", f"Talk — {npc.name}", npc.role))
    opts.append(Option("town", "Return to Roothollow"))
    return opts


def _npc_scene(p: dict, fl) -> Scene:
    """030 Phase 6: the gate town's local speaks. YAML prose is
    numberless; the warden's strength is said in derived numbers
    (economy.warden_stats via the Floor row) and the tone is keyed to
    whether that warden still stands."""
    npc = fl.npc
    flag = f"met_npc_{fl.floor}"
    body = []
    if not p["flags"].get(flag):
        p["flags"][flag] = True
        body.append(npc.greet)
    body.append(npc.lore)
    body.append("Out past the wire: "
                + ", ".join(e.name for e in fl.encounters) + ".")
    w = p.get("_world") or {}
    frontier = int(w.get("frontier", p["unlocked_floor"]))
    if frontier > fl.floor:
        body.append(f"“{fl.warden_name} fell — the lift above runs free, "
                    "and this floor breathes easier for it. Thank you "
                    "for every blade that helped.”")
    else:
        body.append(npc.warn)
        body.append(f"{fl.warden_name} — ATK {fl.warden_atk} · "
                    f"DEF {fl.warden_def} · {fl.warden_hp:,} HP. "
                    "That's the shape of it. Walk in knowing.")
    return Scene(
        eyebrow=f"FLOOR {fl.floor} · {fl.gate_town.upper()}",
        headline=f"{npc.name} — {npc.role}",
        support="Talking is free. Listening is what saves you.",
        body_lines=body,
        options=_gate_town_options(p, fl),
        meters=combat.meters(p),
        banner=fl.banner,
    )


def _gate_town_scene(p: dict) -> Scene:
    fl = schema.get_floor(max(1, p["floor"]))
    body = _presence_floor_lines(p, fl.floor)
    fw = _live_flare(p)
    if fw:
        body.insert(0, f"▪ a RED FLARE hangs over the wilds — "
                       f"{fw.get('name', 'a climber')} is dying out "
                       f"there, {fw.get('monster', 'something')} on them.")
    return Scene(
        eyebrow=f"FLOOR {fl.floor} · {fl.biome.upper()} · {fl.gate_town.upper()}",
        headline=f"{fl.gate_town}",
        support="The fire is small but honest. Beyond the wire, the wilds.",
        body_lines=body,
        options=_gate_town_options(p, fl),
        meters=combat.meters(p),
    )


def _gate_town_action(p: dict, oid: str) -> Scene:
    fl = schema.get_floor(max(1, p["floor"]))
    if oid == "talk" and getattr(fl, "npc", None) is not None:
        return _npc_scene(p, fl)
    if oid == "answer_flare":
        fw = _live_flare(p)
        if fw is None:
            s = _gate_town_scene(p)
            s.shard_note = ("The flare has guttered out — or another "
                            "blade got there first.")
            return s
        if not state.spend_energy(p, economy.COST_WILDS_FIGHT):
            s = _gate_town_scene(p)
            s.shard_note = "Even a rescue takes ⚡ — you're spent."
            return s
        # the claim races other answerers server-side; first tap wins
        # the pay and the Stone line, everyone who ran still fights.
        from . import social
        social._effect(p, "flare_answer", floor=fl.floor)
        combat._ledger(p, "energy", note="flare answer")
        enc = next((e for e in fl.encounters
                    if e.id == fw.get("slug")), None)
        if enc is None:
            enc_id = state.rng_pick(p, combat.hunt_table(p, fl))
            enc = next(e for e in fl.encounters if e.id == enc_id)
        s = combat.start_encounter(p, fl, enc, "wilds")
        s.support = (f"You run toward the light. The {enc.name} turns "
                     f"from {fw.get('name', 'a climber')} to you — "
                     "the rescuer's round.")
        return s
    if oid == "hunt":
        if not state.spend_energy(p, economy.COST_WILDS_FIGHT):
            s = _gate_town_scene(p)
            s.shard_note = ("You're spent — ⚡ regenerates one point every "
                            "45 minutes. Rest, bank, or read the Stone.")
            return s
        # 025 §5: the rubber band weights the roster against your sheet
        enc_id = state.rng_pick(p, combat.hunt_table(p, fl))
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
    # 027: use_* is one law in one place now (_pack_use), reachable from the
    # pack strip in any room — the camp fire keeps its menu row, the
    # handler moved upstream.
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
        # below the frontier: the ECHO bout — a monument that still
        # bites, half pay, no world effect (022/001). Local dev play
        # (no world) keeps the real bout: a world of one.
        if not state.spend_energy(p, economy.COST_WARDEN_ATTEMPT):
            s = _gate_town_scene(p)
            s.shard_note = "A Warden takes 3 ⚡ you don't have. The wilds " \
                           "cost less."
            return s
        s = combat.start_encounter(p, fl, None, "warden")
        if w:
            p["encounter"]["echo"] = True
            s.support = ("An echo of a fallen Warden — half pay, no "
                         "world effect. The real one died long ago.")
        return s
    if oid == "gate":
        p["location"] = "gate"
        return _gate_scene(p)
    return _gate_town_scene(p)
