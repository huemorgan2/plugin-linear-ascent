"""The game pane — the interface, out of the chat (plans 009 + 010).

One self-contained HTML app served at /api/p/plugin-linear-ascent/ui/ and
rendered by Luna's shell as a sidebar-section iframe. GAME reuses the exact
card grammar (render.SCENE_CSS + render_scene_fragment served by
/pane/scene and /act) so the pane is pixel-identical to the old chat cards;
clicks call /act directly with the host token — no card bridge, no model in
the path. SCORE is the full-world leaderboard; COMMUNITY is the faction
NEWS BOARD (read-only): weekly winners, the wins ranking, the biggest /
richest / highest-levelled banners. Joining, founding and managing a
faction happens IN-GAME at the Guildhall in Roothollow.

Auth: the shell posts {type:'luna-auth', token} into the iframe on load and
whenever the session changes; the pane also answers 401s by asking again
(luna-request-auth), matching PluginIframe's contract in Shell.tsx.
"""

from __future__ import annotations

from .render import (AETHER, BORDER, DIM, FAINT, INK, PANEL, PANEL2,
                     SCENE_CSS, TEXT, VIOLET, VIOLET_SOFT)

_API = "/api/p/plugin-linear-ascent"

_CSS = f"""
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
/* ── 010: score & community ── */
.panel{{background:{PANEL};border:1px solid {BORDER};padding:12px 2ch 10px;
 margin-bottom:12px;}}
.panel .eyebrow{{margin-bottom:8px;}}
.trow{{display:grid;grid-template-columns:3ch 1fr 5ch 5ch 9ch 9ch 12ch;
 gap:1ch;padding:3px 0;border-bottom:1px dashed {BORDER};align-items:baseline;
 white-space:nowrap;overflow:hidden;}}
.trow.head{{color:{FAINT};text-transform:uppercase;letter-spacing:.08em;}}
.trow .r{{text-align:right;}}
.trow .gold{{color:#f5a524;text-align:right;}}
.trow.me{{color:{AETHER};}}
.fbanner{{width:160px;aspect-ratio:320/112;background-color:{DIM};
 mask-size:100% 100%;-webkit-mask-size:100% 100%;mask-repeat:no-repeat;
 -webkit-mask-repeat:no-repeat;image-rendering:pixelated;flex:none;}}
.fbanner.big{{width:100%;max-width:320px;background-color:{VIOLET_SOFT};}}
.frow{{display:flex;gap:2ch;align-items:center;padding:8px 0;
 border-bottom:1px dashed {BORDER};}}
.frow .meta{{flex:1;min-width:0;}}
.btn{{background:{PANEL2};border:1px solid {BORDER};color:{TEXT};
 font:inherit;padding:6px 1.5ch;cursor:pointer;border-radius:0;}}
.btn:hover:not(:disabled){{border-color:{VIOLET};}}
.btn:disabled{{opacity:.5;cursor:default;}}
.btn.danger:hover:not(:disabled){{border-color:#f4645f;color:#f4645f;}}
.bgrid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));
 gap:8px;margin:8px 0;}}
.bgrid .cell{{border:1px solid {BORDER};padding:6px;cursor:pointer;
 background:{PANEL2};}}
.bgrid .cell.sel{{border-color:{AETHER};}}
.bgrid .fbanner{{width:100%;}}
.bgrid .cap{{color:{FAINT};font-size:11px;margin-top:4px;
 text-align:center;overflow:hidden;text-overflow:ellipsis;}}
input.ti{{background:{INK};color:{TEXT};border:1px solid {BORDER};
 font:inherit;padding:6px 1ch;width:100%;box-sizing:border-box;}}
select.ti{{background:{INK};color:{TEXT};border:1px solid {BORDER};
 font:inherit;padding:6px 1ch;}}
.bar{{letter-spacing:.5px;color:{VIOLET_SOFT};}}
.bar .off{{color:{BORDER};}}
.kv{{display:flex;justify-content:space-between;gap:2ch;padding:2px 0;}}
.kv .k{{color:{FAINT};}}
.mrow{{display:grid;grid-template-columns:1fr 6ch 10ch auto;gap:1ch;
 padding:4px 0;border-bottom:1px dashed {BORDER};align-items:center;}}
.mrow .r{{text-align:right;}}
"""

