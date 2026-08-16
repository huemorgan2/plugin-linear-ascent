"""032: the banner hall — a faction's home behind the Guildhall.

The Guildhall keeps the town's civic business; every member action lives
here now, app-style: THE COFFER, THE CHEST, THE BULLETIN BOARD, THE
BUNKS, THE WORKS and THE DESK — each its own scene behind
p["hall_area"], exactly the way the founding wizard rides
p["founding_guild"]. worldd injects the numbers as w["faction"]["hall"]
({room_tier, coffer, chest, beds, notes, works}); when the key is absent
(an older world) none of these doors exist and the Guildhall keeps its
010 member panel — the engine never invents hall numbers.

The 010 law stands untouched: gold goes into the coffer from members and
out only to the world (entries, furnishings). Nobody pockets the store.
"""

from __future__ import annotations

from .. import economy
from . import state
from .combat import _ledger, meters
from .scene import Option, Scene
from .social import _effect, world

# 032 §4: four rooms, bought tier by tier, never granted, never
# downgraded. The tier name doubles as the hall home's eyebrow location.
ROOM_TIER_NAMES = {1: "the back room", 2: "a hall of your own",
                   3: "the long hall", 4: "the high hall"}

DONATE_PRESETS = (10, 50, 100)      # 032 §5: presets one tap, custom an ask
NOTE_MAX = 64                        # 032 §7: one line, one member, one day

# THE WORKS: worldd injects priced upgrade rows keyed by kind
# ({kind, tier, price, label, affordable}); the kind maps onto the
# effect the host executes. Ids already shaped like effects pass through.
_WORK_EFFECTS = {
    "room": "hall_room_buy", "room_buy": "hall_room_buy",
    "coffer": "hall_coffer_up", "coffer_up": "hall_coffer_up",
    "chest": "hall_chest_up", "chest_up": "hall_chest_up",
    "bed": "hall_bed_buy", "bed_buy": "hall_bed_buy",
}


def _work_id(wrow: dict) -> str:
    return str(wrow.get("id") or wrow.get("kind") or "")

_DOOR_IDS = ("hall_coffer", "hall_chest", "hall_board", "hall_bunks",
             "hall_works", "hall_desk")

# option art for the doors — 1-bit masks, generated in the art phase;
# a missing file degrades to a plain text row.
_DOOR_ART = {oid: oid for oid in _DOOR_IDS if oid != "hall_desk"}

_STATE_KEYS = ("hall_area", "hall_ask", "hall_putting", "hall_kicking",
               "hall_promoting")


def tier_name(t) -> str:
    try:
        return ROOM_TIER_NAMES.get(int(t or 1), ROOM_TIER_NAMES[1])
    except (TypeError, ValueError):
        return ROOM_TIER_NAMES[1]


def progress_bar(cur: int, target: int, cells: int = 10) -> str:
    """The week's wound-bar grammar: full only when truly full."""
    frac = max(0, cur) / max(1, target)
    filled = round(cells * min(1.0, frac))
    if cur > 0:
        filled = max(1, filled)
    if cur < target:
        filled = min(cells - 1, filled)
    return "▓" * filled + "░" * (cells - filled)


def data(p: dict):
    """(faction, hall) — hall is None on an old world; every caller
    degrades on that (wire law: absent keys mean an older worldd)."""
    w = world(p) or {}
    fac = w.get("faction")
    if not isinstance(fac, dict):
        return None, None
    h = fac.get("hall")
    return fac, (h if isinstance(h, dict) else None)


def clear_state(p: dict) -> None:
    for k in _STATE_KEYS:
        p.pop(k, None)


def enter(p: dict) -> Scene:
    """Walk in — from the square's door or the Guildhall's warm row."""
    clear_state(p)
    p["location"] = "hall"
    return hall_scene(p)


def _eyebrow(fac: dict, hall: dict | None, sub: str = "") -> str:
    """Every hall scene wears the faction's name — EMBER PACT · THE
    COFFER — never a generic ROOTHOLLOW."""
    name = str(fac.get("name", "")).upper()
    if not sub:
        sub = tier_name((hall or {}).get("room_tier", 1)).upper()
    return f"{name} · {sub}"


def _coffer_nums(fac: dict, hall: dict) -> tuple[int, int]:
    c = hall.get("coffer") or {}
    return (int(c.get("bal", fac.get("store", 0)) or 0),
            int(c.get("cap", 0) or 0))


def _note_line(n: dict) -> str:
    day = int(n.get("day", n.get("world_day", 0)) or 0)
    who = str(n.get("player", n.get("name", "?")) or "?")
    return f"DAY {day} · {who} — {str(n.get('line', ''))}"


# ── The scenes ───────────────────────────────────────────────────────────

def hall_scene(p: dict, note: str = "") -> Scene:
    fac, hall = data(p)
    if fac is None or hall is None:
        # an old world, or the colors were folded — the Guildhall takes over
        from . import social
        clear_state(p)
        p["location"] = "guildhall"
        return social.guildhall_scene(p, note=note)
    if p.get("hall_kicking"):
        return _kick_prompt(p, fac, hall, note)
    if p.get("hall_promoting"):
        return _promote_prompt(p, fac, hall, note)
    area = p.get("hall_area")
    if area == "coffer":
        return _coffer_scene(p, fac, hall, note)
    if area == "chest":
        if p.get("hall_putting"):
            return _chest_put_scene(p, fac, hall, note)
        return _chest_scene(p, fac, hall, note)
    if area == "board":
        return _bulletin_scene(p, fac, hall, note)
    if area == "bunks":
        return _bunks_scene(p, fac, hall, note)
    if area == "works":
        return _works_scene(p, fac, hall, note)
    if area == "desk":
        return _desk_scene(p, fac, hall, note)
    return _home_scene(p, fac, hall, note)


