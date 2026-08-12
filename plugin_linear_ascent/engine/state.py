"""Player document + time/meter math.

The player is ONE JSON document (JSONB row locally, worldd row later).
All regen/interest math derives from server timestamps — never from
model-supplied time. World-day is a pure function of UTC time.
"""

from __future__ import annotations

import datetime as dt

from .. import economy

WORLD_DAY_UTC_HOUR = 6
_EPOCH = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)


def now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def world_day(at: dt.datetime | None = None) -> int:
    """Day number since epoch, rolling at WORLD_DAY_UTC_HOUR."""
    at = at or now()
    shifted = at - dt.timedelta(hours=WORLD_DAY_UTC_HOUR)
    return (shifted - _EPOCH.replace(hour=0)).days


def world_day_f(at: dt.datetime | None = None) -> float:
    """Fractional day count on the same clock — the 041 interest slices
    need partial days."""
    at = at or now()
    shifted = at - dt.timedelta(hours=WORLD_DAY_UTC_HOUR)
    return (shifted - _EPOCH.replace(hour=0)) / dt.timedelta(days=1)


def new_player(luna_user: str) -> dict:
    ts = now().isoformat()
    return {
        "version": 9,
        "luna_user": luna_user,
        "stage": "intro",              # intro → creation_race → creation_name → playing
        "name": None, "race": None,
        "level": 1, "xp": 0,
        "hp": economy.player_max_hp(1, economy.GATE_ARMOR.bonus),
        "gold": 50, "bank": 0, "bank_day": world_day(),
        "floor": 0, "location": "town",
        "gear": {"weapon": economy.STARTER_WEAPON.slug,
                 "shield": economy.GATE_SHIELD.slug,
                 "armor": economy.GATE_ARMOR.slug, "shoes": None},
        "hone": {s: 0 for s in economy.HONE_SLOTS},
        # 005: staged onboarding — a slot gets a durability entry only
        # when its first wearing piece arrives. 049: the basic weapon
        # wears, so migrate()'s self-heal grants its pool on first load;
        # the gate guard kit stays wear-free.
        "durability": {},
        "durability_pack": {},
        "inventory": {},
        "energy_ts": ts, "energy_val": float(economy.ENERGY_BASE_CAP),
        "lodged_until_day": -1,
        "last_seen": ts,
        "news_day": world_day(),       # fresh climbers skip today's crier
        "rng_counter": 0,
        "scene": None,
        "encounter": None,
        "unlocked_floor": 1,
        "flags": {},
        "daily": {"day": world_day(), "pvp_used": 0, "energy_cell": False,
                  "death_save": False},
        "sidekick": {"insight": 1, "carried": None},
        "telemetry_day": world_day(),
        # 048: trained rank 0–10 per weapon path — the player's skill.
        # Creation trains the starting path; the School sells the rest.
        "training": {"blade": 0, "bow": 0, "staff": 0},
        # 048 phase 3: CARRY — weapon slugs in hand; held[0] IS the
        # equipped weapon, the School sells the 2nd and 3rd slot.
        "slots": 1,
        "held": [economy.STARTER_WEAPON.slug],
    }


# ── Meters (lazy regen) ──────────────────────────────────────────────────

def _regen(val: float, ts_iso: str, cap: int, minutes_per_point: float,
           at: dt.datetime) -> float:
    ts = dt.datetime.fromisoformat(ts_iso)
    elapsed_min = max(0.0, (at - ts).total_seconds() / 60.0)
    return min(float(cap), val + elapsed_min / minutes_per_point)


def _energy_minutes(p: dict) -> float:
    """037: minutes per energy point RIGHT NOW. Sleeping runs the clock
    faster; the snapshot discipline (energy_ts is re-stamped when sleep
    starts and ends) keeps the fast rate from leaking into waking time."""
    where = (p.get("sleeping") or {}).get("where", "")
    return economy.ENERGY_REGEN_MIN / economy.SLEEP_ENERGY_MULT.get(where,
                                                                    1.0)


