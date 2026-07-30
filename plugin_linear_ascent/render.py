"""Scene → chat card HTML (embed_iframe).

One renderer for every scene — the card grammar from
design/chat_components.md and the live mock in design/chat_components.html:
full-bleed 1-bit banner, mono ANSI grid (ch spacing, no rounded corners),
[n] option keys, block meters, and the typewriter reveal with a blinking
aether cursor. Text fallback comes from Scene.to_text(); this file is pure
presentation. No webfonts, no network: banners are white-ink 1-bit PNGs
inlined as data URLs and tinted via CSS mask.
"""

from __future__ import annotations

import base64
import html
import json as _json
import os
import re
from functools import lru_cache

from . import economy, icons
from .engine import tips
from .engine.scene import Meters, Scene

# ── tokens (design/chat_components.html) ─────────────────────────────────
INK = "#0b0e14"
PANEL = "#11151f"
PANEL2 = "#161b28"
BORDER = "#232a3a"
DIM = "#8b93a7"
FAINT = "#5b6275"
TEXT = "#e6e9f2"
GOLD = "#f5a524"
AETHER = "#5eaefc"
VIOLET = "#8b5cf6"
VIOLET_SOFT = "#a78bfa"
RED = "#f4645f"
OK = "#3ad29f"
ORANGE = "#ff9a3c"

_STRIPE = {"loot": GOLD, "present": GOLD, "death": RED,
           "letter": AETHER, "boss": VIOLET, "news": AETHER}
_HEADLINE = {"death": RED, "loot": GOLD, "present": GOLD}
_BOSS_SLUGS = {"gnarl", "skarn", "barrowking", "vyx", "cindermaw", "hrimgar",
               "zephyra", "huntsman", "malgrim", "vharuk"}
_BANNER_TINT = {"death": RED, "present": GOLD}
# 008 specimen variants reuse the creature's art with a different ink:
# runts fade out, toughs read as danger, alphas as a prize.
_VARIANT_TINT = {"runt": FAINT, "tough": VIOLET_SOFT, "alpha": GOLD}

_ART_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "content", "art")
_ART = os.path.join(_ART_ROOT, "banners")
_CREATURES = os.path.join(_ART_ROOT, "creatures")
_EVENTS = os.path.join(_ART_ROOT, "events")
# 027: faction sigils were pane-only (served as PNGs over HTTP). A banner is
# a picture everywhere now — cards included — so the same 1-bit art resolves
# through the ordinary banner lookup.
_SIGILS = os.path.join(_ART, "factions")

# 011 event animations tint by their moment, not the floor mood.
_FX_TINT = {"ascent_open": VIOLET, "ascent_title": VIOLET_SOFT,
            # 016 intro movie — world scenes dim, the enemy violet,
            # hearth and aether gold.
            "intro_aldervale": DIM, "intro_theft": VIOLET,
            "intro_tower": DIM, "intro_warden": VIOLET,
            "intro_refugee": DIM, "intro_roothollow": GOLD,
            "intro_stone": GOLD, "intro_shard": GOLD,
            "intro_muster": DIM}


@lru_cache(maxsize=None)
def sigil_slugs() -> frozenset:
    """027: the faction sigils on disk — a banner's colors read as its own
    ink (violet), never as the grey of a place."""
    try:
        return frozenset(f[: -len("_320x112.png")]
                         for f in os.listdir(_SIGILS)
                         if f.endswith("_320x112.png"))
    except OSError:
        return frozenset()


def _banner_tint(slug: str, variant: str = "") -> str:
    if variant in _VARIANT_TINT:
        return _VARIANT_TINT[variant]
    if slug in _BANNER_TINT:
        return _BANNER_TINT[slug]
    # a sigil is checked first: one of them is called warden_key, and a
    # banner's colors are its own, not a keep's.
    if slug in sigil_slugs():
        return VIOLET_SOFT
    if slug in _BOSS_SLUGS or slug.startswith("warden_"):
        return VIOLET
    return DIM


@lru_cache(maxsize=None)
def _banner_data_url(slug: str) -> tuple[str, int, int] | None:
    """(data_url, width, height) for the slug's art, or None.

    Creature art (encounters/wardens, plan 005) wins over the banner dir
    so milestone bosses pick up their taller 320x200 art when it exists.
    """
    for art_dir, sizes in ((_CREATURES, ("320x200", "320x112")),
                           (_ART, ("320x112", "160x56", "320x200")),
                           (_SIGILS, ("320x112",))):
        for size in sizes:
            path = os.path.join(art_dir, f"{slug}_{size}.png")
            if os.path.exists(path):
                b64 = base64.b64encode(open(path, "rb").read()).decode()
                w, h = (int(n) for n in size.split("x"))
                return f"data:image/png;base64,{b64}", w, h
    return None


@lru_cache(maxsize=None)
def _fx_data_url(slug: str) -> tuple[str, int, int] | None:
    """(data_url, width, height) for an event animation, or None.

    White-ink 1-bit GIFs from tools/generate_event_gifs.py, used exactly
    like the PNG banners: as an alpha mask over a tint color. Chromium
    (Luna's shell) animates GIF masks, so the kill plays in the card."""
    for size in ("320x112", "320x200"):
        path = os.path.join(_EVENTS, f"{slug}_{size}.gif")
        if os.path.exists(path):
            b64 = base64.b64encode(open(path, "rb").read()).decode()
            w, h = (int(n) for n in size.split("x"))
            return f"data:image/gif;base64,{b64}", w, h
    return None


def _gif_duration_ms(path: str) -> int:
    """Total play time of a GIF, from its Graphic Control delays.
    Stdlib-only block walk (no Pillow at plugin runtime)."""
    data = open(path, "rb").read()
    pos, total = 13, 0
    if data[10] & 0x80:                          # global color table
        pos += 3 * (2 << (data[10] & 0x07))
    while pos < len(data):
        marker = data[pos]
        if marker == 0x21:                       # extension block
            label = data[pos + 1]
            pos += 2
            if label == 0xF9:                    # graphic control: delay
                total += int.from_bytes(data[pos + 2:pos + 4],
                                        "little") * 10
            while data[pos]:                     # skip sub-blocks
                pos += 1 + data[pos]
            pos += 1
        elif marker == 0x2C:                     # image descriptor
            lflags = data[pos + 9]
            pos += 10
            if lflags & 0x80:                    # local color table
                pos += 3 * (2 << (lflags & 0x07))
            pos += 1                             # LZW min code size
            while data[pos]:                     # image sub-blocks
                pos += 1 + data[pos]
            pos += 1
        else:                                    # 0x3B trailer (or junk)
            break
    return total


@lru_cache(maxsize=None)
def _fx_split(slug: str) -> tuple[str, str, int, int, int] | None:
    """(intro_url, loop_url, w, h, intro_ms) for split event art (016):
    <slug>_intro plays its action once, then the card swaps the mask to
    <slug>_loop, the ambient tail. None when the slug isn't split."""
    intro = _fx_data_url(f"{slug}_intro")
    loop = _fx_data_url(f"{slug}_loop")
    if not intro or not loop:
        return None
    url, w, h = intro
    for size in ("320x112", "320x200"):
        path = os.path.join(_EVENTS, f"{slug}_intro_{size}.gif")
        if os.path.exists(path):
            return url, loop[0], w, h, _gif_duration_ms(path)
    return None


def _fx_tint(scene: Scene) -> str:
    if scene.fx in _FX_TINT:
        return _FX_TINT[scene.fx]
    if scene.event_kind == "boss":
        return VIOLET
    if scene.event_kind == "loot":
        return GOLD
    return DIM


