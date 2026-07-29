"""Combat resolver — economy §2–§3 math, deterministic rolls.

The encounter lives in the player doc; every function mutates the doc and
returns a Scene. Flows are gated here, not in prose: out-of-order calls
never reach these functions (core.py dispatches).
"""

from __future__ import annotations

import os

from .. import economy
from . import contracts, state, weekly
from .scene import Meters, Option, Scene

_CREATURES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "..", "content", "art", "creatures")
_EVENTS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "..", "content", "art", "events")


def _creature_art(slug: str) -> bool:
    return any(os.path.exists(os.path.join(_CREATURES, f"{slug}_{s}.png"))
               for s in ("320x112", "320x200"))


def _event_art(slug: str) -> bool:
    return os.path.exists(os.path.join(_EVENTS, f"{slug}_320x112.gif"))


def _fight_banner(e: dict, floor) -> str:
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


# 009: kill GIF variants per damage type — the ending shows YOUR kill:
# steel is the warrior's blade, arrows the archer's shot, magic the
# wizard's cast. Family match is per-token (prefix) so "curator" never
# plays the rat's death.
_KILL_FAMILIES = ("brackjaw", "tortoise", "haunt", "goblin", "boar",
                  "wolf", "rat")
_KILL_SUFFIX = {"melee": "melee", "ranged": "arrow", "magic": "magic"}


def _kill_fx(e: dict, name: str, first_clear: bool, dtype: str = "") -> str:
    """011/009: event animation slug for a victory scene. A typed kill
    GIF (family × landing damage type) wins; the family's untyped kill
    is the fallback; a first floor clear plays the gate opening. The
    renderer silently skips slugs with no shipped art."""
    tokens = f"{e.get('id', '')} {name}".lower().replace("_", " ").split()
    for family in _KILL_FAMILIES:
        if not any(t.startswith(family) for t in tokens):
            continue
        suffix = _KILL_SUFFIX.get(dtype, "")
        if suffix and _event_art(f"{family}_kill_{suffix}"):
            return f"{family}_kill_{suffix}"
        if _event_art(f"{family}_kill"):
            return f"{family}_kill"
        break
    if first_clear:
        return "ascent_open"
    return ""