def gear_band(p: dict) -> int:
    """022/002: the player's gear band — the highest tier worn on any
    paid slot. Keys the energy cap now that the level stops at 30."""
    best = 0
    for slot in ("weapon", "shield", "armor", "shoes"):
        g = economy.FORGE.get(p["gear"].get(slot) or "")
        if g and g.price > 0:
            best = max(best, g.tier)
    return max(1, best)


def energy_cap_of(p: dict) -> int:
    return economy.energy_cap(gear_band(p), p.get("race") or "")


def energy_now(p: dict, at: dt.datetime | None = None) -> int:
    at = at or now()
    return int(_regen(p["energy_val"], p["energy_ts"], energy_cap_of(p),
                      _energy_minutes(p), at))


def spend_energy(p: dict, amount: int, at: dt.datetime | None = None) -> bool:
    at = at or now()
    cur = _regen(p["energy_val"], p["energy_ts"], energy_cap_of(p),
                 _energy_minutes(p), at)
    if cur < amount:
        return False
    p["energy_val"] = cur - amount
    p["energy_ts"] = at.isoformat()
    return True


def gain_energy(p: dict, amount: int, at: dt.datetime | None = None) -> None:
    at = at or now()
    cap = energy_cap_of(p)
    cur = _regen(p["energy_val"], p["energy_ts"], cap,
                 _energy_minutes(p), at)
    p["energy_val"] = min(float(cap), cur + amount)
    p["energy_ts"] = at.isoformat()


# ── 037: active sleep — the only pre-dawn healing ────────────────────────

def start_sleep(p: dict, where: str, at: dt.datetime | None = None) -> None:
    """Lie down in the lodge or the fields. Energy is snapshotted at the
    waking rate first, so the sleep multiplier only counts slept time."""
    at = at or now()
    gain_energy(p, 0, at=at)
    p["sleeping"] = {"where": where, "since": at.isoformat(),
                     "hp_ts": at.isoformat()}


def wake_up(p: dict, at: dt.datetime | None = None) -> str:
    """Get up. Banks the slept-rate energy and any HP still owed, then
    drops the sleep state. Returns where the player slept."""
    at = at or now()
    s = p.get("sleeping") or {}
    apply_sleep_healing(p, at=at)
    gain_energy(p, 0, at=at)
    p.pop("sleeping", None)
    return s.get("where", "")


def apply_sleep_healing(p: dict, at: dt.datetime | None = None) -> int:
    """Lazy HP mend while asleep — a full bar in SLEEP_HP_FULL_MIN minutes,
    whatever the bar's size. The timestamp is only re-stamped once at
    least one whole point has accrued, so fractions are never lost.
    Returns the HP actually mended."""
    s = p.get("sleeping")
    if not s:
        return 0
    at = at or now()
    ts = dt.datetime.fromisoformat(s.get("hp_ts") or s["since"])
    elapsed_min = max(0.0, (at - ts).total_seconds() / 60.0)
    full_min = economy.SLEEP_HP_FULL_MIN.get(s.get("where", ""), 0)
    if full_min <= 0:
        return 0
    heal = int(elapsed_min * max_hp(p) / full_min)
    if heal <= 0:
        return 0
    s["hp_ts"] = at.isoformat()
    before = p["hp"]
    p["hp"] = min(max_hp(p), before + heal)
    return p["hp"] - before


def xp_room(p: dict) -> int | None:
    """How much XP still fits in this level's bar.

    None means uncapped — at LEVEL_CAP the Guildhall refuses training and
    the pool is pure currency (hone / sleep / mend). Below the cap the bar
    is hard: surplus from a kill goes nowhere.

    034 §2: worldd pays every share through gain_xp now, and the docs it
    settles are loaded straight from the table — a partial one must not
    raise mid-fall, so the level is defaulted on both reads.
    """
    level = int(p.get("level", 1))
    if level >= economy.LEVEL_CAP:
        return None
    return max(0, economy.xp_need(level) - int(p.get("xp", 0)))


