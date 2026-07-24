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

def current_scene(p: dict) -> Scene:
    state.touch_daily(p)
    ev = _pop_pending_event(p)
    if ev is not None:
        return ev
    return _build_scene(p)


def apply_choice(p: dict, option_id: str, text: str = "") -> Scene:
    from . import social
    state.touch_daily(p)
    p["last_seen"] = state.now().isoformat()

    if p["stage"] == "creation_name" and text and not option_id:
        return _creation_set_name(p, text)
    if p.get("compose_to") and text and not option_id:
        return social.relay_compose(p, text)
    if p.get("founding_guild") and text and not option_id:
        return social.guildhall_found(p, text)

    scene = _build_scene(p)
    valid = {o.id for o in scene.options}
    if option_id not in valid:
        # numbered fallback: "1".."9" resolve positionally
        if option_id.isdigit() and 1 <= int(option_id) <= len(scene.options):
            option_id = scene.options[int(option_id) - 1].id
        else:
            scene.shard_note = (
                f"That isn't one of the paths in front of us. "
                f"Pick one of: {', '.join(sorted(valid))}.")
            return scene
    return _dispatch(p, option_id)


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


def _maybe_present(p: dict) -> Scene | None:
    if p["stage"] != "playing":
        return None
    last = dt.datetime.fromisoformat(p["last_seen"])
    away_h = (state.now() - last).total_seconds() / 3600
    p["last_seen"] = state.now().isoformat()
    if away_h < economy.PRESENT_AWAY_HOURS:
        return None
    lucky = p.get("race") == "halfling" or \
        p["flags"].get("luck_day") == state.world_day()
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
        lines.append("⚡ your limbs hum — energy restored")
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
    builders = {
        "town": _town_scene, "forge": _forge_scene, "medlab": _medlab_scene,
        "lodge": _lodge_scene, "vault": _vault_scene, "pawn": _pawn_scene,
        "stone": _stone_scene, "gate": _gate_scene,
        "gate_town": _gate_town_scene,
        "relay": social.relay_scene, "fields": social.fields_scene,
        "guildhall": social.guildhall_scene, "grants": social.grant_scene,
        "boss_keep": _boss_keep_scene,
    }
    return builders.get(loc, _town_scene)(p)


def _boss_keep_scene(p: dict) -> Scene:
    from . import social
    fl = schema.get_floor(max(1, p["floor"]))
    return social.boss_scene(p, fl)


def _dispatch(p: dict, oid: str) -> Scene:
    if p["stage"] == "intro":
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

