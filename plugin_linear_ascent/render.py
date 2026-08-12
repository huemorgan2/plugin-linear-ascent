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

# 031 §1: the left stripe is retired everywhere — event colour lives in
# the headline and banner tint, never a vertical line on the box edge.
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
# 030: full-body player portraits, 100×200 — one per armour forge tier.
_PORTRAITS = os.path.join(_ART_ROOT, "portraits")

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
    030: rooms prefer their tall 320x200 art too — a place is a picture,
    not a letterhead; the 320x112 strip stays as the fallback.
    """
    for art_dir, sizes in ((_CREATURES, ("320x200", "320x112")),
                           (_ART, ("320x200", "320x112", "160x56")),
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


# ── 030 Phase 1: one coin, one colour ───────────────────────────────────
# An amount wears its colour everywhere: gold in GOLD behind the 16×16
# coin mask (the win-card coin is THE coin now), XP in VIOLET_SOFT behind
# the aether shard, energy amounts in AETHER with the bolt. ◈/✦ survive
# only in Scene.to_text() — the text surface stays text.
def _coin(n) -> str:
    text = n if isinstance(n, str) else f"{int(n):,}"
    return (f'<span class="amt" style="color:{GOLD}">'
            f"{_eglyph('coin')} {text}</span>")


def _xp(n) -> str:
    text = n if isinstance(n, str) else f"{int(n):,}"
    return (f'<span class="amt" style="color:{VIOLET_SOFT}">'
            f"{_eglyph('aether')} {text} XP</span>")


_PAINT_GOLD = re.compile(r"◈\s?(?P<n>[+\-−]?[\d,]+)")
_PAINT_AE = re.compile(r"✦\s?(?P<n>[+\-−]?[\d,]+)")
_PAINT_XP = re.compile(r"(?P<n>[+\-−]?\d[\d,]*)\s?XP\b")
_PAINT_EN_A = re.compile(r"(?P<n>\d+)\s?⚡")
_PAINT_EN_B = re.compile(r"⚡\s?(?P<n>[+\-−]?\d+)")
_PAINT_ATK = re.compile(r"\+(?P<n>\d+)\s?ATK\b")
_PAINT_DEF = re.compile(r"\+(?P<n>\d+)\s?DEF\b")


def _stat_gain(n: int, key: str, tint: str) -> str:
    """A gear gain wears its stat, not the coin's gold: the number and
    ONE glyph (+5⚔), same tints as the profile pip rows. Never a pip
    per point — a rack of near rungs must read as numbers, at a
    glance."""
    url = icons.icon_data_url(key)
    pip = (f'<span class="gpip" style="background-color:{tint};'
           f"-webkit-mask-image:url('{url}');"
           f"mask-image:url('{url}');\"></span>")
    return (f'<span class="amt" style="color:{tint}">'
            f"+{n:,}{pip}</span>")


def _paint_amounts(s: str) -> str:
    """Runs on ESCAPED text, before _sub_glyphs — a painted ⚡ still
    becomes the 1-bit bolt, tinted by the span it now sits inside. Runs
    after the +/− gain-loss tint upstream, so a green line keeps a
    gold-coloured amount inside it."""
    s = _PAINT_GOLD.sub(lambda m: _coin(m.group("n")), s)
    s = _PAINT_AE.sub(
        lambda m: f'<span class="amt" style="color:{VIOLET_SOFT}">'
                  f"{_eglyph('aether')} {m.group('n')}</span>", s)
    s = _PAINT_XP.sub(
        lambda m: f'<span class="amt" style="color:{VIOLET_SOFT}">'
                  f"{_eglyph('aether')} {m.group('n')} XP</span>", s)
    s = _PAINT_EN_A.sub(
        lambda m: f'<span class="amt" style="color:{AETHER}">'
                  f"{m.group('n')} ⚡</span>", s)
    s = _PAINT_EN_B.sub(
        lambda m: f'<span class="amt" style="color:{AETHER}">'
                  f"⚡ {m.group('n')}</span>", s)
    s = _PAINT_ATK.sub(
        lambda m: _stat_gain(int(m.group("n")), "sword", ORANGE), s)
    s = _PAINT_DEF.sub(
        lambda m: _stat_gain(int(m.group("n")), "armor", DIM), s)
    return s


def _ep(s: str) -> str:
    """Escape + paint amounts + glyph swap — hints, body lines, notices."""
    return _sub_glyphs(_paint_amounts(_e(s)))


@lru_cache(maxsize=None)
def _paper_tex_url() -> str | None:
    """The broadsheet's own grain — banners/paper_320x150.png. Its odd
    size stays out of `_banner_data_url` so no room ever resolves it."""
    path = os.path.join(_ART, "paper_320x150.png")
    if os.path.exists(path):
        b64 = base64.b64encode(open(path, "rb").read()).decode()
        return f"data:image/png;base64,{b64}"
    return None


def _paper_html(paper: dict) -> str:
    """030 Phase 5: the Morning Crier as a broadsheet — paper texture
    (banners/paper_320x150.png) as a light mask over the panel, the
    day's items typeset in dark ink on top, ✕ top-right closes it for
    the day (posts news_close). No texture on disk → a plain dark
    noticeboard, same words."""
    items = [i for i in (paper.get("items") or []) if i]
    if not items:
        return ""
    # 031 §12: the sheet flows to its content now — six 2-line-clamped
    # items before the fold. Payload order is priority order (dawn,
    # night, census, warden, gossip); to_text keeps every item.
    items = items[:6]
    url = _paper_tex_url()
    tex = ""
    cls = " noart"
    if url:
        # the grain sits a shade under the sheet — newsprint is LIGHT,
        # the ink is dark; the texture must never fight the words.
        tex = (f'<span class="ptex" aria-hidden="true" '
               f'style="background-color:color-mix(in srgb,{FAINT} 22%,'
               f"{TEXT});-webkit-mask-image:url('{url}');"
               f"mask-image:url('{url}');\"></span>")
        cls = ""
    close = ""
    if paper.get("closable"):
        close = ('<button type="button" class="pclose" data-opt="news_close" '
                 'aria-label="close the paper for the day">✕</button>')
    hl = paper.get("headline", "")
    head = f'<div class="phl">{_e(hl)}</div>' if hl else ""
    rows = "".join(
        f'<div class="pit">{_ep(i if len(i) <= 76 else i[:75] + "…")}</div>'
        for i in items)
    return (f'<div class="paper{cls} later">{tex}{close}'
            f'<div class="pbody"><div class="pmast">THE MORNING CRIER</div>'
            f"{head}{rows}</div></div>")


@lru_cache(maxsize=None)
def _strip_art_url(slug: str) -> str | None:
    """030 Phase 4: thin band art — {slug}_320x50.png in banners/."""
    path = os.path.join(_ART, f"{slug}_320x50.png")
    if os.path.exists(path):
        b64 = base64.b64encode(open(path, "rb").read()).decode()
        return f"data:image/png;base64,{b64}"
    return None


def _strip_band_html(strip: dict) -> str:
    """The strongbox shelf: one big number over a 320×50 art band on ink.
    The art is a dim backdrop; the text is the point and paints its own
    amounts (Phase 1). Missing art → the band is just the dark shelf."""
    text = strip.get("text", "")
    if not text:
        return ""
    art = ""
    url = _strip_art_url(strip.get("art", ""))
    if url:
        art = (f'<span class="bart" aria-hidden="true" '
               f'style="background-color:{PANEL2};'
               f"-webkit-mask-image:url('{url}');"
               f"mask-image:url('{url}');\"></span>")
    return (f'<div class="stripband later">{art}'
            f'<span class="btx">{_ep(text)}</span></div>')


def _shard_html(note: str) -> str:
    """030 Phase 3: the shardmind has a face — the 16×16 `shard` grid at
    32px, aether-lit, where it writes. to_text() keeps ◆."""
    if "shard" in icons.ICON_KEYS:
        url = icons.icon_data_url("shard")
        glyph = (f'<span class="glyph savatar" aria-hidden="true" '
                 f"style=\"-webkit-mask-image:url('{url}');"
                 f"mask-image:url('{url}')\"></span>")
    else:
        glyph = '<span class="glyph">◆</span>'
    return (f'<div class="shard type">{glyph}'
            f"<span>{_ep(note)}</span></div>")


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
    # 042: the classes are the sound layer's ears — chp is HP lost,
    # chit damage dealt. Purely semantic; the color still paints.
    s = _e(line)
    s = _HIT_HP.sub(
        lambda m: f'<span class="chp" style="color:{RED}">'
                  f"{m.group(0)}</span>", s)
    s = _HIT_DMG.sub(
        lambda m: f'<span class="chit" style="color:{ORANGE}">'
                  f"{m.group(0)}</span>", s)
    return _sub_glyphs(_paint_amounts(s))


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
# 030: XP wears VIOLET_SOFT everywhere now (law 3) — blue stays the
# notification ink plus energy amounts, nothing else.
_TALLY_MARK = {"gold": ("coin", GOLD), "aether": ("aether", VIOLET_SOFT)}
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
            f'<span class="ntx">{_ep(str(nt.get("text", "")))}</span>'
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


# ── 042: the presence grid — who else stands in this room ───────────────
# Seven faces to a row, the same derived portraits the profile rail
# wears (armor tier + race, never stored art). A sleeping climber wears
# a Zzz chip; hover carries coin and energy; every face is a door to
# that climber's page (data-opt="pv:<name>").

def _tile_portrait_url(race: str, armor: str) -> str | None:
    slug = armor if armor in ("rags", "leather", "chain", "scale",
                              "plate", "aegis") else "rags"
    if race:
        url = _portrait_data_url(f"{race}_{slug}")
        if url:
            return url
    return _portrait_data_url(slug)


def _players_here_html(scene: Scene) -> str:
    tiles = getattr(scene, "players_here", None) or []
    if not tiles:
        return ""
    title = _e(str(getattr(scene, "players_title", "") or "PLAYERS HERE"))
    cells = []
    for t in tiles:
        if not isinstance(t, dict) or not t.get("name"):
            continue
        name = str(t["name"])
        url = _tile_portrait_url(str(t.get("race") or ""),
                                 str(t.get("armor") or ""))
        face = (f'<img class="pface" src="{url}" alt="">' if url
                else '<span class="pface none"></span>')
        zzz = ('<span class="pzzz">Zzz</span>'
               if t.get("sleeping") else "")
        rank = (f'<span class="prank">{int(t["rank"])}</span>'
                if t.get("rank") else "")
        sub = (f'<span class="psub">{_et(str(t["sub"]))}</span>'
               if t.get("sub") else "")
        tip = (f"◈ {int(t.get('gold', 0)):,} carried · "
               f"⚡ {int(t.get('energy', 0))}")
        cells.append(
            f'<button type="button" class="ptile" '
            f'data-opt="{_e(str(t.get("opt", "pv:" + name)))}" '
            f'data-tip="{_e(tip)}">'
            f'<span class="pfbox">{face}{zzz}{rank}</span>'
            f'<span class="pname">{_e(name)}</span>'
            f'<span class="plvl">L{int(t.get("level", 1) or 1)}</span>'
            f"{sub}</button>")
    if not cells:
        return ""
    return (f'<div class="phere later"><div class="phead">{title}</div>'
            f'<div class="pgrid">{"".join(cells)}</div></div>')


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
_TIP_XP = ("XP — experience. Fills as you fight, up to the bar for the "
           "next level — surplus goes nowhere. A full bar is your license "
           "to train: buy the next level with gold at the Guildhall. "
           "Honing, spells, and mending burn XP from the bar.")
_TIP_LV = ("LV — your level. Levels are bought at the Guildhall: a full "
           "XP bar plus the training fee in gold.")
_TIP_GOLD = ("Carried gold — spendable anywhere but lost when you die. "
             "The Vault banks it safely at 5%/day interest.")
_TIP_FACTION = ("Your banner. Go to the faction house on Roothollow "
                "main street — the Guildhall — for the store, the "
                "armory and your brothers.")


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
        f"</div>")


def _ident_html(m: Meters) -> str:
    """031 §4: who is climbing, said once and plainly — name and calling
    top-left, LEVEL and COINS in bold top-right. Gold's live counter
    (data-m) moved here from the rail; there is exactly one on the card."""
    who = " ".join(x for x in (m.race, m.clazz) if x)
    left = (f'<span class="idname">{_e(m.name)}</span>'
            + (f'<span class="idwho">{_e(who)}</span>' if who else ""))
    fac = getattr(m, "faction", "")
    if fac:
        left += (f'<span class="idfac" data-tip="{_e(_TIP_FACTION)}">'
                 f'brother of the <b>{_e(fac)}</b> faction</span>')
    gold = (f'<span class="mv" data-m="gold" data-v="{m.gold}">'
            f"{m.gold:,}</span>")
    right = (f'<span class="idlv" data-tip="{_e(_TIP_LV)}">'
             f"LEVEL {m.level}</span>"
             f'<span class="idgold" data-tip="{_e(_TIP_GOLD)}">'
             f'COINS {_eglyph("coin")} {gold}</span>')
    return (f'<div class="ident later"><span class="idl">{left}</span>'
            f'<span class="idr">{right}</span></div>')


# ── 030: the player profile — who is climbing ───────────────────────────
# The rail grows into a profile block: a 100×200 full-body portrait that
# suits up with the armour tier, and total ATK/DEF drawn as rows of ten
# 16×16 glyphs — every 3 points fills half an icon (worn sword / armour
# in the icon house style), the numeral always beside them. Missing art
# or an older engine (no atk on the wire) degrades to the bare rail.

_PORTRAIT_TIERS = ((9, "aegis"), (7, "plate"), (5, "scale"),
                   (3, "chain"), (1, "leather"))

_TIP_ATK = ("ATK — your total attack: class base plus weapon and honing. "
            "Every 3 points fills half a sword.")
_TIP_DEF = ("DEF — your total defense: shield, armor and honing. "
            "Every 3 points fills half an icon.")
_TIP_SPD = ("SPD — your speed: class base plus footwear. Decides dodges, "
            "chases and getaways. Every point fills a bolt.")


def _portrait_slug(scene: Scene) -> str:
    """rags → leather → chain → scale → plate → aegis, resolved from the
    equipped armour on the pack strip — the renderer never opens the
    player doc, it reads the scene it was handed. A race that has its
    own wardrobe (portrait_elf_*_100x200.png) wears it; anyone else
    keeps the shared human set."""
    tier = 0
    for cell in scene.inventory or []:
        if cell.get("kind") == "armor" and cell.get("equipped"):
            g = economy.FORGE.get(cell.get("slug", ""))
            tier = g.tier if g else 0
            break
    slug = "rags"
    for floor_t, s in _PORTRAIT_TIERS:
        if tier >= floor_t:
            slug = s
            break
    race = getattr(scene.meters, "race", "") or ""
    if race and _portrait_data_url(f"{race}_{slug}"):
        return f"{race}_{slug}"
    return slug


@lru_cache(maxsize=None)
def _portrait_data_url(slug: str) -> str | None:
    path = os.path.join(_PORTRAITS, f"portrait_{slug}_100x200.png")
    if os.path.exists(path):
        b64 = base64.b64encode(open(path, "rb").read()).decode()
        return f"data:image/png;base64,{b64}"
    return None


def _pip_row(key: str, label: str, stat: int, tint: str, tip: str,
             per_half: float = 3) -> str:
    halves = max(0, min(20, round(stat / per_half)))
    pips = []
    for i in range(10):
        left = halves - 2 * i
        if left >= 2:
            mode, col = "full", tint
        elif left == 1:
            mode, col = "half", tint
        else:
            mode, col = "outline", FAINT
        url = icons.icon_data_url(key, mode)
        pips.append(f'<span class="pip" style="background-color:{col};'
                    f"-webkit-mask-image:url('{url}');"
                    f"mask-image:url('{url}');\"></span>")
    return (f'<div class="piprow" data-tip="{_e(tip)}">'
            f'<span class="plab" style="color:{tint}">{label} {stat}</span>'
            f'<span class="pips">{"".join(pips)}</span></div>')


def _profile_html(scene: Scene) -> str:
    m = scene.meters
    right = _meters_html(m)
    if getattr(m, "atk", 0):
        spd_row = (_pip_row("bolt", "SPD", m.spd, AETHER, _TIP_SPD,
                            per_half=0.5)
                   if getattr(m, "spd", 0) else "")
        right += ('<div class="piprows later">'
                  + _pip_row("sword", "ATK", m.atk, ORANGE, _TIP_ATK)
                  + _pip_row("armor", "DEF", getattr(m, "dfs", 0), DIM,
                             _TIP_DEF)
                  + spd_row
                  + "</div>")
    # the pack lives in the profile's right column — portrait on the
    # left, everything the climber carries to its right, never below.
    right += _inventory_html(scene)
    ident = _ident_html(m)
    url = _portrait_data_url(_portrait_slug(scene))
    if not url:
        return ident + right
    # a real <img>, not a masked div: with the height stretched to the
    # column, width:auto keeps the 1:2 ratio from the PNG itself — the
    # one sizing rule every webview agrees on. The ink is baked white.
    return (ident
            + f'<div class="profile">'
            f'<img class="portrait later" src="{url}" alt="">'
            f'<div class="pcol">{right}</div></div>')


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
        # 031 §7: nothing reaches you at range — the only blow it has
        # left is the free half-strike when a break-away fails.
        mods.append("it CANNOT reach you at this range — it is still "
                    "crossing")
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


_TIP_EHEAD = ("The enemy's sheet — HP, then attack, defense and speed on "
              "the same scale as your own rows. Everything else is in the "
              "[i] dossier.")


def _enemy_head_html(en: dict) -> str:
    """One line on one ink plate: HP · ATK · DEF · SPD. Nothing more rides
    the art — range, modifiers and the story live in the [i] dossier.
    041: no `later` class — the sheet must read the moment the scene
    lands, not after the typewriter finishes."""
    hp, cap = int(en.get("hp", 0)), max(1, int(en.get("hp_max", 1)))
    low = hp * 10 <= cap * 3
    hp_col = RED if low else VIOLET_SOFT
    sw = icons.icon_data_url("sword")
    ar = icons.icon_data_url("armor")
    spd = ""
    if "mspd" in en:
        bt = icons.icon_data_url("bolt")
        spd = (f'<span class="st" style="color:{AETHER}">'
               f'<span class="eg" aria-hidden="true" '
               f"style=\"-webkit-mask-image:url('{bt}');"
               f"mask-image:url('{bt}')\"></span>"
               f'SPD {int(en.get("mspd", 0))}</span>')
    return (f'<div class="ehead">'
            f'<span class="echip" data-tip="{_e(_TIP_EHEAD)}">'
            f'<span class="st" style="color:{hp_col}">HP {hp}/{cap}</span>'
            f'<span class="st" style="color:{ORANGE}">'
            f'<span class="eg" aria-hidden="true" '
            f"style=\"-webkit-mask-image:url('{sw}');"
            f"mask-image:url('{sw}')\"></span>"
            f'ATK {int(en.get("atk", 0))}</span>'
            f'<span class="st" style="color:{DIM}">'
            f'<span class="eg" aria-hidden="true" '
            f"style=\"-webkit-mask-image:url('{ar}');"
            f"mask-image:url('{ar}')\"></span>"
            f'DEF {int(en.get("def", 0))}</span>'
            f"{spd}</span></div>")


def _dossier_html(en: dict) -> str:
    prof = en.get("profile") or {}
    rows = []

    def row(icon: str, head: str, text: str, tint: str = DIM) -> None:
        rows.append(f'<div class="drw">{_ticon(icon, tint)}'
                    f'<span><b>{_e(head)}</b> {_e(text)}</span></div>')

    # 030 Phase 7: the story leads — who this thing is, before what it
    # does. "story" is the payload key; "lore" the pre-030 fallback.
    story = en.get("story") or en.get("lore")
    if story:
        rows.append(f'<div class="dlore">{_e(story)}</div>')
    # 048: the sign IS the row — one type, its whole triangle spelled out.
    mtype = prof.get("type", "plain")
    if mtype == "armoured":
        row("t_armor", "⛨ armoured.",
            "Plate turns the fight — steel: half, arrows: glance, "
            "magic: full.", TEXT)
    elif mtype == "magic_resist":
        row("t_resist", "✧ magic-resistant.",
            "Spellguard eats the casts — steel: full, arrows: half, "
            "magic: glance.", TEXT)
    elif mtype == "fly":
        row("t_wing", "⚡ it flies.",
            "Steel cannot reach it — arrows: full, magic: half.",
            VIOLET_SOFT)
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
    # the range word and every live modifier moved off the art (the
    # plate is one line now) — they live here, always listed.
    rng = en.get("range", "")
    if rng == "at_range":
        rows.append('<div class="drw"><span class="dmark">◇</span>'
                    "<span>at range — it hasn't reached you yet</span></div>")
    elif rng == "close":
        rows.append('<div class="drw"><span class="dmark">◇</span>'
                    "<span>close quarters — it is on you</span></div>")
    for m in _active_mods(en):
        rows.append(f'<div class="drw"><span class="dmark">◇</span>'
                    f"<span>{_e(m)}</span></div>")
    # 030 Phase 7: the odds — coin and XP ranges from the kill math,
    # painted per the one-coin-one-colour law.
    # 031 §6: wardens carry these rows too; an exact purse (lo == hi)
    # prints as one number, not a 40–40 range.
    drops = en.get("drops") or {}
    if drops.get("gold"):
        lo, hi = drops["gold"]
        amt = f"{lo}" if lo == hi else f"{lo}–{hi}"
        rows.append(f'<div class="drw"><span class="dmark">·</span>'
                    f"<span>{_ep(f'coins ◈ {amt}')}</span></div>")
    if drops.get("xp"):
        lo, hi = drops["xp"]
        amt = f"{lo}" if lo == hi else f"{lo}–{hi}"
        rows.append(f'<div class="drw"><span class="dmark">·</span>'
                    f"<span>{_ep(f'XP ✦ {amt}')}</span></div>")
    return (f'<details class="dx"><summary role="note" aria-label="enemy '
            f'dossier">i</summary><div class="dossier">'
            f'<div class="dhead">{_e(en.get("name", ""))} — the shard\'s '
            f"dossier</div>{''.join(rows)}</div></details>")


def _opt_gear_icon(oid: str, art_slug: str = "") -> str:
    """004: shop rows carry their 1-bit gear icon (32×32 display of the
    16×16 grids) — buy_/wear_ options only, everything else stays text.
    032: the faction chest's cards (take_arm_/put_ ids) name their gear
    through scene.option_art instead — a gear slug there resolves the
    same icon, so the card wall works for any option the engine dresses."""
    if not (oid.startswith("buy_") or oid.startswith("wear_")):
        if art_slug and (art_slug in economy.FORGE
                         or art_slug in economy.RELICS
                         or art_slug == "arrow_pack"):
            slug = art_slug
        else:
            return ""
    else:
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


# ── 031 §13: art rides the choice the engine says it belongs to ─────────
# 030 put fields+warden art on the gate's floor list; the designer moved
# it to the IN-floor choice (hunt vs the keep). The engine now names the
# art per option (scene.option_art, beside options on the wire); the
# renderer just draws what it is told. No art named → plain text row.


def _option_tile_art(scene: Scene, oid: str, locked: bool) -> str:
    slug = (getattr(scene, "option_art", None) or {}).get(oid) or ""
    art = _banner_data_url(slug) if slug else None
    if not art:
        return ""
    url, _w, _h = art
    tint = FAINT if locked else (
        VIOLET if slug.startswith("warden_") else DIM)
    return (f'<span class="farts"><span class="fart" aria-hidden="true" '
            f'style="background-color:{tint};'
            f"-webkit-mask-image:url('{url}');"
            f"mask-image:url('{url}');\"></span></span>")


def _slot_cell(it: dict) -> str:
    """One pack slot — a square button holding the icon, the ×count and
    the wear bar; the name lives in the tip and the action popup."""
    slug = it.get("slug", "")
    equipped = bool(it.get("equipped"))
    url = icons.icon_data_url(icons.icon_key(slug, it.get("kind", "")))
    # 025 §4: the same glyph in the style's ink — ember for keen steel,
    # frost for warded. Unstyled gear keeps the worn/packed contrast.
    tint = _STYLE_TINT.get(economy.style_of(slug)) or (
        TEXT if equipped else DIM)
    count = int(it.get("count", 1))
    ct = (f'<span class="ct">{count}</span>'
          if count > 1 and not equipped else "")
    tip = tips.item_tip(slug, equipped=equipped)
    name = str(it.get("name", slug))
    tip = f"{name} — {tip}" if tip else name
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
        # 045: name the number when the scene ships it (older servers
        # send only the fraction — keep the % fallback for the skew).
        left, total = it.get("dur_left"), it.get("dur_max")
        wear = (f"durability {left:,}/{total:,}" if left is not None
                and total else f"{pct}%")
        tip = (f"{tip} · " if tip else "") + (
            "broken — half strength until the Forge repairs it"
            if dur <= 0 else f"{wear} — repair at the Forge")
    # 027: the cell is a button — the popup lists what this thing can
    # do HERE, or says where it can be done. `acts` come from the
    # engine (core.pack_actions), never guessed client-side.
    acts = it.get("acts") or []
    act_attr = (f" data-acts=\"{_e(_json.dumps(acts))}\""
                if acts else "")
    why_attr = (f' data-why="{_e(str(it.get("why")))}"'
                if it.get("why") else "")
    return (
        f'<button type="button" class="slot item act'
        f'{" eq" if equipped else ""}" '
        f'data-tip="{_e(tip)}" data-slug="{_e(slug)}" '
        f'data-name="{_e(name)}"'
        f"{act_attr}{why_attr}>"
        f'<span class="picon" style="background-color:{tint};'
        f"-webkit-mask-image:url('{url}');mask-image:url('{url}');\">"
        f"</span>{ct}{durbar}</button>")


_PACK_COLS = 6
_PACK_MIN_SLOTS = 12


def _inventory_html(scene: Scene) -> str:
    """031 §3: the pack is a slot grid now — squares that fill with
    what you carry, blanks where nothing does. The weapon in use and
    the shield are promoted to two larger boxes on top; armor and
    shoes keep their bright equipped tint inside the grid. Swapping
    weapons stays the cell popup's job (wear_*), and buying better
    steel still auto-promotes at the Forge."""
    if not scene.inventory:
        return ""
    hand: dict[str, dict] = {}
    rest: list[dict] = []
    for it in scene.inventory:
        kind = it.get("kind", "")
        if it.get("equipped") and kind in ("weapon", "shield") \
                and kind not in hand:
            hand[kind] = it
        else:
            rest.append(it)
    hrow = []
    for kind, lab in (("weapon", "in hand"), ("shield", "shield")):
        it = hand.get(kind)
        cell = (_slot_cell(it) if it else
                f'<span class="slot empty" data-tip="no {lab.replace("in hand", "weapon in hand")} — the Forge sells steel"></span>')
        hrow.append(f'<span class="hcell"><span class="hlab">{lab}'
                    f"</span>{cell}</span>")
    n = len(rest)
    total = max(_PACK_MIN_SLOTS, -(-n // _PACK_COLS) * _PACK_COLS)
    cells = [_slot_cell(it) for it in rest]
    cells += ['<span class="slot empty"></span>'] * (total - n)
    return (f'<div class="inv later"><span class="invlbl">pack</span>'
            f'<div class="handrow">{"".join(hrow)}</div>'
            f'<div class="slotgrid">{"".join(cells)}</div></div>')


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
    // 027: a click on a pack cell focuses it, and a lore bubble on top of
    // the menu it just opened hides the only button in there. Hovering to
    // learn and clicking to act must not collide: while a menu is open,
    // tips stay quiet.
    if (document.querySelector('.pmenu')) return hide();
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
  /* 041: touch — a tap on the [i] toggles the tip; the synthetic
     mouseover/focusin the browser fires right after must not undo the
     toggle, so hover wiring goes quiet for a beat after any touch. */
  var touchT = 0;
  document.addEventListener('pointerdown', function (e) {
    if (e.pointerType !== 'touch') return;
    touchT = Date.now();
    var t = e.target.closest ? e.target.closest('[data-tip]') : null;
    if (!t) return hide();
    if (t === cur && box.style.display === 'block') hide();
    else show(t);
  });
  document.addEventListener('mouseover', function (e) {
    if (Date.now() - touchT < 800) return;
    var t = e.target.closest ? e.target.closest('[data-tip]') : null;
    if (t && t !== cur) show(t);
    else if (!t && cur) hide();
  });
  document.addEventListener('focusin', function (e) {
    if (Date.now() - touchT < 800) return;
    var t = e.target.closest ? e.target.closest('[data-tip]') : null;
    if (t) show(t);
  });
  document.addEventListener('focusout', function () {
    if (Date.now() - touchT < 800) return;
    hide();
  });
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
    var tb = document.getElementById('tipbox');
    if (tb) tb.style.display = 'none';
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
      if (!(k in last) || last[k] === v) return;
      /* 042: the meters speak — before the reduced-motion return so a
         still card still sounds. hurt trails the weapon hit a beat. */
      if (window.__laSfx) {
        if (k === 'gold') window.__laSfx(v > last[k] ? 'coin' : 'spend');
        else if (k === 'hp') window.__laSfx(
          v > last[k] ? 'heal' : 'hurt', v < last[k] ? 0.18 : 0);
        else if (k === 'xp' && v > last[k]) window.__laSfx('xp');
      }
      if (reduced) return;
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

  /* ── the portrait fills the profile column's height; setting an
     explicit px height lets the img's own 1:2 ratio give the width —
     the one proportional-scaling rule every webview honors.
     040: on a phone the full-height portrait ate half the card and
     squeezed the meters off — small screens pin it small and let the
     numbers have the width (the media query owns the layout there). ── */
  function sizePortrait(root) {
    var phone = window.matchMedia
      && window.matchMedia('(max-width: 520px)').matches;
    root.querySelectorAll('.profile').forEach(function (pr) {
      var img = pr.querySelector('.portrait');
      var col = pr.querySelector('.pcol');
      if (!img || !col) return;
      if (phone) {
        img.style.height = '132px';
        img.style.width = 'auto';
        return;
      }
      img.style.height = Math.max(200, col.offsetHeight) + 'px';
      img.style.width = 'auto';
    });
  }
  window.addEventListener('resize', function () {
    sizePortrait(document);
  });

  window.__laWire = function (root) {
    root = root || document;
    wirePack(root); wireAsk(root); countUp(root); sizePortrait(root);
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
/* 041: a click anywhere quadruples the pen */
let fast=false;document.addEventListener('pointerdown',()=>{fast=true});
const textNodes=el=>{const w=document.createTreeWalker(el,NodeFilter.SHOW_TEXT);
const a=[];let n;while((n=w.nextNode()))a.push(n);return a};
async function typeEl(el){const ns=textNodes(el);const full=ns.map(n=>n.nodeValue);
ns.forEach(n=>{n.nodeValue=''});el.classList.remove('pending');
const cur=document.createElement('span');cur.className='cursor';
cur.setAttribute('aria-hidden','true');
for(let i=0;i<ns.length;i++){const n=ns[i],t=full[i];
n.parentNode.insertBefore(cur,n.nextSibling);
for(let c=1;c<=t.length;c++){n.nodeValue=t.slice(0,c);await sleep(fast?2:7)}}
cur.remove()}
(async()=>{for(const el of typed)await typeEl(el);
let d=0;for(const el of later){setTimeout(()=>el.classList.add('shown'),d);d+=fast?22:90}})();
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
    'button.opt, button.nrow, button.gtile, button.ptile, '
    + 'button.pclose'));
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
    plate_on_art = False
    if fx or split or banner:
        banner_html = (
            f'<div class="banner" style="background-color:{tint};'
            f"aspect-ratio:{w}/{h};"
            f"-webkit-mask-image:url('{url}');"
            f"mask-image:url('{url}');\"{swap_attr}></div>")
        # 030 Phase 7: the stat plate sits top-right ON the art whenever
        # there is art to sit on — one visual language with the player's
        # pip rows, so a matchup reads at a glance.
        if scene.enemy:
            banner_html = (f'<div class="bwrap">{banner_html}'
                           f"{_enemy_head_html(scene.enemy)}</div>")
            plate_on_art = True
        parts.append(banner_html)

    # 027: the notice board owns the top of the card — above the location,
    # above the headline. It is not a menu row and must never look like one.
    if getattr(scene, "notices", None):
        parts.append(_notices_html(scene.notices))
    # 030 Phase 5: the day's paper — above the location, below the board.
    if getattr(scene, "paper", None):
        parts.append(_paper_html(scene.paper))

    parts.append(f'<div class="eyebrow type">{_e(scene.eyebrow)}</div>')
    hl_col = _HEADLINE.get(scene.event_kind, TEXT)
    # 030: an amount wears its colour even in a headline (law 1)
    parts.append(f'<div class="headline type" style="color:{hl_col}">'
                 f"{_ep(scene.headline)}</div>")
    if scene.enemy:
        # 003: the always-on enemy bar + range chip, and the [i] badge
        # (top-right of the card — over the banner when there is one).
        if not plate_on_art:
            parts.append(_enemy_head_html(scene.enemy))
        parts.append(_dossier_html(scene.enemy))
    if scene.support:
        parts.append(f'<div class="support type">{_ep(scene.support)}</div>')
    # 030 Phase 4: the art band with one big number (the vault shelf).
    # getattr: a strip-less Scene from an older engine must render fine.
    if getattr(scene, "strip", None):
        parts.append(_strip_band_html(scene.strip))
    if scene.shard_note:
        parts.append(_shard_html(scene.shard_note))
    # 031 §9: a scene with a face — the NPC's portrait floats left of
    # the words, name under it; body text wraps beside it. Missing art
    # or an old wire (no npc) renders the same words, faceless.
    npc = getattr(scene, "npc", None) or {}
    if npc.get("portrait"):
        nurl = _portrait_data_url(npc["portrait"])
        if nurl:
            parts.append(
                f'<div class="npcbox later"><span class="npcimg" '
                f'style="background-color:{TEXT};'
                f"-webkit-mask-image:url('{nurl}');"
                f"mask-image:url('{nurl}');\"></span>"
                f'<span class="npclab">{_e(npc.get("name", ""))}</span>'
                f"</div>")
    in_fold = False
    for line in scene.body_lines:
        # 007: ▣ fold markers — long shop shelves collapse into a
        # <details> block (the [i]-dossier pattern, zero JS).
        if line.startswith("▣ "):
            parts.append(f'<details class="fold"><summary class="type">'
                         f"{_ep(line[2:])}</summary>")
            in_fold = True
            continue
        if line == "▣.":
            if in_fold:
                parts.append("</details>")
                in_fold = False
            continue
        if line.startswith("−") or line.startswith("-"):
            # losses stay red; gains are NOT green — gold paints gold,
            # XP paints XP, everything else keeps the card's ink.
            parts.append(f'<div class="body type" style="color:{RED}">'
                         f"{_ep(line)}</div>")
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
        # 031 §14: grid mode — a scene may ask for a card wall instead of
        # rows. Options that resolve a gear icon become picture cards;
        # the rest (hone, repair, back…) stay rows underneath. Numbering
        # runs across both in scene.options order, so the typed-number
        # fallback never notices the layout.
        grid_mode = bool(getattr(scene, "grid", False))
        rows, cards = [], []
        for i, o in enumerate(scene.options, 1):
            key_cls = " aether" if o.aether else ""
            # 019: a locked row is dimmed but stays a button — clicking
            # it is how the player asks why the gate is shut.
            opt_cls = " locked" if getattr(o, "locked", False) else ""
            hint = (f'<span class="hint">{_ep(o.hint)}</span>'
                    if o.hint else "")
            gicon = _opt_gear_icon(
                o.id, (getattr(scene, "option_art", None) or {})
                .get(o.id) or "")
            # 031 §13: rows carry art only when the engine names it
            tile = _option_tile_art(scene, o.id,
                                    bool(getattr(o, "locked", False)))
            if tile:
                opt_cls += " ftile"
            # 027: the count leaves the label and becomes a blue chip —
            # a notification reads as a notification, at a glance.
            bn = int(getattr(o, "badge", 0) or 0)
            badge = f'<span class="badge">{bn}</span>' if bn else ""
            # 014: the whisper glyph — [i] OUTSIDE the button, so tapping
            # it never fires the option; tip resolves by option id.
            # 031 §14: the card wall keeps it too, pinned to the corner.
            tip = tips.option_tip(o.id)
            info = (f'<span class="info" tabindex="0" role="note" '
                    f'data-tip="{_e(tip)}">i</span>' if tip else "")
            if grid_mode and gicon:
                # the card stacks its facts — cost, stat, durability
                # each on its own line (the button is a column flex,
                # so every span is a line of its own)
                stack = ("".join(
                    f'<span class="hint">{_ep(part)}</span>'
                    for part in o.hint.split(" · ") if part)
                    if o.hint else "")
                card = (f'<button type="button" class="opt gcard{opt_cls}" '
                        f'data-opt="{_e(o.id)}">'
                        f'<span class="key{key_cls}">{i}</span>{gicon}'
                        f'<span class="lbl">{_ep(o.label)}</span>{badge}'
                        f"{stack}</button>")
                cards.append(f'<div class="gcell">{card}{info}</div>')
                continue
            btn = (f'<button type="button" class="opt{opt_cls}" '
                   f'data-opt="{_e(o.id)}">'
                   f'<span class="key{key_cls}">{i}</span>{tile}{gicon}'
                   f'<span class="lbl">{_ep(o.label)}</span>{badge}'
                   f"{hint}</button>")
            rows.append(f'<div class="orow">{btn}{info}</div>')
        wall = (f'<div class="ggrid">{"".join(cards)}</div>'
                if cards else "")
        parts.append(f'<div class="options later">{wall}{"".join(rows)}'
                     f'<div class="reply">click an option — or reply '
                     f"with a number</div></div>")

    # 031 §11: the activity band — what tonight is already set to do,
    # a filled box with no outline at the foot of the options.
    if getattr(scene, "activity", ""):
        parts.append(f'<div class="actband later">{_ep(scene.activity)}'
                     "</div>")

    # 042: the presence grid rides under the options — who else stands
    # in this room, seven faces to a row, every face a door.
    if getattr(scene, "players_here", None):
        parts.append(_players_here_html(scene))

    if scene.meters:
        parts.append(_profile_html(scene))   # pack rides its right column
    else:
        parts.append(_inventory_html(scene))

    # 042: the sound layer's stamps — the hit flavored by damage type,
    # the room keyed for music, the fight marked wilds or warden.
    dtype = str((getattr(scene, "enemy", None) or {}).get("dtype", ""))
    dt = f' data-dtype="{_e(dtype)}"' if dtype else ""
    loc = str(getattr(scene, "location", "") or "")
    dt += f' data-loc="{_e(loc)}"' if loc else ""
    if getattr(scene, "enemy", None):
        fight = "warden" if scene.event_kind == "boss" else "wilds"
        dt += f' data-fight="{fight}"'
    return (f'<div class="card" data-scene="{_e(scene.scene_id)}"{dt}>'
            + "".join(parts) + "</div>")


# The card grammar — shared by the legacy chat card document and the 009
# game pane. Pure presentation tokens; hosts add their own page CSS.
SCENE_CSS = f"""
.card{{background:{PANEL};border:1px solid {BORDER};
 border-radius:0;margin:0;padding:12px 2ch 10px;color:{TEXT};
 font:14px/1.6 ui-monospace,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;
 font-variant-numeric:tabular-nums;overflow:hidden;position:relative;}}
