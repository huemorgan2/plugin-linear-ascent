"""The state machine — every flow gated here, steering hints on refusal.

`current_scene(p)` is idempotent (safe to call anytime).
`apply_choice(p, option_id, text)` validates the option against the
current scene and dispatches. The agent never free-forms game state.
"""

from __future__ import annotations

import datetime as dt

from .. import economy, icons, unlocks
from ..content import schema
from . import combat, contracts, figure3d, labs, names, notices, state, weekly
from .scene import Meters, Option, Scene


# ── Entry points ─────────────────────────────────────────────────────────

# 027: the notice board rides every room in Roothollow, not just the
# square — walking into the Forge should still tell you the Vault is
# holding your money. The climb itself stays clean: no notices at the gate,
# in the wilds or inside a keep, where the only thing that matters is the
# thing trying to kill you.
_NOTICE_ROOMS = ("town", "forge", "arcanum", "medlab", "lodge", "vault",
                 "pawn", "stone", "guildhall", "hall", "board", "relay",
                 "fields", "grants")


def _stamp(p: dict, scene: Scene) -> Scene:
    """scene_id = the act counter. Every choice bumps it, reads reuse it —
    /pane/peek compares ids, so a chat-driven act refreshes the pane
    while idempotent reads never do. 014: the pack strip rides every
    playing scene the same way. 027: so does the notice board, in town."""
    scene.scene_id = f"s{p.get('act_seq', 0)}"
    scene.location = str(p.get("location") or "")   # 042: the music key
    scene.labs = labs.enabled_keys(p)                # 067: the flask
    scene.figure3d = figure3d.payload(p)             # 071: 3D portrait
    scene.inventory = _pack_strip(p)
    scene.slots = _slot_map(p)                      # 069: the gear map
    scene.pack_slots = pack_cap(p)
    if (not scene.notices and not scene.enemy
            and p.get("location") in _NOTICE_ROOMS):
        scene.notices = notices.pending(p)
    # 042: the presence grid rides every ordinary room card — scenes
    # that brought their own grid (warden boards, memorials) keep it.
    from . import presence
    presence.mount(p, scene)
    # 027: every pack cell carries what it can do HERE — the strip stops
    # being a hover-only display and becomes the place you use a thing.
    for cell in scene.inventory:
        acts, why = pack_actions(p, cell["slug"])
        if acts:
            cell["acts"] = [{"opt": o.id, "label": o.label, "hint": o.hint}
                            for o in acts]
        if why:
            cell["why"] = why
    # 070: the week-pick receipt rides the next card, wherever they are.
    note = p.pop("strongbox_note", None)
    if note:
        scene.body_lines = [note, *list(scene.body_lines)]
    return scene


# ── 012: the pack has a size ─────────────────────────────────────────────
# A slot is a stack: one slug, any count. Shops refuse to OPEN a new
# stack in a full pack (before gold moves); every other gain lands — loot
# is never dropped by a bookkeeping rule, the grid just shows the
# surplus in red until the player sells, uses or buys a bigger pack.

def pack_cap(p: dict) -> int:
    return max(1, int(p.get("pack_slots") or economy.PACK_BASE_SLOTS))


def pack_used(p: dict) -> int:
    return sum(1 for n in (p.get("inventory") or {}).values() if n > 0)


def pack_can_take(p: dict, slug: str) -> bool:
    """True if `slug` fits: it already has a stack, or a slot is free."""
    if (p.get("inventory") or {}).get(slug, 0) > 0:
        return True
    return pack_used(p) < pack_cap(p)


def _pack_full(p: dict, scene_fn, what: str) -> Scene:
    used, cap = pack_used(p), pack_cap(p)
    s = scene_fn(p)
    s.shard_note = (f"Your pack is full — {used}/{cap} slots — and the "
                    f"{what} has nowhere to go. Use, sell or donate "
                    "something, or buy a larger pack at the Forge.")
    s.refusal = f"Can't buy this — pack full ({used}/{cap} slots)"
    return s


def _gear_cell(p: dict, slug: str, slot: str, worn: bool) -> dict:
    """069: one gear cell — the worn/held piece with its honed number
    and its wear. `slot` is the durability slot; `worn` says whether the
    piece is the one on the body / in the lead hand (its wear lives in
    `durability[slot]`) or a held side-arm (`durability_pack[slug]`)."""
    g = economy.FORGE[slug]
    hone = state.hone_level(p, slot, slug) if slot == "weapon" \
        else (state.hone_level(p, slot) if worn else 0)
    cell = {"slug": slug, "kind": slot, "count": 1, "equipped": True,
            "name": g.name + (f" +{hone}" if hone else "")}
    cell["stat_name"] = "ATK" if slot == "weapon" else "DEF"
    cell["stat_val"] = economy.honed_bonus(g.bonus, hone)
    left = ((p.get("durability") or {}).get(slot) if worn
            else (p.get("durability_pack") or {}).get(slug))
    if left is not None and economy.wears(g):
        pool = economy.item_pool(g)
        cell["dur"] = max(0.0, min(1.0, left / pool)) if pool else 1.0
        cell["dur_left"] = economy.endurance(g, left)
        cell["dur_max"] = economy.endurance(g)
    return cell


def _slot_map(p: dict) -> list[dict]:
    """069: the seven slots around the portrait — ALWAYS all seven, each
    in one of three states: locked (grey box + lock, the hover says how
    to open it), empty (dotted), filled (the icon; the popover carries
    the slot's acts from `slot_actions`)."""
    if p.get("stage") != "playing":
        return []
    out: list[dict] = []
    rows = {"left": 0, "right": 0}
    lead = (p.get("gear") or {}).get("weapon")
    for sl in economy.SLOTS:
        d = {"key": sl.key, "side": sl.side, "row": rows[sl.side],
             "label": sl.label, "kind": sl.kind, "state": "empty",
             "lock_text": "", "slug": "", "name": "", "icon": "",
             "count": 0}
        rows[sl.side] += 1
        lock = economy.slot_lock(p, sl.key)
        slug = economy.slot_item(p, sl.key)
        if lock:
            d["state"] = "locked"
            d["lock_text"] = lock
            d["icon"] = "lock"
        elif slug:
            d["state"] = "filled"
            d["slug"] = slug
            if slug in economy.FORGE:
                dslot = "weapon" if sl.kind == "weapon" else sl.key
                cell = _gear_cell(p, slug, dslot,
                                  worn=(sl.kind != "weapon" or slug == lead))
                d.update(cell)
                d["lead"] = bool(sl.kind == "weapon" and slug == lead)
                d["icon"] = icons.icon_key(slug, dslot)
            else:
                d["count"] = 1
                if slug in economy.APOTHECARY:
                    item = economy.APOTHECARY[slug]
                    d["name"] = item.name
                    # 081: a potion's number rides the click popup —
                    # "heal_25" → HEALS 25 (prose effects stay in the tip)
                    parts = (item.effect or "").rsplit("_", 1)
                    if len(parts) == 2 and parts[1].isdigit():
                        d["stat_name"] = ("HEALS" if parts[0] == "heal"
                                          else parts[0].upper())
                        d["stat_val"] = int(parts[1])
                elif slug in economy.RELICS:
                    d["name"] = economy.RELICS[slug].name
                else:
                    d["name"] = slug.replace("_", " ")
                d["icon"] = icons.icon_key(slug, "item")
                if slug == "luck_charm":
                    d["charm_dur"] = int(p.get("charm_dur") or 0)
            acts, why = slot_actions(p, sl.key)
            if acts:
                d["acts"] = [{"opt": o.id, "label": o.label, "hint": o.hint}
                             for o in acts]
            if why:
                d["why"] = why
        else:
            d["icon"] = {"weapon": "weapon", "shield": "shield",
                         "armor": "armor", "shoes": "shoes",
                         "charm": "luck_charm"}.get(sl.kind, "pack")
        out.append(d)
    return out


def _pack_strip(p: dict) -> list[dict]:
    """014: what the player carries. 069: the PACK only — worn and held
    gear moved to the slot map (`_slot_map`); a pack stack is a thing
    that does nothing until it is set in a slot. Rendered under the
    gear map as 1-bit icons; empty before the character exists."""
    if p.get("stage") != "playing":
        return []
    strip: list[dict] = []
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
        cell = {"slug": slug, "kind": "item", "count": int(count),
                "name": slug.replace("_", " ")}
        if slug in economy.APOTHECARY:
            item = economy.APOTHECARY[slug]
            cell["name"] = item.name
            # 081: the click popup quotes the potion's number too
            parts = (item.effect or "").rsplit("_", 1)
            if len(parts) == 2 and parts[1].isdigit():
                cell["stat_name"] = ("HEALS" if parts[0] == "heal"
                                     else parts[0].upper())
                cell["stat_val"] = int(parts[1])
        elif slug in economy.RELICS:
            cell["name"], cell["kind"] = economy.RELICS[slug].name, "relic"
        elif slug in economy.PACKS:
            # 064: an old pack riding in the new one
            cell["name"], cell["kind"] = economy.PACKS[slug].name, "pack"
        elif slug in economy.FORGE:
            g = economy.FORGE[slug]
            cell["name"], cell["kind"] = g.name, g.slot
            cell["stat_name"] = "ATK" if g.slot == "weapon" else "DEF"
            cell["stat_val"] = g.bonus
            # 045: packed gear carries its wear too — a spare bought
            # used should say so before it's promoted to the hand.
            left = (p.get("durability_pack") or {}).get(slug)
            if left is not None and economy.wears(g):
                pool = economy.item_pool(g)
                cell["dur"] = (max(0.0, min(1.0, left / pool))
                               if pool else 1.0)
                cell["dur_left"] = economy.endurance(g, left)
                cell["dur_max"] = economy.endurance(g)
        strip.append(cell)
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
PACK_USE_IDS = ("use_medgel", "use_trauma_kit", "use_weapon_oil")
POUCH_ONLY_WHY = ("Nothing works from the pack — set it in your charm "
                  "pouch and it will offer itself in the fight.")
NOT_IN_A_FIGHT = "Not in a fight — set it before you go down."
LAST_BLADE = "You keep one blade in hand."


def pack_full_why(p: dict) -> str:
    return (f"Pack full ({pack_used(p)}/{pack_cap(p)}). Sell or drop "
            "something, or buy a bigger pack at the forge.")


def _wear_level_req(slug: str) -> int:
    g = economy.FORGE.get(slug)
    return economy.rung_player_level_req(g) if g else 0


def slot_actions(p: dict, key: str) -> tuple[list[Option], str]:
    """069: what a SLOT can do — the popover on the gear map. Locked →
    the lock text; empty → nothing; filled → 'Move to the pack' (and the
    Forge trip for worn steel). Refusals that never change with the
    click (a fight, the last blade) come back as `why` with no row; the
    pack-full case keeps its row and refuses on the click, in red."""
    if p.get("stage") != "playing":
        return [], ""
    lock = economy.slot_lock(p, key)
    if lock:
        return [], lock
    slug = economy.slot_item(p, key)
    if not slug:
        return [], ""
    if p.get("encounter"):
        return [], NOT_IN_A_FIGHT
    if key in economy.WEAPON_SLOT_KEYS and \
            len([w for w in (p.get("held") or []) if w in economy.FORGE]) <= 1:
        return [], LAST_BLADE
    opts: list[Option] = []
    if slug in economy.FORGE:
        g = economy.FORGE[slug]
        fix, _ = pack_actions(p, slug)
        opts.extend(o for o in fix if o.id.startswith("forge_fix_"))
        name = g.name
    elif slug in economy.APOTHECARY:
        name = economy.APOTHECARY[slug].name
    elif slug in economy.RELICS:
        name = economy.RELICS[slug].name
    else:
        name = slug.replace("_", " ")
    hint = f"the {name} rides in the pack — it does nothing there"
    if not pack_can_take(p, slug):
        hint = pack_full_why(p)
    opts.append(Option(f"unequip_{key}", "Move to the pack", hint))
    return opts, ""