def gain_xp(p: dict, amount: int) -> int:
    """Add XP, stopping at a full bar. Returns how much actually landed."""
    amount = max(0, int(amount))
    if amount <= 0:
        return 0
    room = xp_room(p)
    if room is not None:
        amount = min(amount, room)
    p["xp"] = int(p.get("xp", 0)) + amount
    return amount


def spend_xp(p: dict, amount: int) -> bool:
    """Burn aether — XP from the current level's pool (006). Never goes
    below 0 and never touches level; the caller shows the refusal."""
    if p["xp"] < amount:
        return False
    p["xp"] -= amount
    return True


# ── Doc upgrades (lazy migration on load — 004 §A.1) ─────────────────────

def ensure_current(p: dict) -> None:
    """Upgrade an older player document in place. Runs at every engine
    entry point, so docs created before a fix are healed on any backend
    (local plugin DB and worldd alike) the next time they're touched."""
    p.setdefault("hone", {s: 0 for s in economy.HONE_SLOTS})
    p.setdefault("news_day", -1)       # 007: existing docs get the crier
    p["gear"].setdefault("shoes", None)    # 004: the shoes ladder
    p.setdefault("durability", {})         # 005: wear per equipped slot
    p.setdefault("durability_pack", {})    # 005: wear stashed with the pack
    if p["gear"].get("weapon") is None:
        # pre-c4ab270 doc: never received the free starter weapon.
        p["gear"]["weapon"] = economy.STARTER_WEAPON.slug
        if p.get("stage") == "playing":
            from .scene import Option, Scene
            p["gold"] += economy.VAULT_APOLOGY_GOLD
            p.setdefault("pending_events", []).insert(0, Scene(
                eyebrow="ROOTHOLLOW · A LETTER FROM THE VAULT",
                headline="The Vault owes you an apology",
                support="Sealed in gray wax: the gate armory shorted your "
                        "kit on arrival.",
                shard_note="Take it. Institutions apologize so rarely.",
                body_lines=[
                    "▪ a Rusted Shiv, gate-issue — yours all along",
                    f"+ ◈ {economy.VAULT_APOLOGY_GOLD} for the trouble",
                ],
                options=[Option("town", "Pocket it and move on")],
                event_kind="present",
            ).to_dict())
    if p.get("version", 1) < 2:
        # 017 §1: doc v2 — every class carries its OWN basic weapon.
        # Existing docs holding the generic shiv get their class piece;
        # archers/sorcerers see a letter (their weapon visibly changed),
        # the warrior's shiv just grew into its proper name.
        clazz = p.get("clazz")
        if (p.get("stage") == "playing" and clazz in economy.CLASS_STARTERS
                and p["gear"].get("weapon") == economy.STARTER_WEAPON.slug):
            starter = economy.CLASS_STARTERS[clazz]
            p["gear"]["weapon"] = starter.slug
            if clazz in ("archer", "sorcerer"):
                from .scene import Option, Scene
                p.setdefault("pending_events", []).insert(0, Scene(
                    eyebrow="ROOTHOLLOW · A LETTER FROM THE GATE ARMORY",
                    headline="Your own weapon, at last",
                    support="The armory finally sorted its ledgers: "
                            "climbers fight with the weapon of their "
                            "calling, not a spare shiv.",
                    shard_note="It fits your hands. It always should have.",
                    body_lines=[
                        f"▪ {starter.name} — {starter.flavor}",
                        "▪ the basic weapon is never lost — it wears "
                        "like any steel, and the Forge mends gate "
                        "steel for a coin",
                    ],
                    options=[Option("town", "Take it up")],
                    event_kind="present",
                ).to_dict())
        p["version"] = 2
    if p.get("version", 1) < 3:
        # 005: docs that predate durability get FULL pools on whatever
        # paid gear they already wear — nobody's kit arrives pre-worn.
        for slot in economy.DURABILITY_SLOTS:
            g = economy.FORGE.get(p["gear"].get(slot) or "")
            if g and g.price > 0 and slot not in p["durability"]:
                p["durability"][slot] = economy.item_pool(g)
        p["version"] = 3
    if p.get("version", 1) < 4:
        # 009: the halfling line is retired — the canon cast is human,
        # elf and dwarf. Existing halflings are re-registered human
        # (the closest line: port-town survivors, adaptable) and told
        # so in-world. The racial luck bonus retires with the line;
        # luck DAYS and luck CHARMS are unchanged — they never keyed
        # off the race.
        if p.get("race") == "halfling":
            p["race"] = "human"
            if p.get("stage") == "playing":
                from .scene import Option, Scene
                p.setdefault("pending_events", []).insert(0, Scene(
                    eyebrow="ROOTHOLLOW · A LETTER FROM THE REGISTRAR",
                    headline="The Stone re-registers your line",
                    support="The registrar's slate was recut: three lines "
                            "climb the Ascent — human, elf, dwarf. Yours "
                            "now reads HUMAN.",
                    shard_note="The registry changed, not you. Your name "
                               "on the Stone stands exactly as carved.",
                    body_lines=[
                        "▪ your line on the slate: HUMAN — adaptable, "
                        "+1 energy cap, effective immediately",
                        "▪ the old luck-of-the-line bonus is retired "
                        "with the listing",
                        "▪ luck charms and luck days work exactly as "
                        "before",
                    ],
                    options=[Option("town", "Fold the letter and climb on")],
                    event_kind="present",
                ).to_dict())
        p["version"] = 4
    if p.get("version", 1) < 5:
        # 017 §1 follow-up: doc v2 re-issued the class basic weapon only to
        # climbers still holding the GENERIC shiv. But every weapon the
        # Forge had ever sold became warrior-line the day the three lines
        # landed — so an archer or sorcerer who had BOUGHT one woke up
        # off-class on gear they paid full price for: half the damage, one
        # swing in four wide, no honing, triple price to replace it. That
        # is a retroactive punishment for a fair purchase.
        #
        # Re-forge every such piece — worn and packed alike — into the same
        # rung of the holder's own line. The lines mirror rung for rung, so
        # the swap is exact: same bonus, same price, wear and hone carried
        # over. Docs still in creation (which v2 skipped) get their class
        # basic weapon here too.
        clazz = p.get("clazz") or ""
        if clazz in economy.CLASS_STARTERS:
            reforged: list[tuple[str, str]] = []
            worn = p["gear"].get("weapon") or ""
            starters = {g.slug for g in economy.CLASS_STARTERS.values()}
            starters.add(economy.STARTER_WEAPON.slug)
            item = economy.FORGE.get(worn)
            if worn in starters:
                p["gear"]["weapon"] = economy.CLASS_STARTERS[clazz].slug
            elif item and item.line and item.line != clazz:
                twin = economy.line_twin(item, clazz)
                if twin:
                    p["gear"]["weapon"] = twin.slug
                    reforged.append((item.name, twin.name))
            pack = p.setdefault("inventory", {})
            stash = p.setdefault("durability_pack", {})
            for slug in list(pack):
                item = economy.FORGE.get(slug)
                if not (item and item.line and item.line != clazz):
                    continue
                twin = economy.line_twin(item, clazz)
                if not twin:
                    continue
                pack[twin.slug] = pack.get(twin.slug, 0) + pack.pop(slug)
                if slug in stash:
                    stash[twin.slug] = max(stash.pop(slug),
                                           stash.get(twin.slug, 0))
                reforged.append((item.name, twin.name))
            if reforged and p.get("stage") == "playing":
                from .scene import Option, Scene
                p.setdefault("pending_events", []).insert(0, Scene(
                    eyebrow="ROOTHOLLOW · THE FORGE, BEFORE OPENING",
                    headline="The smith re-forged what you paid for",
                    support="When the Forge split its racks into three "
                            "lines, the steel you had already bought was "
                            "filed under somebody else's calling. You were "
                            "being charged for a mistake in the ledger.",
                    shard_note="Rung for rung, it is the same weapon. "
                               "You lost nothing — you only stopped "
                               "paying for a clerk's error.",
                    body_lines=[
                        f"▪ {old} → {new} — same rung, same bite, your line"
                        for old, new in reforged
                    ] + ["▪ its wear and its honing came across untouched"],
                    options=[Option("town", "Take it up")],
                    event_kind="present",
                ).to_dict())
        p["version"] = 5
    if p.get("version", 1) < 6:
        # 043: the gate issues the whole kit now — a fresh climber IS
        # bar 1 (level 1 in the floor's reference gear). Docs with a
        # bare shield or armor slot get the gate piece; anything the
        # player already bought stays.
        if not p["gear"].get("shield"):
            p["gear"]["shield"] = economy.GATE_SHIELD.slug
        if not p["gear"].get("armor"):
            p["gear"]["armor"] = economy.GATE_ARMOR.slug
        p["version"] = 6
    if p.get("version", 1) < 7:
        # 048: the School era — training lives on every doc. A legacy
        # doc is honored on its class's path at a rank that scales with
        # the climb: 6 (≈ the old on-class feel) as the floor of it,
        # +1 per ten floors opened, capped at 9 — the tenth rank and
        # the master's studies stay earned.
        if "training" not in p:
            p["training"] = {"blade": 0, "bow": 0, "staff": 0}
            path = economy.PATH_OF_LINE.get(p.get("clazz") or "")
            if path:
                rank = economy.legacy_rank(p.get("unlocked_floor", 1))
                p["training"][path] = rank
                if p.get("stage") == "playing":
                    from .scene import Option, Scene
                    pretty = {"blade": "Blade", "bow": "Bow",
                              "staff": "Staff"}[path]
                    body = [f"▪ {pretty} — trained rank {rank}"]
                    if rank > 6:
                        body.append("▪ the deep floors counted — the "
                                    "School reads the Stone")
                    body.append("▪ the School trains all three paths, "
                                "for XP and coin")
                    p.setdefault("pending_events", []).insert(0, Scene(
                        eyebrow="ROOTHOLLOW · A LETTER FROM THE SCHOOL",
                        headline="The guilds dissolved their halls into "
                                 "one School",
                        support="Every gate town teaches every weapon "
                                "now. Your years on the path are "
                                "honored.",
                        shard_note="A trained hand is a trained hand, "
                                   "whatever the guild called it.",
                        body_lines=body,
                        options=[Option("town", "So be it")],
                        event_kind="present",
                    ).to_dict())
        p["version"] = 7
    if p.get("version", 1) < 8:
        # 049: the basic weapons wear now (full pool granted by the
        # self-heal below). One letter, only to hands that hold one.
        basics_held = [s for s in ([p["gear"].get("weapon")]
                                   + list(p.get("held") or [])
                                   + list(p.get("inventory") or {}))
                       if s in economy.BASIC_WEAPONS]
        if basics_held and p.get("stage") == "playing":
            # appended, not front-inserted: an older doc crossing several
            # versions at once reads the bigger letters first.
            from .scene import Option, Scene
            p.setdefault("pending_events", []).append(Scene(
                eyebrow="ROOTHOLLOW · A WORD FROM THE FORGE",
                headline="Gate steel wears now, like any steel",
                support="The smith stopped pretending salvage iron is "
                        "eternal. Your basic weapon carries a plain "
                        "durability pool from today.",
                shard_note="Nothing to fear — it still can't be lost, "
                           "and broken only ever means half strength.",
                body_lines=[
                    "▪ your basic weapon starts at FULL durability",
                    "▪ the Forge mends gate steel for a coin",
                    "▪ replaced, it rides to your pack instead of "
                    "the scrap bin",
                ],
                options=[Option("town", "Fair enough")],
                event_kind="present",
            ).to_dict())
        p["version"] = 8
    if p.get("version", 1) < 9:
        # 049.1: the Pigsticker grew a name with a weapon in it — Scrap
        # Dagger. Same steel, same numbers; every ledger line follows
        # the slug. Silent, like the v2 warrior rename.
        _old, _new = "pigsticker", "scrap_dagger"
        if p["gear"].get("weapon") == _old:
            p["gear"]["weapon"] = _new
        if p.get("held"):
            p["held"] = [_new if s == _old else s for s in p["held"]]
        inv = p.get("inventory") or {}
        if _old in inv:
            inv[_new] = inv.get(_new, 0) + inv.pop(_old)
        stash = p.get("durability_pack") or {}
        if _old in stash:
            stash[_new] = stash.pop(_old)
        p["version"] = 9
    # 048 phase 3: carry slots + held list, self-healing on every load —
    # held[0] mirrors the hand, length never exceeds slots, and paid
    # overflow returns to the pack instead of vanishing.
    if "slots" not in p:
        p["slots"] = 1
    held = p.setdefault("held", [])
    w = (p.get("gear") or {}).get("weapon")
    if w:
        if w in held:
            held.remove(w)
        held.insert(0, w)
    cap = max(1, int(p["slots"]))
    for slug in held[cap:]:
        g = economy.FORGE.get(slug)
        if g and economy.wears(g):
            p.setdefault("inventory", {})[slug] = \
                p["inventory"].get(slug, 0) + 1
    del held[cap:]
    # 049: the basic weapons wear now — a wearing weapon in the hand
    # without a pool gets a full one (fresh docs, death promotes).
    wg = economy.FORGE.get((p.get("gear") or {}).get("weapon") or "")
    if wg and economy.wears(wg) \
            and "weapon" not in p.setdefault("durability", {}):
        p["durability"]["weapon"] = economy.item_pool(wg)
    # Soft clamp: XP used to bank past a full bar. Anyone already over
    # is brought back to the bar — surplus never bought a level anyway.
    if xp_room(p) is not None:
        need = economy.xp_need(int(p["level"]))
        if int(p.get("xp", 0)) > need:
            p["xp"] = need