_GOAL_VERB = {"hoard": "earn ◈ {t:,} of gold together",
              "cull": "fell {t:,} monsters together",
              "climb": "win {t:,} XP together"}
_GOAL_UNIT = {"hoard": "◈", "cull": "kills", "climb": "XP"}


def _pct(x: float) -> str:
    return f"{x * 100:.0f}%"


def _week_lines(fac: dict, hall: dict, lines: list, opts: list) -> None:
    """032 §9 / 062: THE WEEK box — the loudest thing on the page. One
    solid box (▜ markers) that says the goal, the days left, how far the
    banner is, and — in the prize's own arithmetic — what meeting it
    pays: the pool is base% × target, scaled by attendance (member
    act-days over the 4 needed each): under half → nothing, every day
    all week → ×1.75. Not entered → the same box plus the way in as a
    proper option row (019 law), never prose."""
    wk = fac.get("week") or {}
    kind = str(wk.get("kind", "hoard")).lower()
    bal, _cap = _coffer_nums(fac, hall)
    target = max(1, int(wk.get("target", 0) or 0))
    prog = int(wk.get("progress", 0) or 0)
    att = int(wk.get("attended", 0) or 0)
    req = int(wk.get("required", 0) or 0)
    base = float(wk.get("base_pct", 0) or 0) or (
        0.15 if len(fac.get("members", [])) <= 3 else 0.20)
    entered = bool(wk.get("entered"))
    day = state.world_day()
    left = 7 - day % 7
    verb = _GOAL_VERB.get(kind, _GOAL_VERB["hoard"]).format(t=target)
    unit = _GOAL_UNIT.get(kind, "")
    lines.append(f"\u259c THIS WEEK'S GOAL \u2014 {kind.upper()}")
    lines.append(f"Reach {target:,} {unit} \u2014 {verb}")
    lines.append(f"days left: {left}")
    if entered:
        lines.append(f"goal completed {progress_bar(prog, target, 12)} "
                     f"{min(100, round(100 * prog / target))}% "
                     f"({prog:,} / {target:,})")
        if 0 < req <= 14:
            lines.append("attendance " + "\u25aa" * min(att, req)
                         + "\u25ab" * max(0, req - att) + f" {att}/{req}")
        elif req:
            lines.append(f"attendance {att}/{req}")
    else:
        lines.append("goal completed " + "\u2591" * 12
                     + " 0% \u2014 not entered yet")
    # the prize, in its own arithmetic
    if kind == "hoard":
        def prize(m: float) -> str:
            return f"\u25c8 {round(base * target * m):,} split by attendance"
    else:
        buff = "HP" if kind == "cull" else "XP"
        def prize(m: float) -> str:
            return f"+{round(base * m * 100)}% {buff} all next week"
    lines.append("reaching it at half attendance (2 of 4 days each) gets "
                 f"all faction members {prize(0.5)}")
    lines.append("reaching it at full attendance (4 days each) gets "
                 f"all faction members {prize(1.0)}")
    lines.append("reaching it with everyone in every day gets "
                 f"all faction members {prize(1.75)}")
    lines.append("under half attendance the week pays nothing")
    if entered:
        lines.append(f"on pace for \u00d7{float(wk.get('multiplier', 0)):.2f}"
                     " \u2014 the prize is minted at week's turn")
    lines.append("\u259c.")
    if entered:
        return
    cost = int(wk.get("entry_cost", 0) or 0)
    if fac.get("role") == "steward":
        opts.append(Option("enter_week", "ENTER THE WEEK",
                           f"\u25c8 {cost} from the coffer (\u25c8 {bal:,})"))
    else:
        lines.append("the steward signs the faction in \u2014 nudge them")


def _hands_tag(m: dict) -> str:
    """048: the tenth rank is toasted in every banner hall — a member
    row wears the glyph for each rank-10 path, MASTER once studied."""
    tr = m.get("training") or {}
    ms = m.get("mastery") or {}
    marks = []
    for glyph, path in (("⚔", "blade"), ("➶", "bow"), ("✦", "staff")):
        try:
            r = int(tr.get(path) or 0)
        except (TypeError, ValueError):
            r = 0
        if r >= 10:
            marks.append(f"{glyph} {'MASTER' if ms.get(path) else 'GOLD'}")
    return f" · {' '.join(marks)}" if marks else ""


def _roster_lines(p: dict, fac: dict, lines: list) -> None:
    from .social import _pips
    for m in fac.get("members", [])[:8]:
        tag = ""
        if m.get("founder"):
            tag = " · ★ founder"
        elif m.get("role") == "steward":
            tag = " · steward"
        arr = " ▲ arrears" if m.get("arrears") else ""
        lines.append(f"{m.get('name', '?')}{tag}{_hands_tag(m)} — "
                     f"{_pips(m.get('days', 0), m.get('required', 4))}{arr}")


