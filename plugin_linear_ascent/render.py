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

from . import colors as _colors, economy, icons
from .engine import notices, tips
from .engine.scene import Meters, Scene
from .version import VERSION

# ── tokens (009: the terminal law — worldd/static/site/mock/mock.css) ────
INK = "#000000"
PANEL = "#000000"
PANEL2 = "#000000"
SLATE = "#1f2024"     # 062: the solid box's ground
BORDER = "#5b5952"
DIM = "#5b5952"
FAINT = "#5b5952"
TEXT = "#adaba0"
GOLD = "#f5b825"
AETHER = "#45d0c0"
VIOLET = "#d967c8"
VIOLET_SOFT = "#d967c8"
RED = "#f26541"
OK = "#8ed24a"
ORANGE = "#f5b825"
BRIGHT = "#fbfbf7"
ART = "#d9d9d3"
ARTBRIGHT = "#fbfbf7"
BROWN = "#b5722f"

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
# 057: every weapon wears its own face — per-slug 1-bit art at two
# sizes: icons/<slug>_30x48.png replaces the shared line glyph wherever
# FORGE gear renders; large/<slug>_100x160.png rides the card's hover
# tip. keen/warded variants reuse their base weapon's art (the style
# tint carries the difference, same as the pack strip).
_WEAPONS_ART = os.path.join(_ART_ROOT, "weapons")
# 058: the rest of the shop wears its own face too — shields, focuses,
# armor, boots and the relics, same two sizes, shipped under art/gear.
# Weapons keep their 057 home; the lookup tries both.
_GEAR_ART = os.path.join(_ART_ROOT, "gear")
# 009: ONE font everywhere — the homepage's bitmap IBM VGA 8×16, shipped
# inside the card CSS as a data: url so both hosts (web pane and legacy
# chat card) render it without a network fetch.
_FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "content", "fonts")
with open(os.path.join(_FONTS, "WebPlus_IBM_VGA_8x16.woff"), "rb") as _f:
    _VGA_B64 = base64.b64encode(_f.read()).decode("ascii")
FONT_STACK = '"VGA","Px437 IBM VGA8","Courier New",monospace'

# 011 event animations tint by their moment, not the floor mood.
_FX_TINT = {"ascent_open": VIOLET, "ascent_title": VIOLET_SOFT,
            # 016 intro movie — world scenes dim, the enemy violet,
            # hearth and aether gold.
            "intro_aldervale": DIM, "intro_theft": VIOLET,
            "intro_tower": DIM, "intro_warden": VIOLET,
            "intro_refugee": DIM, "intro_roothollow": GOLD,
            "intro_stone": GOLD, "intro_shard": GOLD,
            "intro_muster": DIM}


# ── 078: the art-base seam ────────────────────────────────────────────────
# ART_BASE unset (the default) inlines every image as base64 — the legacy
# self-contained card, no host wiring needed. A host that mounts
# content/art statically calls set_art_base("/static/laart") and every
# banner/GIF/portrait/gear icon becomes a small, versioned, immutable-
# cacheable URL instead of ~50–650 KB of base64 riding EVERY response.
# The tiny generated SVG glyphs (icons.py) and the VGA font stay inline.
ART_BASE = ""


def set_art_base(base: str) -> None:
    global ART_BASE
    ART_BASE = (base or "").rstrip("/")
    for fn in (_banner_data_url, _sigil_half_data_url, _gear_art_url,
               _fx_data_url, _fx_split, _paper_tex_url, _strip_art_url,
               _portrait_art, _portrait_data_url):
        fn.cache_clear()


def _art_url(path: str, mime: str) -> str:
    """The one door art ships through: a versioned static URL when the
    host mounted the tree, the inline data URL otherwise."""
    if ART_BASE:
        rel = os.path.relpath(path, _ART_ROOT).replace(os.sep, "/")
        return f"{ART_BASE}/{rel}?v={VERSION}"
    b64 = base64.b64encode(open(path, "rb").read()).decode()
    return f"data:image/{mime};base64,{b64}"


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
    return ART


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
                w, h = (int(n) for n in size.split("x"))
                return _art_url(path, "png"), w, h
    return None


@lru_cache(maxsize=None)
def _sigil_half_data_url(slug: str) -> tuple[str, int, int] | None:
    """(data_url, width, height) of the strip's half-res sigil.

    010: the card strip alone downshifts to 160x56 — deliberately not a
    size in _banner_data_url, so hall galleries and banner pages keep
    full res. A missing half falls back rather than blank the strip."""
    for size in ("160x56", "320x112"):
        path = os.path.join(_SIGILS, f"{slug}_{size}.png")
        if os.path.exists(path):
            w, h = (int(n) for n in size.split("x"))
            return _art_url(path, "png"), w, h
    return None


@lru_cache(maxsize=None)
def _gear_art_url(slug: str, kind: str) -> str | None:
    """data URL for an item's own 1-bit art, or None.
    kind: "icons" (30x48) or "large" (100x160). Weapons live under
    art/weapons (057), everything else under art/gear (058)."""
    size = "30x48" if kind == "icons" else "100x160"
    for art_dir in (_WEAPONS_ART, _GEAR_ART):
        path = os.path.join(art_dir, kind, f"{slug}_{size}.png")
        if os.path.exists(path):
            return _art_url(path, "png")
    return None


def _gear_art_slug(slug: str) -> str:
    """The slug whose art an item draws — keen/warded variants reuse
    their base item's face; relics draw their own; "" when the slug
    is neither FORGE gear nor a relic."""
    g = economy.FORGE.get(slug)
    if g is not None:
        return g.base or slug
    if slug in economy.RELICS or slug in economy.APOTHECARY \
            or slug in economy.PACKS:
        return slug
    return ""


@lru_cache(maxsize=None)
def _fx_data_url(slug: str) -> tuple[str, int, int] | None:
    """(data_url, width, height) for an event animation, or None.

    White-ink 1-bit GIFs from tools/generate_event_gifs.py, used exactly
    like the PNG banners: as an alpha mask over a tint color. Chromium
    (Luna's shell) animates GIF masks, so the kill plays in the card."""
    for size in ("320x112", "320x200"):
        path = os.path.join(_EVENTS, f"{slug}_{size}.gif")
        if os.path.exists(path):
            w, h = (int(n) for n in size.split("x"))
            return _art_url(path, "gif"), w, h
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
        return _art_url(path, "png")
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
    # 009: no texture — the terminal law prints the Crier as brown ink
    # on the black sheet; the words are the paper.
    tex = ""
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
        return _art_url(path, "png")
    return None


# ── 009: the big ANSI letters — cfonts-style block caps drawn with
# half-block characters (▀▄█), three text lines tall. One font for every
# number a screen shouts; digits and the coin wear gold, words wear white.
_BIG = {
    "0": ("111", "101", "101", "101", "111"),
    "1": ("010", "110", "010", "010", "111"),
    "2": ("111", "001", "111", "100", "111"),
    "3": ("111", "001", "011", "001", "111"),
    "4": ("101", "101", "111", "001", "001"),
    "5": ("111", "100", "111", "001", "111"),
    "6": ("111", "100", "111", "101", "111"),
    "7": ("111", "001", "001", "010", "010"),
    "8": ("111", "101", "111", "101", "111"),
    "9": ("111", "101", "111", "001", "111"),
    "A": ("111", "101", "111", "101", "101"),
    "B": ("110", "101", "110", "101", "110"),
    "C": ("111", "100", "100", "100", "111"),
    "D": ("110", "101", "101", "101", "110"),
    "E": ("111", "100", "111", "100", "111"),
    "F": ("111", "100", "111", "100", "100"),
    "G": ("111", "100", "101", "101", "111"),
    "H": ("101", "101", "111", "101", "101"),
    "I": ("111", "010", "010", "010", "111"),
    "J": ("011", "001", "001", "101", "111"),
    "K": ("101", "101", "110", "101", "101"),
    "L": ("100", "100", "100", "100", "111"),
    "M": ("10001", "11011", "10101", "10001", "10001"),
    "N": ("1001", "1101", "1011", "1001", "1001"),
    "O": ("111", "101", "101", "101", "111"),
    "P": ("111", "101", "111", "100", "100"),
    "Q": ("1110", "1010", "1010", "1110", "0001"),
    "R": ("111", "101", "110", "101", "101"),
    "S": ("111", "100", "111", "001", "111"),
    "T": ("111", "010", "010", "010", "010"),
    "U": ("101", "101", "101", "101", "111"),
    "V": ("101", "101", "101", "101", "010"),
    "W": ("10001", "10001", "10101", "11011", "10001"),
    "X": ("101", "101", "010", "101", "101"),
    "Y": ("101", "101", "010", "010", "010"),
    "Z": ("111", "001", "010", "100", "111"),
    ":": ("0", "1", "0", "1", "0"),
    "-": ("000", "000", "111", "000", "000"),
    "+": ("000", "010", "111", "010", "000"),
    ".": ("0", "0", "0", "0", "1"),
    ",": ("00", "00", "00", "01", "10"),
    "!": ("1", "1", "1", "0", "1"),
    "/": ("001", "001", "010", "100", "100"),
    "◎": ("01110", "10001", "10101", "10001", "01110"),
    "◈": ("01110", "10001", "10101", "10001", "01110"),
    " ": ("00", "00", "00", "00", "00"),
}


def _big_html(text: str, tint: str = "") -> str:
    """Three <div> lines of half-blocks; digits/coin gold, letters white.
    A tint paints the WHOLE run one colour — the win card's XP shouts in
    violet, its gold in gold, digits and word alike."""
    lines = [[], [], []]
    for ch in str(text).upper():
        g = _BIG.get(ch)
        if g is None:
            continue
        gold = ch.isdigit() or ch in "◎◈,.+"
        cls = "binh" if tint else ("bgold" if gold else "bwhite")
        w = max(len(r) for r in g)
        grid = [r.ljust(w, "0") for r in g] + ["0" * w]
        for li in range(3):
            top, bot = grid[2 * li], grid[2 * li + 1]
            s = "".join(
                "█" if t == "1" and b == "1" else
                "▀" if t == "1" else
                "▄" if b == "1" else " "
                for t, b in zip(top, bot))
            lines[li].append((cls, s + " "))
    out = []
    for segs in lines:
        row = "".join(f'<span class="{c}">{_e(s)}</span>' for c, s in segs)
        out.append(f"<div>{row}</div>")
    style = f' style="color:{tint}"' if tint else ""
    return f'<div class="bigtx"{style}>{"".join(out)}</div>'


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
               f'style="background-color:{ART};'
               f"-webkit-mask-image:url('{url}');"
               f"mask-image:url('{url}');\"></span>")
    band = f'<div class="stripband later">{art}</div>' if art else ""
    return (f"{band}"
            f'<div class="striptx later">{_big_html(text)}</div>')


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
# 053: a fumbled swing must not read like a hit — the whole miss
# sentence (through the School pointer) wears ember.
_HIT_MISS = re.compile(r"ATTACK MISSED — .*?Improve at the School\.")


def _combat_html(line: str) -> str:
    # 042: the classes are the sound layer's ears — chp is HP lost,
    # chit damage dealt. Purely semantic; the color still paints.
    s = _e(line)
    s = _HIT_MISS.sub(
        lambda m: f'<span class="cmiss" style="color:{DIM}">'
                  f"{m.group(0)}</span>", s)
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
# The plain reward lines stay on the TEXT surface (the agent reads them)
# but leave the card when the tally shouts the same numbers big — one
# haul, said once. Rested/assist/spoils lines don't match and stay.
_TALLY_SAID = re.compile(
    r"^\+ (?:◈ )?[\d,]+ (?:XP|gold)(?: \(young-tower bounty\))?$")
# 030: XP wears VIOLET_SOFT everywhere now (law 3) — blue stays the
# notification ink plus energy amounts, nothing else.
_TALLY_MARK = {"gold": ("coin", GOLD), "aether": ("aether", VIOLET_SOFT)}
_TALLY_WORD = {"gold": "gold", "aether": "XP"}


def _tally_html(tally: list[dict], lean: bool = False) -> str:
    """One column per haul, side by side and centered: the amount shouts
    in the big font ([icon] 8 XP · [icon] 36 GOLD, each in its own
    colour), the marks heap under their own amount. Past the cap the
    heap stays home — the big numeral already carries the size.

    `lean` (067 phase 8, roy): the arena victory overlay — only the big
    amount lines, no mark heaps and no note, no slab behind; the scene
    stays visible through it."""
    cols = []
    for item in tally:
        kind = str(item.get("kind", ""))
        n = int(item.get("n", 0) or 0)
        if n <= 0 or kind not in _TALLY_MARK:
            continue
        key, tint = _TALLY_MARK[kind]
        label = f"+{n:,} {_TALLY_WORD[kind]}"
        # 0.97.1 (roy): the lean win amounts read as gains — the number
        # wears a + on its right ("29+ XP").
        big = (f"{n:,}+ {_TALLY_WORD[kind]}" if lean
               else f"{n:,} {_TALLY_WORD[kind]}")
        # 0.97.2 (roy): the icon's shadow lives on a wrapper — CSS paints
        # mask AFTER filter, so a drop-shadow on the masked .eg itself is
        # clipped away by its own mask and never reaches the screen.
        head = (f'<div class="thead" style="color:{tint}">'
                f'<span class="egsh">{_eglyph(key)}</span>'
                f"{_big_html(big, tint)}</div>")
        heap = ""
        if not lean and n < TALLY_CAP:
            heap = (f'<span class="tmarks" style="color:{tint}" '
                    f'aria-hidden="true">' + _eglyph(key) * n + "</span>")
        note = str(item.get("note", ""))
        note_html = ("" if lean else
                     (f'<div class="tnote">{_e(note)}</div>' if note else ""))
        cols.append(f'<div class="thaul" title="{_e(label)}">'
                    f'<span class="tsr">{_e(label)}</span>'
                    f"{head}{heap}{note_html}</div>")
    if not cols:
        return ""
    cls = "tallies lean" if lean else "tallies"
    return f'<div class="{cls}">{"".join(cols)}</div>'


# ── 027: the notice board ───────────────────────────────────────────────
# A count with no sentence around it is a riddle. Every waiting thing gets
# a row at the TOP of the card: the verb, the room, the number, the worth —
# and the row is the shortcut. Blue is the notification ink everywhere in
# this game now; it never means a stat.
_NOTICE_WORD = {"collect": "COLLECT", "plan": "PLAN", "levelup": "LEVEL-UP"}


def _weekpick_html(nt: dict) -> str:
    """070: ANSI number rail inside waiting-for-you — one square around
    the numbers, labels outside, click a row to choose."""
    choices = list(nt.get("choices") or [])
    rows = []
    for c in choices:
        hint = str(c.get("hint") or "")
        hint_h = (f'<span class="whint">{_ep(hint)}</span>' if hint else "")
        title = _e(str(c.get("title") or ""))
        body = _ep(str(c.get("text") or ""))
        rows.append(
            f'<button type="button" class="wrow" '
            f'data-opt="{_e(str(c.get("opt") or ""))}">'
            f'<span class="wnum">{int(c.get("n") or 0)}</span>'
            f'<span class="wtx"><span class="wtitle">{title}</span>'
            f' — {body}</span>{hint_h}</button>')
    if not rows:
        return (f'<div class="weekbox"><div class="whead">'
                f'{_ep(str(nt.get("text", "")))}</div></div>')
    return (f'<div class="weekbox">'
            f'<div class="whead">{_ep(str(nt.get("text", "")))}</div>'
            f'<div class="wbody"><div class="wrail" aria-hidden="true"></div>'
            f'<div class="wlist">{"".join(rows)}</div></div></div>')