def meters(p: dict) -> Meters:
    return Meters(
        hp=p["hp"], hp_max=state.max_hp(p),
        energy=state.energy_now(p),
        energy_max=state.energy_cap_of(p),
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
    if kind == "warden":
        # 022/004: "answer a keep's horn" counts at the OPEN — showing
        # up is the engagement, win or bleed. 005's strongbox counts
        # the same moment — one definition of "engagement".
        contracts.note_warden(p)
        weekly.note(p, "wardens")
    s = fight_scene(p, floor, opener=True)
    # 007: first fight per type that hard-counters the class — the one
    # agent beat besides death and boss. A warden keeps "boss".
    if not s.event_kind and _matchup_moment(p, prof):
        s.event_kind = "matchup"
    return s


def _hard_counter(p: dict, prof: dict) -> bool:
    """007: does this profile hard-counter the player's damage type?
    Soft drags (fast vs kiting, bulwark HP) don't count — only the
    walls: steel can't touch wings, arrows snap on real plate, spells
    die on real spellguard."""
    dt = _damage_type(p)
    if dt == "melee":
        return bool(prof.get("flying"))
    if dt == "ranged":
        return prof.get("armor", "none") in ("med", "high")
    if dt == "magic":
        return prof.get("resist", "none") in ("med", "high")
    return False


def _matchup_moment(p: dict, prof: dict) -> bool:
    """007: the ONE remaining agent beat — the first fight against each
    monster TYPE that hard-counters the class earns a sidekick moment.
    Flagged per encounter id in the doc; never twice, never for soft
    counters (0.17.2 silence holds everywhere else)."""
    eid = p["encounter"].get("id", "")
    if not eid or not _hard_counter(p, prof):
        return False
    seen = p.setdefault("matchup_seen", [])
    if eid in seen:
        return False
    seen.append(eid)
    return True


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
    if e.get("netted"):
        # 006: it cannot close through the net — this attempt is the
        # net's last service.
        e.pop("netted", None)
        return f"The {e['name']} tears at the net instead of the ground."
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


def _relic_options(p: dict) -> list[Option]:
    """006: a relic's fight option appears only when it can actually do
    its one dramatic thing — ownership is rare, the list stays short."""
    e = p["encounter"]
    inv = p["inventory"]
    prof = _profile(p)
    opts: list[Option] = []
    if _damage_type(p) == "ranged":
        for slug in economy.QUIVER_SLUGS:
            if inv.get(slug) and e.get("nocked") != slug:
                r = economy.RELICS[slug]
                opts.append(Option(f"nock_{slug}",
                                   f"Nock {r.name.lower()}",
                                   f"×{inv[slug]}"))
    if inv.get("weapon_oil") and _damage_type(p) != "magic" \
            and p.get("oil", 0) <= 0:
        opts.append(Option("use_oil", "Slick your weapon",
                           f"{economy.OIL_STRIKES} strikes +25%"))
    if inv.get("entangling_net") and e["kind"] != "warden" \
            and not e.get("netted"):
        opts.append(Option("throw_net", "Throw the net",
                           f"×{inv['entangling_net']}"))
    if inv.get("sky_hook") and prof.get("flying"):
        opts.append(Option("use_hook", "Set the sky-hook",
                           f"{inv['sky_hook']} uses left"))
    if inv.get("strip_potion") and prof.get("resist", "none") != "none":
        opts.append(Option("use_strip", "Hurl the strip potion",
                           "spellguard, gone"))
    if inv.get("curse_scroll") and prof.get("armor", "none") != "none":
        opts.append(Option("use_curse", "Read the curse scroll",
                           "its plate, halved"))
    if inv.get("polymorph_dust") and e["kind"] != "warden":
        opts.append(Option("use_polymorph", "Cast the polymorph dust",
                           "no loot, no XP"))
    if not e.get("life_used"):
        if inv.get("veil_draught") and not e.get("veiled"):
            opts.append(Option("use_veil", "Drink the veil draught",
                               "untouchable till you strike"))
        if inv.get("golden_apple") and e.get("apple_hp", 0) <= 0:
            opts.append(Option("use_apple", "Eat the golden apple",
                               "overshield"))
    if inv.get("severing_word") and e["kind"] != "warden":
        opts.append(Option("use_severing", "Speak the Severing Word",
                           "it ends"))
    return opts


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
    opts += _relic_options(p)
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
    fx_note = e.pop("_fx_note", "")
    if fx_note:
        body.append(fx_note)
    # 022/003: the number breathes — every round re-reads who is hot on
    # this floor, and changes fold in as story lines.
    hot, _camped = state.presence_counts(p, floor.floor)
    if hot > 1:
        body.append(f"{hot} blades hot on this floor.")
    body += state.presence_delta_lines(p, floor.floor)
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
        # The creature stays on screen for every round of the fight: it is
        # the same enemy, and dropping the art after the opener read as
        # "this monster has no picture".
        banner=_fight_banner(e, floor),
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
    fighting). 005: every landed blow wears the guard that met it.
    006: the net eats its round; the veil makes you untargetable; the
    apple halves and soaks."""
    e = p["encounter"]
    if e.get("netted") and _range_state(p) != "at_range":
        # in close quarters the tangled round IS the answer; at range
        # the net's last service is blocking the close (_advance_chase).
        e.pop("netted", None)
        return {"dmg": 0, "raw": 0, "blocked": 0, "netted": True}
    if e.get("veiled"):
        return {"dmg": 0, "raw": 0, "blocked": 0, "veiled": True}
    dodge = economy.dodge_pct(economy.player_speed(p), _mspd(p))
    if dodge and state.roll_ok(p, dodge / 100):
        return {"dmg": 0, "raw": 0, "blocked": 0, "dodged": True}
    if _range_state(p) == "at_range":
        halved = True
    raw = state.rng_int(p, e["atk"] // 2, e["atk"])
    chip = max(1, -(-raw // economy.CHIP_DIVISOR))
    dmg = max(chip, raw - state.dfs(p) // 2)
    if halved:
        dmg //= 2
    soaked = 0
    if e.get("apple_hp", 0) > 0:
        dmg //= 2                          # the apple halves everything
        soaked = min(e["apple_hp"], dmg)
        e["apple_hp"] -= soaked
        dmg -= soaked
    p["hp"] -= dmg
    broke = [note for s in ("shield", "armor") if (note := _wear(p, s))]
    return {"dmg": dmg, "raw": raw, "blocked": raw - dmg, "broke": broke,
            "apple": soaked}


def _counter_text(p: dict, hit: dict, lead: str = "") -> str:
    """One line that explains the enemy's blow: what landed, what the
    armor ate. The player asked for this by name — never a bare number."""
    e = p["encounter"]
    guard = guard_name(p)
    dmg, blocked = hit["dmg"], hit["blocked"]
    lead = lead or f"The {e['name']} answers"
    # 005: the round a guard piece snaps, the card says so right here.
    tail = " " + " ".join(hit["broke"]) if hit.get("broke") else ""
    if hit.get("netted"):
        return (f"The {e['name']} thrashes in the net — its round is "
                "spent tearing cord.")
    if hit.get("veiled"):
        return (f"The {e['name']} strikes where you were — the veil "
                "holds; nothing finds you.")
    if hit.get("dodged"):
        return f"{lead} — you slip the blow entirely. Speed tells."
    if hit.get("apple"):
        return (f"{lead} — the golden shell takes {hit['apple']} of it"
                + (f"; −{hit['dmg']} HP seeps through." if hit["dmg"]
                   else "; nothing reaches you.") + tail)
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


def _player_hit(p: dict, mult: float = 1.0, pierce: bool = False) -> int:
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
    # 006: ten oiled strikes hit harder — physical weapons only.
    if p.get("oil", 0) > 0 and _damage_type(p) != "magic":
        mult *= economy.OIL_MULT
        p["oil"] -= 1
    raw = state.rng_int(p, state.atk(p) // 2, state.atk(p))
    prof = _profile(p)
    if pierce:
        prof = dict(prof, armor="none")    # 006: the shot ignores plate
    dmg = economy.typed_damage(_damage_type(p), round(raw * mult),
                               e["def"], prof)
    e["hp"] -= dmg
    return dmg


def _quiver_shot(p: dict) -> tuple[float, bool, str]:
    """006: the nocked special arrow shapes this shot. Consumes one and
    returns (damage mult, pierce, effect) — effect ∈ '', 'poison',
    'slow'. Empty quivers un-nock themselves."""
    e = p["encounter"]
    slug = e.get("nocked", "")
    if not slug or _damage_type(p) != "ranged" \
            or p["inventory"].get(slug, 0) <= 0:
        e.pop("nocked", None)
        return 1.0, False, ""
    p["inventory"][slug] -= 1
    if p["inventory"][slug] <= 0:
        del p["inventory"][slug]
        e.pop("nocked", None)
    if slug == "piercing_arrows":
        return 1.0, True, ""
    if slug == "fire_arrows":
        return economy.FIRE_ARROW_MULT, False, ""
    if slug == "poison_arrows":
        return 1.0, False, "poison"
    if slug == "slowing_arrows":
        return 1.0, False, "slow"
    return 1.0, False, ""


def _apply_shot_effect(p: dict, effect: str) -> str:
    """The special arrow's after-bite, with its limitation said out
    loud when it refuses (003 law: no silent numbers)."""
    e = p["encounter"]
    prof = _profile(p)
    if effect == "poison":
        immune = e["kind"] == "warden" or "venomproof" in (
            e.get("traits") or [])
        if immune:
            return (f"The venom beads off the {e['name']} — this one "
                    "doesn't poison.")
        if e.get("poison_left"):
            return "The venom is already in it — a second dose is wasted."
        e["poison_left"] = economy.POISON_ROUNDS
        e["poison_dmg"] = max(1, round(state.atk(p) * 0.25))
        return (f"The venom takes — {e['poison_dmg']} true damage a "
                f"round, {economy.POISON_ROUNDS} rounds, past any plate.")
    if effect == "slow":
        if prof.get("speed", economy.SPEED_NORMAL) <= economy.SPEED_SLOW:
            return (f"The {e['name']} was already dragging — the "
                    "slowing shaft changes nothing.")
        prof["speed"] = max(1, prof["speed"] - economy.SLOW_ARROW_DELTA)
        e["profile"] = prof
        return (f"The shaft bites tendon — the {e['name']} drops "
                f"{economy.SLOW_ARROW_DELTA} speed for this fight.")
    return ""


# fight actions that spend a round — the venom ticks and the golden
# shell rots exactly once per each.
_ROUND_ACTIONS = frozenset({
    "attack", "close_in", "open_distance", "run", "stand", "shield_wall",
    "sleep_spell", "treeline_shot", "drink_tonic", "use_oil", "throw_net",
    "use_hook", "use_strip", "use_curse", "use_veil", "use_apple"})


def _fx_tick(p: dict) -> bool:
    """Start-of-round upkeep for 006 effects. Returns True when the
    poison finished the monster (caller routes to _victory). Notes land
    on the encounter and fight_scene says them."""
    e = p["encounter"]
    if e.get("apple_hp", 0) > 0:
        e["apple_hp"] = int(e["apple_hp"] * (1 - economy.APPLE_DECAY))
        if e["apple_hp"] <= 0:
            e["_fx_note"] = "The golden shell flakes away to nothing."
    if e.get("poison_left", 0) > 0:
        e["poison_left"] -= 1
        dmg = e.get("poison_dmg", 0)
        e["hp"] -= dmg
        note = f"The venom works through it — {dmg} true damage."
        if e["poison_left"] <= 0:
            note += " The dose is spent."
        e["_fx_note"] = (e.get("_fx_note", "") + " " + note).strip()
        if e["hp"] <= 0:
            return True
    return False


def _train_nudge(p: dict) -> list[str]:
    """012: levels are bought, never granted. When the bar fills, point
    at the Guildhall instead of leveling — XP banks past the cap."""
    if p["xp"] < economy.xp_need(p["level"]):
        return []
    fee = economy.levelup_gold(p["level"])
    return [f"Your XP bar is full. The Guildhall trains climbers to "
            f"LEVEL {p['level'] + 1} — the fee is ◈ {fee:,}."]


def _report_shared_strike(p: dict) -> int:
    """022/001: a shared Warden fight is over (kill, death, or flight) —
    everything it cut away persists in the world pool. One warden_strike
    effect carries the fight's total; the server clamps and resolves."""
    e = p.get("encounter") or {}
    if not e.get("shared") or e.get("strike_sent"):
        return 0
    dealt = max(0, int(e.get("hp_max", 0)) - max(0, int(e.get("hp", 0))))
    if dealt <= 0:
        return 0
    e["strike_sent"] = True
    p.setdefault("_effects", []).append({
        "kind": "warden_strike", "floor": int(e.get("floor", 0)),
        "damage": dealt})
    _ledger(p, "warden_strike", note=f"floor {e.get('floor')} · {dealt}")
    # optimistic pool update so the next keep card reads right
    w = p.get("_world") or {}
    wd = w.get("warden") or {}
    if wd.get("floor") == e.get("floor"):
        wd["hp"] = max(0, int(wd.get("hp", 0)) - dealt)
    return dealt


