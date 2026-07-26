"""The 009 game pane — the interface, out of the chat.

One self-contained HTML app served at /api/p/plugin-linear-ascent/ui/ and
rendered by Luna's shell as a sidebar-section iframe. Reuses the exact card
grammar (render.SCENE_CSS + render_scene_fragment served by /pane/scene and
/act) so the pane is pixel-identical to the old chat cards. Clicks call
/act directly with the host token — no card bridge, no model in the path.

Auth: the shell posts {type:'luna-auth', token} into the iframe on load and
whenever the session changes; the pane also answers 401s by asking again
(luna-request-auth), matching PluginIframe's contract in Shell.tsx.

Tabs: GAME is live; SCORE and COMMUNITY are plan 010.
"""

from __future__ import annotations

from .render import AETHER, BORDER, DIM, FAINT, INK, PANEL, SCENE_CSS, TEXT, VIOLET

_API = "/api/p/plugin-linear-ascent"


def render_pane() -> str:
    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root {{ color-scheme: dark; }}
html,body{{margin:0;padding:0;background:{INK};min-height:100%;}}
body{{color:{TEXT};
 font:14px/1.6 ui-monospace,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;
 font-variant-numeric:tabular-nums;}}
.wrap{{max-width:760px;margin:0 auto;padding:14px 12px 40px;}}
.tabs{{display:flex;gap:2px;margin-bottom:12px;border:1px solid {BORDER};
 background:{PANEL};}}
.tab{{flex:1;background:none;border:0;border-right:1px solid {BORDER};
 color:{DIM};font:inherit;letter-spacing:.14em;text-transform:uppercase;
 padding:9px 0;cursor:pointer;border-radius:0;}}
.tab:last-child{{border-right:0;}}
.tab:hover{{color:{TEXT};}}
.tab.active{{background:{TEXT};color:{INK};font-weight:700;}}
.pane{{display:none;}}
.pane.active{{display:block;}}
.dim{{color:{DIM};}} .faint{{color:{FAINT};}}
.placeholder{{background:{PANEL};border:1px solid {BORDER};padding:18px 2ch;
 color:{DIM};}}
.placeholder .eyebrow{{color:{FAINT};text-transform:uppercase;
 letter-spacing:.08em;margin-bottom:6px;}}
.err{{border:1px solid {BORDER};border-left:3px solid #f4645f;
 background:{PANEL};color:{DIM};padding:12px 2ch;margin-top:10px;}}
a{{color:{AETHER};}}
{SCENE_CSS}
.opt.busy{{border-color:{VIOLET};opacity:.7;}}
</style></head><body>
<div class="wrap">
  <div class="tabs" role="tablist">
    <button class="tab active" data-tab="game" role="tab">Game</button>
    <button class="tab" data-tab="score" role="tab">Score</button>
    <button class="tab" data-tab="community" role="tab">Community</button>
  </div>
  <div id="game" class="pane active"><div class="placeholder">
    <div class="eyebrow">the ascent</div>waking the lift…</div></div>
  <div id="score" class="pane"><div class="placeholder">
    <div class="eyebrow">muster roll</div>
    the scorekeeper is still sharpening his quill.</div></div>
  <div id="community" class="pane"><div class="placeholder">
    <div class="eyebrow">the guildhall</div>
    faction charters arrive with the next caravan.</div></div>
