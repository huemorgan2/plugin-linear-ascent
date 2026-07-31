"""Social scenes — the shared-world layer (relay, fields/PvP, grants,
guildhall, boss quorums).

Only active when the host injected `doc["_world"]` (worldd does; local
solo mode has no social surface). Cross-player writes never happen here:
the engine validates and pays costs, then emits `doc["_effects"]` for the
host to execute in the same transaction.
"""

from __future__ import annotations

import datetime as dt

from .. import economy
from . import state
from .combat import _ledger, meters
from .scene import Option, Scene


def world(p: dict) -> dict | None:
    return p.get("_world")


def _effect(p: dict, kind: str, **kw) -> None:
    p.setdefault("_effects", []).append({"kind": kind, **kw})


# ── Relay Office (letters) ───────────────────────────────────────────────

def relay_scene(p: dict, note: str = "") -> Scene:
    w = world(p) or {}
    letters = w.get("letters", [])
    lines = []
    if note:
        lines.append(note)
    if letters:
        seen = [l["id"] for l in letters if not l.get("gold") and "id" in l]
        if seen:
            _effect(p, "letters_seen", ids=seen)
        for l in letters[:8]:
            gold = f" [◈ {l['gold']:,} enclosed]" if l.get("gold") else ""
            lines.append(f"from {l['from_name']}{gold} — {l['body'][:80]}")
    else:
        lines.append("No letters. The clerk shrugs like it's your fault.")
    opts = []
    if any(l.get("gold") for l in letters):
        opts.append(Option("collect", "Collect the enclosed gold"))
    price_note = (f"◈ {economy.LETTER_PRICE}" if economy.LETTER_PRICE
                  else "free")
    targets = w.get("names", [])[:6]
    for t in targets:
        if t != p.get("name"):
            opts.append(Option(f"write_{t}", f"Write to {t}", price_note))
    opts.append(Option("town", "Back to the square"))
    return Scene(
        eyebrow="ROOTHOLLOW · THE RELAY OFFICE",
        headline=f"{len(letters)} letter{'s' if len(letters) != 1 else ''} "
                 "hold for you",
        support="Paper moves between floors faster than people do.",
        body_lines=lines,
        options=opts,
        meters=meters(p),
        event_kind="letter" if letters else "",
        banner="relay",
    )


def relay_action(p: dict, oid: str) -> Scene:
    if oid == "collect":
        _effect(p, "collect_letter_gold")
        return relay_scene(p, note="+ the clerk counts it out twice")
    if oid.startswith("write_"):
        target = oid.removeprefix("write_")
        if p["gold"] < economy.LETTER_PRICE:
            return relay_scene(
                p, note=f"A letter costs ◈ {economy.LETTER_PRICE} — "
                        "you're short.")
        p["compose_to"] = target
        return Scene(
            eyebrow="ROOTHOLLOW · THE RELAY OFFICE",
            headline=f"A letter to {target}",
            support="The clerk writes down what you say.",
            shard_note="Keep it under a hundred words. The clerk charges "
                       "attitude by the page.",
            options=[],
            meters=meters(p),
            awaits_text=f"the letter's words for {target}",
            ask={"kind": "text", "max": 200,
                 "label": f"the letter to {target}",
                 "placeholder": "what should it say?", "submit": "SEND"},
        )
    return relay_scene(p)


def relay_compose(p: dict, text: str) -> Scene:
    target = p.pop("compose_to", "")
    body = text.strip()[:400]
    if not target or not body:
        return relay_scene(p, note="The clerk waits, pen up. Nothing came.")
    p["gold"] -= economy.LETTER_PRICE
    _ledger(p, "letter", gold=-economy.LETTER_PRICE, note=f"to {target}")
    _effect(p, "send_letter", to_name=target, body=body)
    return relay_scene(p, note=f"+ sealed and slotted for {target}")


# ── The fields (PvP) ─────────────────────────────────────────────────────

def fields_scene(p: dict, note: str = "") -> Scene:
    w = world(p) or {}
    targets = w.get("pvp_targets", [])
    used = p["daily"].get("pvp_used", 0)
    lines = [note] if note else []
    opts = []
    if used >= economy.PVP_ATTACKS_PER_DAY:
        lines.append("You've made enough enemies for one day.")
    else:
        for t in targets[:6]:
            opts.append(Option(
                f"attack_{t['name']}",
                f"Attack {t['name']}",
                f"L{t['level']} · 3 ⚡"))
    if not targets:
        lines.append("Every bunk in the Lodge is paid tonight. "
                     "The fields are empty.")
    opts.append(Option("town", "Back to the square"))
    return Scene(
        eyebrow="ROOTHOLLOW · THE FIELDS",
        headline="Who sleeps rough tonight?",
        support="Skip the Lodge and this is where the world finds you.",
        body_lines=lines,
        options=opts,
        meters=meters(p),
    )


def fields_action(p: dict, oid: str) -> Scene:
    if not oid.startswith("attack_"):
        return fields_scene(p)
    target = oid.removeprefix("attack_")
    if p["daily"].get("pvp_used", 0) >= economy.PVP_ATTACKS_PER_DAY:
        return fields_scene(p, note="Two ambushes a day is the custom. "
                                    "Even bandits have one.")
    if not state.spend_energy(p, economy.COST_PVP_ATTACK):
        return fields_scene(p, note="An ambush takes 3 ⚡ you don't have.")
    p["daily"]["pvp_used"] = p["daily"].get("pvp_used", 0) + 1
    _effect(p, "pvp_attack", target_name=target)
    # the host resolves and replaces this scene via doc["_pvp_result"]
    return fields_scene(p, note=f"You slip out toward {target}'s camp…")


# ── Vault grants ─────────────────────────────────────────────────────────