def _notices_html(notices: list[dict]) -> str:
    rows = []
    for nt in notices:
        kind = str(nt.get("kind", "collect"))
        if kind == "weekpick":
            rows.append(_weekpick_html(nt))
            continue
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
# 052: a portrait_* slug turns the tile into a character card — the
# figure stands full-height on a shared ground line, the name under the
# picture; the giant's 1.3x frame makes him tower without special cases.

_CHAR_PIC_H = 180  # a 100x200 figure's card height; taller frames scale


def _gallery_html(gallery: list[dict]) -> str:
    tiles = []
    chars = False
    for g in gallery:
        slug = str(g.get("slug", ""))
        if slug.startswith("portrait_"):
            art = _portrait_art(slug[len("portrait_"):])
            chars = True
        else:
            art = _banner_data_url(slug) if slug else None
        if art and slug.startswith("portrait_"):
            url, w, h = art
            pic = (f'<span class="gbox"><span class="gpic pchar" '
                   f'style="background-color:{ART};'
                   f"aspect-ratio:{w}/{h};"
                   f"height:{round(_CHAR_PIC_H * h / 200)}px;"
                   f"-webkit-mask-image:url('{url}');"
                   f"mask-image:url('{url}');\"></span></span>")
        elif art:
            url, w, h = art
            pic = (f'<span class="gpic" style="background-color:{ART};'
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
    cls = "gal chars later" if chars else "gal later"
    return f'<div class="{cls}">{"".join(tiles)}</div>'


# ── 042: the presence grid — who else stands in this room ───────────────
# Seven faces to a row, the same race portraits the profile rail wears
# (052: the chosen character is the face — armor never touches it). A
# sleeping climber wears a Zzz chip; hover carries coin and energy;
# every face is a door to that climber's page (data-opt="pv:<name>").

def _tile_portrait_url(race: str) -> str | None:
    if race and _portrait_art(race):
        return _portrait_data_url(race)
    return _portrait_data_url("human")


def player_tiles_html(tiles: list) -> str:
    """Just the tile buttons — the grid's cells. Public: worldd's
    room_more endpoint renders the unfolded batch with the same hand."""
    cells = []
    for t in tiles:
        if not isinstance(t, dict) or not t.get("name"):
            continue
        name = str(t["name"])
        race = str(t.get("race") or "")
        url = _tile_portrait_url(race)
        giant = " giant" if race == "giant" else ""
        face = (f'<img class="pface{giant}" src="{url}" alt="">' if url
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
    return "".join(cells)


def _players_here_html(scene: Scene) -> str:
    tiles = getattr(scene, "players_here", None) or []
    if not tiles:
        return ""
    title = _e(str(getattr(scene, "players_title", "") or "PLAYERS HERE"))
    cells = player_tiles_html(tiles)
    if not cells:
        return ""
    shown = sum(1 for t in tiles if isinstance(t, dict) and t.get("name"))
    total = int(getattr(scene, "players_total", 0) or 0)
    more = ""
    if total > shown:
        more = (f'<div class="pmrow"><button type="button" class="pmore">'
                f"MORE {total - shown} PLAYERS &gt;</button></div>")
    return (f'<div class="phere later"><div class="phead">{title}</div>'
            f'<div class="pgrid">{cells}</div>{more}</div>')


def _blocks(cur: int, cap: int, cells: int = 10) -> str:
    cur = max(0, min(cur, cap))
    filled = round(cells * cur / cap) if cap else 0
    return (f"{'▓' * filled}"
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
_TIP_FACTION = ("Your faction. Go to the Guildhall on Roothollow main "
                "street — home of all the factions — for the store, the "
                "armory and your kin.")


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
                 f'of {_e(fac)}</span>')
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

_TIP_ATK = ("ATK — your total attack: class base plus weapon and honing. "
            "Every 3 points fills half a sword.")
_TIP_DEF = ("DEF — your total defense: shield, armor and honing. "
            "Every 3 points fills half an icon.")
_TIP_SPD = ("SPD — how fast you move (your build plus your boots). "
            "Higher speed helps you dodge, get away, and stay ahead "
            "when something chases you. Every point fills a bolt.")


def _portrait_slug(scene: Scene) -> str:
    """052: the chosen character IS the face — warrior, elf or giant,
    one portrait per line, the armor-tier wardrobe is gone (the pack
    grid and the DEF pips carry the progression now). Docs older than
    the race question wear the warrior frame."""
    race = getattr(scene.meters, "race", "") or ""
    if race and _portrait_art(race):
        return race
    return "human"


# the giant's frame is 1.3x the human one — his size is baked into the
# PNG's aspect, so every natural-ratio surface draws him bigger.
_PORTRAIT_SIZES = ((100, 200), (140, 260))


@lru_cache(maxsize=None)
def _portrait_art(slug: str) -> tuple[str, int, int] | None:
    for w, h in _PORTRAIT_SIZES:
        path = os.path.join(_PORTRAITS, f"portrait_{slug}_{w}x{h}.png")
        if os.path.exists(path):
            return _art_url(path, "png"), w, h
    return None


@lru_cache(maxsize=None)
def _portrait_data_url(slug: str) -> str | None:
    art = _portrait_art(slug)
    return art[0] if art else None


def _portrait_html(url: str | None, fig: dict | None = None) -> str:
    """The shared PNG/experimental-canvas portrait.

    Both the viewer rail and another climber's 072 public sheet use this
    path, so Labs cannot silently fall back to a PNG on player pages.
    """
    if not url:
        return ""
    if fig and fig.get("race"):
        w, h = (int((fig.get("px") or [100, 200])[0]),
                int((fig.get("px") or [100, 200])[1]))
        spec = _e(_json.dumps(fig, separators=(",", ":")))
        return (
            f'<img class="portrait later figure3d-fallback" src="{url}" '
            f'alt="" hidden>'
            f'<canvas class="portrait later figure3d" width="{w}" '
            f'height="{h}" data-figure3d="{spec}"></canvas>')
    return f'<img class="portrait later" src="{url}" alt="">'


# ── 010: the Gmail glyph + the profile's "connect Gmail" box ────────────
# The 4-ink 16×16 Google "G", drawn in the game's own inks — no true blue
# in the warmed-CGA 16, so cyan-teal energy stands in for Google blue.
# Authored once here and mirrored by the website door, so both wear the
# exact same glyph. See plans/010's gen_google_g.py for the shape.

_G_BLUE, _G_RED, _G_YELLOW, _G_GREEN = "#45d0c0", "#f26541", "#f5b825", "#8ed24a"


def _g_cell(x: int, y: int) -> str | None:
    import math
    cx = cy = 7.5
    inner, outer = 3.4, 7.35
    dx, dy = x - cx, y - cy
    d = math.hypot(dx, dy)
    if 7 <= y <= 8 and 7.0 <= x <= 12.0 and d <= outer:
        return _G_BLUE                       # the crossbar tongue
    if d < inner or d > outer:
        return None
    ang = math.degrees(math.atan2(-dy, dx))
    if 3 < ang < 48:
        return None                          # the mouth notch
    if -48 <= ang <= 3:
        return _G_BLUE
    if 48 <= ang < 140:
        return _G_RED
    if ang >= 140 or ang <= -140:
        return _G_YELLOW
    return _G_GREEN


@lru_cache(maxsize=1)
def google_g() -> str:
    """Inline <svg> of the 4-ink Google G, 16×16, crisp when scaled."""
    rects = []
    for y in range(16):
        for x in range(16):
            c = _g_cell(x, y)
            if c:
                rects.append(f'<rect x="{x}" y="{y}" width="1" '
                             f'height="1" fill="{c}"/>')
    return ('<svg class="gicon-svg" xmlns="http://www.w3.org/2000/svg" '
            'viewBox="0 0 16 16" shape-rendering="crispEdges">'
            + "".join(rects) + "</svg>")


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
                  + _pip_row("armor", "DEF", getattr(m, "dfs", 0), TEXT,
                             _TIP_DEF)
                  + spd_row
                  + "</div>")
    ident = _ident_html(m)
    # 069: the pack rides UNDER the profile block, full width — the gear
    # map (slots either side of the portrait) takes the left, the meters
    # and pip rows the right.
    pack = _inventory_html(scene)
    url = _portrait_data_url(_portrait_slug(scene))
    if not url:
        return ident + right + pack
    # a real <img>, not a masked div: with the height set to the slot
    # column's, width:auto keeps the 1:2 ratio from the PNG itself —
    # the one sizing rule every webview agrees on. The ink is baked
    # white.
    # 071: Labs figure3d replaces the PNG with a same-size canvas;
    # the <img> stays as a hidden fallback if WebGL is dead.
    fig = getattr(scene, "figure3d", None)
    figure = _portrait_html(url, fig)
    return (ident
            + '<div class="profile">'
            + _gearmap_html(scene, figure)
            + f'<div class="pcol">{right}</div></div>'
            + pack)


# ── 069: the gear map — seven slots around the figure ────────────────────
# Minecraft's grammar: the figure in the middle, LEFT column top→bottom
# charm/potion · armour · boots, RIGHT column shield · weapon · weapon 2 ·
# weapon 3. Every slot is ALWAYS drawn, in one of three states: locked
# (dark grey box, a lock, the hover says how to open it and at what
# level), empty (dotted, nothing in it), filled (the icon; the click
# offers "Move to the pack"). Nothing in the pack counts — only what
# sits here.

_SLOT_EMPTY_TIP = {
    "charm": "charm pouch — empty. Set a luck charm, a potion or a "
             "relic from the pack; only what sits here acts in a fight.",
    "armor": "armour — none worn. Wear a piece from the pack; it counts "
             "only on your back.",
    "shoes": "boots — none worn. Wear a pair from the pack; speed comes "
             "only from worn boots.",
    "shield": "shield — none held. Hold one from the pack.",
    "weapon": "weapon — an open grip. Hold a blade, bow or staff from "
              "the pack.",
    "weapon2": "weapon 2 — an open grip. Hold a second weapon from the "
               "pack; each weapon in hand is its own attack.",
    "weapon3": "weapon 3 — an open grip. Hold a third weapon from the "
               "pack.",
}


def _slotmap_cell(d: dict, *, readonly: bool = False) -> str:
    """One slot of the gear map in its state."""
    key = str(d.get("key", ""))
    st = d.get("state", "empty")
    if st == "locked":
        url = icons.icon_data_url("lock")
        tip = str(d.get("lock_text") or "Locked.")
        return (f'<span class="slot gm locked" data-key="{_e(key)}" '
                f'data-tip="{_e(tip)}" tabindex="0">'
                f'<span class="picon" style="background-color:#555;'
                f"-webkit-mask-image:url('{url}');mask-image:url('{url}');"
                '"></span></span>')
    if st != "filled" or not d.get("slug"):
        tip = _SLOT_EMPTY_TIP.get(key, f"{d.get('label', key)} — empty")
        return (f'<span class="slot gm empty" data-key="{_e(key)}" '
                f'data-tip="{_e(tip)}"></span>')
    cell_d = dict(d)
    if readonly:
        cell_d["equipped"] = True
        cell_d.pop("acts", None)
        cell_d.pop("why", None)
    cell = _slot_cell(cell_d, readonly=readonly)
    lead = ' lead' if d.get("lead") else ''
    if readonly:
        return cell.replace('class="slot item',
                            f'class="slot gm item{lead}', 1) \
                   .replace('<span ',
                            f'<span data-key="{_e(key)}" ', 1)
    return cell.replace('class="slot item act',
                        f'class="slot gm item act{lead}', 1) \
               .replace('<button type="button" ',
                        f'<button type="button" data-key="{_e(key)}" ', 1)


def _gearmap_from_slots(slots: list, figure: str, *,
                        readonly: bool = False) -> str:
    if not slots:
        return figure
    left = "".join(_slotmap_cell(d, readonly=readonly) for d in slots
                   if d.get("side") == "left")
    right = "".join(_slotmap_cell(d, readonly=readonly) for d in slots
                    if d.get("side") == "right")
    return ('<div class="gearmap later">'
            f'<div class="slotcol left">{left}</div>'
            f'<div class="pwrap">{figure}</div>'
            f'<div class="slotcol right">{right}</div></div>')


def _gearmap_html(scene: Scene, figure: str) -> str:
    slots = list(getattr(scene, "slots", None) or [])
    if not slots:
        # an old scene half (pre-069 server) — the figure alone
        return figure
    return _gearmap_from_slots(slots, figure)


def player_avatar_html(sheet: dict) -> str:
    """072: another climber's public look — ident, figure, worn slots,
    meters and pip rows. Read-only. Not the viewer's profile (no pack,
    no live counters, no unequip)."""
    if not isinstance(sheet, dict) or not sheet.get("name"):
        return ""
    name = str(sheet.get("name") or "")
    race = str(sheet.get("race") or "")
    clazz = str(sheet.get("clazz") or "")
    who = " ".join(x for x in (race, clazz) if x)
    fac = str(sheet.get("faction") or sheet.get("guild") or "")
    left = f'<span class="idname">{_e(name)}</span>'
    if who:
        left += f'<span class="idwho">{_e(who)}</span>'
    if fac:
        left += f'<span class="idfac">of {_e(fac)}</span>'
    gold = int(sheet.get("gold", 0) or 0)
    level = int(sheet.get("level", 1) or 1)
    right = (f'<span class="idlv">LEVEL {level}</span>'
             f'<span class="idgold">COINS {_eglyph("coin")} '
             f"{gold:,}</span>")
    ident = (f'<div class="ident later"><span class="idl">{left}</span>'
             f'<span class="idr">{right}</span></div>')
    slug = race if race and _portrait_art(race) else "human"
    url = _portrait_data_url(slug)
    figure = _portrait_html(url, sheet.get("figure3d"))
    slots = [sl for sl in (sheet.get("slots") or [])
             if isinstance(sl, dict)]
    gear = _gearmap_from_slots(slots, figure, readonly=True)
    hp = int(sheet.get("hp", 0) or 0)
    hp_max = int(sheet.get("hp_max", 0) or 0) or max(hp, 1)
    energy = int(sheet.get("energy", 0) or 0)
    energy_max = int(sheet.get("energy_max", 0) or 0) or max(energy, 1)
    xp = int(sheet.get("xp", 0) or 0)
    xp_need = int(sheet.get("xp_need", 0) or 0) or max(xp, 1)
    low = " low" if hp * 10 <= hp_max * 3 else ""
    meters = (
        f'<div class="rail later">'
        f'<span class="meter hp{low}" data-tip="{_e(_TIP_HP)}">'
        f"<span>HP {hp:,}/{hp_max}</span>"
        f'<span class="blocks" aria-hidden="true">'
        f"{_blocks(hp, hp_max)}</span></span>"
        f'<span class="meter en" data-tip="{_e(_TIP_EN)}">'
        f"<span>{_eglyph('bolt')} {energy:,}/{energy_max}</span>"
        f'<span class="blocks" aria-hidden="true">'
        f"{_blocks(energy, energy_max)}</span></span>"
        f'<span class="meter ae" data-tip="{_e(_TIP_XP)}">'
        f"<span>XP {xp:,}/{xp_need:,}</span>"
        f'<span class="blocks" aria-hidden="true">'
        f"{_blocks(xp, xp_need)}</span></span>"
        f"</div>")
    atk = int(sheet.get("atk", 0) or 0)
    dfs = int(sheet.get("dfs", 0) or 0)
    spd = int(sheet.get("spd", 0) or 0)
    pips = ""
    if atk or dfs or spd:
        spd_row = (_pip_row("bolt", "SPD", spd, AETHER, _TIP_SPD,
                            per_half=0.5) if spd else "")
        pips = ('<div class="piprows later">'
                + _pip_row("sword", "ATK", atk, ORANGE, _TIP_ATK)
                + _pip_row("armor", "DEF", dfs, TEXT, _TIP_DEF)
                + spd_row + "</div>")
    return (f'<div class="pavatar later">{ident}'
            f'<div class="profile">{gear}'
            f'<div class="pcol">{meters}{pips}</div></div></div>')


# ── 059: the faction block — where you stand with the factions ──────────
# Under the profile, full card width. A member: their banner on the
# left, the faction's name, the table's size and how many of them are on
# the floors right now, and a door into the Playing panel's faction tab.
# The unaffiliated: one clear ask — JOIN A FACTION — with the count of
# factions flying; it opens the ledger (every faction, ask to join from
# any row). Founding is the only level-gated door (level 4), and that
# is said in a faint second line. Neither button is a data-opt: both act
# in the pane, no server round trip.

_FACTION_FOUND_LEVEL = 4     # mirrors engine.social.FOUND_MIN_LEVEL

_TIP_FAC_ACT = ("Your faction's hall — the table, the rack, the roll of "
                "your people. Click the banner or the name to walk in.")
_TIP_FAC_JOIN = ("The ledger lists every faction that flies. Ask to join "
                 "any table whose door admits your level; a faction "
                 "pools coin, racks shared gear and enters the weekly "
                 "challenges.")


def _faction_block(m: Meters) -> str:
    """061/062: one full-width strip at the foot of the card, always
    there, cut off from the card above by the same dotted rule the
    other blocks use — no box. A member's banner + name are one door
    (they light on hover, a click walks into the faction's hall); the
    head-count stacks beside them. A loner's strip is the JOIN door."""
    name = getattr(m, "faction", "") or ""
    if name:
        slug = getattr(m, "faction_banner", "") or ""
        art = _sigil_half_data_url(slug) if slug else None
        sig = ""
        if art:
            # 010: white-on-transparent art as a CSS mask — the ink is
            # background-color, so hover can flip it without a filter.
            width = round(60 * art[1] / art[2])
            sig = (f'<span class="facsig" style="width:{width}px;'
                   f"-webkit-mask-image:url('{art[0]}');"
                   f"mask-image:url('{art[0]}');\"></span>")
        ink = _colors.faction_ink(getattr(m, "faction_color", "") or "")
        n = int(getattr(m, "faction_members", 0) or 0)
        on = int(getattr(m, "faction_online", 0) or 0)
        meta = ""
        if n:
            meta = (f'<span class="facsub"><span>{n} climber'
                    f"{'s' if n != 1 else ''}</span>"
                    f'<span>{on} online now</span></span>')
        return (f'<div class="facblk later" data-fac="{_e(name)}" '
                f'style="--fac:{ink}">'
                f'<button type="button" class="facdoor" data-opt="go:hall" '
                f'data-tip="{_e(_TIP_FAC_ACT)}">{sig}'
                f'<span class="facname">{_e(name)}</span></button>'
                + meta + '</div>')
    total = int(getattr(m, "factions_total", -1))
    if total == 0:
        count = "no faction flies yet — be the first"
    elif total > 0:
        count = f"{total} faction{'s' if total != 1 else ''}"
    else:
        count = ""
    lock = ""
    if int(getattr(m, "level", 1) or 1) < _FACTION_FOUND_LEVEL:
        lock = (f'<span class="facsub">found your own '
                f'{_eglyph("lock")} level {_FACTION_FOUND_LEVEL}</span>')
    return (f'<div class="facblk later none">'
            f'<button type="button" class="facdoor join" data-tab="community" '
            f'data-tip="{_e(_TIP_FAC_JOIN)}">'
            f'<span class="facname">JOIN A FACTION</span></button>'
            + (f'<span class="facsub">{_e(count)}</span>' if count else "")
            + lock + '</div>')


# ── 017/003: the enemy header + the [i] dossier ─────────────────────────
# The counter system is invisible noise unless the enemy's sheet is
# readable at a glance (the Kingdom Rush lesson). scene.enemy carries the
# payload; the header shows the always-on HP bar, the range chip and the
# active damage modifier; the [i] rides the headline NAME itself and
# opens the dossier panel as its tip (data-tiph, trusted server HTML) —
# all data inlined, no server round-trip, no model in the path.

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


def _dossier_tip(dossier_html: str) -> str:
    """009: the fold's words, flattened for the [i] tip — same facts,
    no second source of truth."""
    s = re.sub(r"<summary.*?</summary>", " ", dossier_html, flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def _estat_html(en: dict) -> str:
    """009: the monster's sheet is ONE line printed over the creature
    art, bottom-left, on a black ANSI slab — a bar where a bar reads
    (HP), plain numbers where numbers read (ATK/DEF/SPEED). The bar
    wears green while whole, gold while bleeding, red when a third
    remains."""
    hp, cap = int(en.get("hp", 0)), max(1, int(en.get("hp_max", 1)))
    col = OK if hp >= cap else (GOLD if hp * 3 > cap else RED)
    # each power wears its profile ink — HP green, ATK gold, SPD aether
    segs = [f'<span style="color:{OK}">HP</span> '
            f'<span style="color:{col}">{_blocks(hp, cap)} '
            f"{hp}/{cap}</span>"]
    segs.append(f'<span style="color:{GOLD}">ATK '
                f"{int(en.get('atk', 0))}</span>")
    segs.append(f"DEF {int(en.get('def', 0))}")
    if "mspd" in en:
        segs.append(f'<span style="color:{AETHER}">SPEED '
                    f"{int(en['mspd'])}</span>")
    return ('<div class="estat" aria-label="enemy stats">'
            + "   ".join(segs) + "</div>")


def _enemy_head_html(en: dict) -> str:
    """009: the headline owns the name; the plate keeps only the range
    word, then the live modifiers, dim. 041: no `later` class — the
    sheet must read the moment the scene lands, not after the
    typewriter finishes. 0.96.2 (roy): the [i] moved onto the headline
    name itself — the plate no longer carries it."""
    rng = en.get("range", "")
    rword = {"at_range": "◇ at range",
             "close": "◇ close quarters"}.get(rng, "")
    plate = (f'<div class="eplate"><span class="erng">{rword}</span></div>'
             if rword else "")
    mods = "".join(f'<div class="emod">◇ {_e(m)}</div>'
                   for m in _active_mods(en))
    return f'<div class="ehead">{plate}{mods}</div>'


def _dossier_html(en: dict) -> str:
    prof = en.get("profile") or {}
    rows = []

    def row(icon: str, head: str, text: str, tint: str = DIM) -> None:
        rows.append(f'<div class="drw">{_ticon(icon, tint)}'
                    f'<span>{_e(head)} {_e(text)}</span></div>')

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
        chase = ("It is faster than you. It will close the distance, "
                 "and you cannot count on getting away.")
    elif mspd < pspd:
        chase = ("You are faster than it, so you will usually stay "
                 "ahead — but it keeps trying to close, so it will "
                 "catch you now and then.")
    else:
        chase = ("You are about the same speed — neither of you gets "
                 "away clean.")
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
    # 0.96.2 (roy): the bare panel — no <details> fold, no "[i] dossier"
    # line under the scene. The headline's [i] ships this HTML as its
    # data-tiph tip; the panel's own look is unchanged.
    return (f'<div class="dossier">'
            f'<div class="dhead">{_e(en.get("name", ""))} — the shard\'s '
            f"dossier</div>{''.join(rows)}</div>")


# ── 079: the shop's verdict arrow — better or worse than what you own ───

_DELTA_SLOTS = ("weapon", "shield", "armor", "shoes")


def _gear_stat(g, cell: dict | None = None) -> int:
    """The one number a slot competes on: +speed for shoes, +ATK / +DEF
    for the rest. A worn cell carries its honed stat_val — the honed
    number is what a new piece actually has to beat."""
    if g.slot == "shoes":
        return int(g.speed)
    if cell is not None and cell.get("stat_val") is not None:
        return int(cell["stat_val"])
    return int(g.bonus)


def _owned_best(scene: Scene) -> dict[str, int]:
    """Best stat the player already owns per gear slot — the worn
    pieces on the slot map plus every spare riding in the pack."""
    best: dict[str, int] = {}
    worn = [sl for sl in (getattr(scene, "slots", None) or [])
            if sl.get("state") == "filled"]
    for cell in [*worn, *(getattr(scene, "inventory", None) or [])]:
        g = economy.FORGE.get(cell.get("slug") or "")
        if g is None or g.slot not in _DELTA_SLOTS:
            continue
        val = _gear_stat(g, cell)
        if val > best.get(g.slot, -1):
            best[g.slot] = val
    return best


def _opt_delta(oid: str, best: dict[str, int]) -> str:
    """'up' | 'down' | '' for a shop card — the card's gear against the
    best owned in its slot. A slot with nothing in it makes anything an
    upgrade; equal steel (a spare of the worn rung) draws no arrow.
    Cards without a slot to compete on (relics, salves, packs) stay
    bare."""
    if not oid.startswith(("buy_", "wear_")):
        return ""
    g = economy.FORGE.get(oid.split("_", 1)[1])
    if g is None or g.slot not in _DELTA_SLOTS:
        return ""
    have = best.get(g.slot)
    if have is None:
        return "up"
    val = _gear_stat(g)
    return "up" if val > have else ("down" if val < have else "")


def _delta_arrow(delta: str) -> str:
    """The 16×16 house-style arrow, tinted by verdict — rides the top
    right of the card cell, over the [i]."""
    if not delta:
        return ""
    url = icons.icon_data_url(f"arrow_{delta}")
    tint = OK if delta == "up" else RED
    word = "an upgrade" if delta == "up" else "weaker than yours"
    return (f'<span class="delta" role="img" aria-label="{word}" '
            f'style="background-color:{tint};'
            f"-webkit-mask-image:url('{url}');"
            f"mask-image:url('{url}')\"></span>")


def _opt_gear_icon(oid: str, art_slug: str = "") -> str:
    """004: shop rows carry their 1-bit gear icon (32×32 display of the
    16×16 grids) — buy_/wear_ options only, everything else stays text.
    032: the faction chest's cards (take_arm_/put_ ids) name their gear
    through scene.option_art instead — a gear slug there resolves the
    same icon, so the card wall works for any option the engine dresses."""
    if not (oid.startswith("buy_") or oid.startswith("wear_")):
        if art_slug and (art_slug in economy.FORGE
                         or art_slug in economy.RELICS
                         or art_slug in economy.APOTHECARY
                         or art_slug in economy.PACKS
                         or art_slug == "arrow_pack"):
            slug = art_slug
        else:
            return ""
    elif oid == "buy_pack" and art_slug in economy.PACKS:
        # 064: the Forge's pack row names the NEXT tier's face
        slug = art_slug
    else:
        slug = oid.split("_", 1)[1]
    # 057/058: an item wears its OWN face when the art ships — the
    # shared line glyph survives only as the fallback. keen/warded
    # keep their style ink over the base item's mask.
    wart = _gear_art_slug(slug)
    wurl = _gear_art_url(wart, "icons") if wart else None
    if wurl:
        tint = _STYLE_TINT.get(economy.style_of(slug))
        tint_css = f"background-color:{tint};" if tint else ""
        return (f'<span class="gicon gw" aria-hidden="true" '
                f'style="{tint_css}'
                f"-webkit-mask-image:url('{wurl}');"
                f"mask-image:url('{wurl}')\"></span>")
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


def _gear_card_preview(oid: str, hint: str, art_slug: str = "") -> str:
    """057b: the item preview — not a tooltip. The card's own face
    grows: a sibling card 20% larger in every direction, the 100x160
    portrait at full card scale, the name, the stat line, and a buy
    button carrying the price at the foot. Desktop shows it on :hover;
    touch opens it on tap (instead of buying) and ✕ closes it — the
    wiring lives in TIP_JS, the show/hide rules in SCENE_CSS.
    058: any FORGE item or relic with shipped art previews; "" else."""
    if not oid.startswith(("buy_", "wear_")):
        return ""
    slug = oid.split("_", 1)[1]
    if oid == "buy_pack" and art_slug in economy.PACKS:
        slug = art_slug           # 064: the next pack tier's face
    g = economy.FORGE.get(slug)
    relic = economy.RELICS.get(slug) if g is None else None
    # 062: the Medlab shelf previews too; 064: the packs
    ware = (economy.APOTHECARY.get(slug) or economy.PACKS.get(slug)
            if g is None and relic is None else None)
    wart = _gear_art_slug(slug)
    lurl = _gear_art_url(wart, "large") if wart else None
    if (g is None and relic is None and ware is None) or not lurl:
        return ""
    name = (g.name if g is not None
            else relic.name if relic is not None else ware.name)
    tint = _STYLE_TINT.get(economy.style_of(slug)) or ART
    parts = [t for t in (hint or "").split(" · ") if t]
    pay = next((t for t in parts if t.startswith(("pay ", "◈ "))), "")
    if oid.startswith("buy_"):
        act = _ep("buy " + pay.removeprefix("pay ")) if pay else "buy it"
    else:
        act = "wear it"
    stats = _ep(" · ".join(t for t in parts if t != pay))
    stat_html = f'<span class="wpstat">{stats}</span>' if stats else ""
    return (
        '<div class="wprev">'
        '<button type="button" class="wpx" aria-label="close">✕</button>'
        f'<span class="wpart" aria-hidden="true" '
        f'style="background-color:{tint};'
        f"-webkit-mask-image:url('{lurl}');mask-image:url('{lurl}')\">"
        "</span>"
        f'<span class="wpname">{_e(name)}</span>{stat_html}'
        f'<button type="button" class="opt wpbuy" '
        f'data-opt="{_e(oid)}">{act}</button></div>')


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
        VIOLET if slug.startswith("warden_") else ART)
    return (f'<span class="farts"><span class="fart" aria-hidden="true" '
            f'style="background-color:{tint};'
            f"-webkit-mask-image:url('{url}');"
            f"mask-image:url('{url}');\"></span></span>")


def _slot_cell(it: dict, *, readonly: bool = False) -> str:
    """One pack slot — a square button holding the icon, the ×count and
    the wear bar; the name lives in the tip and the action popup.
    readonly: a span, no acts — used by the other-climber avatar."""
    slug = it.get("slug", "")
    equipped = bool(it.get("equipped"))
    url = icons.icon_data_url(icons.icon_key(slug, it.get("kind", "")))
    # 057/058: items wear their own face in the pack too — the 30x48
    # art centered in the square cell (mask-size contain via .gw);
    # anything without shipped art keeps the 16×16 grid glyphs.
    picon_cls = ""
    wart = _gear_art_slug(slug)
    wurl = _gear_art_url(wart, "icons") if wart else None
    if wurl:
        url, picon_cls = wurl, " gw"
    # 025 §4: the same glyph in the style's ink — ember for keen steel,
    # frost for warded. Unstyled gear keeps the worn/packed contrast.
    tint = _STYLE_TINT.get(economy.style_of(slug)) or (
        ART if equipped else DIM)
    count = int(it.get("count", 1))
    ct = (f'<span class="ct">{count}</span>'
          if count > 1 and not equipped else "")
    tip = tips.item_tip(slug, equipped=equipped, bonus=it.get("stat_val"))
    name = str(it.get("name", slug))
    tip = f"{name} — {tip}" if tip else name
    if it.get("charm_dur"):
        # 069: a worn luck charm names its remaining pool
        tip += f" · {int(it['charm_dur'])} victories of fortune left"
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
    # every item leads its tip with the numbers that matter, in ink the
    # eye can split (color, never bold — the VGA face has none): ATK/DEF
    # gold (the HONED number — core put it on the cell), DURABILITY
    # green, red once it's broken, AMOUNT violet on stacks. The HTML
    # rides data-tiph; data-tip stays the plain-text fallback.
    tiph_attr = ""
    params: list[str] = []
    sval = it.get("stat_val")
    if sval is not None:
        params.append(f'<span style="color:{GOLD}">'
                      f'{it.get("stat_name", "ATK")} {sval}</span>')
        left_n, total_n = it.get("dur_left"), it.get("dur_max")
        dtxt = (f"{left_n:,}/{total_n:,}"
                if left_n is not None and total_n else "∞")
        dcol = RED if (dur is not None and dur <= 0) else OK
        params.append(f'<span style="color:{dcol}">'
                      f'DURABILITY {dtxt}</span>')
    if count > 1:
        params.append(f'<span style="color:{VIOLET}">AMOUNT {count}</span>')
    # 058b: the hover tip carries the item's 100x160 portrait on its
    # left — every pack item with shipped art, sword to relic. The art
    # rides the tiph HTML with inline styles so both hosts (pane and
    # chat card) show it without new tipbox CSS.
    lurl = _gear_art_url(wart, "large") if wart else None
    if params or lurl:
        text = " · ".join(params) + (f"<br>{_e(tip)}" if params
                                     else _e(tip))
        if lurl:
            atint = _STYLE_TINT.get(economy.style_of(slug)) or ART
            tiph = (
                '<span style="display:flex;gap:10px;'
                'align-items:center;">'
                f'<span style="flex:none;width:105px;height:168px;'
                f'background-color:{atint};'
                f"-webkit-mask-image:url('{lurl}');"
                f"mask-image:url('{lurl}');"
                f'-webkit-mask-size:contain;mask-size:contain;'
                f'-webkit-mask-repeat:no-repeat;mask-repeat:no-repeat;'
                f'-webkit-mask-position:center;mask-position:center;'
                f'image-rendering:pixelated;"></span>'
                f'<span style="min-width:0">{text}</span></span>')
        else:
            tiph = text
        tiph_attr = f' data-tiph="{_e(tiph)}"'
    # 027: the cell is a button — the popup lists what this thing can
    # do HERE, or says where it can be done. `acts` come from the
    # engine (core.pack_actions), never guessed client-side.
    acts = [] if readonly else (it.get("acts") or [])
    act_attr = (f" data-acts=\"{_e(_json.dumps(acts))}\""
                if acts else "")
    why_attr = ("" if readonly else
                (f' data-why="{_e(str(it.get("why")))}"'
                 if it.get("why") else ""))
    if readonly:
        return (
            f'<span class="slot item'
            f'{" eq" if equipped else ""}" '
            f'data-tip="{_e(tip)}"{tiph_attr} data-slug="{_e(slug)}" '
            f'data-name="{_e(name)}">'
            f'<span class="picon{picon_cls}" style="background-color:{tint};'
            f"-webkit-mask-image:url('{url}');mask-image:url('{url}');\">"
            f"</span>{ct}{durbar}</span>")
    return (
        f'<button type="button" class="slot item act'
        f'{" eq" if equipped else ""}" '
        f'data-tip="{_e(tip)}"{tiph_attr} data-slug="{_e(slug)}" '
        f'data-name="{_e(name)}"'
        f"{act_attr}{why_attr}>"
        f'<span class="picon{picon_cls}" style="background-color:{tint};'
        f"-webkit-mask-image:url('{url}');mask-image:url('{url}');\">"
        f"</span>{ct}{durbar}</button>")


# 012: the grid draws the pack's CAPACITY — one square per slot the
# player owns (scene.pack_slots; 0 = an old scene half, draw the items
# and this many blanks at least). Rows flow to the card's edge.
_PACK_MIN_SLOTS = 6


def _inventory_html(scene: Scene) -> str:
    """031 §3: the pack is a slot grid — squares that fill with what you
    carry, blanks where nothing does. 069: the PACK ONLY — worn and held
    gear live in the gear map above; a pack stack does nothing until it
    is set in a slot (the cell popup's wear_* / Set in pouch)."""
    if not scene.inventory and not getattr(scene, "slots", None):
        return ""
    packed = [it for it in scene.inventory
              if not it.get("equipped") and not it.get("held")]
    n = len(packed)
    cap = int(getattr(scene, "pack_slots", 0) or 0)
    total = max(cap or _PACK_MIN_SLOTS, n)
    cells = []
    for i, it in enumerate(packed):
        cell = _slot_cell(it)
        if cap and i >= cap:
            # over capacity — the thing is yours (loot never drops for
            # a bookkeeping rule) but shops won't open a new stack until
            # the pack is back under; the red dashed border says so.
            cell = cell.replace('class="slot item act',
                                'class="slot item act over', 1)
        cells.append(cell)
    cells += ['<span class="slot empty"></span>'] * (total - len(cells))
    lbl = "pack"
    if cap:
        lbl = f"pack {n}/{cap}" + (" · over" if n > cap else "")
    return (f'<div class="inv later"><span class="invlbl">{lbl}</span>'
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
    /* data-tiph is trusted server-authored HTML (the colored ATK /
       DURABILITY line); plain tips stay textContent */
    var h = el.getAttribute('data-tiph');
    if (h) box.innerHTML = h;
    else box.textContent = el.getAttribute('data-tip') || '';
    if (!box.textContent) return hide();
    box.style.display = 'block';
    var r = el.getBoundingClientRect();
    /* the dossier tip is a whole panel — give it panel room */
    var wide = box.querySelector('.dossier');
    box.style.maxWidth = Math.min(wide ? 560 : 380, innerWidth - 16) + 'px';
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
  /* 057b: the weapon preview. Desktop (hover) shows it in CSS and the
     buy button is simply on top of the card. On touch the card's tap
     must open the preview INSTEAD of buying — this capture listener
     fires before the host's buy wiring and stops it. ✕ or a tap
     anywhere outside closes; the preview's own buy button acts. */
  function unpre() {
    var o = document.querySelectorAll('.gcell.wopen');
    for (var i = 0; i < o.length; i++) o[i].classList.remove('wopen');
  }
  document.addEventListener('click', function (e) {
    if (!e.target.closest) return;
    var x = e.target.closest('.wpx');
    if (x) { e.preventDefault(); e.stopPropagation(); unpre(); return; }
    if (matchMedia('(hover: hover)').matches) return;
    var c = e.target.closest('.gcard[data-wprev]');
    if (c) {
      e.preventDefault(); e.stopPropagation();
      var cell = c.closest('.gcell');
      unpre();
      if (cell) cell.classList.add('wopen');
      return;
    }
    if (!e.target.closest('.wprev')) unpre();
  }, true);
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
    root.querySelectorAll('.inv .item, .gearmap .item').forEach(function (it) {
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
      /* 069: the figure stands between the slot columns — it takes the
         taller column's height (4 slots + gaps), never the meters' */
      var h = 0;
      pr.querySelectorAll('.slotcol').forEach(function (c) {
        h = Math.max(h, c.offsetHeight); });
      if (phone) {
        img.style.height = (h || 210) + 'px';
        img.style.width = 'auto';
        return;
      }
      img.style.height = Math.max(200, h || col.offsetHeight) + 'px';
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
for(let c=3;c<t.length+3;c+=3){n.nodeValue=t.slice(0,Math.min(c,t.length));await sleep(fast?2:7)}}
cur.remove()}
(async()=>{for(const el of typed)await typeEl(el);
let d=0;for(const el of later){setTimeout(()=>el.classList.add('shown'),d);d+=fast?8:30}})();
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
    'button.opt, button.nrow, button.wrow, button.gtile, button.ptile, '
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


# ── 067: the arena card — HUD, tiles, log ─────────────────────────────
_ARENA_TYPE = {   # the foe's kind badge: glyph key, ink, word
    "fly": ("t_wing", AETHER, "FLYING"),
    "armoured": ("t_armor", ORANGE, "ARMOURED"),
    "magic_resist": ("t_resist", VIOLET, "MAGIC RES"),
    "plain": ("", TEXT, "REGULAR"),
}


def _aicon(key: str, ink: str = "", cls: str = "", tip: str = "") -> str:
    if not key:
        return ""
    url = icons.icon_data_url(key)
    st = f"background-color:{ink};" if ink else ""
    tp = f' data-tip="{_e(tip)}" tabindex="0" role="note"' if tip else ""
    return (f'<span class="aico{(" " + cls) if cls else ""}"{tp} style="{st}'
            f"-webkit-mask-image:url('{url}');mask-image:url('{url}')\">"
            "</span>")


# 067 phase 6: the foe's kind, spelt out for the [i]-less reader
_TIP_KIND = {
    "fly": "Flying — a sword cannot reach it; use a bow or magic. "
           "You also cannot back away from it, because it follows "
           "you through the air.",
    "armoured": "Armoured — heavy plate. A blade cuts at half "
                "strength, arrows all but bounce off, magic goes "
                "through in full.",
    "magic_resist": "Magic resistance — spells barely scratch it. "
                    "A blade cuts in full, arrows at half strength.",
    "bulwark": "Bulwark — holds its ground; you cannot push it back.",
}
_PATH_GLYPH = {"blade": "sword", "bow": "bow", "staff": "staff"}


def _abar(hp: int, cap: int, cls: str) -> str:
    """067 phase 5: the HP bar is the regular fight's bar — ▓░ blocks in
    the VGA face (`_blocks`), the number after it, ink by the third
    left. `.abar.me/.foe[data-hp][data-max]` is arena3d.js's hook: it
    rewrites the blocks and the number as the beats land."""
    cap = max(1, int(cap))
    hp = max(0, min(int(hp), cap))
    col = OK if hp >= cap else (GOLD if hp * 3 > cap else RED)
    return (f'<span class="abar {cls}" data-hp="{hp}" data-max="{cap}" '
            f'style="color:{col}"><span class="blocks">{_blocks(hp, cap, 20)}'
            f'</span> <span class="anum">{hp}/{cap}</span></span>')


def _astat_html(side: dict, cls: str, speed_key: str, name: str = "",
                name_extra: str = "", def_extra: str = "",
                tail: str = "") -> str:
    """One black ANSI slab, the `_estat_html` grammar: `NAME` (067
    phase 6 — bright, with the kind icons after it), `HP ▓▓▓░ n/m`,
    `ATK n DEF n SPEED n` (the armour icon rides after DEF), then any
    tail line (the climber's gear glyphs)."""
    segs = [f'<span style="color:{GOLD}">ATK {int(side.get("atk", 0))}</span>',
            f"DEF {int(side.get('def', 0))}{def_extra}"]
    if speed_key in side:
        segs.append(f'<span style="color:{AETHER}">SPEED '
                    f"{int(side[speed_key])}</span>")
    # 069 phase 5: the pouch under the climber's HP — the charm or potion
    # that acts in this fight (nothing in the pack does)
    charm = side.get("charm") or {}
    pouch = ""
    if charm.get("slug"):
        url = icons.icon_data_url(icons.icon_key(str(charm["slug"]), "item"))
        n = charm.get("dur")
        pouch = (f'<div class="apouch"><span class="picon" style="'
                 f'background-color:{GOLD};-webkit-mask-image:url(\'{url}\');'
                 f'mask-image:url(\'{url}\');"></span> '
                 f'{_e(str(charm.get("name", "")))}'
                 + (f' <span style="color:{GOLD}">×{int(n)}</span>'
                    if n is not None else "") + '</div>')
    nm = (f'<div class="aname">{_e(str(name or side.get("name") or "").upper())}'
          f'{name_extra}</div>')
    return (f'<div class="astat {cls}">{nm}<div><span style="color:{OK}">HP</span> '
            f'{_abar(side.get("hp", 0), side.get("hp_max", 1), cls)}</div>'
            f'<div>{" ".join(segs)}</div>{pouch}{tail}</div>')


def _arena_hud_html(a: dict, info: str = "") -> str:
    """067 phase 6 (roy): one row along the top of the stage — the
    climber's slab left, the foe's right, both named, both top-aligned
    a half line down. The climber's slab ends in a gear line (every
    weapon in hand — the lead outlined gold, a broken one red — armour,
    shield); the foe's name carries its kind icons (flying aether,
    magic resistance violet with its level, bulwark gold) and the
    armour icon rides on the DEF when the foe is armoured."""
    me, foe = a.get("me") or {}, a.get("foe") or {}
    gear = []
    for w in me.get("weapons") or []:
        key = _PATH_GLYPH.get(str(w.get("path", "blade")), "sword")
        cls = ("lead" if w.get("lead") else "") + (" broken" if w.get("broken") else "")
        ink = RED if w.get("broken") else (GOLD if w.get("lead") else TEXT)
        tip = str(w.get("name", "")) + (" — in hand" if w.get("lead") else "") \
            + (" — BROKEN" if w.get("broken") else "")
        gear.append(_aicon(key, ink, cls.strip(), tip))
    guard = me.get("guard") or {}
    for slot, key in (("armor", "armor"), ("shield", "shield")):
        g = guard.get(slot)
        if g:
            broken = bool(g.get("broken"))
            tip = str(g.get("name", "")) + (f' +{int(g.get("bonus", 0))}'
                                            if g.get("bonus") else "") \
                + (" — BROKEN" if broken else "")
            gear.append(_aicon(key, RED if broken else TEXT,
                               "broken" if broken else "", tip))
    tail = f'<div class="agear">{"".join(gear)}</div>' if gear else ""
    kinds = ""
    if foe.get("flying"):
        kinds += _aicon("t_wing", AETHER, "", _TIP_KIND["fly"])
    if foe.get("resist_pct"):
        kinds += (_aicon("t_resist", VIOLET, "", _TIP_KIND["magic_resist"])
                  + f'<span class="akw" style="color:{VIOLET}">MR '
                  f'{int(foe["resist_pct"])}%</span>')
    if foe.get("bulwark"):
        kinds += _aicon("t_bulwark", GOLD, "", _TIP_KIND["bulwark"])
    dext = (_aicon("t_armor", ORANGE, "", _TIP_KIND["armoured"])
            if foe.get("armoured") else "")
    # 0.97.1 (roy): the [i] rides the foe's nameplate — the one name the
    # scene already shows — and opens the dossier tip right there.
    return ('<div class="ahuds">'
            + _astat_html(me, "me", "spd", tail=tail)
            + _astat_html(foe, "foe", "spd", name_extra=kinds + info,
                          def_extra=dext)
            + "</div>")


def _arena_banner_html(scene, info: str = "") -> str:
    a = scene.arena or {}
    w = int(a.get("w", 320))
    # 067 phase 8 (roy): the stage the card shows is a 320×160 band —
    # half the 3D frame's height. The layer keeps rendering its 320×300
    # frame; CSS windows the actor band (same px per row, nothing
    # squashes) and the floats layer wears the same window. Tiles no
    # longer ride inside the scene — they sit UNDER it (the fragment).
    # Victory: the win amounts land OVER the scene, centered — the lean
    # tally (big lines only, no slab, no mark heaps) so the scene shows.
    tally = ""
    if a.get("phase") == "victory" and getattr(scene, "tally", None):
        inner = _tally_html(scene.tally, lean=True)
        if inner:
            tally = f'<div class="awin later">{inner}</div>'
    return (f'<div class="banner arena" style="background-color:#000;'
            f'aspect-ratio:{w}/160;" data-a3d-slot="1">'
            f'{_arena_hud_html(a, info)}<div class="afloats"></div>'
            f"{tally}</div>")


def _arena_log_html(a: dict) -> str:
    lines = [ln for ln in (a.get("log") or []) if ln]
    if not lines:
        return ""
    return ('<div class="alog">'
            + "".join(f'<div class="aline">{_ep(ln)}</div>'
                      for ln in lines)
            + "</div>")


def _arena_tile_fallback(o, phase: str = "") -> dict:
    from .engine import arena as _arena_mod
    t = _arena_mod.tile(o.id, {})
    if not _arena_mod._TILE_LABEL.get(o.id):
        t["label"] = o.label[:12].upper()
    return t


def _arena_tiles_html(scene, later: bool = True) -> str:
    """The option tiles: an icon on a black box, `[n] LABEL` under it,
    the [i] pinned to the corner. Numbering runs on scene.options order
    so the pane's 1..9 keys pick the same button."""
    a = scene.arena or {}
    tiles = a.get("tiles") or {}
    cells = []
    for i, o in enumerate(scene.options, 1):
        # 067 phase 6: the end card's menu (built after the payload) has
        # no tiles on the wire — the tables in arena.tile() dress it
        t = tiles.get(o.id) or _arena_tile_fallback(o, str(a.get("phase", "")))
        key_cls = " aether" if o.aether else ""
        locked = bool(getattr(o, "locked", False))
        cls = "opt atile" + (" locked" if locked else "")
        tip = tips.option_tip(o.id) or o.hint or ""
        info = (f'<span class="info" tabindex="0" role="note" '
                f'data-tip="{_e(tip)}">i</span>' if tip else "")
        # 067 phase 5: the item's own 30×48 face (the pack's icons),
        # drawn as a pixelated <img> so it scales crisp with the scene;
        # the 16×16 glyph only where no art ships.
        # 067 phase 8 v2 (roy): the tile is a ROW — a big 76px black box
        # (56px `.picon` mask, art `.gw` when it ships, the glyph
        # otherwise, ART ink, no border) with a text column on its
        # RIGHT: `[n]` one line, the label the next, the ATK a gold
        # line, the [i] the last — every line the card's own 16px.
        wart = _gear_art_slug(t.get("art") or "")
        wurl = _gear_art_url(wart, "icons") if wart else None
        murl, pcls = ((wurl, " gw") if wurl
                      else (icons.icon_data_url(t.get("icon") or "focus"), ""))
        ink = DIM if locked else ART
        icon = (f'<span class="abox"><span class="picon{pcls}" '
                f'style="background-color:{ink};'
                f"-webkit-mask-image:url('{murl}');mask-image:url('{murl}')\">"
                '</span></span>')
        hint = (f'<span class="ahint">{_ep(o.hint)}</span>' if o.hint else "")
        # 069 phase 5: an attack tile carries the ATK its own weapon
        # swings with — three blades, three numbers
        atk = (f'<span class="aatk">ATK {int(t["atk"])}</span>'
               if t.get("atk") is not None else "")
        btn = (f'<button type="button" class="{cls}" data-opt="{_e(o.id)}" '
               f'title="{_e(o.label)}">{icon}'
               f'<span class="atxt"><span class="key{key_cls}">{i}</span>'
               f'<span class="lbl">{_e(t.get("label") or o.label)}</span>'
               f'{atk}{hint}</span></button>')
        cells.append(f'<div class="atcell">{btn}{info}</div>')
    return (f'<div class="options{" later" if later else ""} arena-opts">'
            f'{"".join(cells)}</div>')


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
        # 068: inside its own hall the sigil flies the faction's ink
        if getattr(scene, "banner_ink", "") and scene.banner in sigil_slugs():
            tint = scene.banner_ink
    k3 = getattr(scene, "kill3d", None)
    # 067: the arena owns the slot after the opener — a bare 320×300
    # band with the HUD in it; the website's arena3d layer paints the 3D
    # into it. The opener keeps the creature's close-up (roy: first the
    # image, the 3D after the first strike).
    ar = getattr(scene, "arena", None)
    arena_live = bool(ar) and ar.get("phase") not in ("opener",)
    # 067 phase 8 (roy): the icon tiles exist ONLY in the fight itself.
    # Opener and end cards (victory/death/fled) use the regular menu.
    arena_round = bool(ar) and ar.get("phase") == "round"
    # 0.96.2/0.97.1 (roy): the [i] sits right after the creature's name
    # and its tip IS the dossier panel (data-tiph, trusted server HTML).
    # The name lives in exactly ONE place per card: the headline on
    # regular cards, the foe's HUD nameplate in the live arena.
    hl_info = ""
    if scene.enemy:
        dossier = _dossier_html(scene.enemy)
        hl_info = (f'<span class="info" tabindex="0" role="note" '
                   f'aria-label="enemy dossier" '
                   f'data-tip="{_e(_dossier_tip(dossier))}" '
                   f'data-tiph="{_e(dossier)}">i</span>')
    if arena_live:
        parts.append(_arena_banner_html(scene, info=hl_info))
        if arena_round and scene.options:
            # the toolbar: one row of tiles DIRECTLY under the stage
            parts.append(_arena_tiles_html(scene, later=False))
        parts.append(_arena_log_html(ar))
    elif fx or split or banner:
        banner_html = (
            f'<div class="banner" style="background-color:{tint};'
            f"aspect-ratio:{w}/{h};"
            f"-webkit-mask-image:url('{url}');"
            f"mask-image:url('{url}');\"{swap_attr}></div>")
        if scene.enemy:
            banner_html = (f'<div class="bwrap">{banner_html}'
                           f"{_estat_html(scene.enemy)}</div>")
        parts.append(banner_html)
    elif k3 and k3.get("id"):
        # PLAN4: a floor-1 kill card ships its banner BARE — no ending
        # GIF anywhere on it. The website's fight3d layer mounts the 3D
        # scene in this slot; a surface without the layer (or a dead
        # WebGL) shows the black band, and the client repaints the reel
        # itself from the fx slug in data-kill3d.
        parts.append('<div class="banner" style="background-color:#000;'
                     'aspect-ratio:320/112;"></div>')

    # 027: the notice board owns the top of the card — above the location,
    # above the headline. It is not a menu row and must never look like one.
    if getattr(scene, "notices", None):
        parts.append(_notices_html(scene.notices))
    # 030 Phase 5: the day's paper — above the location, below the board.
    if getattr(scene, "paper", None):
        parts.append(_paper_html(scene.paper))

    parts.append(f'<div class="eyebrow type">{_e(scene.eyebrow)}</div>')
    hl_col = _HEADLINE.get(scene.event_kind, BRIGHT)
    # 030: an amount wears its colour even in a headline (law 1)
    # 0.97.1 (roy): in the live arena the foe's nameplate already says
    # the name (with the [i]) — the headline under the scene would say
    # it a second time, so that line is dropped entirely.
    if not (arena_live and scene.enemy):
        parts.append(f'<div class="headline type" style="color:{hl_col}">'
                     f"{_ep(scene.headline)}{hl_info}</div>")
    if scene.enemy and not arena_live:
        parts.append(_enemy_head_html(scene.enemy))
    if scene.support:
        parts.append(f'<div class="support type">{_ep(scene.support)}</div>')
    # 072: another climber's public sheet — on top, before the words.
    av = getattr(scene, "avatar", None)
    if av:
        parts.append(player_avatar_html(av))
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
    in_callout = False
    has_tally = bool(getattr(scene, "tally", None))
    arena_note = (ar or {}).get("note") if arena_live else ""
    for line in scene.body_lines:
        if has_tally and _TALLY_SAID.match(line):
            continue
        if arena_note and line == arena_note:
            continue
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
        # 059: ▛ callout markers — a white-bordered box with a title,
        # for the announcements a player must actually read (level-up).
        if line.startswith("▛ "):
            if in_callout:
                parts.append("</div>")
            parts.append(f'<div class="callout"><div class="callouth type">'
                         f"{_ep(line[2:])}</div>")
            in_callout = True
            continue
        if line == "▛.":
            if in_callout:
                parts.append("</div>")
                in_callout = False
            continue
        # 062: ▜ solid-box markers — a filled box with a title band,
        # for the hall's weekly goal (no border, background colour).
        if line.startswith("▜ "):
            if in_callout:
                parts.append("</div>")
            parts.append(f'<div class="callout solid"><div class="callouth '
                         f'type">{_ep(line[2:])}</div>')
            in_callout = True
            continue
        if line == "▜.":
            if in_callout:
                parts.append("</div>")
                in_callout = False
            continue
        if line.startswith("−") or line.startswith("-"):
            # losses stay red; gains are NOT green — gold paints gold,
            # XP paints XP, everything else keeps the card's ink.
            parts.append(f'<div class="body type" style="color:{RED}">'
                         f"{_ep(line)}</div>")
        else:
            parts.append(f'<div class="body type">{_combat_html(line)}</div>')
    if in_callout:
        parts.append("</div>")
    if in_fold:
        parts.append("</details>")
    # 067 phase 8: on the arena's victory card the tally rides OVER the
    # scene (`.awin` in the banner) — never said twice on one card.
    if getattr(scene, "tally", None) \
            and not (arena_live and (ar or {}).get("phase") == "victory"):
        parts.append(_tally_html(scene.tally))
    if getattr(scene, "gallery", None):
        parts.append(_gallery_html(scene.gallery))
    if getattr(scene, "ask", None):
        parts.append(_ask_html(scene.ask))

    if scene.options and arena_round:
        pass    # 067 phase 8: the round's tiles already sit under the stage
    elif scene.options:
        # 031 §14: grid mode — a scene may ask for a card wall instead of
        # rows. Options that resolve a gear icon become picture cards;
        # the rest (hone, repair, back…) stay rows underneath. Numbering
        # runs across both in scene.options order, so the typed-number
        # fallback never notices the layout.
        grid_mode = bool(getattr(scene, "grid", False))
        # 052: an option the gallery already shows as a picture tile
        # never repeats as a row — the card IS the button. Numbering
        # stays on scene.options order so typed numbers keep working.
        gal_opts = {str(g.get("opt", "")) for g in
                    (getattr(scene, "gallery", None) or [])}
        # 079: what the shop cards have to beat — computed once per scene
        owned_best = _owned_best(scene) if grid_mode else {}
        rows, cards = [], []
        for i, o in enumerate(scene.options, 1):
            if o.id in gal_opts:
                continue
            sect = getattr(o, "section", "") or ""
            if sect:
                rows.append(f'<div class="osect">{_e(sect)}</div>')
            key_cls = " aether" if o.aether else ""
            # 019: a locked row is dimmed but stays a button — clicking
            # it is how the player asks why the gate is shut.
            opt_cls = " locked" if getattr(o, "locked", False) else ""
            # 068: a row that ends something is red — never navigation
            if getattr(o, "danger", False):
                opt_cls += " danger"
            hint = (f'<span class="hint">{_ep(o.hint)}</span>'
                    if o.hint else "")
            # 068: a colour pick wears its ink as two block glyphs before the name
            swatch = ""
            if o.id.startswith(("hcol_", "col_")):
                cslug = o.id.split("_", 1)[1]
                if cslug in _colors.FACTION_COLORS:
                    swatch = (f'<span class="swatch" style="color:'
                              f'{_colors.faction_ink(cslug)}">██</span>')
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
            if bn:
                btip = notices.badge_tip(o.id)
                badge = (f'<span class="badge" tabindex="0" role="note" '
                         f'data-tip="{_e(btip)}">{bn}</span>')
            else:
                badge = ""
            # 014: the whisper glyph — [i] OUTSIDE the button, so tapping
            # it never fires the option; tip resolves by option id.
            # 031 §14: the card wall keeps it too, pinned to the corner.
            tip = tips.option_tip(o.id)
            info = (f'<span class="info" tabindex="0" role="note" '
                    f'data-tip="{_e(tip)}">i</span>' if tip else "")
            # the mend rows keep their place at the foot of the wall —
            # the icon rides the row, left of the label, never a card
            if grid_mode and gicon \
                    and not o.id.startswith(("repair_", "token_")):
                # the card stacks its facts — cost, stat, durability
                # each on its own line (the button is a column flex,
                # so every span is a line of its own)
                # 062: a long note (the Medlab's "better loot …")
                # wraps inside the card instead of spilling past it
                stack = ("".join(
                    f'<span class="hint{" wrap" if len(part) > 14 else ""}">'
                    f'{_ep(part)}</span>'
                    for part in o.hint.split(" · ") if part)
                    if o.hint else "")
                # 057b: an item card grows a preview — a 20% bigger
                # sibling card with the portrait at full scale and the
                # buy button at the foot. Hover shows it on desktop;
                # on touch the tap opens it INSTEAD of buying (the
                # data-wprev flag tells TIP_JS to intercept). Locked
                # cards keep their plain "why is the gate shut" click.
                prev = ("" if getattr(o, "locked", False)
                        else _gear_card_preview(
                            o.id, o.hint or "",
                            (getattr(scene, "option_art", None) or {})
                            .get(o.id) or ""))
                wflag = ' data-wprev="1"' if prev else ""
                card = (f'<button type="button" class="opt gcard{opt_cls}" '
                        f'data-opt="{_e(o.id)}"{wflag}>'
                        f'<span class="key{key_cls}">{i}</span>{gicon}'
                        f'<span class="lbl">{_ep(o.label)}</span>{badge}'
                        f"{stack}</button>")
                # 079: the verdict arrow rides the cell's top right; the
                # CSS drops the [i] to sit just under it.
                darr = _delta_arrow(_opt_delta(o.id, owned_best))
                cards.append(
                    f'<div class="gcell">{card}{darr}{info}{prev}</div>')
                continue
            btn = (f'<button type="button" class="opt{opt_cls}" '
                   f'data-opt="{_e(o.id)}">'
                   f'<span class="key{key_cls}">{i}</span>{tile}{gicon}'
                   f'{swatch}<span class="lbl">{_ep(o.label)}</span>{badge}'
                   f"{hint}</button>")
            nest = " nest" if getattr(o, "nest", False) else ""
            rows.append(f'<div class="orow{nest}">{btn}{info}</div>')
        wall = (f'<div class="ggrid">{"".join(cards)}</div>'
                if cards else "")
        parts.append(f'<div class="options later">{wall}{"".join(rows)}'
                     "</div>")

    # 031 §11: the activity band — what tonight is already set to do,
    # a filled box with no outline at the foot of the options.
    if getattr(scene, "activity", ""):
        parts.append(f'<div class="actband later">{_ep(scene.activity)}'
                     "</div>")

    # 042: the presence grid rides under the options — who else stands
    # in this room, seven faces to a row, every face a door.
    if getattr(scene, "players_here", None):
        parts.append(_players_here_html(scene))

    if arena_round:
        pass    # 067 phase 5/8: no profile under the fight ITSELF (roy);
        # the end cards are regular cards again and keep theirs
    elif scene.meters:
        parts.append(_profile_html(scene))   # pack rides its right column
        parts.append(_faction_block(scene.meters))   # 059
    else:
        parts.append(_inventory_html(scene))

    # 042: the sound layer's stamps — the hit flavored by damage type,
    # the room keyed for music, the fight marked wilds or warden.
    dtype = str((getattr(scene, "enemy", None) or {}).get("dtype", ""))
    dt = f' data-dtype="{_e(dtype)}"' if dtype else ""
    loc = str(getattr(scene, "location", "") or "")
    dt += f' data-loc="{_e(loc)}"' if loc else ""
    # 076: the ride's direction — the pane plays the lift transition
    # over this card. Only "up"/"down" ever ride the wire.
    lift = str(getattr(scene, "lift", "") or "")
    if lift in ("up", "down"):
        dt += f' data-lift="{_e(lift)}"'
    if getattr(scene, "enemy", None):
        fight = "warden" if scene.event_kind == "boss" else "wilds"
        dt += f' data-fight="{fight}"'
        # the foe's slug — fight3d warms only THIS creature's model
        foe = str(scene.enemy.get("id", "") or "")
        if foe:
            dt += f' data-foe3d="{_e(foe)}"'
    # the climber's rig — race:line[:slug+slug…] — so fight3d warms one
    # rig, not fifteen. 080: the third field names the worn item GLBs so
    # the finisher's gear is warm before the kill card lands.
    m = scene.meters
    if m and getattr(m, "race", "") and getattr(m, "line", ""):
        rig = f"{m.race}:{m.line}"
        gear = [g for g in (getattr(m, "gear", None) or []) if g]
        if gear:
            rig += ":" + "+".join(gear)
        dt += f' data-rig3d="{_e(rig)}"'
    # PLAN3: the live 3D finisher's spec — the creature, the killing
    # blow's race/line, and the SAME tint the creature's banner wears,
    # so the canvas inks itself like the card. Only the website's
    # fight3d layer reads it; everything else leaves the attr alone.
    k3 = getattr(scene, "kill3d", None)
    if k3 and k3.get("id") and not ar:
        k3 = dict(k3)
        k3["tint"] = _banner_tint(k3["id"], k3.get("specimen", ""))
        dt += f' data-kill3d="{_e(_json.dumps(k3))}"'
    if ar:
        # 067: the arena's script — the same tint law as kill3d
        ar = dict(ar)
        fid = str((ar.get("foe") or {}).get("id") or "")
        ar["tint"] = (_banner_tint(fid, (ar.get("foe") or {})
                                   .get("specimen", "")) if fid else TEXT)
        dt += f' data-arena="{_e(_json.dumps(ar))}"'
    # 067: which Labs experiments are on — the bar's flask reads it
    lb = getattr(scene, "labs", None)
    if lb:
        dt += f' data-labs="{_e(",".join(lb))}"'
    return (f'<div class="card" data-scene="{_e(scene.scene_id)}"{dt}>'
            + "".join(parts) + "</div>")


# The card grammar — shared by the legacy chat card document and the 009
# game pane. Pure presentation tokens; hosts add their own page CSS.
SCENE_CSS = f"""
@font-face{{font-family:"VGA";
 src:url(data:font/woff;base64,{_VGA_B64}) format("woff");}}
.card{{background:{PANEL};border:1px solid {BORDER};
 border-radius:0;margin:0;padding:12px 2ch 10px;color:{TEXT};
 font:16px/1.5 {FONT_STACK};
 -webkit-font-smoothing:none;font-smooth:never;text-rendering:optimizeSpeed;
 font-variant-numeric:tabular-nums;overflow:hidden;position:relative;}}

/* ── 067: the arena card ── */
.banner.arena{{position:relative;overflow:hidden;
 -webkit-mask-image:none;mask-image:none;
 /* phase 8 (roy): the card shows a 320×160 band. The 3D layer keeps
    its 320×300 frame; the canvas (and the floats layer with it) is
    windowed on the actor band — same px per row, nothing squashes:
    height 300/160; top pulled up so rows 115–275 show and the actors
    (rows ~150–240) sit centered — sky cut above, ground cut below.
    arena3d.js copies these two vars onto the canvas inline (its
    createStage ships inset:0/height:100% inline, which beats any
    stylesheet rule — the squash bug of 0.96.0). */
 --awin-h:187.5%;--awin-top:-71.9%;}}
.banner.arena canvas{{position:absolute;left:0;width:100%;
 top:var(--awin-top);height:var(--awin-h);
 image-rendering:pixelated;display:block;}}
/* 067 phase 6: one row along the top, half a line down — the climber's
   slab left, the foe's right, both top-aligned; a frame too narrow for
   both wraps the foe's slab under (still flush right). */
.ahuds{{position:absolute;left:.5em;right:.5em;top:.5em;z-index:3;display:flex;
 justify-content:space-between;align-items:flex-start;flex-wrap:wrap;
 gap:4px;pointer-events:none;}}
/* 067 phase 7 (roy): no slab box — the ink sits on black only where
   there is text; the scene shows between the lines */
.astat{{background:none;padding:0;white-space:pre;color:{BRIGHT};
 pointer-events:auto;}}
.astat>div{{background:{INK};width:fit-content;padding:0 .5ch;}}
.astat .off{{color:{DIM};}}
.astat.foe{{margin-left:auto;text-align:right;}}
.astat.foe>div{{margin-left:auto;}}
/* 0.97.1 (roy): the [i] rides the foe's nameplate in the live arena */
.aname .info{{display:inline-flex;margin-left:1ch;color:{DIM};}}
/* 0.97.1 (roy): the win amounts cast a crisp black shadow — the same
   shape shifted one DRAWING pixel right+down (45°). The big font's
   pixel is one char wide and half a line tall → 1ch/.5em scales with
   the font; the icons are 16×16 grids, so their pixel is display/16.
   Icons at 150% (30→45px), same 16×16 resolution. */
.awin .bigtx div{{text-shadow:1ch .5em 0 {INK};}}
/* 0.97.2 (roy): the filter sits on the .egsh wrapper, NOT on the masked
   .eg — mask paints after filter, so a shadow on the .eg itself is
   clipped by its own mask and never shows. */
.awin .thead .eg{{width:45px;height:45px;}}
.awin .thead>.egsh{{filter:drop-shadow(2.8125px 2.8125px 0 {INK});}}
/* a narrow stage (phone): the slabs drop to 12px so both still share
   the top line with the 20-cell bars */
@container (max-width: 600px){{.astat{{font-size:12px;line-height:1.4;}}
 .astat .aico{{width:12px;height:12px;vertical-align:-2px;}}
 /* phase 8: the win amounts shrink with the 160 band so they never
    swallow the scene on a phone */
 .awin .tallies{{font-size:9px;gap:0 14px;}}
 /* 150% of the 16px trim icon; drawing pixel 24/16 = 1.5px */
 .awin .thead .eg{{width:24px;height:24px;}}
 .awin .thead>.egsh{{filter:drop-shadow(1.5px 1.5px 0 {INK});}}}}
/* phase 8: a phone-narrow stage — the HP line is 31ch of pre (20 blocks
   + the numbers); at 12px two slabs with a 3-digit foe HP outgrow the
   row and the foe slab wraps under. 10px keeps both on the top line. */
@container (max-width: 440px){{.astat{{font-size:10px;}}
 .astat .aico{{width:10px;height:10px;vertical-align:-1px;}}
 .astat .apouch .picon{{width:12px;height:12px;}}}}
.astat .aname{{color:{BRIGHT};}}
.astat .aico{{width:16px;height:16px;vertical-align:-3px;margin:0 0 0 4px;}}
.astat .aico.lead{{outline:1px solid {GOLD};outline-offset:1px;}}
.astat .agear{{line-height:1.2;padding:2px 0 3px;}}
.astat .agear .aico{{margin:0 6px 0 0;}}
.astat .akw{{margin-left:3px;font-size:12px;}}
.aico{{display:inline-block;width:14px;height:14px;vertical-align:-2px;
 background-color:{TEXT};mask-size:100% 100%;-webkit-mask-size:100% 100%;
 mask-repeat:no-repeat;-webkit-mask-repeat:no-repeat;
 image-rendering:pixelated;margin:0 2px;}}
.akind .akb{{display:inline-block;margin-left:6px;white-space:nowrap;
 font-size:11px;letter-spacing:.06em;}}
/* the floats layer wears the SAME window as the canvas so screenOf()'s
   percentages (of the full 320×300 frame) keep landing on the heads;
   the banner's overflow clips what falls outside the band */
.afloats{{position:absolute;left:0;right:0;top:var(--awin-top,0);
 height:var(--awin-h,100%);z-index:4;pointer-events:none;}}
.afloat{{position:absolute;--dx:0px;
 transform:translate(calc(-50% + var(--dx)),-50%);
 background:#000;color:{RED};padding:1px 6px;font-size:16px;
 white-space:nowrap;animation:afloat 3s linear forwards;}}
.afloat.blocked{{color:{TEXT};}} .afloat.foe{{color:{GOLD};}}
.afloat.miss{{color:{BRIGHT};animation:ajitter 3s linear forwards;}}
/* 067 phase 5: 3 s travel — full ink for the first 500 ms, then the fade */
@keyframes afloat{{0%{{opacity:1;margin-top:0;}}17%{{opacity:1;}}
 100%{{opacity:0;margin-top:-44px;}}}}
@keyframes ajitter{{0%,17%{{opacity:1;}}
 3%{{margin-left:-6px;}}6%{{margin-left:6px;}}9%{{margin-left:-5px;}}
 12%{{margin-left:5px;}}15%{{margin-left:-3px;}}18%{{margin-left:3px;}}
 21%{{margin-left:0;}}100%{{opacity:0;margin-top:-30px;}}}}
.alog{{margin:8px 0 0;padding:0 1ch;border-top:1px dashed {BORDER};}}
.alog .aline{{color:{TEXT};}}
.alog .aline.pending{{display:none;}}
.banner.arena{{container-type:inline-size;}}
/* 067 phase 8 v2 (roy): the tiles are a TOOLBAR in the card's flow,
   directly under the stage — never over the picture. Each tile is a
   ROW: a big 76px black box (56px picon, ART ink, no border) with a
   4-line text column on its RIGHT — [n], the label, the gold ATK, the
   [i] — every line the card's own 16px; the icon spans all four
   lines. Round cards only. */
.options.arena-opts{{flex-direction:row;flex-wrap:wrap;gap:8px 14px;
 justify-content:center;align-items:flex-start;margin:6px 0 0;
 border:0;padding:0;background:none;}}
.arena-opts.busy .atile{{pointer-events:none;opacity:.45;}}
.arena-opts .atcell{{position:relative;display:flex;}}
.arena-opts .opt.atile{{position:relative;flex-direction:row;
 align-items:flex-start;justify-content:flex-start;width:auto;
 min-width:0;padding:0;background:none;border:0;gap:8px;
 text-align:left;}}
.arena-opts .opt.atile::after{{content:none;}}
.arena-opts .abox{{position:relative;width:76px;height:76px;flex:none;
 background:{INK};display:inline-flex;align-items:center;
 justify-content:center;}}
.arena-opts .abox .picon{{width:56px;height:56px;}}
.arena-opts .opt.atile:hover:not(:disabled) .abox,
.arena-opts .opt.atile:focus-visible .abox{{outline:1px solid {BRIGHT};}}
.arena-opts .atile .atxt{{display:flex;flex-direction:column;
 align-items:flex-start;height:76px;white-space:nowrap;
 letter-spacing:.04em;padding:0;line-height:1.2;}}
.arena-opts .atile .atxt .key{{min-width:0;text-align:left;}}
.arena-opts .atile .ahint{{display:none;}}
.arena-opts .atile .aatk{{color:{GOLD};line-height:1.2;
 pointer-events:none;}}
/* the win amounts over the settled scene — no slab, no mark heaps
   (roy): the big lines float clear and the scene stays visible */
.banner.arena .awin{{position:absolute;inset:0;z-index:5;display:flex;
 align-items:center;justify-content:center;pointer-events:none;}}
.banner.arena .awin .tallies{{background:none;padding:0;margin:0;}}
.astat .apouch{{display:flex;align-items:center;gap:.5ch;color:{ART};}}
.astat .apouch .picon{{width:14px;height:14px;}}
.arena-opts .atile.locked .lbl{{color:{DIM};}}
/* the [i] is the column's LAST line — a sibling of the button (a
   focusable tip can't live inside one), pinned where line 4 falls:
   left of the 76px box + 8px gap, bottom of the 76px row. */
.atcell .info{{position:absolute;left:84px;bottom:0;border:0;
 background:none;line-height:1.2;}}
/* ── 009: the enemy plate — the foe's meter in the player's grammar ── */
.bwrap{{position:relative;}}
.estat{{position:absolute;left:12px;bottom:12px;background:{INK};
 padding:0 1ch;white-space:pre;color:{BRIGHT};}}
.estat .off{{color:{DIM};}}
.ehead{{margin-top:6px;}}
.banner+.notices,.banner+.paper{{margin-top:10px;}}
.banner+.headline{{margin-top:10px;}}
.eplate{{display:flex;align-items:baseline;gap:1ch;}}
.eplate .erng{{color:{DIM};white-space:nowrap;}}
.emod{{color:{DIM};}}
/* 0.96.2 (roy): the [i] rides the headline name, dim until hovered;
   its tip IS the dossier panel. Inside #tipbox the box itself is the
   aether frame, so the panel sheds its own border/slab — the LOOK of
   the sheet (dhead, rows, icons) is byte-identical. */
.headline .info{{display:inline-flex;margin-left:1ch;color:{DIM};}}
.dossier{{border:1px solid {AETHER};background:{INK};
 padding:10px 1.5ch;margin:8px 0 2px;}}
#tipbox .dossier{{border:0;background:none;padding:0;margin:0;}}
.dhead{{color:{AETHER};text-transform:uppercase;letter-spacing:.08em;
 margin-bottom:6px;}}
.drw{{display:flex;gap:1ch;align-items:flex-start;padding:3px 0;
 color:{DIM};}}
.drw b{{color:{TEXT};}}
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
/* 025/006: the haul. The amount shouts in the big font, one column per
   kind side by side and centered; marks tile ten to a row under their
   own amount so a 99-coin kill still reads as one heap. */
.tallies{{display:flex;flex-wrap:wrap;justify-content:center;
 align-items:flex-start;gap:8px 4ch;margin:10px 0 2px;line-height:1;}}
.thaul{{display:flex;flex-direction:column;align-items:center;gap:5px;}}
.thead{{display:flex;align-items:center;gap:10px;}}
/* 0.97.2 (roy): the icon sits in an .egsh wrapper (the shadow carrier —
   mask paints after filter, so the drop-shadow must sit on a parent). */
.thead>.egsh{{display:flex;flex:none;}}
.thead .eg{{width:30px;height:30px;vertical-align:0;flex:none;}}
.thead .bigtx{{padding:0;}}
.thaul .tmarks{{display:inline-grid;grid-template-columns:repeat(10,14px);
 gap:1px;}}
.thaul .tmarks .eg{{width:14px;height:14px;vertical-align:0;}}
.thaul .tnote{{color:{FAINT};}}
.thaul .tsr{{position:absolute;width:1px;height:1px;overflow:hidden;
 clip:rect(0 0 0 0);white-space:nowrap;}}
.dlore{{color:{FAINT};margin-top:6px;
 border-top:1px dashed {BORDER};padding-top:6px;}}
.banner{{display:block;width:calc(100% + 4ch);margin:-12px -2ch 0;
 mask-size:100% 100%;-webkit-mask-size:100% 100%;mask-repeat:no-repeat;
 -webkit-mask-repeat:no-repeat;image-rendering:pixelated;
 border-bottom:1px solid {BORDER};}}
/* ── 027: the notice board. Blue is the notification ink — it never
   means a stat, only "something waits for you". ── */
.notices{{border:1px solid {BORDER};background:{INK};
 padding:8px 1.5ch 9px;margin:0 0 10px;}}
.nhead{{color:{AETHER};text-transform:uppercase;letter-spacing:.14em;
 margin-bottom:5px;}}
.nrow{{display:flex;align-items:center;gap:1ch;width:100%;margin-top:4px;
 background:transparent;border:1px solid transparent;border-radius:0;
 padding:4px .5ch;font:inherit;color:{TEXT};text-align:left;
 cursor:pointer;}}
/* hover / focus = reverse video: black on aether across the whole row,
   no outline — the same read as .opt's black-on-gold */
.nrow:hover:not(:disabled),.nrow:focus-visible{{background:{AETHER};
 border-color:{AETHER};outline:none;color:{INK};}}
.nrow .nk{{flex:none;color:{AETHER};letter-spacing:.12em;
 min-width:8ch;}}
.nrow .ntx{{flex:1;min-width:0;color:{DIM};}}
.nrow .ngo{{flex:none;color:{FAINT};}}
.nrow:hover:not(:disabled) .nk,.nrow:hover:not(:disabled) .ntx,
.nrow:hover:not(:disabled) .ngo,.nrow:focus-visible .nk,
.nrow:focus-visible .ntx,.nrow:focus-visible .ngo{{color:{INK};}}
.nrow:hover:not(:disabled) .nb,.nrow:focus-visible .nb{{
 background:{INK};color:{AETHER};}}
/* 070: last week's reward — one square around the numbers, labels out. */
.weekbox{{margin-top:8px;}}
.whead{{color:{AETHER};margin-bottom:6px;}}
.wbody{{position:relative;}}
.wrail{{position:absolute;left:0;top:0;bottom:0;width:4.4ch;
 border:1px solid {AETHER};border-radius:0;box-sizing:border-box;
 pointer-events:none;}}
.wlist{{display:flex;flex-direction:column;padding:3px 0;}}
.wrow{{display:flex;align-items:center;gap:1ch;width:100%;
 background:transparent;border:1px solid transparent;border-radius:0;
 padding:4px 0;font:inherit;color:{TEXT};text-align:left;cursor:pointer;}}
.wnum{{flex:none;width:4.4ch;text-align:center;color:{AETHER};
 font-variant-numeric:tabular-nums;position:relative;z-index:1;}}
.wtx{{flex:1;min-width:0;color:{DIM};}}
.wtitle{{color:{TEXT};}}
.whint{{flex:none;color:{GOLD};padding-right:.5ch;}}
.wrow:hover:not(:disabled) .wtx,.wrow:focus-visible .wtx{{
 background:{AETHER};color:{INK};}}
.wrow:hover:not(:disabled) .wtitle,.wrow:focus-visible .wtitle,
.wrow:hover:not(:disabled) .whint,.wrow:focus-visible .whint{{
 color:{INK};}}
.wrow:hover:not(:disabled),.wrow:focus-visible{{outline:none;}}
.nb{{flex:none;display:inline-block;min-width:2ch;padding:0 .5ch;
 background:{AETHER};color:{INK};text-align:center;
 font-variant-numeric:tabular-nums;}}
.badge{{flex:none;display:inline-block;min-width:2ch;padding:0 .4ch;
 margin-left:1ch;color:{AETHER};background:transparent;
 border:2px solid {AETHER};text-align:center;
 font-variant-numeric:tabular-nums;box-sizing:border-box;
 cursor:help;}}
/* ── 009: the Crier under the terminal law — a black sheet behind a
   brown frame, brown ink, the masthead a brown reverse-video bar. ── */
.paper{{position:relative;margin:0 0 10px;background:{INK};
 border:1px solid {BROWN};}}
.paper .pbody{{padding:0 1ch 8px;color:{BROWN};}}
.paper .pmast{{letter-spacing:.22em;text-transform:uppercase;
 text-align:center;background:{BROWN};color:{INK};
 margin:0 -1ch 6px;padding:0 1ch;}}
.paper .phl{{margin-bottom:5px;text-wrap:balance;}}
.paper .pit{{display:-webkit-box;-webkit-line-clamp:2;
 -webkit-box-orient:vertical;overflow:hidden;padding:3px 0 2px;
 border-top:1px dotted {BROWN};}}
.paper .pit::before{{content:"· ";}}
.paper .pclose{{position:absolute;top:0;right:0;z-index:2;
 background:transparent;border:0;color:{INK};font:inherit;
 line-height:1.5;cursor:pointer;padding:0 .6ch;}}
.paper .pclose:hover{{background:{INK};color:{BROWN};}}
/* ── 027: the card's own input ── */
.ask{{margin:10px 0 0;padding:8px 1ch;border:1px solid {AETHER};
 background:{INK};display:block;}}
.ask .alab{{display:block;color:{DIM};margin-bottom:5px;}}
.ask .arow{{display:flex;gap:6px;align-items:stretch;}}
.ask .ti{{flex:1;min-width:0;background:{INK};border:1px solid {AETHER};
 color:{TEXT};padding:6px 1.5ch;font:inherit;border-radius:0;
 font-variant-numeric:tabular-nums;}}
.ask .ti::placeholder{{color:{FAINT};}}
.ask .ti:focus{{outline:none;border-color:{TEXT};}}
.ask .asend{{flex:none;background:{AETHER};border:1px solid {AETHER};
 color:{INK};font:inherit;letter-spacing:.08em;
 padding:6px 2ch;border-radius:0;cursor:pointer;}}
.ask .asend:hover:not(:disabled){{background:{TEXT};border-color:{TEXT};}}
.ask .asend:disabled{{opacity:.5;cursor:default;}}
/* ── 027: picture tiles (faction sigils) ── */
.gal{{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));
 gap:8px;margin:10px 0 0;}}
.gtile{{display:flex;flex-direction:column;gap:4px;background:{PANEL2};
 border:1px solid {BORDER};border-radius:0;padding:6px;font:inherit;
 color:{TEXT};text-align:left;cursor:pointer;}}
.gtile:hover:not(:disabled){{border-color:{GOLD};}}
.gtile:focus-visible{{outline:1px solid {AETHER};outline-offset:1px;}}
.gtile .gpic{{display:block;width:100%;aspect-ratio:320/112;
 mask-size:100% 100%;-webkit-mask-size:100% 100%;mask-repeat:no-repeat;
 -webkit-mask-repeat:no-repeat;image-rendering:pixelated;}}
.gtile .gpic.none{{background:{BORDER};}}
.gtile:hover .gpic{{background-color:{GOLD};}}
.gtile .glab{{color:{TEXT};}}
.gtile .gsub{{color:{FAINT};}}
/* ── 052: character cards — three climbers on one ground line ── */
.gal.chars{{grid-template-columns:repeat(3,1fr);}}
.gal.chars .gtile{{align-items:center;text-align:center;
 padding:12px 6px 10px;}}
.gal.chars .gbox{{flex:1;display:flex;align-items:flex-end;
 justify-content:center;width:100%;}}
.gal.chars .gpic.pchar{{display:block;width:auto;
 mask-size:100% 100%;-webkit-mask-size:100% 100%;mask-repeat:no-repeat;
 -webkit-mask-repeat:no-repeat;image-rendering:pixelated;}}
.gal.chars .glab{{letter-spacing:.08em;margin-top:6px;}}
.gal.chars .gsub{{min-height:3.2em;}}
/* ── 042: the presence grid — seven faces to a row ── */
.phere{{margin:12px 0 0;}}
.phere .phead{{color:{FAINT};text-transform:uppercase;
 letter-spacing:.1em;margin-bottom:6px;}}
.pgrid{{display:grid;grid-template-columns:repeat(7,1fr);gap:6px;}}
.pmrow{{display:flex;justify-content:flex-end;margin-top:4px;}}
.pmore{{background:none;border:0;padding:0 1ch;font:inherit;
 color:{TEXT};cursor:pointer;}}
.pmore:hover,.pmore:focus-visible{{background:{TEXT};color:{INK};
 outline:none;}}
.pmore:disabled{{color:{DIM};background:none;cursor:default;}}
.ptile{{display:flex;flex-direction:column;align-items:center;gap:2px;
 background:{PANEL2};border:1px solid {BORDER};border-radius:0;
 padding:5px 2px 4px;font:inherit;color:{TEXT};cursor:pointer;
 min-width:0;}}
.ptile:hover:not(:disabled),.ptile:focus-visible{{background:{GOLD};
 border-color:{GOLD};outline:none;color:{INK};}}
.ptile:hover:not(:disabled) .pface,.ptile:focus-visible .pface{{
 filter:brightness(0);}}
.ptile:hover:not(:disabled) .pname,.ptile:hover:not(:disabled) .plvl,
.ptile:hover:not(:disabled) .psub,.ptile:focus-visible .pname,
.ptile:focus-visible .plvl,.ptile:focus-visible .psub{{color:{INK};}}
.ptile .pfbox{{position:relative;display:flex;height:72px;
 align-items:flex-end;}}
.ptile .pface{{display:block;height:56px;width:auto;
 image-rendering:pixelated;}}
.ptile .pface.giant{{height:72px;}}
.ptile .pface.none{{display:block;height:56px;width:28px;
 background:{BORDER};}}
.ptile .pzzz{{position:absolute;top:-2px;right:-14px;background:{INK};
 border:1px solid {AETHER};color:{AETHER};
 padding:0 3px;letter-spacing:.06em;}}
.ptile .prank{{position:absolute;top:-2px;left:-14px;background:{INK};
 border:1px solid {BORDER};color:{DIM};padding:0 3px;
 font-variant-numeric:tabular-nums;}}
.ptile .pname{{max-width:100%;overflow:hidden;text-overflow:ellipsis;
 white-space:nowrap;color:{BRIGHT};}}
.ptile .plvl{{color:{FAINT};
 font-variant-numeric:tabular-nums;}}
.ptile .psub{{max-width:100%;overflow:hidden;text-overflow:ellipsis;
 white-space:nowrap;color:{DIM};
 font-variant-numeric:tabular-nums;}}
/* ── 027: the pack popup — click an item, act on it ── */
.pmenu{{position:fixed;z-index:100;min-width:220px;max-width:300px;
 background:{INK};border:1px solid {AETHER};
 padding:8px 1.5ch;color:{TEXT};
 font:16px/1.5 {FONT_STACK};-webkit-font-smoothing:none;}}
.pmenu .phead{{color:{AETHER};text-transform:uppercase;
 letter-spacing:.1em;margin-bottom:6px;}}
.pmenu .pact{{display:flex;gap:1ch;align-items:center;width:100%;
 background:none;border:0;border-radius:0;
 color:{TEXT};font:inherit;text-align:left;padding:2px 0;
 margin-top:2px;cursor:pointer;}}
.pmenu .pact:hover:not(:disabled){{background:{GOLD};color:{INK};}}
.pmenu .pact:hover:not(:disabled) .phint{{color:{INK};}}
.pmenu .pact .phint{{margin-left:auto;color:{FAINT};}}
.pmenu .pwhy{{color:{DIM};}}
.inv .item{{font:inherit;border-radius:0;padding:0;}}
.inv .item.act{{cursor:pointer;}}
.inv .item.act:hover,.inv .item.act:focus-visible{{
 border-color:{GOLD};}}
.inv .item.act:hover .picon,.inv .item.act:focus-visible .picon{{
 background-color:{GOLD} !important;}}
.eyebrow{{background:{TEXT};color:{INK};text-transform:uppercase;
 letter-spacing:.08em;margin:0 -2ch;padding:0 1ch;}}
.card>.eyebrow:first-child{{margin-top:-12px;}}
.headline{{margin:4px 0 0;text-wrap:balance;}}
.support{{color:{TEXT};}}
.shard{{display:flex;gap:1ch;margin-top:8px;color:{DIM};}}
.shard .glyph{{color:{AETHER};flex:none;}}
.body{{margin:6px 0 0;white-space:pre-wrap;}}
/* ── 031 §9: the NPC block — portrait left of the words ── */
.npcbox{{float:left;display:flex;flex-direction:column;align-items:center;
 gap:3px;margin:8px 2ch 4px 0;border:1px solid {BORDER};background:{INK};
 padding:4px 4px 2px;}}
.npcbox .npcimg{{width:80px;aspect-ratio:100/200;display:block;
 mask-size:100% 100%;-webkit-mask-size:100% 100%;mask-repeat:no-repeat;
 -webkit-mask-repeat:no-repeat;image-rendering:pixelated;}}
.npcbox .npclab{{color:{BRIGHT};text-transform:uppercase;
 letter-spacing:.12em;}}
/* ── 009: the activity band — a gold reverse-video bar ── */
.actband{{margin-top:10px;padding:0 1ch;
 background:{GOLD};color:{INK};letter-spacing:.02em;}}
/* ── 009: the art band — art above, the amount in a bordered box ── */
.stripband{{position:relative;margin:8px 0 0;background:{INK};
 border:1px solid {BORDER};border-bottom:0;aspect-ratio:320/50;
 overflow:hidden;}}
.stripband .bart{{position:absolute;inset:0;mask-size:cover;
 -webkit-mask-size:cover;mask-position:center;-webkit-mask-position:center;
 mask-repeat:no-repeat;-webkit-mask-repeat:no-repeat;
 image-rendering:pixelated;}}
.striptx{{margin:8px 0 0;border:1px solid {BORDER};padding:0 1ch;
 text-align:center;color:{BRIGHT};letter-spacing:.06em;
 font-variant-numeric:tabular-nums;}}
.stripband+.striptx{{margin-top:0;}}
.striptx .eg{{width:18px;height:18px;vertical-align:-3px;}}
.bigtx{{line-height:1;letter-spacing:0;padding:5px 0 4px;
 text-align:center;overflow:hidden;}}
.bigtx div{{white-space:pre;}}
.bigtx .bwhite{{color:{BRIGHT};}}
.bigtx .bgold{{color:{GOLD};}}
.bigtx .binh{{color:inherit;}}
/* ── 007: folded shop shelves (▣ markers) ── */
.fold{{margin:6px 0 0;}}
.fold summary{{list-style:none;cursor:pointer;user-select:none;
 color:{DIM};}}
.fold summary:hover,.fold[open] summary{{color:{BRIGHT};}}
.fold summary::-webkit-details-marker{{display:none;}}
.fold summary::before{{content:"▸ ";color:{FAINT};}}
.fold[open] summary::before{{content:"▾ ";}}
.fold .body{{margin-left:1ch;}}
/* ── 059: the callout box (▛ markers) — white frame, white words ── */
.callout{{border:1px solid {BRIGHT};padding:10px 12px;margin:10px 0 4px;
 color:{BRIGHT};}}
.callouth{{color:{BRIGHT};font-weight:bold;letter-spacing:.06em;
 margin-bottom:6px;}}
.callout .body{{color:{BRIGHT};margin:4px 0 0;}}
/* 062: the solid variant (▜ markers) — no frame; a slate ground with a
   gold title band; the words stay bright on it */
.callout.solid{{border:0;background:{SLATE};padding:0 0 10px;
 margin:12px 0 6px;}}
.callout.solid .callouth{{background:{GOLD};color:{INK};padding:6px 12px;
 margin:0 0 8px;letter-spacing:.12em;text-transform:uppercase;}}
.callout.solid .body{{padding:0 12px;}}
.options{{clear:both;margin:10px 0 0;
 display:flex;flex-direction:column;
 border-top:1px dashed {BORDER};border-bottom:1px dashed {BORDER};
 padding:6px 0;}}
.options+.ident,.options+.rail{{border-top:0;padding-top:0;}}
.opt{{display:flex;align-items:center;gap:1ch;width:100%;
 background:none;border:0;padding:.3rem 0;
 font:inherit;color:inherit;text-align:left;border-radius:0;
 cursor:pointer;}}
/* 009: the dot leader — the line between a door and its price */
.opt::after{{content:"· · · · · · · · · · · · · · · · · · · · · · · · "
 "· · · · · · · · · · · · · · · · · · · · · · · · · · · · · · · · ·";
 order:1;flex:1;overflow:hidden;white-space:nowrap;color:{DIM};
 text-align:left;min-width:2ch;}}
.opt .hint{{order:2;margin-left:0;color:{DIM};text-align:right;
 white-space:nowrap;}}
.opt .lbl{{color:{BRIGHT};}}
.opt .key{{flex:none;color:{GOLD};min-width:2ch;text-align:right;
 white-space:pre;}}
.opt .key::before{{content:"[";color:{DIM};}}
.opt .key::after{{content:"]";color:{DIM};}}
.opt .key.aether{{color:{AETHER};}}
/* hover / focus = reverse video: black on gold across the whole line */
.opt:hover:not(:disabled),.opt:focus-visible{{background:{GOLD};
 outline:none;}}
.opt:hover:not(:disabled) .key,.opt:hover:not(:disabled) .lbl,
.opt:hover:not(:disabled) .hint,.opt:hover:not(:disabled) .amt,
.opt:hover:not(:disabled) .key::before,
.opt:hover:not(:disabled) .key::after,
.opt:hover:not(:disabled)::after,
.opt:focus-visible .key,.opt:focus-visible .lbl,.opt:focus-visible .hint,
.opt:focus-visible .amt,.opt:focus-visible .key::before,
.opt:focus-visible .key::after,.opt:focus-visible::after{{
 color:{INK}!important;}}
.opt:hover:not(:disabled) .badge,.opt:focus-visible .badge{{
 background:transparent;color:{AETHER};border-color:{AETHER};}}
/* painted spans INSIDE a hovered row (coin counts, lock lines, keys of
   any colour) go black too — reverse video means ALL ink flips */
.opt:hover:not(:disabled) .lbl *,.opt:hover:not(:disabled) .hint *,
.opt:hover:not(:disabled) .amt *,.opt:hover:not(:disabled) .key *,
.opt:focus-visible .lbl *,.opt:focus-visible .hint *,
.opt:focus-visible .amt *,.opt:focus-visible .key *,
.opt.chosen .lbl *,.opt.chosen .hint *{{color:{INK}!important;}}
/* the locked row's grey hover flips its ink the same way */
.opt.locked:hover:not(:disabled) .key,
.opt.locked:hover:not(:disabled) .lbl,
.opt.locked:hover:not(:disabled) .hint,
.opt.locked:hover:not(:disabled) .lbl *,
.opt.locked:hover:not(:disabled) .hint *,
.opt.locked:hover:not(:disabled) .key::before,
.opt.locked:hover:not(:disabled) .key::after,
.opt.locked:hover:not(:disabled)::after{{color:{INK}!important;}}
.opt.locked .lbl,.opt.locked .key,.opt.locked .key::before,
.opt.locked .key::after{{color:{DIM};}}
.opt.locked .hint{{color:{DIM};}}
.opt.locked:hover:not(:disabled),.opt.locked:focus-visible{{
 background:{DIM};}}
.opt:disabled{{cursor:default;}}
/* 068: the danger row — red label and key; hover flips to black on red */
.opt.danger .lbl,.opt.danger .key{{color:{RED};}}
.opt.danger:hover:not(:disabled),.opt.danger:focus-visible{{
 background:{RED};}}
/* 068: the colour swatch — two block glyphs in the ink before a colour's name */
.opt .swatch{{flex:none;line-height:1;}}
.opt.chosen{{background:{GOLD};}}
.opt.chosen .key,.opt.chosen .lbl,.opt.chosen .hint,
.opt.chosen .key::before,.opt.chosen .key::after,.opt.chosen::after{{
 color:{INK}!important;}}
.opt.stale{{opacity:.45;}}
.opt .gicon{{width:32px;height:32px;flex:none;display:inline-block;
 background-color:{DIM};mask-size:100% 100%;-webkit-mask-size:100% 100%;
 mask-repeat:no-repeat;-webkit-mask-repeat:no-repeat;
 image-rendering:pixelated;}}
/* 057: a weapon's own 30x48 face keeps its portrait aspect */
.opt .gicon.gw{{width:30px;height:48px;}}
/* ── 030: gate floor rows — a door you can see through ── */
.opt.ftile{{min-height:96px;}}
.farts{{flex:none;display:flex;gap:4px;align-items:center;}}
.fart{{display:inline-block;width:120px;max-width:24vw;height:84px;
 mask-size:cover;-webkit-mask-size:cover;mask-position:center;
 -webkit-mask-position:center;mask-repeat:no-repeat;
 -webkit-mask-repeat:no-repeat;image-rendering:pixelated;}}
.opt.ftile:hover .fart{{background-color:{INK};}}
.opt.ftile.locked:hover .fart{{background-color:{INK};}}
.opt:hover .gicon{{background-color:{INK};}}
.opt.locked .gicon,.opt.locked:hover .gicon{{background-color:{INK};}}
.orow{{display:flex;align-items:stretch;gap:5px;}}
.orow .opt{{flex:1;min-width:0;}}
/* 073: districts on the square — a header is not a door; a nested
   row sits under the door you'd look for first. */
.osect{{color:{FAINT};letter-spacing:.14em;text-transform:uppercase;
 margin:8px 0 2px;padding-top:6px;border-top:1px dashed {BORDER};}}
.osect:first-child{{margin-top:0;padding-top:2px;border-top:0;}}
.orow.nest{{padding-left:3ch;}}
/* ── 031 §14: the card wall — a shop shelf you look at, not read ── */
.ggrid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(148px,1fr));
 gap:6px;margin-bottom:6px;}}
.gcell{{position:relative;display:flex;}}
.gcard{{flex-direction:column;align-items:center;justify-content:flex-start;
 gap:6px;padding:22px 1ch 12px;text-align:center;position:relative;
 border:1px solid {BORDER};}}
.gcard::after{{content:none;}}
.gcard .hint{{margin-left:0;}}
.gcard:hover:not(:disabled) .hint,.gcard:hover:not(:disabled) .lbl{{
 color:{INK}!important;}}
.gcard .key{{position:absolute;top:5px;left:7px;}}
.gcard .gicon{{width:56px;height:56px;background-color:{ART};}}
.gcard .gicon.gw{{width:60px;height:96px;}}
.gcard:hover .gicon{{background-color:{INK};}}
.gcard.locked .gicon{{background-color:{DIM};}}
.gcard.locked:hover .gicon{{background-color:{INK};}}
.gcard .lbl{{line-height:1.3;}}
.gcard .hint{{margin-left:0;text-align:center;color:{DIM};
 display:block;white-space:nowrap;}}
.gcard .hint+.hint{{margin-top:-3px;}}
.gcard .hint.wrap{{white-space:normal;line-height:1.3;max-width:100%;}}
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
/* 079: the verdict arrow owns the corner; the [i] sits just under it */
.gcell .delta{{position:absolute;top:5px;right:6px;width:16px;
 height:16px;mask-size:100% 100%;-webkit-mask-size:100% 100%;
 mask-repeat:no-repeat;-webkit-mask-repeat:no-repeat;
 image-rendering:pixelated;pointer-events:none;z-index:1;}}
.gcell .delta~.info{{top:24px;}}
/* ── 057b: the weapon preview — the card, 20% bigger, portrait at
   full scale, the buy button at the foot. Desktop: lives on :hover.
   Touch: a tap opens it (.wopen, wired in TIP_JS), ✕ closes. ── */
.gcell .wprev{{display:none;position:absolute;left:-10%;top:-10%;
 width:120%;height:120%;z-index:30;flex-direction:column;
 align-items:center;gap:4px;padding:10px 8px 8px;text-align:center;
 background:{PANEL};border:1px solid {ART};}}
.gcell.wopen .wprev{{display:flex;}}
@media (hover: hover){{
 .gcell:hover .wprev{{display:flex;}}
 .wprev .wpx{{display:none;}}}}
.wpart{{flex:1;width:100%;min-height:0;
 mask-size:contain;-webkit-mask-size:contain;
 mask-position:center;-webkit-mask-position:center;
 mask-repeat:no-repeat;-webkit-mask-repeat:no-repeat;
 image-rendering:pixelated;}}
.wpname{{color:{BRIGHT};line-height:1.3;flex:none;}}
.wpstat{{color:{DIM};flex:none;}}
.wprev .wpbuy{{width:100%;flex:none;justify-content:center;
 text-align:center;}}
.wpx{{position:absolute;top:2px;right:2px;background:none;border:0;
 color:{DIM};padding:4px 8px;cursor:pointer;z-index:1;}}
.wpx:hover{{color:{BRIGHT};}}
.info{{flex:none;display:flex;align-items:center;padding:0;
 background:none;border:0;color:{DIM};
 cursor:help;user-select:none;}}
.info::before{{content:"[";}}
.info::after{{content:"]";}}
.info:hover,.info:focus-visible{{color:{AETHER};outline:none;}}
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
.ident .idname{{color:{BRIGHT};}}
.ident .idwho{{color:{DIM};text-transform:uppercase;
 letter-spacing:.08em;}}
.ident .idfac{{color:{DIM};cursor:help;
 white-space:nowrap;}}
.ident .idfac b{{color:{TEXT};}}
.ident .idr{{margin-left:auto;display:inline-flex;gap:2ch;
 white-space:nowrap;}}
.ident .idlv{{color:{BRIGHT};cursor:help;}}
.ident .idgold{{color:{GOLD};cursor:help;}}
.pavatar{{margin:6px 0 12px;padding-bottom:10px;
 border-bottom:1px dashed {BORDER};}}
.pavatar .ident{{margin-top:0;padding-top:0;border-top:0;}}
.pavatar .gearmap .item{{cursor:help;}}
.profile{{display:flex;gap:2ch;align-items:flex-start;margin-top:8px;}}
.profile .portrait{{flex:none;height:auto;width:auto;
 min-height:200px;image-rendering:pixelated;}}
.profile .pcol{{flex:1;min-width:0;}}
/* ── 069: the gear map — slots either side of the figure. The columns
   are the height (4 × 60 + 3 × 6); the figure stretches to match. ── */
.gearmap{{display:grid;grid-template-columns:auto auto auto;gap:0 8px;
 align-items:stretch;flex:none;}}
.gearmap .slotcol{{display:flex;flex-direction:column;gap:6px;}}
.gearmap .pwrap{{display:flex;align-items:stretch;justify-content:center;
 min-width:60px;}}
.gearmap .pwrap .portrait{{height:258px;}}
.gearmap .pwrap canvas.figure3d{{display:block;image-rendering:pixelated;
 width:auto;}}
.slot.gm.locked{{background:#222;border:2px solid #555;opacity:1;
 cursor:help;}}
.slot.gm.locked .picon{{width:26px;height:26px;}}
.slot.gm.empty{{border:2px dotted {BORDER};background:transparent;
 opacity:.9;}}
.slot.gm.lead{{border-color:{GOLD};}}
.gearmap .item{{font:inherit;border-radius:0;padding:0;}}
.gearmap .item.act{{cursor:pointer;}}
.gearmap .item.act:hover,.gearmap .item.act:focus-visible{{
 border-color:{GOLD};}}
.gearmap .item.act:hover .picon,.gearmap .item.act:focus-visible .picon{{
 background-color:{GOLD} !important;}}
.profile .rail{{margin-top:0;padding-top:0;border-top:0;
 flex-direction:column;align-items:flex-start;gap:4px;}}
.profile .inv{{border-top:0;padding-top:0;margin-top:8px;}}
/* ── 059/062: the faction strip at the foot of the card — no box, the
   card's own dotted rule above it; banner + name are the door ── */
.facblk{{display:flex;align-items:center;gap:1.5ch;margin-top:10px;
 border-top:1px dashed {BORDER};padding:8px 0 0;color:{DIM};
 letter-spacing:.06em;text-transform:uppercase;min-width:0;}}
.facblk .facdoor{{display:flex;align-items:center;gap:1ch;flex:none;
 max-width:100%;min-width:0;background:none;border:0;margin:0;
 padding:2px 1ch 2px 0;font:inherit;letter-spacing:inherit;
 text-transform:inherit;color:{TEXT};cursor:pointer;text-align:left;
 transition:background-color .12s;}}
.facblk .facsig{{flex:none;height:60px;background-color:{ARTBRIGHT};
 image-rendering:pixelated;margin:-4px 0;
 mask-size:100% 100%;-webkit-mask-size:100% 100%;
 mask-repeat:no-repeat;-webkit-mask-repeat:no-repeat;
 transition:background-color .12s;}}
.facblk .facname{{color:{TEXT};letter-spacing:.14em;
 border-bottom:1px solid transparent;transition:color .12s,
 border-color .12s;white-space:nowrap;overflow:hidden;
 text-overflow:ellipsis;}}
/* 010: the door hovers in the faction's own ink — a flat block behind
   banner + name only; no growth, no glow; the counts stay put. */
.facblk .facdoor:hover,.facblk .facdoor:focus-visible{{
 background:var(--fac,{VIOLET_SOFT});}}
.facblk .facdoor:hover .facname,.facblk .facdoor:focus-visible .facname{{
 color:#000;border-bottom-color:transparent;}}
.facblk .facdoor:hover .facsig,.facblk .facdoor:focus-visible .facsig{{
 background-color:#000;}}
.facblk .facdoor.join:hover,.facblk .facdoor.join:focus-visible{{
 background:none;}}
.facblk .facdoor.join:hover .facname,
.facblk .facdoor.join:focus-visible .facname{{
 color:{GOLD};border-bottom-color:{GOLD};}}
.facblk .facdoor:focus-visible{{outline:0;}}
.facblk .facsub{{display:flex;flex-direction:column;align-items:flex-start;
 gap:1px;color:{DIM};text-transform:none;letter-spacing:.06em;
 line-height:1.35;}}
.facblk .facsub .dim{{color:{DIM};}}
.piprows{{margin-top:8px;color:{DIM};}}
.profile .piprows{{margin-top:0;}}
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
.slot{{position:relative;width:60px;height:60px;flex:none;
 background:{INK};border:1px solid {BORDER};display:inline-flex;
 align-items:center;justify-content:center;cursor:help;outline:none;}}
.slot.empty{{border-style:dashed;opacity:.5;}}
.slot.over{{border-style:dashed;border-color:{RED};}}
/* 012: rows flow to the card's edge — as many squares as fit */
.slotgrid{{display:flex;flex-wrap:wrap;gap:6px;}}
.picon{{width:42px;height:42px;flex:none;display:inline-block;
 mask-size:100% 100%;-webkit-mask-size:100% 100%;mask-repeat:no-repeat;
 -webkit-mask-repeat:no-repeat;image-rendering:pixelated;}}
/* 057: weapon art is 30x48 upright — in the square pack cell it sits
   centered at its own aspect instead of stretching to fill */
.picon.gw{{mask-size:contain;-webkit-mask-size:contain;
 mask-position:center;-webkit-mask-position:center;}}
.slot .ct{{position:absolute;right:2px;bottom:0;color:{TEXT};
 line-height:1.2;}}
.slot .dur{{position:absolute;left:3px;right:3px;bottom:2px;height:3px;
 background:{BORDER};}}
.slot .durf{{display:block;height:100%;}}
/* the VGA bitmap has no bold face — synthesized bold smears into mud,
   so bold is banned wherever this font renders; color carries emphasis */
b,strong{{font-weight:normal;}}
#tipbox{{position:fixed;display:none;z-index:99;max-width:44ch;
 background:{INK};border:1px solid {AETHER};color:{TEXT};
 padding:8px 1.5ch;font:16px/1.5 {FONT_STACK};
 -webkit-font-smoothing:none;pointer-events:none;
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
 .profile{{gap:1.5ch;align-items:flex-start;flex-wrap:wrap;}}
 .profile .portrait{{align-self:flex-start;min-height:0;height:210px;}}
 .gearmap{{margin:0 auto;}}
 .gearmap .pwrap .portrait{{height:210px;}}
 .profile .pcol{{flex-basis:100%;}}
 .ident{{flex-wrap:wrap;row-gap:2px;}}
 .ident .idr{{margin-left:auto;}}
 .facblk{{flex-wrap:wrap;row-gap:4px;}}
 .rail{{gap:.5ch 1.5ch;}}
 .piprow .pips{{grid-template-columns:repeat(10,minmax(12px,18px));}}
 .pip{{width:100%;max-width:16px;}}
 .slotgrid{{max-width:100%;}}
 .slot{{width:48px;height:48px;}}
 .picon{{width:36px;height:36px;}}
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
