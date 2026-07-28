"""Social scenes — the shared-world layer (relay, fields/PvP, grants,
guildhall, boss quorums).

Only active when the host injected `doc["_world"]` (worldd does; local
solo mode has no social surface). Cross-player writes never happen here:
the engine validates and pays costs, then emits `doc["_effects"]` for the
host to execute in the same transaction.
"""

from __future__ import annotations

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
            support="Say the words in chat — the clerk writes them down.",
            shard_note="Keep it under a hundred words. The clerk charges "
                       "attitude by the page.",
            options=[],
            meters=meters(p),
            awaits_text=f"the letter's words for {target}",
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
        support="Receivers must be level 5+ — the Vault doesn't fund cradles.",
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
    lines = [note] if note else []
    opts = []
    # 012: training — levels are bought here, never granted in the field.
    fee = economy.levelup_gold(p["level"])
    need = economy.xp_need(p["level"])
    opts.append(Option("guild_train", f"Train to LEVEL {p['level'] + 1}",
                       f"◈ {fee:,}"))
    if p["xp"] < need and not note:
        lines.append(f"The drillmaster sizes you up: XP {p['xp']:,}/{need:,}."
                     " Come back with a full bar — the fee is "
                     f"◈ {fee:,}.")
    if fac:
        _member_panel(p, fac, lines, opts)
        headline = f"The {fac['name']} table"
    elif w.get("factions") is not None:
        _hall_list(p, w["factions"], lines, opts)
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
        banner="guildhall",
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


def _hall_list(p: dict, factions: list, lines: list, opts: list) -> None:
    """015: joining is a REQUEST an admin accepts; founding takes rank.
    019: both doors are always ROWS — founding shows locked below the
    rank, and the full ledger has its own row into the Community tab."""
    w = world(p) or {}
    requested = w.get("faction_requested", "")
    if not factions:
        lines.append("No banners fly yet. Yours could be the first.")
    for f in factions[:5]:
        n = f.get("members", 0)
        lines.append(f"{f['name']} — {n} at the table")
        if f["name"] == requested:
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


def guild_train(p: dict) -> Scene:
    """012: buy the level — full XP bar is the license, gold is the fee.
    XP banked past the cap carries over; wounds close on the level."""
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
    p["level"] += 1
    p["hp"] = state.max_hp(p)
    _ledger(p, "levelup", gold=-fee, note=f"level {p['level']}")
    return guildhall_scene(
        p, note=f"+ LEVEL {p['level']} — the drill burns it into your "
                "frame. Wounds close.")


def _founding_scene(p: dict, st: dict, note: str = "") -> Scene:
    """The creation flow, one scene per step: name → banner → join fee →
    weekly dues. Typed steps take a chat reply; the banner step is an
    option pick."""
    step = st.get("step", "name")
    opts = [Option("cancel_found", "Never mind")]
    awaits = ""
    if step == "name":
        head, sup = "Name your banner", "Say it in chat — 3 to 24 letters."
        lines = []
        awaits = "the new banner's name"
    elif step == "banner":
        head, sup = f"A sigil for {st['name']}", \
            "Pick the mark your banner flies."
        lines = []
        for slug in _sigil_picks(st.get("name", ""), st.get("slugs") or []):
            opts.insert(-1, Option(f"sig_{slug}",
                                   slug.replace("_", " ").title()))
    elif step == "fee":
        head = "Set the join fee"
        sup = (f"Say a number in chat — ◈ 0 to {JOIN_FEE_MAX}. Every "
               "climber who joins pays it once, into the store.")
        lines = ["Immutable after founding — pick numbers people can "
                 "read before they join."]
        awaits = f"the join fee — a number, 0 to {JOIN_FEE_MAX}"
    else:  # dues
        head = "Set the weekly dues"
        sup = (f"Say a number in chat — ◈ {DUES_MIN} to {DUES_MAX}, "
               "collected from every member each week, into the store.")
        lines = [f"Join fee set at ◈ {st.get('fee', 0)}. You pay dues "
                 "too — the ◈ 500 founding price was your buy-in."]
        awaits = f"the weekly dues — a number, {DUES_MIN} to {DUES_MAX}"
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
        support=f"Say a number in chat — you carry ◈ {p['gold']:,}. "
                "Carried gold only; the bank stays yours.",
        body_lines=[note] if note else [],
        options=[Option("cancel_donate", "Never mind")],
        meters=meters(p),
        awaits_text="the donation amount — a number in carried gold",
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
        g = p.pop("guild", None)
        if g:
            _effect(p, "guild_leave", guild=g)
        return guildhall_scene(p, note="You fold your colors and walk out.")
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
    return guildhall_scene(p, note=f"+ the {name} banner goes up over "
                                   f"your table — join ◈ {join_fee}, "
                                   f"dues ◈ {dues}/week")


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