def _home_scene(p: dict, fac: dict, hall: dict, note: str = "") -> Scene:
    w = world(p) or {}
    lines = note.split("\n") if note else []
    opts: list[Option] = []
    steward = fac.get("role") == "steward"
    tier = int(hall.get("room_tier", 1) or 1)
    bal, cap = _coffer_nums(fac, hall)
    chest = hall.get("chest") or {}
    used = int(chest.get("used", len(w.get("armory") or [])) or 0)
    slots = int(chest.get("cap", w.get("armory_cap", 4)) or 4)
    beds = hall.get("beds") or {}
    notes = hall.get("notes") or []

    _week_lines(fac, hall, lines, opts)
    if notes:
        lines.append(_note_line(notes[0]))

    # the doors — every area its own scene, the forge way
    opts.append(Option("hall_coffer", "THE COFFER",
                       f"◈ {bal:,} of ◈ {cap:,}" if cap else f"◈ {bal:,}"))
    opts.append(Option("hall_chest", "THE CHEST", f"{used} of {slots} slots"))
    opts.append(Option("hall_board", "THE BULLETIN BOARD",
                       f"{len(notes)} line{'s' if len(notes) != 1 else ''}"))
    if tier >= 2:
        cnt = int(beds.get("count", 0) or 0)
        claimed = len(beds.get("tonight") or [])
        opts.append(Option("hall_bunks", "THE BUNKS",
                           f"{cnt} bed{'s' if cnt != 1 else ''}, "
                           f"{claimed} claimed"))
    else:
        # 019: the gated door is a dimmed row, not a missing one
        opts.append(Option("hall_bunks", "THE BUNKS",
                           "🔒 beds fit from a hall of your own",
                           locked=True))
    opts.append(Option("hall_works", "THE WORKS", "buy up the hall"))
    if steward:
        pend = int(fac.get("pending_requests", 0) or 0)
        opts.append(Option("hall_desk", "THE DESK",
                           (f"{pend} ask to join" if pend
                            else "requests and the name"),
                           badge=pend))
    _roster_lines(p, fac, lines)
    if steward and len(fac.get("members", [])) > 1:
        opts.append(Option("kick", "Remove a member"))
        if any(m.get("role") != "steward" and m.get("name") != p.get("name")
               for m in fac.get("members", [])):
            opts.append(Option("promote", "Raise a member to steward"))
    opts.append(Option("guild_leave", "Leave the faction"))
    opts.append(Option("town", "Back to the square"))
    return Scene(
        eyebrow=_eyebrow(fac, hall),
        headline=f"The {fac.get('name', '?')} table",
        support="Your colors over your own roof. What the dues bought.",
        body_lines=lines,
        options=opts,
        meters=meters(p),
        banner=str(fac.get("banner") or "") or "guildhall",
        strip={"art": f"hall_room_{tier}", "text": tier_name(tier)},
        option_art=dict(_DOOR_ART),
    )


# ── THE COFFER (032 §5) ──────────────────────────────────────────────────

def _coffer_scene(p: dict, fac: dict, hall: dict, note: str = "") -> Scene:
    bal, cap = _coffer_nums(fac, hall)
    if p.get("hall_ask") == "donate":
        return Scene(
            eyebrow=_eyebrow(fac, hall, "THE COFFER"),
            headline="A sum of your naming",
            support=f"You carry ◈ {p['gold']:,}. Carried gold only; the "
                    "coffer takes what fits.",
            body_lines=[note] if note else [],
            options=[Option("hall_cancel", "Never mind")],
            meters=meters(p),
            awaits_text="the donation amount — a number in carried gold",
            ask={"kind": "number", "min": 1, "max": max(1, int(p["gold"])),
                 "label": "into the coffer, in carried gold",
                 "placeholder": "0", "submit": "DONATE"},
        )
    lines = note.split("\n") if note else []
    if cap:
        lines.append(f"◈ {bal:,} of ◈ {cap:,}"
                     + (" — full to the brim" if bal >= cap else ""))
        lines.append(progress_bar(bal, cap, 12))
    else:
        lines.append(f"◈ {bal:,} in the box")
    for row in (fac.get("ledger") or [])[:8]:
        if isinstance(row, dict):
            amt = int(row.get("amount", row.get("gold", 0)) or 0)
            tail = str(row.get("note", "") or "")
            lines.append(f"· {row.get('kind', '?')} "
                         f"{'+' if amt >= 0 else '−'}◈ {abs(amt):,}"
                         + (f" — {tail}" if tail else ""))
        else:
            lines.append(f"· {row}")
    opts = [Option(f"donate_{a}", f"Donate ◈ {a}", "carried ◈")
            for a in DONATE_PRESETS]
    opts.append(Option("donate_custom", "A sum of your naming", "carried ◈"))
    opts.append(Option("hall_home", "Back to the hall"))
    return Scene(
        eyebrow=_eyebrow(fac, hall, "THE COFFER"),
        headline=f"The coffer holds ◈ {bal:,}",
        support="Every coin in is the faction's for good — it leaves only "
                "to the world, never to a pocket.",
        body_lines=lines,
        options=opts,
        meters=meters(p),
        banner=str(fac.get("banner") or ""),
    )


