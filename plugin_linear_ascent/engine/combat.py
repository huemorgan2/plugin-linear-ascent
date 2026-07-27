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


def _kill_fx(e: dict, name: str, first_clear: bool) -> str:
    """011: event animation slug for a victory scene. Creature-specific
    kill GIFs win; a first floor clear plays the gate opening. The
    renderer silently skips slugs with no shipped art."""
    hay = f"{e.get('id', '')} {name}".lower()
    for family in ("brackjaw", "boar", "goblin", "wolf"):
        if family in hay:
            return f"{family}_kill"
    if first_clear:
        return "ascent_open"
    return ""


def meters(p: dict) -> Meters:
    return Meters(
        hp=p["hp"], hp_max=state.max_hp(p),
        energy=state.energy_now(p),
        energy_max=economy.energy_cap(p["level"], p.get("race") or ""),
        xp=p["xp"],
        xp_need=economy.xp_need(p["level"]),
        gold=p["gold"],
        level=p["level"])


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
    # 017 §2: the defense profile — armor/resist tiers, flying, bulwark,
    # speed — derived from qualitative content traits, priced in economy.
    traits = tuple(getattr(enc, "traits", ()) or ()) if enc is not None else ()
    if kind == "warden":
        prof = economy.warden_profile(floor.floor)
    else:
        prof = economy.profile_from_traits(traits)
    if prof["bulwark"]:
        hp = round(hp * economy.BULWARK_HP_MULT)
    specimen = "common"
    if kind == "wilds":
        # 008: specimen roll — same averages, real variance. Visible on
        # the opener so fighting an alpha is an informed choice.
        specimen = state.rng_pick(
            p, [(s["weight"], k) for k, s in economy.SPECIMENS.items()])
        spec = economy.SPECIMENS[specimen]
        atk = round(atk * spec["atk"])
        hp = round(hp * spec["hp"])
        if spec["tag"]:
            prose = f"{prose} This one is {spec['tag']}."
    if kind == "wilds" and prof["speed"] != economy.SPEED_NORMAL:
        pass  # speed is chase-priced in 002; stored below, shown on cards
    p["encounter"] = {
        "kind": kind, "name": name, "prose": prose,
        "id": (enc.id if enc is not None else ""),
        "specimen": specimen, "traits": list(traits),
        "profile": prof,
        "atk": atk, "def": dfs, "hp": hp, "hp_max": hp,
        "floor": floor.floor, "shot_used": False,
    }
    return fight_scene(p, floor, opener=True)


def _profile(p: dict) -> dict:
    """Encounter profile with a safe default for pre-017 docs mid-fight."""
    return p["encounter"].get("profile") or economy.profile_from_traits(
        p["encounter"].get("traits") or ())


def _profile_line(prof: dict) -> str:
    """One compact readable line — the [i] card (003) will do it justice;
    until then the opener itself must say what the player is facing."""
    bits = []
    if prof.get("armor", "none") != "none":
        bits.append(f"plate {economy.TIER_LABEL[prof['armor']]}")
    if prof.get("resist", "none") != "none":
        bits.append(f"spellguard {economy.TIER_LABEL[prof['resist']]}")
    if prof.get("flying"):
        bits.append("AIRBORNE")
    if prof.get("bulwark"):
        bits.append("bulwark")
    if prof.get("speed", economy.SPEED_NORMAL) >= economy.SPEED_FAST:
        bits.append("fast")
    elif prof.get("speed", economy.SPEED_NORMAL) <= economy.SPEED_SLOW:
        bits.append("slow")
    return " · ".join(bits)


