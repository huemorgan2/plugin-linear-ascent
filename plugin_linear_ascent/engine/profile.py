"""042: the player profile — any avatar, anywhere, opens this page.

worldd injects `w["profiles"]`: name → payload for everyone in the
viewer's room, on the local boards, and the profile already open. The
engine only reads; every action is the same law as everywhere else —
validate, pay the doc's own costs, emit an effect for the host.

The page shows everything PUBLIC: level, guild and what they gave it,
carried coin, energy, the pack. The bank stays private — code law since
030, the Vault is the one secret the tower keeps.
"""

from __future__ import annotations

import datetime as dt

from .. import economy
from . import state
from .combat import _ledger, meters
from .scene import Option, Scene
from .social import _effect, world

LOOT_COOLDOWN_S = 3600         # one attempt per attacker per target per hour
LOOT_COST = economy.COST_PVP_ATTACK


def open_profile(p: dict, name: str) -> Scene:
    """A tile was clicked — remember where to come back to."""
    if p.get("location") != "profile":
        p["profile_back"] = {"loc": p.get("location"),
                             "floor": int(p.get("floor") or 0)}
    for k in ("profile_pay", "profile_gift", "profile_loot"):
        p.pop(k, None)
    p["profile_view"] = name
    p["location"] = "profile"
    return profile_scene(p)


def close_profile(p: dict) -> None:
    back = p.pop("profile_back", None) or {}
    for k in ("profile_view", "profile_pay", "profile_gift",
              "profile_loot"):
        p.pop(k, None)
    p["location"] = back.get("loc") or "town"
    p["floor"] = int(back.get("floor") or 0)
    if p["location"] == "profile":       # never loop back into the page
        p["location"], p["floor"] = "town", 0


def _payload(p: dict) -> dict | None:
    w = world(p) or {}
    profiles = w.get("profiles")
    name = p.get("profile_view")
    if not isinstance(profiles, dict) or not name:
        return None
    pr = profiles.get(name)
    return pr if isinstance(pr, dict) else None


def _loot_cd_left(p: dict, name: str) -> int:
    """Seconds left on the per-pair cooldown; prunes stale entries."""
    cd = p.get("loot_cd") or {}
    now = state.now()
    keep = {}
    left = 0
    for n, iso in cd.items():
        try:
            ts = dt.datetime.fromisoformat(iso)
        except (ValueError, TypeError):
            continue
        gone = (now - ts).total_seconds()
        if gone < LOOT_COOLDOWN_S:
            keep[n] = iso
            if n == name:
                left = int(LOOT_COOLDOWN_S - gone)
    if keep:
        p["loot_cd"] = keep
    else:
        p.pop("loot_cd", None)
    return left