def _donate(p: dict, amt: int, fac: dict, hall: dict) -> Scene:
    bal, cap = _coffer_nums(fac, hall)
    if amt <= 0:
        return hall_scene(p, note="The coffer takes numbers, not speeches.")
    if p["gold"] < amt:
        return hall_scene(p, note=f"You carry ◈ {p['gold']:,} — "
                                  f"not ◈ {amt:,}.")
    space = (cap - bal) if cap else amt
    if space <= 0:
        return hall_scene(
            p, note=f"The coffer is full — ◈ {bal:,} of ◈ {cap:,}. "
                    "The works sell a bigger one.")
    give = min(amt, space)
    p["gold"] -= give
    _ledger(p, "faction_donation", gold=-give, note=fac.get("name", ""))
    _effect(p, "faction_donate", amount=give)
    coffer = hall.setdefault("coffer", {})
    coffer["bal"] = bal + give
    fac["store"] = int(fac.get("store", 0) or 0) + give
    if give < amt:
        # 032 §5: clip to the brim — nothing is burned out of a pocket
        return hall_scene(
            p, note=f"+ the coffer takes ◈ {give:,} of your ◈ {amt:,} — "
                    "it is full")
    return hall_scene(p, note=f"+ ◈ {give:,} into the coffer — "
                              f"◈ {bal + give:,} of ◈ {cap:,} now")


# ── THE CHEST (032 §6 — the armory, reborn as a card wall) ──────────────

def _donatable(p: dict) -> list[str]:
    inv = p.get("inventory") or {}
    return [k for k, n in inv.items()
            if n > 0 and k in economy.FORGE and economy.FORGE[k].price > 0]


def _chest_scene(p: dict, fac: dict, hall: dict, note: str = "") -> Scene:
    w = world(p) or {}
    rack = w.get("armory") or []
    chest = hall.get("chest") or {}
    cap = int(chest.get("cap", w.get("armory_cap", 4)) or 4)
    used = len(rack)
    took = bool(w.get("armory_took_today"))
    lines = note.split("\n") if note else []
    opts: list[Option] = []
    art: dict[str, str] = {}
    for it in rack:
        try:
            iid = int(it.get("id", -1) or -1)
        except (TypeError, ValueError):
            continue
        if iid < 0:
            continue        # optimistic deposit — worldd stamps the id
        worn = (f" · worn to {round(it.get('frac', 1.0) * 100)}%"
                if it.get("frac", 1.0) < 1.0 else "")
        oid = f"take_arm_{iid}"
        opts.append(Option(oid, str(it.get("name", "?")),
                           f"from {it.get('donor', 'a member')}{worn}"))
        if it.get("slug"):
            art[oid] = str(it["slug"])
    open_slots = max(0, cap - used)
    if open_slots:
        # the bought capacity is VISIBLE — dark sockets, the pack way
        lines.append("▫ " * open_slots
                     + f"— {open_slots} open socket"
                       f"{'s' if open_slots != 1 else ''} of {cap}")
    else:
        lines.append(f"every socket filled — {used} of {cap}. "
                     "The works sell a bigger chest.")
    if took and rack:
        lines.append("you already took your piece today — the racks "
                     "open again tomorrow")
    donatable = _donatable(p)
    if donatable and open_slots:
        opts.append(Option("chest_put", "PUT IN — from your pack",
                           f"{len(donatable)} piece"
                           f"{'s' if len(donatable) != 1 else ''} fit"))
    elif donatable:
        opts.append(Option("chest_put", "PUT IN — from your pack",
                           "🔒 every socket filled", locked=True))
    opts.append(Option("hall_home", "Back to the hall"))
    return Scene(
        eyebrow=_eyebrow(fac, hall, "THE CHEST"),
        headline=f"{used} of {cap} slots hold steel",
        support="No coin crosses this lid — wear rides through, one take "
                "a day, and the donor's name stays on the piece.",
        body_lines=lines,
        options=opts,
        meters=meters(p),
        grid=True,
        option_art=art,
    )


def _chest_take(p: dict, raw_id: str, fac: dict, hall: dict) -> Scene:
    """017 law intact: member-only, one take per player per world-day,
    wear rides through, no gold anywhere in the loop."""
    w = world(p) or {}
    rack = w.get("armory")
    if rack is None:
        return hall_scene(p)
    if w.get("armory_took_today"):
        return hall_scene(
            p, note="One piece a day — the racks open again tomorrow.")
    try:
        item_id = int(raw_id)
    except ValueError:
        return hall_scene(p)
    it = next((x for x in rack if int(x.get("id", -1)) == item_id), None)
    if it is None:
        return hall_scene(p, note="That piece already left the rack.")
    _effect(p, "armory_take", item_id=item_id)
    w["armory"] = [x for x in rack if int(x.get("id", -1)) != item_id]
    w["armory_took_today"] = True
    chest = hall.get("chest") or {}
    if "used" in chest:
        chest["used"] = max(0, int(chest["used"]) - 1)
    worn = (f" — worn to {round(it.get('frac', 1.0) * 100)}%"
            if it.get("frac", 1.0) < 1.0 else "")
    return hall_scene(
        p, note=f"+ the {it['name']} comes out of the chest into your "
                f"pack{worn}. {it.get('donor', 'a member')} put it there.")