def _shard_advice(p: dict, floor) -> str:
    """Insight-scaled whisper — sometimes wrong, on purpose."""
    e = p["encounter"]
    insight = p["sidekick"]["insight"]
    correct = state.roll_ok(p, 0.5 + 0.05 * insight)
    if e.get("specimen") == "alpha":
        return ("It leads whatever pack is left down here. It hits harder "
                "and pays better. Your call — I carry you either way.")
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
                           f"class · {economy.sleep_xp_cost(floor.floor)} XP",
                           aether=True))
    elif clazz == "archer" and not e["shot_used"]:
        opts.append(Option("treeline_shot", "Treeline shot", "class", aether=True))
    if p["inventory"].get("trollblood_tonic"):
        opts.append(Option("drink_tonic", "Drink trollblood tonic", "full heal"))
    charges = p["sidekick"]["scout_charges"]
    opts.append(Option(
        "scout", "Ask the shard to scan it",
        f"{charges} charges" if charges > 0
        else f"{economy.scan_xp_cost(floor.floor)} XP",
        aether=True))

    body = [e["prose"]] if opener else []
    if opener:
        # 017: the defense profile, named on sight — the counter system
        # is invisible noise unless the enemy's sheet is readable.
        pline = _profile_line(_profile(p))
        if pline:
            body.append(f"◈ {pline}")
        # 013: your own numbers, spelled out — armor was invisible and
        # players couldn't tell WHY hits landed for 0.
        guard = guard_name(p)
        body.append(
            f"You — ATK {state.atk(p)} with your {weapon_name(p)}, "
            f"DEF {state.dfs(p)} "
            + (f"behind your {guard}." if guard else "on reflex alone."))
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
        banner_variant=(e.get("specimen", "")
                        if e["kind"] == "wilds"
                        and e.get("specimen") != "common" else ""),
        event_kind="boss" if e["kind"] == "warden" else "",
    )


def weapon_name(p: dict) -> str:
    slug = p["gear"].get("weapon") or economy.STARTER_WEAPON.slug
    item = economy.FORGE.get(slug)
    name = item.name if item else "blade"
    return f"honed {name}" if state.hone_level(p, "weapon") else name


def guard_name(p: dict) -> str:
    """'Riveted Leather and Ironbound Targe', or '' when bare."""
    names = []
    for slot in ("armor", "shield"):
        slug = p["gear"].get(slot)
        if slug and slug in economy.FORGE:
            names.append(economy.FORGE[slug].name)
    return " and ".join(names)