def _intro_scene(p: dict) -> Scene:
    return Scene(
        eyebrow="LINEAR ASCENT · THE STORY SO FAR",
        headline="Climb the Ascent. Cast down the Demon King.",
        support="One hundred floors between Roothollow and the throne.",
        body_lines=[
            "Aldervale was whole once — human river-ports, elven deep "
            "woods, dwarven fusion-forges. Magic and machine were one "
            "craft there. They called it aether.",
            "Then Vharuk, the Demon King, rose from below. He did not "
            "burn the world — he stole it: realm by realm, torn from the "
            "ground and stacked into a tower of a hundred floors, welded "
            "with black iron and chains of aether.",
            "Every floor is a captured realm. On every floor a Warden "
            "holds the lift. On the hundredth, in a citadel half throne "
            "room, half reactor core, sits Vharuk himself.",
            "At the tower's foot stands Roothollow, the last free "
            "settlement — where every climber starts, and every dead "
            "climber wakes. When a Warden falls, the lift opens for "
            "everyone, and the names that did it are cut into the Stone "
            "of the Climb.",
        ],
        options=[Option("begin", "Walk to the tower gate")],
        banner="title",
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
    s.shard_note = ("We carry ◈ 50 — the Forge's cheapest blade wants ◈ 250. "
                    "The meadows first, then: teeth before steel.")
    return s


# ── Roothollow ───────────────────────────────────────────────────────────

def _town_scene(p: dict) -> Scene:
    w = p.get("_world") or {}
    lines = []
    for h in (w.get("happenings") or [])[:5]:
        lines.append(f"· {h}")
    opts = [
        Option("forge", "The Forge", "gear"),
        Option("medlab", "Apothecary & Medlab", "potions"),
        Option("lodge", "The Lodge",
               f"◈ {economy.LODGE_PRICE_PER_LEVEL * p['level']}/night"),
        Option("vault", "The Vault", "bank"),
        Option("pawn", "Pawn shop", "sell"),
        Option("stone", "Stone of the Climb", "news"),
        Option("gate", "The tower gate", "climb"),
    ]
    if w:
        inbox = w.get("inbox_count", 0)
        opts.insert(5, Option(
            "relay", "The Relay Office",
            f"{inbox} letter{'s' if inbox != 1 else ''}" if inbox else "post"))
        opts.insert(6, Option("fields", "The fields", "pvp"))
        opts.insert(7, Option("guildhall", "The Guildhall",
                              p.get("guild") or "banners"))
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
    town_menus = ("forge", "medlab", "lodge", "vault", "pawn", "stone",
                  "gate", "relay", "fields", "guildhall")
    if loc == "town" and oid in town_menus:
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
    return _build_scene(p)


# ── Forge ────────────────────────────────────────────────────────────────

def _forge_scene(p: dict) -> Scene:
    tier = economy.gear_tier_for_floor(p["unlocked_floor"])
    opts, lines = [], []
    for g in economy.forge_tier(tier):
        owned = " — equipped" if p["gear"].get(g.slot) == g.slug else ""
        opts.append(Option(f"buy_{g.slug}", g.name, f"◈ {g.price:,}"))
        flavor = f", {g.flavor}" if g.flavor else ""
        lines.append(
            f"{g.name}{flavor} — {g.slot} +{g.bonus}{owned}")
    opts.append(Option("back", "Back to the square"))
    return Scene(
        eyebrow="ROOTHOLLOW · THE FORGE",
        headline=f"Tier {tier} steel, scrap to plasma",
        support="One named piece per slot per tier. Own the set, wear the climb.",
        body_lines=lines,
        options=opts,
        meters=combat.meters(p),
        banner="forge",
    )


def _forge_buy(p: dict, oid: str) -> Scene:
    slug = oid.removeprefix("buy_")
    g = economy.FORGE.get(slug)
    if not g:
        return _forge_scene(p)
    if p["gold"] < g.price:
        s = _forge_scene(p)
        s.shard_note = f"{g.name} wants ◈ {g.price:,}; you carry ◈ {p['gold']:,}. " \
                       "The Vault pays interest for a reason."
        return s
    old = p["gear"].get(g.slot)
    p["gold"] -= g.price
    p["gear"][g.slot] = g.slug
    note = f"+ {g.name} equipped ({g.slot} +{g.bonus})"
    if old:
        p["inventory"][old] = p["inventory"].get(old, 0) + 1
        note += f" — your {economy.FORGE[old].name} goes to your pack"
    combat._ledger(p, "buy", gold=-g.price, note=g.slug)
    s = _forge_scene(p)
    s.body_lines.insert(0, note)
    return s


# ── Medlab ───────────────────────────────────────────────────────────────

def _medlab_scene(p: dict) -> Scene:
    opts = [Option(f"buy_{i.slug}", i.name,
                   f"◈ {i.price}" + (f" · {i.note}" if i.note else ""))
            for i in economy.APOTHECARY.values()]
    opts.append(Option("back", "Back to the square"))
    inv = [f"{economy.APOTHECARY[k].name} ×{v}"
           for k, v in p["inventory"].items() if k in economy.APOTHECARY]
    return Scene(
        eyebrow="ROOTHOLLOW · APOTHECARY & MEDLAB",
        headline="Gels, stims, and honest odds",
        support="The lamp hums. The shelves are stocked. The prices are firm.",
        body_lines=(["you carry: " + ", ".join(inv)] if inv else []),
        options=opts,
        meters=combat.meters(p),
        banner="medlab",
    )


def _medlab_buy(p: dict, oid: str) -> Scene:
    slug = oid.removeprefix("buy_")
    item = economy.APOTHECARY.get(slug)
    if not item:
        return _medlab_scene(p)
    daily = p["daily"]
    if slug == "energy_cell" and daily.get("energy_cell"):
        s = _medlab_scene(p)
        s.shard_note = "One cell a day. Your heart is not a reactor."
        return s
    if slug == "aether_philtre" and daily.get("aether_philtre"):
        s = _medlab_scene(p)
        s.shard_note = "One philtre a day — aether scars if you gulp it."
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
    elif slug == "aether_philtre":
        daily["aether_philtre"] = True
        state.gain_mana(p, 3)
        note += " — ✦ +3"
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

def _lodge_scene(p: dict) -> Scene:
    price = economy.LODGE_PRICE_PER_LEVEL * p["level"]
    lodged = p["lodged_until_day"] >= state.world_day() + 1
    return Scene(
        eyebrow="ROOTHOLLOW · THE LODGE",
        headline="Sleep behind the palisade" if not lodged
                 else "Your bunk is paid through tonight",
        support="Skip the lodge and you sleep in the fields — where anyone "
                "may find you.",
        body_lines=[f"A night costs ◈ {price}. Banked gold can't buy it — "
                    "carry coin."],
        options=([Option("sleep", "Pay for the night", f"◈ {price}")]
                 if not lodged else [])
                + [Option("back", "Back to the square")],
        meters=combat.meters(p),
        banner="lodge",
    )


def _lodge_action(p: dict, oid: str) -> Scene:
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
    s.body_lines.insert(0, "+ one safe night. Nothing finds you here.")
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

def _pawn_scene(p: dict) -> Scene:
    gear_in_pack = [k for k in p["inventory"] if k in economy.FORGE]
    opts = []
    lines = []
    for slug in gear_in_pack:
        g = economy.FORGE[slug]
        offer = int(g.price * economy.PAWN_BUYBACK)
        opts.append(Option(f"sell_{slug}", f"Sell {g.name}", f"◈ {offer:,}"))
        lines.append(f"{g.name} ×{p['inventory'][slug]} — offers ◈ {offer:,}")
    if not lines:
        lines.append("Nothing in your pack the broker wants today.")
    opts.append(Option("back", "Back to the square"))
    return Scene(
        eyebrow="ROOTHOLLOW · PAWN SHOP",
        headline="Forty on the hundred, no haggling",
        support="The broker has seen everything twice and paid less for it "
                "both times.",
        body_lines=lines,
        options=opts,
        meters=combat.meters(p),
    )


def _pawn_action(p: dict, oid: str) -> Scene:
    slug = oid.removeprefix("sell_")
    if slug in p["inventory"] and slug in economy.FORGE:
        g = economy.FORGE[slug]
        offer = int(g.price * economy.PAWN_BUYBACK)
        p["inventory"][slug] -= 1
        if p["inventory"][slug] <= 0:
            del p["inventory"][slug]
        p["gold"] += offer
        combat._ledger(p, "pawn", gold=offer, note=slug)
        s = _pawn_scene(p)
        s.body_lines.insert(0, f"+ ◈ {offer:,} for the {g.name}")
        return s
    return _pawn_scene(p)


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
    heal_price = 2 * fl.floor
    opts = [Option("hunt", "Hunt the wilds", "1 ⚡")]
    if p["hp"] < state.max_hp(p):
        opts.append(Option("heal", "The healer's tent", f"◈ {heal_price}"))
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
        price = 2 * fl.floor
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
    if oid == "keep":
        # milestone keeps run the quorum flow in the shared world
        if fl.milestone and p.get("_world"):
            from . import social
            p["location"] = "boss_keep"
            return social.boss_scene(p, fl)
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
