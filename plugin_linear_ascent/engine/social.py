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
    targets = w.get("names", [])[:6]
    for t in targets:
        if t != p.get("name"):
            opts.append(Option(f"write_{t}", f"Write to {t}",
                               f"◈ {economy.LETTER_PRICE}"))
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

GUILD_FOUND_FEE = 500


def guildhall_scene(p: dict, note: str = "") -> Scene:
    w = world(p) or {}
    guilds = w.get("guilds", [])
    mine = p.get("guild")
    lines = [note] if note else []
    opts = []
    if mine:
        roster = w.get("guild_roster", [])
        lines.append(f"Your banner: {mine} — "
                     + (", ".join(roster[:8]) if roster else "just you"))
        opts.append(Option("guild_leave", "Leave the guild"))
    else:
        for g in guilds[:6]:
            opts.append(Option(f"join_{g}", f"Join {g}"))
        if p["gold"] >= GUILD_FOUND_FEE:
            opts.append(Option("found_guild", "Found a guild",
                               f"◈ {GUILD_FOUND_FEE}"))
        elif not guilds:
            lines.append(f"Founding a banner costs ◈ {GUILD_FOUND_FEE}.")
    opts.append(Option("town", "Back to the square"))
    return Scene(
        eyebrow="ROOTHOLLOW · THE GUILDHALL",
        headline=(f"The {mine} table" if mine else "Banners for hire"),
        support="Milestone Wardens fall to war parties, not heroes.",
        body_lines=lines,
        options=opts,
        meters=meters(p),
        banner="guildhall",
    )


def guildhall_action(p: dict, oid: str, text: str = "") -> Scene:
    if oid == "found_guild":
        p["founding_guild"] = True
        return Scene(
            eyebrow="ROOTHOLLOW · THE GUILDHALL",
            headline="Name your banner",
            support="Say it in chat — 3 to 24 letters.",
            options=[],
            meters=meters(p),
        )
    if oid.startswith("join_"):
        g = oid.removeprefix("join_")
        p["guild"] = g
        _effect(p, "guild_join", guild=g)
        return guildhall_scene(p, note=f"+ you drink under the {g} banner now")
    if oid == "guild_leave":
        g = p.pop("guild", None)
        if g:
            _effect(p, "guild_leave", guild=g)
        return guildhall_scene(p, note="You fold your colors and walk out.")
    return guildhall_scene(p)


def guildhall_found(p: dict, text: str) -> Scene:
    p.pop("founding_guild", None)
    name = text.strip()[:24]
    if len(name) < 3:
        return guildhall_scene(p, note="Three letters at least. Banners "
                                       "need room for glory.")
    if p["gold"] < GUILD_FOUND_FEE:
        return guildhall_scene(p, note="The fee stands at ◈ 500. Come back "
                                       "heavier.")
    p["gold"] -= GUILD_FOUND_FEE
    p["guild"] = name
    _ledger(p, "guild_found", gold=-GUILD_FOUND_FEE, note=name)
    _effect(p, "guild_found", guild=name)
    return guildhall_scene(p, note=f"+ the {name} banner goes up over "
                                   "your table")


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