def _monster_hit(p: dict, halved: bool = False) -> dict:
    """013: armor blunts, it never nullifies — every landed hit chips at
    least ⌈raw/4⌉ (min 1) through any DEF. Returns the breakdown so the
    card can SAY what the armor did instead of silently eating hits."""
    e = p["encounter"]
    raw = state.rng_int(p, e["atk"] // 2, e["atk"])
    chip = max(1, -(-raw // economy.CHIP_DIVISOR))
    dmg = max(chip, raw - state.dfs(p) // 2)
    if halved:
        dmg //= 2
    p["hp"] -= dmg
    return {"dmg": dmg, "raw": raw, "blocked": raw - dmg}


def _counter_text(p: dict, hit: dict, lead: str = "") -> str:
    """One line that explains the enemy's blow: what landed, what the
    armor ate. The player asked for this by name — never a bare number."""
    e = p["encounter"]
    guard = guard_name(p)
    dmg, blocked = hit["dmg"], hit["blocked"]
    lead = lead or f"The {e['name']} answers"
    if dmg <= 0:
        what = f"your {guard}" if guard else "your guard"
        return f"{lead} — {what} turns the whole blow. 0 damage."
    if guard and blocked >= dmg:
        return (f"{lead} — your {guard} soak almost all of it: "
                f"only −{dmg} HP gets through.")
    if guard and blocked > 0:
        return (f"{lead} for −{dmg} HP — your {guard} blunted "
                f"{blocked} of it.")
    if guard:
        return f"{lead} and finds a gap past your {guard}: −{dmg} HP."
    return f"{lead} with nothing between you and its teeth: −{dmg} HP."


def _strike_text(p: dict, dmg: int) -> str:
    """The player's blow, explained: which weapon, how hard it bit."""
    e = p["encounter"]
    w = weapon_name(p)
    prof = _profile(p)
    if dmg <= 0:
        if prof.get("flying") and _damage_type(p) == "melee":
            return (f"The {e['name']} lifts out of reach — your {w} "
                    "cuts empty air. Steel can't touch what flies.")
        return (f"Your {w} glances off the {e['name']}'s hide — "
                "nothing lands.")
    tier_note = ""
    dt = _damage_type(p)
    if dt == "magic" and prof.get("resist", "none") != "none":
        tier_note = (f" — its spellguard "
                     f"({economy.TIER_LABEL[prof['resist']]}) eats part "
                     "of the cast")
    elif dt != "magic" and prof.get("armor", "none") != "none":
        tier_note = (f" — its plate "
                     f"({economy.TIER_LABEL[prof['armor']]}) turns part "
                     "of the blow")
    if dmg >= max(1, e["hp_max"] // 3):
        return (f"Your {w} bites deep — {dmg} damage the "
                f"{e['name']} won't shrug off{tier_note}.")
    return f"Your {w} takes it for {dmg}{tier_note}."


def _damage_type(p: dict) -> str:
    return economy.DAMAGE_TYPE.get(p.get("clazz") or "", "melee")


def _player_hit(p: dict, mult: float = 1.0) -> int:
    # 017 §2: typed damage through the defense profile. Magic ignores
    # flat DEF but eats the resist tier; melee/ranged keep raw−DEF/2 and
    # eat the armor tier. Whatever CAN hit chips ≥1; melee vs flying is
    # the one legal zero.
    e = p["encounter"]
    raw = state.rng_int(p, state.atk(p) // 2, state.atk(p))
    dmg = economy.typed_damage(_damage_type(p), round(raw * mult),
                               e["def"], _profile(p))
    e["hp"] -= dmg
    return dmg


def _train_nudge(p: dict) -> list[str]:
    """012: levels are bought, never granted. When the bar fills, point
    at the Guildhall instead of leveling — XP banks past the cap."""
    if p["xp"] < economy.xp_need(p["level"]):
        return []
    fee = economy.levelup_gold(p["level"])
    return [f"Your XP bar is full. The Guildhall trains climbers to "
            f"LEVEL {p['level'] + 1} — the fee is ◈ {fee:,}."]


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
        # 008: hard specimens pay more, runts pay less
        gold = round(
            gold * economy.SPECIMENS[e.get("specimen", "common")]["gold"])
        # 017: a hard profile pays for the diagnosis it demands
        gold = round(gold * economy.profile_gold_mult(_profile(p)))
    if p.get("race") == "elf":
        xp = round(xp * (1 + economy.ELF_XP_BONUS))
    buff = state.faction_buff_pct(p, "xp")
    if buff:
        xp = round(xp * (1 + buff / 100))     # 010: CLIMB week blessing
    p["xp"] += xp
    p["gold"] += gold
    _ledger(p, "kill", gold=gold, xp=xp, note=e["name"])
    downed = (f"The {e['name']} goes down — no match for your "
              f"{weapon_name(p)}."
              if e["kind"] == "wilds" else f"The {e['name']} goes down.")
    lines = [downed, f"+ {xp} XP", f"+ ◈ {gold} carried gold"]
    if e.get("specimen") == "alpha":
        loot = state.rng_pick(p, [(70, "medgel"), (30, "luck_charm")])
        p["inventory"][loot] = p["inventory"].get(loot, 0) + 1
        lines.append(f"▪ alpha spoils: {economy.APOTHECARY[loot].name}")
    lines += _train_nudge(p)

    first_clear = False
    if e["kind"] == "warden":
        nxt = floor.floor + 1
        if p["unlocked_floor"] < nxt:
            p["unlocked_floor"] = nxt
            first_clear = True
            lines.append(f"The lift grinds open. FLOOR {nxt} is yours to enter.")
            if p.get("_world") is not None:
                p.setdefault("_effects", []).append({
                    "kind": "happening", "floor": floor.floor,
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
        fx=_kill_fx(e, e["name"], first_clear),
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
            options=[Option("heal", "The healer's tent",
                            f"◈ {economy.HEALER_TENT_PER_FLOOR * floor.floor}"),
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
            "kind": "happening", "floor": floor.floor,
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
                f"The shard needs {economy.scan_xp_cost(floor.floor)} XP of "
                "what you've learned — you haven't learned enough yet."))
        pline = _profile_line(_profile(p))
        return fight_scene(
            p, floor,
            note=f"◆ scan: {e['name']} — ATK {e['atk']} / DEF {e['def']} / "
                 f"HP {e['hp']}/{e['hp_max']}"
                 + (f" · {pline}" if pline else "")
                 + f". Your ATK {state.atk(p)} / DEF {state.dfs(p)}.")

    if option_id == "drink_tonic":
        p["inventory"]["trollblood_tonic"] -= 1
        if p["inventory"]["trollblood_tonic"] <= 0:
            del p["inventory"]["trollblood_tonic"]
        p["hp"] = state.max_hp(p)
        hit = _monster_hit(p)
        if p["hp"] <= 0:
            return _death(p, floor)
        return fight_scene(p, floor, note=(
            "The tonic burns going down — full health. "
            + _counter_text(p, hit,
                            lead=f"The {e['name']} strikes while you drink")))

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
        hit = _monster_hit(p)
        if p["hp"] <= 0:
            return _death(p, floor)
        return fight_scene(p, floor, note=(
            "It cuts off your line — no way out. "
            + _counter_text(p, hit, lead="It catches you turning")))

    if option_id == "stand":
        hit = _monster_hit(p, halved=True)
        if p["hp"] <= 0:
            return _death(p, floor)
        guard = guard_name(p)
        braced = (f"You brace behind your {guard} and give ground slowly."
                  if guard else "You brace and give ground slowly.")
        held = ("Nothing gets through — guard held."
                if hit["dmg"] <= 0 else
                f"−{hit['dmg']} HP, guard held.")
        return fight_scene(p, floor, note=f"{braced} {held}")

    if option_id == "shield_wall" and p.get("clazz") == "warrior":
        # 017: the counter is a melee blow — it cannot reach a flyer
        if _profile(p).get("flying"):
            counter = 0
        else:
            counter = max(0, state.atk(p) // 4 - e["def"] // 2)
        e["hp"] -= counter
        if e["hp"] <= 0:
            return _victory(p, floor)
        if counter <= 0 and _profile(p).get("flying"):
            return fight_scene(p, floor, note=(
                "Shield up — nothing gets through. But your counter "
                "swings under it: the thing is airborne."))
        return fight_scene(p, floor, note=(
            f"Shield up — nothing gets through. Your counter takes {counter}."))

    if option_id == "sleep_spell" and p.get("clazz") == "sorcerer":
        # 017: a High spellguard shrugs the lullaby off entirely —
        # refused BEFORE the XP is spent, so probing costs nothing.
        if _profile(p).get("resist") == "high":
            return fight_scene(p, floor, note=(
                f"You shape the lullaby and the {e['name']}'s spellguard "
                "burns it off mid-air. This one won't sleep."))
        cost = economy.sleep_xp_cost(floor.floor)
        if not state.spend_xp(p, cost):
            return fight_scene(p, floor, note=(
                f"Sleep burns {cost} XP of what you've learned — you don't "
                "carry that much yet."))
        _ledger(p, "sleep", xp=-cost, note=e["name"])
        p["encounter"] = None
        p["location"] = "gate_town"
        return Scene(
            eyebrow=_eyebrow(p, floor),
            headline="Sleep takes it mid-snarl",
            body_lines=[f"The {e['name']} folds into the grass, snoring.",
                        f"− {cost} XP burned — you step past it"],
            options=_after_fight_options(p, floor),
            meters=meters(p))

    if option_id == "treeline_shot" and p.get("clazz") == "archer" \
            and not e["shot_used"]:
        e["shot_used"] = True
        if _profile(p).get("armor") in ("med", "high"):
            # 017: Medium+ plate over the vitals — the long shot loses
            # its double (Low plate still leaves gaps for a marksman)
            dmg = _player_hit(p)
            if e["hp"] <= 0:
                return _victory(p, floor)
            return fight_scene(p, floor, note=(
                f"Your arrow snaps against its plate — {dmg} damage, "
                "no clean gap for a killing shot."))
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
        f"{_strike_text(p, dmg)} {_counter_text(p, back)}"))
