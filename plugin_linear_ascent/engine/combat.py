"""Combat resolver — economy §2–§3 math, deterministic rolls.

The encounter lives in the player doc; every function mutates the doc and
returns a Scene. Flows are gated here, not in prose: out-of-order calls
never reach these functions (core.py dispatches).
"""

from __future__ import annotations

import os

from .. import economy
from . import state
from .scene import Meters, Option, Scene

_CREATURES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "..", "content", "art", "creatures")


def _creature_art(slug: str) -> bool:
    return any(os.path.exists(os.path.join(_CREATURES, f"{slug}_{s}.png"))
               for s in ("320x112", "320x200"))


def _opener_banner(e: dict, floor) -> str:
    """Creature's own art if shipped (plan 005), else the old behavior."""
    if e["kind"] == "warden":
        if floor.floor % 10 == 0:  # milestone boss banners ship in banners/
            return "gnarl" if floor.floor == 10 else floor.banner
        slug = f"warden_{floor.floor:03d}"
        return slug if _creature_art(slug) else ""
    slug = e.get("id", "")
    if slug and _creature_art(slug):
        return slug
    return floor.banner if e["kind"] == "wilds" else ""


def meters(p: dict) -> Meters:
    return Meters(
        hp=p["hp"], hp_max=state.max_hp(p),
        energy=state.energy_now(p),
        energy_max=economy.energy_cap(p["level"], p.get("race") or ""),
        xp=p["xp"],
        xp_need=economy.xp_need(p["level"]),
        gold=p["gold"])


def _eyebrow(p: dict, floor) -> str:
    return f"FLOOR {floor.floor} · {floor.biome.upper()} · {floor.zone.upper()}"


def _ledger(p: dict, kind: str, gold: int = 0, xp: int = 0, note: str = "") -> None:
    p.setdefault("_ledger", []).append(
        {"kind": kind, "gold": gold, "xp": xp, "note": note})


def start_encounter(p: dict, floor, enc, kind: str = "wilds") -> Scene:
    if kind == "warden":
        if floor.milestone and floor.floor == 10:
            # Solo-tuned fallback: the real quorum fight arrives with guilds.
            atk, dfs, hp = economy.warden_stats(floor.floor)
            name = floor.warden_name
        else:
            atk, dfs, hp = economy.warden_stats(floor.floor)
            name = floor.warden_name
        prose = floor.warden_prose
    else:
        atk, dfs, hp = floor.monster_atk, floor.monster_def, floor.monster_hp
        name, prose = enc.name, enc.prose
    p["encounter"] = {
        "kind": kind, "name": name, "prose": prose,
        "id": (enc.id if enc is not None else ""),
        "atk": atk, "def": dfs, "hp": hp, "hp_max": hp,
        "floor": floor.floor, "shot_used": False,
    }
    return fight_scene(p, floor, opener=True)


def _shard_advice(p: dict, floor) -> str:
    """Insight-scaled whisper — sometimes wrong, on purpose."""
    e = p["encounter"]
    insight = p["sidekick"]["insight"]
    correct = state.roll_ok(p, 0.5 + 0.05 * insight)
    stronger = e["atk"] > state.atk(p)
    if not correct:
        stronger = not stronger
    if e["kind"] == "warden":
        return ("This one guards the stair. Hit it before it settles."
                if not stronger else
                "Its frame outweighs yours. Keep your shield arm honest.")
    return ("Its guard is lower than yours — press it."
            if not stronger else
            "That thing hits harder than you do. Running costs pride, not gold.")