def _e(s: str) -> str:
    return html.escape(s, quote=True)


# ── 010.1: no emoji, ever ─────────────────────────────────────────────────
# The engine emits ⚡ and 🔒 as one-character semantic markers; every HTML
# surface swaps them for 16×16 1-bit mask glyphs (tinted by currentColor,
# so they inherit the surrounding text color). Plain-text surfaces
# (Scene.to_text, tooltips) carry words instead — an emoji must never
# reach a player's screen from any path.
_EMOJI_GLYPHS = {"⚡": "bolt", "🔒": "lock"}


def _eglyph(key: str) -> str:
    url = icons.icon_data_url(key)
    return (f'<span class="eg" aria-hidden="true" '
            f"style=\"-webkit-mask-image:url('{url}');"
            f"mask-image:url('{url}')\"></span>")


def _sub_glyphs(escaped: str) -> str:
    for ch, key in _EMOJI_GLYPHS.items():
        if ch in escaped:
            escaped = escaped.replace(ch, _eglyph(key))
    return escaped


def _et(s: str) -> str:
    """Escape + swap marker chars for 1-bit glyphs (the common path)."""
    return _sub_glyphs(_e(s))


# Combat numbers, colored in place: damage the player deals reads orange,
# HP the player loses reads red. Scene content stays plain text (the
# renderer contract) — these match the battle-text phrasings from
# engine/combat.py and engine/social.py after escaping. "0 damage" (a
# fully blocked enemy blow) is deliberately left uncolored.
_HIT_HP = re.compile(r"[−-]\d+ HP|(?<=answers for )[1-9][\d,]*")
_HIT_DMG = re.compile(
    r"[1-9]\d* damage|(?<=takes it for )[1-9]\d*"
    r"|(?<=counter takes )[1-9]\d*|(?<=blow lands for )[1-9][\d,]*")


def _combat_html(line: str) -> str:
    s = _e(line)
    s = _HIT_HP.sub(
        lambda m: f'<span style="color:{RED}">{m.group(0)}</span>', s)
    s = _HIT_DMG.sub(
        lambda m: f'<span style="color:{ORANGE}">{m.group(0)}</span>', s)
    return _sub_glyphs(s)


# ── 025 §6: the haul, drawn ─────────────────────────────────────────────
# "When an animal gives coins draw the coins, don't just show the number —
# have the coin icon repeated so it'll be visually clear you received a
# lot. Until it reaches 100, then write just the number."
#
# A numeral is a fact; a heap is a feeling. Under the cap the card lays
# out one mark per point, ten to a row, so 8 gold and 60 gold are told
# apart before the number is read. At the cap the heap would stop scaling
# and start costing DOM, so the numeral takes over.
TALLY_CAP = 100
_TALLY_MARK = {"gold": ("coin", GOLD), "aether": ("aether", AETHER)}
_TALLY_WORD = {"gold": "gold", "aether": "XP"}


def _tally_html(tally: list[dict]) -> str:
    rows = []
    for item in tally:
        kind = str(item.get("kind", ""))
        n = int(item.get("n", 0) or 0)
        if n <= 0 or kind not in _TALLY_MARK:
            continue
        key, tint = _TALLY_MARK[kind]
        label = f"+{n:,} {_TALLY_WORD[kind]}"
        if n >= TALLY_CAP:
            body = (f'<span class="tnum" style="color:{tint}">'
                    f"{_eglyph(key)} {n:,}</span>")
        else:
            body = (f'<span class="tmarks" style="color:{tint}" '
                    f'aria-hidden="true">' + _eglyph(key) * n + "</span>")
        rows.append(f'<div class="tally" title="{_e(label)}">'
                    f'<span class="tsr">{_e(label)}</span>{body}</div>')
    return "".join(rows)


# ── 027: the notice board ───────────────────────────────────────────────
# A count with no sentence around it is a riddle. Every waiting thing gets
# a row at the TOP of the card: the verb, the room, the number, the worth —
# and the row is the shortcut. Blue is the notification ink everywhere in
# this game now; it never means a stat.
_NOTICE_WORD = {"collect": "COLLECT", "plan": "PLAN"}


def _notices_html(notices: list[dict]) -> str:
    rows = []
    for nt in notices:
        kind = str(nt.get("kind", "collect"))
        word = _NOTICE_WORD.get(kind, "COLLECT")
        n = int(nt.get("n", 0) or 0)
        chip = f'<span class="nb">{n}</span>' if n > 0 else ""
        opt = str(nt.get("opt", ""))
        rows.append(
            f'<button type="button" class="nrow" data-opt="{_e(opt)}">'
            f'<span class="nk">{word}</span>{chip}'
            f'<span class="ntx">{_et(str(nt.get("text", "")))}</span>'
            f'<span class="ngo">→</span></button>')
    if not rows:
        return ""
    return (f'<div class="notices"><div class="nhead">waiting for you</div>'
            f'{"".join(rows)}</div>')


# ── 027: the card's own input — nobody should have to type into the chat
# to name a character. Same monospace, same border grammar as an option.
def _ask_html(ask: dict) -> str:
    kind = "number" if str(ask.get("kind", "")) == "number" else "text"
    attrs = [f'type="{kind}"', 'class="ti"', 'name="ans"', 'autocomplete="off"']
    if kind == "number":
        attrs.append('inputmode="numeric"')
        if ask.get("min") is not None:
            attrs.append(f'min="{int(ask["min"])}"')
        if ask.get("max") is not None:
            attrs.append(f'max="{int(ask["max"])}"')
    else:
        attrs.append(f'maxlength="{int(ask.get("max") or 200)}"')
    ph = str(ask.get("placeholder") or "")
    if ph:
        attrs.append(f'placeholder="{_e(ph)}"')
    label = str(ask.get("label") or "")
    submit = str(ask.get("submit") or "SEND")
    lab = f'<span class="alab">{_et(label)}</span>' if label else ""
    return (f'<form class="ask later" data-ask="1">{lab}'
            f'<span class="arow"><input {" ".join(attrs)}>'
            f'<button type="submit" class="asend">{_e(submit)}</button>'
            f"</span></form>")


# ── 027: picture tiles — a banner is a sigil, not a filename ────────────
def _gallery_html(gallery: list[dict]) -> str:
    tiles = []
    for g in gallery:
        slug = str(g.get("slug", ""))
        art = _banner_data_url(slug) if slug else None
        if art:
            url, w, h = art
            pic = (f'<span class="gpic" style="background-color:{AETHER};'
                   f"aspect-ratio:{w}/{h};"
                   f"-webkit-mask-image:url('{url}');"
                   f"mask-image:url('{url}');\"></span>")
        else:
            pic = '<span class="gpic none"></span>'
        sub = (f'<span class="gsub">{_et(str(g.get("sub", "")))}</span>'
               if g.get("sub") else "")
        tiles.append(
            f'<button type="button" class="gtile" '
            f'data-opt="{_e(str(g.get("opt", "")))}">{pic}'
            f'<span class="glab">{_et(str(g.get("label", slug)))}</span>'
            f"{sub}</button>")
    if not tiles:
        return ""
    return f'<div class="gal later">{"".join(tiles)}</div>'


def _blocks(cur: int, cap: int, cells: int = 10) -> str:
    cur = max(0, min(cur, cap))
    filled = round(cells * cur / cap) if cap else 0
    return (f"{'█' * filled}"
            f'<span class="off">{"░" * (cells - filled)}</span>')


