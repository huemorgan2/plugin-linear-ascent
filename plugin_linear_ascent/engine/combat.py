"""Combat resolver — economy §2–§3 math, deterministic rolls.

The encounter lives in the player doc; every function mutates the doc and
returns a Scene. Flows are gated here, not in prose: out-of-order calls
never reach these functions (core.py dispatches).
"""

from __future__ import annotations

import datetime as dt
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


def _typed_slug(slug: str, p: dict | None, line: str = "") -> str:
    """049: the scene drawn for THIS climber — {slug}_{race}_{line} art
    (the player's race x the path of the weapon in hand) wins over the
    creature's solo art when it ships. Returns slug unchanged when no
    typed art exists."""
    if not slug or not p:
        return slug
    race = p.get("race") or ""
    line = line or _train_path(p)
    if race and _creature_art(f"{slug}_{race}_{line}"):
        return f"{slug}_{race}_{line}"
    return slug


def _fight_banner(e: dict, floor, p: dict | None = None) -> str:
    """Creature's own art if shipped (plan 005), else the old behavior."""
    if e["kind"] == "warden":
        if floor.floor % 10 == 0:  # milestone boss banners ship in banners/
            return "gnarl" if floor.floor == 10 else floor.banner
        slug = f"warden_{floor.floor:03d}"
        typed = _typed_slug(slug, p)
        if typed != slug:
            return typed
        return slug if _creature_art(slug) else ""
    slug = e.get("id", "")
    if slug:
        typed = _typed_slug(slug, p)
        if typed != slug:
            return typed
        if _creature_art(slug):
            return slug
    return floor.banner if e["kind"] == "wilds" else ""


# 009: kill GIF variants per damage type — the ending shows YOUR kill:
# steel is the warrior's blade, arrows the archer's shot, magic the
# wizard's cast. Family match is per-token (prefix) so "curator" never
# plays the rat's death.
_KILL_FAMILIES = ("brackjaw", "tortoise", "haunt", "goblin", "boar",
                  "wolf", "rat")
_KILL_SUFFIX = {"melee": "melee", "ranged": "arrow", "magic": "magic"}

# 038: a kinded creature's ending shows what the kill MEANS — a cure,
# a death, or an eviction — never a generic kill reel.
_BREED_FX_VERB = {"native": "freed", "pressed": "fall",
                  "wrongmade": "evicted"}

# 049: the landing damage type names the weapon line of the last blow.
_LINE_OF_DTYPE = {"melee": "blade", "ranged": "bow", "magic": "staff"}


def _kill_fx(e: dict, name: str, first_clear: bool, dtype: str = "",
             p: dict | None = None) -> str:
    """011/009: event animation slug for a victory scene. A typed kill
    GIF (family × landing damage type) wins; the family's untyped kill
    is the fallback; a first floor clear plays the gate opening. The
    renderer silently skips slugs with no shipped art.

    038: kinded creatures (world-lore §5) resolve by what the kill
    means instead of the family table — {id}_{verb} first, then the
    kind's generic {kind}_{verb}, then nothing. The family kill reels
    are deliberately NOT a fallback here: a death animation on a cured
    Native would tell the wrong story. Legacy floors (kind == "") keep
    the family logic exactly."""
    breed = e.get("breed", "")
    if breed in _BREED_FX_VERB:
        if first_clear:
            return "ascent_open"
        verb = _BREED_FX_VERB[breed]
        slug = e.get("id", "")
        if not slug and e.get("kind") == "warden" and e.get("floor"):
            slug = f"warden_{e['floor']:03d}"
        # 049: the ending shows YOUR kill — the movie keyed by the
        # player's race and the line of the weapon that landed the
        # last blow wins over the untyped ending.
        if slug and p:
            race = p.get("race") or ""
            wline = _LINE_OF_DTYPE.get(dtype, "")
            if race and wline and _event_art(
                    f"{slug}_{verb}_{race}_{wline}"):
                return f"{slug}_{verb}_{race}_{wline}"
        if slug and _event_art(f"{slug}_{verb}"):
            return f"{slug}_{verb}"
        if _event_art(f"{breed}_{verb}"):
            return f"{breed}_{verb}"
        return ""
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
        level=p["level"],
        atk=state.atk(p),
        dfs=state.dfs(p),
        spd=economy.player_speed(p),
        # 031 §4: the header line — who is climbing
        name=p.get("name") or "",
        race=p.get("race") or "",
        # 048: the class field died — the wire slot carries the path of
        # the weapon in hand so old clients keep a sane header.
        clazz=economy.PATH_OF_LINE.get(_weapon_line(p), ""),
        # the banner: worldd injects w["faction"] for members; local
        # dev mode keeps the legacy doc-string guild name.
        faction=(((p.get("_world") or {}).get("faction") or {})
                 .get("name") or p.get("guild") or ""))


def _eyebrow(p: dict, floor) -> str:
    return f"FLOOR {floor.floor} · {floor.biome.upper()} · {floor.zone.upper()}"


def _ledger(p: dict, kind: str, gold: int = 0, xp: int = 0, note: str = "") -> None:
    p.setdefault("_ledger", []).append(
        {"kind": kind, "gold": gold, "xp": xp, "note": note})