</div>
<script>
(() => {{
const API = {_API!r};
let token = new URLSearchParams(location.search).get('token') || '';
let sceneId = '';
let loading = false;

/* ── auth handshake (PluginIframe contract) ─────────────────────────── */
window.addEventListener('message', (e) => {{
  const d = e.data || {{}};
  if (d.type === 'luna-auth' && d.token) {{
    const fresh = d.token !== token;
    token = d.token;
    if (fresh && !sceneId) loadScene();
  }}
}});
try {{ parent.postMessage({{type: 'luna-ui-ready'}}, '*'); }} catch (e) {{}}

function hdrs() {{
  return {{'Content-Type': 'application/json',
           ...(token ? {{'Authorization': 'Bearer ' + token}} : {{}})}};
}}
async function call(path, body) {{
  const r = await fetch(API + path, body === undefined
    ? {{headers: hdrs()}}
    : {{method: 'POST', headers: hdrs(), body: JSON.stringify(body)}});
  if (r.status === 401) {{
    try {{ parent.postMessage({{type: 'luna-request-auth'}}, '*'); }} catch (e) {{}}
    throw new Error('auth');
  }}
  if (!r.ok) {{
    let detail = 'the lift jams';
    try {{ const d = await r.json(); if (d.detail) detail = String(d.detail); }}
    catch (e) {{}}
    throw new Error(detail);
  }}
  return r.json();
}}

/* ── tabs ───────────────────────────────────────────────────────────── */
const tabs = [...document.querySelectorAll('.tab')];
tabs.forEach(t => t.addEventListener('click', () => {{
  tabs.forEach(x => x.classList.toggle('active', x === t));
  document.querySelectorAll('.pane').forEach(p =>
    p.classList.toggle('active', p.id === t.dataset.tab));
  if (t.dataset.tab === 'game') loadScene(true);
}}));

/* ── scene grammar FX: the mock's typewriter, scoped to the pane ────── */
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function runFX(root) {{
  const typed = [...root.querySelectorAll('.type')];
  const later = [...root.querySelectorAll('.later')];
  if (reduced) return;
  typed.forEach(e => e.classList.add('pending'));
  later.forEach(e => e.classList.add('waiting'));
  const textNodes = el => {{
    const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    const a = []; let n; while ((n = w.nextNode())) a.push(n); return a; }};
  for (const el of typed) {{
    if (!el.isConnected) return;           // scene swapped mid-reveal
    const ns = textNodes(el); const full = ns.map(n => n.nodeValue);
    ns.forEach(n => {{ n.nodeValue = ''; }});
    el.classList.remove('pending');
    const cur = document.createElement('span');
    cur.className = 'cursor'; cur.setAttribute('aria-hidden', 'true');
    for (let i = 0; i < ns.length; i++) {{
      const n = ns[i], t = full[i];
      n.parentNode.insertBefore(cur, n.nextSibling);
      for (let c = 1; c <= t.length; c++) {{
        n.nodeValue = t.slice(0, c); await sleep(7);
        if (!el.isConnected) {{ cur.remove(); return; }}
      }}
    }}
    cur.remove();
  }}
  let d = 0;
  for (const el of later) {{
    setTimeout(() => el.classList.add('shown'), d); d += 90;
  }}
}}

/* ── the game loop: swap fragments in place, act directly ───────────── */
const game = document.getElementById('game');
function showScene(d) {{
  sceneId = d.scene_id || '';
  game.innerHTML = d.fragment;
  wireOptions();
  runFX(game);
}}
function showErr(msg) {{
  const e = document.createElement('div');
  e.className = 'err'; e.textContent = msg;
  game.appendChild(e);
  setTimeout(() => e.remove(), 6000);
}}
function wireOptions() {{
  const btns = [...game.querySelectorAll('button.opt')];
  const hint = game.querySelector('.reply');
  btns.forEach(b => b.addEventListener('click', async () => {{
    if (loading) return; loading = true;
    btns.forEach(x => {{ x.disabled = true;
      x.classList.add(x === b ? 'busy' : 'stale'); }});
    if (hint) hint.textContent = '…';
    try {{
      showScene(await call('/act',
        {{option: b.dataset.opt, scene_id: sceneId, mode: 'pane'}}));
    }} catch (err) {{
      btns.forEach(x => {{ x.disabled = false;
        x.classList.remove('busy', 'stale'); }});
      if (hint) hint.textContent = 'click an option — or reply with a number';
      if (err.message !== 'auth') showErr(err.message);
    }} finally {{ loading = false; }}
  }}));
}}
async function loadScene(force) {{
  if (loading || (!token && !force)) return;
  loading = true;
  try {{ showScene(await call('/pane/scene', {{}})); }}
  catch (err) {{ if (err.message !== 'auth') showErr(err.message); }}
  finally {{ loading = false; }}
}}

/* ── freshness: chat-driven acts and world events reach the pane ────── */
async function peek() {{
  if (!token || document.hidden || loading) return;
  try {{
    const d = await call('/pane/peek');
    if (d.scene_id && sceneId && d.scene_id !== sceneId) loadScene(true);
  }} catch (e) {{}}
}}
setInterval(peek, 15000);
document.addEventListener('visibilitychange', () => {{
  if (!document.hidden) peek();
}});

if (token) loadScene();
}})();
</script></body></html>"""