def _chest_put_scene(p: dict, fac: dict, hall: dict,
                     note: str = "") -> Scene:
    opts: list[Option] = []
    art: dict[str, str] = {}
    for slug in _donatable(p):
        g = economy.FORGE[slug]
        oid = f"put_{slug}"
        # 011: the card says WHAT leaves the pack — stat, durability
        # (worn pieces show left-of-full), style — before the law line.
        left = (p.get("durability_pack") or {}).get(slug)
        opts.append(Option(
            oid, g.name,
            f"{economy.gear_card_stats(g, left)} · "
            "no coin — the faction keeps it"))
        art[oid] = slug
    opts.append(Option("hall_cancel", "Never mind"))
    return Scene(
        eyebrow=_eyebrow(fac, hall, "THE CHEST"),
        headline="What goes in the chest?",
        support="The wear rides with the piece — the chest launders "
                "nothing.",
        body_lines=[note] if note else [],
        options=opts,
        meters=meters(p),
        grid=True,
        option_art=art,
    )


def _chest_put(p: dict, slug: str, fac: dict, hall: dict) -> Scene:
    w = world(p) or {}
    g = economy.FORGE.get(slug)
    rack = w.get("armory")
    if (g is None or g.price <= 0 or rack is None
            or (p.get("inventory") or {}).get(slug, 0) <= 0):
        return hall_scene(p)
    chest = hall.get("chest") or {}
    cap = int(chest.get("cap", w.get("armory_cap", 4)) or 4)
    if len(rack) >= cap:
        return hall_scene(
            p, note=f"Every socket is filled — {len(rack)} of {cap}. "
                    "The works sell a bigger chest.")
    p["inventory"][slug] -= 1
    if p["inventory"][slug] <= 0:
        del p["inventory"][slug]
    uses = (p.get("durability_pack") or {}).pop(slug, None)
    _effect(p, "armory_deposit", slug=slug, uses_left=uses)
    _ledger(p, "armory_give", gold=0, note=slug)
    # optimistic: the socket fills; worldd stamps the real row id
    rack.append({"id": -1, "slug": slug, "name": g.name,
                 "donor": p.get("name") or "you", "frac": 1.0})
    if "used" in chest:
        chest["used"] = int(chest["used"]) + 1
    return hall_scene(
        p, note=f"+ the {g.name} goes into the chest — the faction keeps "
                "it now, your name on the socket.")


# ── THE BULLETIN BOARD (032 §7) ─────────────────────────────────────────

def _bulletin_scene(p: dict, fac: dict, hall: dict,
                    note: str = "") -> Scene:
    if p.get("hall_ask") == "note":
        return Scene(
            eyebrow=_eyebrow(fac, hall, "THE BULLETIN BOARD"),
            headline="One line for the board",
            support=f"{NOTE_MAX} letters, plain words. One note a day — "
                    "writing again replaces it.",
            body_lines=[note] if note else [],
            options=[Option("hall_cancel", "Never mind")],
            meters=meters(p),
            awaits_text="the note — one short line",
            ask={"kind": "text", "max": NOTE_MAX,
                 "label": "your line on the board",
                 "placeholder": "say it short", "submit": "PIN IT"},
        )
    lines = note.split("\n") if note else []
    notes = hall.get("notes") or []
    for n in notes[:20]:
        lines.append(_note_line(n))
    if not notes:
        lines.append("The board hangs empty — nails and no news.")
    opts = [Option("write_note", "WRITE A LINE",
                   f"free · {NOTE_MAX} letters"),
            Option("hall_home", "Back to the hall")]
    return Scene(
        eyebrow=_eyebrow(fac, hall, "THE BULLETIN BOARD"),
        headline=f"{len(notes)} line{'s' if len(notes) != 1 else ''} "
                 "on the nails",
        support="The newest line sits over the hall door until someone "
                "out-writes it.",
        body_lines=lines,
        options=opts,
        meters=meters(p),
    )


# ── THE BUNKS (032 §8 — a free safe night) ──────────────────────────────

def _bunks_scene(p: dict, fac: dict, hall: dict, note: str = "") -> Scene:
    beds = hall.get("beds") or {}
    cnt = int(beds.get("count", 0) or 0)
    tonight = [str(x) for x in (beds.get("tonight") or [])]
    lines = note.split("\n") if note else []
    opts: list[Option] = []
    if cnt:
        open_ = max(0, cnt - len(tonight))
        lines.append("tonight: "
                     + (", ".join(tonight) if tonight else "no one yet")
                     + f" — {open_} bed{'s' if open_ != 1 else ''} open")
        lines.append("a faction bed buys the same night the Lodge sells — "
                     "nothing finds you before dawn. Free; the dues "
                     "bought it.")
        opts.append(Option("bed_claim", "SLEEP HERE TONIGHT",
                           "free — first come, first bunked"))
    else:
        lines.append("No beds yet — the works sell them, ◈ 250 a frame.")
    opts.append(Option("hall_home", "Back to the hall"))
    return Scene(
        eyebrow=_eyebrow(fac, hall, "THE BUNKS"),
        headline=f"{cnt} bed{'s' if cnt != 1 else ''} against the wall",
        support="One claim a night, by name. Dawn still heals everyone — "
                "the bunk decides who FINDS you first.",
        body_lines=lines,
        options=opts,
        meters=meters(p),
    )


