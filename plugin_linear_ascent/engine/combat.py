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
    if specimen == "alpha":
        prof["speed"] += economy.ALPHA_SPEED_BONUS
    p["encounter"] = {
        "kind": kind, "name": name, "prose": prose,
        "id": (enc.id if enc is not None else ""),
        "specimen": specimen, "traits": list(traits),
        "profile": prof,
        "atk": atk, "def": dfs, "hp": hp, "hp_max": hp,
        "floor": floor.floor, "shot_used": False,
        # 017 §2.4: fights open at range — bows and spells carry,
        # steel must close.
        "range": "at_range",
    }
    return fight_scene(p, floor, opener=True)


def _profile(p: dict) -> dict:
    """Encounter profile with a safe default for pre-017 docs mid-fight."""
    return p["encounter"].get("profile") or economy.profile_from_traits(
        p["encounter"].get("traits") or ())


def _range_state(p: dict) -> str:
    """'at_range' or 'close'. Pre-002 encounters mid-fight default to
    close — the only state they ever knew."""
    return p["encounter"].get("range", "close")


def _mspd(p: dict) -> int:
    return _profile(p).get("speed", economy.SPEED_NORMAL)


def _advance_chase(p: dict) -> str:
    """End of an at-range round: the monster tries to close the gap
    (§2.4 p_close). Returns the line that tells the player what moved."""
    e = p["encounter"]
    if e.get("range") != "at_range":
        return ""
    if state.roll_ok(p, economy.p_close(_mspd(p), economy.player_speed(p))):
        e["range"] = "close"
        return f"The {e['name']} closes the gap — it is on you now."
    return f"The {e['name']} comes on across open ground."


def _profile_tiers(prof: dict) -> list[str]:
    """The profile as named tiers — the [i] dossier's rows and the text
    fallback's compact line share this list."""
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
    return bits


def _profile_line(prof: dict) -> str:
    return " · ".join(_profile_tiers(prof))


def _lore(e: dict, floor) -> str:
    """003: the dossier's flavor line, from content by encounter id."""
    slug = e.get("id", "")
    for enc in getattr(floor, "encounters", ()):
        if enc.id == slug:
            return getattr(enc, "lore", "") or ""
    return ""