# Plain string on purpose: real braces everywhere — no f-string doubling.
_JS = r"""
(() => {
const API = '__API__';
let token = new URLSearchParams(location.search).get('token') || '';
let sceneId = '';
let loading = false;

/* ── auth handshake (PluginIframe contract) ─────────────────────────── */
window.addEventListener('message', (e) => {
  const d = e.data || {};
  if (d.type === 'luna-auth' && d.token) {
    const fresh = d.token !== token;
    token = d.token;
    if (fresh && !sceneId) loadScene(true);
  }
});
try { parent.postMessage({type: 'luna-ui-ready'}, '*'); } catch (e) {}

function hdrs() {
  return {'Content-Type': 'application/json',
          ...(token ? {'Authorization': 'Bearer ' + token} : {})};
}
async function call(path, body) {
  const r = await fetch(API + path, body === undefined
    ? {headers: hdrs()}
    : {method: 'POST', headers: hdrs(), body: JSON.stringify(body)});
  if (r.status === 401) {
    try { parent.postMessage({type: 'luna-request-auth'}, '*'); } catch (e) {}
    throw new Error('auth');
  }
  if (!r.ok) {
    let detail = 'the lift jams';
    try { const d = await r.json(); if (d.detail) detail = String(d.detail); }
    catch (e) {}
    throw new Error(detail);
  }
  return r.json();
}
const esc = s => String(s ?? '').replace(/[&<>"']/g, c =>
  ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const num = n => Number(n || 0).toLocaleString('en-US');
const sig = (slug, cls) => {
  const u = API + '/art/factions/' + encodeURIComponent(slug) + '.png';
  return '<div class="fbanner ' + (cls || '') + '" style="mask-image:url(\''
    + u + '\');-webkit-mask-image:url(\'' + u + '\')"></div>';
};
const bar = (cur, cap, cells) => {
  cells = cells || 20;
  const f = cap > 0 ? Math.max(0, Math.min(cells,
    Math.round(cells * cur / cap))) : 0;
  return '<span class="bar">' + '█'.repeat(f)
    + '<span class="off">' + '░'.repeat(cells - f) + '</span></span>';
};
function paneFail(el, eyebrow, msg) {
  el.innerHTML = '<div class="placeholder"><div class="eyebrow">'
    + esc(eyebrow) + '</div>' + esc(msg) + '</div>';
}

/* ── tabs ───────────────────────────────────────────────────────────── */
const tabs = [...document.querySelectorAll('.tab')];
tabs.forEach(t => t.addEventListener('click', () => {
  tabs.forEach(x => x.classList.toggle('active', x === t));
  document.querySelectorAll('.pane').forEach(p =>
    p.classList.toggle('active', p.id === t.dataset.tab));
  if (t.dataset.tab === 'game') loadScene(true);
  if (t.dataset.tab === 'score') loadScore();
  if (t.dataset.tab === 'community') loadCommunity();
}));

/* ── scene grammar FX: the mock's typewriter, scoped to the pane ────── */
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function runFX(root) {
  const typed = [...root.querySelectorAll('.type')];
  const later = [...root.querySelectorAll('.later')];
  if (reduced) return;
  typed.forEach(e => e.classList.add('pending'));
  later.forEach(e => e.classList.add('waiting'));
  const textNodes = el => {
    const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    const a = []; let n; while ((n = w.nextNode())) a.push(n); return a; };
  for (const el of typed) {
    if (!el.isConnected) return;           // scene swapped mid-reveal
    const ns = textNodes(el); const full = ns.map(n => n.nodeValue);
    ns.forEach(n => { n.nodeValue = ''; });
    el.classList.remove('pending');
    const cur = document.createElement('span');
    cur.className = 'cursor'; cur.setAttribute('aria-hidden', 'true');
    for (let i = 0; i < ns.length; i++) {
      const n = ns[i], t = full[i];
      n.parentNode.insertBefore(cur, n.nextSibling);
      for (let c = 1; c <= t.length; c++) {
        n.nodeValue = t.slice(0, c); await sleep(7);
        if (!el.isConnected) { cur.remove(); return; }
      }
    }
    cur.remove();
  }
  let d = 0;
  for (const el of later) {
    setTimeout(() => el.classList.add('shown'), d); d += 90;
  }
}

/* ── the game loop: swap fragments in place, act directly ───────────── */
const game = document.getElementById('game');
function showScene(d) {
  sceneId = d.scene_id || '';
  game.innerHTML = d.fragment;
  wireOptions();
  runFX(game);
}
function showErr(msg) {
  const e = document.createElement('div');
  e.className = 'err'; e.textContent = msg;
  game.appendChild(e);
  setTimeout(() => e.remove(), 6000);
}
function wireOptions() {
  const btns = [...game.querySelectorAll('button.opt')];
  const hint = game.querySelector('.reply');
  btns.forEach(b => b.addEventListener('click', async () => {
    if (loading) return; loading = true;
    btns.forEach(x => { x.disabled = true;
      x.classList.add(x === b ? 'busy' : 'stale'); });
    if (hint) hint.textContent = '…';
    try {
      showScene(await call('/act',
        {option: b.dataset.opt, scene_id: sceneId, mode: 'pane'}));
    } catch (err) {
      btns.forEach(x => { x.disabled = false;
        x.classList.remove('busy', 'stale'); });
      if (hint) hint.textContent = 'click an option — or reply with a number';
      if (err.message !== 'auth') showErr(err.message);
    } finally { loading = false; }
  }));
}
async function loadScene(force) {
  if (loading || (!token && !force)) return;
  loading = true;
  try { showScene(await call('/pane/scene', {})); }
  catch (err) { if (err.message !== 'auth') showErr(err.message); }
  finally { loading = false; }
}

/* ── freshness: chat-driven acts and world events reach the pane ────── */
async function peek() {
  if (!token || document.hidden || loading) return;
  try {
    const d = await call('/pane/peek');
    if (d.scene_id && sceneId && d.scene_id !== sceneId) loadScene(true);
  } catch (e) {}
}
setInterval(peek, 15000);
document.addEventListener('visibilitychange', () => {
  if (!document.hidden) peek();
});

/* ── SCORE: the muster roll, whole world ────────────────────────────── */
const score = document.getElementById('score');
async function loadScore() {
  try {
    const d = await call('/pane/score');
    let h = '<div class="panel"><div class="eyebrow">muster roll · '
      + num(d.total) + ' climbers on the Ascent</div>'
      + '<div class="trow head"><span>#</span><span>name</span>'
      + '<span class="r">lvl</span><span class="r">floor</span>'
      + '<span class="r">carried</span><span class="r">banked</span>'
      + '<span>faction</span></div>';
    d.players.forEach((p, i) => {
      h += '<div class="trow' + (p.you ? ' me' : '') + '">'
        + '<span>' + (i + 1) + '</span>'
        + '<span>' + esc(p.name) + ' <span class="faint">'
        + esc(p.race) + ' ' + esc(p.clazz) + '</span></span>'
        + '<span class="r">' + p.level + '</span>'
        + '<span class="r">' + p.floor + '</span>'
        + '<span class="gold">◈ ' + num(p.gold) + '</span>'
        + '<span class="gold">◈ ' + num(p.bank) + '</span>'
        + '<span class="faint">' + (esc(p.faction) || '—') + '</span></div>';
    });
    score.innerHTML = h + '</div>';
  } catch (err) {
    if (err.message !== 'auth') paneFail(score, 'muster roll', err.message);
  }
}

/* ── COMMUNITY: the faction news board (read-only) ──────────────────── */
const community = document.getElementById('community');
async function loadCommunity() {
  try {
    const d = await call('/pane/community');
    community.innerHTML = renderBoard(d);
  } catch (err) {
    if (err.message !== 'auth')
      paneFail(community, 'the faction board', err.message);
  }
}

const KIND_LABEL = {hoard: 'HOARD — gold earned',
                    cull: 'CULL — kills made',
                    climb: 'CLIMB — experience won'};

function chipRow(name, banners, right) {
  const slug = banners[name] || '';
  return '<div class="frow">'
    + (slug ? sig(slug) : '<div class="fbanner"></div>')
    + '<div class="meta"><div>' + esc(name) + '</div></div>'
    + '<span class="dim">' + right + '</span></div>';
}

function renderBoard(d) {
  const banners = d.banners || {};
  const empty = !Object.keys(banners).length;
  let h = '<div class="panel"><div class="eyebrow">this week — '
    + esc(KIND_LABEL[d.challenge.kind] || d.challenge.kind) + '</div>';
  if (empty) {
    h += '<div class="faint">no banners raised yet — the Guildhall in '
      + 'Roothollow takes founders</div></div>';
    return h;
  }
  h += '<div class="faint">entry ◈ ' + d.challenge.entry_per_member
    + ' a head, paid from the faction store — the steward signs up at '
    + 'the Guildhall</div>';
  if (d.last_week.length) {
    h += '<div style="margin-top:8px">';
    d.last_week.forEach(wk => {
      h += '<div class="kv"><span' + (wk.won ? '' : ' class="k"') + '>'
        + (wk.won ? '★ ' : '') + esc(wk.faction) + ' — '
        + esc(wk.goal_kind).toUpperCase() + '</span><span class="dim">'
        + esc(wk.prize_note || (num(wk.progress) + '/'
        + num(wk.goal_target))) + '</span></div>';
    });
    h += '</div>';
  } else {
    h += '<div class="faint" style="margin-top:8px">no banner entered '
      + 'last week</div>';
  }
  h += '</div>';

  h += '<div class="panel"><div class="eyebrow">hall of banners — '
    + 'wins all-time</div>';
  if (d.wins.length) {
    d.wins.forEach((w, i) => {
      h += '<div class="kv"><span' + (i ? ' class="k"' : '') + '>'
        + (i === 0 ? '#1 ' : (i + 1) + '  ') + esc(w.faction)
        + '</span><span>' + w.wins + ' win' + (w.wins === 1 ? '' : 's')
        + '</span></div>';
    });
  } else {
    h += '<div class="faint">no challenge has been won yet</div>';
  }
  h += '</div>';

  h += '<div class="panel"><div class="eyebrow">most climbers</div>'
    + d.most_members.map(f => chipRow(f.name, banners,
        f.members + ' member' + (f.members === 1 ? '' : 's'))).join('')
    + '</div>';
  h += '<div class="panel"><div class="eyebrow">richest store</div>'
    + d.richest.map(f => chipRow(f.name, banners,
        '◈ ' + num(f.treasury))).join('')
    + '</div>';
  h += '<div class="panel"><div class="eyebrow">highest blades</div>'
    + d.highest.map(f => chipRow(f.name, banners,
        'avg lvl ' + f.avg_level)).join('')
    + '</div>';

  if (d.ticker.length) {
    h += '<div class="panel"><div class="eyebrow">the wire</div>'
      + d.ticker.map(t => '<div class="faint">· ' + esc(t)
        + '</div>').join('') + '</div>';
  }
  return h;
}

if (token) loadScene();
})();
"""


def render_pane() -> str:
    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>{_CSS}</style></head><body>
<div class="wrap">
  <div class="tabs" role="tablist">
    <button class="tab active" data-tab="game" role="tab">Game</button>
    <button class="tab" data-tab="score" role="tab">Score</button>
    <button class="tab" data-tab="community" role="tab">Community</button>
  </div>
  <div id="game" class="pane active"><div class="placeholder">
    <div class="eyebrow">the ascent</div>waking the lift…</div></div>
  <div id="score" class="pane"><div class="placeholder">
    <div class="eyebrow">muster roll</div>calling the roll…</div></div>
  <div id="community" class="pane"><div class="placeholder">
    <div class="eyebrow">the guildhall</div>unrolling the charters…</div></div>
</div>
<script>{_JS.replace("__API__", _API)}</script></body></html>"""
