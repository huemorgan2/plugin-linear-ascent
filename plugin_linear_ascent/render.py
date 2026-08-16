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
                b64 = base64.b64encode(open(path, "rb").read()).decode()
                w, h = (int(n) for n in size.split("x"))
                return f"data:image/png;base64,{b64}", w, h
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
            b64 = base64.b64encode(open(path, "rb").read()).decode()
            return f"data:image/png;base64,{b64}"
    return None


def _gear_art_slug(slug: str) -> str:
    """The slug whose art an item draws — keen/warded variants reuse
    their base item's face; relics draw their own; "" when the slug
    is neither FORGE gear nor a relic."""
    g = economy.FORGE.get(slug)
    if g is not None:
        return g.base or slug
    if slug in economy.RELICS or slug in economy.APOTHECARY:
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
        b64 = base64.b64encode(open(path, "rb").read()).decode()
        return f"data:image/png;base64,{b64}"
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
        gold = ch.isdigit() or ch in "◎◈,."
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


def _tally_html(tally: list[dict]) -> str:
    """One column per haul, side by side and centered: the amount shouts
    in the big font ([icon] 8 XP · [icon] 36 GOLD, each in its own
    colour), the marks heap under their own amount. Past the cap the
    heap stays home — the big numeral already carries the size."""
    cols = []
    for item in tally:
        kind = str(item.get("kind", ""))
        n = int(item.get("n", 0) or 0)
        if n <= 0 or kind not in _TALLY_MARK:
            continue
        key, tint = _TALLY_MARK[kind]
        label = f"+{n:,} {_TALLY_WORD[kind]}"
        head = (f'<div class="thead" style="color:{tint}">'
                f"{_eglyph(key)}"
                f"{_big_html(f'{n:,} {_TALLY_WORD[kind]}', tint)}</div>")
        heap = ""
        if n < TALLY_CAP:
            heap = (f'<span class="tmarks" style="color:{tint}" '
                    f'aria-hidden="true">' + _eglyph(key) * n + "</span>")
        note = str(item.get("note", ""))
        note_html = f'<div class="tnote">{_e(note)}</div>' if note else ""
        cols.append(f'<div class="thaul" title="{_e(label)}">'
                    f'<span class="tsr">{_e(label)}</span>'
                    f"{head}{heap}{note_html}</div>")
    if not cols:
        return ""
    return f'<div class="tallies">{"".join(cols)}</div>'


# ── 027: the notice board ───────────────────────────────────────────────
# A count with no sentence around it is a riddle. Every waiting thing gets
# a row at the TOP of the card: the verb, the room, the number, the worth —
# and the row is the shortcut. Blue is the notification ink everywhere in
# this game now; it never means a stat.
_NOTICE_WORD = {"collect": "COLLECT", "plan": "PLAN", "levelup": "LEVEL-UP"}


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
                 f'brother of the {_e(fac)} faction</span>')
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
_TIP_SPD = ("SPD — your speed: class base plus footwear. Decides dodges, "
            "chases and getaways. Every point fills a bolt.")


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
            b64 = base64.b64encode(open(path, "rb").read()).decode()
            return f"data:image/png;base64,{b64}", w, h
    return None


def _portrait_data_url(slug: str) -> str | None:
    art = _portrait_art(slug)
    return art[0] if art else None


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
        art = _banner_data_url(slug) if slug else None
        sig = (f'<img class="facsig" src="{art[0]}" alt="">' if art
               else "")
        n = int(getattr(m, "faction_members", 0) or 0)
        on = int(getattr(m, "faction_online", 0) or 0)
        meta = ""
        if n:
            meta = (f'<span class="facsub"><span>{n} climber'
                    f"{'s' if n != 1 else ''}</span>"
                    f'<span>{on} online now</span></span>')
        return (f'<div class="facblk later" data-fac="{_e(name)}">'
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


def _enemy_head_html(en: dict, tip: str = "") -> str:
    """009: the headline owns the name; the plate keeps only the range
    word and the [i] dossier, then the live modifiers, dim. 041: no
    `later` class — the sheet must read the moment the scene lands,
    not after the typewriter finishes."""
    rng = en.get("range", "")
    rword = {"at_range": "◇ at range",
             "close": "◇ close quarters"}.get(rng, "")
    rhtml = f'<span class="erng">{rword}</span>' if rword else ""
    info = (f'<span class="info" tabindex="0" role="note" '
            f'data-tip="{_e(tip)}">i</span>' if tip else "")
    plate = (f'<div class="eplate">{rhtml}{info}</div>'
             if rhtml or info else "")
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
                         or art_slug in economy.APOTHECARY
                         or art_slug == "arrow_pack"):
            slug = art_slug
        else:
            return ""
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


