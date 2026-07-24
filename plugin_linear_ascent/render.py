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
import os
from functools import lru_cache

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

_STRIPE = {"loot": GOLD, "present": GOLD, "death": RED,
           "letter": AETHER, "boss": VIOLET}
_HEADLINE = {"death": RED, "loot": GOLD, "present": GOLD}
_BANNER_TINT = {"death": RED, "present": GOLD, "gnarl": VIOLET}

_ART = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "content", "art", "banners")


@lru_cache(maxsize=None)
def _banner_data_url(slug: str) -> tuple[str, int, int] | None:
    """(data_url, width, height) for the slug's art, or None."""
    for size in ("320x112", "160x56", "320x200"):
        path = os.path.join(_ART, f"{slug}_{size}.png")
        if os.path.exists(path):
            b64 = base64.b64encode(open(path, "rb").read()).decode()
            w, h = (int(n) for n in size.split("x"))
            return f"data:image/png;base64,{b64}", w, h
    return None


def _e(s: str) -> str:
    return html.escape(s, quote=True)


def _blocks(cur: int, cap: int, cells: int = 10) -> str:
    cur = max(0, min(cur, cap))
    filled = round(cells * cur / cap) if cap else 0
    return (f"{'█' * filled}"
            f'<span class="off">{"░" * (cells - filled)}</span>')


def _meters_html(m: Meters) -> str:
    low = " low" if m.hp * 10 <= m.hp_max * 3 else ""
    return (
        f'<div class="rail later">'
        f'<span class="meter hp{low}"><span>HP {m.hp}/{m.hp_max}</span>'
        f'<span class="blocks" aria-hidden="true">'
        f"{_blocks(m.hp, m.hp_max)}</span></span>"
        f'<span class="meter en"><span>⚡ {m.energy}/{m.energy_max}</span>'
        f'<span class="blocks" aria-hidden="true">'
        f"{_blocks(m.energy, m.energy_max)}</span></span>"
        f'<span class="meter ae"><span>✦ {m.mana}/{m.mana_max}</span>'
        f'<span class="blocks" aria-hidden="true">'
        f"{_blocks(m.mana, m.mana_max)}</span></span>"
        f'<span class="gold">◈ {m.gold:,}</span>'
        f"</div>")


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

_SCRIPT = """<script>(()=>{
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
/* card actions — clicks act through the host bridge, no model in the way */
(function () {
  var btns = Array.prototype.slice.call(
    document.querySelectorAll('button.opt'));
  if (!btns.length) return;
  var acted = false;
  var hint = document.querySelector('.reply');
  function setHint(t) { if (hint) hint.textContent = t; }
  function lock(chosen) { btns.forEach(function (b) {
    b.disabled = true; b.classList.add(b === chosen ? 'chosen' : 'stale');
  }); }
  function unlock() { acted = false; btns.forEach(function (b) {
    b.disabled = false; b.classList.remove('chosen', 'stale');
  }); }
  btns.forEach(function (b) { b.addEventListener('click', function () {
    if (acted) return; acted = true; lock(b); setHint('\\u2026');
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
      body: {option: b.dataset.opt,
             scene_id: document.body.dataset.scene || ''}}, '*');
  }); });
})();</script>""".replace("__ACT__", _ACT_PATH)