# ── Durability (005 §3.5) ────────────────────────────────────────────────

def durability_max(p: dict, slot: str) -> int:
    """The full pool of the slot's equipped item; 0 for wear-free gear
    (049: the basic weapons wear now — only the gate guard kit is
    wear-free)."""
    g = economy.FORGE.get(p["gear"].get(slot) or "")
    return economy.item_pool(g) if g and economy.wears(g) else 0


def is_broken(p: dict, slot: str) -> bool:
    dur = (p.get("durability") or {}).get(slot)
    return dur is not None and dur <= 0 and durability_max(p, slot) > 0


def wear_gear(p: dict, slot: str, n: int = 1) -> bool:
    """−n uses on the slot's paid piece. True exactly on the wear that
    snaps it — the caller owes the player one line for that moment."""
    dur = p.get("durability")
    if not dur or slot not in dur or durability_max(p, slot) <= 0:
        return False
    if dur[slot] <= 0:
        return False
    dur[slot] = max(0, dur[slot] - n)
    return dur[slot] == 0


# ── Derived stats ────────────────────────────────────────────────────────

def hone_level(p: dict, slot: str) -> int:
    return int((p.get("hone") or {}).get(slot, 0))


def gear_bonus(p: dict, slot: str) -> int:
    slug = p["gear"].get(slot)
    if not slug:
        # a doc can never be bare-handed again: an empty weapon slot
        # fights with the gate-issue shiv (004 §A.1 defensive floor).
        return economy.STARTER_WEAPON.bonus if slot == "weapon" else 0
    item = economy.FORGE.get(slug)
    base = item.bonus if item else 0
    # 046: a hone step multiplies the piece by the pillar — gear, not
    # the capped level, carries the within-band exponential.
    total = economy.honed_bonus(base, hone_level(p, slot))
    if is_broken(p, slot):
        total //= 2                    # 005: broken, never gone
    return total