def _unequip(p: dict, key: str) -> Scene:
    """069: a slot item goes back to the pack. Weapons leave their slot
    (the lead pointer moves to the first blade left), a bow's quiver
    returns to the pack with it, oil on that blade is lost, worn steel
    carries its wear along; the shield's and armour's honing resets."""
    s_lock = economy.slot_lock(p, key)
    slug = economy.slot_item(p, key)
    if s_lock or not slug:
        s = _build_scene(p)
        s.shard_note = s_lock or "Nothing there."
        return s
    if p.get("encounter"):
        s = _build_scene(p)
        s.shard_note = NOT_IN_A_FIGHT
        return s
    inv = p.setdefault("inventory", {})
    held = [w for w in (p.get("held") or []) if w in economy.FORGE]
    if key in economy.WEAPON_SLOT_KEYS and len(held) <= 1:
        s = _build_scene(p)
        s.shard_note = LAST_BLADE
        return s
    # capacity: the piece, plus every quiver stack that comes back with
    # the last bow
    need = [slug]
    quiver_back = {}
    if key in economy.WEAPON_SLOT_KEYS:
        def _ranged(w):
            g = economy.FORGE.get(w)
            return bool(g) and economy.DAMAGE_TYPE.get(g.line) == "ranged"
        if _ranged(slug) and not any(_ranged(w) for w in held if w != slug):
            quiver_back = {k: n for k, n in (p.get("quiver") or {}).items()
                           if n > 0}
            need.extend(quiver_back)
    free = pack_cap(p) - pack_used(p)
    opening = [x for x in dict.fromkeys(need) if inv.get(x, 0) <= 0]
    if len(opening) > free:
        s = _build_scene(p)
        s.shard_note = pack_full_why(p)
        s.refusal = f"Can't move it — pack full ({pack_used(p)}/{pack_cap(p)})"
        return s
    notes = []
    if key in economy.WEAPON_SLOT_KEYS:
        if p["gear"].get("weapon") == slug:
            other = next(w for w in held if w != slug)
            combat._promote_held(p, other)     # swaps the wear pools too
        p["held"] = [w for w in (p.get("held") or []) if w != slug]
        if (p.get("oil") or {}).pop(slug, None):
            notes.append("the oil dries on the shelf")
        for k, n in quiver_back.items():
            inv[k] = inv.get(k, 0) + n
            p["quiver"].pop(k, None)
        if quiver_back:
            notes.append("the quiver comes back to the pack with the bow")
    else:
        p["gear"][key] = None
        if key in economy.DURABILITY_SLOTS:
            left = (p.get("durability") or {}).pop(key, None)
            if left is not None:
                p.setdefault("durability_pack", {})[slug] = left
        if key in ("shield", "armor") and state.hone_level(p, key):
            state.set_hone(p, key, 0)
            notes.append("its honing is lost")
    inv[slug] = inv.get(slug, 0) + 1
    combat._ledger(p, "use", note=f"unequip {slug}")
    if slug in economy.FORGE:
        name = economy.FORGE[slug].name
    elif slug in economy.APOTHECARY:
        name = economy.APOTHECARY[slug].name
    elif slug in economy.RELICS:
        name = economy.RELICS[slug].name
    else:
        name = slug.replace("_", " ")
    s = _build_scene(p)
    line = f"▪ the {name} goes to your pack — it does nothing there"
    if notes:
        line += " (" + "; ".join(notes) + ")"
    s.body_lines.insert(0, line)
    return s


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
        # 081: the sizing-up window — the fight has not begun and the
        # foe sheet just named the weapon that answers. Weapons only;
        # the level gate still reads on the row.
        if combat.swap_window(p) and slug in economy.FORGE \
                and economy.FORGE[slug].slot == "weapon" and have:
            req = _wear_level_req(slug)
            if p["level"] < req:
                return [], (f"🔒 level {req} — {economy.FORGE[slug].name} "
                            f"answers to level {req} hands; you are "
                            f"level {p['level']}.")
            return [Option(f"wear_{slug}", "Hold",
                           "swap before the steel meets")], ""
        # 069: in a fight the pack offers NOTHING — the pouch and the
        # bow's quiver are the only things that act, and they are set
        # before the fight.
        if slug in economy.QUIVER_SLUGS:
            return [], ("Loose arrows do nothing — bind them to your bow "
                        "before the fight.")
        if slug in economy.CHARM_KINDS:
            return [], POUCH_ONLY_WHY
        return [], "Nothing this one can do in the middle of this."

    # The salves: a number in the effect string ("heal_25"). The tonic's
    # "heal_full" is a fight item and answers below.
    if item and item.effect.startswith("heal_") \
            and item.effect != "heal_full" and have \
            and slug not in economy.CHARM_KINDS:
        amount = int(item.effect.rsplit("_", 1)[1])
        if p["hp"] >= state.max_hp(p):
            return [], ("You're whole. Keep it sealed for when you're "
                        "not — it heals the same at any level.")
        return [Option(f"use_{slug}", f"Use a {item.name}",
                       f"+{amount} HP · {have} left")], ""
    if slug == "weapon_oil" and have:
        # 069: oil is applied on the road to the blade that LEADS
        lead = p["gear"].get("weapon") or ""
        g = economy.FORGE.get(lead)
        if not g or economy.DAMAGE_TYPE.get(g.line, "melee") == "magic":
            return [], "Oil wants steel or a bowstring — not a focus."
        if state.oil_left(p) > 0:
            return [], (f"The {g.name} is already slick — "
                        f"{state.oil_left(p)} strikes left.")
        return [Option("use_weapon_oil", f"Slick the {g.name}",
                       f"{economy.OIL_STRIKES} strikes +25% · {have} left")], ""
    if slug in economy.QUIVER_SLUGS and have:
        # 069: arrows bind to a held bow — the whole stack moves
        if not any(economy.DAMAGE_TYPE.get(economy.FORGE[w].line) == "ranged"
                   for w in (p.get("held") or []) if w in economy.FORGE):
            return [], "Arrows want a bow in hand."
        return [Option(f"nock_{slug}", "Bind to your bow",
                       f"×{have} into the quiver")], ""
    if slug == "repair_token":
        return [], "The Forge spends it: one full mend, free."
    if slug in economy.CHARM_KINDS and have:
        # 069: relics, potions and the luck charm act from the POUCH —
        # the pack row SETS them there (a salve keeps its road use too)
        lock = economy.slot_lock(p, "charm")
        rows: list[Option] = []
        salve = bool(item and item.effect.startswith("heal_")
                     and item.effect != "heal_full")
        if salve:
            amount = int(item.effect.rsplit("_", 1)[1])
            if p["hp"] < state.max_hp(p):
                rows.append(Option(f"use_{slug}", f"Use a {item.name}",
                                   f"+{amount} HP · {have} left"))
        if lock:
            # the pouch's lock reads on the SLOT; a salve row stands on
            # its own, a whole body hears why it has none
            if rows:
                return rows, ""
            return [], (("You're whole. Keep it sealed for when you're "
                         "not — it heals the same at any level.")
                        if salve else lock)
        worn = (p.get("gear") or {}).get("charm")
        if worn == slug:
            return rows, "One is already in your pouch."
        wname = (economy.APOTHECARY[worn].name if worn in economy.APOTHECARY
                 else economy.RELICS[worn].name if worn in economy.RELICS
                 else worn)
        hint = f"swap out the {wname}" if worn else "into the charm pouch"
        rows.append(Option(f"wear_{slug}", "Set in pouch", hint))
        return rows, ""
    if slug in economy.FORGE:
        # 045: gear promotes itself from the pack — one weapon held, one
        # shield, one armour; the slot decides which.
        g = economy.FORGE[slug]
        if g.slot in economy.DURABILITY_SLOTS \
                and p["gear"].get(g.slot) == slug:
            # the worn piece's popup offers the trip home: one tap
            # walks you to the Forge, where the repair row waits.
            # Just the shortcut — the anvil takes the coin there.
            left = (p.get("durability") or {}).get(g.slot)
            if economy.wears(g) and left is not None:
                pool = economy.item_pool(g)
                if left < pool:
                    rprice = economy.repair_price(g, 1 - left / pool)
                    xp_cost = economy.hone_xp(p["unlocked_floor"])
                    return [Option(
                        f"forge_fix_{g.slot}",
                        "Go to the Forge and fix",
                        f"◈ {rprice:,} + {xp_cost} XP")], ""
            return [], ("Already in your hand."
                        if g.slot in ("weapon", "shield")
                        else "Already worn.")
        if g.slot in economy.DURABILITY_SLOTS and have:
            # 069: the level gate reads on the pack row, before the tap
            req = _wear_level_req(slug)
            if p["level"] < req:
                return [], (f"🔒 level {req} — {g.name} answers to level "
                            f"{req} hands; you are level {p['level']}.")
            if g.slot in ("weapon", "shield"):
                label = "Hold"
            else:
                label = "Wear"
            worn = p["gear"].get(g.slot)
            # 081: "from your pack" said where it was, not what happens —
            # held slots now say the move plainly.
            bare = ("move to hand" if g.slot in ("weapon", "shield")
                    else "from your pack")
            hint = (f"swap out the {economy.FORGE[worn].name}"
                    if worn and worn in economy.FORGE else bare)
            # 048 phase 3: an untrained path warns BEFORE the swap —
            # no silent numbers, even on a tooltip.
            if g.slot == "weapon":
                path = economy.PATH_OF_LINE.get(g.line, "")
                if path and not int((p.get("training") or {})
                                    .get(path, 0)):
                    hint += (f" · untrained {path} — miss "
                             f"{economy.TRAIN_MISS_PCT(0)}%, weak swings")
            if g.slot != "weapon" and state.hone_level(p, g.slot):
                hint += " · honing resets"
            return [Option(f"wear_{slug}", label, hint)], ""
        return [], "The Forge swaps gear in and out of the pack."
    return [], ""


def _pack_use(p: dict, oid: str) -> Scene | None:
    """027: a pack action taken from the strip — legal in any room, never
    in a fight. Returns None when the id isn't a pack action."""
    wearing = oid.startswith("wear_")
    fixing = oid.startswith("forge_fix_")
    nocking = oid.startswith("nock_") and not p.get("encounter")
    unequipping = oid.startswith("unequip_") and \
        oid.removeprefix("unequip_") in {sl.key for sl in economy.SLOTS}
    if oid not in PACK_USE_IDS and not wearing and not fixing \
            and not nocking and not unequipping:
        return None
    if unequipping:
        return _unequip(p, oid.removeprefix("unequip_"))
    if p.get("encounter"):
        if wearing:
            # 081: at the sizing-up a pack WEAPON may still come to
            # hand — the same swap as on the road, the card rebuilt
            # around the new lead. Once the fight has begun, the old
            # refusal stands.
            slug = oid.removeprefix("wear_")
            acts, why = pack_actions(p, slug)
            if any(o.id == oid for o in acts):
                fl = schema.get_floor(p["encounter"]["floor"])
                return _wear_from_pack(
                    p, slug,
                    lambda q: combat.fight_scene(q, fl, opener=True))
        if wearing or fixing:
            # 048 phase 3: the promote is refused mid-fight WITH a
            # reason — not the generic "not one of the paths".
            s = _build_scene(p)
            s.shard_note = (("Not mid-fight — the Forge keeps. Finish "
                             "this first.") if fixing else
                            ("Not mid-fight — you don't re-rig your "
                             "hands with teeth in your face. The swap "
                             "waits for the road."))
            return s
        return None
    if fixing:
        # the worn piece's shortcut home: one tap walks you to the
        # anvil from any room. Just the trip — the repair row on the
        # wall takes the coin.
        slot = oid.removeprefix("forge_fix_")
        slug = (p.get("gear") or {}).get(slot) or ""
        acts, why = pack_actions(p, slug) if slug else ([], "")
        if not any(o.id == oid for o in acts):
            s = _build_scene(p)
            s.shard_note = why or "Nothing happens."
            return s
        p["location"] = "forge"
        p["floor"] = 0
        for k in ("hall_area", "hall_ask", "hall_putting", "hall_kicking",
                  "hall_promoting", "hall_leaving", "guild_leaving",
                  "banner_page", "guild_dir",
                  "door_rules", "profile_view", "profile_back",
                  "profile_pay", "profile_gift", "profile_loot"):
            p.pop(k, None)
        s = _forge_scene(p)
        g = economy.FORGE.get(slug)
        if g:
            s.shard_note = (f"Back to Roothollow — the smith waves the "
                            f"{g.name} onto the anvil. The repair row "
                            "is on the wall.")
        return s
    slug = oid.removeprefix("wear_" if wearing else
                            "nock_" if nocking else "use_")
    acts, why = pack_actions(p, slug)
    if not any(o.id == oid for o in acts):
        s = _build_scene(p)
        s.shard_note = why or "Nothing happens."
        return s
    if wearing:
        # 045: promote from the pack — same swap the Forge row performs.
        return _wear_from_pack(p, slug, _build_scene)
    if nocking:
        # 069: the whole stack binds to the bow's quiver
        n = p["inventory"].pop(slug)
        p.setdefault("quiver", {})[slug] = p["quiver"].get(slug, 0) + n
        combat._ledger(p, "use", note=f"quiver {slug}")
        s = _build_scene(p)
        s.body_lines.insert(0, (f"+ {economy.RELICS[slug].name} ×{n} into "
                                "the quiver — they fly from the bow now"))
        return s
    if slug == "weapon_oil":
        lead = p["gear"]["weapon"]
        p.setdefault("oil", {})[lead] = economy.OIL_STRIKES
        note = (f"+ you slick the {economy.FORGE[lead].name} — the next "
                f"{economy.OIL_STRIKES} strikes bite +25%")
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
    if p.get("hall_ask") and text and not option_id:
        # 032: the hall's inline asks — a donate sum, a board line,
        # the banner's new name
        from . import hall
        return _stamp(p, hall.hall_text(p, text))
    if (isinstance(p.get("guild_dir"), dict)
            and p["guild_dir"].get("asking") and text and not option_id):
        # 042: the directory's typed search line
        return _stamp(p, social.guild_dir_search(p, text))

    # 027: two surfaces act from OUTSIDE the menu — the pack popup and the
    # notice board. Their ids are validated by the engine that owns them,
    # not by the row list, so they work from any room.
    used = _pack_use(p, option_id)
    if used is not None:
        return _stamp(p, used)

    # 070: last week's reward — the ANSI box on the notice board. Valid
    # from any room the board rides; not mid-fight.
    if (option_id or "").startswith("pick_") \
            and p.get("stage") == "playing" \
            and p.get("level", 1) >= economy.STRONGBOX_LEVEL:
        if p.get("encounter") or p.get("movie_floor"):
            scene = _build_scene(p)
            scene.refusal = "Choose after the fight."
            return _stamp(p, scene)
        if weekly.pick(p, option_id):
            return _stamp(p, _build_scene(p))

    # 030 Phase 5: the paper's ✕ — closing the Crier stamps the same
    # news_day guard the delivery keys on, so closed stays closed until
    # dawn. Valid wherever the paper shows, hence outside the row list.
    if option_id == "news_close":
        p["news_day"] = state.world_day()
        return _stamp(p, _build_scene(p))

    # 081: the foe sheet's swap hint ✕ — dismissed for good, a doc flag
    # like the Crier's (survives reloads and other devices). Lives
    # outside the row list, same as news_close.
    if option_id == "foehint_close" and p.get("stage") == "playing":
        p["foehint_done"] = True
        if p.get("encounter"):
            fl = schema.get_floor(p["encounter"]["floor"])
            return _stamp(p, combat.fight_scene(p, fl, opener=True))
        return _stamp(p, _build_scene(p))

    # 081: the sticky mail toast is a door — a clicked wire/letter
    # notification walks the player straight to the Relay Office. Valid
    # from any quiet room (the toast lives outside the row list); a
    # fight is never left mid-swing.
    if option_id == "goto_relay" and p.get("stage") == "playing":
        if p.get("encounter") or p.get("movie_floor"):
            scene = _build_scene(p)
            scene.refusal = ("The Relay keeps — finish this fight "
                             "first.")
            return _stamp(p, scene)
        if not _door_open(p, economy.RELAY_LEVEL) \
                and not int((p.get("_world") or {})
                            .get("inbox_count") or 0):
            scene = _build_scene(p)
            scene.refusal = (f"Entering the Relay requires level "
                             f"{economy.RELAY_LEVEL} — you are level "
                             f"{p['level']}")
            return _stamp(p, scene)
        for k in ("hall_area", "hall_ask", "hall_putting", "hall_kicking",
                  "hall_promoting", "hall_leaving", "guild_leaving",
                  "banner_page", "guild_dir",
                  "door_rules", "profile_view", "profile_back",
                  "profile_pay", "profile_gift", "profile_loot"):
            p.pop(k, None)
        p["floor"] = 0
        p["location"] = "relay"
        return _stamp(p, _build_scene(p))

    # 067: the Labs card — reached from the bottom bar's flask, valid
    # from any room (the bar is outside the row list). Not mid-fight or
    # mid-creation: the switch would change the card under the player.
    if labs.is_labs_option(option_id):
        if p["stage"] != "playing" or p.get("encounter") \
                or p.get("movie_floor"):
            scene = _build_scene(p)
            scene.refusal = "Labs opens between fights — finish this first"
            return _stamp(p, scene)
        return _stamp(p, labs.handle(p, option_id, _build_scene))

    # 030 Phase 8: mid-reel every click is the next beat ("skip" cuts to
    # the arrival card). A stray id ("hunt" sent before the arrival card)
    # advances the frame instead of erroring — the reel only runs one
    # direction and nothing can wedge against it.
    if p.get("movie_floor"):
        return _stamp(p, _floor_movie_advance(p, option_id))

    scene = _build_scene(p)
    if p.get("location") in _NOTICE_ROOMS and not scene.enemy:
        doors = {nt.get("opt") for nt in notices.pending(p) if nt.get("opt")}
        if option_id in doors and option_id not in {o.id for o in scene.options}:
            # the notice row is a shortcut to the door: walk to the square
            # and open it, exactly as a player would with two clicks.
            p["location"] = "town"
            return _stamp(p, _dispatch(p, option_id))

    # 027: a picture tile is a row — the sigil grid's ids are as valid as
    # any option's, they just look like what they choose.
    # 042: so is a face on the presence grid — mount it first so its
    # pv: targets count (the response scene mounts again in _stamp).
    from . import presence
    presence.mount(p, scene)
    valid = ({o.id for o in scene.options}
             | {str(g.get("opt", "")) for g in scene.gallery}
             | presence.valid_opts(scene))
    # the MORE unfold appends faces past the shipped tiles — any pv:
    # click is a door regardless (an unknown name reads a silent stone)
    if option_id.startswith("pv:"):
        valid = valid | {option_id}
    # 062: the profile's faction bar is a door — from any room on the
    # square (or a climber's page) it walks to town and into the hall.
    if option_id == "go:hall" and not scene.enemy \
            and p.get("location") in _NOTICE_ROOMS + ("profile",) \
            and p["stage"] == "playing":
        _dispatch(p, "town")
        return _stamp(p, _dispatch(p, "hall"))
    if option_id not in valid:
        # numbered fallback: "1".."9" resolve positionally
        if option_id.isdigit() and 1 <= int(option_id) <= len(scene.options):
            option_id = scene.options[int(option_id) - 1].id
        elif option_id == "attack" and "close_in" in valid:
            # 002: players and the sidekick say "attack" by habit — at
            # range, for steel, that means crossing the ground.
            option_id = "close_in"
        else:
            # 081: a Collect clicked on a card drawn before the gold
            # moved — the first click already paid out. Swap the card
            # calmly; a refusal would keep the stale button on screen.
            if option_id == "collect":
                scene.shard_note = ("The clerk checks the ledger — that "
                                    "gold is already in your purse.")
                return _stamp(p, scene)
            # 048: no raw id dump — a human reads this. The numbered
            # fallback above means "say the row's number" always works.
            scene.shard_note = (
                "That isn't one of the paths in front of us — "
                "pick one of the numbered rows on the card.")
            scene.refusal = ("That isn't one of the paths — pick a "
                             "numbered row on the card")
            return _stamp(p, scene)
    # 042: a face is a door — clicking any avatar opens that climber's
    # page, from any room, any board.
    if option_id.startswith("pv:") and p.get("location") != "profile":
        from . import profile as profile_mod
        return _stamp(p, profile_mod.open_profile(p, option_id[3:]))
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
    table = list(economy.PRESENT_TABLE)
    if combat.lucky(p):                        # 069: a WORN charm
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
        # legacy doc parked on the dead class question — hand it the
        # starter kit and move it along to the name.
        return _creation_finish_race(p)
    if p["stage"] == "creation_name":
        return _creation_name_scene(p)
    # 030 Phase 8: mid-movie a refresh replays the current beat; the
    # Skip on the card is how a player cuts it short.
    if p.get("movie_floor"):
        return _floor_movie_scene(p)
    if p.get("encounter"):
        fl = schema.get_floor(p["encounter"]["floor"])
        return combat.fight_scene(p, fl)
    from . import hall, social
    loc = p["location"]
    if loc == "muster":
        # The Muster Roll is retired; saved docs may still stand there.
        p["location"] = loc = "town"
    builders = {
        "town": _town_scene, "forge": _forge_scene,
        "arcanum": _arcanum_scene, "medlab": _medlab_scene,
        "lodge": _lodge_scene, "vault": _vault_scene, "pawn": _pawn_scene,
        "sleep_menu": _sleep_menu_scene, "sleeping": _sleeping_scene,
        "board": _board_scene,
        "stone": _stone_scene, "gate": _gate_scene,
        "gate_town": _gate_town_scene,
        "school": _school_scene,
        "relay": social.relay_scene, "fields": social.fields_scene,
        "guildhall": social.guildhall_scene, "hall": hall.hall_scene,
        "grants": social.grant_scene,
        "boss_keep": _boss_keep_scene,
        "warden_keep": _warden_keep_scene,
        "memorial": _memorial_scene,
        "profile": _profile_scene,
    }
    return builders.get(loc, _town_scene)(p)