def render_scene(scene: Scene) -> str:
    parts: list[str] = []

    banner = _banner_data_url(scene.banner) if scene.banner else None
    if banner:
        url, w, h = banner
        tint = _BANNER_TINT.get(scene.banner, DIM)
        parts.append(
            f'<div class="banner" style="background-color:{tint};'
            f"aspect-ratio:{w}/{h};"
            f"-webkit-mask-image:url('{url}');"
            f"mask-image:url('{url}');\"></div>")

    parts.append(f'<div class="eyebrow type">{_e(scene.eyebrow)}</div>')
    hl_col = _HEADLINE.get(scene.event_kind, TEXT)
    parts.append(f'<div class="headline type" style="color:{hl_col}">'
                 f"{_e(scene.headline)}</div>")
    if scene.support:
        parts.append(f'<div class="support type">{_e(scene.support)}</div>')
    if scene.shard_note:
        parts.append(f'<div class="shard type"><span class="glyph">◆</span>'
                     f"<span>{_e(scene.shard_note)}</span></div>")
    for line in scene.body_lines:
        if line.startswith("+"):
            parts.append(f'<div class="body type" style="color:{OK}">'
                         f"{_e(line)}</div>")
        elif line.startswith("−") or line.startswith("-"):
            parts.append(f'<div class="body type" style="color:{RED}">'
                         f"{_e(line)}</div>")
        else:
            parts.append(f'<div class="body type">{_e(line)}</div>')

    if scene.options:
        rows = []
        for i, o in enumerate(scene.options, 1):
            key_cls = " aether" if o.aether else ""
            hint = (f'<span class="hint">{_e(o.hint)}</span>'
                    if o.hint else "")
            rows.append(
                f'<button type="button" class="opt" data-opt="{_e(o.id)}">'
                f'<span class="key{key_cls}">{i}</span>'
                f'<span class="lbl">{_e(o.label)}</span>{hint}</button>')
        parts.append(f'<div class="options later">{"".join(rows)}'
                     f'<div class="reply">click an option — or reply '
                     f"with a number</div></div>")

    if scene.meters:
        parts.append(_meters_html(scene.meters))

    stripe = _STRIPE.get(scene.event_kind)
    stripe_css = (f"border-left:3px solid {stripe};" if stripe else "")

    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;padding:0;background:{INK};}}
.card{{background:{PANEL};border:1px solid {BORDER};{stripe_css}
 border-radius:0;margin:8px;padding:12px 2ch 10px;color:{TEXT};
 font:14px/1.6 ui-monospace,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;
 font-variant-numeric:tabular-nums;overflow:hidden;}}
.banner{{display:block;width:calc(100% + 4ch);margin:-12px -2ch 10px;
 mask-size:100% 100%;-webkit-mask-size:100% 100%;mask-repeat:no-repeat;
 -webkit-mask-repeat:no-repeat;image-rendering:pixelated;
 border-bottom:1px solid {BORDER};}}
.eyebrow{{color:{FAINT};text-transform:uppercase;letter-spacing:.08em;}}
.headline{{font-weight:700;margin:4px 0 0;text-wrap:balance;}}
.support{{color:{DIM};}}
.shard{{display:flex;gap:1ch;border-left:2px solid {AETHER};
 background:color-mix(in srgb,{AETHER} 5%,{PANEL});
 padding:8px 1.5ch;margin-top:8px;color:{DIM};}}
.shard .glyph{{color:{AETHER};flex:none;}}
.body{{margin:6px 0 0;white-space:pre-wrap;}}
.options{{margin:10px 0 0;padding:10px 0 0;border-top:1px dashed {BORDER};
 display:flex;flex-direction:column;gap:5px;}}
.opt{{display:flex;align-items:center;gap:1ch;width:100%;
 background:{PANEL2};border:1px solid {BORDER};padding:6px 1.5ch;
 font:inherit;color:inherit;text-align:left;border-radius:0;
 cursor:pointer;}}
.opt:hover:not(:disabled){{border-color:{VIOLET};}}
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
.reply{{color:{FAINT};letter-spacing:.08em;margin-top:5px;}}
.reply::before{{content:"· ";}}
.rail{{display:flex;flex-wrap:wrap;align-items:center;gap:2ch;
 margin-top:10px;padding-top:8px;border-top:1px dashed {BORDER};
 color:{DIM};}}
.meter{{display:flex;align-items:center;gap:1ch;}}
.meter .blocks{{letter-spacing:.5px;}}
.meter .blocks .off{{color:{BORDER};}}
.meter.hp .blocks{{color:{OK};}}
.meter.hp.low .blocks{{color:{RED};}}
.meter.en .blocks{{color:{AETHER};}}
.meter.ae .blocks{{color:{VIOLET_SOFT};}}
.rail .gold{{color:{GOLD};margin-left:auto;}}
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
</style></head><body data-scene="{_e(scene.scene_id)}"><div class="card">{''.join(parts)}</div>{_SCRIPT}</body></html>"""