def profile_scene(p: dict, note: str = "") -> Scene:
    name = str(p.get("profile_view") or "")
    pr = _payload(p)
    if pr is None:
        return _missing_scene(p, name, note)
    if p.get("profile_pay"):
        return _pay_scene(p, pr, note)
    if p.get("profile_gift"):
        return _gift_scene(p, pr, note)
    if p.get("profile_loot"):
        return _loot_confirm_scene(p, pr, note)
    lines = note.split("\n") if note else []
    race = str(pr.get("race") or "").title()
    if race:
        lines.append(race)
    # 048: the classes died — the public page shows the trained hands.
    # Rank 10 reads GOLD, a studied mastery reads MASTER; older worldd
    # payloads carry no training key and the line simply doesn't render.
    tr = pr.get("training") or {}
    if isinstance(tr, dict) and any(
            int(tr.get(k) or 0) for k in ("blade", "bow", "staff")):
        ms = pr.get("mastery") or {}
        parts = []
        for glyph, path in (("⚔", "blade"), ("➶", "bow"), ("✦", "staff")):
            r = int(tr.get(path) or 0)
            word = f"{glyph} {r}"
            if r >= 10:
                word += " MASTER" if ms.get(path) else " GOLD"
            parts.append(word)
        lines.append("hands: " + " · ".join(parts))
    if pr.get("sleeping"):
        lines.append("Asleep — the tower keeps their bunk warm.")
    lines.append(f"carries ◈ {int(pr.get('gold', 0)):,} · "
                 f"⚡ {int(pr.get('energy', 0))}")
    if pr.get("atk") or pr.get("dfs"):
        lines.append(f"ATK {int(pr.get('atk', 0))} · "
                     f"DEF {int(pr.get('dfs', 0))} · "
                     f"HP {int(pr.get('hp', 0))}/{int(pr.get('hp_max', 0))}")
    g = pr.get("guild")
    if g:
        c = pr.get("contribution") or {}
        gave = []
        if int(c.get("coins", 0)):
            gave.append(f"◈ {int(c['coins']):,} coined")
        if int(c.get("items", 0)):
            gave.append(f"{int(c['items'])} piece"
                        f"{'s' if int(c['items']) != 1 else ''} racked")
        if int(c.get("warden", 0)):
            gave.append(f"{int(c['warden']):,} cut from Wardens")
        lines.append(f"flies the {g} banner"
                     + (" — gave " + ", ".join(gave) if gave else ""))
    gear = [str(x) for x in (pr.get("gear") or []) if x]
    if gear:
        lines.append("carries: " + ", ".join(gear[:6]))
    inv = [x for x in (pr.get("inventory") or []) if isinstance(x, dict)]
    if inv:
        packed = ", ".join(
            f"{x.get('name', '?')}"
            + (f" ×{int(x.get('count', 1))}" if int(x.get('count', 1)) > 1
               else "") for x in inv[:8])
        lines.append(f"in the pack: {packed}")
    mins = pr.get("last_seen_min")
    if pr.get("lootable"):
        lines.append("Their camp sits quiet — no move in over an hour.")
    elif isinstance(mins, int):
        lines.append("Active recently — a loot here answers at double "
                     "their strength.")
    opts = []
    price_note = (f"◈ {economy.LETTER_PRICE}" if economy.LETTER_PRICE
                  else "free")
    opts.append(Option("pf_msg", "Send a letter", price_note))
    opts.append(Option("pf_pay", "Send money",
                       f"the Vault burns "
                       f"{int(economy.GRANT_BURN_PCT * 100)}%"))
    if (p.get("inventory") or {}):
        opts.append(Option("pf_gift", "Gift an item", "from your pack"))
    cd = _loot_cd_left(p, name)
    if pr.get("same_guild"):
        opts.append(Option("pf_loot", "Loot their camp",
                           "🔒 not a guildmate", locked=True))
    elif pr.get("protected"):
        opts.append(Option("pf_loot", "Loot their camp",
                           "🔒 under the tower's protection", locked=True))
    elif cd:
        opts.append(Option("pf_loot", "Loot their camp",
                           f"🔒 again in {max(1, cd // 60)}m", locked=True))
    else:
        risk = ("their camp is cold — the odds favor you"
                if pr.get("lootable")
                else "ACTIVE — they strike back at 200%")
        opts.append(Option("pf_loot", "Loot their camp",
                           f"{LOOT_COST} ⚡ · {risk}"))
    opts.append(Option("back", "Step away"))
    tile = {"opt": f"pv:{name}", "name": name,
            "level": int(pr.get("level", 1)),
            "race": str(pr.get("race") or ""),
            "armor": str(pr.get("armor") or ""),
            "sleeping": bool(pr.get("sleeping")),
            "gold": int(pr.get("gold", 0)),
            "energy": int(pr.get("energy", 0))}
    return Scene(
        eyebrow="THE STONE OF NAMES · A CLIMBER'S PAGE",
        headline=f"{name} — LEVEL {int(pr.get('level', 1))}",
        support="Everything the Stone shows is public. The Vault keeps "
                "its one secret.",
        body_lines=lines,
        options=opts,
        meters=meters(p),
        players_here=[tile],
    )


def _missing_scene(p: dict, name: str, note: str = "") -> Scene:
    return Scene(
        eyebrow="THE STONE OF NAMES",
        headline=f"The Stone has no page for {name or 'that name'}",
        support="They moved on, or the Stone is still carving.",
        body_lines=[note] if note else [],
        options=[Option("back", "Step away")],
        meters=meters(p),
    )