def _shared_warden_victory(p: dict, floor) -> Scene:
    """The pool hit zero under YOUR blade. The server settles the fall —
    frontier raise, reward split by damage, letters to every striker —
    so this card promises nothing it doesn't know."""
    e = p["encounter"]
    dealt = _report_shared_strike(p)
    p["encounter"] = None
    p["location"] = "gate_town"
    return Scene(
        eyebrow=_eyebrow(p, floor),
        headline=f"{e['name']} collapses",
        support="The Warden's frame ticks as it cools. The whole tower "
                "heard that.",
        body_lines=[
            f"Your blade took the last {dealt:,} of it.",
            "The fall pays every striker by damage dealt — your share "
            "arrives with the word of it.",
            f"FLOOR {floor.floor + 1} opens for everyone the moment the "
            "tower counts the body.",
        ],
        options=_after_fight_options(p, floor),
        meters=meters(p),
        event_kind="boss",
        fx=_kill_fx(e, e["name"], True, _damage_type(p)),
    )


def _victory(p: dict, floor) -> Scene:
    e = p["encounter"]
    if e["kind"] == "warden" and e.get("shared"):
        return _shared_warden_victory(p, floor)
    fade = economy.fade_multiplier(p["unlocked_floor"], floor.floor)
    if e["kind"] == "warden":
        xp = round(economy.warden_xp(floor.floor) * fade)
        gold = round(economy.warden_gold(floor.floor) * fade)
        if floor.milestone:
            xp = round(floor.milestone.xp / 2 * fade)
            gold = round(floor.milestone.gold / 2 * fade)
        if e.get("echo"):
            # 022/001: a fallen Warden re-fought is an ECHO — half pay,
            # no world effect. Training and story, not progress.
            xp = round(xp * economy.WARDEN_ECHO_MULT)
            gold = round(gold * economy.WARDEN_ECHO_MULT)
    else:
        xp = round(state.rng_jitter(p, economy.xp_per_kill(floor.floor), 0.25) * fade)
        # 009: luck is a DAY now — the halfling racial bonus is retired.
        lucky = p["flags"].get("luck_day") == state.world_day()
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
    # 022/005: rested aether pays out here and ONLY here — on a kill's
    # XP, never on contract or strongbox payouts.
    rested = state.rested_bonus(p, xp)
    p["xp"] += xp + rested
    p["gold"] += gold
    _ledger(p, "kill", gold=gold, xp=xp + rested, note=e["name"])
    if e["kind"] == "wilds":
        # 022/004: the kill the engine just scored is the contract
        # board's only bookkeeping.
        contracts.note_kill(p, e, _damage_type(p))
    weekly.note(p, "kills")     # 022/005: the strongbox counts the week
    downed = (f"The {e['name']} goes down — no match for your "
              f"{weapon_name(p)}."
              if e["kind"] == "wilds" else f"The {e['name']} goes down.")
    lines = [downed, f"+ {xp} XP", f"+ ◈ {gold} carried gold"]
    if rested:
        lines.insert(2, f"+ {rested} XP rested — ✦ {p['rested']} left "
                        "in the pool")
    if e.get("specimen") == "alpha":
        # 006 §3.8 faucet cut: charms drop 30% → 10% — bought relics
        # need the free ones scarce.
        loot = state.rng_pick(p, [(100 - economy.ALPHA_CHARM_PCT, "medgel"),
                                  (economy.ALPHA_CHARM_PCT, "luck_charm")])
        p["inventory"][loot] = p["inventory"].get(loot, 0) + 1
        lines.append(f"▪ alpha spoils: {economy.APOTHECARY[loot].name}")
    lines += _train_nudge(p)

    first_clear = False
    if e["kind"] == "warden":
        # 022/001: the personal unlock is DELETED in the shared world —
        # the frontier moves only when the world Warden's pool empties.
        # Local dev play is a world of one: ITS frontier is personal.
        nxt = floor.floor + 1
        if e.get("echo"):
            lines.append("▪ an echo of a fallen Warden — half pay, and "
                         "the tower doesn't so much as creak")
        elif p.get("_world") is None and p["unlocked_floor"] < nxt:
            old_floor = p["unlocked_floor"]
            p["unlocked_floor"] = nxt
            first_clear = True
            lines.append(f"The lift grinds open. FLOOR {nxt} is yours to enter.")
            # 020: a first clear names what the new frontier opened —
            # relic shelves, gear bands, the honing cap reset.
            from .. import unlocks
            for u in unlocks.just_reached(p, p["level"], old_floor)[:3]:
                lines.append(f"{unlocks.glyph(u)} {u.title} — {u.why}")
        # guaranteed rare-loot roll (006 §3.8: charm 40% → 12% — the
        # gate is ≤ 1/3 of the old rate, and 15 missed it by a hair)
        loot = state.rng_pick(
            p, [(100 - economy.WARDEN_CHARM_PCT, "trollblood_tonic"),
                (economy.WARDEN_CHARM_PCT, "luck_charm")])
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
        fx=_kill_fx(e, e["name"], first_clear, _damage_type(p)),
    )