def would_probably_kill(p: dict, floor, enc) -> bool:
    """025 §5: could this creature, met right now, finish you? Analytic —
    rounds-to-kill against damage-taken-per-round, read off the player's
    CURRENT sheet and CURRENT wounds. Deliberately blind to consumables,
    relics and the opening round at range: it is a weighting hint, not a
    promise (see MUST_BE_DONE_LATER.md §6)."""
    traits = tuple(getattr(enc, "traits", ()) or ())
    atk, dfs, hp = economy.creature_stats(floor.floor, traits)
    prof = economy.profile_from_traits(traits)
    if prof["bulwark"]:
        hp = round(hp * economy.BULWARK_HP_MULT)
    dmg = economy.typed_damage_048(
        _train_path(p), round(0.75 * state.atk(p)), dfs, prof["type"],
        focus=bool((p.get("mastery") or {}).get("staff")))
    if dmg <= 0:
        return True            # a blade that cannot reach it — 017's zero
    rounds = max(1, -(-hp // dmg))
    raw = 0.75 * atk
    bite = max(max(1, -(-raw // economy.CHIP_DIVISOR)),
               raw - state.dfs(p) // 2)
    dodge = economy.dodge_pct(economy.player_speed(p), prof["speed"])
    return rounds * bite * (1 - dodge / 100) >= (
        economy.LETHAL_SHARE * max(1, p["hp"]))


def hunt_table(p: dict, floor, deep: bool = False) -> list[tuple[int, str]]:
    """The floor's roster, weighted for THIS player. Content weights are
    scaled up first so the cuts still have resolution. 039: prey draws
    fade with altitude and the lethal-draw mercy loosens — the floor
    shapes the table, not just the costumes. A DEEP hunt drops prey
    entirely — feeble bites AND frail bodies — and skips the rubber
    band: the player chose this."""
    if deep:
        table = [(e.weight * 100, e.id) for e in floor.encounters
                 if not {"feeble", "frail"}
                 & set(tuple(getattr(e, "traits", ()) or ()))]
        # a roster of nothing but prey (none exist today) falls back
        return table or [(e.weight * 100, e.id) for e in floor.encounters]
    table = []
    fade = economy.prey_weight_mult(floor.floor)
    cut = economy.rubber_band_cut(floor.floor)
    for e in floor.encounters:
        w = e.weight * 100
        traits = tuple(getattr(e, "traits", ()) or ())
        if "feeble" in traits:
            w = max(1, round(w * fade))
        if would_probably_kill(p, floor, e):
            w = max(1, round(w * cut))
        table.append((w, e.id))
    return table


def start_encounter(p: dict, floor, enc, kind: str = "wilds",
                    deep: bool = False) -> Scene:
    # 017 §2: the defense profile — armor/resist tiers, flying, bulwark,
    # speed — derived from qualitative content traits, priced in economy.
    traits = tuple(getattr(enc, "traits", ()) or ()) if enc is not None else ()
    if kind == "warden":
        # Milestone floors are quorum bosses; the solo-tuned line is the
        # fallback until a war party gathers.
        atk, dfs, hp = economy.warden_stats(floor.floor)
        name = floor.warden_name
        prose = floor.warden_prose
        prof = economy.warden_profile(floor.floor)
    else:
        # 025 §1: the floor sets the baseline; the archetype says what
        # THIS animal is. Before 025 every creature on a floor shared one
        # stat line — four costumes, one monster.
        atk, dfs, hp = economy.creature_stats(floor.floor, traits)
        name, prose = enc.name, enc.prose
        prof = economy.profile_from_traits(traits)
        if (note := economy.archetype_note(traits)):
            prose = f"{prose} It is {note}."
    if prof["bulwark"]:
        hp = round(hp * economy.BULWARK_HP_MULT)
    specimen = "common"
    if kind == "wilds":
        # 008: specimen roll — real variance, visible on the opener so
        # fighting an alpha is an informed choice. 039: weights are
        # floor-shaped — runts thin out at altitude; a DEEP hunt rolls
        # its own table (no runts at all).
        spec_table = (economy.DEEP_SPECIMENS if deep
                      else economy.specimen_table(floor.floor))
        specimen = state.rng_pick(
            p, [(s["weight"], k) for k, s in spec_table.items()
                if s["weight"] > 0])
        spec = spec_table[specimen]
        atk = round(atk * spec["atk"])
        hp = round(hp * spec["hp"])
        if spec["tag"]:
            prose = f"{prose} This one is {spec['tag']}."
    if deep and kind == "wilds":
        # 039 §2: the prime — harder in ATK and SPEED, NEVER in HP.
        # The fight gets scarier, not longer.
        atk = round(atk * economy.DEEP_ATK_MULT)
        prof["speed"] += economy.DEEP_SPEED_BONUS
        prose = ("You leave the lit paths. What finds you out here "
                 f"was never hunted thin. {prose}")
    if specimen == "alpha":
        prof["speed"] += economy.ALPHA_SPEED_BONUS
    p["encounter"] = {
        "kind": kind, "name": name, "prose": prose,
        "id": (enc.id if enc is not None else ""),
        # 038: the three kinds of monster (world-lore §5) — what a kill
        # MEANS. Runtime key is "breed" because "kind" on this dict
        # already means wilds/warden. A Warden is Wrongmade by
        # definition; "" is a legacy floor and keeps today's copy.
        "breed": ("wrongmade" if kind == "warden"
                  else (getattr(enc, "kind", "") or "")
                  if enc is not None else ""),
        # 038: the true creature under the fever — set for natives.
        "was": ((getattr(enc, "was", "") or "")
                if kind != "warden" and enc is not None else ""),
        "specimen": specimen, "traits": list(traits),
        "deep": bool(deep and kind == "wilds"),
        "profile": prof,
        "atk": atk, "def": dfs, "hp": hp, "hp_max": hp,
        "floor": floor.floor, "shot_used": False,
        # 040: the treeline shot is an opener — any attack burns it.
        "attacked": False,
        # 017 §2.4: fights open at range — bows and spells carry,
        # steel must close. 036: "at range" is gap 1 on the ladder.
        "range": "at_range", "gap": 1,
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
    t = prof.get("type", "plain")
    if dt == "melee":
        return t == "fly"
    if dt == "ranged":
        return t == "armoured"
    if dt == "magic":
        return t == "magic_resist"
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


def _gap(p: dict) -> int:
    """036: the gap in lengths — 0 is close quarters, 1 is the classic
    at_range opening, 2–3 are the archer's made ground. Derived from
    `range` first so every pre-036 doc (and every test that pins `range`
    by hand) reads correctly."""
    if _range_state(p) != "at_range":
        return 0
    return max(1, int(p["encounter"].get("gap", 1)))


def _advance_chase(p: dict) -> str:
    """End of an at-range round: the monster tries to close the gap
    (§2.4 p_close). Returns the line that tells the player what moved.
    036: the gap is a ladder now — each successful close eats ONE length;
    only the last one puts the monster in your face."""
    e = p["encounter"]
    if e.get("range") != "at_range":
        return ""
    if e.get("netted"):
        # 006: it cannot close through the net — this attempt is the
        # net's last service.
        e.pop("netted", None)
        return f"{_the(e['name'])} tears at the net instead of the ground."
    if state.roll_ok(p, economy.p_close(_mspd(p), economy.player_speed(p))):
        gap = _gap(p) - 1
        e["gap"] = gap
        if gap <= 0:
            e["range"] = "close"
            return f"{_the(e['name'])} closes the gap — it is on you now."
        return (f"{_the(e['name'])} eats a length of the open ground — "
                f"{gap} between you now.")
    return f"{_the(e['name'])} comes on across open ground."


def _profile_tiers(prof: dict) -> list[str]:
    """The profile as its sign — the [i] dossier's rows and the text
    fallback's compact line share this list."""
    bits = []
    t = prof.get("type", "plain")
    if t != "plain":
        bits.append(f"{economy.TYPE_SIGN[t]} {economy.TYPE_NAME[t]}")
    if prof.get("bulwark"):
        bits.append("bulwark")
    spd = prof.get("speed", economy.SPEED_NORMAL)
    if spd >= economy.SPEED_FAST:
        bits.append("fast")
    elif spd <= economy.SPEED_SLOW:
        bits.append("slow")
    return bits


def _profile_line(prof: dict) -> str:
    return " · ".join(_profile_tiers(prof))


def _breed_line(e: dict) -> str:
    """038: one dossier line naming WHAT the thing is (world-lore §5),
    so the [i] card says what the kill will mean before it lands."""
    breed = e.get("breed", "")
    if breed == "native":
        # `was` is a noun phrase by contract; shed a stray final period
        # so the splice never doubles up.
        was = (e.get("was", "") or "an animal").rstrip(" .")
        return f"Fevered — a possession riding {was}."
    if breed == "pressed":
        return "A conscript of the tower. Killing it is a death, not a cure."
    if breed == "wrongmade":
        return "A made thing. Breaking it is eviction, not killing."
    return ""


def _lore(e: dict, floor) -> str:
    """003: the dossier's flavor line, from content by encounter id.
    038: kinded creatures get one more line naming what they are."""
    slug = e.get("id", "")
    base = ""
    for enc in getattr(floor, "encounters", ()):
        if enc.id == slug:
            base = getattr(enc, "lore", "") or ""
            break
    line = _breed_line(e)
    if base and line:
        return f"{base} {line}"
    return base or line


def _drop_ranges(p: dict, floor) -> dict:
    """030 Phase 7: the dossier says the odds — coin and XP ranges from
    the SAME math _victory rolls (jitter band × fade × specimen ×
    profile), so the promise and the payout can't drift. 043: base pay
    keys off the creature's BAR — toughness is priced once, by the
    anchor, and the old threat multiplier is gone."""
    e = p["encounter"]
    fade = economy.fade_multiplier(p["unlocked_floor"], floor.floor)
    bar = economy.creature_bar(floor.floor, e.get("traits") or ())
    deep = economy.deep_reward_mult(floor.floor) if e.get("deep") else 1.0
    g_mult = (economy.SPECIMENS[e.get("specimen", "common")]["gold"]
              * economy.profile_gold_mult(_profile(p)) * fade * deep)
    g = economy.gold_per_kill(bar)
    x = economy.xp_per_kill(bar)
    x_mult = fade * deep
    return {
        "gold": [max(1, round(g * 0.5 * g_mult)),
                 max(1, round(g * 1.5 * g_mult))],
        "xp": [max(1, round(x * 0.75 * x_mult)),
               max(1, round(x * 1.25 * x_mult))],
    }


def _warden_drop_ranges(p: dict, floor) -> dict:
    """031 §6: the Warden [i] declares its purse like every monster —
    from the SAME math the payouts use, so promise and payout can't
    drift. Solo: the kill purse itself. Shared: your estimated cut
    for one full exchange of damage (the real cut scales with damage)."""
    e = p["encounter"]
    n = floor.floor
    if e.get("shared"):
        mult = economy.world_warden_reward_mult(n)
        share = economy.pool_unit(n) / max(1, economy.world_warden_hp(n))
        g = economy.warden_gold(n) * mult * share
        x = economy.warden_xp(n) * mult * share
        return {"gold": [max(1, round(g * 0.8)), max(1, round(g * 1.2))],
                "xp": [max(1, round(x * 0.8)), max(1, round(x * 1.2))]}
    fade = economy.fade_multiplier(p["unlocked_floor"], n)
    x = economy.warden_xp(n) * fade
    g = economy.warden_gold(n) * fade
    if floor.milestone:
        x = floor.milestone.xp / 2 * fade
        g = floor.milestone.gold / 2 * fade
    g, x = max(1, round(g)), max(1, round(x))
    return {"gold": [g, g], "xp": [x, x]}


def _enemy_payload(p: dict, floor) -> dict:
    """003: everything the [i] card and the fight header need, in one
    dict on the Scene — the renderer never reads the player doc."""
    e = p["encounter"]
    prof = _profile(p)
    pspd = economy.player_speed(p)
    return {
        # 030 Phase 7: additive keys — old renderers drop them (wire law)
        "story": _lore(e, floor),
        "drops": (_drop_ranges(p, floor) if e["kind"] == "wilds"
                  else _warden_drop_ranges(p, floor)
                  if e["kind"] == "warden" else None),
        "name": e["name"],
        "hp": max(0, e["hp"]), "hp_max": e["hp_max"],
        "atk": e["atk"], "def": e["def"],
        "profile": prof,
        "tiers": _profile_tiers(prof),
        "range": e.get("range", ""),
        "gap": _gap(p),
        "lore": _lore(e, floor),
        # 038: additive keys — the three-kinds read, for renderers that
        # want to badge it (old renderers drop them, wire law).
        "breed": e.get("breed", ""),
        "was": e.get("was", ""),
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
    if inv.get("strip_potion") and prof.get("type") == "magic_resist":
        opts.append(Option("use_strip", "Hurl the strip potion",
                           "spellguard, gone"))
    if inv.get("curse_scroll") and prof.get("type") == "armoured":
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


def _pred_damage(p: dict, path: str, rank: int) -> int:
    """048 T2: the number on the attack row BEFORE the click — this
    rank's mean swing through the triangle against THIS monster."""
    e = p["encounter"]
    atk_full = state.atk(p)
    lo = round(economy.TRAIN_ROLL_FLOOR(rank) * atk_full)
    return economy.typed_damage_048(
        path, round((lo + atk_full) / 2), e["def"],
        _profile(p).get("type", "plain"),
        focus=bool((p.get("mastery") or {}).get("staff")))


def _verdict(p: dict) -> list[str]:
    """048 T2: the verdict before the first swing — every held weapon's
    ACTUAL answer with its rank, and the full answer the player does
    NOT hold, named as the lever. Path words only (the pane is
    class-free)."""
    mtype = _profile(p).get("type", "plain")
    lead = {"fly": "⚡ It flies.", "armoured": "⛨ Armoured.",
            "magic_resist": "✧ Spellguarded."}.get(mtype, "")
    lines = []
    held_paths = set()
    for slug in _held_slugs(p):
        g = economy.FORGE[slug]
        path = economy.PATH_OF_LINE.get(g.line, "blade")
        held_paths.add(path)
        mult = economy.TYPE_MULT[mtype][path]
        word = ("cannot reach it" if mult <= 0
                else economy.answer_word(mult))
        lines.append(f"Your {g.name}: {word} — "
                     f"{path} rank {_rank_of(p, path)}.")
    if not any(economy.TYPE_MULT[mtype][h] >= 1.0 for h in held_paths):
        full = {"blade": "Steel bites full", "bow": "A bow bites full",
                "staff": "A staff bites full"}
        for path in ("blade", "bow", "staff"):
            if path not in held_paths \
                    and economy.TYPE_MULT[mtype][path] >= 1.0:
                lines.append(f"{full[path]} — yours is rank "
                             f"{_rank_of(p, path)}.")
                break
    if lead and lines:
        lines[0] = f"{lead} {lines[0]}"
    return lines


def fight_scene(p: dict, floor, opener: bool = False, note: str = "") -> Scene:
    e = p["encounter"]
    at_range = _range_state(p) == "at_range"
    # every swing at a Warden costs energy — priced on the row.
    strike_hint = (f"{economy.COST_WARDEN_STRIKE} ⚡"
                   if e["kind"] == "warden" else "")
    # 017 §2.4: at range steel cannot attack — Close in replaces it.
    # In close quarters anyone may try to Open distance.
    if at_range and _damage_type(p) == "melee":
        opts = [Option("close_in", "Close in", "cross the ground")]
    else:
        # 048 T2: rank and predicted damage on the row, before the click.
        lead_path = _train_path(p)
        lead_hint = (f"{lead_path} rank {_train_rank(p)} — "
                     f"~{_pred_damage(p, lead_path, _train_rank(p))} "
                     "vs this one")
        if strike_hint:
            lead_hint = f"{strike_hint} · {lead_hint}"
        opts = [Option("attack", "Attack", lead_hint)]
    # 048: one attack row per HELD weapon — the lead hand is "attack",
    # the other slots swing by name (choosing one promotes it). Steel
    # in a side slot can't reach at range: close in first.
    cur = p["gear"].get("weapon") or ""
    for slug in _held_slugs(p):
        if slug == cur:
            continue
        g = economy.FORGE[slug]
        if at_range and economy.DAMAGE_TYPE.get(g.line, "melee") == "melee":
            # 049.1: the row used to vanish at range — a held blade
            # looked lost until close quarters. It shows, locked, and
            # explains itself (048 N7 law).
            opts.append(Option(
                f"attack_{slug}", f"Attack — {g.name}",
                "steel can't reach at range — close in first",
                locked=True))
            continue
        path = economy.PATH_OF_LINE.get(g.line, "blade")
        opts.append(Option(
            f"attack_{slug}", f"Attack — {g.name}",
            f"{path} rank {_rank_of(p, path)} — "
            f"~{_pred_damage(p, path, _rank_of(p, path))} vs this one"))
    # 040: one verb for making ground. The bow's gap ladder (036) and
    # the footwork break (031 §7) read as duplicates on the menu, so only
    # one "Open distance" row ever shows: the marksman's — always works,
    # the monster may collect a toll — replaces the gamble outright.
    # 048 N7: giving ground ON PURPOSE is rank-6 bowwork; the draw
    # bonus on the row appears once rank 8 makes it real.
    bow_rank = _rank_of(p, "bow")
    if _damage_type(p) == "ranged" and _gap(p) < economy.GAP_MAX:
        nxt = _gap(p) + 1
        if bow_rank >= economy.GAP_OPEN_RANK:
            hint = (f"shot ×{economy.bow_gap_mult(nxt):g} "
                    f"at {nxt} length{'s' if nxt > 1 else ''}"
                    if bow_rank >= economy.GAP_DRAW_RANK
                    else f"give ground on purpose — "
                         f"{nxt} length{'s' if nxt > 1 else ''}")
            opts.append(Option("create_distance", "Open distance", hint))
        else:
            opts.append(Option(
                "create_distance", "Open distance",
                f"needs Bow rank {economy.GAP_OPEN_RANK} "
                f"(you: {bow_rank})", locked=True))
    # 031 §7: you cannot open ground from something as fast as you —
    # the row only shows when your legs actually beat its legs.
    elif not at_range and economy.player_speed(p) > _mspd(p):
        opts.append(Option("open_distance", "Open distance"))
    opts += [
        Option("stand", "Stand your ground"),
        Option("run", "Run away"),
    ]
    # 048 N7: the weapon in a slot opens its row; the trained rank
    # unlocks it. A locked row stays clickable and explains itself.
    shield = economy.FORGE.get(p["gear"].get("shield") or "")
    if _held_melee(p) and shield and shield.line != "sorcerer":
        r = _rank_of(p, "blade")
        if r >= economy.WALL_RANK:
            opts.append(Option("shield_wall", "Shield wall", "",
                               aether=True))
        else:
            opts.append(Option(
                "shield_wall", "Shield wall",
                f"needs Blade rank {economy.WALL_RANK} (you: {r})",
                locked=True, aether=True))
    if _held_of_line(p, "sorcerer"):
        r = _rank_of(p, "staff")
        if r >= economy.SLEEP_RANK:
            opts.append(Option(
                "sleep_spell", "Sleep spell",
                f"{economy.sleep_xp_cost(floor.floor)} XP", aether=True))
        else:
            opts.append(Option(
                "sleep_spell", "Sleep spell",
                f"needs Staff rank {economy.SLEEP_RANK} (you: {r})",
                locked=True, aether=True))
    if _held_of_line(p, "archer") and not e["shot_used"] \
            and not e.get("attacked") and at_range:
        # 040: the OPENING move — taken from the distance, before the
        # first attack. Once you have attacked, the cover is blown and
        # the row is gone for the rest of the fight; in close quarters
        # there is no treeline to shoot from.
        r = _rank_of(p, "bow")
        if r >= economy.TREELINE_RANK:
            opts.append(Option("treeline_shot", "Treeline shot",
                               strike_hint, aether=True))
        else:
            opts.append(Option(
                "treeline_shot", "Treeline shot",
                f"needs Bow rank {economy.TREELINE_RANK} (you: {r})",
                locked=True, aether=True))
    if p["inventory"].get("trollblood_tonic"):
        opts.append(Option("drink_tonic", "Drink trollblood tonic", "full heal"))
    # 022/008: below a quarter bar, a dying climber can call the floor —
    # once per fight, world mode only (a flare needs someone to see it).
    if p.get("_world") is not None and not e.get("flared") \
            and p["hp"] <= round(state.max_hp(p) * economy.FLARE_HP_PCT):
        opts.append(Option(
            "flare", "Send up a flare",
            f"{economy.FLARE_AETHER} XP · every hot blade sees it",
            aether=True))
    opts += _relic_options(p)

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
        # 048 T2: the sign's whole triangle, then the verdict.
        body.append(economy.type_line(_profile(p).get("type", "plain")))
        body += _verdict(p)
    if note:
        body.append(note)
    fx_note = e.pop("_fx_note", "")
    if fx_note:
        body.append(fx_note)
    # 022/008: an answered flare folds into the fight as story plus one
    # free disengage — read from the injected world row on the flared
    # player's own act, never pushed into the doc from outside.
    fw = (p.get("_world") or {}).get("flare") if e.get("flared") else None
    if fw and fw.get("own") and fw.get("answered_by") \
            and not e.get("rescue_seen"):
        e["rescue_seen"] = True
        e["rescued"] = True
        body.append(f"{fw['answered_by']} answered your flare — the "
                    f"{e['name']} wheels to face the new blade. Run now: "
                    "it will not chase you.")
    # 022/003: the number breathes — every round re-reads who is hot on
    # this floor, and changes fold in as story lines.
    hot, _camped = state.presence_counts(p, floor.floor)
    if hot > 1:
        body.append(f"{hot} blades hot on this floor.")
    body += state.presence_delta_lines(p, floor.floor)
    _sign = economy.TYPE_SIGN.get(_profile(p).get("type", "plain"), "")
    return Scene(
        eyebrow=_eyebrow(p, floor),
        # 003: the headline keeps ATK/DEF; HP lives in the always-on
        # enemy bar (scene.enemy) from round one.
        headline=(f"{e['name']}"
                  f"{' ' + _sign if _sign else ''} — "
                  f"HP {max(0, e['hp'])}/{e['hp_max']} · "
                  f"ATK {e['atk']} · DEF {e['def']} · "
                  f"SPD {_mspd(p)}{economy.speed_word(_mspd(p))}"),
        support="It is between you and the way forward.",
        shard_note=_shard_advice(p, floor) if opener else "",
        body_lines=body,
        options=opts,
        meters=meters(p),
        # The creature stays on screen for every round of the fight: it is
        # the same enemy, and dropping the art after the opener read as
        # "this monster has no picture".
        banner=_fight_banner(e, floor, p),
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


def _monster_hit(p: dict, halved: bool = False, least: int = 0,
                 no_dodge: bool = False) -> dict:
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
    if not no_dodge and dodge and state.roll_ok(p, dodge / 100):
        return {"dmg": 0, "raw": 0, "blocked": 0, "dodged": True}
    if _range_state(p) == "at_range":
        halved = True
    if e.pop("flare_guard", None):
        # 022/008: the flare's burst buys one round — the startled
        # monster's next blow lands half as hard.
        halved = True
    raw = state.rng_int(p, e["atk"] // 2, e["atk"])
    chip = max(1, -(-raw // economy.CHIP_DIVISOR))
    dmg = max(chip, raw - state.dfs(p) // 2)
    if halved:
        dmg //= 2
    # 026: some blows are not the damage table's business — a Warden that
    # catches you turning your back lands its grip, not a chip.
    dmg = max(dmg, int(least))
    soaked = 0
    if e.get("apple_hp", 0) > 0:
        dmg //= 2                          # the apple halves everything
        soaked = min(e["apple_hp"], dmg)
        e["apple_hp"] -= soaked
        dmg -= soaked
    p["hp"] -= dmg
    if e.get("shared"):
        # 042: the live board bills the Warden's side of the exchange —
        # what this fight has cost the climber, summed per strike.
        e["taken"] = int(e.get("taken", 0)) + dmg
    blocked = raw - dmg
    # 034 §1 / 035: both guard pieces met the blow, and both are billed for
    # what they turned — the card already narrates that number. A blow that
    # chips straight through still costs each of them its single point.
    broke = [note for note in
             (_wear(p, "shield", _shield_wear(p, blocked)),
              _wear(p, "armor", _armor_wear(p, blocked))) if note]
    hit = {"dmg": dmg, "raw": raw, "blocked": blocked, "broke": broke,
           "apple": soaked}
    # 048 N4: the riposte — a blocked or shallow blow, answered in the
    # same breath. Studied blade hands only, steel in a slot, close in.
    if ((p.get("mastery") or {}).get("blade") and _held_melee(p)
            and _range_state(p) != "at_range" and blocked >= dmg):
        atk_full = state.atk(p)
        lo = round(economy.TRAIN_ROLL_FLOOR(_rank_of(p, "blade"))
                   * atk_full)
        back = max(1, round(economy.RIPOSTE_RETURN
                            * (lo + atk_full) / 2))
        e["hp"] -= back
        hit["riposte"] = back
    return hit


def _shield_wear(p: dict, blocked: int) -> int:
    """034 §1: uses the shield spends turning `blocked` of a blow."""
    return economy.shield_wear(blocked, state.gear_bonus(p, "shield"),
                               state.dfs(p))


def _armor_wear(p: dict, blocked: int) -> int:
    """035: uses the plate spends turning `blocked` of a blow."""
    return economy.armor_wear(blocked, state.gear_bonus(p, "armor"),
                              state.dfs(p))


def _counter_text(p: dict, hit: dict, lead: str = "") -> str:
    """One line that explains the enemy's blow: what landed, what the
    armor ate. The player asked for this by name — never a bare number."""
    e = p["encounter"]
    guard = guard_name(p)
    dmg, blocked = hit["dmg"], hit["blocked"]
    lead = lead or f"{_the(e['name'])} answers"
    # 005: the round a guard piece snaps, the card says so right here.
    tail = " " + " ".join(hit["broke"]) if hit.get("broke") else ""
    if hit.get("riposte"):
        # 048 N4: the studied blade answers in the same breath.
        tail += f" Your riposte answers — {hit['riposte']} back."
    if hit.get("netted"):
        return (f"{_the(e['name'])} thrashes in the net — its round is "
                "spent tearing cord.")
    if hit.get("veiled"):
        return (f"{_the(e['name'])} strikes where you were — the veil "
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
    """The player's blow, explained: which weapon, how hard it bit —
    and, on a bad roll, WHOSE fault it was (the hand, not luck)."""
    e = p["encounter"]
    w = weapon_name(p)
    path = _train_path(p)
    mtype = _profile(p).get("type", "plain")
    swing = e.pop("_swing", None) or {}
    if dmg <= 0:
        if mtype == "fly" and path == "blade":
            return (f"{_the(e['name'])} lifts out of reach — your {w} "
                    "cuts empty air. Steel can't touch what flies.")
        return (f"Your {w} glances off {_the(e['name'], False)}'s hide — "
                "nothing lands.")
    mult = economy.TYPE_MULT[mtype][path]
    note = ""
    if mult <= 0.2:
        note = (f" — its {economy.TYPE_NAME[mtype]} sign turns "
                f"{economy.PATH_WEAPON_WORD[path]} to a glance")
    elif mult < 1.0:
        note = (f" — its {economy.TYPE_NAME[mtype]} sign halves "
                f"{economy.PATH_WEAPON_WORD[path]}")
    if swing.get("crit"):
        note += {"blade": " — the full swing finds its mark",
                 "bow": " — the long draw finds its mark",
                 "staff": " — the deep focus finds its mark"}[path]
    # 048 S5: a bottom-of-the-band roll names the rank as the cause
    rank = _train_rank(p)
    lo, hi = swing.get("lo", 0), swing.get("hi", 0)
    shallow = (rank < 8 and hi > lo
               and swing.get("raw", hi) <= lo + 0.25 * (hi - lo))
    if shallow:
        better = economy.typed_damage_048(
            path, round((economy.TRAIN_ROLL_FLOOR(min(10, rank + 2))
                         + 1) / 2 * hi), e["def"], mtype)
        # 049.1: the verb follows the weapon in hand — a bow SHOOTS,
        # it never "swings" or "cuts"
        blow, verb = {"blade": ("swing", "cuts"),
                      "bow": ("shot", "shoots"),
                      "staff": ("cast", "casts")}[path]
        return (f"Your rank-{rank} {blow} lands shallow — {dmg}{note}. "
                f"A rank-{min(10, rank + 2)} hand {verb} nearer {better}.")
    if dmg >= max(1, e["hp_max"] // 3):
        return (f"Your {w} bites deep — {dmg} damage the "
                f"{e['name']} won't shrug off{note}.")
    return f"Your {w} takes it for {dmg}{note}."


def _weapon_line(p: dict) -> str:
    """004: the equipped weapon's class line ('' for pre-class docs)."""
    item = economy.FORGE.get(p["gear"].get("weapon") or "")
    return getattr(item, "line", "") if item else ""


def _damage_type(p: dict) -> str:
    # 048: the WEAPON decides the damage type — nothing else is asked.
    # Line-less salvage (the shiv) swings as steel.
    line = _weapon_line(p)
    if line:
        return economy.DAMAGE_TYPE[line]
    return "melee"


def _train_path(p: dict) -> str:
    """048: the weapon in hand names the path it trains under."""
    return economy.PATH_OF_LINE.get(_weapon_line(p), "blade")


def _train_rank(p: dict) -> int:
    return int((p.get("training") or {}).get(_train_path(p), 0))


def _rank_of(p: dict, path: str) -> int:
    return int((p.get("training") or {}).get(path, 0))


def _the(name, cap: bool = True) -> str:
    """048 phase 8: exactly one article. Monsters named with their own
    ("The lamp-eater", "The Seep") never read "the The lamp-eater"."""
    n = str(name)
    if n[:4].lower() == "the ":
        return n if cap else "the " + n[4:]
    return ("The " if cap else "the ") + n


def _held_slugs(p: dict) -> list[str]:
    """Every weapon in the carry slots, lead hand first. Docs from
    before the slots existed read as holding their equipped weapon."""
    held = [s for s in (p.get("held") or []) if s in economy.FORGE]
    if held:
        return held
    w = p["gear"].get("weapon")
    return [w] if w in economy.FORGE else []


def _held_lines(p: dict) -> set:
    return {economy.FORGE[s].line
            for s in _held_slugs(p) if economy.FORGE[s].line}


def _held_of_line(p: dict, line: str) -> str:
    for s in _held_slugs(p):
        if economy.FORGE[s].line == line:
            return s
    return ""


def _held_melee(p: dict) -> str:
    for s in _held_slugs(p):
        line = economy.FORGE[s].line
        if economy.DAMAGE_TYPE.get(line, "melee") == "melee":
            return s
    return ""


def _promote_held(p: dict, slug: str) -> None:
    """Bring a held weapon into the striking hand. This is which of
    your carried weapons LEADS — not a pack swap (those wait for the
    road, per 045/048). 049: wear rides the item, so the hands swap
    their pools too — the resting hand's count stashes per slug, the
    lead hand's comes back out (fresh pool if it never wore)."""
    held = p.setdefault("held", [])
    old = p["gear"].get("weapon")
    if slug in held:
        held.remove(slug)
    held.insert(0, slug)
    p["gear"]["weapon"] = slug
    if old == slug:
        return
    stash = p.setdefault("durability_pack", {})
    old_dur = (p.get("durability") or {}).pop("weapon", None)
    if old and old_dur is not None:
        stash[old] = old_dur
    g = economy.FORGE.get(slug)
    if g and economy.wears(g):
        p.setdefault("durability", {})["weapon"] = stash.pop(
            slug, economy.item_pool(g))


def _player_hit(p: dict, mult: float = 1.0, pierce: bool = False) -> int:
    # 017 §2: typed damage through the defense profile. Magic ignores
    # flat DEF but eats the resist tier; melee/ranged keep raw−DEF/2 and
    # eat the armor tier. Whatever CAN hit chips ≥1; melee vs flying is
    # the one legal zero.
    e = p["encounter"]
    # 002/036: a bow in close quarters is half a weapon, and a bow with
    # made ground behind it is more than one — the gap ladder prices the
    # draw. Magic and steel keep full strength at every distance.
    if _damage_type(p) == "ranged":
        m = economy.bow_gap_mult(_gap(p))
        if m > 1 and _train_rank(p) < economy.GAP_DRAW_RANK:
            m = 1.0        # 048: the long draw pays only rank-8 hands
        mult *= m
    # 006: ten oiled strikes hit harder — physical weapons only.
    if p.get("oil", 0) > 0 and _damage_type(p) != "magic":
        mult *= economy.OIL_MULT
        p["oil"] -= 1
    # 048: the trained hand sets the floor of the swing — rank 5 is the
    # old [ATK/2, ATK] band; rank 10 never swings below 70%.
    atk_full = state.atk(p)
    lo = round(economy.TRAIN_ROLL_FLOOR(_train_rank(p)) * atk_full)
    raw = state.rng_int(p, lo, atk_full)
    path = _train_path(p)
    mastery = p.get("mastery") or {}
    # 048+: a master's hand hits 10% harder — every study, every
    # weapon, every swing. Three studies stack to +30%.
    studied = sum(1 for v in mastery.values() if v)
    if studied:
        mult *= 1 + economy.MASTERY_ATK_BONUS * studied
    mtype = _profile(p).get("type", "plain")
    if pierce and mtype == "armoured":
        mtype = "plain"        # 006: the shot never meets the plate
    # 048 N4: the long draw — a gap-3 shot in the top of the roll band
    # crits, for hands that studied it.
    crit = (path == "bow" and mastery.get("bow")
            and _gap(p) >= economy.GAP_MAX and atk_full > lo
            and raw >= lo + (1 - economy.LONG_DRAW_TOP) * (atk_full - lo))
    if crit:
        mult *= economy.LONG_DRAW_CRIT_MULT
    dmg = economy.typed_damage_048(
        path, round(raw * mult), e["def"], mtype,
        focus=bool(mastery.get("staff")))
    # the swing memo — _strike_text reads it to blame the hand, not luck
    e["_swing"] = {"raw": raw, "lo": lo, "hi": atk_full, "crit": bool(crit)}
    if e.get("shared") and e.get("kind") == "warden":
        # 046: levels ride the pillar, so one over-levelled blow can be
        # worth many fight-units — a charge never cuts past its unit,
        # not even the killing blow.
        unit = economy.pool_unit(int(e.get("floor", 1)))
        dmg = min(dmg, max(1, unit - _cut_this_fight(e)))
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
            return (f"The venom beads off {_the(e['name'], False)} — this one "
                    "doesn't poison.")
        if e.get("poison_left"):
            return "The venom is already in it — a second dose is wasted."
        e["poison_left"] = economy.POISON_ROUNDS
        e["poison_dmg"] = max(1, round(state.atk(p) * 0.25))
        return (f"The venom takes — {e['poison_dmg']} true damage a "
                f"round, {economy.POISON_ROUNDS} rounds, past any plate.")
    if effect == "slow":
        if prof.get("speed", economy.SPEED_NORMAL) <= economy.SPEED_SLOW:
            return (f"{_the(e['name'])} was already dragging — the "
                    "slowing shaft changes nothing.")
        prof["speed"] = max(1, prof["speed"] - economy.SLOW_ARROW_DELTA)
        e["profile"] = prof
        return (f"The shaft bites tendon — {_the(e['name'], False)} drops "
                f"{economy.SLOW_ARROW_DELTA} speed for this fight.")
    return ""


# fight actions that spend a round — the venom ticks and the golden
# shell rots exactly once per each.
_ROUND_ACTIONS = frozenset({
    "attack", "close_in", "open_distance", "create_distance", "run",
    "stand", "shield_wall", "sleep_spell", "treeline_shot", "drink_tonic",
    "use_oil", "throw_net", "use_hook", "use_strip", "use_curse",
    "use_veil", "use_apple"})


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


def _cut_this_fight(e: dict) -> int:
    """What THIS fight took out of the shared body — measured from where
    the blade joined it, not from the body's full size."""
    base = int(e.get("hp_join", e.get("hp_max", 0)))
    return max(0, base - max(0, int(e.get("hp", 0))))


def _report_shared_strike(p: dict) -> int:
    """022/001: a shared Warden fight is over (kill, death, or flight) —
    everything it cut away persists in the world pool. One warden_strike
    effect carries the fight's total; the server clamps and resolves."""
    e = p.get("encounter") or {}
    if not e.get("shared") or e.get("strike_sent"):
        return 0
    dealt = _cut_this_fight(e)
    if dealt <= 0:
        return 0
    e["strike_sent"] = True
    p.setdefault("_effects", []).append({
        "kind": "warden_strike", "floor": int(e.get("floor", 0)),
        "damage": dealt, "taken": int(e.get("taken", 0))})
    _ledger(p, "warden_strike", note=f"floor {e.get('floor')} · {dealt}")
    # optimistic pool update so the next keep card reads right
    w = p.get("_world") or {}
    wd = w.get("warden") or {}
    if wd.get("floor") == e.get("floor"):
        wd["hp"] = max(0, int(wd.get("hp", 0)) - dealt)
    return dealt


def kill_receipt_lines(r: dict) -> list[str]:
    """033: the Warden kill receipt, one wording everywhere — the fall
    reel at the kill, the mid-reel refresh, and the worldd patch that
    lands the settled numbers on the outgoing card all read this."""
    lines = []
    if r.get("dealt"):
        lines.append(f"Your blade took the last {int(r['dealt']):,} of it.")
    if r.get("xp"):
        share = " — your share of the kill" if r.get("shared") else ""
        lines.append(f"+ {int(r['xp']):,} XP{share}")
    if r.get("xp_clipped"):
        # 034 §2: a share bigger than the bar is clipped, and a silent
        # clip reads as theft — the card says what the bar could not take.
        lines.append(f"▪ {int(r['xp_clipped']):,} XP ran off a full bar "
                     "— train at the Guildhall before the next one")
    if r.get("gold"):
        lines.append(f"+ ◈ {int(r['gold']):,} from the Warden's hoard")
    if r.get("loot"):
        lines.append("▪ the killing blow was yours — rare loot: "
                     f"{r['loot']}")
    return lines


def _slain_reel(p: dict, floor, beat: int) -> None:
    """033: arm the fall reel — the slain beat, then floor n+1's world
    and keep beats (the existing 030 movie), then back to this floor.
    Watching from the kill counts as the once-per-floor showing."""
    p["movie_floor"] = floor.floor + 1
    p["movie_beat"] = beat
    p["movie_teaser"] = True


def _shared_warden_victory(p: dict, floor) -> Scene:
    """The pool hit zero under YOUR blade. The server settles the fall —
    frontier raise, reward split by damage, letters to every striker —
    in the SAME request; worldd lands the settled receipt on this card
    before it goes out (033: the kill pays in the card)."""
    e = p["encounter"]
    dealt = _report_shared_strike(p)
    p["encounter"] = None
    p["location"] = "gate_town"
    # 033: this Warden fell — its memory of the treeline dies with it.
    tw = p.get("treeline_wardens")
    if tw and floor.floor in tw:
        tw.remove(floor.floor)
    p["kill_receipt"] = {"dealt": dealt, "shared": True}
    _slain_reel(p, floor, beat=-1)     # this card IS the slain beat
    from . import core
    s = core.floor_movie_scene(p)
    s.event_kind = "boss"
    s.meters = meters(p)
    return s


def _assist_partner(p: dict, e: dict) -> str:
    """022/008: the most recent OTHER blade on the same prey inside the
    assist window, from the injected floor kill-log — or ''."""
    kills = (p.get("_world") or {}).get("recent_kills") or []
    now = state.now()
    me = p.get("name") or ""
    for k in reversed(kills):
        if k.get("slug") != e.get("id") or not k.get("by") \
                or k.get("by") == me:
            continue
        try:
            ts = dt.datetime.fromisoformat(k["ts"])
        except (KeyError, TypeError, ValueError):
            continue
        if (now - ts).total_seconds() <= economy.ASSIST_WINDOW_MIN * 60:
            return k["by"]
    return ""


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
    else:
        # 043: pay keys off the creature's BAR — the F+1 terror out-pays
        # the F−2 snack from the base formula, no threat multiplier.
        bar = economy.creature_bar(floor.floor, e.get("traits") or ())
        xp = round(state.rng_jitter(p, economy.xp_per_kill(bar), 0.25) * fade)
        # 009: luck is a DAY now — the halfling racial bonus is retired.
        lucky = p["flags"].get("luck_day") == state.world_day()
        gold = round(state.rng_jitter(p, economy.gold_per_kill(bar),
                                      0.50 if not lucky else 0.25) * fade)
        # 008: hard specimens pay more, runts pay less
        gold = round(
            gold * economy.SPECIMENS[e.get("specimen", "common")]["gold"])
        # 017: a hard profile pays for the diagnosis it demands
        gold = round(gold * economy.profile_gold_mult(_profile(p)))
        xp = max(1, xp)
        gold = max(1, gold)
        if e.get("deep"):
            # 039 §2: the deep hunt pays its premium in BOTH currencies
            mult = economy.deep_reward_mult(floor.floor)
            xp = max(1, round(xp * mult))
            gold = max(1, round(gold * mult))
    if p.get("race") == "elf":
        xp = round(xp * (1 + economy.ELF_XP_BONUS))
    buff = state.faction_buff_pct(p, "xp")
    if buff:
        xp = round(xp * (1 + buff / 100))     # 010: CLIMB week blessing
    # 022/005: rested aether pays out here and ONLY here — on a kill's
    # XP, never on contract or strongbox payouts. The bar is hard: once
    # it fills, more XP (and the rested that would ride it) goes nowhere.
    got = state.gain_xp(p, xp)
    rested = state.rested_bonus(p, got) if got else 0
    if rested:
        landed = state.gain_xp(p, rested)
        if landed < rested:                 # bar filled mid-draw — refund
            p["rested"] = int(p.get("rested", 0)) + (rested - landed)
            rested = landed
    xp_landed = got + rested
    p["gold"] += gold
    _ledger(p, "kill", gold=gold, xp=xp_landed, note=e["name"])
    if e["kind"] == "wilds":
        # 022/004: the kill the engine just scored is the contract
        # board's only bookkeeping.
        contracts.note_kill(p, e, _damage_type(p))
    weekly.note(p, "kills")     # 022/005: the strongbox counts the week
    downed = (f"{_the(e['name'])} goes down — no match for your "
              f"{weapon_name(p)}."
              if e["kind"] == "wilds" else f"{_the(e['name'])} goes down.")
    # Just what landed — a full bar takes no more XP, so a kill at the
    # cap writes gold (and spoils) and stays quiet about the overflow.
    lines = [downed]
    if got:
        lines.append(f"+ {got} XP")
    if rested:
        lines.append(f"+ {rested} XP rested — ✦ {p['rested']} left "
                     "in the pool")
    if e["kind"] == "wilds" and floor.floor <= economy.EARLY_COIN_FLOORS:
        # 048 N8: the fade must never read as a nerf — name the bounty
        lines.append(f"+ ◈ {gold} gold (young-tower bounty)")
    else:
        lines.append(f"+ ◈ {gold} gold")
    if e["kind"] == "wilds" and p.get("_world") is not None:
        # 022/008: assist strikes — a floor-mate on the same prey inside
        # the window links the logs. Gold only (rested already paid on
        # the kill's XP above — no double-dip, structurally). Contract
        # credit stays exactly one note_kill per participant: each blade
        # scored their own kill.
        by = _assist_partner(p, e)
        if by:
            bonus = max(1, round(gold * economy.ASSIST_BONUS_PCT))
            p["gold"] += bonus
            _ledger(p, "assist", gold=bonus, note=f"with {by}")
            lines.append(f"▪ {by}'s blade bit first — yours finishes it. "
                         f"+ ◈ {bonus} assist")
        # tell the floor about THIS kill so the next blade can link to it
        p.setdefault("_effects", []).append({
            "kind": "kill_note", "floor": e.get("floor"),
            "slug": e.get("id", "")})
    if e.get("specimen") == "alpha":
        # 006 §3.8 faucet cut: charms drop 30% → 10% — bought relics
        # need the free ones scarce.
        loot = state.rng_pick(p, [(100 - economy.ALPHA_CHARM_PCT, "medgel"),
                                  (economy.ALPHA_CHARM_PCT, "luck_charm")])
        p["inventory"][loot] = p["inventory"].get(loot, 0) + 1
        lines.append(f"▪ alpha spoils: {economy.APOTHECARY[loot].name}")

    first_clear = False
    if e["kind"] == "warden":
        # 022/001: the personal unlock is DELETED in the shared world —
        # the frontier moves only when the world Warden's pool empties.
        # Local dev play is a world of one: ITS frontier is personal.
        nxt = floor.floor + 1
        if p.get("_world") is None and p["unlocked_floor"] < nxt:
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
    opts = _after_fight_options(p, floor)
    if first_clear:
        # 033: a first clear earns the fall reel — this card keeps the
        # haul (the numbers are right here), the next click shows the
        # Warden go down, then floor n+1 introduces itself.
        p["kill_receipt"] = {"xp": xp_landed, "gold": gold,
                             "loot": economy.APOTHECARY[loot].name}
        _slain_reel(p, floor, beat=-2)   # the reel starts NEXT click
        opts = [Option("next", "Next"), Option("skip", "Skip")]
    # 038: the kill card speaks per kind (world-lore §5) — a Native is
    # CURED, a Pressed conscript DIES, a Wrongmade is EVICTED. Legacy
    # floors (breed == "") keep the old card word for word.
    breed = e.get("breed", "")
    if e["kind"] == "warden":
        # Wardens are Wrongmade by definition — breaking one is the
        # mercy, and the veil it tended starts to come down.
        headline = (f"{e['name']} — evicted"
                    + (" — the floor is opened" if first_clear else ""))
        support = ("The made shape comes apart; what ran it drains back "
                   "below. Overhead the veil frays, and the floor "
                   "brightens.")
    elif breed == "native":
        # A cure, not a kill — the blade ended the possession, and the
        # true animal underneath walks off. Never "defeated".
        headline = f"{e['name']} — freed"
        was = e.get("was", "").rstrip(" .")
        support = (f"The fever's shape drops away. "
                   f"{was[:1].upper()}{was[1:]} shakes itself loose and "
                   "slips back to the wild edges." if was else
                   "The fever's shape drops away. The animal underneath, "
                   "cured, slips back to the wild edges.")
    elif breed == "pressed":
        # The hard one. A conscript killed is simply dead — the card
        # stays plain and takes no bow.
        headline = f"{e['name']} falls"
        support = ("No ghost leaves it. A collared conscript lies where "
                   "it stood, and that is the whole of it.")
    elif breed == "wrongmade":
        headline = f"{e['name']} — evicted"
        support = ("The made shape comes apart. The scrap of will that "
                   "ran it drains downward, back to the country it was "
                   "poured from.")
    else:
        headline = (f"{e['name']} defeated"
                    + (" — the floor is opened" if first_clear else ""))
        support = "The wilds go quiet around you."
    return Scene(
        eyebrow=_eyebrow(p, floor),
        headline=headline,
        support=support,
        body_lines=lines,
        options=opts,
        meters=meters(p),
        event_kind=kind,
        # 025 §6: the haul, drawn. The lines above still SAY the numbers
        # (the agent reads those); the card lays out one coin per gold and
        # one shard per point of XP so a big kill looks like a big kill.
        tally=[{"kind": "gold", "n": gold},
               {"kind": "aether", "n": xp_landed}],
        # 045: the exit card carries the floor's tiles like the gate
        # town does — the reel branch keeps its two bare buttons.
        option_art=(None if first_clear else _floor_art(floor)),
        fx=_kill_fx(e, e["name"], first_clear, _damage_type(p), p),
    )


def _floor_art(floor) -> dict:
    from . import core
    return core._gate_town_art(floor)


def _after_fight_options(p: dict, floor) -> list[Option]:
    """045: a fight's exit card shows the floor's REAL menu. This was a
    hand-rolled copy of four rows — no deep hunt, no stew or pack heals
    right when they matter most, and a stale keep label after the Warden
    fell. The gate town owns the list; borrow it."""
    from . import core
    opts = core._gate_town_options(p, floor)
    for i, o in enumerate(opts):
        if o.id == "hunt":
            opts[i] = Option("hunt", "Hunt the wilds again", o.hint)
            # 048 retro: the gate row rides the borrowed menu itself
            # now — every camp keeps a lift to the Tower Gate
            break
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
        if g and economy.wears(g) and slot in (p.get("durability") or {}):
            p["durability"][slot] = economy.item_pool(g)
    for slug in list((p.get("durability_pack") or {})):
        g = economy.FORGE.get(slug)
        if g:
            p["durability_pack"][slug] = economy.item_pool(g)


def _defeat_cause(p: dict, e: dict) -> str:
    """048 T2: every defeat names its cause and ONE lever the player
    owns. Computed while the encounter still stands — the daily-save
    branch clears it before its lines are built."""
    t = (e.get("profile") or {}).get("type", "plain")
    held = {economy.PATH_OF_LINE.get(economy.FORGE[s].line, "blade")
            for s in _held_slugs(p)}
    path = _train_path(p)
    rank = _train_rank(p)
    if t == "fly" and held <= {"blade"}:
        return ("It flew; your blade never reached it once. A bow "
                "answers in full — the armory sells one.")
    if t == "armoured" and path == "bow":
        return ("Its plate turned your arrows — that was always too "
                "many shots. Steel halves it; a staff bites full.")
    if t == "magic_resist" and path == "staff":
        return ("Its spellguard ate your casts down to a glance. "
                "Steel bites full; arrows take half.")
    if rank <= 1:
        return (f"Your rank-{rank} {path} hands missed and landed "
                "shallow all fight — the School in town fixes this.")
    return ("Nothing turned your blows — it simply hit harder than "
            "you could trade. Better gear, or run from this one until "
            "a floor's rungs catch you up.")


def _death(p: dict, floor) -> Scene:
    e = p["encounter"]
    cause = _defeat_cause(p, e)
    daily = p["daily"]
    if not daily.get("death_save"):
        daily["death_save"] = True
        _report_shared_strike(p)   # 022/001: the wounds you left persist
        p["hp"] = 1
        p["encounter"] = None
        p["location"] = "gate_town"
        # 031 §8: the save keeps your life and your gear — never your
        # purse. Half the carried coin scatters where you fell.
        # 043.2: unless you are still level 1 — the first stumble is free.
        if p["level"] <= economy.DEATH_FREE_MAX_LEVEL:
            save_tax = 0
        else:
            save_tax = p["gold"] - p["gold"] // 2
            p["gold"] //= 2
        save_lines = [f"{_the(e['name'])} loses you in the grass.", cause]
        if save_tax:
            save_lines.append(f"− ◈ {save_tax:,} carried gold, scattered "
                              "where you fell")
        elif p["level"] <= economy.DEATH_FREE_MAX_LEVEL:
            save_lines.append("▪ your purse is untouched — the tower asks "
                              "nothing of the newly arrived")
        save_lines.append("You are at 1 HP. The gate town is close.")
        if save_tax:
            _ledger(p, "death", gold=-save_tax, note=e["name"])
        return Scene(
            eyebrow=_eyebrow(p, floor),
            headline="Your shardmind drags you out",
            support="Everything goes white, then very loud, then quiet.",
            shard_note="I have you. Once a day, I have you. Do not spend it "
                       "like this again.",
            body_lines=save_lines,
            options=[Option("heal", "The healer's tent",
                            f"pay ◈ {economy.healer_tent_price(floor.floor)}"),
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
    lines = [f"Killed by {_the(e['name'], False)}.", cause]
    if mercy:
        # 004 §A.2: a bad first hour can't spiral — keep everything but
        # half the carried gold. 043.2: at level 1 not even that.
        if p["level"] <= economy.DEATH_FREE_MAX_LEVEL:
            lost_gold = 0
        else:
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
        # 031 §8: past the pardon level the tower takes almost everything
        # you carry — the Vault is the only mercy left.
        no_pardon = p["level"] >= economy.DEATH_NO_PARDON_LEVEL
        if no_pardon:
            frac = economy.DEATH_GOLD_NO_PARDON
        else:
            frac = state.rng_int(p, round(economy.DEATH_GOLD_MIN * 100),
                                 round(economy.DEATH_GOLD_MAX * 100)) / 100
        lost_gold = round(p["gold"] * frac)
        p["gold"] -= lost_gold
        if lost_gold:
            lines.append(f"− ◈ {lost_gold:,} carried gold "
                         f"({round(frac * 100)}%), gone")
        if no_pardon:
            # 049: the basics wear now but are still never LOST — the
            # tower's tumble passes over gate steel.
            stacks = sorted(slug for slug, n in (p.get("inventory") or {})
                            .items()
                            if n > 0 and slug not in economy.BASIC_WEAPONS)
            if stacks:
                slug = stacks[state.rng_int(p, 0, len(stacks) - 1)]
                n = p["inventory"].pop(slug)
                (p.get("durability_pack") or {}).pop(slug, None)
                it = (economy.FORGE.get(slug)
                      or economy.APOTHECARY.get(slug)
                      or economy.RELICS.get(slug))
                name = it.name if it else slug.replace("_", " ")
                lines.append(f"− {name}" + (f" ×{n}" if n > 1 else "")
                             + " tumbles from your pack into the dark")
        lost_names = []
        for where, slug in _paid_weapons(p):
            if not state.roll_ok(p, economy.DEATH_WEAPON_LOSS):
                continue
            g = economy.FORGE[slug]
            lost_names.append(g.name)
            if where == "equipped":
                held = p.setdefault("held", [])
                if slug in held:
                    held.remove(slug)
                # 049: the lost weapon's wear dies with it — clear the
                # slot BEFORE the promote, which now moves pools around
                # (a packed spare's stash entry is its own and stays).
                (p.get("durability") or {}).pop("weapon", None)
                basic = (economy.CLASS_STARTERS.get(g.line)
                         or economy.STARTER_WEAPON)
                _promote_held(p, basic.slug)
                p["hone"]["weapon"] = 0
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


def _driven_back(p: dict, floor, spent: str = "guard") -> Scene:
    """026: the exchange one 3 ⚡ charge buys is spent. The Warden's guard
    closes and puts the keep's length between you — everything you cut
    stays cut, and the ⚡ was the price of the exchange, not of a swing.
    Without this the keep fight had no end but death: a climber whose DEF
    had outgrown the gate swung free until the pool was empty."""
    e = p["encounter"]
    name = e["name"]
    dealt = _report_shared_strike(p)
    p["encounter"] = None
    p["location"] = "gate_town"
    if spent == "unit":
        lines = [f"A full fight's worth is out of {name} — it gives ground, "
                 "hauls the keep doors between you and shuts them. Nobody "
                 "takes a gate in one standing."]
    else:
        lines = [f"{name}'s guard closes and it drives you the length of "
                 "the keep. The exchange is over — you are still standing."]
    if dealt:
        lines.append(f"▪ the {dealt:,} you cut away stays cut — it holds "
                     "your wounds for the next blade")
    lines.append("▪ walk back in whenever you like — every swing costs "
                 f"{economy.COST_WARDEN_STRIKE} ⚡, and the wound will be "
                 "exactly where you left it")
    return Scene(
        eyebrow=_eyebrow(p, floor),
        headline="Driven back from the keep",
        support="A gate is not worn down in one standing. That is what "
                "makes it a gate.",
        body_lines=lines,
        options=_after_fight_options(p, floor),
        meters=meters(p),
        event_kind="boss")


def resolve_fight_action(p: dict, floor, option_id: str) -> Scene:
    """026: one charge buys ONE exchange against a shared Warden — the
    same fight-unit the pool is measured in, whichever way you spend it:
    the rounds an at-level climber survives, or a full unit of damage cut
    out of the body, whichever comes first. Both ends matter. The round
    budget stops the over-armoured climber standing in the keep forever;
    the damage budget stops the over-levelled one, whose blows are worth
    three at-level fights, ending a 3-fight gate in a single charge.
    Everything else about the fight is untouched."""
    # 048: "attack_<slug>" is the attack row of a held side-arm —
    # promote it to the lead hand and resolve a plain attack.
    if option_id.startswith("attack_"):
        slug = option_id.removeprefix("attack_")
        if slug in (p.get("held") or []) and slug in economy.FORGE:
            g = economy.FORGE[slug]
            if (_range_state(p) == "at_range"
                    and economy.DAMAGE_TYPE.get(g.line, "melee")
                    == "melee"):
                # 049.1: the locked at-range row — refuse without
                # promoting, spend nothing.
                s = fight_scene(p, floor)
                s.shard_note = (f"The {g.name} can't reach at range — "
                                "close in first.")
                return s
            _promote_held(p, slug)
        option_id = "attack"
    e = p.get("encounter") or {}
    spends = option_id in _ROUND_ACTIONS or option_id.startswith("use_")
    keep = spends and e.get("shared") and e.get("kind") == "warden"
    s = _resolve_round(p, floor, option_id)
    e = p.get("encounter")
    if e and e.pop("_no_round", None):
        return s              # a refused swing spends nothing
    if not (keep and e):
        return s
    e["rounds"] = int(e.get("rounds", 0)) + 1
    cut, unit = _cut_this_fight(e), economy.pool_unit(floor.floor)
    if cut >= unit:
        # 046: levels ride the pillar now, so one over-levelled blow can
        # overshoot the unit without bound — the gate keeps the overshoot.
        e["hp"] += cut - unit
        return _driven_back(p, floor, spent="unit")
    if e["rounds"] >= economy.warden_exchange_rounds(floor.floor):
        return _driven_back(p, floor)
    return s


def _resolve_round(p: dict, floor, option_id: str) -> Scene:
    e = p["encounter"]
    notes: list[str] = []

    # Every swing at a Warden costs energy — refused BEFORE the round is
    # spent, so a dry bar costs nothing (no venom tick, no counter, no
    # round against the exchange budget). A melee "attack" from range
    # resolves as the crossing, not a swing, and stays free.
    if e["kind"] == "warden" and option_id in ("attack", "treeline_shot") \
            and not (_damage_type(p) == "melee"
                     and _range_state(p) == "at_range"):
        if not state.spend_energy(p, economy.COST_WARDEN_STRIKE):
            e["_no_round"] = True
            s = fight_scene(p, floor, note=(
                f"A swing at a Warden takes {economy.COST_WARDEN_STRIKE} ⚡ "
                "you don't have. Stand your ground, run, or let the clock "
                "refill you."))
            s.refusal = (f"Can't attack — not enough energy "
                         f"(⚡ {economy.COST_WARDEN_STRIKE} needed)")
            return s

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
                            lead=f"{_the(e['name'])} presses while you pour")
            + (f" {chase}" if chase else "")))

    if option_id == "throw_net" and p["inventory"].get("entangling_net") \
            and e["kind"] != "warden":
        p["inventory"]["entangling_net"] -= 1
        if p["inventory"]["entangling_net"] <= 0:
            del p["inventory"]["entangling_net"]
        e["netted"] = True
        return fight_scene(p, floor, note=(
            f"The net blooms open and drops — {_the(e['name'], False)} goes down "
            "thrashing in cord. Its round is spent, and it closes no "
            "ground through the mesh."))

    if option_id == "use_hook" and p["inventory"].get("sky_hook") \
            and _profile(p).get("flying"):
        p["inventory"]["sky_hook"] -= 1
        if p["inventory"]["sky_hook"] <= 0:
            del p["inventory"]["sky_hook"]
        prof = _profile(p)
        prof["flying"] = False
        # 048: grounded is grounded — it fights as a plain thing now,
        # or the triangle would keep steel at zero with the wings gone.
        prof["type"] = "plain"
        e["profile"] = prof
        hit = _monster_hit(p)
        if p["hp"] <= 0:
            return _death(p, floor)
        chase = _advance_chase(p)
        return fight_scene(p, floor, note=(
            "The sky-hook's line goes taut — whatever height it had, "
            "it fights on your ground now. "
            + _counter_text(p, hit,
                            lead=f"{_the(e['name'])} comes down swinging")
            + (f" {chase}" if chase else "")))

    if option_id == "use_strip" and p["inventory"].get("strip_potion") \
            and _profile(p).get("type") == "magic_resist":
        p["inventory"]["strip_potion"] -= 1
        if p["inventory"]["strip_potion"] <= 0:
            del p["inventory"]["strip_potion"]
        prof = _profile(p)
        prof["type"] = "plain"
        e["profile"] = prof
        hit = _monster_hit(p)
        if p["hp"] <= 0:
            return _death(p, floor)
        chase = _advance_chase(p)
        return fight_scene(p, floor, note=(
            f"The vial bursts across {_the(e['name'], False)} — its spellguard "
            "dissolves like frost in rain. "
            + _counter_text(p, hit)
            + (f" {chase}" if chase else "")))

    if option_id == "use_curse" and p["inventory"].get("curse_scroll") \
            and _profile(p).get("type") == "armoured":
        p["inventory"]["curse_scroll"] -= 1
        if p["inventory"]["curse_scroll"] <= 0:
            del p["inventory"]["curse_scroll"]
        prof = _profile(p)
        prof["type"] = "plain"
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

    if option_id == "flare":
        # 022/008: doesn't spend the round — the burst startles the
        # monster instead (its next blow lands halved).
        if p.get("_world") is None or e.get("flared"):
            return fight_scene(p, floor)
        if not state.spend_xp(p, economy.FLARE_AETHER):
            return fight_scene(p, floor, note=(
                f"A flare burns {economy.FLARE_AETHER} XP of focus — "
                "you don't have it to burn."))
        e["flared"] = True
        e["flare_guard"] = True
        p.setdefault("_effects", []).append({
            "kind": "flare", "floor": floor.floor,
            "slug": e.get("id", ""), "monster": e["name"]})
        _ledger(p, "flare", xp=-economy.FLARE_AETHER, note=e["name"])
        hot, _camped = state.presence_counts(p, floor.floor)
        seen = max(0, hot - 1)
        return fight_scene(p, floor, note=(
            "The flare goes up red and hangs over the wilds — "
            + (f"{seen} hot blade{'s' if seen != 1 else ''} on this floor "
               "will see it. " if seen else
               "no torch burns close, but flares carry. ")
            + f"{_the(e['name'])} flinches from the light."))

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
                            lead=f"{_the(e['name'])} strikes while you drink")
            + (f" {chase}" if chase else "")))

    if option_id in ("close_in", "attack") and _damage_type(p) == "melee" \
            and _range_state(p) == "at_range":
        # §2.4: always succeeds, costs the round; the monster strikes at
        # −50% while you cross the open ground. A bare "attack" from a
        # melee player at range IS the crossing — steel can't swing yet.
        e["range"] = "close"
        e["gap"] = 0
        snap = _wear(p, "shoes")       # 005: crossing spends shoe tread
        hit = _monster_hit(p, halved=True)
        if p["hp"] <= 0:
            return _death(p, floor)
        return fight_scene(p, floor, note=(
            "You cross the open ground fast and low. "
            + _counter_text(p, hit,
                            lead=f"{_the(e['name'])} meets you mid-stride")
            + (f" {snap}" if snap else "")))

    if option_id == "open_distance" and _range_state(p) == "close":
        # 031 §7: no gap opens from something your speed or better —
        # refused flat, before the turn is spent.
        if _mspd(p) >= economy.player_speed(p):
            return fight_scene(p, floor, note=(
                f"{_the(e['name'])} matches you stride for stride — "
                "no gap will open against those legs."))
        # §2.4: speed decides; on failure the monster gets a free
        # halved hit while you turn.
        snap = _wear(p, "shoes")       # 005: the turn spends shoe tread
        if state.roll_ok(p, economy.p_open(economy.player_speed(p),
                                           _mspd(p))):
            e["range"] = "at_range"
            e["gap"] = 1
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
                            lead=f"{_the(e['name'])} punishes the turn")
            + (f" {snap}" if snap else "")))

    if option_id == "create_distance" and _damage_type(p) == "ranged":
        # 048 N7: giving ground on purpose is rank-6 bowwork.
        if _train_rank(p) < economy.GAP_OPEN_RANK:
            e["_no_round"] = True
            return fight_scene(p, floor, note=(
                f"Giving ground on purpose is rank-"
                f"{economy.GAP_OPEN_RANK} bowwork — you're at "
                f"{_train_rank(p)}. The School trains it."))
        # 036: the marksman's third axis — give ground ON PURPOSE. It
        # always works (this is the trade, not a gamble): the question
        # is only whether the monster collects a parting blow on the
        # way out, and THAT is what your legs are for. Every length of
        # gap is draw-time, and draw-time is power on the next shot.
        gap = _gap(p)
        if gap >= economy.GAP_MAX:
            return fight_scene(p, floor, note=(
                f"Any more ground and you'd be out of the fight — "
                f"{economy.GAP_MAX} lengths is the long edge of a kill."))
        snap = _wear(p, "shoes")       # 005: made ground spends tread
        e["range"] = "at_range"
        e["gap"] = gap + 1
        shot = (f"The gap is {e['gap']} length"
                f"{'s' if e['gap'] > 1 else ''} now"
                + (f" — your bow hits "
                   f"×{economy.bow_gap_mult(e['gap']):g} from here."
                   if _train_rank(p) >= economy.GAP_DRAW_RANK else "."))
        if state.roll_ok(p, economy.p_gap_hit(economy.player_speed(p),
                                              _mspd(p))):
            # speed already had its say in p_gap_hit — no second dodge
            hit = _monster_hit(p, no_dodge=True)   # at range → halved
            if p["hp"] <= 0:
                return _death(p, floor)
            return fight_scene(p, floor, note=(
                "You give ground and it collects the toll — "
                + _counter_text(p, hit,
                                lead=f"{_the(e['name'], False)} rakes you as "
                                     "you pull away")
                + f" {shot}" + (f" {snap}" if snap else "")))
        return fight_scene(p, floor, note=(
            "You break clean — your legs beat its lunge and nothing "
            f"touches you. {shot}" + (f" {snap}" if snap else "")))

    if option_id == "run":
        # §2.4: the flat 60% is gone — speed decides the getaway.
        # 022/008: an answered flare buys ONE guaranteed disengage — the
        # monster has a new front and does not chase.
        snap = _wear(p, "shoes")       # 005: the sprint spends shoe tread
        chance = economy.p_flee(economy.player_speed(p), _mspd(p))
        if e["kind"] == "warden":
            # 026: a Warden always has a chance to follow you out of the
            # keep — turning your back on a gate is a price, not a button.
            chance = min(chance, economy.WARDEN_FLEE_MAX)
        if e.pop("rescued", None) or state.roll_ok(p, chance):
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
        # 026: the price of the attempt. A gate's grip is not a chip —
        # this is the "sometimes it follows you" the keep had lost.
        least = (economy.warden_grab_damage(state.max_hp(p))
                 if e["kind"] == "warden" else 0)
        hit = _monster_hit(p, least=least)
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

    if option_id == "shield_wall":
        # 048 N7: the wall wants steel in one hand, a shield on the
        # other arm, and rank-4 bladework holding them together.
        shield = economy.FORGE.get(p["gear"].get("shield") or "")
        if not _held_melee(p) or not shield or shield.line == "sorcerer":
            e["_no_round"] = True
            return fight_scene(p, floor, note=(
                "A shield wall needs steel in one hand and a shield "
                "on the other arm."))
        if _rank_of(p, "blade") < economy.WALL_RANK:
            e["_no_round"] = True
            return fight_scene(p, floor, note=(
                f"The wall is rank-{economy.WALL_RANK} bladework — "
                f"you're at {_rank_of(p, 'blade')}. "
                "The School trains it."))
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
        # 034 §1: nothing gets through because the SHIELD stops all of it —
        # the most expensive round in the game for the piece doing the
        # work. A monster still crossing open ground lands nothing to stop.
        snap = ""
        if not at_range:
            turned = state.rng_int(p, e["atk"] // 2, e["atk"])
            snap = _wear(p, "shield", _shield_wear(p, turned))
        tail = f" {snap}" if snap else ""
        chase = _advance_chase(p)
        if counter <= 0 and _profile(p).get("flying"):
            return fight_scene(p, floor, note=(
                "Shield up — nothing gets through. But your counter "
                "swings under it: the thing is airborne." + tail))
        if counter <= 0 and at_range:
            return fight_scene(p, floor, note=(
                "Shield up — nothing gets through. Your counter finds "
                "only air: it hasn't reached you yet."
                + (f" {chase}" if chase else "") + tail))
        return fight_scene(p, floor, note=(
            f"Shield up — nothing gets through. Your counter takes "
            f"{counter}.{tail}"))

    if option_id == "sleep_spell":
        # 048 N7: the lullaby is shaped through a held staff by
        # rank-6 staffwork.
        if not _held_of_line(p, "sorcerer"):
            e["_no_round"] = True
            return fight_scene(p, floor, note=(
                "The lullaby needs a staff in your hands — there is "
                "none in your slots."))
        if _rank_of(p, "staff") < economy.SLEEP_RANK:
            e["_no_round"] = True
            return fight_scene(p, floor, note=(
                f"The lullaby is rank-{economy.SLEEP_RANK} staffwork — "
                f"you're at {_rank_of(p, 'staff')}. "
                "The School trains it."))
        # 022/001: the shared Warden never sleeps — there is nothing to
        # walk past; the floor opens when its pool empties, not before.
        if e.get("shared"):
            return fight_scene(p, floor, note=(
                "You shape the lullaby and it dies against the Warden's "
                "hull. A war-machine wearing a body does not sleep."))
        # 017: a High spellguard shrugs the lullaby off entirely —
        # refused BEFORE the XP is spent, so probing costs nothing.
        if _profile(p).get("type") == "magic_resist":
            return fight_scene(p, floor, note=(
                f"You shape the lullaby and {_the(e['name'], False)}'s spellguard "
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
            body_lines=[f"{_the(e['name'])} folds into the grass, snoring.",
                        f"− {cost} XP burned — you step past it"],
            options=_after_fight_options(p, floor),
            meters=meters(p))

    if option_id == "treeline_shot" \
            and not e["shot_used"] and not e.get("attacked") \
            and _range_state(p) == "at_range":
        # 048 N7: the shot from cover wants a held bow and rank-4
        # bowwork; taking it brings the bow into the lead hand.
        bow = _held_of_line(p, "archer")
        if not bow:
            e["_no_round"] = True
            return fight_scene(p, floor, note=(
                "The shot from cover needs a bow in your slots."))
        if _rank_of(p, "bow") < economy.TREELINE_RANK:
            e["_no_round"] = True
            return fight_scene(p, floor, note=(
                f"The shot from cover is rank-{economy.TREELINE_RANK} "
                f"bowwork — you're at {_rank_of(p, 'bow')}. "
                "The School trains it."))
        _promote_held(p, bow)
        e["shot_used"] = True
        e["attacked"] = True
        if e.get("shared") and e["kind"] == "warden":
            # 033: a Warden you have fled remembers you — where the
            # wounds persist, so does its memory. The shot from cover
            # works once per Warden, not once per fight.
            seen = p.setdefault("treeline_wardens", [])
            if int(e["floor"]) not in seen:
                seen.append(int(e["floor"]))
        snap = _wear(p, "weapon")      # 005: the long shot is an attack
        mult, pierce, effect = _quiver_shot(p)   # 006: special ammo rides
        e.pop("veiled", None)                    # the veil breaks here too
        if not pierce and _profile(p).get("type") == "armoured":
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
    # 048: the weapon decides and the rank prices the swing — the
    # off-class system (arrow burn, flat 25% miss) died with the
    # classes. 006: a nocked special arrow IS the ammo for this shot.
    e["attacked"] = True           # 040: the first swing burns the treeline
    snap = _wear(p, "weapon")          # 005: every swing spends the edge
    # 031 §7: while the gap is open the beast has no answer — its whole
    # round is the ground between you (_advance_chase). Closing the gap
    # or getting caught is what puts you back in its reach.
    unreachable = _range_state(p) == "at_range"
    # 048: the hand decides — an untrained swing goes wide. The miss
    # eats the round and the monster answers, exactly like any fumble.
    rank = _train_rank(p)
    miss = economy.TRAIN_MISS_PCT(rank) / 100
    if miss > 0 and state.roll_ok(p, miss):
        wide = (f"Rank-{rank} hands — your {weapon_name(p)} swings "
                "wide. The School trains this away.")
        if unreachable:
            chase = _advance_chase(p)
            return fight_scene(p, floor, note=(
                wide + " It cannot reach you to make you pay."
                + (f" {chase}" if chase else "")
                + (f" {snap}" if snap else "")))
        back = _monster_hit(p)
        if p["hp"] <= 0:
            return _death(p, floor)
        chase = _advance_chase(p)
        return fight_scene(p, floor, note=(
            wide + " "
            + _counter_text(p, back,
                            lead=f"{_the(e['name'])} makes you pay "
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
    if unreachable:
        # 031 §7: the shot flies, nothing flies back — the gap is armor.
        chase = _advance_chase(p)
        return fight_scene(p, floor, note=(
            f"{_strike_text(p, dmg)}"
            + (f" {fxn}" if fxn else "")
            + " It has no answer at this range."
            + (f" {chase}" if chase else "")
            + (f" {snap}" if snap else "")))
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