# Hover tooltips — the rail is the HUD, so each meter explains itself.
# 014: data-tip + the shared instant tipbox (was native title= — the
# browser's 500ms+ delay made them undiscoverable).
_TIP_HP = ("HP — health. At 0 you die: all carried gold is lost and armor "
           "and shield break. Heal at the healer's tent or the Apothecary.")
_TIP_EN = ("Energy — actions spend it: wilds hunt 1, Warden attempt 3, "
           "milestone boss 5, PvP attack 3. Regenerates 1 every 45 minutes.")
_TIP_XP = ("XP — experience. Fills as you fight and banks past the cap. "
           "A full bar is your license to train: buy the next level with "
           "gold at the Guildhall. Honing, spells, and shard scans burn "
           "XP — spending delays training, never lowers a level.")
_TIP_LV = ("LV — your level. Levels are bought at the Guildhall: a full "
           "XP bar plus the training fee in gold.")
_TIP_GOLD = ("◈ Carried gold — spendable anywhere but lost when you die. "
             "The Vault banks it safely at 5%/day interest.")


def _meters_html(m: Meters) -> str:
    """The rail. 027: every number carries data-m/data-v/data-max so the
    pane can COUNT it to its new value instead of blinking — a 25-point
    heal should be felt as twenty-five, not as an arithmetic result."""
    low = " low" if m.hp * 10 <= m.hp_max * 3 else ""

    def val(key: str, cur: int, cap: int | None = None) -> str:
        mx = f' data-max="{cap}"' if cap is not None else ""
        return (f'<span class="mv" data-m="{key}" data-v="{cur}"{mx}>'
                f"{cur:,}</span>")

    return (
        f'<div class="rail later">'
        f'<span class="meter hp{low}" data-tip="{_e(_TIP_HP)}">'
        f"<span>HP {val('hp', m.hp, m.hp_max)}/{m.hp_max}</span>"
        f'<span class="blocks" data-bar="hp" aria-hidden="true">'
        f"{_blocks(m.hp, m.hp_max)}</span></span>"
        f'<span class="meter en" data-tip="{_e(_TIP_EN)}">'
        f"<span>{_eglyph('bolt')} {val('en', m.energy, m.energy_max)}/"
        f"{m.energy_max}</span>"
        f'<span class="blocks" data-bar="en" aria-hidden="true">'
        f"{_blocks(m.energy, m.energy_max)}</span></span>"
        f'<span class="meter ae" data-tip="{_e(_TIP_XP)}">'
        f"<span>XP {val('xp', m.xp, m.xp_need)}/{m.xp_need:,}</span>"
        f'<span class="blocks" data-bar="xp" aria-hidden="true">'
        f"{_blocks(m.xp, m.xp_need)}</span></span>"
        f'<span class="gold">'
        f'<span class="lvl" data-tip="{_e(_TIP_LV)}">LV {m.level}</span>'
        f'<span data-tip="{_e(_TIP_GOLD)}">◈ {val("gold", m.gold)}</span>'
        f"</span></div>")


# ── 017/003: the enemy header + the [i] dossier ─────────────────────────
# The counter system is invisible noise unless the enemy's sheet is
# readable at a glance (the Kingdom Rush lesson). scene.enemy carries the
# payload; the header shows the always-on HP bar, the range chip and the
# active damage modifier; the [i] badge opens the dossier — a native
# <details>, all data inlined, no server round-trip, no model in the path.

# 025 §4: a style is a palette on the same 1-bit silhouette — keen reads
# ember, warded reads frost, and plain steel keeps the worn/packed ink.
_STYLE_TINT = {"keen": ORANGE, "warded": AETHER}

_TIER_ICON = {"armor": "t_armor", "resist": "t_resist", "flying": "t_wing",
              "bulwark": "t_bulwark", "speed": "t_speed"}


def _ticon(key: str, tint: str = DIM) -> str:
    url = icons.icon_data_url(key)
    return (f'<span class="ticon" style="background-color:{tint};'
            f"-webkit-mask-image:url('{url}');mask-image:url('{url}');\">"
            f"</span>")


def _speed_word(spd: int) -> str:
    if spd >= 7:
        return "fast"
    if spd <= 3:
        return "slow"
    return "steady"


def _active_mods(en: dict) -> list[str]:
    """The 002 retro line: every live damage modifier, NAMED — the bow's
    close-quarters collapse read as a bug when nothing on screen said why."""
    mods = []
    rng, dt = en.get("range", ""), en.get("dtype", "")
    prof = en.get("profile") or {}
    if rng == "at_range":
        mods.append("its blows land at HALF — it hasn't reached you")
        if dt == "melee":
            mods.append("your steel can't swing until you close")
    elif rng == "close":
        if dt == "ranged":
            mods.append("your bow works at ×0.6 in this press — open "
                        "distance to shoot full")
    if prof.get("flying") and dt == "melee":
        mods.append("AIRBORNE — your steel cannot touch it")
    if en.get("dodge"):
        mods.append(f"your speed edge slips {en['dodge']}% of its blows")
    return mods


def _enemy_head_html(en: dict) -> str:
    hp, cap = int(en.get("hp", 0)), max(1, int(en.get("hp_max", 1)))
    low = " low" if hp * 10 <= cap * 3 else ""
    rng = en.get("range", "")
    chip = ""
    if rng == "at_range":
        chip = '<span class="rchip">◇ at range</span>'
    elif rng == "close":
        chip = '<span class="rchip">◇ close quarters</span>'
    mods = _active_mods(en)
    mod = (f'<span class="mchip">{_e(mods[0])}</span>' if mods else "")
    return (f'<div class="ehead later">'
            f'<span class="meter foe{low}" data-tip="The enemy\'s health — '
            f'visible from the first breath. Kill it before it kills you.">'
            f"<span>HP {hp}/{cap}</span>"
            f'<span class="blocks" aria-hidden="true">'
            f"{_blocks(hp, cap)}</span></span>"
            f"{chip}{mod}</div>")


def _dossier_html(en: dict) -> str:
    prof = en.get("profile") or {}
    rows = []

    def row(icon: str, head: str, text: str, tint: str = DIM) -> None:
        rows.append(f'<div class="drw">{_ticon(icon, tint)}'
                    f'<span><b>{_e(head)}</b> {_e(text)}</span></div>')

    if prof.get("armor", "none") != "none":
        row("t_armor", f"plate — {economy.TIER_LABEL[prof['armor']]}.",
            "Turns part of every blow of steel or shot. Spellwork "
            "ignores it.", TEXT)
    if prof.get("resist", "none") != "none":
        row("t_resist", f"spellguard — {economy.TIER_LABEL[prof['resist']]}.",
            "Eats part of every cast. Steel and shot ignore it.", TEXT)
    if prof.get("flying"):
        row("t_wing", "airborne.",
            "Steel cannot reach it. Arrows and spellwork fly.", VIOLET_SOFT)
    if prof.get("bulwark"):
        row("t_bulwark", "bulwark.",
            "Half again the flesh — this will take time.", TEXT)
    mspd = int(en.get("mspd", 5))
    pspd = int(en.get("pspd", 5))
    if mspd > pspd:
        chase = "It closes ground you cannot hold — don't count on outrunning it."
    elif mspd < pspd:
        chase = "You hold the range and you choose the exit — kite it."
    else:
        chase = "An even footrace — no one gets away clean."
    row("t_speed", f"speed — {_speed_word(mspd)} ({mspd}) against "
        f"your {pspd}.", chase,
        RED if mspd > pspd else (OK if mspd < pspd else DIM))
    for m in _active_mods(en):
        rows.append(f'<div class="drw"><span class="dmark">◇</span>'
                    f"<span>{_e(m)}</span></div>")
    if en.get("lore"):
        rows.append(f'<div class="dlore">{_e(en["lore"])}</div>')
    return (f'<details class="dx"><summary role="note" aria-label="enemy '
            f'dossier">i</summary><div class="dossier">'
            f'<div class="dhead">{_e(en.get("name", ""))} — the shard\'s '
            f"dossier</div>{''.join(rows)}</div></details>")