def fight_scene(p: dict, floor, opener: bool = False, note: str = "") -> Scene:
    e = p["encounter"]
    opts = [
        Option("attack", "Attack"),
        Option("stand", "Stand your ground"),
        Option("run", "Run"),
    ]
    clazz = p.get("clazz")
    if clazz == "warrior":
        opts.append(Option("shield_wall", "Shield wall", "class", aether=True))
    elif clazz == "sorcerer":
        opts.append(Option("sleep_spell", "Sleep spell",
                           f"class · ✦ {economy.sleep_xp_cost(floor.floor)}",
                           aether=True))
    elif clazz == "archer" and not e["shot_used"]:
        opts.append(Option("treeline_shot", "Treeline shot", "class", aether=True))
    if p["inventory"].get("trollblood_tonic"):
        opts.append(Option("drink_tonic", "Drink trollblood tonic", "full heal"))
    charges = p["sidekick"]["scout_charges"]
    opts.append(Option(
        "scout", "Ask the shard to scan it",
        f"{charges} charges" if charges > 0
        else f"✦ {economy.scan_xp_cost(floor.floor)}",
        aether=True))

    body = [e["prose"]] if opener else []
    if note:
        body.append(note)
    return Scene(
        eyebrow=_eyebrow(p, floor),
        headline=f"{e['name']} — ATK {e['atk']} / DEF {e['def']}"
                 + (f" / HP {e['hp']}/{e['hp_max']}" if not opener else ""),
        support="It is between you and the way forward.",
        shard_note=_shard_advice(p, floor) if opener else "",
        body_lines=body,
        options=opts,
        meters=meters(p),
        banner=_opener_banner(e, floor) if opener else "",
        event_kind="boss" if e["kind"] == "warden" else "",
    )


