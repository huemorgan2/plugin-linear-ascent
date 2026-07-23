"""Scene → chat card HTML (embed_iframe).

One renderer for every scene — the card grammar from
design/chat_components.md. Text fallback comes from Scene.to_text();
this file is pure presentation. No webfonts, no network: banners are
white-ink 1-bit PNGs inlined as data URLs and tinted via CSS mask.
"""

from __future__ import annotations

import base64
import html
import os
from functools import lru_cache

from .engine.scene import Meters, Scene

# ── tokens ───────────────────────────────────────────────────────────────
INK = "#0b0e14"
PANEL = "#11151f"
BORDER = "#232a36"
DIM = "#8b93a7"
TEXT = "#e6e9f2"
GOLD = "#f5a524"
AETHER = "#5eaefc"
VIOLET = "#8b5cf6"
RED = "#f4645f"
OK = "#4ade80"

_STRIPE = {"loot": GOLD, "present": GOLD, "death": RED,
           "letter": AETHER, "boss": VIOLET}
_BANNER_TINT = {"death": RED, "present": GOLD, "gnarl": VIOLET}

_ART = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "content", "art", "banners")


@lru_cache(maxsize=None)
def _banner_data_url(slug: str) -> str | None:
    for fname in (f"{slug}_320x112.png", f"{slug}_160x56.png"):
        path = os.path.join(_ART, fname)
        if os.path.exists(path):
            b64 = base64.b64encode(open(path, "rb").read()).decode()
            return f"data:image/png;base64,{b64}"
    return None


def _e(s: str) -> str:
    return html.escape(s, quote=True)


def _bar(cur: int, cap: int, cells: int = 10) -> str:
    cur = max(0, min(cur, cap))
    filled = round(cells * cur / cap) if cap else 0
    return "█" * filled + "░" * (cells - filled)


def _meters_html(m: Meters) -> str:
    hp_col = RED if m.hp * 3 <= m.hp_max else TEXT
    return (
        f'<div class="rail">'
        f'<span style="color:{hp_col}">HP {_bar(m.hp, m.hp_max)} '
        f'{m.hp}/{m.hp_max}</span>'
        f'<span>⚡ {m.energy}/{m.energy_max}</span>'
        f'<span style="color:{AETHER}">✦ {m.mana}/{m.mana_max}</span>'
        f'<span style="color:{GOLD}">◈ {m.gold:,}</span>'
        f"</div>")


def render_scene(scene: Scene) -> str:
    parts: list[str] = []

    banner = _banner_data_url(scene.banner) if scene.banner else None
    if banner:
        tint = _BANNER_TINT.get(scene.banner, DIM)
        parts.append(
            f'<div class="banner" style="background-color:{tint};'
            f"-webkit-mask-image:url('{banner}');"
            f"mask-image:url('{banner}');\"></div>")

    parts.append(f'<div class="eyebrow">{_e(scene.eyebrow)}</div>')
    parts.append(f'<div class="headline">{_e(scene.headline)}</div>')
    if scene.support:
        parts.append(f'<div class="support">{_e(scene.support)}</div>')
    if scene.shard_note:
        parts.append(f'<div class="shard">◆ {_e(scene.shard_note)}</div>')
    for line in scene.body_lines:
        cls = "body"
        if line.startswith("+"):
            cls, col = "body", OK
            parts.append(f'<div class="{cls}" style="color:{col}">'
                         f"{_e(line)}</div>")
            continue
        if line.startswith("−") or line.startswith("-"):
            parts.append(f'<div class="body" style="color:{RED}">'
                         f"{_e(line)}</div>")
            continue
        parts.append(f'<div class="{cls}">{_e(line)}</div>')

    if scene.options:
        rows = []
        for i, o in enumerate(scene.options, 1):
            key_col = AETHER if o.aether else GOLD
            hint = (f'<span class="hint">{_e(o.hint)}</span>'
                    if o.hint else "")
            rows.append(
                f'<div class="opt"><span class="key" '
                f'style="color:{key_col};border-color:{key_col}">'
                f"{i}</span><span class=\"lbl\">{_e(o.label)}</span>{hint}</div>")
        parts.append('<div class="sep"></div>' + "".join(rows))
        parts.append(f'<div class="reply">reply with a number to act</div>')

    if scene.meters:
        parts.append(_meters_html(scene.meters))

    stripe = _STRIPE.get(scene.event_kind)
    stripe_css = (f"border-left:3px solid {stripe};" if stripe else "")

    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;padding:0;background:{INK};}}
.card{{background:{PANEL};border:1px solid {BORDER};{stripe_css}
 margin:8px;padding:12px 14px;color:{TEXT};
 font:14px/1.45 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
 max-width:62ch;}}
.banner{{width:320px;max-width:100%;aspect-ratio:320/112;
 mask-size:contain;-webkit-mask-size:contain;mask-repeat:no-repeat;
 -webkit-mask-repeat:no-repeat;image-rendering:pixelated;
 margin-bottom:10px;}}
.eyebrow{{color:{DIM};font-size:11px;letter-spacing:.14em;}}
.headline{{color:{TEXT};font-weight:700;margin:2px 0 4px;}}
.support{{color:{DIM};margin-bottom:6px;}}
.shard{{color:{AETHER};border-left:2px solid {AETHER};
 padding-left:8px;margin:8px 0;}}
.body{{margin:2px 0;white-space:pre-wrap;}}
.sep{{border-top:1px solid {BORDER};margin:10px 0 6px;}}
.opt{{display:flex;gap:1ch;align-items:baseline;margin:3px 0;}}
.key{{border:1px solid;padding:0 .6ch;font-size:12px;}}
.lbl{{flex:0 1 auto;}}
.hint{{color:{DIM};margin-left:auto;font-size:12px;}}
.reply{{color:{DIM};font-size:11px;margin-top:6px;letter-spacing:.08em;}}
.rail{{display:flex;gap:2ch;flex-wrap:wrap;border-top:1px solid {BORDER};
 margin-top:10px;padding-top:8px;color:{DIM};font-size:12px;}}
</style></head><body><div class="card">{''.join(parts)}</div></body></html>"""