def _opt_gear_icon(oid: str) -> str:
    """004: shop rows carry their 1-bit gear icon (32×32 display of the
    16×16 grids) — buy_/wear_ options only, everything else stays text."""
    if not (oid.startswith("buy_") or oid.startswith("wear_")):
        return ""
    slug = oid.split("_", 1)[1]
    if slug == "arrow_pack":
        key = "arrows"
    elif slug in economy.RELICS:
        # 006: the relic shelf wears its own glyphs, same as the pack
        key = icons.icon_key(slug, "relic")
    else:
        g = economy.FORGE.get(slug)
        if g is None:
            return ""
        key = icons.icon_key(slug, g.slot)
    url = icons.icon_data_url(key)
    return (f'<span class="gicon" aria-hidden="true" '
            f"style=\"-webkit-mask-image:url('{url}');"
            f"mask-image:url('{url}')\"></span>")


def _inventory_html(scene: Scene) -> str:
    """014: the pack strip — 32×32 single-color 1-bit icons under the
    rail. Equipped gear reads bright, pack items dim; every cell
    explains itself through the instant tipbox."""
    if not scene.inventory:
        return ""
    cells = []
    for it in scene.inventory:
        slug = it.get("slug", "")
        equipped = bool(it.get("equipped"))
        url = icons.icon_data_url(icons.icon_key(slug, it.get("kind", "")))
        # 025 §4: the same glyph in the style's ink — ember for keen steel,
        # frost for warded. Unstyled gear keeps the worn/packed contrast.
        tint = _STYLE_TINT.get(economy.style_of(slug)) or (
            TEXT if equipped else DIM)
        count = int(it.get("count", 1))
        ct = (f'<span class="ct">×{count}</span>'
              if count > 1 and not equipped else "")
        tip = tips.item_tip(slug, equipped=equipped)
        # 005: worn gear shows a hairline bar under its icon; the hover
        # names the number ("62% — repair at the Forge").
        dur = it.get("dur")
        durbar = ""
        if dur is not None and dur < 1.0:
            pct = max(0, round(dur * 100))
            col = RED if dur <= 0 else (GOLD if dur < 0.34 else OK)
            durbar = (f'<span class="dur"><span class="durf" '
                      f'style="width:{max(pct, 4)}%;'
                      f'background-color:{col};"></span></span>')
            tip = (f"{tip} · " if tip else "") + (
                "broken — half strength until the Forge repairs it"
                if dur <= 0 else f"{pct}% — repair at the Forge")
        # 027: the cell is a button now — the popup lists what this thing
        # can do HERE, or says where it can be done. `acts` come from the
        # engine (core.pack_actions), never guessed client-side.
        acts = it.get("acts") or []
        act_attr = (f" data-acts=\"{_e(_json.dumps(acts))}\""
                    if acts else "")
        why_attr = (f' data-why="{_e(str(it.get("why")))}"'
                    if it.get("why") else "")
        cells.append(
            f'<button type="button" class="item act'
            f'{" eq" if equipped else ""}" '
            f'data-tip="{_e(tip)}" data-slug="{_e(slug)}" '
            f'data-name="{_e(str(it.get("name", slug)))}"'
            f"{act_attr}{why_attr}>"
            f'<span class="pico"><span class="picon" '
            f'style="background-color:{tint};'
            f"-webkit-mask-image:url('{url}');mask-image:url('{url}');\">"
            f"</span>{durbar}</span>"
            f'<span class="pname">{_e(it.get("name", slug))}{ct}</span>'
            f"</button>")
    return (f'<div class="inv later"><span class="invlbl">pack</span>'
            f'{"".join(cells)}</div>')


# The card's script, three blocks in one tag:
#  1. the mock's typewriter — narration letter by letter behind a blinking
#     cursor, then options and rail fade in staggered
#     (prefers-reduced-motion renders instantly);
#  2. luna:embed:height reporting (056);
#  3. card actions (057) — option buttons post luna:card:action to the chat
#     shell, which calls the plugin's /act route with the user's auth; the
#     next scene arrives as its own card while this one keeps the chosen
#     row lit and the rest disabled. When no bridge answers (stock Luna,
#     or the card is riding inside an agent bubble) the buttons revert
#     after a timeout and the player types a number — cards stay
#     enhancement, never a gate.
_ACT_PATH = "/api/p/plugin-linear-ascent/act"

# 014: the instant tipbox — one fixed element, delegated wiring (survives
# the pane's fragment swaps), zero delay. Shared verbatim by the chat
# card script below and the pane document (pane.py embeds TIP_JS).
TIP_JS = """(function () {
  if (document.getElementById('tipbox')) return;
  var box = document.createElement('div');
  box.id = 'tipbox';
  document.body.appendChild(box);
  var cur = null;
  function show(el) {
    cur = el;
    box.textContent = el.getAttribute('data-tip') || '';
    if (!box.textContent) return hide();
    box.style.display = 'block';
    var r = el.getBoundingClientRect();
    box.style.maxWidth = Math.min(340, innerWidth - 16) + 'px';
    var x = Math.max(8, Math.min(r.left, innerWidth - box.offsetWidth - 8));
    var y = r.top - box.offsetHeight - 6;
    if (y < 4) y = Math.min(r.bottom + 6, innerHeight - box.offsetHeight - 4);
    box.style.left = x + 'px';
    box.style.top = Math.max(4, y) + 'px';
  }
  function hide() { cur = null; box.style.display = 'none'; }
  document.addEventListener('mouseover', function (e) {
    var t = e.target.closest ? e.target.closest('[data-tip]') : null;
    if (t && t !== cur) show(t);
    else if (!t && cur) hide();
  });
  document.addEventListener('focusin', function (e) {
    var t = e.target.closest ? e.target.closest('[data-tip]') : null;
    if (t) show(t);
  });
  document.addEventListener('focusout', hide);
  window.addEventListener('scroll', hide, true);
})();"""