def _profile_scene(p: dict) -> Scene:
    from . import profile as profile_mod
    return profile_mod.profile_scene(p)


def _boss_keep_scene(p: dict) -> Scene:
    from . import social
    fl = schema.get_floor(max(1, p["floor"]))
    return social.boss_scene(p, fl)


def _warden_keep_scene(p: dict) -> Scene:
    from . import social
    fl = schema.get_floor(max(1, p["floor"]))
    return social.warden_scene(p, fl)


def _warden_has_fallen(p: dict, fl) -> bool:
    """034 §3: a Warden dies once, and the world is the record of it.
    Below the shared frontier the keep is empty; in local dev play (a
    world of one) the personal unlock says the same thing."""
    w = p.get("_world") or {}
    if w:
        return int(w.get("frontier", 1)) > fl.floor
    return p["unlocked_floor"] > fl.floor


def _fall_record(p: dict, fl) -> dict:
    """What the world remembers about this keep's fall. Reads the top
    level first (034), then the map 030 hung under `warden`, so a worldd
    that has not shipped 034 yet still names the slayers."""
    w = p.get("_world") or {}
    rec = (w.get("fallen") or {}).get(str(fl.floor))
    if isinstance(rec, dict):
        return rec
    names = ((w.get("warden") or {}).get("fallen_by") or {}).get(
        str(fl.floor), "")
    return {"names": names} if names else {}


def _memorial_scene(p: dict) -> Scene:
    """034 §3: the keep of a Warden that has already died. It used to
    re-arm as an ECHO bout — a full Warden fight at half pay, repeatable
    forever, on a card that said in as many words that the real one died
    long ago. A dead thing does not pay out twice. What stands here now
    is the story of who killed it and when."""
    fl = schema.get_floor(max(1, p["floor"]))
    rec = _fall_record(p, fl)
    names = rec.get("names") or ""
    body = []
    day = rec.get("day")
    when = ""
    if isinstance(day, int):
        ago = state.world_day() - day
        when = (" today" if ago <= 0 else
                " yesterday" if ago == 1 else
                f" — {ago:,} days ago")
        when = f" on day {day:,}{when}"
    if names:
        body.append(f"Cast down{when} by {names}.")
    elif when:
        body.append(f"Cast down{when}. The roll of names is lost.")
    else:
        body.append("Cast down in the early days of the climb, by "
                    "climbers whose names the Stone no longer carries.")
    if rec.get("top") and rec.get("top_dmg"):
        body.append(f"The deepest cut was {rec['top']}'s: "
                    f"{int(rec['top_dmg']):,}.")
    body.append("The lift above has run free ever since. Nothing waits "
                "in here for you — the wilds outside still do.")
    # 042: the honored fallen — everyone who cut this Warden, ranked by
    # damage dealt, faces on the wall forever.
    board = []
    for i, r in enumerate([x for x in (rec.get("roll") or [])
                           if isinstance(x, dict) and x.get("name")][:70]):
        board.append({"opt": f"pv:{r['name']}", "name": str(r["name"]),
                      "level": int(r.get("level", 1) or 1),
                      "race": str(r.get("race") or ""),
                      "armor": str(r.get("armor") or ""),
                      "rank": i + 1,
                      "sub": f"{int(r.get('dmg', 0) or 0):,} dealt"})
    return Scene(
        eyebrow=f"FLOOR {fl.floor} · THE KEEP",
        headline=f"{fl.warden_name} fell here",
        support="The doors stand open. Nothing has held them since.",
        body_lines=body,
        options=[Option("back", "Back to the camp")],
        meters=combat.meters(p),
        banner=f"warden_{fl.floor:03d}",
        fx="warden_fall",
        players_here=board,
        players_title="THE HONORED FALLEN" if board else "",
    )


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
        return _creation_finish_race(p)
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


# 052: the pick is three portrait cards on one ground line — the face
# chosen here is the face the whole game wears from then on.
_RACE_CARDS = {"human": "WARRIOR", "elf": "ELF", "giant": "GIANT"}


def _creation_race_scene(p: dict) -> Scene:
    return Scene(
        eyebrow="THE TOWER GATE · FIRST LIGHT",
        headline="A shard of old Aldervale chooses you",
        support="Every climber is bonded to a shardmind. Yours just woke up.",
        shard_note="I remember this gate when it was a mountain. Tell me "
                   "what you are, refugee.",
        body_lines=["The registrar's slate wants your line first — "
                    "pick your climber."],
        options=[Option(r, _RACE_CARDS.get(r, r.capitalize()),
                        economy.RACES[r].split(":")[0])
                 for r in economy.RACES],
        gallery=[{"opt": r, "slug": f"portrait_{r}",
                  "label": _RACE_CARDS.get(r, r.capitalize()),
                  "sub": economy.RACES[r].split(".")[0]}
                 for r in economy.RACES],
        banner="gate",
    )


def _creation_pick_race(p: dict, oid: str) -> Scene:
    if oid not in economy.RACES:
        return _creation_race_scene(p)
    p["race"] = oid
    return _creation_finish_race(p)


def _creation_finish_race(p: dict) -> Scene:
    """048: the class question died — every climber walks in with the
    gate's Rusted Sword and two ranks of bladework (enough to swing
    honestly on floor 1; the School sells the rest). The weapon in the
    hand decides everything the class used to."""
    p.setdefault("training", {"blade": 0, "bow": 0, "staff": 0})
    if p["training"].get("blade", 0) < 2:
        p["training"]["blade"] = 2
    p["gear"]["weapon"] = economy.CLASS_STARTERS["warrior"].slug
    p["held"] = [p["gear"]["weapon"]]
    if p.get("name"):
        # 005 web play: the door already carved this name at signup —
        # the registrar recognizes the account and waves them through.
        return _creation_welcome(p)
    p["stage"] = "creation_name"
    return _creation_name_scene(p)


def _creation_name_scene(p: dict) -> Scene:
    # 004: name and username are one string. It is the name the Crier
    # speaks, the name letters are addressed to, and the name on the
    # Stone — so it is one word, and nobody else in the world holds it.
    return Scene(
        eyebrow="THE TOWER GATE · REGISTRAR",
        headline="Your username — the Stone carves the same one",
        support="One word, two to twenty-four strokes, yours alone in the "
                "whole world.",
        shard_note="You get one name here: it signs your letters, rides the "
                   "Crier, and takes the credit when a Warden falls. Spaces "
                   "get joined — granite has no gaps.",
        options=[],
        awaits_text="the climber's username",
        ask={"kind": "text", "max": 24, "label": "your username",
             "placeholder": "one word — the world will read it",
             "submit": "CLAIM IT"},
    )


def _creation_set_name(p: dict, text: str) -> Scene:
    name = names.canonical(text)
    if not names.is_legal(name):
        s = _creation_name_scene(p)
        s.shard_note = ("Two to twenty-four strokes — letters and numbers, "
                        "- and _ if you must. The mason charges by the "
                        "stroke and carves nothing else.")
        return s
    # worldd is the only judge of who already holds a name: it claims the
    # row before the engine runs and leaves the verdict here. Offline play
    # has no registry and no flag — one climber alone may call itself
    # whatever it likes.
    if (p.get("_world") or {}).get("name_claim") == "taken":
        s = _creation_name_scene(p)
        s.shard_note = (f"{name} already climbs — one name, one world. Pick "
                        "another and the registrar writes it down.")
        return s
    p["name"] = name
    s = _creation_welcome(p)
    if names.joined_words(text, name):
        s.body_lines = [f"+ the registrar closes the gaps — you climb as "
                        f"{name}"] + list(s.body_lines)
    return s