def _bed_claim(p: dict, fac: dict, hall: dict) -> Scene:
    beds = hall.get("beds") or {}
    cnt = int(beds.get("count", 0) or 0)
    tonight = [str(x) for x in (beds.get("tonight") or [])]
    me = p.get("name") or ""
    if cnt <= 0:
        return hall_scene(p)
    if me and me in tonight:
        return hall_scene(
            p, note="You already hold a bunk tonight — one claim a night.")
    if p.get("lodged_until_day", 0) >= state.world_day() + 1:
        return hall_scene(
            p, note="Tonight is already paid for — leave the bed to a "
                    "colder back.")
    if len(tonight) >= cnt:
        first = ", ".join(tonight[:4])
        return hall_scene(
            p, note=f"Every bed is claimed tonight — {first} got here "
                    "first. The Lodge still sells walls.")
    _effect(p, "hall_bed_claim")
    # the SAME flag the Lodge sells — PvP target selection already honors it
    p["lodged_until_day"] = state.world_day() + 1
    tonight.append(me or "you")
    beds["tonight"] = tonight
    hall["beds"] = beds
    _ledger(p, "hall_bed", gold=0, note=fac.get("name", ""))
    return hall_scene(
        p, note="+ a bunk is yours till dawn — nothing finds you under "
                "the faction's roof.")


# ── THE WORKS (032 §4/§5/§6/§8 — the coffer's sinks) ────────────────────

def _works_scene(p: dict, fac: dict, hall: dict, note: str = "") -> Scene:
    bal, _cap = _coffer_nums(fac, hall)
    steward = fac.get("role") == "steward"
    lines = note.split("\n") if note else []
    lines.append(f"Paid from the coffer — ◈ {bal:,} in it. Bought, never "
                 "granted; never downgraded.")
    if not steward:
        lines.append("the works answer to the steward's hand — yours to "
                     "read, theirs to buy")
    opts: list[Option] = []
    works = hall.get("works") or []
    for wrow in works:
        if not isinstance(wrow, dict):
            continue
        wid = _work_id(wrow)
        price = int(wrow.get("price", 0) or 0)
        afford = bool(wrow.get("affordable", price <= bal))
        # 019 law: a priced row, live or locked — never prose-only
        hint = (f"◈ {price:,} from the coffer" if afford
                else f"🔒 ◈ {price:,} — the coffer holds ◈ {bal:,}")
        opts.append(Option(f"work_{wid}", str(wrow.get("label", wid)),
                           hint, locked=not afford))
    if not works:
        lines.append("Nothing left to buy — the hall stands finished.")
    opts.append(Option("hall_home", "Back to the hall"))
    return Scene(
        eyebrow=_eyebrow(fac, hall, "THE WORKS"),
        headline="Buy up the hall",
        support="Coffer gold goes to the world and never back to a "
                "pocket — the 010 law, kept.",
        body_lines=lines,
        options=opts,
        meters=meters(p),
    )


def _work_buy(p: dict, wid: str, fac: dict, hall: dict) -> Scene:
    works = hall.get("works") or []
    wrow = next((x for x in works
                 if isinstance(x, dict) and _work_id(x) == wid), None)
    if wrow is None:
        return hall_scene(p)
    label = str(wrow.get("label", wid))
    if fac.get("role") != "steward":
        s = hall_scene(
            p, note="The works answer to the steward's hand — nudge them.")
        s.refusal = "Can't buy this — only the steward buys works"
        return s
    bal, _cap = _coffer_nums(fac, hall)
    price = int(wrow.get("price", 0) or 0)
    if price > bal or not wrow.get("affordable", True):
        s = hall_scene(
            p, note=f"The {label} takes ◈ {price:,} and the coffer holds "
                    f"◈ {bal:,} — ◈ {max(0, price - bal):,} short. Dues "
                    "land at week's turn, or pass the hat.")
        s.refusal = (f"Can't buy this — the coffer is "
                     f"◈ {max(0, price - bal):,} short")
        return s
    kind = wid if wid.startswith("hall_") \
        else _WORK_EFFECTS.get(wid, f"hall_{wid}")
    _effect(p, kind)
    coffer = hall.setdefault("coffer", {})
    coffer["bal"] = bal - price
    fac["store"] = max(0, int(fac.get("store", 0) or 0) - price)
    hall["works"] = [x for x in works
                     if not isinstance(x, dict) or _work_id(x) != wid]
    if kind == "hall_room_buy":
        hall["room_tier"] = int(hall.get("room_tier", 1) or 1) + 1
    elif kind == "hall_bed_buy":
        beds = hall.setdefault("beds", {})
        beds["count"] = int(beds.get("count", 0) or 0) + 1
    return hall_scene(
        p, note=f"+ {label} — ◈ {price:,} from the coffer, gone to the "
                "world. The hall keeps what it buys.")


# ── THE DESK (032 §2 — requests and the name, in the hall) ──────────────

def _requests(fac: dict, hall: dict) -> list[dict]:
    """Injected request rows, wherever the world put them. Absent on an
    older worldd — the desk then points at the Community mirror."""
    for src in (hall, fac):
        v = src.get("requests")
        if isinstance(v, list):
            return v
    return []