# ── 027: the three new interactions, written once for both hosts ────────
# Both the pane and the chat card define window.__laAct(option, text) — the
# one thing that differs (a direct fetch vs the host bridge) — and then call
# window.__laWire(root) after every scene swap. Everything below is host
# agnostic: the pack popup, the card's own input box, and the rail count-up.
INTERACT_JS = """(function () {
  if (window.__laWire) return;
  var reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ── the pack popup: click a carried thing, act on it ── */
  function closeMenu() {
    var m = document.querySelector('.pmenu');
    if (m) m.remove();
  }
  document.addEventListener('click', function (e) {
    if (!e.target.closest || !e.target.closest('.pmenu')) closeMenu();
  }, true);
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeMenu();
  });
  window.addEventListener('scroll', closeMenu, true);

  function openMenu(item) {
    closeMenu();
    var acts = [];
    try { acts = JSON.parse(item.dataset.acts || '[]'); } catch (err) {}
    var box = document.createElement('div');
    box.className = 'pmenu';
    var name = item.dataset.name || 'this';
    var h = '<div class="phead">' + name + '</div>';
    acts.forEach(function (a, i) {
      h += '<button type="button" class="pact" data-opt="' + a.opt + '">'
        + '<span>' + a.label + '</span>'
        + (a.hint ? '<span class="phint">' + a.hint + '</span>' : '')
        + '</button>';
    });
    if (!acts.length)
      h += '<div class="pwhy">' + (item.dataset.why
        || 'Nothing to do with it here.') + '</div>';
    box.innerHTML = h;
    document.body.appendChild(box);
    var r = item.getBoundingClientRect();
    var x = Math.max(8, Math.min(r.left, innerWidth - box.offsetWidth - 8));
    var y = r.top - box.offsetHeight - 6;
    if (y < 4) y = Math.min(r.bottom + 6, innerHeight - box.offsetHeight - 4);
    box.style.left = x + 'px';
    box.style.top = Math.max(4, y) + 'px';
    box.querySelectorAll('.pact').forEach(function (b) {
      b.addEventListener('click', function () {
        box.querySelectorAll('.pact').forEach(function (x2) {
          x2.disabled = true; });
        closeMenu();
        window.__laAct(b.dataset.opt, '');
      });
    });
  }

  function wirePack(root) {
    root.querySelectorAll('.inv .item').forEach(function (it) {
      if (it.dataset.wired) return;
      it.dataset.wired = '1';
      it.addEventListener('click', function (e) {
        e.stopPropagation(); openMenu(it); });
      it.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault(); openMenu(it); }
      });
    });
  }

  /* ── the card's own input: nobody types a name into the chat ── */
  function wireAsk(root) {
    root.querySelectorAll('form.ask').forEach(function (f) {
      if (f.dataset.wired) return;
      f.dataset.wired = '1';
      var input = f.querySelector('.ti');
      var send = f.querySelector('.asend');
      f.addEventListener('submit', function (e) {
        e.preventDefault();
        var v = (input.value || '').trim();
        if (!v) { input.focus(); return; }
        input.disabled = true; send.disabled = true;
        window.__laAct('', v);
      });
      setTimeout(function () { try { input.focus(); } catch (err) {} }, 60);
    });
  }

  /* ── the rail count-up: a 25-point heal should be felt as 25 ── */
  var last = {};
  function blocks(cur, cap, cells) {
    var f = cap > 0 ? Math.round(cells * Math.max(0, Math.min(cur, cap))
      / cap) : 0;
    return '\\u2588'.repeat(f) + '<span class="off">'
      + '\\u2591'.repeat(cells - f) + '</span>';
  }
  function tween(el, from, to) {
    var cap = el.dataset.max ? parseInt(el.dataset.max, 10) : 0;
    var bar = null, meter = el.closest('.meter');
    if (meter) bar = meter.querySelector('[data-bar]');
    var steps = Math.min(25, Math.max(1, Math.abs(to - from)));
    var ms = Math.max(16, Math.round(600 / steps));
    var i = 0;
    if (meter) meter.classList.add(to > from ? 'up' : 'down');
    var t = setInterval(function () {
      i++;
      var v = i >= steps ? to
        : Math.round(from + (to - from) * (i / steps));
      el.textContent = v.toLocaleString('en-US');
      if (bar && cap) bar.innerHTML = blocks(v, cap, 10);
      if (i >= steps) {
        clearInterval(t);
        if (meter) setTimeout(function () {
          meter.classList.remove('up', 'down'); }, 260);
      }
    }, ms);
  }
  function countUp(root) {
    var seen = {};
    root.querySelectorAll('.mv[data-m]').forEach(function (el) {
      var k = el.dataset.m, v = parseInt(el.dataset.v, 10);
      seen[k] = v;
      if (reduced || !(k in last) || last[k] === v) return;
      var from = last[k], cap = el.dataset.max
        ? parseInt(el.dataset.max, 10) : 0;
      el.textContent = from.toLocaleString('en-US');
      var meter = el.closest('.meter');
      var bar = meter ? meter.querySelector('[data-bar]') : null;
      if (bar && cap) bar.innerHTML = blocks(from, cap, 10);
      tween(el, from, v);
    });
    last = seen;
  }

  window.__laWire = function (root) {
    root = root || document;
    wirePack(root); wireAsk(root); countUp(root);
  };
})();"""

# 016: split fx — the banner's action gif plays once, then the mask swaps
# to the ambient loop. Shared by the chat card script and the pane.
SWAP_JS = """(function () {
  document.querySelectorAll('.banner[data-swap]').forEach(function (b) {
    if (b.dataset.swapped) return;
    b.dataset.swapped = '1';
    setTimeout(function () {
      if (!b.isConnected) return;
      var u = "url('" + b.dataset.swap + "')";
      b.style.webkitMaskImage = u; b.style.maskImage = u;
    }, parseInt(b.dataset.swapMs || '5000', 10));
  });
})();"""

_SCRIPT = """<script>__SWAP_JS__(()=>{
if(matchMedia('(prefers-reduced-motion: reduce)').matches)return;
const typed=[...document.querySelectorAll('.type')];
const later=[...document.querySelectorAll('.later')];
typed.forEach(e=>e.classList.add('pending'));
later.forEach(e=>e.classList.add('waiting'));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const textNodes=el=>{const w=document.createTreeWalker(el,NodeFilter.SHOW_TEXT);
const a=[];let n;while((n=w.nextNode()))a.push(n);return a};
async function typeEl(el){const ns=textNodes(el);const full=ns.map(n=>n.nodeValue);
ns.forEach(n=>{n.nodeValue=''});el.classList.remove('pending');
const cur=document.createElement('span');cur.className='cursor';
cur.setAttribute('aria-hidden','true');
for(let i=0;i<ns.length;i++){const n=ns[i],t=full[i];
n.parentNode.insertBefore(cur,n.nextSibling);
for(let c=1;c<=t.length;c++){n.nodeValue=t.slice(0,c);await sleep(7)}}
cur.remove()}
(async()=>{for(const el of typed)await typeEl(el);
let d=0;for(const el of later){setTimeout(()=>el.classList.add('shown'),d);d+=90}})();
})();
/* luna:embed:height — hosts that support it auto-size the iframe so the
   card never scrolls internally; harmless where nobody listens. */
(function () {
  function post() {
    try {
      parent.postMessage({type: "luna:embed:height",
        height: document.documentElement.scrollHeight}, "*");
    } catch (e) {}
  }
  if (window.ResizeObserver)
    new ResizeObserver(post).observe(document.documentElement);
  window.addEventListener("load", post);
  post();
})();
/* card actions — clicks act through the host bridge, no model in the way.
   027: the notice board, the sigil tiles, the pack popup and the card's own
   input all act through the same one door (window.__laAct). */
(function () {
  var btns = Array.prototype.slice.call(document.querySelectorAll(
    'button.opt, button.nrow, button.gtile'));
  var acted = false;
  var hint = document.querySelector('.reply');
  function setHint(t) { if (hint) hint.textContent = t; }
  function lock(chosen) { btns.forEach(function (b) {
    b.disabled = true; b.classList.add(b === chosen ? 'chosen' : 'stale');
  }); }
  function unlock() { acted = false; btns.forEach(function (b) {
    b.disabled = false; b.classList.remove('chosen', 'stale');
  }); }
  window.__laAct = function (option, text, chosen) {
    if (acted) return; acted = true; lock(chosen); setHint('\\u2026');
    var nonce = Math.random().toString(36).slice(2);
    var timer = setTimeout(function () {
      window.removeEventListener('message', onRes);
      unlock(); setHint('reply with a number to act');
    }, 6000);
    function onRes(e) {
      var d = e.data || {};
      if (d.type !== 'luna:card:result' || d.nonce !== nonce) return;
      clearTimeout(timer); window.removeEventListener('message', onRes);
      if (d.ok) { setHint(''); return; }
      unlock();
      var t = d.body && d.body.detail ? String(d.body.detail)
                                      : 'that didn\\u2019t take';
      setHint(t.slice(0, 140) + ' \\u2014 reply with a number to act');
    }
    window.addEventListener('message', onRes);
    parent.postMessage({type: 'luna:card:action', nonce, path: '__ACT__',
      body: {option: option || '', text: text || '',
             scene_id: document.body.dataset.scene || ''}}, '*');
  };
  btns.forEach(function (b) { b.addEventListener('click', function () {
    window.__laAct(b.dataset.opt, '', b);
  }); });
})();
__INTERACT_JS__
if (window.__laWire) window.__laWire(document);
__TIP_JS__</script>""".replace("__ACT__", _ACT_PATH) \
                      .replace("__TIP_JS__", TIP_JS) \
                      .replace("__INTERACT_JS__", INTERACT_JS) \
                      .replace("__SWAP_JS__", SWAP_JS)