def _creation_welcome(p: dict) -> Scene:
    p["stage"] = "playing"
    p["location"] = "town"
    s = _town_scene(p)
    s.headline = f"Welcome to Roothollow, {p['name']}"
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

    # 073: the square in districts. The gate still leads (007); related
    # doors nest under the one you'd look for first. Headers and
    # indent ride the option — the list stays one numbered tap.
    opts = [
        Option("gate", "The Tower Gate", "leave town and climb",
               section="THE CLIMB"),
        Option("board", "The contract board",
               "three jobs a day" if p["level"] >= economy.BOARD_LEVEL
               else f"🔒 level {economy.BOARD_LEVEL}",
               locked=p["level"] < economy.BOARD_LEVEL,
               badge=_b("board"), nest=True),
        Option("forge", "The Forge", "gear", badge=_b("forge"),
               section="THE MARKET"),
        Option("arcanum", "The Arcanum",
               "magic" if _door_open(p, economy.ARCANUM_LEVEL)
               else f"🔒 level {economy.ARCANUM_LEVEL}",
               locked=not _door_open(p, economy.ARCANUM_LEVEL)),
        Option("medlab", "Apothecary & Medlab", "potions"),
        Option("pawn", "Pawn shop", "sell"),
        Option("vault", "The Vault",
               f"deposited ◈ {p['bank']:,}" if p["bank"] > 0 else "bank",
               badge=_b("vault"), section="THE KEEP"),
        Option("lodge", "The Lodge",
               f"pay ◈ {economy.LODGE_PRICE_PER_LEVEL * p['level']}/night",
               badge=_b("lodge")),
        # 037: active sleep — the only thing that mends wounds before dawn.
        # 042: always on — the player sleeps whenever they want, not only
        # when the bar is dry.
        Option("sleep_menu", "Sleep",
               "mend ⚡ and HP faster — the Lodge or the fields"),
        # 012: the Guildhall is core — training (buying levels) lives
        # there, so it must exist even without a connected world.
        Option("guildhall", "The Guildhall",
               p.get("guild") or "training", badge=_b("guildhall"),
               section="THE BANNER"),
    ]
    # 032: members get their own door — the banner's name on the hint.
    # No hall key from the world (older worldd) → no door, old behavior.
    fac = w.get("faction") if isinstance(w.get("faction"), dict) else None
    if fac and isinstance(fac.get("hall"), dict):
        opts.append(Option("hall", "YOUR FACTION'S HALL",
                           str(fac.get("name", "")),
                           badge=_b("hall"), nest=True))
    # 048 retro: the School lives on the square — one school, your
    # ranks ride with you; the floor camps stopped teaching.
    opts.append(Option("school", "The School",
                       "train any weapon — blade, bow, staff"))
    if w:
        inbox = int(w.get("inbox_count") or 0)
        # 040: post with your name on it opens the clerk's window at ANY
        # level — a level-1 climber granted gold must be able to collect
        # it, not stare at a lock.
        relay_open = _door_open(p, economy.RELAY_LEVEL) or inbox > 0
        opts.append(Option(
            "relay", "The Relay Office",
            (f"{inbox} letter{'s' if inbox != 1 else ''}" if inbox
             else "post") if relay_open
            else f"🔒 level {economy.RELAY_LEVEL}",
            locked=not relay_open,
            badge=_b("relay"), section="THE WIRE"))
        opts.append(Option("stone", "Stone of the Climb", "news",
                           nest=True))
        opts.append(Option(
            "fields", "The fields",
            "pvp" if p["level"] >= economy.FIELDS_LEVEL
            else f"🔒 level {economy.FIELDS_LEVEL}",
            locked=p["level"] < economy.FIELDS_LEVEL))
    else:
        opts.append(Option("stone", "Stone of the Climb", "news",
                           section="THE WIRE"))
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
        # 076: coming down from a floor above ground is a lift ride —
        # the square's card carries the descent animation.
        _went_down = int(p.get("floor") or 0) > 0
        p["location"] = "town"
        p["floor"] = 0
        # 032: stepping onto the square drops any hall or banner-page
        # sub-state — the doors reopen fresh
        for k in ("hall_area", "hall_ask", "hall_putting", "hall_kicking",
                  "hall_promoting", "hall_leaving", "guild_leaving",
                  "banner_page", "guild_dir",
                  "door_rules", "profile_view", "profile_back",
                  "profile_pay", "profile_gift", "profile_loot"):
            p.pop(k, None)
        s = _town_scene(p)
        if _went_down:
            s.lift = "down"
        return s
    town_menus = ("forge", "arcanum", "medlab", "lodge", "vault", "pawn",
                  "stone", "gate", "relay", "fields", "guildhall", "hall",
                  "board", "sleep_menu", "school")
    if loc == "town" and oid in town_menus:
        if oid == "arcanum" and not _door_open(p, economy.ARCANUM_LEVEL):
            s = _town_scene(p)
            s.shard_note = (
                "The Arcanum's door reads the hand on it — it wants "
                f"level {economy.ARCANUM_LEVEL}. Climb first; the "
                "star-charts will keep.")
            s.refusal = (f"Entering the Arcanum requires level "
                         f"{economy.ARCANUM_LEVEL} — you are level "
                         f"{p['level']}")
            return s
        # 007: the other locked doors follow the Arcanum's grammar —
        # a level, a reason, no scene change.
        if oid == "relay" and not _door_open(p, economy.RELAY_LEVEL) \
                and not int((p.get("_world") or {})
                            .get("inbox_count") or 0):
            # 040: held post opens the door at any level (see _town_scene)
            s = _town_scene(p)
            s.shard_note = (
                "The Relay clerk sorts post for names the Stone knows — "
                f"level {economy.RELAY_LEVEL} first. Letters keep.")
            s.refusal = (f"Entering the Relay requires level "
                         f"{economy.RELAY_LEVEL} — you are level "
                         f"{p['level']}")
            return s
        if oid == "fields" and p["level"] < economy.FIELDS_LEVEL:
            s = _town_scene(p)
            s.shard_note = (
                "The fields take climbers who can take a hit back — "
                f"level {economy.FIELDS_LEVEL}. The tower first.")
            s.refusal = (f"Entering the fields requires level "
                         f"{economy.FIELDS_LEVEL} — you are level "
                         f"{p['level']}")
            return s
        if oid == "board" and p["level"] < economy.BOARD_LEVEL:
            s = _town_scene(p)
            s.shard_note = (
                "The board hangs work for names it trusts — level "
                f"{economy.BOARD_LEVEL} first. The jobs will keep; "
                "new ones every dawn.")
            s.refusal = (f"Entering the board requires level "
                         f"{economy.BOARD_LEVEL} — you are level "
                         f"{p['level']}")
            return s
        if oid == "gate":
            p["gate_from"] = int(p.get("floor") or 0)   # 076: ride origin
        p["location"] = oid
        return _build_scene(p)
    if oid == "back":
        if loc == "profile":
            # 042: the page closes back onto wherever it was opened from
            from . import profile as profile_mod
            profile_mod.close_profile(p)
            return _build_scene(p)
        if loc == "memorial":
            # 034 §3: the only way out of a monument is back to the camp.
            p["location"] = "gate_town"
        else:
            # 048 retro: the School moved onto the square — it rides
            # town_menus now, so the generic route below takes it home.
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
    if loc == "sleep_menu":
        return _sleep_action(p, oid)
    if loc == "sleeping":
        return _sleeping_action(p, oid)
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
    if loc == "school":
        return _school_action(p, oid)
    if loc == "relay":
        return social.relay_action(p, oid)
    if loc == "fields":
        return social.fields_action(p, oid)
    if loc == "guildhall":
        return social.guildhall_action(p, oid)
    if loc == "hall":
        from . import hall
        return hall.hall_action(p, oid)
    if loc == "grants":
        return social.grant_action(p, oid)
    if loc == "boss_keep":
        return social.boss_action(p, schema.get_floor(max(1, p["floor"])), oid)
    if loc == "warden_keep":
        return social.warden_action(
            p, schema.get_floor(max(1, p["floor"])), oid)
    if loc == "profile":
        from . import profile as profile_mod
        return profile_mod.profile_action(p, oid)
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

    # 031 §14: the stat rides IN the hint now — the Forge's card grid
    # has no body lines to carry it, and richer hints hurt no shop
    # 045: durability rides next to the stat — what the piece can take
    # (guard steel: damage turned; weapons/shoes: swings/strides) is
    # half the price tag's meaning. 048: the word is "durability",
    # spelled out — "END" said nothing to anyone.
    def _end(g):
        return f"durability {economy.endurance(g):,}"

    for g in show:
        hint = f"pay ◈ {g.price:,} · {_stat(g)} · {_end(g)}"
        if g.slug == worn:
            hint += " · worn — spare"
        opts.append(Option(f"buy_{g.slug}", g.name, hint))
        flavor = f", {g.flavor}" if g.flavor else ""
        lines.append(f"{g.name}{flavor} — {_stat(g)}, {_end(g)}")
        # 025 §4: the newest rung is also a CHOICE — the same steel cut
        # keen (sharper, spends itself) or warded (patient). Older rungs
        # stay one row so the rack never becomes a catalogue.
        if g is show[-1]:
            for v in economy.gear_styles(g):
                opts.append(Option(f"buy_{v.slug}", v.name,
                                   f"pay ◈ {v.price:,} · {_stat(v)} · "
                                   f"{_end(v)} · "
                                   f"{economy.STYLE_WORD[v.style]}"))
                lines.append(f"{v.name} — {_stat(v)}, {_end(v)}, "
                             f"{v.flavor}")
    if nxt is not None:
        # 022/002: past the level cap the gate is the WORLD's floor,
        # not your level — the locked row says which one bars it.
        freq = economy.rung_floor_req(nxt)
        gate = (f"floor {freq}" if freq > p["unlocked_floor"]
                else f"level {economy.rung_player_level_req(nxt)}")
        opts.append(Option(
            f"buy_{nxt.slug}", nxt.name,
            f"🔒 {gate} · pay ◈ {nxt.price:,} · {_stat(nxt)} · "
            f"{_end(nxt)}", locked=True))
        lines.append(f"{nxt.name} — {_stat(nxt)}, {_end(nxt)}, "
                     "the rung you're saving for")


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
                                combat._held_lines(p))
    if not stock:
        return
    fold = len(lines) > 8
    lines.append(f"▣ the relic shelf — {len(stock)} on the wall"
                 if fold else "— the relic shelf —")
    for r in stock:
        price = economy.relic_price(r.slug, p["unlocked_floor"])
        owned = p["inventory"].get(r.slug, 0)
        hint = f"pay ◈ {price:,}" + (f" · ×{r.count}" if r.count > 1 else "")
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
        s.refusal = f"Can't buy this — it opens at floor {r.floor}"
        return s
    if r.line and r.line not in combat._held_lines(p):
        s = scene_fn(p)
        word = {"warrior": "blade", "archer": "bow",
                "sorcerer": "staff"}.get(r.line, r.line)
        s.shard_note = (f"The {r.name} answers only to a {word} — "
                        "nothing in your hands can use it.")
        s.refusal = f"Can't buy this — it answers only to a {word}"
        return s
    if r.hold1 and p["inventory"].get(slug, 0) >= 1:
        s = scene_fn(p)
        s.shard_note = (f"You hold a {r.name} already — its kind "
                        "suffers no company. One, exactly.")
        s.refusal = "Can't buy this — you already hold one"
        return s
    if not pack_can_take(p, slug):                           # 012
        return _pack_full(p, scene_fn, r.name)
    price = economy.relic_price(slug, p["unlocked_floor"])
    if p["gold"] < price:
        s = scene_fn(p)
        s.shard_note = (f"The {r.name} is ◈ {price:,} and you carry "
                        f"◈ {p['gold']:,}.")
        s.refusal = f"Can't buy this — not enough gold (◈ {price:,} needed)"
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
    opts, lines = [], []
    # 048: the smith sells every physical line to every hand at list
    # price — the trained rank is the only tax on strange steel.
    # Staves and focuses still live at the Arcanum.
    nod = ("Buy whatever you need for archery and swordsmanship — "
           "magic weapons are sold at the Arcanum, across the square.")
    _rack(p, economy.weapon_line("warrior"), opts, lines)
    _rack(p, economy.weapon_line("archer"), opts, lines)
    _rack(p, economy.gear_rungs("shield"), opts, lines)
    _rack(p, economy.gear_rungs("armor"), opts, lines)
    _rack(p, economy.gear_rungs("shoes"), opts, lines)
    # 048: the gate-issue basics of the other lines hang by the door —
    # a flat coin buys a second path's first weapon. 049: they wear
    # like any steel now, but are never lost and mend for a coin.
    owned = set(combat._held_slugs(p)) | set(p.get("inventory") or {})
    for slug in ("basic_bow", "worn_staff"):
        if slug in owned:
            continue
        g = economy.FORGE[slug]
        opts.append(Option(
            f"buy_{slug}", g.name,
            f"pay ◈ {economy.BASIC_WEAPON_PRICE} · +{g.bonus} ATK · "
            f"durability {economy.endurance(g):,}"))
        lines.append(f"{g.name} — {g.flavor}")
    _relic_rows(p, "forge", opts, lines)      # 006: quivers and tools
    for g in _wearable_pack(p):
        if p["gear"].get(g.slot) != g.slug:
            opts.append(Option(f"wear_{g.slug}", f"Wear {g.name}",
                               "from your pack"))
    cap = economy.max_hone(p["unlocked_floor"])
    price = economy.hone_price(p["unlocked_floor"])
    hone_xp = economy.hone_xp(p["unlocked_floor"])
    # every bench row wears the piece's own 1-bit icon (option_art
    # resolves gear slugs to the same glyph the shop rows use)
    mend_art: dict[str, str] = {}
    for slot in economy.HONE_SLOTS:
        slug = p["gear"].get(slot)
        lvl = state.hone_level(p, slot)
        if slug and lvl < cap:
            name = economy.FORGE[slug].name
            opts.append(Option(f"hone_{slot}", f"Hone {name} +{lvl + 1}",
                               f"pay ◈ {price:,} · +{hone_xp} XP"))
            mend_art[f"hone_{slot}"] = slug
    # 005: the repair bench — every worn PAID piece on the body gets a
    # row; price scales with the missing fraction, XP mirrors honing.
    # 0.29.4: a held repair token adds a FREE row per worn piece — the
    # token finally spends where its name promised.
    tokens = p["inventory"].get("repair_token", 0)
    for slot in economy.DURABILITY_SLOTS:
        g = economy.FORGE.get(p["gear"].get(slot) or "")
        left = (p.get("durability") or {}).get(slot)
        if not g or not economy.wears(g) or left is None:
            continue
        pool = economy.item_pool(g)
        if left >= pool:
            continue
        rprice = economy.repair_price(g, 1 - left / pool)
        opts.append(Option(
            f"repair_{slot}",
            f"Repair {g.name}" + (" — broken" if left <= 0 else ""),
            f"pay ◈ {rprice:,} · +{hone_xp} XP · "
            f"durability {economy.endurance(g, left):,} → "
            f"{economy.endurance(g):,}"))
        mend_art[f"repair_{slot}"] = g.slug
        if tokens > 0:
            opts.append(Option(
                f"token_{slot}",
                f"Mend {g.name} with a token",
                f"free — {tokens} held"))
            mend_art[f"token_{slot}"] = g.slug
    if cap > 0:
        honed = ", ".join(
            f"{slot} +{state.hone_level(p, slot)}"
            for slot in economy.HONE_SLOTS if state.hone_level(p, slot))
        lines.append(f"Honing bench: up to +{cap} per piece this band"
                     + (f" — yours: {honed}" if honed else ""))
    # 012: the pack rack — ONE row, the next size up. Below its level
    # the row shows LOCKED with the level on it (049.2: a locked row
    # that names its gate, never a bare hint beside a buyable look).
    have = pack_cap(p)
    nxt = economy.pack_next_tier(have)
    if nxt:
        lvl_req, slots, gold = nxt
        level = int(p.get("level", 1))
        # 064: the pack is a card like every other buyable — the next
        # tier's face rides scene.option_art; the old pack stays yours.
        pk = economy.PACKS.get(economy.pack_slug(slots))
        label = f"{pk.name} — {slots} slots" if pk else \
            f"Larger pack — {slots} slots"
        if level < lvl_req:
            opts.append(Option(
                "buy_pack", label,
                f"🔒 level {lvl_req} · ◈ {gold:,}", locked=True))
        else:
            opts.append(Option(
                "buy_pack", label,
                f"pay ◈ {gold:,} · {have} → {slots} slots"))
        mend_art["buy_pack"] = economy.pack_slug(slots)
    opts.append(Option("back", "Back to the square"))
    tier = economy.gear_tier_for_floor(p["unlocked_floor"])
    # 031 §14: the Forge is a card wall now — no prose above the racks.
    # Everything the body lines used to say lives in the hints and the
    # [i] tips; `lines` is built and dropped so _rack stays one shape.
    # 048: one folded legend survives — the cards' words, in plain
    # English, for anyone who never played a game with a stat line.
    legend = [
        "▣ what the cards say — in plain words",
        "• cost — the gold you hand over once, at the counter.",
        "• attack / defense — attack is how hard you hit; "
        "defense is how much of a blow you shrug off.",
        "• durability — how many hits a piece can take before it "
        "breaks. Bring it back here and the smith repairs it.",
        "• speed — boots only: how much earlier you strike.",
        "▣.",
    ]
    return Scene(
        eyebrow="ROOTHOLLOW · THE FORGE",
        headline=f"Tier {tier} steel, scrap to plasma",
        shard_note=nod,
        body_lines=legend,
        options=opts,
        grid=True,
        meters=combat.meters(p),
        banner="forge",
        option_art=mend_art,
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
        s.refusal = f"Can't hone — not enough gold (◈ {price:,} needed)"
        return s
    if p["xp"] < xp_cost:
        s = _forge_scene(p)
        s.shard_note = (f"The bench takes {xp_cost} XP of what you've "
                        f"learned along with the coin — you carry "
                        f"{p['xp']} XP. Hunt first.")
        s.refusal = f"Can't hone — not enough XP ({xp_cost} needed)"
        return s
    p["gold"] -= price
    state.spend_xp(p, xp_cost)
    state.set_hone(p, slot, lvl + 1)
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
    if (not g or not economy.wears(g) or left is None
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
    if not g or not economy.wears(g) or left is None:
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
        s.refusal = f"Can't mend — not enough gold (◈ {price:,} needed)"
        return s
    if p["xp"] < xp_cost:
        s = _forge_scene(p)
        s.shard_note = (f"The smith takes {xp_cost} XP of what you've "
                        f"learned along with the coin — you carry "
                        f"{p['xp']} XP. Hunt first.")
        s.refusal = f"Can't mend — not enough XP ({xp_cost} needed)"
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
    equip + old piece to the pack. 048: list price for every hand —
    the trained rank is the only tax on a strange line."""
    req = economy.rung_player_level_req(g)
    price = g.price
    if p["level"] < req:
        s = scene_fn(p)
        s.shard_note = (f"{g.name} answers to level {req} hands — you are "
                        f"level {p['level']}. The Guildhall trains climbers "
                        "with a full XP bar and the fee in gold.")
        s.refusal = (f"Can't buy this — it needs a level {req} hand "
                     f"— you are level {p['level']}")
        return s
    freq = economy.rung_floor_req(g)
    if freq > p["unlocked_floor"]:
        # 022/002: deep steel waits for the WORLD to climb there
        s = scene_fn(p)
        s.shard_note = (f"{g.name} is floor-{freq} work — the war has "
                        f"only opened floor {p['unlocked_floor']}. The "
                        "smith won't sell steel the tower hasn't earned.")
        s.refusal = f"Can't buy this — floor {freq} isn't open yet"
        return s
    if p["gold"] < price:
        s = scene_fn(p)
        s.shard_note = f"{g.name} wants ◈ {price:,}; you carry ◈ {p['gold']:,}. " \
                       "The Vault pays interest for a reason."
        s.refusal = f"Can't buy this — not enough gold (◈ {price:,} needed)"
        return s
    old = p["gear"].get(g.slot)
    if old == g.slug:
        # 019: a spare of the piece you wear — straight to the pack,
        # fresh pool, nothing on your body moves. Wear in the pack is
        # tracked per slug: a fresh copy only claims the key when no
        # stashed copy holds it (the armory takes donations as-is).
        if not pack_can_take(p, g.slug):                     # 012
            return _pack_full(p, scene_fn, "spare")
        p["gold"] -= price
        p["inventory"][g.slug] = p["inventory"].get(g.slug, 0) + 1
        p.setdefault("durability_pack", {}).setdefault(
            g.slug, economy.item_pool(g))
        combat._ledger(p, "buy", gold=-price, note=f"{g.slug} (spare)")
        s = scene_fn(p)
        s.body_lines.insert(0, (f"+ {g.name} — a spare for the pack "
                                "(the armory takes donations)"))
        return s
    # 012: the old piece rides to the pack — only if the pack has room
    # for it (a paid piece or gate basic; the scrap bin takes the rest).
    if old and (economy.FORGE[old].price > 0
                or old in economy.BASIC_WEAPONS) \
            and not pack_can_take(p, old):
        return _pack_full(p, scene_fn, f"{economy.FORGE[old].name} you wear")
    p["gold"] -= price
    p["gear"][g.slot] = g.slug
    # 048 phase 3: the hand changed — held[0] follows, the old piece
    # leaves the held list (it rides to the pack below, not both).
    if g.slot == "weapon":
        # 069: the new blade takes the lead's SLOT — held is slot order
        held = p.setdefault("held", [])
        if g.slug in held:
            held.remove(g.slug)
        if old in held:
            held[held.index(old)] = g.slug
        else:
            held.insert(0, g.slug)
        del held[max(1, int(p.get("slots", 1))):]
    if g.slot != "weapon":
        state.set_hone(p, g.slot, 0)  # honing lives on the item it honed
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
    # 049: the basic weapon rides to the pack with the paid gear — the
    # scrap bin only takes the gate guard kit now.
    if old and (economy.FORGE[old].price > 0
                or old in economy.BASIC_WEAPONS):
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
    # 056: faction grain — the banner hears about new steel.
    if p.get("_world") is not None and p.get("guild"):
        from . import social
        social._effect(p, "happening", scope="faction",
                       line=f"{p.get('name') or 'A climber'} bought "
                            f"{g.name}",
                       meta={"item": g.slug})
    s = scene_fn(p)
    s.body_lines.insert(0, note)
    return s


def _wear_charm(p: dict, slug: str, scene_fn) -> Scene:
    """069: set a charm / potion / relic in the pouch from the pack; the
    one there goes back to the pack (capacity checked first)."""
    lock = economy.slot_lock(p, "charm")
    if lock:
        s = scene_fn(p)
        s.shard_note = lock
        return s
    if p.get("encounter"):
        s = scene_fn(p)
        s.shard_note = NOT_IN_A_FIGHT
        return s
    inv = p.setdefault("inventory", {})
    if inv.get(slug, 0) <= 0:
        return scene_fn(p)
    old = p["gear"].get("charm")
    if old == slug:
        s = scene_fn(p)
        s.shard_note = "One is already in your pouch."
        return s
    if old and inv.get(old, 0) <= 0 and inv.get(slug, 0) > 1 \
            and pack_used(p) >= pack_cap(p):
        s = scene_fn(p)
        s.shard_note = pack_full_why(p)
        s.refusal = f"Can't swap — pack full ({pack_used(p)}/{pack_cap(p)})"
        return s
    inv[slug] -= 1
    if inv[slug] <= 0:
        del inv[slug]
    if old:
        inv[old] = inv.get(old, 0) + 1
    p["gear"]["charm"] = slug
    if slug == "luck_charm" and int(p.get("charm_dur") or 0) <= 0:
        p["charm_dur"] = economy.CHARM_POOL
    name = (economy.APOTHECARY[slug].name if slug in economy.APOTHECARY
            else economy.RELICS[slug].name if slug in economy.RELICS
            else slug)
    combat._ledger(p, "use", note=f"pouch {slug}")
    s = scene_fn(p)
    line = f"+ {name} in the pouch — it acts from there"
    if old:
        oname = (economy.APOTHECARY[old].name if old in economy.APOTHECARY
                 else economy.RELICS[old].name if old in economy.RELICS
                 else old)
        line += f"; the {oname} goes to your pack"
    s.body_lines.insert(0, line)
    return s


def _wear_from_pack(p: dict, slug: str, scene_fn) -> Scene:
    if slug in economy.CHARM_KINDS and slug not in economy.FORGE:
        return _wear_charm(p, slug, scene_fn)
    g = economy.FORGE.get(slug)
    if not g or (p.get("inventory") or {}).get(slug, 0) <= 0:
        return scene_fn(p)
    req = _wear_level_req(slug)
    if p["level"] < req:
        s = scene_fn(p)
        s.shard_note = (f"🔒 level {req} — {g.name} answers to level {req} "
                        f"hands; you are level {p['level']}.")
        s.refusal = f"Can't wear this — it needs a level {req} hand"
        return s
    old = p["gear"].get(g.slot)
    # 069: a full hand / a worn piece sends the OLD one to the pack —
    # refuse first if the pack can't take it (the stack being worn may
    # free a slot, which counts)
    held = p.get("held") or []
    cap = max(1, int(p.get("slots", 1)))
    to_pack = old if g.slot != "weapon" else (
        old if (slug not in held and len(held) >= cap) else None)
    if to_pack and economy.FORGE.get(to_pack) \
            and (economy.FORGE[to_pack].price > 0
                 or to_pack in economy.BASIC_WEAPONS) \
            and not pack_can_take(p, to_pack) \
            and p["inventory"][slug] > 1:
        s = scene_fn(p)
        s.shard_note = pack_full_why(p)
        s.refusal = f"Can't swap — pack full ({pack_used(p)}/{pack_cap(p)})"
        return s
    p["inventory"][slug] -= 1
    if p["inventory"][slug] <= 0:
        del p["inventory"][slug]
    p["gear"][g.slot] = slug
    if g.slot != "weapon":
        state.set_hone(p, g.slot, 0)
    # 005: swap the wear along with the piece — no fresh pool for free.
    stash = p.setdefault("durability_pack", {})
    old_dur = (p.get("durability") or {}).pop(g.slot, None)
    if old and old_dur is not None:
        stash[old] = old_dur
    if economy.wears(g):
        p.setdefault("durability", {})[g.slot] = stash.pop(
            slug, economy.item_pool(g))
    # 048 phase 3: CARRY — a free slot keeps the old weapon in hand
    # instead of bumping it to the pack; held[0] is always the hand.
    kept = False
    if g.slot == "weapon":
        # 069: held is slot order — a free slot takes the new blade and
        # the old one stays where it was; a full hand swaps the lead's
        # slot. The lead pointer moves to the new blade either way.
        held = p.setdefault("held", [])
        cap = max(1, int(p.get("slots", 1)))
        if slug not in held:
            if len(held) < cap:
                held.append(slug)
            elif old in held:
                held[held.index(old)] = slug
            else:
                held.insert(0, slug)
        del held[cap:]
        kept = bool(old) and old in held and old != slug
    note = f"+ {g.name} back on"
    if kept:
        note += (f" — the {economy.FORGE[old].name} stays in your "
                 "other hand")
    elif old and economy.FORGE.get(old) \
            and (economy.FORGE[old].price > 0
                 or old in economy.BASIC_WEAPONS):
        p["inventory"][old] = p["inventory"].get(old, 0) + 1
        note += f" — the {economy.FORGE[old].name} goes to your pack"
    s = scene_fn(p)
    s.body_lines.insert(0, note)
    return s


def _basic_buy(p: dict, slug: str, scene_fn) -> Scene:
    """048: a gate-issue basic of another line — flat coin, never lost
    (049: it wears now, but the smith mends gate steel for a coin). It
    goes into a free carry slot if one is open, else into the pack
    (promote it on the road)."""
    g = economy.FORGE[slug]
    owned = set(combat._held_slugs(p)) | set(p.get("inventory") or {})
    if slug in owned:
        s = scene_fn(p)
        s.shard_note = f"You already carry a {g.name} — one is plenty; " \
                       "the Forge mends gate steel for a coin."
        s.refusal = "Can't buy this — you already carry one"
        return s
    if len(p.get("held") or []) >= max(1, int(p.get("slots", 1))) \
            and not pack_can_take(p, slug):                  # 012
        return _pack_full(p, scene_fn, g.name)
    price = economy.BASIC_WEAPON_PRICE
    if p["gold"] < price:
        s = scene_fn(p)
        s.shard_note = (f"{g.name} wants ◈ {price}; you carry "
                        f"◈ {p['gold']:,}.")
        s.refusal = f"Can't buy this — not enough gold (◈ {price} needed)"
        return s
    p["gold"] -= price
    held = p.setdefault("held", [])
    cap = max(1, int(p.get("slots", 1)))
    if len(held) < cap:
        held.append(slug)
        where = "into your free hand"
    else:
        p["inventory"][slug] = p["inventory"].get(slug, 0) + 1
        where = "into your pack"
    combat._ledger(p, "buy", gold=-price, note=slug)
    s = scene_fn(p)
    s.body_lines.insert(0, f"+ {g.name} — {where}. The School teaches "
                           "any weapon to bite.")
    return s


def _forge_pack(p: dict) -> Scene:
    """012: the next pack tier — level gate, sequential, gold only."""
    have = pack_cap(p)
    nxt = economy.pack_next_tier(have)
    if not nxt:
        s = _forge_scene(p)
        s.shard_note = (f"Your pack already holds {have} — the smith "
                        "has nothing larger.")
        s.refusal = "Can't buy this — your pack is the largest made"
        return s
    lvl_req, slots, gold = nxt
    level = int(p.get("level", 1))
    if level < lvl_req:
        s = _forge_scene(p)
        s.shard_note = (f"The {slots}-slot pack opens at level {lvl_req} "
                        f"— you're level {level}.")
        s.refusal = (f"Can't buy this — it opens at level {lvl_req} "
                     f"(you: {level})")
        return s
    if p["gold"] < gold:
        s = _forge_scene(p)
        s.shard_note = (f"The {slots}-slot pack is ◈ {gold:,} and you "
                        f"carry ◈ {p['gold']:,}.")
        s.refusal = f"Can't buy this — not enough gold (◈ {gold:,} needed)"
        return s
    p["gold"] -= gold
    p["pack_slots"] = slots
    combat._ledger(p, "buy", gold=-gold, note=f"pack {slots}")
    # 064: the old pack goes INTO the new one — an item now, sold at
    # the broker or put in the faction chest. Three more slots than it
    # had, so it always fits.
    old = economy.pack_slug(have)
    inv = p.setdefault("inventory", {})
    if old in economy.PACKS:
        inv[old] = int(inv.get(old, 0)) + 1
    s = _forge_scene(p)
    s.body_lines.insert(0, f"+ a larger pack — {slots} slots now "
                           f"(was {have}). The straps take the weight."
                           + (f" Your old {economy.PACKS[old].name} rides "
                              "inside it — the broker buys it, or the "
                              "faction chest takes it."
                              if old in economy.PACKS else ""))
    return s


def _forge_buy(p: dict, oid: str) -> Scene:
    if oid == "buy_pack":
        return _forge_pack(p)
    if oid.startswith("hone_") and oid.removeprefix("hone_") in \
            economy.HONE_SLOTS:
        return _forge_hone(p, oid.removeprefix("hone_"))
    if oid.startswith("repair_") and oid.removeprefix("repair_") in \
            economy.DURABILITY_SLOTS:
        return _forge_repair(p, oid.removeprefix("repair_"))
    if oid.startswith("token_") and oid.removeprefix("token_") in \
            economy.DURABILITY_SLOTS:
        return _forge_token_mend(p, oid.removeprefix("token_"))
    if oid.startswith("wear_"):
        return _wear_from_pack(p, oid.removeprefix("wear_"), _forge_scene)
    slug = oid.removeprefix("buy_")
    if slug in economy.RELICS and economy.RELICS[slug].shop == "forge":
        return _relic_buy(p, slug, _forge_scene)
    if slug in ("basic_bow", "worn_staff"):
        return _basic_buy(p, slug, _forge_scene)
    g = economy.FORGE.get(slug)
    if not g:
        return _forge_scene(p)
    if g.line == "sorcerer":
        s = _forge_scene(p)
        s.shard_note = "The smith shrugs: caster's work. The Arcanum " \
                       "sells the staves and the focuses."
        s.refusal = "Can't buy this here — the Arcanum sells caster's work"
        return s
    return _gear_purchase(p, g, _forge_scene)


# ── The Arcanum (004 §3.4) ───────────────────────────────────────────────

def _arcanum_scene(p: dict) -> Scene:
    if not _door_open(p, economy.ARCANUM_LEVEL):
        p["location"] = "town"
        s = _town_scene(p)
        s.shard_note = (f"The Arcanum wants level {economy.ARCANUM_LEVEL} "
                        "hands. Climb first.")
        s.refusal = (f"Entering the Arcanum requires level "
                     f"{economy.ARCANUM_LEVEL} — you are level "
                     f"{p['level']}")
        return s
    opts, lines = [], []
    # 048: star-charts for every hand — the full staff line and the
    # focuses at list price; the trained rank is the only gate.
    _rack(p, economy.weapon_line("sorcerer"), opts, lines)
    _rack(p, economy.gear_rungs("shield", "sorcerer"), opts, lines)
    _relic_rows(p, "arcanum", opts, lines)    # 006: the magic relics
    opts.append(Option("back", "Back to the square"))
    # 057: the Arcanum is the Forge's twin now — a card wall, not prose
    # above a list. One line of explanation survives as the shard note;
    # `lines` is built and dropped so _rack stays one shape, and the
    # same folded legend rides the foot of the wall.
    nod = ("Staves and focuses for every hand — steel and armor are "
           "sold at the Forge, across the square.")
    legend = [
        "▣ what the cards say — in plain words",
        "• cost — the gold you hand over once, at the counter.",
        "• attack / defense — attack is how hard you hit; "
        "defense is how much of a blow you shrug off.",
        "• durability — how many hits a piece can take before it "
        "breaks. The Forge's smith repairs caster's work too.",
        "▣.",
    ]
    return Scene(
        eyebrow="ROOTHOLLOW · THE ARCANUM",
        headline="Star-charts, staves and patient glass",
        shard_note=nod,
        body_lines=legend,
        options=opts,
        grid=True,
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
        s.refusal = "Can't buy this here — the Forge sells the steel"
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
        grid=True,  # 062: the shelf is a card wall — every ware wears its face
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
        s.refusal = "Can't buy this — one energy cell a day"
        return s
    if slug != "energy_cell" and not pack_can_take(p, slug):    # 012
        return _pack_full(p, _medlab_scene, item.name)
    if p["gold"] < item.price:
        s = _medlab_scene(p)
        s.shard_note = f"That's ◈ {item.price} and you carry ◈ {p['gold']}."
        s.refusal = f"Can't buy this — not enough gold (◈ {item.price} needed)"
        return s
    p["gold"] -= item.price
    combat._ledger(p, "buy", gold=-item.price, note=slug)
    note = f"+ {item.name}"
    if slug == "energy_cell":
        daily["energy_cell"] = True
        state.gain_energy(p, 5)
        note += " — ⚡ +5"
    elif slug == "luck_charm":
        # 069: it lands in the pack — wear it in the charm pouch to
        # feel it (nothing works from the pack)
        p["inventory"][slug] = p["inventory"].get(slug, 0) + 1
        note += " — set it in your charm pouch; it does nothing in the pack"
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
        s.refusal = (f"Can't buy this — not enough gold "
                     f"(◈ {economy.STEW_PRICE} needed)")
        return s
    if p["hp"] >= state.max_hp(p):
        s = scene_fn(p)
        s.shard_note = "You're whole. Save the coin for when you're not."
        s.refusal = "No need — you're already at full HP"
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
    # 041: one door to a bunk — "Turn in" pays the night itself, so the
    # separate "Pay for the night" row only read as a second sleep.
    if p["hp"] < state.max_hp(p):
        opts.append(Option("stew", "Hunter's stew",
                           f"pay ◈ {economy.STEW_PRICE} · "
                           f"+{economy.STEW_HEAL_HP} HP"))
    # 037: lie down and actively sleep — the clocks run while you do
    _sp = _sleep_spec("lodge")
    opts.append(Option("lie_down", "Turn in — sleep now",
                       f"⚡ ×{_sp['mult']:g} · full HP ~{_sp['hp_h']:g} h"
                       + ("" if lodged else f" · pay ◈ {price}")))
    body = [f"A night costs ◈ {price}. Banked gold can't buy it — "
            "carry coin.",
            # 022/004: dawn heals everyone everywhere — the Lodge
            # sells the one thing dawn doesn't: not being found.
            "Dawn closes wounds wherever you lie. The palisade "
            "is about who can FIND you before it does."]
    # 022/005: the night slot — one action per night, resolved at dawn.
    # 0.29.1: below the level it is SHOWN and locked — a visible door is
    # a reason to climb; an invisible one is nothing.
    # 031 §10/§11: say it plainly. The job is a JOB OFFER with the pay
    # and the trade-off in the line; the rest is an ACTIVITY; whichever
    # is picked lives in the activity band under the options.
    activity = ""
    if p["level"] < economy.NIGHT_SLOT_LEVEL:
        body.append("The night slot — one action a night: rest by the "
                    "fire or take a shift for coin at dawn.")
        opts.append(Option("night_slot", "The night slot",
                           f"🔒 level {economy.NIGHT_SLOT_LEVEL}",
                           locked=True))
    if p["level"] >= economy.NIGHT_SLOT_LEVEL:
        day = state.world_day()
        shift = _night_shift(day)
        work_pay = economy.night_work_gold(max(1, p["unlocked_floor"]))
        rest_pool = economy.night_rest_aether(p["level"])
        body.append("One thing gets done per night: work a shift for "
                    "coin, or rest by the fire and fight sharper "
                    "tomorrow. Either way dawn still closes your wounds.")
        night = p.get("night") or {}
        plan = night.get("choice") if night.get("day") == day else None
        if plan == "rest":
            activity = (f"ACTIVITY IN THE LODGE: resting by the fire — "
                        f"✦ {rest_pool} banked at dawn, spent as "
                        f"+{round(economy.RESTED_XP_BONUS_PCT * 100)}% "
                        "XP on your next kills")
        elif plan == "work":
            activity = (f"ACTIVITY IN THE LODGE: job taken — {shift}, "
                        f"◈ {work_pay} paid at dawn (a working night: "
                        "no rested-XP bonus)")
        else:
            activity = "ACTIVITY IN THE LODGE: no activity selected"
        if plan != "rest":
            opts.append(Option(
                "night_rest", "ACTIVITY: rest by the fire",
                f"✦ {rest_pool} banked — sharper kills, no pay"))
        if plan != "work":
            opts.append(Option(
                "night_work", f"JOB OFFER: {shift}",
                f"receive ◈ {work_pay} at dawn — paid work, no "
                "rested-XP bonus"))
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
                f"pay ◈ {economy.FIRE_STEW_GOLD} · a letter with it"))
    # 031 §9: the keeper has a face and a name now — Wick.
    opts.append(Option("talk", "Talk with Wick", "the keeper · free"))
    opts.append(Option("back", "Back to the square"))
    return Scene(
        eyebrow="ROOTHOLLOW · THE LODGE",
        headline="Sleep behind the palisade" if not lodged
                 else "Your bunk is paid through tonight",
        support="Skip the lodge and you sleep in the fields — where anyone "
                "may find you.",
        body_lines=body,
        options=opts,
        activity=activity,
        meters=combat.meters(p),
        banner="lodge",
    )


def _keeper_scene(p: dict) -> Scene:
    """030 Phase 6 → 031 §9: the keeper is Wick now — a stout one-armed
    old climber with a braided beard and a tankard he never sets down.
    He explains the lodge, bores you with his life story, and hands out
    the lore of the tower in the same breath. Every number is read off
    economy.py at build time; the prose rotates so a second ask is not
    a replay. His portrait rides scene.npc; this is Wick's room — no
    shard chatter in it."""
    day = state.world_day()
    shift = _night_shift(day)
    work = economy.night_work_gold(max(1, p["unlocked_floor"]))
    rest = economy.night_rest_aether(p["level"])
    tellings = (
        ["“Lodge works like this, and I'll keep it short because the "
         "beer won't. A bunk for the night keeps the ambushers off "
         "you — dawn heals everybody, but only the palisade decides "
         "who FINDS you first. One thing gets done per night: a shift "
         f"for coin — tonight it's {shift}, ◈ {work} at dawn — or you "
         f"rest by my fire and bank ✦ {rest} toward your next kills. "
         "Work pays, rest sharpens. Pick one, you can't have both. "
         "Now, did I ever tell you about my elbows? Forty years of "
         "carrying trays. Ruined. Both of them.”"],
        [f"“Brand never swung harder than anyone. He just slept "
         f"smarter. A night by my fire banks ✦ {rest}, and it rides "
         f"out at +{round(economy.RESTED_XP_BONUS_PCT * 100)}% a kill "
         "till the pool runs dry — "
         f"{economy.RESTED_POOL_CAP_NIGHTS} nights' worth it holds, no "
         "more. He rested, he killed rested, he leveled a floor ahead "
         "of climbers twice his arm. Glory is a schedule.”"],
        ["“The arm? Floor nine took it. I was a climber once — Wick "
         "the Quick, if you can believe it, and my knees certainly "
         "can't anymore. Made it past three Wardens in my day. The "
         "tower was here before Roothollow, before the wire, before "
         "anyone thought to charge for beds — the Wardens don't guard "
         "the floors, you know. They guard the LIFT. Kill one anywhere "
         "and the whole world rides up free. That's why every blade "
         "counts, even the rusty ones. Especially the rusty ones. "
         "I was a rusty one.”"],
        [f"“Asha kept every coin she won in the Vault — "
         f"{round(economy.BANK_INTEREST_RATE * 100)}% a day it pays, "
         "stubs dripping in all day, regular as bells. Little numbers. She let "
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
        body.insert(0, "The old man behind the counter sets down the "
                       "ledger — one arm, a braided beard, a tankard "
                       "that never empties. “Wick. Keeper of this roof "
                       "and everything it knows. A new name for the "
                       "book, then.”")
    return Scene(
        eyebrow="ROOTHOLLOW · THE LODGE",
        headline="Wick leans on the counter",
        support="Ask again — Wick always has another story, and most "
                "of them are even true.",
        body_lines=body,
        npc={"name": "Wick", "portrait": "wick"},
        options=[Option("talk", "Talk with Wick — another story", "free"),
                 Option("back", "Back to the square")],
        meters=combat.meters(p),
        banner="lodge",
    )


def _lodge_action(p: dict, oid: str) -> Scene:
    if oid == "lie_down":
        return _sleep_action(p, "sleep_lodge")
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
            s.refusal = (f"Can't buy this — not enough gold "
                         f"(◈ {economy.FIRE_STEW_GOLD} needed)")
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
        s.refusal = (f"The night slot requires level "
                     f"{economy.NIGHT_SLOT_LEVEL} — you are level "
                     f"{p['level']}")
        return s
    if oid in ("night_rest", "night_work"):
        p["night"] = {"day": state.world_day(),
                      "choice": "rest" if oid == "night_rest" else "work"}
        s = _lodge_scene(p)
        s.shard_note = ("The night is planned. Dawn settles it — one "
                        "action a night, no more.")
        return s
    # 041: "Pay for the night" folded into lie_down — one door to a bunk
    return _lodge_scene(p)


# ── 037: active sleep — the fast clock ──────────────────────────────────
# Awake, ⚡ ticks every ENERGY_REGEN_MIN minutes and wounds wait for dawn.
# Turning in runs both clocks: the fields free and rough, the Lodge paid,
# palisaded, and exactly double the waking pace.

def _sleep_spec(where: str) -> dict:
    mult = economy.SLEEP_ENERGY_MULT[where]
    return {
        "mult": mult,
        "e_min": economy.ENERGY_REGEN_MIN / mult,
        "hp_h": economy.SLEEP_HP_FULL_MIN[where] / 60.0,
    }


def _sleep_menu_scene(p: dict) -> Scene:
    price = economy.LODGE_PRICE_PER_LEVEL * p["level"]
    lodged = p["lodged_until_day"] >= state.world_day() + 1
    lg, fd = _sleep_spec("lodge"), _sleep_spec("fields")
    body = [
        f"Awake, ⚡ returns 1 point every {economy.ENERGY_REGEN_MIN} min "
        "and wounds wait for dawn. Sleep runs both clocks:",
        f"· THE LODGE — ⚡ 1 point every {lg['e_min']:g} min "
        f"(×{lg['mult']:g}, double the waking pace) and a full HP bar "
        f"mends in about {lg['hp_h']:g} hours. The palisade keeps "
        "ambushers off you"
        + (" — your bunk is already paid." if lodged
           else f" — a bunk costs ◈ {price} carried coin."),
        f"· THE FIELDS — free. ⚡ 1 point every {fd['e_min']:g} min "
        f"(×{fd['mult']:g}) and a full HP bar mends in about "
        f"{fd['hp_h']:g} hours. You sleep rough — anyone hunting the "
        "fields can still find you.",
        "Wake whenever you like — the meters bank what the clock earned.",
    ]
    return Scene(
        eyebrow="ROOTHOLLOW · TURNING IN",
        headline="Where do you sleep?",
        support="Sleep is the only thing that mends wounds before dawn "
                "does — and the only way to hurry the energy bar.",
        body_lines=body,
        options=[
            Option("sleep_lodge", "A bunk at the Lodge",
                   f"⚡ ×{lg['mult']:g} · full HP ~{lg['hp_h']:g} h · "
                   + ("bunk paid" if lodged else f"pay ◈ {price}")
                   + " · safe"),
            Option("sleep_fields", "Find a place in the fields",
                   f"⚡ ×{fd['mult']:g} · full HP ~{fd['hp_h']:g} h · "
                   "free · ambushers can find you"),
            Option("back", "Back to the square"),
        ],
        meters=combat.meters(p),
        banner="lodge",
    )


def _sleep_fx(p: dict, where: str) -> str:
    """One sleeping animation per showcase character per place — the art
    canon puts every figure on one of the three class silhouettes."""
    g = economy.FORGE.get(p["gear"].get("weapon") or "")
    look = (g.line if g and g.line else "") or "warrior"
    return f"sleep_{where}_{look}"


def _sleeping_scene(p: dict, note: str = "") -> Scene:
    state.apply_sleep_healing(p)
    s = p.get("sleeping") or {}
    where = s.get("where", "fields")
    sp = _sleep_spec(where)
    place = ("in your bunk at the Lodge" if where == "lodge"
             else "in a hollow in the fields")
    body = [
        f"⚡ 1 point every {sp['e_min']:g} min (×{sp['mult']:g} the waking "
        f"pace) · wounds mend a full bar in ~{sp['hp_h']:g} h.",
        ("The palisade keeps watch. Nothing finds you here."
         if where == "lodge" else
         "You sleep rough — anyone hunting the fields can find you."),
    ]
    return Scene(
        eyebrow="ROOTHOLLOW · ASLEEP",
        headline="Asleep behind the palisade" if where == "lodge"
                 else "Asleep under the open sky",
        support="The clocks work while you don't. Wake whenever you like.",
        body_lines=body,
        shard_note=note,
        activity=f"ASLEEP {place.upper()} — ⚡ and HP mending",
        options=[Option("doze", "Sleep on", "let the clock work"),
                 Option("wake", "Wake up")],
        meters=combat.meters(p),
        banner="lodge" if where == "lodge" else "roothollow",
        fx=_sleep_fx(p, where),
    )


def _sleep_action(p: dict, oid: str) -> Scene:
    if oid == "sleep_fields":
        state.start_sleep(p, "fields")
        p["location"] = "sleeping"
        if p.get("_world") is not None:
            from . import social
            social._effect(p, "happening",
                           line=f"{p.get('name') or 'A climber'} lies down "
                                f"in the open fields of floor "
                                f"{p.get('floor', 1)}",
                           floor=p.get("floor", 1))
        return _sleeping_scene(p, note="You roll into a hollow out of the "
                                       "wind and let the fields hold you.")
    if oid != "sleep_lodge":
        return _sleep_menu_scene(p)
    if p["lodged_until_day"] < state.world_day() + 1:
        price = economy.LODGE_PRICE_PER_LEVEL * p["level"]
        if p["gold"] < price:
            s = _sleep_menu_scene(p)
            s.shard_note = (f"A bunk is ◈ {price} carried coin. The fields "
                            "are free — or the Vault is on the square.")
            s.refusal = (f"Can't rent a bunk — not enough carried gold "
                         f"(◈ {price} needed)")
            return s
        p["gold"] -= price
        p["lodged_until_day"] = state.world_day() + 1
        combat._ledger(p, "lodge", gold=-price)
    state.start_sleep(p, "lodge")
    p["location"] = "sleeping"
    return _sleeping_scene(p, note="Wick nods you up the stairs. The bunk "
                                   "is warm and the palisade stands its "
                                   "quiet watch.")


def _sleeping_action(p: dict, oid: str) -> Scene:
    if oid != "wake":
        return _sleeping_scene(p)
    hp0 = p["hp"]
    where = state.wake_up(p)
    healed = p["hp"] - hp0
    p["location"] = "lodge" if where == "lodge" else "town"
    s = _build_scene(p)
    s.shard_note = ("You wake " + ("in your bunk" if where == "lodge"
                                   else "with dew on your cloak")
                    + (f" — +{healed} HP mended while you slept."
                       if healed else " — the bar banked what the clock "
                                      "earned."))
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
                               f"receive ◈ {max(0, gold - economy.BOARD_PRICE)}"))
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
            f"receive ◈ {total:,} to the bank"))
    # 022/005: the weekly strongbox. 0.29.1: below the level it is
    # SHOWN and locked — the clerk polishes a box you can't open yet.
    if p["level"] < economy.STRONGBOX_LEVEL:
        lines.append(f"the weekly strongbox — 🔒 level "
                     f"{economy.STRONGBOX_LEVEL}. Kills, keeps and "
                     "floors gained fill it; every week you pick one "
                     "reward from what you earned.")
    if p["level"] >= economy.STRONGBOX_LEVEL:
        box = weekly.sync(p)
        pts = weekly.points(p, box)
        n = weekly.slots(p)
        lines.append(f"strongbox — this week: {box['kills']} kills · "
                     f"{box['wardens']} keeps · "
                     f"{max(0, p['unlocked_floor'] - box['floor0'])} floors "
                     f"= {pts} points, {n} slot{'s' if n != 1 else ''} open "
                     f"(thresholds {'/'.join(map(str, economy.STRONGBOX_THRESHOLDS))}).")
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
                "Interest drips in through the day as stubs — collect "
                "them and it compounds.",
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
    if slug in economy.PACKS:
        # 064: an outgrown pack sells at its tier's price × rate
        pk = economy.PACKS[slug]
        return (pk.name, max(1, int(pk.price * rate)))
    it = economy.APOTHECARY[slug]
    return (it.name, max(1, int(it.price * rate)))


def _pawn_refused(p: dict) -> list[str]:
    """081: the pack pieces the broker won't buy — rusted basics and
    price-0 gate kit. Named out loud instead of silently skipped."""
    return [k for k in p["inventory"] if k in economy.FORGE
            and (k in economy.BASIC_WEAPONS
                 or economy.FORGE[k].price <= 0)]


def _pawn_waves_off(p: dict) -> str:
    names = [economy.FORGE[k].name for k in _pawn_refused(p)]
    if not names:
        return ""
    joined = (" and ".join(names) if len(names) <= 2
              else ", ".join(names[:-1]) + f" and {names[-1]}")
    return (f"The broker waves off the {joined} — gate steel and rusted "
            "basics are worth nothing to him, and never lost to you.")


def _pawn_scene(p: dict) -> Scene:
    rate = economy.pawn_rate(state.world_day())
    # 049: the broker won't take gate steel — the basics are worth
    # nothing to him and are never lost to the player.
    # 081: price-0 gate kit is off the offer list too (a ◈ 0 row read
    # as a glitch) — both walk into the waves-off line instead.
    gear_in_pack = [k for k in p["inventory"] if k in economy.FORGE
                    and k not in economy.BASIC_WEAPONS
                    and economy.FORGE[k].price > 0]
    relics_in_pack = [k for k in p["inventory"] if k in economy.RELICS]
    # 006 §3.8: the pawn always buys ANYTHING — so potions and tokens
    # get a row too (0.29.4: they used to be invisible here, which read
    # as the broker refusing).
    sundries = [k for k in p["inventory"]
                if k in economy.APOTHECARY or k == "repair_token"
                or k in economy.PACKS]
    opts = []
    lines = [f"The broker pays {round(rate * 100)}% today. Tomorrow is "
             "another mood."]
    waved = _pawn_waves_off(p)
    if waved:
        lines.append(waved)
    for slug in gear_in_pack:
        g = economy.FORGE[slug]
        offer = _pawn_offer(p, g)
        frac = _pawn_frac(p, g)
        worn = f", worn to {round(frac * 100)}%" if frac < 1.0 else ""
        opts.append(Option(f"sell_{slug}", f"Sell {g.name}",
                           f"receive ◈ {offer:,}"))
        lines.append(f"{g.name} ×{p['inventory'][slug]}{worn} — "
                     f"offers ◈ {offer:,}")
    for slug in relics_in_pack:
        r = economy.RELICS[slug]
        offer = _pawn_relic_offer(p, slug)
        opts.append(Option(f"sell_{slug}", f"Sell {r.name}",
                           f"receive ◈ {offer:,}"))
        lines.append(f"{r.name} ×{p['inventory'][slug]} — offers ◈ {offer:,}")
    for slug in sundries:
        name, offer = _pawn_sundry(p, slug)
        opts.append(Option(f"sell_{slug}", f"Sell {name}",
                           f"receive ◈ {offer:,}"))
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
                # 011: same card law as the chest's PUT wall — the row
                # says what the piece is before it says what it costs.
                left = (p.get("durability_pack") or {}).get(slug)
                opts.append(Option(
                    f"donate_{slug}",
                    f"Donate {g.name} to the armory",
                    f"{economy.gear_card_stats(g, left)} · "
                    "no coin — the faction keeps it"))
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
    if slug in p["inventory"] and slug in economy.FORGE \
            and slug not in economy.BASIC_WEAPONS \
            and economy.FORGE[slug].price > 0:
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
                                   or slug == "repair_token"
                                   or slug in economy.PACKS):
        name, offer = _pawn_sundry(p, slug)
        p["inventory"][slug] -= 1
        if p["inventory"][slug] <= 0:
            del p["inventory"][slug]
        p["gold"] += offer
        combat._ledger(p, "pawn", gold=offer, note=slug)
        s = _pawn_scene(p)
        s.body_lines.insert(0, f"+ ◈ {offer:,} for the {name}")
        return s
    # 081: a sell click for a piece the broker refuses no longer falls
    # through silently — the waves-off line says why nothing happened.
    if slug in _pawn_refused(p):
        s = _pawn_scene(p)
        s.shard_note = _pawn_waves_off(p)
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
        s.refusal = "Can't donate — the armory racks are full"
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
           f"{w['faction'].get('name', 'faction')} racks — the faction "
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
    beat = int(p.get("movie_beat", 0))
    if beat < 0:
        # 033: the fall reel's opening beat — the Warden of floor n−1
        # goes down under all three blades. The receipt rides the doc
        # (worldd lands the settled numbers on the doc the same turn the
        # kill resolves, so a mid-reel refresh keeps them).
        return _warden_slain_scene(p, n - 1)
    fl = schema.get_floor(n)
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


def _warden_slain_scene(p: dict, n: int) -> Scene:
    """033: the fall reel, beat one — the Warden of floor n dies on
    screen, brought down the only way great Wardens die: blade in
    close, an arrow's line from the treeline, sorcerer's light behind.
    The kill receipt (033 item 2) is the text of this beat."""
    from . import combat
    fl = schema.get_floor(n)
    r = p.get("kill_receipt") or {}
    body = combat.kill_receipt_lines(r)
    body.append(f"FLOOR {n + 1} stands open.")
    names = r.get("names", "")
    tally = []
    if r.get("gold") or r.get("xp"):
        tally = [{"kind": "gold", "n": int(r.get("gold", 0))},
                 {"kind": "aether", "n": int(r.get("xp", 0))}]
    return Scene(
        eyebrow=f"FLOOR {n} · THE KEEP · THE FALL",
        headline=f"{fl.warden_name} falls",
        support=(f"Struck down by {names}." if names else
                 "The Warden's frame ticks as it cools. The whole "
                 "tower heard that."),
        body_lines=body,
        options=[Option("next", "Next"),
                 Option("skip", "Skip")],
        # warden_slain art was never generated (plan 033); until it is,
        # the fall reel that ships carries the beat
        fx="warden_fall",
        banner=f"warden_{n:03d}",
        tally=tally,
    )


def floor_movie_scene(p: dict) -> Scene:
    """The current movie beat — combat routes the Warden kill here so
    the victory card IS the fall reel's first frame (033)."""
    return _floor_movie_scene(p)


def _floor_movie_advance(p: dict, oid: str = "next") -> Scene:
    """Next steps a beat; Skip (on every beat) cuts straight to the
    arrival card. Either way the floor counts as seen — the movie
    plays once, skipped or watched. 033: entered from a Warden kill
    (movie_teaser) the reel opens on the slain beat, the floor beats
    only exist where the content does, and the exit is the floor the
    player is standing on, not an arrival card for one they may not
    yet be allowed to enter."""
    n = int(p["movie_floor"])
    beat = int(p.get("movie_beat", 0))
    last = 1 if n <= schema.max_content_floor() else -1
    if oid != "skip" and beat < last:
        p["movie_beat"] = beat + 1
        return _floor_movie_scene(p)
    if n <= schema.max_content_floor():
        p["flags"][f"floor_seen_{n}"] = True
    teaser = bool(p.pop("movie_teaser", None))
    p.pop("movie_floor", None)
    p.pop("movie_beat", None)
    p.pop("kill_receipt", None)
    if teaser:
        return _build_scene(p)
    return _floor_arrival_scene(p, n)


def _gate_pick(p: dict, oid: str) -> Scene:
    if not oid.startswith("floor_"):
        return _gate_scene(p)
    n = int(oid.removeprefix("floor_"))
    if n > p["unlocked_floor"] or n > schema.max_content_floor():
        s = _gate_scene(p)
        s.shard_note = f"Floor {n} is still sealed. A Warden holds every lift."
        s.refusal = f"Can't ride up — floor {n} is still sealed"
        return s
    req = economy.floor_entry_player_level(n)
    if p["level"] < req:
        s = _gate_scene(p)
        s.shard_note = (f"The lift is open, but floor {n} wants level {req} "
                        f"legs — you are level {p['level']}. Climb closer "
                        "to your weight first.")
        s.refusal = (f"Can't ride up — floor {n} requires level {req} "
                     f"— you are level {p['level']}")
        return s
    # 076: the true origin — the camp's gate shortcut zeroes p["floor"]
    # on the way into the lobby, so it stashes gate_from first.
    old_floor = int(p.pop("gate_from", p.get("floor") or 0) or 0)
    p["floor"] = n
    p["location"] = "gate_town"
    # 056: faction grain — the world feed doesn't care which lift you
    # rode; your banner does.
    if p.get("_world") is not None and p.get("guild"):
        from . import social
        social._effect(p, "happening", scope="faction",
                       line=f"{p.get('name') or 'A climber'} steps onto "
                            f"floor {n}",
                       floor=n)
    # 030 Phase 8: the first time a character sets foot on a floor —
    # old name or new — the floor introduces itself: a short movie,
    # once per floor, skippable on every beat.
    # 076: the arrival card carries the ride's direction — the pane plays
    # the matching lift animation over it. Same-floor picks stay silent.
    lift = "up" if n > old_floor else ("down" if n < old_floor else "")
    if not p["flags"].get(f"floor_seen_{n}"):
        p["movie_floor"], p["movie_beat"] = n, 0
        s = _floor_movie_scene(p)
        s.lift = lift
        return s
    s = _floor_arrival_scene(p, n)
    s.lift = lift
    return s


def _floor_arrival_scene(p: dict, n: int) -> Scene:
    fl = schema.get_floor(n)
    lines = [fl.arrival]
    # 048 retro: the stat roster is gone — the fight card and the
    # mechanics page carry the numbers; the camp stays prose.
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
        option_art=_gate_town_art(fl),
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


def _gate_town_art(fl) -> dict:
    """031 §13: the hunting grounds and the Warden wear their pictures
    on the choice ITSELF — the hunt row carries the floor's fields, the
    keep row its warden. Rides beside options on the wire (option_art);
    old clients drop the unknown top-level key and lose only decoration."""
    return {"hunt": fl.banner, "hunt_deep": fl.banner,
            "keep": f"warden_{fl.floor:03d}"}


def _gate_town_options(p: dict, fl) -> list[Option]:
    # 065: the wound bill — priced for THIS wound, on the row
    heal_price = economy.healer_tent_price(fl.floor, p["hp"],
                                           state.max_hp(p))
    opts = [Option("hunt", "Hunt the wilds", "1 ⚡")]
    # 039 §2: from floor 4 the wilds have a dangerous end — an informed
    # opt-in, priced on the row before the click.
    if fl.floor >= economy.DEEP_HUNT_MIN_FLOOR:
        opts.append(Option("hunt_deep", "Hunt deep — off the lit paths",
                           f"{economy.COST_WILDS_DEEP} ⚡ · harder, richer"))
    if _live_flare(p):
        opts.insert(0, Option("answer_flare", "Answer the flare",
                              "1 ⚡ · run toward the light"))
    if p["hp"] < state.max_hp(p):
        opts.append(Option("stew", "Hunter's stew",
                           f"pay ◈ {economy.STEW_PRICE} · "
                           f"+{economy.STEW_HEAL_HP} HP"))
        opts.append(Option("heal", "The healer's tent",
                           f"pay ◈ {heal_price} · "
                           f"+{state.max_hp(p) - p['hp']} HP"))
        # 014: the pack heals finally have a mouth — usable at the camp
        # fire (the tonic stays the only MID-fight heal, per 013).
        for slug in ("medgel", "trauma_kit"):
            have = p["inventory"].get(slug, 0)
            if have:
                item = economy.APOTHECARY[slug]
                amount = int(item.effect.rsplit("_", 1)[1])
                opts.append(Option(f"use_{slug}", f"Use a {item.name}",
                                   f"+{amount} HP · {have} left"))
    # 031 §5: the walk to the keep is free — the swing is the price.
    # 034 §3: unless the Warden is dead, and then there is no price at
    # all — the row says monument, not swing, before the click.
    if _warden_has_fallen(p, fl):
        opts.append(Option("keep", f"The keep where {fl.warden_name} fell",
                           "a monument · free"))
    else:
        opts.append(Option("keep", f"The Warden's keep — {fl.warden_name}",
                           f"{economy.COST_WARDEN_STRIKE} ⚡ a swing"))
    # 030 Phase 6: the floor's one voice — floors without an npc block
    # (11-100, until their art pass) simply have no talk row.
    npc = getattr(fl, "npc", None)
    if npc is not None:
        opts.append(Option("talk", f"Talk — {npc.name}", npc.role))
    # 048 retro: the camp lift runs straight to the Tower Gate — change
    # floors without the walk home (the School moved to the square).
    opts.append(Option("gate", "The Tower Gate",
                       "change floors from here"))
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
        option_art=_gate_town_art(fl),
        meters=combat.meters(p),
        banner=fl.banner,
    )


# ── The School (048: train, mastery, carry — on Roothollow's square) ─

_PATH_GLYPH = {"blade": "⚔", "bow": "➶", "staff": "✦"}
_PATH_ORDER = ("blade", "bow", "staff")


def _school_bar(rank: int) -> str:
    return "▰" * rank + "▱" * (10 - rank)


def _school_discounted(p: dict, path: str) -> bool:
    """A master pays 80% on the OTHER paths' ranks 1-5."""
    m = p.get("mastery") or {}
    return any(m.get(k) for k in _PATH_ORDER if k != path)


def _school_scene(p: dict) -> Scene:
    front = max(1, p["unlocked_floor"])
    training = p.get("training") or {}
    mastery = p.get("mastery") or {}
    lines, opts = [], []
    for path in _PATH_ORDER:
        r = int(training.get(path, 0))
        g = _PATH_GLYPH[path]
        if r >= 10:
            # the bar turns gold — rank 10 is a public achievement
            lines.append(f"{g} {path.upper()} — trained rank 10 "
                         f"{_school_bar(10)} · GOLD")
            if mastery.get(path):
                lines.append("   MASTERY — studied. The hand hits "
                             "10% harder — everything, always.")
            else:
                lines.append(f"   MASTERY — the master offers the "
                             f"{path} study: {economy.MASTERY_XP} XP")
                opts.append(Option(f"mastery_{path}",
                                   f"Study {path} mastery",
                                   f"{economy.MASTERY_XP} XP"))
            continue
        nxt = r + 1
        xp = economy.train_xp_cost(nxt, _school_discounted(p, path))
        gold = economy.train_gold(nxt, front)
        lines.append(f"{g} {path.upper()} — trained rank {r} "
                     f"{_school_bar(r)} · next: rank {nxt} — "
                     f"{xp} XP + ◈ {gold}")
        m0, m1 = economy.TRAIN_MISS_PCT(r), economy.TRAIN_MISS_PCT(nxt)
        f0 = round(economy.TRAIN_ROLL_FLOOR(r) * 100)
        f1 = round(economy.TRAIN_ROLL_FLOOR(nxt) * 100)
        lines.append(f"   rank {nxt}: miss {m0}%→{m1}%, worst swing "
                     f"{f0}%→{f1}% of full power")
        opts.append(Option(f"train_{path}",
                           f"Train {path} to rank {nxt}",
                           f"{xp} XP + ◈ {gold}"))
    slots = int(p.get("slots", 1))
    carry = (f"✥ CARRY — {slots} weapon "
             f"slot{'s' if slots != 1 else ''}")
    if slots == 1:
        carry += (f" · 2nd slot — {economy.CARRY2_XP} XP + "
                  f"◈ {economy.CARRY2_GOLD}")
        opts.append(Option("buy_carry2",
                           "Unlock the 2nd weapon slot",
                           f"{economy.CARRY2_XP} XP + "
                           f"◈ {economy.CARRY2_GOLD}"))
    elif slots == 2:
        # 049.2: the row is always on the menu — owned slots are named
        # in the CARRY line, and below level 8 the 3rd shows LOCKED
        # with the level on it (a bare "needs level" hint next to a
        # buyable-looking row read as a bug).
        gold3 = economy.carry3_gold(front)
        level = int(p.get("level", 1))
        if level < economy.CARRY3_LEVEL:
            carry += (f" · 3rd slot locked — opens at level "
                      f"{economy.CARRY3_LEVEL}")
            opts.append(Option("buy_carry3",
                               "Unlock the 3rd weapon slot",
                               f"locked — level {economy.CARRY3_LEVEL} "
                               f"(you: {level})", locked=True))
        else:
            carry += (f" · 3rd slot — {economy.CARRY3_XP} XP + "
                      f"◈ {gold3}")
            opts.append(Option("buy_carry3",
                               "Unlock the 3rd weapon slot",
                               f"{economy.CARRY3_XP} XP + ◈ {gold3}"))
    lines.append(carry)
    # 069: the charm pouch — the seventh slot. Always on the menu:
    # owned → named in the line; under level 9 → LOCKED with the level.
    level = int(p.get("level", 1))
    if p.get("charm_slot"):
        lines.append("◇ POUCH — one charm or potion rides at your belt")
    else:
        goldc = economy.charm_slot_gold(front)
        if level < economy.CHARM_SLOT_LEVEL:
            lines.append(f"◇ POUCH locked — opens at level "
                         f"{economy.CHARM_SLOT_LEVEL}")
            opts.append(Option("buy_charm_slot", "Unlock the charm pouch",
                               f"locked — level {economy.CHARM_SLOT_LEVEL} "
                               f"(you: {level})", locked=True))
        else:
            lines.append(f"◇ POUCH — {economy.CHARM_SLOT_XP} XP + "
                         f"◈ {goldc} · one charm or potion at your belt")
            opts.append(Option("buy_charm_slot", "Unlock the charm pouch",
                               f"{economy.CHARM_SLOT_XP} XP + ◈ {goldc}"))
    opts.append(Option("back", "Back to the square"))
    return Scene(
        eyebrow="ROOTHOLLOW · THE SCHOOL",
        headline="The School",
        banner="school",
        support="Any hand can hold any weapon. The School teaches it "
                "to bite. Training spends the XP bar — the same pool "
                "the Guildhall levels from.",
        body_lines=lines,
        options=opts,
        meters=combat.meters(p),
    )


def _school_action(p: dict, oid: str) -> Scene:
    if oid == "back":
        p["location"] = "town"
        return _town_scene(p)
    if oid.startswith("train_"):
        path = oid.removeprefix("train_")
        if path in _PATH_GLYPH:
            return _school_train(p, path)
    if oid.startswith("mastery_"):
        path = oid.removeprefix("mastery_")
        if path in _PATH_GLYPH:
            return _school_mastery(p, path)
    if oid in ("buy_carry2", "buy_carry3"):
        return _school_carry(p, oid)
    if oid == "buy_charm_slot":
        return _school_charm(p)
    return _school_scene(p)


def _school_charm(p: dict) -> Scene:
    """069: the charm pouch — bought once, level 9 and up."""
    if p.get("charm_slot"):
        return _school_refuse(p, "The pouch already hangs at your belt.")
    level = int(p.get("level", 1))
    if level < economy.CHARM_SLOT_LEVEL:
        return _school_refuse(
            p, f"The pouch opens at level {economy.CHARM_SLOT_LEVEL} — "
               f"you're level {level}.")
    xp = economy.CHARM_SLOT_XP
    gold = economy.charm_slot_gold(max(1, p["unlocked_floor"]))
    if p["xp"] < xp:
        return _school_refuse(
            p, f"The pouch wants {xp} XP — your bar holds {p['xp']}.")
    if p["gold"] < gold:
        return _school_refuse(
            p, f"The pouch's fee is ◈ {gold} — you carry "
               f"◈ {p['gold']:,}.")
    p["xp"] -= xp
    p["gold"] -= gold
    p["charm_slot"] = True
    combat._ledger(p, "train", gold=-gold, xp=-xp, note="charm pouch")
    s = _school_scene(p)
    s.body_lines.insert(
        0, "+ POUCH — one charm or potion rides at your belt now. Set "
           "it from the pack; only what sits there acts in a fight.")
    return s


def _school_refuse(p: dict, why: str) -> Scene:
    s = _school_scene(p)
    s.shard_note = why
    # 050: the school's refusals are already one short line — the toast
    # speaks the same words the card would.
    s.refusal = why
    return s


def _school_train(p: dict, path: str) -> Scene:
    r = int(p["training"].get(path, 0))
    if r >= 10:
        return _school_refuse(
            p, f"Rank 10 — the School has nothing left to teach "
               f"your {path}. The master, though, might.")
    nxt = r + 1
    xp = economy.train_xp_cost(nxt, _school_discounted(p, path))
    gold = economy.train_gold(nxt, max(1, p["unlocked_floor"]))
    if p["xp"] < xp:
        return _school_refuse(
            p, f"Rank {nxt} {path} wants {xp} XP — your bar holds "
               f"{p['xp']}. Kills fill it.")
    if p["gold"] < gold:
        return _school_refuse(
            p, f"The instructor's fee is ◈ {gold} — you carry "
               f"◈ {p['gold']:,}.")
    p["xp"] -= xp
    p["gold"] -= gold
    p["training"][path] = nxt
    combat._ledger(p, "train", gold=-gold, xp=-xp, note=f"{path} {nxt}")
    if nxt == 10 and not p["flags"].get(f"invited_{path}"):
        # rank 10 — the invitation card, once, ever
        p["flags"][f"invited_{path}"] = True
        p.setdefault("pending_events", []).insert(0, Scene(
            eyebrow="THE SCHOOL · AN INVITATION",
            headline=f"The {path} master will see you now",
            support="Rank 10 — the drills end where the studies "
                    "begin.",
            body_lines=[
                f"▪ {path} mastery — a study of "
                f"{economy.MASTERY_XP} XP, at any School",
                "▪ a master's hand hits 10% harder — everything, "
                "always",
                "▪ a master pays 80% on the other paths' first "
                "five ranks",
                "▪ a tenth rank is toasted in every faction hall — "
                "the tower knows its masters by name",
            ],
            options=[Option("town", "So be it")],
            event_kind="present",
        ).to_dict())
    s = _school_scene(p)
    s.body_lines.insert(
        0, f"+ {path} — trained rank {nxt}. The drills stick.")
    return s


def _school_mastery(p: dict, path: str) -> Scene:
    if int(p["training"].get(path, 0)) < 10:
        return _school_refuse(
            p, "The studies open at rank 10 — train first.")
    if (p.get("mastery") or {}).get(path):
        return _school_refuse(
            p, "Already studied — the master has no second lesson.")
    if p["xp"] < economy.MASTERY_XP:
        return _school_refuse(
            p, f"The study wants {economy.MASTERY_XP} XP — your bar "
               f"holds {p['xp']}.")
    p["xp"] -= economy.MASTERY_XP
    p.setdefault("mastery", {})[path] = True
    combat._ledger(p, "train", xp=-economy.MASTERY_XP,
                   note=f"mastery {path}")
    s = _school_scene(p)
    s.body_lines.insert(
        0, f"+ {path} MASTERY — the study is yours. Your hand hits "
           "10% harder now — everything, always.")
    return s


def _school_carry(p: dict, oid: str) -> Scene:
    slots = int(p.get("slots", 1))
    if oid == "buy_carry2":
        if slots != 1:
            return _school_refuse(p, "Your hands already know the "
                                     "second grip.")
        xp, gold = economy.CARRY2_XP, economy.CARRY2_GOLD
    else:
        if slots >= 3:
            return _school_refuse(p, "Three is all the hands you have.")
        if slots < 2:
            return _school_refuse(p, "The second grip comes first.")
        if int(p.get("level", 1)) < economy.CARRY3_LEVEL:
            return _school_refuse(
                p, f"The third grip opens at level "
                   f"{economy.CARRY3_LEVEL} — you're level "
                   f"{int(p.get('level', 1))}.")
        xp, gold = economy.CARRY3_XP, economy.carry3_gold(
            max(1, p["unlocked_floor"]))
    if p["xp"] < xp:
        return _school_refuse(
            p, f"The grip wants {xp} XP — your bar holds "
               f"{p['xp']}.")
    if p["gold"] < gold:
        return _school_refuse(
            p, f"The grip's fee is ◈ {gold} — you carry "
               f"◈ {p['gold']:,}.")
    p["xp"] -= xp
    p["gold"] -= gold
    p["slots"] = slots + 1
    combat._ledger(p, "train", gold=-gold, xp=-xp,
                   note=f"carry {slots + 1}")
    s = _school_scene(p)
    s.body_lines.insert(
        0, f"+ CARRY — {slots + 1} weapon slots now. The weight "
           "settles across your back.")
    return s


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
        option_art=_gate_town_art(fl),
        meters=combat.meters(p),
    )