def warden_scene(p: dict, fl, note: str = "") -> Scene:
    w = world(p) or {}
    wd = w.get("warden") or {}
    if wd.get("floor") != fl.floor:
        return _warden_fallen_scene(p, fl)
    hp, hp_max = int(wd.get("hp", 0)), max(1, int(wd.get("hp_max", 1)))
    atk_w, def_w, _ = economy.warden_stats(fl.floor)
    pct = max(0, round(100 * hp / hp_max))
    lines = []
    if note:
        lines.append(note)
    lines.append(fl.warden_prose)
    lines.append(f"the Warden stands at {pct}% — {hp:,}/{hp_max:,} HP")
    strikers = wd.get("strikers") or []
    if strikers:
        names = ", ".join(s.get("name") or "?" for s in strikers[:6])
        lines.append(f"blades against it: {names}")
    else:
        lines.append("no blade has touched it yet — the first strike is "
                     "yours to take")
    return Scene(
        eyebrow=f"FLOOR {fl.floor} · {fl.biome.upper()} · THE KEEP",
        headline=f"{fl.warden_name} — ATK {atk_w} / DEF {def_w} / "
                 f"HP {hp:,}/{hp_max:,}",
        support="One Warden for the whole world. Whoever lands the last "
                "blow opens this floor for everyone.",
        body_lines=lines,
        options=[Option("strike", "Strike the Warden",
                        f"{economy.COST_WARDEN_ATTEMPT} ⚡"),
                 Option("town", "Withdraw to Roothollow")],
        meters=meters(p),
        event_kind="boss",
        banner=_warden_banner(fl),
    )


def warden_action(p: dict, fl, oid: str) -> Scene:
    if oid != "strike":
        return warden_scene(p, fl)
    w = world(p) or {}
    wd = w.get("warden") or {}
    if wd.get("floor") != fl.floor:
        return _warden_fallen_scene(p, fl)
    if not state.spend_energy(p, economy.COST_WARDEN_ATTEMPT):
        return warden_scene(p, fl, note="A strike takes 3 ⚡ you don't "
                                        "have. The wilds cost less.")
    atk_w, def_w, _ = economy.warden_stats(fl.floor)
    raw = state.rng_int(p, state.atk(p) // 2, state.atk(p))
    dmg = max(1, raw - def_w // 2)
    _effect(p, "warden_strike", floor=fl.floor, damage=dmg)
    _ledger(p, "warden_strike", note=f"floor {fl.floor} · {dmg}")
    # the Warden answers — one counter-swing per strike. 013: same chip
    # rule as the wilds — armor blunts, it never nullifies.
    back_raw = state.rng_int(p, atk_w // 2, atk_w)
    chip = max(1, -(-back_raw // economy.CHIP_DIVISOR))
    back = max(chip, back_raw - state.dfs(p) // 2)
    back_blocked = back_raw - back
    p["hp"] -= back
    if p["hp"] <= 0:
        # the dying blow still lands (the effect above is already queued)
        from .combat import _death
        p["encounter"] = {"kind": "warden", "name": fl.warden_name,
                          "prose": "", "id": "", "atk": atk_w, "def": def_w,
                          "hp": 1, "hp_max": 1, "floor": fl.floor,
                          "shot_used": False}
        return _death(p, fl)
    # optimistic display — the authoritative write is the effect above
    wd["hp"] = max(0, int(wd.get("hp", 0)) - dmg)
    strikers = wd.setdefault("strikers", [])
    mine = next((s for s in strikers if s.get("name") == p.get("name")),
                None)
    if mine is None:
        strikers.append({"name": p.get("name") or "?", "dmg": dmg})
    else:
        mine["dmg"] = int(mine.get("dmg", 0)) + dmg
    note = f"your blow lands for {dmg:,} — it answers for {back}"
    if back_blocked > 0:
        note += f" (your armor blunted {back_blocked})"
    if wd["hp"] <= 0:
        note += (". It staggers. If it fell, word reaches Roothollow "
                 "with your name on it")
    return warden_scene(p, fl, note=note)


# ── Milestone boss quorum ────────────────────────────────────────────────

def boss_scene(p: dict, floor, note: str = "") -> Scene:
    w = world(p) or {}
    b = w.get("boss") or {}
    ms = floor.milestone
    committed = b.get("committed", [])
    quorum = b.get("quorum", ms.quorum if ms else 2)
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