def _grant_amount_scene(p: dict) -> Scene:
    amounts = [a for a in (100, 500, p["gold"] // 2) if 0 < a <= p["gold"]]
    opts = [Option(f"grantamt_{a}", f"◈ {a:,}",
                   f"burn ◈ {int(a * economy.GRANT_BURN_PCT):,}")
            for a in sorted(set(amounts))]
    opts.append(Option("grants", "Back"))
    return Scene(
        eyebrow="ROOTHOLLOW · THE VAULT · GRANTS DESK",
        headline=f"How much for {p['grant_to']}?",
        options=opts,
        meters=meters(p),
    )


def grant_scene(p: dict, note: str = "") -> Scene:
    if p.get("grant_to"):
        return _grant_amount_scene(p)
    w = world(p) or {}
    targets = [n for n in w.get("grant_targets", []) if n != p.get("name")]
    lines = [note] if note else []
    cap = economy.GRANT_DAILY_CAP_PER_LEVEL * p["level"]
    sent = p["daily"].get("granted", 0)
    lines.append(f"Daily grant cap ◈ {cap:,} — used ◈ {sent:,}. "
                 f"The Vault burns {int(economy.GRANT_BURN_PCT * 100)}% "
                 "of every transfer.")
    opts = []
    for t in targets[:6]:
        opts.append(Option(f"grantto_{t}", f"Grant to {t}"))
    opts.append(Option("vault", "Back to the Vault"))
    return Scene(
        eyebrow="ROOTHOLLOW · THE VAULT · GRANTS DESK",
        headline="Move money, lose a tithe",
        support=f"Receivers must be level "
                f"{economy.GRANT_MIN_RECEIVER_LEVEL}+ — the Vault "
                "doesn't fund cradles.",
        body_lines=lines,
        options=opts,
        meters=meters(p),
    )


def grant_action(p: dict, oid: str) -> Scene:
    if oid == "grants":
        p.pop("grant_to", None)
        return grant_scene(p)
    if oid.startswith("grantto_"):
        p["grant_to"] = oid.removeprefix("grantto_")
        return _grant_amount_scene(p)
    if oid.startswith("grantamt_"):
        amt = int(oid.removeprefix("grantamt_"))
        target = p.pop("grant_to", "")
        cap = economy.GRANT_DAILY_CAP_PER_LEVEL * p["level"]
        if not target:
            return grant_scene(p)
        if amt > p["gold"]:
            return grant_scene(p, note="You don't carry that much.")
        if p["daily"].get("granted", 0) + amt > cap:
            return grant_scene(p, note="That would breach today's cap.")
        p["gold"] -= amt
        p["daily"]["granted"] = p["daily"].get("granted", 0) + amt
        net = amt - int(amt * economy.GRANT_BURN_PCT)
        _ledger(p, "grant_out", gold=-amt, note=f"to {target}")
        _effect(p, "grant", to_name=target, net=net, gross=amt)
        return grant_scene(p, note=f"+ ◈ {net:,} moves to {target} "
                                   f"(◈ {amt - net:,} burned)")
    return grant_scene(p)


# ── Guildhall ────────────────────────────────────────────────────────────
# 010: faction LIFE happens here — join/found a banner, the store, dues,
# the week's world challenge, donations, kicks. The COMMUNITY pane tab is
# a read-only news board. worldd injects w["faction"] (member panel) or
# w["factions"] (the hall list); local dev mode keeps the legacy
# doc-string guilds with none of the purse mechanics.

GUILD_FOUND_FEE = 300      # 019: mirrored by worldd factions.FOUND_FEE
FOUND_MIN_LEVEL = 4        # 015: founding is a rank privilege
JOIN_FEE_MAX = 500
DUES_MIN, DUES_MAX = 1, 50


def _take_gold(p: dict, amount: int) -> bool:
    """Charge carried gold first, then the bank."""
    gold, bank = int(p.get("gold", 0)), int(p.get("bank", 0))
    if gold + bank < amount:
        return False
    take = min(gold, amount)
    p["gold"] = gold - take
    p["bank"] = bank - (amount - take)
    return True


def _pips(days: int, required: int) -> str:
    d = max(0, min(7, int(days)))
    return "▪" * d + "▫" * (7 - d) + f" {d}/{required}"


def guildhall_scene(p: dict, note: str = "") -> Scene:
    st = p.get("founding_guild")
    if isinstance(st, dict):
        return _founding_scene(p, st, note)
    if p.get("faction_donating"):
        return _donate_prompt(p, note)
    if p.get("faction_kicking"):
        return _kick_prompt(p, note)
    w = world(p) or {}
    fac = w.get("faction")
    # 020: a note may carry several announcement lines (level-up card)
    lines = note.split("\n") if note else []
    opts = []
    # 012: training — levels are bought here, never granted in the field.
    # 022/002: the drill ends at the cap; from there gear and the war
    # carry the climb, and ✦ is pure currency.
    if p["level"] >= economy.LEVEL_CAP:
        if not note:
            lines.append(f"LEVEL {economy.LEVEL_CAP} — the drillmaster "
                         "has nothing left to teach you. From here the "
                         "steel, the honing bench and the war carry you; "
                         "your ✦ buys spells, scans and edges now.")
    else:
        fee = economy.levelup_gold(p["level"])
        need = economy.xp_need(p["level"])
        opts.append(Option("guild_train", f"Train to LEVEL {p['level'] + 1}",
                           f"◈ {fee:,}"))
        if p["xp"] < need and not note:
            lines.append(f"The drillmaster sizes you up: XP "
                         f"{p['xp']:,}/{need:,}. Come back with a full "
                         f"bar — the fee is ◈ {fee:,}.")
    gallery: list[dict] = []
    # 027: your own colors hang over your own table — the generic hall art
    # only shows when you have no banner of your own.
    banner = "guildhall"
    if fac:
        _member_panel(p, fac, lines, opts)
        headline = f"The {fac['name']} table"
        if fac.get("banner"):
            banner = str(fac["banner"])
    elif w.get("factions") is not None:
        gallery = _hall_list(p, w["factions"], lines, opts)
        headline = "Banners for hire"
    else:
        # local dev mode — legacy doc-string guilds, no purse
        mine = p.get("guild")
        headline = f"The {mine} table" if mine else "Banners for hire"
        if mine:
            roster = w.get("guild_roster", [])
            lines.append(f"Your banner: {mine} — "
                         + (", ".join(roster[:8]) if roster else "just you"))
            opts.append(Option("guild_leave", "Leave the guild"))
        else:
            for g in w.get("guilds", [])[:6]:
                opts.append(Option(f"join_{g}", f"Join {g}"))
            # 019: the founding door is always a row, locked below rank
            if p["level"] < FOUND_MIN_LEVEL:
                opts.append(Option("found_guild", "Found a guild",
                                   f"🔒 level {FOUND_MIN_LEVEL} · "
                                   f"◈ {GUILD_FOUND_FEE}", locked=True))
            else:
                opts.append(Option("found_guild", "Found a guild",
                                   f"◈ {GUILD_FOUND_FEE}"))
    opts.append(Option("town", "Back to the square"))
    return Scene(
        eyebrow="ROOTHOLLOW · THE GUILDHALL",
        headline=headline,
        support="Milestone Wardens fall to war parties, not heroes.",
        body_lines=lines,
        options=opts,
        meters=meters(p),
        banner=banner,
        gallery=gallery,
    )


def _member_panel(p: dict, fac: dict, lines: list, opts: list) -> None:
    wk = fac.get("week") or {}
    kind = str(wk.get("kind", "hoard")).upper()
    lines.append(f"STORE ◈ {fac.get('store', 0):,} · dues "
                 f"◈ {fac.get('dues', 0)}/week · join ◈ "
                 f"{fac.get('join_fee', 0)}")
    if wk.get("entered"):
        lines.append(f"this week's {kind}: {wk.get('progress', 0):,}"
                     f"/{wk.get('target', 0):,} — entered, on pace for "
                     f"×{wk.get('multiplier', 0):.2f} of the prize")
    else:
        lines.append(f"this week the Ascent demands a {kind} — target "
                     f"{wk.get('target', 0):,} · entry "
                     f"◈ {wk.get('entry_cost', 0)} from the store")
    for m in fac.get("members", [])[:8]:
        tag = ""
        if m.get("founder"):
            tag = " · ★ founder"
        elif m.get("role") == "steward":
            tag = " · admin"
        arr = " ▲ arrears" if m.get("arrears") else ""
        lines.append(f"{m.get('name', '?')}{tag} — "
                     f"{_pips(m.get('days', 0), m.get('required', 4))}"
                     f"{arr}")
    if fac.get("last_week"):
        lines.append(f"last week: {fac['last_week']}")
    # 007: the armory — the banner's shared rack. Donations go in at
    # the pawn shop; here a member takes ONE piece a day, wear intact.
    w = world(p) or {}
    rack = w.get("armory")
    if rack is not None:
        cap = int(w.get("armory_cap", 50))
        lines.append(f"ARMORY {len(rack)}/{cap} — donate at the pawn "
                     "shop; one take a day")
        took = bool(w.get("armory_took_today"))
        for it in rack[:6]:
            worn = (f", worn to {round(it.get('frac', 1.0) * 100)}%"
                    if it.get("frac", 1.0) < 1.0 else "")
            lines.append(f"  {it['name']}{worn} — from {it['donor']}")
            if not took:
                opts.append(Option(f"take_arm_{it['id']}",
                                   f"Take the {it['name']}",
                                   "the racks open again tomorrow"))
        if len(rack) > 6:
            lines.append(f"  …and {len(rack) - 6} more on the racks")
        if rack and took:
            lines.append("  you already took your piece today")
    if fac.get("role") == "steward" and fac.get("pending_requests"):
        n = int(fac["pending_requests"])
        lines.append(f"▲ {n} request{'s' if n != 1 else ''} wait at the "
                     "desk — the Community pane holds the ledger")
    opts.append(Option("donate", "Donate to the store", "carried ◈"))
    if fac.get("role") == "steward":
        if not wk.get("entered"):
            opts.append(Option("enter_week",
                               f"Enter the week's {kind}",
                               f"◈ {wk.get('entry_cost', 0)} from the "
                               "store"))
        if len(fac.get("members", [])) > 1:
            opts.append(Option("kick", "Remove a member"))
    opts.append(Option("guild_leave", "Leave the banner"))


def _hall_list(p: dict, factions: list, lines: list,
               opts: list) -> list[dict]:
    """015: joining is a REQUEST an admin accepts; founding takes rank.
    019: both doors are always ROWS — founding shows locked below the
    rank, and the full ledger has its own row into the Community tab.
    027: every banner on offer shows its COLORS — the tile is the ask."""
    w = world(p) or {}
    requested = w.get("faction_requested", "")
    # 020: a non-member learns what the feature IS before the price.
    lines.append("A banner pools coin, fields a war party, racks shared "
                 "gear and enters the world's weekly challenges — its "
                 "prize is minted, not taken.")
    if not factions:
        lines.append(f"No banners fly yet. Yours could be the first — "
                     f"level {FOUND_MIN_LEVEL}, ◈ {GUILD_FOUND_FEE}.")
    gallery: list[dict] = []
    for f in factions[:5]:
        n = f.get("members", 0)
        asked = f["name"] == requested
        gallery.append({
            "opt": ("hall_ledger" if asked else f"join_{f['name']}"),
            "slug": str(f.get("banner") or ""),
            "label": f["name"],
            "sub": ("your request waits at their desk" if asked else
                    f"{n} at the table · join ◈ {f.get('join_fee', 0)} · "
                    f"dues ◈ {f.get('weekly_dues', 0)}/wk"),
        })
        lines.append(f"{f['name']} — {n} at the table")
        if asked:
            lines.append("  your request waits at their desk")
        else:
            opts.append(Option(f"join_{f['name']}", f"Ask to join {f['name']}",
                               f"join ◈ {f.get('join_fee', 0)} · dues "
                               f"◈ {f.get('weekly_dues', 0)}/wk"))
    total = int(w.get("factions_total", len(factions)))
    if total:
        opts.append(Option("hall_ledger", "Join a banner",
                           f"{total} flying · the Community tab"))
    if p["level"] < FOUND_MIN_LEVEL:
        opts.append(Option("found_guild", "Raise a new banner",
                           f"🔒 level {FOUND_MIN_LEVEL} · "
                           f"◈ {GUILD_FOUND_FEE}", locked=True))
    else:
        opts.append(Option("found_guild", "Raise a new banner",
                           f"◈ {GUILD_FOUND_FEE}"))
    return gallery


def guild_train(p: dict) -> Scene:
    """012: buy the level — full XP bar is the license, gold is the fee.
    XP banked past the cap carries over; wounds close on the level.
    022/002: LEVEL_CAP ends the drill — a refusal worth reading."""
    if p["level"] >= economy.LEVEL_CAP:
        return guildhall_scene(
            p, note=f"The drillmaster looks you over and laughs once: "
                    f"LEVEL {economy.LEVEL_CAP} is the whole drill. "
                    "There is no level after — only better steel, a "
                    "keener edge, and the war upstairs. Your ✦ spends "
                    "at the bench and in the field now.")
    need = economy.xp_need(p["level"])
    fee = economy.levelup_gold(p["level"])
    if p["xp"] < need:
        return guildhall_scene(
            p, note=f"The drillmaster shakes his head: XP "
                    f"{p['xp']:,}/{need:,}. Earn the bar first — "
                    "the tower is the only teacher.")
    if p["gold"] < fee:
        return guildhall_scene(
            p, note=f"Training to LEVEL {p['level'] + 1} costs ◈ {fee:,} "
                    f"— you carry ◈ {p['gold']:,}. Come back heavier.")
    p["gold"] -= fee
    p["xp"] -= need
    old_level = p["level"]
    p["level"] += 1
    p["hp"] = state.max_hp(p)
    _ledger(p, "levelup", gold=-fee, note=f"level {p['level']}")
    # 020: levels are BOUGHT, so this card is guaranteed to be read —
    # it announces everything the new level opens and closes.
    from .. import unlocks
    note = (f"+ LEVEL {p['level']} — the drill burns it into your "
            "frame. Wounds close.")
    for u in unlocks.just_reached(p, old_level, p["unlocked_floor"])[:4]:
        cost = f" ({u.cost})" if u.cost else ""
        note += f"\n{unlocks.glyph(u)} {u.title}{cost} — {u.why}"
    return guildhall_scene(p, note=note)


def _founding_scene(p: dict, st: dict, note: str = "") -> Scene:
    """The creation flow, one scene per step: name → banner → join fee →
    weekly dues. 027: the typed steps carry their own input box (the chat
    still works), and the sigil step shows the SIGILS instead of asking a
    founder to pick their colors out of a list of filenames."""
    step = st.get("step", "name")
    opts = [Option("cancel_found", "Never mind")]
    awaits, ask, gallery = "", None, []
    if step == "name":
        head, sup = "Name your banner", "3 to 24 letters."
        lines = []
        awaits = "the new banner's name"
        ask = {"kind": "text", "max": 24, "label": "the banner's name",
               "placeholder": "the name it flies under", "submit": "RAISE IT"}
    elif step == "banner":
        head, sup = f"A sigil for {st['name']}", \
            "Pick the mark your banner flies."
        lines = []
        gallery = [{"opt": f"sig_{slug}", "slug": slug,
                    "label": slug.replace("_", " ").title()}
                   for slug in _sigil_picks(st.get("name", ""),
                                            st.get("slugs") or [])]
    elif step == "fee":
        head = "Set the join fee"
        sup = (f"◈ 0 to {JOIN_FEE_MAX}. Every climber who joins pays it "
               "once, into the store.")
        lines = ["Immutable after founding — pick numbers people can "
                 "read before they join."]
        awaits = f"the join fee — a number, 0 to {JOIN_FEE_MAX}"
        ask = {"kind": "number", "min": 0, "max": JOIN_FEE_MAX,
               "label": "join fee, in gold", "placeholder": "0",
               "submit": "SET"}
    else:  # dues
        head = "Set the weekly dues"
        sup = (f"◈ {DUES_MIN} to {DUES_MAX}, collected from every member "
               "each week, into the store.")
        lines = [f"Join fee set at ◈ {st.get('fee', 0)}. You pay dues "
                 "too — the ◈ 500 founding price was your buy-in."]
        awaits = f"the weekly dues — a number, {DUES_MIN} to {DUES_MAX}"
        ask = {"kind": "number", "min": DUES_MIN, "max": DUES_MAX,
               "label": "weekly dues, in gold", "placeholder": str(DUES_MIN),
               "submit": "SET"}
    if note:
        lines.insert(0, note)
    return Scene(
        eyebrow="ROOTHOLLOW · THE GUILDHALL",
        headline=head,
        support=sup,
        body_lines=lines,
        options=opts,
        meters=meters(p),
        awaits_text=awaits,
        ask=ask,
        gallery=gallery,
    )


def _sigil_picks(name: str, slugs: list) -> list:
    """8 sigils from the full set, rotated by the banner's name so every
    founder sees a different spread."""
    if not slugs:
        return []
    start = sum(name.encode()) % len(slugs)
    return [slugs[(start + i) % len(slugs)] for i in range(min(8,
                                                               len(slugs)))]


def _donate_prompt(p: dict, note: str = "") -> Scene:
    return Scene(
        eyebrow="ROOTHOLLOW · THE GUILDHALL",
        headline="How much goes in the box?",
        support=f"You carry ◈ {p['gold']:,}. Carried gold only; the bank "
                "stays yours.",
        body_lines=[note] if note else [],
        options=[Option("cancel_donate", "Never mind")],
        meters=meters(p),
        awaits_text="the donation amount — a number in carried gold",
        ask={"kind": "number", "min": 1, "max": max(1, int(p["gold"])),
             "label": "into the store, in carried gold",
             "placeholder": "0", "submit": "DONATE"},
    )


def _kick_prompt(p: dict, note: str = "") -> Scene:
    w = world(p) or {}
    fac = w.get("faction") or {}
    opts = []
    for m in fac.get("members", [])[:8]:
        nm = m.get("name", "?")
        if nm != p.get("name"):
            arr = " · arrears" if m.get("arrears") else ""
            pips = _pips(m.get("days", 0), m.get("required", 4))
            opts.append(Option(f"kick_{nm}", f"Remove {nm}",
                               f"{pips}{arr}"))
    opts.append(Option("cancel_kick", "Never mind"))
    return Scene(
        eyebrow="ROOTHOLLOW · THE GUILDHALL",
        headline="Who leaves the table?",
        support="Kicking a no-show lifts their dead weight off the "
                "attendance ratio.",
        body_lines=[note] if note else [],
        options=opts,
        meters=meters(p),
    )


def guildhall_action(p: dict, oid: str, text: str = "") -> Scene:
    w = world(p) or {}
    fac = w.get("faction")
    st = p.get("founding_guild")
    if isinstance(st, dict):
        if oid == "cancel_found":
            p.pop("founding_guild", None)
            return guildhall_scene(p, note="The charter stays blank.")
        if oid.startswith("sig_") and st.get("step") == "banner":
            st["banner"] = oid.removeprefix("sig_")
            st["step"] = "fee"
            return _founding_scene(p, st)
        return _founding_scene(p, st)
    if p.get("faction_donating"):
        p.pop("faction_donating", None)
        return guildhall_scene(p, note="The box stays shut.")
    if p.get("faction_kicking"):
        p.pop("faction_kicking", None)
        if oid.startswith("kick_") and fac:
            target = oid.removeprefix("kick_")
            _effect(p, "faction_kick", name=target)
            fac["members"] = [m for m in fac.get("members", [])
                              if m.get("name") != target]
            return guildhall_scene(
                p, note=f"+ {target}'s chair scrapes back. The table "
                        "moves on.")
        return guildhall_scene(p)
    if oid == "guild_train":
        return guild_train(p)
    if oid == "hall_ledger":
        # 019: the door to the board — the pane switches tabs on this
        # id client-side; the chat path gets told where the ledger is.
        return guildhall_scene(
            p, note="The full ledger hangs in the Community tab — "
                    "every banner, every desk. Ask to join from there, "
                    "or raise your own right here.")
    if oid == "found_guild":
        if fac or p.get("guild"):
            # 019: one banner per climber — leaving first is the path
            name = (fac or {}).get("name") or p.get("guild")
            return guildhall_scene(
                p, note=f"You already sit at the {name} table — leave "
                        "it before you raise your own.")
        if p["level"] < FOUND_MIN_LEVEL:
            return guildhall_scene(
                p, note=f"The hall charters new banners for level "
                        f"{FOUND_MIN_LEVEL}+ climbers. Train first.")
        if p["gold"] < GUILD_FOUND_FEE:
            return guildhall_scene(
                p, note=f"The charter takes ◈ {GUILD_FOUND_FEE} carried "
                        f"— you hold ◈ {p['gold']:,}. The Vault gives "
                        "back what it keeps.")
        if w.get("factions") is None:
            # local dev mode — legacy one-shot naming, no purse
            p["founding_guild"] = True
            return Scene(
                eyebrow="ROOTHOLLOW · THE GUILDHALL",
                headline="Name your banner",
                support="Say it in chat — 3 to 24 letters.",
                options=[],
                meters=meters(p),
            )
        p["founding_guild"] = {"step": "name",
                               "slugs": w.get("faction_banners") or []}
        return _founding_scene(p, p["founding_guild"])
    if oid == "donate" and fac:
        p["faction_donating"] = True
        return _donate_prompt(p)
    if oid.startswith("take_arm_") and fac:
        return _armory_take(p, oid.removeprefix("take_arm_"))
    if oid == "enter_week" and fac and fac.get("role") == "steward":
        wk = fac.get("week") or {}
        cost = int(wk.get("entry_cost", 0))
        store = int(fac.get("store", 0))
        if wk.get("entered"):
            return guildhall_scene(p, note="Your banner is already in "
                                           "this week's lists.")
        if store < cost:
            return guildhall_scene(
                p, note=f"The entry is ◈ {cost} and the store holds "
                        f"◈ {store} — ◈ {cost - store} short. Dues land "
                        "at week's turn, or pass the hat.")
        _effect(p, "faction_enter")
        wk["entered"] = True
        fac["store"] = store - cost
        return guildhall_scene(
            p, note=f"+ ◈ {cost} from the store — the "
                    f"{str(wk.get('kind', '')).upper()} is on. "
                    "Everything the table earns this week counts.")
    if oid == "kick" and fac and fac.get("role") == "steward":
        p["faction_kicking"] = True
        return _kick_prompt(p)
    if oid.startswith("join_"):
        g = oid.removeprefix("join_")
        if w.get("factions") is not None:
            # 015: joining is a request — no gold moves until an admin
            # accepts it (the fee is charged at the desk, on accept)
            f = next((x for x in w["factions"] if x["name"] == g), None)
            if f is None:
                return guildhall_scene(p, note="That banner came down "
                                               "while you read the wall.")
            _effect(p, "faction_request", guild=g)
            w["faction_requested"] = g
            fee = int(f.get("join_fee", 0))
            fee_note = (f" — the ◈ {fee} join fee is charged if they "
                        "take you" if fee else "")
            return guildhall_scene(
                p, note=f"+ your name goes to the {g} admins{fee_note}. "
                        "Watch the Community desk.")
        p["guild"] = g
        _effect(p, "guild_join", guild=g)
        return guildhall_scene(p, note=f"+ you drink under the {g} banner now")
    if oid == "guild_leave":
        g = p.pop("guild", None) or (fac or {}).get("name")
        if g:
            _effect(p, "guild_leave", guild=g)
        # its own card, for the same reason founding has one: the snapshot in
        # hand still seats you at the table you just walked out of.
        return Scene(
            eyebrow="ROOTHOLLOW · THE GUILDHALL",
            headline="You fold your colors",
            support="Milestone Wardens fall to war parties, not heroes.",
            body_lines=[
                f"+ your name comes off the {g} roster" if g
                else "+ your name comes off the roster",
                "What you paid in stays in the store. The rack keeps what "
                "you hung on it.",
            ],
            options=[Option("hall_table", "The hall"),
                     Option("town", "Back to the square")],
            meters=meters(p),
            banner="guildhall",
        )
    return guildhall_scene(p)


def _armory_take(p: dict, raw_id: str) -> Scene:
    """007: lift a piece off the banner's rack. The engine validates
    against the injected shelf (cooldown, row still there) and emits
    the effect; worldd moves the piece into the pack, wear intact —
    no gold anywhere in the loop (the EV law)."""
    w = world(p) or {}
    rack = w.get("armory")
    if rack is None:
        return guildhall_scene(p)
    if w.get("armory_took_today"):
        return guildhall_scene(
            p, note="One piece a day — the racks open again tomorrow.")
    try:
        item_id = int(raw_id)
    except ValueError:
        return guildhall_scene(p)
    it = next((x for x in rack if int(x.get("id", -1)) == item_id), None)
    if it is None:
        return guildhall_scene(
            p, note="That piece already left the rack.")
    _effect(p, "armory_take", item_id=item_id)
    w["armory"] = [x for x in rack if int(x.get("id", -1)) != item_id]
    w["armory_took_today"] = True
    worn = (f" — worn to {round(it.get('frac', 1.0) * 100)}%"
            if it.get("frac", 1.0) < 1.0 else "")
    return guildhall_scene(
        p, note=f"+ the {it['name']} comes off the rack into your "
                f"pack{worn}. {it['donor']} hung it there.")


def guildhall_found(p: dict, text: str) -> Scene:
    """Typed replies during the founding flow (and the donate amount —
    core routes both here via the doc flags)."""
    st = p.get("founding_guild")
    if not isinstance(st, dict):
        # legacy one-shot flow (local dev mode)
        p.pop("founding_guild", None)
        return _found_finish(p, text.strip()[:24], "", 0, 5)
    step = st.get("step", "name")
    if step == "name":
        name = text.strip()[:24]
        if len(name) < 3:
            return _founding_scene(p, st, note="Three letters at least. "
                                               "Banners need room for "
                                               "glory.")
        st["name"] = name
        if st.get("slugs"):
            st["step"] = "banner"
        else:
            st["step"] = "fee"
        return _founding_scene(p, st)
    if step == "fee":
        try:
            fee = int(text.strip().lstrip("◈").replace(",", ""))
        except ValueError:
            return _founding_scene(p, st, note="A number, ◈ 0 to "
                                               f"{JOIN_FEE_MAX}.")
        if not 0 <= fee <= JOIN_FEE_MAX:
            return _founding_scene(p, st, note="A number, ◈ 0 to "
                                               f"{JOIN_FEE_MAX}.")
        st["fee"] = fee
        st["step"] = "dues"
        return _founding_scene(p, st)
    if step == "dues":
        try:
            dues = int(text.strip().lstrip("◈").replace(",", ""))
        except ValueError:
            return _founding_scene(p, st, note=f"A number, ◈ {DUES_MIN} "
                                               f"to {DUES_MAX}.")
        if not DUES_MIN <= dues <= DUES_MAX:
            return _founding_scene(p, st, note=f"A number, ◈ {DUES_MIN} "
                                               f"to {DUES_MAX}.")
        p.pop("founding_guild", None)
        return _found_finish(p, st["name"], st.get("banner", ""),
                             st.get("fee", 0), dues)
    return _founding_scene(p, st)


def _found_finish(p: dict, name: str, banner: str, join_fee: int,
                  dues: int) -> Scene:
    if len(name) < 3:
        return guildhall_scene(p, note="Three letters at least. Banners "
                                       "need room for glory.")
    if p["gold"] < GUILD_FOUND_FEE:
        return guildhall_scene(p, note=f"The fee stands at "
                                       f"◈ {GUILD_FOUND_FEE}. Come back "
                                       "heavier.")
    p["gold"] -= GUILD_FOUND_FEE
    p["guild"] = name
    _ledger(p, "guild_found", gold=-GUILD_FOUND_FEE, note=name)
    _effect(p, "guild_found", guild=name, banner=banner,
            join_fee=join_fee, weekly_dues=dues)
    # 027: its own card, not the hall's. worldd is the single writer, so the
    # snapshot in hand still holds no faction — rendering the hall here put
    # "No banners fly yet. Yours could be the first" directly under the line
    # announcing that yours had just gone up.
    return Scene(
        eyebrow="ROOTHOLLOW · THE GUILDHALL",
        headline=f"The {name} banner flies",
        support="Milestone Wardens fall to war parties, not heroes.",
        body_lines=[
            f"+ the charter is signed — ◈ {GUILD_FOUND_FEE} to the hall, "
            "and the sigil goes up over your table",
            f"join ◈ {join_fee} once · dues ◈ {dues}/week — both immutable "
            "now, both paid into the store",
            "The store funds the war party and the armory. Take the week's "
            "work when the Ascent names it.",
        ],
        options=[Option("hall_table", "Your table"),
                 Option("town", "Back to the square")],
        meters=meters(p),
        banner=banner or "guildhall",
    )


def guildhall_donate(p: dict, text: str) -> Scene:
    """The typed donation amount (carried gold only)."""
    p.pop("faction_donating", None)
    w = world(p) or {}
    fac = w.get("faction") or {}
    try:
        amt = int(text.strip().lstrip("◈").replace(",", ""))
    except ValueError:
        return guildhall_scene(p, note="The box takes numbers, not "
                                       "speeches.")
    if amt <= 0:
        return guildhall_scene(p, note="The box takes numbers, not "
                                       "speeches.")
    if p["gold"] < amt:
        return guildhall_scene(p, note=f"You carry ◈ {p['gold']:,} — "
                                       f"not ◈ {amt:,}.")
    p["gold"] -= amt
    _ledger(p, "faction_donation", gold=-amt, note=fac.get("name", ""))
    _effect(p, "faction_donate", amount=amt)
    fac["store"] = int(fac.get("store", 0)) + amt
    return guildhall_scene(p, note=f"+ ◈ {amt:,} into the store — "
                                   f"◈ {fac['store']:,} now")


# ── The shared frontier Warden (007 §3) ──────────────────────────────────
# One live Warden for the whole world: worldd injects its HP pool as
# w["warden"]; strikes are effects the host resolves transactionally. The
# kill (frontier raise, reward split, fall reports) happens server-side.

def _warden_banner(fl) -> str:
    from .combat import _creature_art
    slug = f"warden_{fl.floor:03d}"
    return slug if _creature_art(slug) else ""


def _warden_fallen_scene(p: dict, fl) -> Scene:
    p["location"] = "gate_town"
    return Scene(
        eyebrow=f"FLOOR {fl.floor} · {fl.biome.upper()} · THE KEEP",
        headline=f"{fl.warden_name} has already fallen",
        support="The keep is a monument now. The lift above stands open.",
        body_lines=["Scorch marks and silence. Someone got here first."],
        options=[Option("hunt", "Hunt the wilds", "1 ⚡"),
                 Option("town", "Return to Roothollow")],
        meters=meters(p),
    )


def _war_bar(hp: int, hp_max: int, cells: int = 10) -> str:
    """022/006: the wound at a glance. Full cells only when truly full,
    an empty bar only at zero."""
    frac = hp / max(1, hp_max)
    filled = round(cells * frac)
    if hp > 0:
        filled = max(1, filled)
    if hp < hp_max:
        filled = min(cells - 1, filled)
    return "█" * filled + "·" * (cells - filled)


def _fmt_countdown(seconds) -> str:
    h, m = int(seconds) // 3600, (int(seconds) % 3600) // 60
    return f"{h}h {m:02d}m" if h else f"{m}m"


def _hour_roll(strikers: list[dict]) -> str:
    """'Kettle, Brakka +24 struck this hour' — hot blades first."""
    now = state.now()
    recent = []
    for s in strikers:
        try:
            ts = dt.datetime.fromisoformat(s["ts"])
        except (KeyError, ValueError, TypeError):
            continue
        if (now - ts).total_seconds() <= 3600:
            recent.append(s)
    if not recent:
        return ""
    recent.sort(key=lambda s: -int(s.get("dmg", 0)))
    names = ", ".join(s.get("name") or "?" for s in recent[:2])
    more = len(recent) - 2
    tail = f" +{more}" if more > 0 else ""
    return f"{names}{tail} struck this hour"


def _war_standings(strikers: list[dict]) -> list[str]:
    """Faction damage standings — top banners by total cut."""
    by: dict[str, int] = {}
    for s in strikers:
        g = s.get("guild") or ""
        if g:
            by[g] = by.get(g, 0) + int(s.get("dmg", 0))
    top = sorted(by.items(), key=lambda kv: -kv[1])[:3]
    return [f"· {g} — {d:,} cut" for g, d in top]


def warden_scene(p: dict, fl, note: str = "") -> Scene:
    w = world(p) or {}
    wd = w.get("warden") or {}
    if wd.get("floor") != fl.floor:
        return _warden_fallen_scene(p, fl)
    hp, hp_max = int(wd.get("hp", 0)), max(1, int(wd.get("hp_max", 1)))
    atk_w, def_w, _ = economy.warden_stats(fl.floor)
    pct = max(0, round(100 * hp / hp_max))
    pity = int(wd.get("pity", 0))
    lines = []
    if note:
        lines.append(note)
    # 022/006: a wound that closed since the last look — the pity line.
    seen = p.get("war_seen") or {}
    if seen.get("floor") == fl.floor and pity > int(seen.get("pity", 0)):
        lines.append("The wound has CLOSED — the Warden healed whole. "
                     "But slower than before: every closing costs it "
                     f"{round(economy.WARDEN_PITY_PCT * 100)}% of its "
                     "body, forever.")
    p["war_seen"] = {"floor": fl.floor, "pity": pity}
    lines.append(fl.warden_prose)
    lines.append(f"{_war_bar(hp, hp_max)} {pct}% — {hp:,}/{hp_max:,} HP")
    # 024: a four-digit bar reads as a wall unless the card says what the
    # pool is MEASURED in. One full fight is the unit it was sized in.
    unit = max(1, economy.strike_fight_damage(fl.floor))
    left = max(1, -(-hp // unit))
    if left == 1:
        lines.append("≈1 full fight left to close it — the last blow is "
                     "there for the taking")
    else:
        lines.append(f"≈{left} full fights left to close it — {left} of "
                     "yours, or one each from as many blades")
    closes = wd.get("closes_in_s")
    if economy.warden_silence_hours(fl.floor) is None:
        # 025 §3: the siege floors. No regen, no silence window, no pity —
        # say so plainly, because "come back tomorrow" is only a strategy
        # if the player knows the wound will still be there.
        if hp < hp_max:
            lines.append("This one does not heal. Every blow landed here "
                         "is permanent — leave and come back a day later "
                         "and the wound is exactly as you left it.")
        else:
            lines.append("It stands whole, and it does not heal. From the "
                         "first blow onward, every point you take off it "
                         "stays off.")
    elif hp < hp_max and closes is not None:
        lines.append(f"the wound closes in {_fmt_countdown(closes)} — "
                     "keep striking")
    if pity > 0:
        lines.append(f"it has healed {pity} time{'s' if pity != 1 else ''}"
                     " — each closing left it weaker")
    strikers = wd.get("strikers") or []
    roll = _hour_roll(strikers)
    if roll:
        lines.append(roll)
    if strikers:
        names = ", ".join(s.get("name") or "?" for s in strikers[:6])
        lines.append(f"blades against it: {names}")
        lines += _war_standings(strikers)
    else:
        lines.append("no blade has touched it yet — the first strike is "
                     "yours to take")
    # 026: say what a charge actually buys, in rounds, and that walking
    # out of a keep is a gamble rather than a button.
    lines.append(f"one charge buys an exchange of about "
                 f"{economy.warden_exchange_rounds(fl.floor)} rounds, and "
                 f"every swing inside costs {economy.COST_WARDEN_STRIKE} ⚡ "
                 "more — then its guard closes and drives you back. Turning "
                 "your back on it early is a gamble; it can follow you out.")
    opts = [Option("strike", "Join the fight",
                   f"{economy.COST_WARDEN_ATTEMPT} ⚡ · a full fight")]
    # 022/006: the horn — guild hands only, only while a wound is open.
    if p.get("guild") and hp < hp_max:
        opts.append(Option("horn", "Sound the horn",
                           "letters every guildmate — once a wound"))
    opts.append(Option("town", "Withdraw to Roothollow"))
    return Scene(
        eyebrow=f"FLOOR {fl.floor} · {fl.biome.upper()} · THE KEEP",
        headline=f"{fl.warden_name} — ATK {atk_w} / DEF {def_w} / "
                 f"HP {hp:,}/{hp_max:,}",
        support="One Warden for the whole world. Every wound you leave "
                "stays in its body — the last blow opens this floor for "
                "everyone.",
        body_lines=lines,
        options=opts,
        meters=meters(p),
        event_kind="boss",
        banner=_warden_banner(fl),
    )


def warden_action(p: dict, fl, oid: str) -> Scene:
    """022/001: the single-swing strike is retired — joining the shared
    Warden is a FULL keep fight. Damage dealt persists to the world pool
    (emitted as one warden_strike when the fight ends, however it ends);
    the pool at zero opens the floor for everyone."""
    if oid == "horn":
        # 022/006: one tap letters the whole banner. The doc-side flag
        # stops re-taps this wound; the server's horns slate is the law
        # (once per BANNER per wound).
        w = world(p) or {}
        wd = w.get("warden") or {}
        if not p.get("guild") or wd.get("floor") != fl.floor \
                or int(wd.get("hp", 0)) >= int(wd.get("hp_max", 1)):
            return warden_scene(p, fl)
        mark = f"{fl.floor}:{int(wd.get('pity', 0))}"
        if p.get("horn_sent") == mark:
            return warden_scene(p, fl, note="The horn has sounded for "
                                            "this wound — the banner "
                                            "knows.")
        p["horn_sent"] = mark
        _effect(p, "horn", floor=fl.floor)
        _ledger(p, "horn", note=f"floor {fl.floor}")
        return warden_scene(p, fl, note="The horn rings down the tower — "
                                        "your banner has the floor and "
                                        "the clock.")
    if oid != "strike":
        return warden_scene(p, fl)
    w = world(p) or {}
    wd = w.get("warden") or {}
    if wd.get("floor") != fl.floor:
        return _warden_fallen_scene(p, fl)
    if not state.spend_energy(p, economy.COST_WARDEN_ATTEMPT):
        return warden_scene(p, fl, note="Joining the fight takes 3 ⚡ you "
                                        "don't have. The wilds cost less.")
    from . import combat
    s = combat.start_encounter(p, fl, None, "warden")
    e = p["encounter"]
    e["shared"] = True
    # the fight is against the WORLD's body: pick up the pool where the
    # last blade left it (optimistic — the server clamps on the effect).
    e["hp"] = max(1, int(wd.get("hp", e["hp"])))
    e["hp_max"] = max(e["hp"], int(wd.get("hp_max", e["hp"])))
    # 026: where THIS blade found the body. hp_max is the body's size (the
    # war bar, the scan, "bites deep" all read it); the strike this fight
    # reports has to be measured from the join, or a climber who walks
    # into a half-cut gate is credited with everyone else's work and the
    # pool collapses on his first swing.
    e["hp_join"] = e["hp"]
    s2 = combat.fight_scene(p, fl, opener=True)
    s2.event_kind = s.event_kind or "boss"
    s2.support = ("Its wounds are the world's wounds — whatever you cut "
                  "away stays cut.")
    return s2


# ── Milestone boss quorum ────────────────────────────────────────────────

def boss_scene(p: dict, floor, note: str = "") -> Scene:
    w = world(p) or {}
    b = w.get("boss") or {}
    ms = floor.milestone
    committed = b.get("committed", [])
    quorum = b.get("quorum",
                   economy.milestone_quorum(floor.floor) if ms else 2)
    dots = "■" * len(committed) + "□" * max(0, quorum - len(committed))
    lines = [floor.warden_prose]
    if note:
        lines.insert(0, note)
    lines.append(f"war party {dots}  ({len(committed)}/{quorum})")
    if committed:
        lines.append("committed: " + ", ".join(committed))
    opts = []
    already = p.get("name") in committed
    if already:
        lines.append("Your blade is pledged. The fight begins when the "
                     "party is whole.")
    else:
        opts.append(Option("boss_commit", "Pledge your blade",
                           f"{economy.COST_BOSS_COMMIT} ⚡"))
    opts.append(Option("town", "Withdraw to Roothollow"))
    return Scene(
        eyebrow=f"FLOOR {floor.floor} · {floor.biome.upper()} · THE KEEP",
        headline=f"{ms.name if ms else floor.warden_name} — "
                 f"ATK {ms.atk} / DEF {ms.dfs} / HP {ms.hp:,}" if ms else
                 floor.warden_name,
        support="A quorum fight. Pledges hold for two days, then lapse.",
        body_lines=lines,
        options=opts,
        meters=meters(p),
        event_kind="boss",
        banner="gnarl" if floor.floor == 10 else "",
    )


def boss_action(p: dict, floor, oid: str) -> Scene:
    if oid != "boss_commit":
        return boss_scene(p, floor)
    if not state.spend_energy(p, economy.COST_BOSS_COMMIT):
        return boss_scene(p, floor, note="A pledge costs 5 ⚡ — rest first.")
    _effect(p, "boss_commit", floor=floor.floor)
    return boss_scene(p, floor, note="You drive your blade into the "
                                     "pledge-post.")