def render_scene_fragment(scene: Scene) -> str:
    """The scene panel itself — one `<div class="card">` with the full card
    grammar. Shared verbatim by the legacy chat card (render_scene wraps it
    in a document + bridge script) and the 009 game pane (which swaps
    fragments in place and drives /act directly)."""
    parts: list[str] = []

    # 011: an event animation owns the banner slot when it ships art;
    # the static banner is the fallback for the same scene.
    # 016: split art (intro+loop) plays the action once, then the swap
    # script settles the banner into the ambient loop.
    fx = _fx_data_url(scene.fx) if scene.fx else None
    split = _fx_split(scene.fx) if scene.fx and not fx else None
    banner = _banner_data_url(scene.banner) if scene.banner else None
    swap_attr = ""
    if fx:
        url, w, h = fx
        tint = _fx_tint(scene)
    elif split:
        url, loop_url, w, h, intro_ms = split
        tint = _fx_tint(scene)
        swap_attr = f' data-swap="{loop_url}" data-swap-ms="{intro_ms}"'
    elif banner:
        url, w, h = banner
        tint = _banner_tint(scene.banner, scene.banner_variant)
    if fx or split or banner:
        parts.append(
            f'<div class="banner" style="background-color:{tint};'
            f"aspect-ratio:{w}/{h};"
            f"-webkit-mask-image:url('{url}');"
            f"mask-image:url('{url}');\"{swap_attr}></div>")

    # 027: the notice board owns the top of the card — above the location,
    # above the headline. It is not a menu row and must never look like one.
    if getattr(scene, "notices", None):
        parts.append(_notices_html(scene.notices))

    parts.append(f'<div class="eyebrow type">{_e(scene.eyebrow)}</div>')
    hl_col = _HEADLINE.get(scene.event_kind, TEXT)
    parts.append(f'<div class="headline type" style="color:{hl_col}">'
                 f"{_e(scene.headline)}</div>")
    if scene.enemy:
        # 003: the always-on enemy bar + range chip, and the [i] badge
        # (top-right of the card — over the banner when there is one).
        parts.append(_enemy_head_html(scene.enemy))
        parts.append(_dossier_html(scene.enemy))
    if scene.support:
        parts.append(f'<div class="support type">{_et(scene.support)}</div>')
    if scene.shard_note:
        parts.append(f'<div class="shard type"><span class="glyph">◆</span>'
                     f"<span>{_et(scene.shard_note)}</span></div>")
    in_fold = False
    for line in scene.body_lines:
        # 007: ▣ fold markers — long shop shelves collapse into a
        # <details> block (the [i]-dossier pattern, zero JS).
        if line.startswith("▣ "):
            parts.append(f'<details class="fold"><summary class="type">'
                         f"{_et(line[2:])}</summary>")
            in_fold = True
            continue
        if line == "▣.":
            if in_fold:
                parts.append("</details>")
                in_fold = False
            continue
        if line.startswith("+"):
            parts.append(f'<div class="body type" style="color:{OK}">'
                         f"{_et(line)}</div>")
        elif line.startswith("−") or line.startswith("-"):
            parts.append(f'<div class="body type" style="color:{RED}">'
                         f"{_et(line)}</div>")
        else:
            parts.append(f'<div class="body type">{_combat_html(line)}</div>')
    if in_fold:
        parts.append("</details>")
    if getattr(scene, "tally", None):
        parts.append(_tally_html(scene.tally))
    if getattr(scene, "gallery", None):
        parts.append(_gallery_html(scene.gallery))
    if getattr(scene, "ask", None):
        parts.append(_ask_html(scene.ask))

    if scene.options:
        rows = []
        for i, o in enumerate(scene.options, 1):
            key_cls = " aether" if o.aether else ""
            # 019: a locked row is dimmed but stays a button — clicking
            # it is how the player asks why the gate is shut.
            opt_cls = " locked" if getattr(o, "locked", False) else ""
            hint = (f'<span class="hint">{_et(o.hint)}</span>'
                    if o.hint else "")
            gicon = _opt_gear_icon(o.id)
            # 027: the count leaves the label and becomes a blue chip —
            # a notification reads as a notification, at a glance.
            bn = int(getattr(o, "badge", 0) or 0)
            badge = f'<span class="badge">{bn}</span>' if bn else ""
            btn = (f'<button type="button" class="opt{opt_cls}" '
                   f'data-opt="{_e(o.id)}">'
                   f'<span class="key{key_cls}">{i}</span>{gicon}'
                   f'<span class="lbl">{_et(o.label)}</span>{badge}'
                   f"{hint}</button>")
            # 014: the whisper glyph — [i] OUTSIDE the button, so tapping
            # it never fires the option; tip resolves by option id.
            tip = tips.option_tip(o.id)
            info = (f'<span class="info" tabindex="0" role="note" '
                    f'data-tip="{_e(tip)}">i</span>' if tip else "")
            rows.append(f'<div class="orow">{btn}{info}</div>')
        parts.append(f'<div class="options later">{"".join(rows)}'
                     f'<div class="reply">click an option — or reply '
                     f"with a number</div></div>")

    if scene.meters:
        parts.append(_meters_html(scene.meters))
    parts.append(_inventory_html(scene))

    stripe = _STRIPE.get(scene.event_kind)
    style_attr = (f' style="border-left:3px solid {stripe};"' if stripe else "")
    return (f'<div class="card" data-scene="{_e(scene.scene_id)}"{style_attr}>'
            + "".join(parts) + "</div>")