def _after_fight_options(p: dict, floor) -> list[Option]:
    opts = [Option("hunt", "Hunt the wilds again", "1 ⚡")]
    if p["unlocked_floor"] > floor.floor:
        opts.append(Option("gate", "Back to the tower gate"))
    opts.append(Option("keep", "The Warden's keep", "3 ⚡"))
    opts.append(Option("town", "Return to Roothollow"))
    return opts


def _paid_weapons(p: dict) -> list[tuple[str, str]]:
    """Every paid weapon the player owns as (where, slug) — the death
    pool. `where` is 'equipped' or 'pack'."""
    out = []
    w = p["gear"].get("weapon")
    g = economy.FORGE.get(w or "")
    if g and g.price > 0:
        out.append(("equipped", w))
    for slug, n in (p.get("inventory") or {}).items():
        it = economy.FORGE.get(slug)
        if it and it.slot == "weapon" and it.price > 0 and n > 0:
            out.append(("pack", slug))
    return out


def _repair_everything(p: dict) -> None:
    """006: the Reincarnation Spell's promise — every weapon and armor
    piece to full, worn or stashed."""
    for slot in economy.DURABILITY_SLOTS:
        g = economy.FORGE.get(p["gear"].get(slot) or "")
        if g and g.price > 0 and slot in (p.get("durability") or {}):
            p["durability"][slot] = economy.item_pool(g)
    for slug in list((p.get("durability_pack") or {})):
        g = economy.FORGE.get(slug)
        if g:
            p["durability_pack"][slug] = economy.item_pool(g)