def _monster_hit(p: dict, halved: bool = False) -> int:
    e = p["encounter"]
    day = state.world_day()
    raw = state.rng_int(p, e["atk"] // 2, e["atk"])
    dmg = max(0, raw - state.dfs(p) // 2)
    if halved:
        dmg //= 2
    p["hp"] -= dmg
    return dmg


def _player_hit(p: dict, mult: float = 1.0) -> int:
    e = p["encounter"]
    raw = state.rng_int(p, state.atk(p) // 2, state.atk(p))
    dmg = max(0, round(raw * mult) - e["def"] // 2)
    e["hp"] -= dmg
    return dmg


def _level_ups(p: dict) -> list[str]:
    lines = []
    while p["xp"] >= economy.xp_need(p["level"]):
        p["xp"] -= economy.xp_need(p["level"])
        p["level"] += 1
        p["hp"] = state.max_hp(p)
        lines.append(f"LEVEL {p['level']} — your frame remembers how to be "
                     "stronger. Wounds close.")
    return lines


def _victory(p: dict, floor) -> Scene:
    e = p["encounter"]
    fade = economy.fade_multiplier(p["unlocked_floor"], floor.floor)
    if e["kind"] == "warden":
        xp = round(economy.warden_xp(floor.floor) * fade)
        gold = round(economy.warden_gold(floor.floor) * fade)
        if floor.milestone:
            xp = round(floor.milestone.xp / 2 * fade)
            gold = round(floor.milestone.gold / 2 * fade)
    else:
        xp = round(state.rng_jitter(p, economy.xp_per_kill(floor.floor), 0.25) * fade)
        lucky = (p.get("race") == "halfling" or
                 p["flags"].get("luck_day") == state.world_day())
        gold = round(state.rng_jitter(p, economy.gold_per_kill(floor.floor),
                                      0.50 if not lucky else 0.25) * fade)
    if p.get("race") == "elf":
        xp = round(xp * (1 + economy.ELF_XP_BONUS))
    p["xp"] += xp
    p["gold"] += gold
    _ledger(p, "kill", gold=gold, xp=xp, note=e["name"])
    lines = [f"The {e['name']} goes down.",
             f"+ {xp} experience", f"+ ◈ {gold} carried gold"]
    lines += _level_ups(p)

    first_clear = False
    if e["kind"] == "warden":
        nxt = floor.floor + 1
        if p["unlocked_floor"] < nxt:
            p["unlocked_floor"] = nxt
            first_clear = True
            lines.append(f"The lift grinds open. FLOOR {nxt} is yours to enter.")
            if p.get("_world") is not None:
                p.setdefault("_effects", []).append({
                    "kind": "happening",
                    "line": (f"{p.get('name') or 'A climber'} cast down "
                             f"{e['name']} — floor {nxt} opens for them")})
        # guaranteed rare-loot roll
        loot = state.rng_pick(p, [(60, "trollblood_tonic"), (40, "luck_charm")])
        p["inventory"][loot] = p["inventory"].get(loot, 0) + 1
        lines.append(f"▪ rare loot: {economy.APOTHECARY[loot].name}")
    p["encounter"] = None
    p["location"] = "gate_town"
    kind = "boss" if e["kind"] == "warden" else "loot"
    return Scene(
        eyebrow=_eyebrow(p, floor),
        headline=(f"{e['name']} defeated"
                  + (" — the floor is opened" if first_clear else "")),
        support="The wilds go quiet around you." if e["kind"] == "wilds"
                else "The Warden's frame ticks as it cools.",
        body_lines=lines,
        options=_after_fight_options(p, floor),
        meters=meters(p),
        event_kind=kind,
    )


def _after_fight_options(p: dict, floor) -> list[Option]:
    opts = [Option("hunt", "Hunt the wilds again", "1 ⚡")]
    if p["unlocked_floor"] > floor.floor:
        opts.append(Option("gate", "Back to the tower gate"))
    opts.append(Option("keep", "The Warden's keep", "3 ⚡"))
    opts.append(Option("town", "Return to Roothollow"))
    return opts


def _death(p: dict, floor) -> Scene:
    e = p["encounter"]
    daily = p["daily"]
    if not daily.get("death_save"):
        daily["death_save"] = True
        p["hp"] = 1
        p["encounter"] = None
        p["location"] = "gate_town"
        return Scene(
            eyebrow=_eyebrow(p, floor),
            headline="Your shardmind drags you out",
            support="Everything goes white, then very loud, then quiet.",
            shard_note="I have you. Once a day, I have you. Do not spend it "
                       "like this again.",
            body_lines=[f"The {e['name']} loses you in the grass.",
                        "You are at 1 HP. The gate town is close."],
            options=[Option("heal", "The healer's tent", f"◈ {2 * floor.floor}"),
                     Option("town", "Limp back to Roothollow")],
            meters=meters(p),
            event_kind="death",
        )
    mercy = p["level"] <= economy.BEGINNER_MERCY_MAX_LEVEL
    if mercy:
        # 004 §A.2: a bad first hour can't spiral — keep armor and
        # shield, lose only half the carried gold.
        lost_gold = p["gold"] - p["gold"] // 2
        p["gold"] //= 2
        broken: list[str] = []
    else:
        lost_gold = p["gold"]
        p["gold"] = 0
        broken = [s for s in ("armor", "shield") if p["gear"].get(s)]
        for slot in broken:
            p["gear"][slot] = None
    _ledger(p, "death", gold=-lost_gold, note=e["name"])
    if p.get("_world") is not None:
        p.setdefault("_effects", []).append({
            "kind": "happening",
            "line": (f"{p.get('name') or 'A climber'} fell to a "
                     f"{e['name']} on floor {floor.floor}")})
    p["encounter"] = None
    p["location"] = "town"
    p["floor"] = 0
    p["hp"] = state.max_hp(p)
    lines = [f"Killed by the {e['name']}."]
    if lost_gold:
        lines.append(f"− ◈ {lost_gold} carried gold, gone")
    if broken:
        lines.append("▪ " + " and ".join(broken) + " destroyed")
    if mercy:
        lines.append("▪ your gear survives — the tower is gentler with "
                     "the newly arrived")
    lines.append("Banked gold untouched. The Vault keeps its word.")
    return Scene(
        eyebrow="ROOTHOLLOW · THE SQUARE",
        headline="You wake at the foot of the Stone",
        support="Dying in the Ascent means waking in Roothollow. It always has.",
        shard_note="I carried what I could. We go again when you're ready.",
        body_lines=lines,
        options=[Option("town", "Get up")],
        meters=meters(p),
        event_kind="death",
        banner="death",
    )


def resolve_fight_action(p: dict, floor, option_id: str) -> Scene:
    e = p["encounter"]
    notes: list[str] = []

    if option_id == "scout":
        if p["sidekick"]["scout_charges"] > 0:
            p["sidekick"]["scout_charges"] -= 1
        elif not state.spend_xp(p, economy.scan_xp_cost(floor.floor)):
            return fight_scene(p, floor, note=(
                f"The shard needs ✦ {economy.scan_xp_cost(floor.floor)} of "
                "what you've learned — you haven't learned enough yet."))
        return fight_scene(
            p, floor,
            note=f"◆ scan: {e['name']} — ATK {e['atk']} / DEF {e['def']} / "
                 f"HP {e['hp']}/{e['hp_max']}. Your ATK {state.atk(p)} / "
                 f"DEF {state.dfs(p)}.")

    if option_id == "drink_tonic":
        p["inventory"]["trollblood_tonic"] -= 1
        if p["inventory"]["trollblood_tonic"] <= 0:
            del p["inventory"]["trollblood_tonic"]
        p["hp"] = state.max_hp(p)
        dmg = _monster_hit(p)
        if p["hp"] <= 0:
            return _death(p, floor)
        return fight_scene(p, floor, note=(
            f"The tonic burns going down — full health. The {e['name']} "
            f"strikes while you drink: −{dmg} HP."))

    if option_id == "run":
        if state.roll_ok(p, 0.60):
            p["encounter"] = None
            p["location"] = "gate_town"
            return Scene(
                eyebrow=_eyebrow(p, floor),
                headline="You break away",
                support="No shame the grass will remember.",
                body_lines=["You put fence and dark between you and it."],
                options=_after_fight_options(p, floor),
                meters=meters(p))
        dmg = _monster_hit(p)
        if p["hp"] <= 0:
            return _death(p, floor)
        return fight_scene(p, floor, note=(
            f"It cuts off your line — no way out. −{dmg} HP."))

    if option_id == "stand":
        dmg = _monster_hit(p, halved=True)
        if p["hp"] <= 0:
            return _death(p, floor)
        return fight_scene(p, floor, note=(
            f"You brace and give ground slowly. −{dmg} HP, guard held."))

    if option_id == "shield_wall" and p.get("clazz") == "warrior":
        counter = max(0, state.atk(p) // 4 - e["def"] // 2)
        e["hp"] -= counter
        if e["hp"] <= 0:
            return _victory(p, floor)
        return fight_scene(p, floor, note=(
            f"Shield up — nothing gets through. Your counter takes {counter}."))

    if option_id == "sleep_spell" and p.get("clazz") == "sorcerer":
        cost = economy.sleep_xp_cost(floor.floor)
        if not state.spend_xp(p, cost):
            return fight_scene(p, floor, note=(
                f"Sleep burns ✦ {cost} of what you've learned — you don't "
                "carry that much yet."))
        _ledger(p, "sleep", xp=-cost, note=e["name"])
        p["encounter"] = None
        p["location"] = "gate_town"
        return Scene(
            eyebrow=_eyebrow(p, floor),
            headline="Sleep takes it mid-snarl",
            body_lines=[f"The {e['name']} folds into the grass, snoring.",
                        f"− ✦ {cost} experience burned — you step past it"],
            options=_after_fight_options(p, floor),
            meters=meters(p))

    if option_id == "treeline_shot" and p.get("clazz") == "archer" \
            and not e["shot_used"]:
        e["shot_used"] = True
        dmg = _player_hit(p, mult=2.0)
        if e["hp"] <= 0:
            return _victory(p, floor)
        return fight_scene(p, floor, note=(
            f"Your shot from cover takes it for {dmg} before it finds you."))

    # default: attack
    dmg = _player_hit(p)
    if e["hp"] <= 0:
        return _victory(p, floor)
    back = _monster_hit(p)
    if p["hp"] <= 0:
        return _death(p, floor)
    return fight_scene(p, floor, note=(
        f"You take it for {dmg}. It answers for {back}."))