# ── Send money — the Grants Desk law, from anywhere ─────────────────────

def _pay_scene(p: dict, pr: dict, note: str = "") -> Scene:
    name = str(pr.get("name") or p.get("profile_view"))
    amounts = [a for a in (100, 500, p["gold"] // 2) if 0 < a <= p["gold"]]
    opts = [Option(f"pf_pay_{a}", f"◈ {a:,}",
                   f"pay ◈ {a:,} — ◈ {int(a * economy.GRANT_BURN_PCT):,} "
                   "of it burns")
            for a in sorted(set(amounts))]
    if not opts:
        note = (note + "\n" if note else "") + \
            "You carry nothing to send — the Vault moves carried gold only."
    opts.append(Option("pf_cancel", "Never mind"))
    cap = economy.GRANT_DAILY_CAP_PER_LEVEL * p["level"]
    sent = p["daily"].get("granted", 0)
    return Scene(
        eyebrow="THE STONE OF NAMES · A CLIMBER'S PAGE",
        headline=f"How much for {name}?",
        support=f"Daily cap ◈ {cap:,} — used ◈ {sent:,}. The Vault burns "
                f"{int(economy.GRANT_BURN_PCT * 100)}% of every transfer.",
        body_lines=[ln for ln in note.split("\n") if ln] if note else [],
        options=opts,
        meters=meters(p),
    )


def _gift_scene(p: dict, pr: dict, note: str = "") -> Scene:
    name = str(pr.get("name") or p.get("profile_view"))
    opts = []
    inv = p.get("inventory") or {}
    for slug in sorted(inv):
        if inv[slug] <= 0:
            continue
        it = (economy.APOTHECARY.get(slug) or economy.FORGE.get(slug)
              or economy.RELICS.get(slug))
        label = it.name if it else slug.replace("_", " ")
        n = int(inv[slug])
        opts.append(Option(f"pf_gift_{slug}", f"Give the {label}",
                           f"×{n} in your pack" if n > 1 else ""))
        if len(opts) >= 8:
            break
    opts.append(Option("pf_cancel", "Never mind"))
    return Scene(
        eyebrow="THE STONE OF NAMES · A CLIMBER'S PAGE",
        headline=f"What goes to {name}?",
        support="The relay wraps it. It leaves your pack now.",
        body_lines=[note] if note else [],
        options=opts,
        meters=meters(p),
    )


def _loot_confirm_scene(p: dict, pr: dict, note: str = "") -> Scene:
    name = str(pr.get("name") or p.get("profile_view"))
    lines = [note] if note else []
    if pr.get("lootable"):
        lines.append("Their camp has sat quiet for over an hour. They "
                     "still defend it in their sleep — a quarter of "
                     "their strength answers you.")
    else:
        lines.append("They are AWAKE AND MOVING. The loot fails and "
                     "they answer at TWICE their strength. Walk away.")
    lines.append("On a win you take a cut of their CARRIED coin — the "
                 "Vault's gold is beyond any blade. The tower logs the "
                 "attempt with your name on it.")
    return Scene(
        eyebrow="THE STONE OF NAMES · A CLIMBER'S PAGE",
        headline=f"Rob {name}'s camp?",
        support="Looting is an action — your own camp reads as active "
                "for the next hour.",
        body_lines=lines,
        options=[Option("pf_loot_go", "Do it", f"{LOOT_COST} ⚡"),
                 Option("pf_cancel", "Walk away")],
        meters=meters(p),
        event_kind="matchup",
    )


def profile_action(p: dict, oid: str) -> Scene:
    name = str(p.get("profile_view") or "")
    pr = _payload(p)
    if oid == "back":
        close_profile(p)
        from . import core
        return core._build_scene(p)
    if oid == "pf_cancel":
        for k in ("profile_pay", "profile_gift", "profile_loot"):
            p.pop(k, None)
        return profile_scene(p)
    if oid.startswith("pv:"):
        return open_profile(p, oid[3:])
    if pr is None:
        return _missing_scene(p, name)

    if oid == "pf_msg":
        if p["gold"] < economy.LETTER_PRICE:
            return profile_scene(
                p, note=f"A letter costs ◈ {economy.LETTER_PRICE} — "
                        "you're short.")
        p["compose_to"] = name
        return Scene(
            eyebrow="THE STONE OF NAMES · A CLIMBER'S PAGE",
            headline=f"A letter to {name}",
            support="The relay carries it from here.",
            options=[],
            meters=meters(p),
            awaits_text=f"the letter's words for {name}",
            ask={"kind": "text", "max": 200,
                 "label": f"the letter to {name}",
                 "placeholder": "what should it say?", "submit": "SEND"},
        )
    if oid == "pf_pay":
        p["profile_pay"] = True
        return _pay_scene(p, pr)
    if oid.startswith("pf_pay_"):
        p.pop("profile_pay", None)
        try:
            amt = int(oid.removeprefix("pf_pay_"))
        except ValueError:
            return profile_scene(p)
        cap = economy.GRANT_DAILY_CAP_PER_LEVEL * p["level"]
        if amt <= 0 or amt > p["gold"]:
            return profile_scene(p, note="You don't carry that much.")
        if p["daily"].get("granted", 0) + amt > cap:
            return profile_scene(
                p, note="That would breach today's grant cap.")
        p["gold"] -= amt
        p["daily"]["granted"] = p["daily"].get("granted", 0) + amt
        net = amt - int(amt * economy.GRANT_BURN_PCT)
        _ledger(p, "grant_out", gold=-amt, note=f"to {name}")
        _effect(p, "grant", to_name=name, net=net, gross=amt)
        return profile_scene(
            p, note=f"+ ◈ {net:,} moves to {name} "
                    f"(◈ {amt - net:,} burned)")
    if oid == "pf_gift":
        p["profile_gift"] = True
        return _gift_scene(p, pr)
    if oid.startswith("pf_gift_"):
        p.pop("profile_gift", None)
        slug = oid.removeprefix("pf_gift_")
        inv = p.get("inventory") or {}
        if int(inv.get(slug, 0)) <= 0:
            return profile_scene(p, note="Your pack doesn't hold that.")
        inv[slug] = int(inv[slug]) - 1
        if inv[slug] <= 0:
            inv.pop(slug, None)
            (p.get("durability_pack") or {}).pop(slug, None)
        it = (economy.APOTHECARY.get(slug) or economy.FORGE.get(slug)
              or economy.RELICS.get(slug))
        label = it.name if it else slug.replace("_", " ")
        _ledger(p, "gift_out", note=f"{label} to {name}")
        _effect(p, "gift_item", to_name=name, slug=slug)
        return profile_scene(
            p, note=f"+ the {label} leaves your pack for {name}")
    if oid == "pf_loot":
        if pr.get("same_guild"):
            return profile_scene(
                p, note="You drink under the same banner. The table "
                        "would never seat you again.")
        if pr.get("protected"):
            return profile_scene(
                p, note="The tower shields them — a paid bunk or too "
                        "few days on the climb.")
        if _loot_cd_left(p, name):
            return profile_scene(
                p, note="You cased that camp within the hour. Let the "
                        "dust settle.")
        p["profile_loot"] = True
        return _loot_confirm_scene(p, pr)
    if oid == "pf_loot_go":
        p.pop("profile_loot", None)
        if pr.get("same_guild") or pr.get("protected"):
            return profile_scene(p)
        if _loot_cd_left(p, name):
            return profile_scene(
                p, note="You cased that camp within the hour.")
        if not state.spend_energy(p, LOOT_COST):
            return profile_scene(
                p, note=f"A raid takes {LOOT_COST} ⚡ you don't have.")
        p.setdefault("loot_cd", {})[name] = state.now().isoformat()
        _ledger(p, "loot_try", note=name)
        _effect(p, "loot_attempt", target_name=name)
        return profile_scene(
            p, note=f"You slip toward {name}'s camp… the tower will "
                    "carry word of how it went.")
    return profile_scene(p)