def _desk_scene(p: dict, fac: dict, hall: dict, note: str = "") -> Scene:
    if p.get("hall_ask") == "rename":
        return Scene(
            eyebrow=_eyebrow(fac, hall, "THE DESK"),
            headline="New colors for everyone",
            support="3 to 24 letters. Every list, every sigil caption "
                    "learns it at once.",
            body_lines=[note] if note else [],
            options=[Option("hall_cancel", "Never mind")],
            meters=meters(p),
            awaits_text="the faction's new name",
            ask={"kind": "text", "max": 24, "label": "the faction's new name",
                 "placeholder": str(fac.get("name", "")),
                 "submit": "RENAME"},
        )
    lines = note.split("\n") if note else []
    opts: list[Option] = []
    reqs = _requests(fac, hall)
    fee = int(fac.get("join_fee", 0) or 0)
    if reqs:
        for i, r in enumerate(reqs[:8]):
            nm = str(r.get("name") or r.get("player") or "?")
            lines.append(f"{nm} — L{int(r.get('level', 1) or 1)}, asked "
                         f"day {int(r.get('requested_day', 0) or 0)}")
            opts.append(Option(f"req_ok_{i}", f"Take {nm} in",
                               f"◈ {fee} join fee charged" if fee
                               else "no join fee"))
            opts.append(Option(f"req_no_{i}", f"Turn {nm} away"))
    else:
        pend = int(fac.get("pending_requests", 0) or 0)
        if pend:
            lines.append(f"{pend} request{'s' if pend != 1 else ''} wait — "
                         "their papers hang at the Community desk")
        else:
            lines.append("No one waits at the desk.")
    opts.append(Option("rename_banner", "Rename the faction",
                       "3–24 letters — new colors for everyone"))
    opts.append(Option("hall_home", "Back to the hall"))
    return Scene(
        eyebrow=_eyebrow(fac, hall, "THE DESK"),
        headline="The steward's desk",
        support="Who sits at the table, and what the table is called.",
        body_lines=lines,
        options=opts,
        meters=meters(p),
    )


def _req_act(p: dict, oid: str, fac: dict, hall: dict) -> Scene:
    ok = oid.startswith("req_ok_")
    try:
        i = int(oid.rsplit("_", 1)[1])
    except ValueError:
        return hall_scene(p)
    reqs = _requests(fac, hall)
    if not 0 <= i < len(reqs):
        return hall_scene(p)
    r = reqs.pop(i)
    fac["pending_requests"] = max(
        0, int(fac.get("pending_requests", 0) or 0) - 1)
    nm = str(r.get("name") or r.get("player") or "?")
    _effect(p, "faction_approve" if ok else "faction_reject",
            tenant=str(r.get("tenant", "")), player=str(r.get("player", "")))
    if ok:
        return hall_scene(
            p, note=f"+ {nm} gets a chair — the join fee lands in the "
                    "coffer as they sit.")
    return hall_scene(
        p, note=f"+ {nm}'s paper comes off the desk. The tower is wide.")


# ── roster prompts (kick / promote, moved home from the Guildhall) ──────

def _kick_prompt(p: dict, fac: dict, hall: dict, note: str = "") -> Scene:
    from .social import _pips
    opts = []
    for m in fac.get("members", [])[:8]:
        nm = m.get("name", "?")
        if nm != p.get("name"):
            arr = " · arrears" if m.get("arrears") else ""
            pips = _pips(m.get("days", 0), m.get("required", 4))
            opts.append(Option(f"kick_{nm}", f"Remove {nm}", f"{pips}{arr}"))
    opts.append(Option("hall_cancel", "Never mind"))
    return Scene(
        eyebrow=_eyebrow(fac, hall),
        headline="Who leaves the table?",
        support="Kicking a no-show lifts their dead weight off the "
                "attendance ratio.",
        body_lines=[note] if note else [],
        options=opts,
        meters=meters(p),
    )


def _promote_prompt(p: dict, fac: dict, hall: dict,
                    note: str = "") -> Scene:
    opts = []
    for m in fac.get("members", [])[:8]:
        nm = m.get("name", "?")
        if nm != p.get("name") and m.get("role") != "steward":
            opts.append(Option(f"promote_{nm}", f"Raise {nm} to steward",
                               "keys to the desk and the works"))
    opts.append(Option("hall_cancel", "Never mind"))
    return Scene(
        eyebrow=_eyebrow(fac, hall),
        headline="Who keeps the keys?",
        support="A steward enters the week, buys the works and runs "
                "the desk.",
        body_lines=[note] if note else [],
        options=opts,
        meters=meters(p),
    )


# ── the week's entry, from the hall ─────────────────────────────────────

def _enter_week(p: dict, fac: dict, hall: dict) -> Scene:
    wk = fac.get("week") or {}
    if fac.get("role") != "steward":
        return hall_scene(
            p, note="the steward signs the faction in — nudge them")
    if wk.get("entered"):
        return hall_scene(
            p, note="Your faction is already in this week's lists.")
    cost = int(wk.get("entry_cost", 0) or 0)
    bal, _cap = _coffer_nums(fac, hall)
    if bal < cost:
        return hall_scene(
            p, note=f"The entry is ◈ {cost} and the coffer holds "
                    f"◈ {bal} — ◈ {cost - bal} short. Dues land at "
                    "week's turn, or pass the hat.")
    _effect(p, "faction_enter")
    wk["entered"] = True
    coffer = hall.setdefault("coffer", {})
    coffer["bal"] = bal - cost
    fac["store"] = max(0, int(fac.get("store", 0) or 0) - cost)
    return hall_scene(
        p, note=f"+ ◈ {cost} from the coffer — the "
                f"{str(wk.get('kind', '')).upper()} is on. Everything "
                "the table earns this week counts.")