def atk(p: dict) -> int:
    return economy.player_atk(p["level"], gear_bonus(p, "weapon"))


def dfs(p: dict) -> int:
    return economy.player_def(p["level"], gear_bonus(p, "shield"),
                              gear_bonus(p, "armor"), p.get("race") or "")


def faction_buff_pct(p: dict, kind: str) -> int:
    """010: the faction's weekly blessing — {'kind','pct','week'} written
    by worldd's weekly resolution; live only during its week."""
    b = p.get("faction_buff")
    if (isinstance(b, dict) and b.get("kind") == kind
            and b.get("week") == world_day() // 7):
        return max(0, int(b.get("pct", 0)))
    return 0


def max_hp(p: dict) -> int:
    # 022/002: the armor on your back feeds the pool — HP keeps growing
    # past the level cap the same way ATK/DEF do.
    base = economy.player_max_hp(p["level"], gear_bonus(p, "armor"))
    pct = faction_buff_pct(p, "hp")
    return round(base * (1 + pct / 100)) if pct else base


def next_roll(p: dict) -> int:
    """Advance and return the RNG counter."""
    p["rng_counter"] += 1
    return p["rng_counter"]


# ── Player-scoped deterministic rolls ────────────────────────────────────

def _key(p: dict) -> str:
    return p.get("luna_user", "?")


def rng_int(p: dict, lo: int, hi: int) -> int:
    from . import rng
    return rng.roll_int(_key(p), world_day(), next_roll(p), lo, hi)


def rng_jitter(p: dict, base: int, pct: float) -> int:
    from . import rng
    return rng.roll_pct_jitter(_key(p), world_day(), next_roll(p), base, pct)


def rng_pick(p: dict, table: list[tuple[int, str]]) -> str:
    from . import rng
    return rng.weighted_pick(_key(p), world_day(), next_roll(p), table)


def roll_ok(p: dict, prob: float) -> bool:
    from . import rng
    return rng.roll(_key(p), world_day(), next_roll(p)) < prob


def touch_daily(p: dict) -> None:
    """Reset per-day counters when the world day advanced."""
    day = world_day()
    if p["daily"].get("day") != day:
        # 022/004 dawn law: wounds close at the world-day boundary and
        # ONLY there — full HP, wherever you slept. No daytime trickle,
        # so mid-session healing still costs gold (the potion sink
        # lives). Replaces the Lodge's +20 special case; the Lodge
        # sells a SAFE night now, never health.
        healed = False
        if p.get("stage") == "playing" and p.get("hp", 0) < max_hp(p):
            p["hp"] = max_hp(p)
            healed = True
        # 022/005 night slot: ONE action per night, resolved at dawn.
        # Away nights don't stack — the plan covered one night.
        night_yield = None
        night = p.get("night")
        if (night and night.get("day", -1) < day
                and p.get("stage") == "playing"):
            fl = max(1, p.get("unlocked_floor", 1))
            if night.get("choice") == "work":
                g = economy.night_work_gold(fl)
                p["gold"] = p.get("gold", 0) + g
                p.setdefault("_ledger", []).append(
                    {"kind": "night_work", "gold": g, "xp": 0,
                     "note": "the night shift"})
                night_yield = {"kind": "work", "gold": g}
            else:
                amt = economy.night_rest_aether(p["level"])
                cap = economy.rested_pool_cap(p["level"])
                before = int(p.get("rested", 0))
                p["rested"] = min(cap, before + amt)
                night_yield = {"kind": "rest",
                               "aether": p["rested"] - before}
            p["night"] = None
        p["daily"] = {"day": day, "pvp_used": 0, "energy_cell": False,
                      "death_save": False, "dawn_healed": healed,
                      "night_yield": night_yield}


def rested_bonus(p: dict, kill_xp: int) -> int:
    """022/005: draw the rested pool down against a KILL's XP — the only
    place rested aether pays out (never contracts, never the strongbox).
    Mutates the pool; returns the bonus XP."""
    pool = int(p.get("rested", 0))
    if pool <= 0 or kill_xp <= 0:
        return 0
    bonus = min(pool, max(1, round(kill_xp * economy.RESTED_XP_BONUS_PCT)))
    p["rested"] = pool - bonus
    return bonus


def prestige(p: dict) -> int:
    """022/007: reincarnation points from past eras — 0 for first-era
    climbers. Prestige buys TIME, never power: early doors, a rested
    pool at boot, a glyph by the name. Written server-side at doc
    creation; the plugin only reads it."""
    return int((p.get("prestige") or {}).get("points", 0))


def interest_sync(p: dict) -> list[dict]:
    """023/041: materialize the vault's interest STUBS. The 5%-a-day
    rate drips in slices — BANK_INTEREST_TICKS per day, so 1% lands
    every 24/5 hours — one stub per slice, priced off the principal as
    it stood. Fractions carry between slices, so small banks lose
    nothing to rounding. Uncollected interest is SIMPLE; collecting
    re-banks it, so the hand who shows up still compounds — the
    compounding is the hook. Lazy (runs when the doc loads a scene,
    absent players cost nothing) and bounded (the clerk keeps a month
    of slices, oldest dropped)."""
    day_f = world_day_f()
    stubs = p.setdefault("interest_due", [])
    # pre-041 docs stamped whole day numbers — a float mark reads both
    mark = float(p.get("bank_day", day_f))
    per_day = economy.BANK_INTEREST_TICKS
    ticks = int((day_f - mark) * per_day)
    if ticks > 0:
        kept = min(ticks, economy.INTEREST_STUB_CAP)
        # 6-decimal quantum kills float drift — 0.3 stays 0.3, ten of
        # them reach 3.0, and the third coin actually lands
        per = round(p.get("bank", 0) * economy.BANK_INTEREST_RATE
                    / per_day, 6)
        carry = float(p.get("interest_frac", 0.0))
        for t in range(ticks - kept + 1, ticks + 1):
            carry = round(carry + per, 6)
            gold = int(carry)
            if gold >= 1:
                carry -= gold
                stubs.append({"day": int(mark + t / per_day), "gold": gold})
        p["interest_frac"] = round(carry, 6)
        # advance by whole slices only — partial-slice time is never lost
        p["bank_day"] = mark + ticks / per_day
        del stubs[:-economy.INTEREST_STUB_CAP]
    return stubs


def interest_collect(p: dict) -> int:
    """Bank the whole pile; returns the total (0 if nothing waited)."""
    stubs = interest_sync(p)
    total = sum(s["gold"] for s in stubs)
    if total > 0:
        p["bank"] += total
        p["interest_due"] = []
    return total


# ── Presence (022 §003) — reads of the injected `_world["presence"]` ─────
# hot = acted on the floor within 3 min (the only tier that counts as
# "with you"); camped = within the hour. Shared by core (town cards)
# and combat (the fight refreshes it every round); all of it degrades
# to silence when no world is attached.

def presence_counts(p: dict, floor: int) -> tuple[int, int]:
    """(hot, camped) on `floor` — (0, 0) without a world."""
    w = p.get("_world") or {}
    by = (w.get("presence") or {}).get("by_floor") or {}
    slot = by.get(floor) or by.get(str(floor)) or {}
    return int(slot.get("hot", 0)), int(slot.get("camped", 0))


def presence_torches(p: dict, floor: int) -> list[dict]:
    """Named hot climbers on `floor`, your own torch filtered out."""
    w = p.get("_world") or {}
    t = (w.get("presence") or {}).get("torches") or {}
    torches = t.get(floor) or t.get(str(floor)) or []
    me = p.get("name") or ""
    return [x for x in torches if x.get("name") != me]


def presence_delta_lines(p: dict, floor: int) -> list[str]:
    """Presence changes since the player's LAST card on this floor,
    folded in as story — never a widget. Updates the watermark."""
    if "presence" not in (p.get("_world") or {}):
        return []
    hot, _ = presence_counts(p, floor)
    seen = p.get("presence_seen") or {}
    lines: list[str] = []
    if int(seen.get("floor", -1)) == floor:
        delta = hot - int(seen.get("hot", 0))
        if delta >= 2:
            lines.append(f"{delta} more torches on the ridge since you "
                         "last looked.")
        elif delta == 1:
            lines.append("Another torch on the ridge since you last "
                         "looked.")
        elif delta <= -1:
            lines.append("A torch has guttered out since you last "
                         "looked.")
    p["presence_seen"] = {"floor": floor, "hot": hot}
    return lines