def _death(p: dict, floor) -> Scene:
    e = p["encounter"]
    daily = p["daily"]
    if not daily.get("death_save"):
        daily["death_save"] = True
        _report_shared_strike(p)   # 022/001: the wounds you left persist
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
    # 006: the Stone of Undying cancels the death itself — but only one
    # life-guard works per fight, and the daily save comes first (free
    # things spend before bought things).
    if p["inventory"].get("stone_of_undying") and not e.get("life_used"):
        p["inventory"]["stone_of_undying"] -= 1
        if p["inventory"]["stone_of_undying"] <= 0:
            del p["inventory"]["stone_of_undying"]
        e["life_used"] = True
        p["hp"] = max(1, round(state.max_hp(p) * economy.STONE_REVIVE_PCT))
        return fight_scene(p, floor, note=(
            "The Stone of Undying burns to sand in your pocket — and "
            f"you stand back up at {p['hp']} HP. It is still here."))
    _report_shared_strike(p)       # 022/001: the wounds you left persist
    mercy = p["level"] <= economy.BEGINNER_MERCY_MAX_LEVEL
    lines = [f"Killed by the {e['name']}."]
    if mercy:
        # 004 §A.2: a bad first hour can't spiral — keep everything but
        # half the carried gold.
        lost_gold = p["gold"] - p["gold"] // 2
        p["gold"] //= 2
        if lost_gold:
            lines.append(f"− ◈ {lost_gold} carried gold, gone")
        lines.append("▪ your gear survives — the tower is gentler with "
                     "the newly arrived")
    elif p["inventory"].get("reincarnation_spell"):
        # 006 §3.6 protected: one spell burns — nothing is lost and the
        # whole kit repairs to full. The ONLY leak: spare spells.
        lost_gold = 0
        p["inventory"]["reincarnation_spell"] -= 1
        _repair_everything(p)
        lines.append("▪ the Weapon Reincarnation Spell burns instead of "
                     "you — nothing is lost")
        lines.append("▪ every weapon and armor piece stands repaired, "
                     "as if new-forged")
        spares = p["inventory"].get("reincarnation_spell", 0)
        leaked = sum(1 for _ in range(spares)
                     if state.roll_ok(p, economy.SPARE_SPELL_LEAK))
        if leaked:
            p["inventory"]["reincarnation_spell"] -= leaked
            lines.append(f"− {leaked} SPARE spell"
                         + ("s" if leaked > 1 else "")
                         + " lost in the flare — hoarded magic leaks")
        if p["inventory"].get("reincarnation_spell", 0) <= 0:
            p["inventory"].pop("reincarnation_spell", None)
    else:
        # 006 §3.6 unprotected: a random bite of gold, every paid weapon
        # rolls the void, the guard slots take wear instead of death.
        # 020: the FIRST unprotected death names the change once, so the
        # loss is legible even if the level-up card went unread.
        if not p["flags"].get("mercy_end_named"):
            p["flags"]["mercy_end_named"] = True
            lines.append("▪ the tower is no longer gentle with you — "
                         "from here, deaths cost gear and gold")
        frac = state.rng_int(p, round(economy.DEATH_GOLD_MIN * 100),
                             round(economy.DEATH_GOLD_MAX * 100)) / 100
        lost_gold = round(p["gold"] * frac)
        p["gold"] -= lost_gold
        if lost_gold:
            lines.append(f"− ◈ {lost_gold:,} carried gold "
                         f"({round(frac * 100)}%), gone")
        lost_names = []
        for where, slug in _paid_weapons(p):
            if not state.roll_ok(p, economy.DEATH_WEAPON_LOSS):
                continue
            g = economy.FORGE[slug]
            lost_names.append(g.name)
            if where == "equipped":
                p["gear"]["weapon"] = economy.class_starter(
                    p.get("clazz") or "").slug
                p["hone"]["weapon"] = 0
                (p.get("durability") or {}).pop("weapon", None)
            else:
                p["inventory"][slug] -= 1
                if p["inventory"][slug] <= 0:
                    del p["inventory"][slug]
                    (p.get("durability_pack") or {}).pop(slug, None)
        if lost_names:
            verb = "are" if len(lost_names) > 1 else "is"
            lines.append("▪ your " + " and ".join(lost_names)
                         + f" {verb} gone for good — the tower keeps "
                         "what falls")
        worn = []
        for slot in ("armor", "shield", "shoes"):
            g = economy.FORGE.get(p["gear"].get(slot) or "")
            dur = (p.get("durability") or {})
            if g and g.price > 0 and slot in dur:
                hit = round(economy.item_pool(g)
                            * economy.DEATH_DURABILITY_HIT)
                dur[slot] = max(0, dur[slot] - hit)
                worn.append(g.name)
        if worn:
            verb = "take" if len(worn) > 1 else "takes"
            lines.append("▪ your " + " and ".join(worn)
                         + f" {verb} the fall hard — half a lifetime of "
                         "wear, the Forge can mend it")
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

    # 006: round upkeep — the venom ticks and the golden shell rots on
    # every round-spending action, before the action itself resolves.
    if option_id in _ROUND_ACTIONS or option_id.startswith("use_"):
        if _fx_tick(p):
            return _victory(p, floor)

    # 006: nocking is free — switching arrows doesn't spend the round.
    if option_id.startswith("nock_"):
        slug = option_id.removeprefix("nock_")
        if slug in economy.QUIVER_SLUGS and p["inventory"].get(slug):
            e["nocked"] = slug
            r = economy.RELICS[slug]
            return fight_scene(p, floor, note=(
                f"You nock one of the {r.name.lower()} — "
                f"{r.effect}."))
        return fight_scene(p, floor)

    if option_id == "use_oil" and p["inventory"].get("weapon_oil") \
            and _damage_type(p) != "magic":
        p["inventory"]["weapon_oil"] -= 1
        if p["inventory"]["weapon_oil"] <= 0:
            del p["inventory"]["weapon_oil"]
        p["oil"] = economy.OIL_STRIKES
        hit = _monster_hit(p)
        if p["hp"] <= 0:
            return _death(p, floor)
        chase = _advance_chase(p)
        return fight_scene(p, floor, note=(
            f"You slick the {weapon_name(p)} — the next "
            f"{economy.OIL_STRIKES} strikes bite +25%. "
            + _counter_text(p, hit,
                            lead=f"The {e['name']} presses while you pour")
            + (f" {chase}" if chase else "")))

    if option_id == "throw_net" and p["inventory"].get("entangling_net") \
            and e["kind"] != "warden":
        p["inventory"]["entangling_net"] -= 1
        if p["inventory"]["entangling_net"] <= 0:
            del p["inventory"]["entangling_net"]
        e["netted"] = True
        return fight_scene(p, floor, note=(
            f"The net blooms open and drops — the {e['name']} goes down "
            "thrashing in cord. Its round is spent, and it closes no "
            "ground through the mesh."))

    if option_id == "use_hook" and p["inventory"].get("sky_hook") \
            and _profile(p).get("flying"):
        p["inventory"]["sky_hook"] -= 1
        if p["inventory"]["sky_hook"] <= 0:
            del p["inventory"]["sky_hook"]
        prof = _profile(p)
        prof["flying"] = False
        e["profile"] = prof
        hit = _monster_hit(p)
        if p["hp"] <= 0:
            return _death(p, floor)
        chase = _advance_chase(p)
        return fight_scene(p, floor, note=(
            "The sky-hook's line goes taut — whatever height it had, "
            "it fights on your ground now. "
            + _counter_text(p, hit,
                            lead=f"The {e['name']} comes down swinging")
            + (f" {chase}" if chase else "")))

    if option_id == "use_strip" and p["inventory"].get("strip_potion") \
            and _profile(p).get("resist", "none") != "none":
        p["inventory"]["strip_potion"] -= 1
        if p["inventory"]["strip_potion"] <= 0:
            del p["inventory"]["strip_potion"]
        prof = _profile(p)
        prof["resist"] = "none"
        e["profile"] = prof
        hit = _monster_hit(p)
        if p["hp"] <= 0:
            return _death(p, floor)
        chase = _advance_chase(p)
        return fight_scene(p, floor, note=(
            f"The vial bursts across the {e['name']} — its spellguard "
            "dissolves like frost in rain. "
            + _counter_text(p, hit)
            + (f" {chase}" if chase else "")))

    if option_id == "use_curse" and p["inventory"].get("curse_scroll") \
            and _profile(p).get("armor", "none") != "none":
        p["inventory"]["curse_scroll"] -= 1
        if p["inventory"]["curse_scroll"] <= 0:
            del p["inventory"]["curse_scroll"]
        prof = _profile(p)
        prof["armor"] = {"high": "low", "med": "low"}.get(
            prof["armor"], "none")
        e["profile"] = prof
        hit = _monster_hit(p)
        if p["hp"] <= 0:
            return _death(p, floor)
        chase = _advance_chase(p)
        return fight_scene(p, floor, note=(
            "You read the curse and the words take — its plate hangs "
            "half as sure. "
            + _counter_text(p, hit)
            + (f" {chase}" if chase else "")))

    if option_id == "use_polymorph" and p["inventory"].get("polymorph_dust") \
            and e["kind"] != "warden":
        p["inventory"]["polymorph_dust"] -= 1
        if p["inventory"]["polymorph_dust"] <= 0:
            del p["inventory"]["polymorph_dust"]
        name = e["name"]
        p["encounter"] = None
        p["location"] = "gate_town"
        return Scene(
            eyebrow=_eyebrow(p, floor),
            headline="A harmless thing blinks up at you",
            support="The dust settles. So does everything else.",
            body_lines=[f"The {name} is a fat vole now, nosing the grass.",
                        "No loot, no XP — the fight simply never finishes."],
            options=_after_fight_options(p, floor),
            meters=meters(p))

    if option_id == "use_veil" and p["inventory"].get("veil_draught"):
        if e.get("life_used"):
            return fight_scene(p, floor, note=(
                "One life-guard per fight — something protective has "
                "already spent itself here."))
        p["inventory"]["veil_draught"] -= 1
        if p["inventory"]["veil_draught"] <= 0:
            del p["inventory"]["veil_draught"]
        e["veiled"] = True
        e["life_used"] = True
        return fight_scene(p, floor, note=(
            "The draught goes down cold — the world slides off you. "
            "Nothing can touch you until your first strike lands."))

    if option_id == "use_apple" and p["inventory"].get("golden_apple"):
        if e.get("life_used"):
            return fight_scene(p, floor, note=(
                "One life-guard per fight — something protective has "
                "already spent itself here."))
        p["inventory"]["golden_apple"] -= 1
        if p["inventory"]["golden_apple"] <= 0:
            del p["inventory"]["golden_apple"]
        e["apple_hp"] = round(state.max_hp(p) * economy.APPLE_SHIELD_MULT)
        e["life_used"] = True
        hit = _monster_hit(p)
        if p["hp"] <= 0:
            return _death(p, floor)
        chase = _advance_chase(p)
        return fight_scene(p, floor, note=(
            f"You eat the golden apple to the core — a shell of light "
            f"({e['apple_hp']}) settles over you and every blow lands "
            "half as hard. It rots as the rounds pass. "
            + _counter_text(p, hit)
            + (f" {chase}" if chase else "")))

    if option_id == "use_severing" and p["inventory"].get("severing_word") \
            and e["kind"] != "warden":
        p["inventory"]["severing_word"] -= 1
        if p["inventory"]["severing_word"] <= 0:
            del p["inventory"]["severing_word"]
        e["hp"] = 0
        e["_fx_note"] = ""
        s = _victory(p, floor)
        s.body_lines.insert(0, "You speak the Severing Word once, "
                            "quietly, and the fight is simply over.")
        return s

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
            dealt = _report_shared_strike(p)   # 022/001: wounds persist
            p["encounter"] = None
            p["location"] = "gate_town"
            lines = ["You put fence and dark between you and it."]
            if dealt:
                lines.append(f"▪ the {dealt:,} you cut away stays cut — "
                             "the Warden holds your wounds for the next "
                             "blade")
            return Scene(
                eyebrow=_eyebrow(p, floor),
                headline="You break away",
                support="No shame the grass will remember.",
                body_lines=lines + ([snap] if snap else []),
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
        # 022/001: the shared Warden never sleeps — there is nothing to
        # walk past; the floor opens when its pool empties, not before.
        if e.get("shared"):
            return fight_scene(p, floor, note=(
                "You shape the lullaby and it dies against the Warden's "
                "hull. A war-machine wearing a body does not sleep."))
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
        mult, pierce, effect = _quiver_shot(p)   # 006: special ammo rides
        e.pop("veiled", None)                    # the veil breaks here too
        if not pierce and _profile(p).get("armor") in ("med", "high"):
            # 017: Medium+ plate over the vitals — the long shot loses
            # its double (Low plate still leaves gaps for a marksman;
            # 006: a piercing arrow never meets the plate at all)
            dmg = _player_hit(p, mult=mult)
            if e["hp"] <= 0:
                return _victory(p, floor)
            fxn = _apply_shot_effect(p, effect) if effect else ""
            chase = _advance_chase(p)
            return fight_scene(p, floor, note=(
                f"Your arrow snaps against its plate — {dmg} damage, "
                "no clean gap for a killing shot."
                + (f" {fxn}" if fxn else "")
                + (f" {chase}" if chase else "")
                + (f" {snap}" if snap else "")))
        dmg = _player_hit(p, mult=2.0 * mult, pierce=pierce)
        if e["hp"] <= 0:
            return _victory(p, floor)
        fxn = _apply_shot_effect(p, effect) if effect else ""
        chase = _advance_chase(p)
        return fight_scene(p, floor, note=(
            f"Your shot from cover takes it for {dmg} before it finds you."
            + (f" {fxn}" if fxn else "")
            + (f" {chase}" if chase else "")
            + (f" {snap}" if snap else "")))

    # default: attack
    # 004 §3.2: off-class hands — a bow burns bought arrows for anyone
    # but an archer, and every off-class swing misses 25% of the time
    # (the miss eats the round; the monster answers).
    # 006: a nocked special arrow IS the ammo for this shot.
    special_ready = bool(e.get("nocked")
                         and p["inventory"].get(e["nocked"], 0) > 0)
    if _off_class(p):
        if _damage_type(p) == "ranged" and not special_ready:
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
    # 006: the special arrow shapes the shot; the veil breaks on your
    # first strike — the answer to it lands.
    mult, pierce, effect = _quiver_shot(p)
    e.pop("veiled", None)
    dmg = _player_hit(p, mult=mult, pierce=pierce)
    if e["hp"] <= 0:
        return _victory(p, floor)
    fxn = _apply_shot_effect(p, effect) if effect else ""
    if pierce and dmg > 0:
        fxn = "The shaft goes through plate like paper."
    back = _monster_hit(p)
    if p["hp"] <= 0:
        return _death(p, floor)
    chase = _advance_chase(p)
    return fight_scene(p, floor, note=(
        f"{_strike_text(p, dmg)}"
        + (f" {fxn}" if fxn else "")
        + f" {_counter_text(p, back)}"
        + (f" {chase}" if chase else "")
        + (f" {snap}" if snap else "")))