def _enemy_payload(p: dict, floor) -> dict:
    """003: everything the [i] card and the fight header need, in one
    dict on the Scene — the renderer never reads the player doc."""
    e = p["encounter"]
    prof = _profile(p)
    pspd = economy.player_speed(p)
    return {
        "name": e["name"],
        "hp": max(0, e["hp"]), "hp_max": e["hp_max"],
        "atk": e["atk"], "def": e["def"],
        "profile": prof,
        "tiers": _profile_tiers(prof),
        "range": e.get("range", ""),
        "lore": _lore(e, floor),
        "specimen": e.get("specimen", ""),
        "pspd": pspd,
        "mspd": prof.get("speed", economy.SPEED_NORMAL),
        "dtype": _damage_type(p),
        "dodge": economy.dodge_pct(pspd,
                                   prof.get("speed", economy.SPEED_NORMAL)),
    }


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
    clazz = p.get("clazz")
    at_range = _range_state(p) == "at_range"
    # 017 §2.4: at range steel cannot attack — Close in replaces it.
    # In close quarters anyone may try to Open distance.
    if at_range and _damage_type(p) == "melee":
        opts = [Option("close_in", "Close in", "cross the ground")]
    else:
        opts = [Option("attack", "Attack")]
    if not at_range:
        opts.append(Option("open_distance", "Open distance"))
    opts += [
        Option("stand", "Stand your ground"),
        Option("run", "Run"),
    ]
    if clazz == "warrior":
        opts.append(Option("shield_wall", "Shield wall", "class", aether=True))
    elif clazz == "sorcerer":
        opts.append(Option("sleep_spell", "Sleep spell",
                           f"class · {economy.sleep_xp_cost(floor.floor)} XP",
                           aether=True))
    elif clazz == "archer" and not e["shot_used"] \
            and _damage_type(p) == "ranged":
        # 004: the long shot needs a bow in hand — an archer swinging
        # off-class steel has no string to draw.
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
        # 013: your own numbers, spelled out — armor was invisible and
        # players couldn't tell WHY hits landed for 0.
        # (003: the enemy's profile moved off the body and into the
        # fight header + [i] dossier — scene.enemy carries it.)
        guard = guard_name(p)
        body.append(
            f"You — ATK {state.atk(p)} with your {weapon_name(p)}, "
            f"DEF {state.dfs(p)} "
            + (f"behind your {guard}." if guard else "on reflex alone."))
    if note:
        body.append(note)
    return Scene(
        eyebrow=_eyebrow(p, floor),
        # 003: the headline keeps ATK/DEF; HP lives in the always-on
        # enemy bar (scene.enemy) from round one.
        headline=f"{e['name']} — ATK {e['atk']} / DEF {e['def']}",
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
        enemy=_enemy_payload(p, floor),
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


def _wear(p: dict, slot: str, n: int = 1) -> str:
    """005: wear the slot's paid piece. The FIRST time it snaps, say so
    on the card — an unexplained half-strength number reads as a bug
    (002/003 law). Every round after, the pack strip carries the state."""
    if not state.wear_gear(p, slot, n):
        return ""
    g = economy.FORGE.get(p["gear"].get(slot) or "")
    name = g.name if g else slot
    return (f"Your {name} gives out — cracked and dull, half its "
            "strength until the Forge repairs it.")


def _monster_hit(p: dict, halved: bool = False) -> dict:
    """013: armor blunts, it never nullifies — every landed hit chips at
    least ⌈raw/4⌉ (min 1) through any DEF. Returns the breakdown so the
    card can SAY what the armor did instead of silently eating hits.
    002: a speed advantage gives a small capped dodge before anything
    else; a monster still at range strikes at −50% (charging, not
    fighting). 005: every landed blow wears the guard that met it."""
    dodge = economy.dodge_pct(economy.player_speed(p), _mspd(p))
    if dodge and state.roll_ok(p, dodge / 100):
        return {"dmg": 0, "raw": 0, "blocked": 0, "dodged": True}
    e = p["encounter"]
    if _range_state(p) == "at_range":
        halved = True
    raw = state.rng_int(p, e["atk"] // 2, e["atk"])
    chip = max(1, -(-raw // economy.CHIP_DIVISOR))
    dmg = max(chip, raw - state.dfs(p) // 2)
    if halved:
        dmg //= 2
    p["hp"] -= dmg
    broke = [note for s in ("shield", "armor") if (note := _wear(p, s))]
    return {"dmg": dmg, "raw": raw, "blocked": raw - dmg, "broke": broke}


def _counter_text(p: dict, hit: dict, lead: str = "") -> str:
    """One line that explains the enemy's blow: what landed, what the
    armor ate. The player asked for this by name — never a bare number."""
    e = p["encounter"]
    guard = guard_name(p)
    dmg, blocked = hit["dmg"], hit["blocked"]
    lead = lead or f"The {e['name']} answers"
    # 005: the round a guard piece snaps, the card says so right here.
    tail = " " + " ".join(hit["broke"]) if hit.get("broke") else ""
    if hit.get("dodged"):
        return f"{lead} — you slip the blow entirely. Speed tells."
    if dmg <= 0:
        what = f"your {guard}" if guard else "your guard"
        return f"{lead} — {what} turns the whole blow. 0 damage.{tail}"
    if guard and blocked >= dmg:
        soak = "soak" if " and " in guard else "soaks"
        return (f"{lead} — your {guard} {soak} almost all of it: "
                f"only −{dmg} HP gets through.{tail}")
    if guard and blocked > 0:
        return (f"{lead} for −{dmg} HP — your {guard} blunted "
                f"{blocked} of it.{tail}")
    if guard:
        return f"{lead} and finds a gap past your {guard}: −{dmg} HP.{tail}"
    return f"{lead} with nothing between you and its teeth: −{dmg} HP.{tail}"


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


def _weapon_line(p: dict) -> str:
    """004: the equipped weapon's class line ('' for pre-class docs)."""
    item = economy.FORGE.get(p["gear"].get("weapon") or "")
    return getattr(item, "line", "") if item else ""


def _damage_type(p: dict) -> str:
    # 004 §3.2: the WEAPON decides the damage type — a warrior holding
    # a bought bow shoots (badly). Line-less docs fall back to class.
    line = _weapon_line(p)
    if line:
        return economy.DAMAGE_TYPE[line]
    return economy.DAMAGE_TYPE.get(p.get("clazz") or "", "melee")


def _off_class(p: dict) -> bool:
    line = _weapon_line(p)
    return bool(line) and bool(p.get("clazz")) and line != p["clazz"]


def _player_hit(p: dict, mult: float = 1.0) -> int:
    # 017 §2: typed damage through the defense profile. Magic ignores
    # flat DEF but eats the resist tier; melee/ranged keep raw−DEF/2 and
    # eat the armor tier. Whatever CAN hit chips ≥1; melee vs flying is
    # the one legal zero.
    e = p["encounter"]
    # 002: a bow in close quarters is half a weapon; magic and steel
    # keep full strength at both ranges.
    if _damage_type(p) == "ranged" and _range_state(p) == "close":
        mult *= economy.BOW_CLOSE_MULT
    # 004 §3.2: an off-class weapon is a stopgap — half strength always.
    if _off_class(p):
        mult *= economy.OFF_CLASS_DMG_MULT
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
        # 003: the scan's edge over the free dossier — exact numbers
        # plus the monster's NEXT INTENT, odds named.
        intent = ""
        if _range_state(p) == "at_range":
            pc = round(100 * economy.p_close(_mspd(p),
                                             economy.player_speed(p)))
            intent = (f" It will try to close this round — "
                      f"{pc}% it makes it.")
        elif _profile(p).get("speed",
                             economy.SPEED_NORMAL) >= economy.SPEED_FAST:
            intent = " It is faster than you — it will stay on you."
        return fight_scene(
            p, floor,
            note=f"◆ scan: {e['name']} — ATK {e['atk']} / DEF {e['def']} / "
                 f"HP {e['hp']}/{e['hp_max']}"
                 + (f" · {pline}" if pline else "")
                 + f". Your ATK {state.atk(p)} / DEF {state.dfs(p)}."
                 + intent)

    if option_id == "drink_tonic":
        p["inventory"]["trollblood_tonic"] -= 1
        if p["inventory"]["trollblood_tonic"] <= 0:
            del p["inventory"]["trollblood_tonic"]
        p["hp"] = state.max_hp(p)
        hit = _monster_hit(p)
        if p["hp"] <= 0:
            return _death(p, floor)
        chase = _advance_chase(p)
        return fight_scene(p, floor, note=(
            "The tonic burns going down — full health. "
            + _counter_text(p, hit,
                            lead=f"The {e['name']} strikes while you drink")
            + (f" {chase}" if chase else "")))

    if option_id in ("close_in", "attack") and _damage_type(p) == "melee" \
            and _range_state(p) == "at_range":
        # §2.4: always succeeds, costs the round; the monster strikes at
        # −50% while you cross the open ground. A bare "attack" from a
        # melee player at range IS the crossing — steel can't swing yet.
        e["range"] = "close"
        snap = _wear(p, "shoes")       # 005: crossing spends shoe tread
        hit = _monster_hit(p, halved=True)
        if p["hp"] <= 0:
            return _death(p, floor)
        return fight_scene(p, floor, note=(
            "You cross the open ground fast and low. "
            + _counter_text(p, hit,
                            lead=f"The {e['name']} meets you mid-stride")
            + (f" {snap}" if snap else "")))

    if option_id == "open_distance" and _range_state(p) == "close":
        # §2.4: speed decides; on failure the monster gets a free
        # halved hit while you turn.
        snap = _wear(p, "shoes")       # 005: the turn spends shoe tread
        if state.roll_ok(p, economy.p_open(economy.player_speed(p),
                                           _mspd(p))):
            e["range"] = "at_range"
            chase = _advance_chase(p)
            return fight_scene(p, floor, note=(
                "You break contact and put ground between you. "
                + chase + (f" {snap}" if snap else "")))
        hit = _monster_hit(p, halved=True)
        if p["hp"] <= 0:
            return _death(p, floor)
        return fight_scene(p, floor, note=(
            "No gap opens — it stays with you. "
            + _counter_text(p, hit,
                            lead=f"The {e['name']} punishes the turn")
            + (f" {snap}" if snap else "")))

    if option_id == "run":
        # §2.4: the flat 60% is gone — speed decides the getaway.
        snap = _wear(p, "shoes")       # 005: the sprint spends shoe tread
        if state.roll_ok(p, economy.p_flee(economy.player_speed(p),
                                           _mspd(p))):
            p["encounter"] = None
            p["location"] = "gate_town"
            return Scene(
                eyebrow=_eyebrow(p, floor),
                headline="You break away",
                support="No shame the grass will remember.",
                body_lines=(["You put fence and dark between you and it."]
                            + ([snap] if snap else [])),
                options=_after_fight_options(p, floor),
                meters=meters(p))
        hit = _monster_hit(p)
        if p["hp"] <= 0:
            return _death(p, floor)
        chase = _advance_chase(p)
        return fight_scene(p, floor, note=(
            "It cuts off your line — no way out. "
            + _counter_text(p, hit, lead="It catches you turning")
            + (f" {chase}" if chase else "")
            + (f" {snap}" if snap else "")))

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
        broke = " " + " ".join(hit["broke"]) if hit.get("broke") else ""
        chase = _advance_chase(p)
        return fight_scene(
            p, floor,
            note=f"{braced} {held}{broke}" + (f" {chase}" if chase else ""))

    if option_id == "shield_wall" and p.get("clazz") == "warrior":
        # 017: the counter is a melee blow — it cannot reach a flyer,
        # and (002) it cannot reach a monster still crossing open ground.
        at_range = _range_state(p) == "at_range"
        if _profile(p).get("flying") or at_range:
            counter = 0
        else:
            counter = max(0, state.atk(p) // 4 - e["def"] // 2)
        e["hp"] -= counter
        if e["hp"] <= 0:
            return _victory(p, floor)
        chase = _advance_chase(p)
        if counter <= 0 and _profile(p).get("flying"):
            return fight_scene(p, floor, note=(
                "Shield up — nothing gets through. But your counter "
                "swings under it: the thing is airborne."))
        if counter <= 0 and at_range:
            return fight_scene(p, floor, note=(
                "Shield up — nothing gets through. Your counter finds "
                "only air: it hasn't reached you yet."
                + (f" {chase}" if chase else "")))
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
        snap = _wear(p, "weapon")      # 005: the long shot is an attack
        if _profile(p).get("armor") in ("med", "high"):
            # 017: Medium+ plate over the vitals — the long shot loses
            # its double (Low plate still leaves gaps for a marksman)
            dmg = _player_hit(p)
            if e["hp"] <= 0:
                return _victory(p, floor)
            chase = _advance_chase(p)
            return fight_scene(p, floor, note=(
                f"Your arrow snaps against its plate — {dmg} damage, "
                "no clean gap for a killing shot."
                + (f" {chase}" if chase else "")
                + (f" {snap}" if snap else "")))
        dmg = _player_hit(p, mult=2.0)
        if e["hp"] <= 0:
            return _victory(p, floor)
        chase = _advance_chase(p)
        return fight_scene(p, floor, note=(
            f"Your shot from cover takes it for {dmg} before it finds you."
            + (f" {chase}" if chase else "")
            + (f" {snap}" if snap else "")))

    # default: attack
    # 004 §3.2: off-class hands — a bow burns bought arrows for anyone
    # but an archer, and every off-class swing misses 25% of the time
    # (the miss eats the round; the monster answers).
    if _off_class(p):
        if _damage_type(p) == "ranged":
            arrows = int(p["inventory"].get("arrows", 0))
            if arrows <= 0:
                bow = p["gear"]["weapon"]
                p["inventory"][bow] = p["inventory"].get(bow, 0) + 1
                p["gear"]["weapon"] = economy.class_starter(
                    p.get("clazz") or "").slug
                p["hone"]["weapon"] = 0
                # 005: the bow keeps its wear in the pack; the basic
                # weapon underneath never wears.
                bow_dur = (p.get("durability") or {}).pop("weapon", None)
                if bow_dur is not None:
                    p.setdefault("durability_pack", {})[bow] = bow_dur
                return fight_scene(p, floor, note=(
                    "Your quiver runs dry — the bow goes over your "
                    f"shoulder and your {weapon_name(p)} comes back "
                    "out. The Forge sells arrows by the pack."))
            p["inventory"]["arrows"] = arrows - 1
    snap = _wear(p, "weapon")          # 005: every swing spends the edge
    if _off_class(p) and state.roll_ok(p, economy.OFF_CLASS_MISS):
        back = _monster_hit(p)
        if p["hp"] <= 0:
            return _death(p, floor)
        chase = _advance_chase(p)
        return fight_scene(p, floor, note=(
            f"Not your weapon — your {weapon_name(p)} goes wide "
            "of anything that matters. "
            + _counter_text(p, back,
                            lead=f"The {e['name']} makes you pay "
                                 "for the fumble")
            + (f" {chase}" if chase else "")
            + (f" {snap}" if snap else "")))
    dmg = _player_hit(p)
    if e["hp"] <= 0:
        return _victory(p, floor)
    back = _monster_hit(p)
    if p["hp"] <= 0:
        return _death(p, floor)
    chase = _advance_chase(p)
    return fight_scene(p, floor, note=(
        f"{_strike_text(p, dmg)} {_counter_text(p, back)}"
        + (f" {chase}" if chase else "")
        + (f" {snap}" if snap else "")))