def _gear_card_preview(oid: str, hint: str) -> str:
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
    g = economy.FORGE.get(slug)
    relic = economy.RELICS.get(slug) if g is None else None
    # 062: the Medlab shelf previews too
    ware = (economy.APOTHECARY.get(slug)
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


def _slot_cell(it: dict) -> str:
    """One pack slot — a square button holding the icon, the ×count and
    the wear bar; the name lives in the tip and the action popup."""
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
    acts = it.get("acts") or []
    act_attr = (f" data-acts=\"{_e(_json.dumps(acts))}\""
                if acts else "")
    why_attr = (f' data-why="{_e(str(it.get("why")))}"'
                if it.get("why") else "")
    return (
        f'<button type="button" class="slot item act'
        f'{" eq" if equipped else ""}" '
        f'data-tip="{_e(tip)}"{tiph_attr} data-slug="{_e(slug)}" '
        f'data-name="{_e(name)}"'
        f"{act_attr}{why_attr}>"
        f'<span class="picon{picon_cls}" style="background-color:{tint};'
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
    side: list[dict] = []
    rest: list[dict] = []
    for it in scene.inventory:
        kind = it.get("kind", "")
        if it.get("equipped") and kind in ("weapon", "shield") \
                and kind not in hand:
            hand[kind] = it
        elif kind == "weapon" and it.get("held"):
            # 049.2: side-arms and bought-but-empty slots are HAND
            # cells, not pack clutter — one square per carry slot the
            # player owns, so a bought slot visibly exists.
            side.append(it)
        else:
            rest.append(it)
    hrow = []
    it = hand.get("weapon")
    cell = (_slot_cell(it) if it else
            '<span class="slot empty" data-tip="no weapon in hand '
            '— the Forge sells steel"></span>')
    hrow.append(f'<span class="hcell"><span class="hlab">in hand'
                f"</span>{cell}</span>")
    for it in side:
        if it.get("empty_slot"):
            cell = ('<span class="slot empty" data-tip="an open weapon '
                    'slot — the Forge sells steel"></span>')
            lab = "open slot"
        else:
            cell = _slot_cell(it)
            lab = "held"
        hrow.append(f'<span class="hcell"><span class="hlab">{lab}'
                    f"</span>{cell}</span>")
    it = hand.get("shield")
    cell = (_slot_cell(it) if it else
            '<span class="slot empty" data-tip="no shield '
            '— the Forge sells steel"></span>')
    hrow.append(f'<span class="hcell"><span class="hlab">shield'
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
    /* data-tiph is trusted server-authored HTML (the colored ATK /
       DURABILITY line); plain tips stay textContent */
    var h = el.getAttribute('data-tiph');
    if (h) box.innerHTML = h;
    else box.textContent = el.getAttribute('data-tip') || '';
    if (!box.textContent) return hide();
    box.style.display = 'block';
    var r = el.getBoundingClientRect();
    box.style.maxWidth = Math.min(380, innerWidth - 16) + 'px';
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
    k3 = getattr(scene, "kill3d", None)
    if fx or split or banner:
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
    parts.append(f'<div class="headline type" style="color:{hl_col}">'
                 f"{_ep(scene.headline)}</div>")
    if scene.enemy:
        # 009: the plate rides under the name — the foe's meter in the
        # player's grammar; the [i] carries the dossier as a tip, the
        # <details> fold stays below as the full sheet.
        dossier = _dossier_html(scene.enemy)
        parts.append(_enemy_head_html(scene.enemy, _dossier_tip(dossier)))
        parts.append(dossier)
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
    in_callout = False
    has_tally = bool(getattr(scene, "tally", None))
    for line in scene.body_lines:
        if has_tally and _TALLY_SAID.match(line):
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
        # 052: an option the gallery already shows as a picture tile
        # never repeats as a row — the card IS the button. Numbering
        # stays on scene.options order so typed numbers keep working.
        gal_opts = {str(g.get("opt", "")) for g in
                    (getattr(scene, "gallery", None) or [])}
        rows, cards = [], []
        for i, o in enumerate(scene.options, 1):
            if o.id in gal_opts:
                continue
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
                        else _gear_card_preview(o.id, o.hint or ""))
                wflag = ' data-wprev="1"' if prev else ""
                card = (f'<button type="button" class="opt gcard{opt_cls}" '
                        f'data-opt="{_e(o.id)}"{wflag}>'
                        f'<span class="key{key_cls}">{i}</span>{gicon}'
                        f'<span class="lbl">{_ep(o.label)}</span>{badge}'
                        f"{stack}</button>")
                cards.append(f'<div class="gcell">{card}{info}{prev}</div>')
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

    if scene.meters:
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
    if getattr(scene, "enemy", None):
        fight = "warden" if scene.event_kind == "boss" else "wilds"
        dt += f' data-fight="{fight}"'
        # the foe's slug — fight3d warms only THIS creature's model
        foe = str(scene.enemy.get("id", "") or "")
        if foe:
            dt += f' data-foe3d="{_e(foe)}"'
    # the climber's rig — race:line — so fight3d warms one rig, not fifteen
    m = scene.meters
    if m and getattr(m, "race", "") and getattr(m, "line", ""):
        dt += f' data-rig3d="{_e(m.race)}:{_e(m.line)}"'
    # PLAN3: the live 3D finisher's spec — the creature, the killing
    # blow's race/line, and the SAME tint the creature's banner wears,
    # so the canvas inks itself like the card. Only the website's
    # fight3d layer reads it; everything else leaves the attr alone.
    k3 = getattr(scene, "kill3d", None)
    if k3 and k3.get("id"):
        k3 = dict(k3)
        k3["tint"] = _banner_tint(k3["id"], k3.get("specimen", ""))
        dt += f' data-kill3d="{_e(_json.dumps(k3))}"'
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
.eplate .info{{margin-left:auto;}}
.emod{{color:{DIM};}}
.dx{{margin:4px 0 0;}}
.dx summary{{list-style:none;display:inline-flex;color:{DIM};
 cursor:pointer;user-select:none;padding:0;background:none;border:0;}}
.dx summary::-webkit-details-marker{{display:none;}}
.dx summary::before{{content:"[";}}
.dx summary::after{{content:"] dossier";}}
.dx summary:hover,.dx[open] summary{{color:{AETHER};}}
.dossier{{border:1px solid {AETHER};background:{INK};
 padding:10px 1.5ch;margin:8px 0 2px;}}
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
.thead>.eg{{width:30px;height:30px;vertical-align:0;flex:none;}}
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
.nb,.badge{{flex:none;display:inline-block;min-width:2ch;padding:0 .5ch;
 background:{AETHER};color:{INK};text-align:center;
 font-variant-numeric:tabular-nums;}}
.badge{{margin-left:1ch;}}
.opt:hover .badge{{background:{TEXT};}}
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
 background:{INK};color:{GOLD};}}
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
.profile{{display:flex;gap:2ch;align-items:stretch;margin-top:8px;}}
.profile .portrait{{flex:none;align-self:stretch;height:auto;width:auto;
 min-height:200px;image-rendering:pixelated;}}