def _gate_town_action(p: dict, oid: str) -> Scene:
    fl = schema.get_floor(max(1, p["floor"]))
    if oid == "talk" and getattr(fl, "npc", None) is not None:
        return _npc_scene(p, fl)
    if oid == "gate":
        # 048 retro: the lift to the Gate runs from every camp — pick
        # the next floor without walking the square first.
        # 076: the gate lobby zeroes p["floor"], so the ride's true
        # origin is stashed here and consumed by _gate_pick.
        p["gate_from"] = int(p.get("floor") or 0)
        p["location"] = "gate"
        p["floor"] = 0
        return _gate_scene(p)
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
            s.refusal = "Can't answer the flare — not enough energy"
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
            s.refusal = "Can't hunt — not enough energy"
            return s
        # 025 §5: the rubber band weights the roster against your sheet
        enc_id = state.rng_pick(p, combat.hunt_table(p, fl))
        enc = next(e for e in fl.encounters if e.id == enc_id)
        combat._ledger(p, "energy", note="wilds")
        return combat.start_encounter(p, fl, enc, "wilds")
    if oid == "hunt_deep":
        # 039 §2: the deep hunt — ⚡2, floor 4+, no prey, no rubber band
        if fl.floor < economy.DEEP_HUNT_MIN_FLOOR:
            return _gate_town_scene(p)
        if not state.spend_energy(p, economy.COST_WILDS_DEEP):
            s = _gate_town_scene(p)
            s.shard_note = (f"The deep wants ⚡ {economy.COST_WILDS_DEEP} "
                            "in hand — you're short. One point returns "
                            "every 45 minutes.")
            s.refusal = (f"Can't hunt the deep — not enough energy "
                         f"(⚡ {economy.COST_WILDS_DEEP} needed)")
            return s
        enc_id = state.rng_pick(p, combat.hunt_table(p, fl, deep=True))
        enc = next(e for e in fl.encounters if e.id == enc_id)
        combat._ledger(p, "energy", note="wilds deep")
        return combat.start_encounter(p, fl, enc, "wilds", deep=True)
    if oid == "heal":
        price = economy.healer_tent_price(fl.floor, p["hp"],
                                          state.max_hp(p))
        if p["gold"] < price:
            s = _gate_town_scene(p)
            s.shard_note = f"The healer wants ◈ {price} you don't carry."
            s.refusal = f"Can't heal — not enough gold (◈ {price} needed)"
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
        # 034 §3: a Warden dies once. Its keep is a memorial afterwards —
        # checked BEFORE the milestone branch, or a cleared floor 10 goes
        # on showing a war-party quorum board forever.
        if _warden_has_fallen(p, fl):
            p["location"] = "memorial"
            return _memorial_scene(p)
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
        # 031 §5: walking into a keep is free — every swing inside
        # costs 3 ⚡, and that is the whole price.
        return combat.start_encounter(p, fl, None, "warden")
    if oid == "gate":
        p["location"] = "gate"
        return _gate_scene(p)
    return _gate_town_scene(p)