# The card grammar — shared by the legacy chat card document and the 009
# game pane. Pure presentation tokens; hosts add their own page CSS.
SCENE_CSS = f"""
.card{{background:{PANEL};border:1px solid {BORDER};
 border-radius:0;margin:0;padding:12px 2ch 10px;color:{TEXT};
 font:14px/1.6 ui-monospace,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;
 font-variant-numeric:tabular-nums;overflow:hidden;position:relative;}}
/* ── 017/003: enemy header + [i] dossier ── */
.ehead{{display:flex;flex-wrap:wrap;align-items:center;gap:1ch 2ch;
 margin-top:6px;color:{DIM};}}
.meter.foe .blocks{{color:{VIOLET_SOFT};}}
.meter.foe.low .blocks{{color:{RED};}}
.rchip{{color:{VIOLET_SOFT};letter-spacing:.04em;}}
.mchip{{color:{ORANGE};font-size:12px;}}
.dx summary{{position:absolute;top:8px;right:8px;z-index:3;
 list-style:none;display:flex;align-items:center;padding:1px .6ch;
 background:{INK};border:1px solid {AETHER};color:{AETHER};
 cursor:help;user-select:none;font-style:italic;font-size:13px;
 line-height:1.5;}}
.dx summary::-webkit-details-marker{{display:none;}}
.dx summary::before{{content:"[";font-style:normal;}}
.dx summary::after{{content:"]";font-style:normal;}}
.dx summary:hover,.dx[open] summary{{background:{AETHER};color:{INK};}}
.dossier{{border:1px solid {AETHER};background:color-mix(in srgb,
 {AETHER} 6%,{PANEL});padding:10px 1.5ch;margin:8px 0 2px;}}
.dhead{{color:{AETHER};text-transform:uppercase;letter-spacing:.08em;
 font-size:12px;margin-bottom:6px;}}
.drw{{display:flex;gap:1ch;align-items:flex-start;padding:3px 0;
 color:{DIM};}}
.drw b{{color:{TEXT};font-weight:700;}}
.drw .dmark{{color:{VIOLET_SOFT};flex:none;width:16px;text-align:center;}}
.ticon{{width:16px;height:16px;flex:none;display:inline-block;
 margin-top:3px;mask-size:100% 100%;-webkit-mask-size:100% 100%;
 mask-repeat:no-repeat;-webkit-mask-repeat:no-repeat;
 image-rendering:pixelated;}}
/* 010.1: inline 1-bit glyphs where the engine marks bolt/lock — tinted
   by currentColor so they read as text, never as emoji. */
.eg{{width:16px;height:16px;display:inline-block;vertical-align:-3px;
 background-color:currentColor;mask-size:100% 100%;
 -webkit-mask-size:100% 100%;mask-repeat:no-repeat;
 -webkit-mask-repeat:no-repeat;image-rendering:pixelated;}}
/* 025/006: the haul. Marks tile ten to a row and shrink a little so a
   99-coin kill still reads as one heap instead of a wall of glyphs. */
.tally{{margin:2px 0 0;line-height:1;}}
.tally .tmarks{{display:inline-grid;grid-template-columns:repeat(10,14px);
 gap:1px;}}
.tally .tmarks .eg{{width:14px;height:14px;vertical-align:0;}}
.tally .tnum{{font-variant-numeric:tabular-nums;}}
.tally .tsr{{position:absolute;width:1px;height:1px;overflow:hidden;
 clip:rect(0 0 0 0);white-space:nowrap;}}
.dlore{{color:{FAINT};font-style:italic;margin-top:6px;
 border-top:1px dashed {BORDER};padding-top:6px;}}
.banner{{display:block;width:calc(100% + 4ch);margin:-12px -2ch 10px;
 mask-size:100% 100%;-webkit-mask-size:100% 100%;mask-repeat:no-repeat;
 -webkit-mask-repeat:no-repeat;image-rendering:pixelated;
 border-bottom:1px solid {BORDER};}}
/* ── 027: the notice board. Blue is the notification ink — it never
   means a stat, only "something waits for you". ── */
.notices{{border:1px solid {AETHER};border-left:3px solid {AETHER};
 background:color-mix(in srgb,{AETHER} 7%,{PANEL});
 padding:8px 1.5ch 9px;margin:0 0 10px;}}
.nhead{{color:{AETHER};text-transform:uppercase;letter-spacing:.14em;
 font-size:11px;margin-bottom:5px;}}
.nrow{{display:flex;align-items:center;gap:1ch;width:100%;margin-top:4px;
 background:transparent;border:1px solid transparent;border-radius:0;
 padding:4px .5ch;font:inherit;color:{TEXT};text-align:left;
 cursor:pointer;}}
.nrow:hover:not(:disabled){{border-color:{AETHER};
 background:color-mix(in srgb,{AETHER} 10%,{PANEL});}}
.nrow:focus-visible{{outline:1px solid {AETHER};outline-offset:1px;}}
.nrow .nk{{flex:none;color:{AETHER};font-size:11px;letter-spacing:.12em;
 min-width:8ch;}}
.nrow .ntx{{flex:1;min-width:0;color:{DIM};}}
.nrow:hover .ntx{{color:{TEXT};}}
.nrow .ngo{{flex:none;color:{FAINT};}}
.nrow:hover .ngo{{color:{AETHER};}}
.nb,.badge{{flex:none;display:inline-block;min-width:2ch;padding:0 .5ch;
 background:{AETHER};color:{INK};font-weight:700;text-align:center;
 font-variant-numeric:tabular-nums;}}
.badge{{margin-left:1ch;}}
.opt:hover .badge{{background:{TEXT};}}
/* ── 027: the card's own input ── */
.ask{{margin:10px 0 0;padding:10px 0 0;border-top:1px dashed {BORDER};
 display:block;}}
.ask .alab{{display:block;color:{DIM};margin-bottom:5px;}}
.ask .arow{{display:flex;gap:6px;align-items:stretch;}}
.ask .ti{{flex:1;min-width:0;background:{INK};border:1px solid {AETHER};
 color:{TEXT};padding:6px 1.5ch;font:inherit;border-radius:0;
 font-variant-numeric:tabular-nums;}}
.ask .ti::placeholder{{color:{FAINT};}}
.ask .ti:focus{{outline:none;border-color:{TEXT};}}
.ask .asend{{flex:none;background:{AETHER};border:1px solid {AETHER};
 color:{INK};font:inherit;font-weight:700;letter-spacing:.08em;
 padding:6px 2ch;border-radius:0;cursor:pointer;}}
.ask .asend:hover:not(:disabled){{background:{TEXT};border-color:{TEXT};}}
.ask .asend:disabled{{opacity:.5;cursor:default;}}
/* ── 027: picture tiles (faction sigils) ── */
.gal{{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));
 gap:8px;margin:10px 0 0;}}
.gtile{{display:flex;flex-direction:column;gap:4px;background:{PANEL2};
 border:1px solid {BORDER};border-radius:0;padding:6px;font:inherit;
 color:{TEXT};text-align:left;cursor:pointer;}}
.gtile:hover:not(:disabled){{border-color:{AETHER};}}
.gtile:focus-visible{{outline:1px solid {AETHER};outline-offset:1px;}}
.gtile .gpic{{display:block;width:100%;aspect-ratio:320/112;
 mask-size:100% 100%;-webkit-mask-size:100% 100%;mask-repeat:no-repeat;
 -webkit-mask-repeat:no-repeat;image-rendering:pixelated;}}
.gtile .gpic.none{{background:{BORDER};}}
.gtile:hover .gpic{{background-color:{TEXT};}}
.gtile .glab{{color:{TEXT};}}
.gtile .gsub{{color:{FAINT};font-size:12px;}}
/* ── 027: the pack popup — click an item, act on it ── */
.pmenu{{position:fixed;z-index:98;min-width:220px;max-width:300px;
 background:{INK};border:1px solid {AETHER};
 box-shadow:0 4px 18px rgba(0,0,0,.55);padding:8px 1.5ch;color:{TEXT};
 font:13px/1.55 ui-monospace,"SF Mono",Menlo,Consolas,monospace;}}
.pmenu .phead{{color:{AETHER};text-transform:uppercase;
 letter-spacing:.1em;font-size:11px;margin-bottom:6px;}}
.pmenu .pact{{display:flex;gap:1ch;align-items:center;width:100%;
 background:{PANEL2};border:1px solid {BORDER};border-radius:0;
 color:{TEXT};font:inherit;text-align:left;padding:5px 1ch;
 margin-top:4px;cursor:pointer;}}
.pmenu .pact:hover:not(:disabled){{border-color:{AETHER};}}
.pmenu .pact .phint{{margin-left:auto;color:{FAINT};}}
.pmenu .pwhy{{color:{DIM};}}
.inv .item{{background:none;border:0;border-radius:0;font:inherit;
 padding:0;}}
.inv .item.act{{cursor:pointer;}}
.inv .item.act:hover .picon,.inv .item.act:focus-visible .picon{{
 background-color:{AETHER} !important;}}
.eyebrow{{color:{FAINT};text-transform:uppercase;letter-spacing:.08em;}}
.headline{{font-weight:700;margin:4px 0 0;text-wrap:balance;}}
.support{{color:{DIM};}}
.shard{{display:flex;gap:1ch;border-left:2px solid {AETHER};
 background:color-mix(in srgb,{AETHER} 5%,{PANEL});
 padding:8px 1.5ch;margin-top:8px;color:{DIM};}}
.shard .glyph{{color:{AETHER};flex:none;}}
.body{{margin:6px 0 0;white-space:pre-wrap;}}
/* ── 007: folded shop shelves (▣ markers) ── */
.fold{{margin:6px 0 0;}}
.fold summary{{list-style:none;cursor:pointer;user-select:none;
 color:{VIOLET_SOFT};}}
.fold summary::-webkit-details-marker{{display:none;}}
.fold summary::before{{content:"▸ ";color:{FAINT};}}
.fold[open] summary::before{{content:"▾ ";}}
.fold .body{{margin-left:1ch;}}
.options{{margin:10px 0 0;padding:10px 0 0;border-top:1px dashed {BORDER};
 display:flex;flex-direction:column;gap:5px;}}
.opt{{display:flex;align-items:center;gap:1ch;width:100%;
 background:{PANEL2};border:1px solid {BORDER};padding:6px 1.5ch;
 font:inherit;color:inherit;text-align:left;border-radius:0;
 cursor:pointer;}}
.opt:hover:not(:disabled){{border-color:{VIOLET};}}
.opt.locked .lbl,.opt.locked .key{{color:{DIM};}}
.opt.locked .hint{{color:{FAINT};}}
.opt.locked:hover:not(:disabled){{border-color:{BORDER};}}
.opt:focus-visible{{outline:1px solid {VIOLET};outline-offset:1px;}}
.opt:disabled{{cursor:default;}}
.opt.chosen{{border-color:{VIOLET};
 background:color-mix(in srgb,{VIOLET} 10%,{PANEL2});}}
.opt.chosen .key{{color:{VIOLET};}}
.opt.stale{{opacity:.45;}}
.opt .key{{flex:none;color:{VIOLET_SOFT};}}
.opt .key::before{{content:"[";color:{FAINT};}}
.opt .key::after{{content:"]";color:{FAINT};}}
.opt .key.aether{{color:{AETHER};}}
.opt .hint{{margin-left:auto;color:{FAINT};text-align:right;}}
.opt .gicon{{width:32px;height:32px;flex:none;display:inline-block;
 background-color:{DIM};mask-size:100% 100%;-webkit-mask-size:100% 100%;
 mask-repeat:no-repeat;-webkit-mask-repeat:no-repeat;
 image-rendering:pixelated;}}
.opt:hover .gicon{{background-color:{TEXT};}}
.opt.locked .gicon,.opt.locked:hover .gicon{{background-color:{FAINT};}}
.orow{{display:flex;align-items:stretch;gap:5px;}}
.orow .opt{{flex:1;min-width:0;}}
.info{{flex:none;display:flex;align-items:center;padding:0 .5ch;
 background:{PANEL2};border:1px solid {BORDER};color:{FAINT};
 cursor:help;user-select:none;font-style:italic;}}
.info::before{{content:"[";font-style:normal;}}
.info::after{{content:"]";font-style:normal;}}
.info:hover,.info:focus-visible{{color:{AETHER};border-color:{AETHER};
 outline:none;}}
.reply{{color:{FAINT};letter-spacing:.08em;margin-top:5px;}}
.reply::before{{content:"· ";}}
.rail{{display:flex;flex-wrap:wrap;align-items:center;gap:2ch;
 margin-top:10px;padding-top:8px;border-top:1px dashed {BORDER};
 color:{DIM};}}
.meter{{display:flex;align-items:center;gap:1ch;cursor:help;}}
.meter .blocks{{letter-spacing:.5px;}}
/* 027: while a number is counting, the meter says which way it went. */
.meter .mv{{font-variant-numeric:tabular-nums;transition:color .2s ease;}}
.meter.up .mv{{color:{OK};}}
.meter.down .mv{{color:{RED};}}
.meter.hp .blocks{{color:{OK};}}
.meter.hp.low .blocks{{color:{RED};}}
.meter.en .blocks{{color:{AETHER};}}
.meter.ae .blocks{{color:{VIOLET_SOFT};}}
.rail .gold{{color:{GOLD};margin-left:auto;display:inline-flex;gap:1.5ch;}}
.rail .gold [data-tip]{{cursor:help;}}
.rail .lvl{{color:{TEXT};}}
.inv{{display:flex;flex-wrap:wrap;align-items:center;gap:6px 2ch;
 margin-top:8px;padding-top:8px;border-top:1px dashed {BORDER};}}
.invlbl{{color:{FAINT};text-transform:uppercase;letter-spacing:.08em;}}
.inv .item{{display:inline-flex;align-items:center;gap:1ch;cursor:help;
 outline:none;}}
.inv .item:hover .pname,.inv .item:focus-visible .pname{{color:{TEXT};}}
.picon{{width:32px;height:32px;flex:none;display:inline-block;
 mask-size:100% 100%;-webkit-mask-size:100% 100%;mask-repeat:no-repeat;
 -webkit-mask-repeat:no-repeat;image-rendering:pixelated;}}
.inv .pname{{color:{DIM};}}
.inv .item.eq .pname{{color:{TEXT};}}
.inv .ct{{color:{FAINT};margin-left:.5ch;}}
.pico{{display:inline-flex;flex-direction:column;flex:none;gap:2px;}}
.pico .dur{{display:block;width:32px;height:3px;background:{BORDER};}}
.pico .durf{{display:block;height:100%;}}
#tipbox{{position:fixed;display:none;z-index:99;max-width:340px;
 background:{INK};border:1px solid {VIOLET};color:{TEXT};
 padding:8px 1.5ch;font-size:12px;line-height:1.55;
 box-shadow:0 4px 18px rgba(0,0,0,.55);pointer-events:none;
 white-space:normal;}}
.type.pending{{visibility:hidden;}}
.cursor{{display:inline-block;width:.55em;height:1.05em;background:{AETHER};
 vertical-align:text-bottom;margin-left:1px;
 animation:blink .9s steps(1) infinite;}}
@keyframes blink{{50%{{opacity:0;}}}}
.later.waiting{{opacity:0;transition:opacity .3s ease;}}
.later.shown{{opacity:1;}}
@media (prefers-reduced-motion: reduce){{
 .type.pending{{visibility:visible;}}
 .later.waiting{{opacity:1;transition:none;}}
 .cursor{{display:none;}}}}
"""


def render_scene(scene: Scene) -> str:
    """Legacy chat-card document: fragment + doc shell + host bridge script.
    Kept so cards already sitting in chat history still render and act."""
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>'
            f"html,body{{margin:0;padding:0;background:{INK};overflow:hidden;}}"
            f"body{{padding:8px;}}{SCENE_CSS}</style></head>"
            f'<body data-scene="{_e(scene.scene_id)}">'
            f"{render_scene_fragment(scene)}{_SCRIPT}</body></html>")