/* ── 017/003: enemy header + [i] dossier ── */
.ehead{{display:flex;margin-top:6px;color:{DIM};}}
/* 030: one line at the top of the art — HP · ATK · DEF on a solid ink
   plate (the black-background rule); the [i] badge keeps the corner. */
.bwrap{{position:relative;}}
.bwrap .ehead{{position:absolute;top:8px;right:46px;margin:0;z-index:2;}}
.echip{{display:inline-flex;align-items:center;gap:1.5ch;background:{INK};
 border:1px solid {BORDER};padding:2px 8px;font-size:12px;cursor:help;}}
.echip .st{{display:inline-flex;align-items:center;gap:.5ch;
 font-variant-numeric:tabular-nums;white-space:nowrap;}}
.echip .eg{{vertical-align:0;}}
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
.notices{{border:1px solid {AETHER};
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
/* ── 030 Phase 5: the Morning Crier's broadsheet — a LIGHT sheet, dark
   ink, like paper. Only the artless fallback stays a dark board. ── */
/* 031 §12: the Crier reads as an actual newspaper — light sheet,
   centered masthead over a double rule, serif headline, ruled items,
   the ✕ folds it for the day. Height follows the news, not the art. */
.paper{{position:relative;margin:0 0 10px;background:{TEXT};
 border:1px solid {BORDER};overflow:hidden;min-height:96px;}}
.paper.noart{{background:{PANEL};}}
.paper .ptex{{position:absolute;inset:0;mask-size:cover;
 -webkit-mask-size:cover;mask-position:center;-webkit-mask-position:center;
 mask-repeat:no-repeat;-webkit-mask-repeat:no-repeat;
 image-rendering:pixelated;}}
.paper .pbody{{position:relative;z-index:1;
 padding:9px 2.5ch 10px 1.5ch;color:{INK};}}
.paper.noart .pbody{{color:{TEXT};}}
.paper .pmast{{font-weight:700;letter-spacing:.22em;font-size:12px;
 text-transform:uppercase;text-align:center;
 border-bottom:3px double currentColor;
 padding-bottom:4px;margin-bottom:6px;}}
.paper .phl{{font-weight:700;margin-bottom:5px;text-wrap:balance;
 font-family:Georgia,"Times New Roman",serif;font-size:15px;
 line-height:1.35;}}
.paper .pit{{display:-webkit-box;-webkit-line-clamp:2;
 -webkit-box-orient:vertical;overflow:hidden;padding:3px 0 2px;
 border-top:1px dotted color-mix(in srgb,currentColor 45%,transparent);}}
.paper .pit::before{{content:"· ";}}
.paper .pclose{{position:absolute;top:6px;right:6px;z-index:2;
 background:transparent;border:1px solid {FAINT};color:{INK};font:inherit;
 line-height:1.2;cursor:pointer;padding:1px .6ch;border-radius:0;}}
.paper .pclose:hover{{border-color:{INK};background:{INK};color:{TEXT};}}
.paper.noart .pclose{{background:{INK};border-color:{BORDER};color:{DIM};}}
.paper.noart .pclose:hover{{color:{TEXT};border-color:{TEXT};}}
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
/* ── 042: the presence grid — seven faces to a row ── */
.phere{{margin:12px 0 0;}}
.phere .phead{{color:{FAINT};text-transform:uppercase;
 letter-spacing:.1em;font-size:11px;margin-bottom:6px;}}
.pgrid{{display:grid;grid-template-columns:repeat(7,1fr);gap:6px;}}
.ptile{{display:flex;flex-direction:column;align-items:center;gap:2px;
 background:{PANEL2};border:1px solid {BORDER};border-radius:0;
 padding:5px 2px 4px;font:inherit;color:{TEXT};cursor:pointer;
 min-width:0;}}
.ptile:hover:not(:disabled){{border-color:{AETHER};}}
.ptile:focus-visible{{outline:1px solid {AETHER};outline-offset:1px;}}
.ptile .pfbox{{position:relative;display:block;height:56px;}}
.ptile .pface{{display:block;height:56px;width:auto;
 image-rendering:pixelated;}}
.ptile .pface.none{{display:block;height:56px;width:28px;
 background:{BORDER};}}
.ptile .pzzz{{position:absolute;top:-2px;right:-14px;background:{INK};
 border:1px solid {AETHER};color:{AETHER};font-size:9px;
 padding:0 3px;letter-spacing:.06em;}}
.ptile .prank{{position:absolute;top:-2px;left:-14px;background:{INK};
 border:1px solid {BORDER};color:{DIM};font-size:9px;padding:0 3px;
 font-variant-numeric:tabular-nums;}}
.ptile .pname{{max-width:100%;overflow:hidden;text-overflow:ellipsis;
 white-space:nowrap;font-size:11px;color:{TEXT};}}
.ptile .plvl{{font-size:10px;color:{FAINT};
 font-variant-numeric:tabular-nums;}}
.ptile .psub{{max-width:100%;overflow:hidden;text-overflow:ellipsis;
 white-space:nowrap;font-size:10px;color:{DIM};
 font-variant-numeric:tabular-nums;}}
/* ── 027: the pack popup — click an item, act on it ── */
.pmenu{{position:fixed;z-index:100;min-width:220px;max-width:300px;
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
.inv .item{{font:inherit;border-radius:0;padding:0;}}
.inv .item.act{{cursor:pointer;}}
.inv .item.act:hover,.inv .item.act:focus-visible{{
 border-color:{DIM};}}
.inv .item.act:hover .picon,.inv .item.act:focus-visible .picon{{
 background-color:{AETHER} !important;}}
.eyebrow{{color:{FAINT};text-transform:uppercase;letter-spacing:.08em;}}
.headline{{font-weight:700;margin:4px 0 0;text-wrap:balance;}}
.support{{color:{DIM};}}
.shard{{display:flex;gap:1ch;
 background:color-mix(in srgb,{AETHER} 5%,{PANEL});
 padding:8px 1.5ch;margin-top:8px;color:{DIM};}}
.shard .glyph{{color:{AETHER};flex:none;}}
.body{{margin:6px 0 0;white-space:pre-wrap;}}
/* ── 031 §9: the NPC block — portrait left of the words ── */
.npcbox{{float:left;display:flex;flex-direction:column;align-items:center;
 gap:3px;margin:8px 2ch 4px 0;}}
.npcbox .npcimg{{width:80px;aspect-ratio:100/200;display:block;
 mask-size:100% 100%;-webkit-mask-size:100% 100%;mask-repeat:no-repeat;
 -webkit-mask-repeat:no-repeat;image-rendering:pixelated;}}
.npcbox .npclab{{color:{DIM};text-transform:uppercase;
 letter-spacing:.12em;font-size:11px;}}
/* ── 031 §11: the activity band — a filled box, no outline ── */
.actband{{margin-top:10px;padding:8px 1.5ch;border:0;
 background:color-mix(in srgb,{VIOLET_SOFT} 14%,{PANEL});
 color:{VIOLET_SOFT};letter-spacing:.02em;}}
/* ── 030: the art band — one big number on a dark shelf ── */
.stripband{{position:relative;display:flex;align-items:center;
 justify-content:center;margin:8px 0 0;background:{INK};
 border:1px solid {BORDER};aspect-ratio:320/50;overflow:hidden;}}
.stripband .bart{{position:absolute;inset:0;mask-size:cover;
 -webkit-mask-size:cover;mask-position:center;-webkit-mask-position:center;
 mask-repeat:no-repeat;-webkit-mask-repeat:no-repeat;
 image-rendering:pixelated;}}
.stripband .btx{{position:relative;z-index:1;font-size:18px;
 font-weight:700;letter-spacing:.06em;font-variant-numeric:tabular-nums;}}
.stripband .btx .eg{{width:18px;height:18px;vertical-align:-3px;}}
/* ── 007: folded shop shelves (▣ markers) ── */
.fold{{margin:6px 0 0;}}
.fold summary{{list-style:none;cursor:pointer;user-select:none;
 color:{VIOLET_SOFT};}}
.fold summary::-webkit-details-marker{{display:none;}}
.fold summary::before{{content:"▸ ";color:{FAINT};}}
.fold[open] summary::before{{content:"▾ ";}}
.fold .body{{margin-left:1ch;}}
.options{{clear:both;margin:10px 0 0;padding:10px 0 0;
 border-top:1px dashed {BORDER};
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
/* ── 030: gate floor rows — a door you can see through ── */
.opt.ftile{{min-height:96px;}}
.farts{{flex:none;display:flex;gap:4px;align-items:center;}}
.fart{{display:inline-block;width:120px;max-width:24vw;height:84px;
 mask-size:cover;-webkit-mask-size:cover;mask-position:center;
 -webkit-mask-position:center;mask-repeat:no-repeat;
 -webkit-mask-repeat:no-repeat;image-rendering:pixelated;}}
.opt.ftile:hover .fart{{background-color:{TEXT};}}
.opt.ftile.locked:hover .fart{{background-color:{FAINT};}}
.opt:hover .gicon{{background-color:{TEXT};}}
.opt.locked .gicon,.opt.locked:hover .gicon{{background-color:{FAINT};}}
.orow{{display:flex;align-items:stretch;gap:5px;}}
.orow .opt{{flex:1;min-width:0;}}
/* ── 031 §14: the card wall — a shop shelf you look at, not read ── */
.ggrid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(148px,1fr));
 gap:6px;margin-bottom:6px;}}
.gcell{{position:relative;display:flex;}}
.gcard{{flex-direction:column;align-items:center;justify-content:flex-start;
 gap:6px;padding:22px 1ch 12px;text-align:center;position:relative;}}
.gcard .key{{position:absolute;top:5px;left:7px;}}
.gcard .gicon{{width:56px;height:56px;background-color:{TEXT};}}
.gcard:hover .gicon{{background-color:{GOLD};}}
.gcard.locked .gicon,.gcard.locked:hover .gicon{{background-color:{FAINT};}}
.gcard .lbl{{font-weight:700;line-height:1.3;}}
.gcard .hint{{margin-left:0;text-align:center;color:{DIM};
 display:block;white-space:nowrap;}}
.gcard .hint+.hint{{margin-top:-3px;}}
.gcard.locked .hint{{color:{FAINT};}}
.gpip{{display:inline-block;width:11px;height:11px;margin:0 1px;
 vertical-align:-1px;mask-size:contain;-webkit-mask-size:contain;
 mask-repeat:no-repeat;-webkit-mask-repeat:no-repeat;
 mask-position:center;-webkit-mask-position:center;
 image-rendering:pixelated;}}
.opt.locked .gpip,.gcard.locked .gpip{{background-color:{FAINT}!important;}}
.opt.locked .amt,.gcard.locked .amt{{color:{FAINT}!important;}}
.gcell .info{{position:absolute;top:5px;right:5px;border:0;
 background:none;padding:0;}}
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
/* 030 law 3: a number wears its colour — the meter labels match their
   bars, not just the blocks. Blue stays energy + notifications only. */
.meter.hp{{color:{OK};}}
.meter.hp .blocks{{color:{OK};}}
.meter.hp.low{{color:{RED};}}
.meter.hp.low .blocks{{color:{RED};}}
.meter.en{{color:{AETHER};}}
.meter.en .blocks{{color:{AETHER};}}
.meter.ae{{color:{VIOLET_SOFT};}}
.meter.ae .blocks{{color:{VIOLET_SOFT};}}
.amt{{white-space:nowrap;}}
/* ── 030: the profile block — portrait beside the rail + pip rows ──
   031 §4: the ident band opens it — name + calling left, LEVEL and
   COINS bold right — and carries the divider the profile used to. */
.ident{{display:flex;align-items:baseline;gap:2ch;margin-top:10px;
 padding-top:8px;border-top:1px dashed {BORDER};}}
.ident .idl{{display:inline-flex;align-items:baseline;gap:1.5ch;
 min-width:0;}}
.ident .idname{{font-weight:700;color:{TEXT};}}
.ident .idwho{{color:{DIM};text-transform:uppercase;
 letter-spacing:.08em;font-size:12px;}}
.ident .idfac{{color:{DIM};font-size:12px;cursor:help;
 white-space:nowrap;}}
.ident .idfac b{{color:{TEXT};font-weight:700;}}
.ident .idr{{margin-left:auto;display:inline-flex;gap:2ch;
 white-space:nowrap;}}
.ident .idlv{{font-weight:700;color:{TEXT};cursor:help;}}
.ident .idgold{{font-weight:700;color:{GOLD};cursor:help;}}
.profile{{display:flex;gap:2ch;align-items:stretch;margin-top:8px;}}
.profile .portrait{{flex:none;align-self:stretch;height:auto;width:auto;
 min-height:200px;image-rendering:pixelated;}}
.profile .pcol{{flex:1;min-width:0;}}
.profile .rail{{margin-top:0;padding-top:0;border-top:0;}}
.profile .inv{{border-top:0;padding-top:0;margin-top:8px;}}
.piprows{{margin-top:8px;color:{DIM};}}
.piprow{{display:flex;align-items:center;gap:1ch;margin-top:4px;
 cursor:help;}}
.piprow .plab{{flex:none;min-width:8ch;font-variant-numeric:tabular-nums;}}
.piprow .pips{{display:inline-grid;grid-template-columns:repeat(10,18px);
 gap:1px;}}
.pip{{width:16px;height:16px;display:inline-block;
 mask-size:100% 100%;-webkit-mask-size:100% 100%;mask-repeat:no-repeat;
 -webkit-mask-repeat:no-repeat;image-rendering:pixelated;}}
/* ── 031 §3: the pack is a slot grid — squares fill Minecraft-style;
   the weapon in use and the shield sit promoted in two boxes on top ── */
.inv{{margin-top:8px;padding-top:8px;border-top:1px dashed {BORDER};}}
.invlbl{{color:{FAINT};text-transform:uppercase;letter-spacing:.08em;
 display:block;margin-bottom:5px;}}
.handrow{{display:flex;gap:2ch;margin-bottom:6px;}}
.hcell{{display:inline-flex;flex-direction:column;gap:3px;}}
.hlab{{color:{FAINT};text-transform:uppercase;letter-spacing:.08em;
 font-size:10px;}}
.slot{{position:relative;width:40px;height:40px;flex:none;
 background:{INK};border:1px solid {BORDER};display:inline-flex;
 align-items:center;justify-content:center;cursor:help;outline:none;}}
.hcell .slot{{width:50px;height:50px;}}
.slot.empty{{border-style:dashed;opacity:.5;}}
.slotgrid{{display:grid;grid-template-columns:repeat({_PACK_COLS},40px);
 gap:4px;}}
.picon{{width:28px;height:28px;flex:none;display:inline-block;
 mask-size:100% 100%;-webkit-mask-size:100% 100%;mask-repeat:no-repeat;
 -webkit-mask-repeat:no-repeat;image-rendering:pixelated;}}
.hcell .picon{{width:34px;height:34px;}}
.slot .ct{{position:absolute;right:2px;bottom:0;color:{TEXT};
 font-size:11px;line-height:1.2;text-shadow:0 0 3px {INK};}}
.slot .dur{{position:absolute;left:3px;right:3px;bottom:2px;height:3px;
 background:{BORDER};}}
.slot .durf{{display:block;height:100%;}}
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
/* ── 040: the phone layout — the player area must be SEEN. The portrait
   stops stretching to the column's height (sizePortrait pins it small),
   the meters keep the full width beside it, and the pack's fixed 40px
   grid relaxes so six slots never overflow a 360px screen. ── */
@media (max-width: 520px){{
 .profile{{gap:1.5ch;align-items:flex-start;}}
 .profile .portrait{{align-self:flex-start;min-height:0;height:132px;}}
 .ident{{flex-wrap:wrap;row-gap:2px;}}
 .ident .idr{{margin-left:auto;}}
 .rail{{gap:.5ch 1.5ch;}}
 .piprow .pips{{grid-template-columns:repeat(10,minmax(12px,18px));}}
 .pip{{width:100%;max-width:16px;}}
 .slotgrid{{grid-template-columns:repeat({_PACK_COLS},minmax(32px,40px));
  max-width:100%;}}
 .slot{{width:auto;min-width:32px;aspect-ratio:1;height:auto;}}
 .hcell .slot{{width:44px;height:44px;}}
 .picon{{width:24px;height:24px;}}
}}
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