.profile .pcol{{flex:1;min-width:0;}}
.profile .rail{{margin-top:0;padding-top:0;border-top:0;}}
.profile .inv{{border-top:0;padding-top:0;margin-top:8px;}}
/* ── 059/062: the faction strip at the foot of the card — no box, the
   card's own dotted rule above it; banner + name are the door ── */
.facblk{{display:flex;align-items:center;gap:1.5ch;margin-top:10px;
 border-top:1px dashed {BORDER};padding:8px 0 0;color:{DIM};
 letter-spacing:.06em;text-transform:uppercase;min-width:0;}}
.facblk .facdoor{{display:flex;align-items:center;gap:1ch;flex:none;
 max-width:100%;min-width:0;background:none;border:0;padding:0;margin:0;
 font:inherit;letter-spacing:inherit;text-transform:inherit;color:{TEXT};
 cursor:pointer;text-align:left;}}
.facblk .facsig{{flex:none;height:60px;width:auto;
 image-rendering:pixelated;margin:-4px 0;
 transition:filter .12s,transform .12s;}}
.facblk .facname{{color:{TEXT};letter-spacing:.14em;
 border-bottom:1px solid transparent;transition:color .12s,
 border-color .12s;white-space:nowrap;overflow:hidden;
 text-overflow:ellipsis;}}
.facblk .facdoor:hover .facname,.facblk .facdoor:focus-visible .facname{{
 color:{GOLD};border-bottom-color:{GOLD};}}
.facblk .facdoor:hover .facsig,.facblk .facdoor:focus-visible .facsig{{
 filter:brightness(1.35) drop-shadow(0 0 4px {GOLD});
 transform:scale(1.06);}}
.facblk .facdoor:focus-visible{{outline:0;}}
.facblk .facsub{{display:flex;flex-direction:column;align-items:flex-start;
 gap:1px;color:{DIM};text-transform:none;letter-spacing:.06em;
 line-height:1.35;}}
.facblk .facsub .dim{{color:{DIM};}}
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
.hlab{{color:{FAINT};letter-spacing:.08em;}}
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
 .profile{{gap:1.5ch;align-items:flex-start;}}
 .profile .portrait{{align-self:flex-start;min-height:0;height:132px;}}
 .ident{{flex-wrap:wrap;row-gap:2px;}}
 .ident .idr{{margin-left:auto;}}
 .facblk{{flex-wrap:wrap;row-gap:4px;}}
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
