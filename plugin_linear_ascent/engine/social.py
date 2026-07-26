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


# ── The Muster Roll (004 §C.2 — every climber, on one board) ────────────

def muster_scene(p: dict, note: str = "") -> Scene:
    w = world(p) or {}
    roster = w.get("roster", [])
    count = w.get("roster_count", len(roster))
    frontier = w.get("frontier", p["unlocked_floor"])
    lines = [note] if note else []
    for r in roster[:12]:
        me = " ← you" if r.get("name") == p.get("name") else ""
        seen = r.get("last_seen_days", 0)
        seen_txt = ("today" if seen <= 0 else
                    f"{seen}d ago" if seen < 30 else "long gone")
        lines.append(
            f"{r.get('name', '?')} — {r.get('race', '?')} "
            f"{r.get('clazz', '?')}, L{r.get('level', 1)} · "
            f"power {r.get('power', 0)} · floor {r.get('floor', 1)} · "
            f"wealth #{r.get('bank_rank', '?')} · {seen_txt}{me}")
    if not roster:
        lines.append("The board is freshly sanded. Yours could be the "
                     "first name on it.")
    return Scene(
        eyebrow="ROOTHOLLOW · THE MUSTER ROLL",
        headline=f"{count} climber{'s' if count != 1 else ''} on the Ascent",
        support=f"Every name on this board is climbing the same tower. "
                f"The frontier stands at floor {frontier}.",
        body_lines=lines,
        options=[Option("town", "Back to the square")],
        meters=meters(p),
    )


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
    # the Warden answers — one counter-swing per strike
    back_raw = state.rng_int(p, atk_w // 2, atk_w)
    back = max(0, back_raw - state.dfs(p) // 2)
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