# ── dispatch ─────────────────────────────────────────────────────────────

def hall_action(p: dict, oid: str) -> Scene:
    fac, hall = data(p)
    if fac is None or hall is None:
        from . import social
        clear_state(p)
        p["location"] = "guildhall"
        return social.guildhall_action(p, oid)
    if p.get("hall_kicking"):
        p.pop("hall_kicking", None)
        if oid.startswith("kick_"):
            target = oid.removeprefix("kick_")
            _effect(p, "faction_kick", name=target)
            fac["members"] = [m for m in fac.get("members", [])
                              if m.get("name") != target]
            return hall_scene(
                p, note=f"+ {target}'s chair scrapes back. The table "
                        "moves on.")
        return hall_scene(p)
    if p.get("hall_promoting"):
        p.pop("hall_promoting", None)
        if oid.startswith("promote_"):
            target = oid.removeprefix("promote_")
            _effect(p, "faction_promote", name=target)
            for m in fac.get("members", []):
                if m.get("name") == target:
                    m["role"] = "steward"
            return hall_scene(
                p, note=f"+ {target} keeps the keys now too — two hands "
                        "on the desk.")
        return hall_scene(p)
    if p.get("hall_ask"):
        p.pop("hall_ask", None)
        return hall_scene(p, note="Never mind, then."
                          if oid == "hall_cancel" else "")
    if p.get("hall_putting"):
        p.pop("hall_putting", None)
        if oid.startswith("put_"):
            return _chest_put(p, oid.removeprefix("put_"), fac, hall)
        return hall_scene(p)
    if oid == "hall_home":
        p.pop("hall_area", None)
        return hall_scene(p)
    if oid in _DOOR_IDS:
        area = oid.removeprefix("hall_")
        if area == "bunks" and int(hall.get("room_tier", 1) or 1) < 2:
            return hall_scene(
                p, note="Beds fit from a hall of your own up — the works "
                        "sell the room for ◈ 500.")
        if area == "desk" and fac.get("role") != "steward":
            return hall_scene(
                p, note="The desk answers to the steward's hand.")
        p["hall_area"] = area
        return hall_scene(p)
    if oid == "enter_week":
        return _enter_week(p, fac, hall)
    if oid == "guild_leave":
        from . import social
        clear_state(p)
        p["location"] = "guildhall"
        return social.guildhall_action(p, "guild_leave")
    if oid == "donate_custom":
        p["hall_ask"] = "donate"
        return hall_scene(p)
    if oid.startswith("donate_"):
        try:
            amt = int(oid.removeprefix("donate_"))
        except ValueError:
            return hall_scene(p)
        return _donate(p, amt, fac, hall)
    if oid.startswith("take_arm_"):
        return _chest_take(p, oid.removeprefix("take_arm_"), fac, hall)
    if oid == "chest_put":
        if _donatable(p):
            p["hall_putting"] = True
        return hall_scene(p)
    if oid == "write_note":
        p["hall_ask"] = "note"
        return hall_scene(p)
    if oid == "bed_claim":
        return _bed_claim(p, fac, hall)
    if oid.startswith("work_"):
        return _work_buy(p, oid.removeprefix("work_"), fac, hall)
    if oid.startswith(("req_ok_", "req_no_")):
        return _req_act(p, oid, fac, hall)
    if oid == "rename_banner":
        p["hall_ask"] = "rename"
        return hall_scene(p)
    if oid == "kick" and fac.get("role") == "steward":
        p["hall_kicking"] = True
        return hall_scene(p)
    if oid == "promote" and fac.get("role") == "steward":
        p["hall_promoting"] = True
        return hall_scene(p)
    return hall_scene(p)


def hall_text(p: dict, text: str) -> Scene:
    """Typed replies while a hall ask is open (donate sum, board line,
    the rename) — core routes here on the hall_ask flag."""
    kind = p.pop("hall_ask", None)
    fac, hall = data(p)
    if fac is None or hall is None:
        from . import social
        clear_state(p)
        p["location"] = "guildhall"
        return social.guildhall_scene(p)
    if kind == "donate":
        try:
            amt = int(text.strip().lstrip("◈").replace(",", ""))
        except ValueError:
            return hall_scene(p, note="The coffer takes numbers, not "
                                      "speeches.")
        return _donate(p, amt, fac, hall)
    if kind == "note":
        line = " ".join(text.split())[:NOTE_MAX]
        if not line:
            return hall_scene(p, note="The board takes words — none came.")
        _effect(p, "hall_note", line=line)
        me, day = p.get("name") or "you", state.world_day()
        notes = [n for n in (hall.get("notes") or [])
                 if not (str(n.get("player", "")) == me
                         and int(n.get("day", -1) or -1) == day)]
        notes.insert(0, {"day": day, "player": me, "line": line})
        hall["notes"] = notes[:20]
        return hall_scene(
            p, note="+ your line is pinned — the newest word owns the "
                    "top of the hall.")
    if kind == "rename":
        name = text.strip()[:24]
        if len(name) < 3:
            return hall_scene(p, note="Three letters at least. Factions "
                                      "need room for glory.")
        _effect(p, "faction_rename", name=name)
        old = fac.get("name", "")
        fac["name"] = name
        return hall_scene(
            p, note=f"+ the {old} colors fly as {name} now — every list "
                    "learns it at once.")
    return hall_scene(p)
