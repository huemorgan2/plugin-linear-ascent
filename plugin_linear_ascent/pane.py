"""The game pane — the interface, out of the chat (plans 009 + 010).

One self-contained HTML app served at /api/p/plugin-linear-ascent/ui/ and
rendered by Luna's shell as a sidebar-section iframe. GAME reuses the exact
card grammar (render.SCENE_CSS + render_scene_fragment served by
/pane/scene and /act) so the pane is pixel-identical to the old chat cards;
clicks call /act directly with the host token — no card bridge, no model in
the path. SCORE is the full-world leaderboard; COMMUNITY is factions:
join/create (name + sigil pick), weekly goals, attendance, steward tools.

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

/* ── COMMUNITY: factions ────────────────────────────────────────────── */
const community = document.getElementById('community');
let pickedBanner = '';
async function loadCommunity() {
  try {
    const d = await call('/pane/community');
    community.innerHTML = d.status && d.status.faction
      ? renderMine(d.status) : renderHall(d.list);
    wireCommunity(d);
  } catch (err) {
    if (err.message !== 'auth')
      paneFail(community, 'the guildhall', err.message);
  }
}

const GOAL_LABEL = {hoard: 'HOARD — gold earned',
                    cull: 'CULL — kills made',
                    climb: 'CLIMB — experience won'};
const GOAL_PRIZE = {hoard: 'prize: bonus gold, split by days shown',
                    cull: 'prize: +HP blessing all next week',
                    climb: 'prize: +XP blessing all next week'};

function renderMine(s) {
  const pct = Math.round(s.base_pct * 100);
  const att = s.attendance;
  const goalSet = s.goal && s.goal.target > 0;
  let h = '<div class="panel"><div class="eyebrow">your banner</div>'
    + '<div class="frow" style="border-bottom:0">' + sig(s.banner, 'big')
    + '<div class="meta"><div style="font-weight:700">' + esc(s.faction)
    + '</div><div class="faint">' + s.members.length + ' at the table · '
    + 'you are ' + esc(s.role) + ' · base prize ' + pct + '%</div>'
    + '</div></div></div>';

  h += '<div class="panel"><div class="eyebrow">weekly goal</div>';
  if (goalSet) {
    h += '<div class="kv"><span class="k">'
      + esc(GOAL_LABEL[s.goal.kind] || s.goal.kind) + '</span><span>'
      + num(s.goal.progress) + ' / ' + num(s.goal.target) + '</span></div>'
      + '<div>' + bar(s.goal.progress, s.goal.target, 28) + '</div>'
      + '<div class="faint" style="margin-top:4px">'
      + esc(GOAL_PRIZE[s.goal.kind] || '') + '</div>';
  } else {
    h += '<div class="faint">no goal set — the steward picks one below'
      + '</div>';
  }
  if (s.role === 'steward') {
    h += '<div style="display:flex;gap:1ch;margin-top:10px;flex-wrap:wrap">'
      + '<select id="goal-kind" class="ti">'
      + ['hoard', 'cull', 'climb'].map(k =>
          '<option value="' + k + '"'
          + (goalSet && s.goal.kind === k ? ' selected' : '') + '>'
          + k.toUpperCase() + '</option>').join('')
      + '</select>'
      + '<input id="goal-target" class="ti" style="max-width:16ch" '
      + 'type="number" min="1" placeholder="target" value="'
      + (goalSet ? s.goal.target : '') + '">'
      + '<button class="btn" id="goal-set">Set goal</button></div>'
      + '<div class="faint" style="margin-top:6px">fair for this crew: '
      + Object.entries(s.suggested).map(([k, v]) =>
          k + ' ' + num(v)).join(' · ') + '</div>';
  }
  h += '</div>';

  h += '<div class="panel"><div class="eyebrow">attendance — '
    + att.attended + '/' + att.required + ' member-days · prize ×'
    + att.multiplier.toFixed(2) + '</div>'
    + '<div class="faint" style="margin-bottom:6px">4 days each = full '
    + 'prize · under half = nothing · all 7 = ×1.75 (cap)</div>';
  s.members.forEach(m => {
    h += '<div class="mrow"><span>' + esc(m.name)
      + (m.role === 'steward' ? ' <span class="faint">· steward</span>' : '')
      + '</span><span class="r">lv ' + m.level + '</span>'
      + '<span class="r">' + m.days + '/' + m.required + ' days</span>'
      + '<span style="text-align:right">'
      + (s.role === 'steward' && !(m.role === 'steward')
         ? '<button class="btn danger" data-kick-t="' + esc(m.tenant)
           + '" data-kick-p="' + esc(m.player) + '">remove</button>' : '')
      + '</span></div>';
  });
  if (s.last_week) {
    h += '<div class="faint" style="margin-top:8px">last week: '
      + esc(s.last_week.prize_note || '—') + '</div>';
  }
  h += '<div style="margin-top:10px"><button class="btn danger" id="leave">'
    + 'Leave the faction</button></div></div>';
  return h;
}

function renderHall(l) {
  let h = '<div class="panel"><div class="eyebrow">banners flying</div>';
  if (!l.factions.length) {
    h += '<div class="faint">no factions yet — raise the first banner'
      + '</div>';
  }
  l.factions.forEach(f => {
    h += '<div class="frow">' + sig(f.banner)
      + '<div class="meta"><div>' + esc(f.name) + '</div>'
      + '<div class="faint">' + f.members + ' member'
      + (f.members === 1 ? '' : 's')
      + (f.goal_target > 0 ? ' · ' + esc(f.goal_kind) + ' '
         + num(f.goal_target) : ' · no goal yet') + '</div></div>'
      + '<button class="btn" data-join="' + esc(f.name) + '">Join</button>'
      + '</div>';
  });
  h += '</div>';

  h += '<div class="panel"><div class="eyebrow">found a new banner · ◈ '
    + num(l.found_fee) + '</div>'
    + '<input id="new-name" class="ti" maxlength="24" '
    + 'placeholder="name your faction (3–24 letters)">'
    + '<div class="faint" style="margin:8px 0 0">pick your sigil</div>'
    + '<div class="bgrid">'
    + l.banners.map(b => '<div class="cell" data-banner="' + esc(b) + '">'
        + sig(b) + '<div class="cap">' + esc(b.replace(/_/g, ' '))
        + '</div></div>').join('')
    + '</div>'
    + '<button class="btn" id="create" disabled>Raise the banner · ◈ '
    + num(l.found_fee) + '</button>'
    + '<span class="faint" id="create-hint" style="margin-left:1ch">'
    + 'name + sigil first</span></div>';
  return h;
}

function wireCommunity(d) {
  const el = community;
  const act = async (fn) => {
    try { await fn(); await loadCommunity(); }
    catch (err) {
      if (err.message !== 'auth') {
        const e = document.createElement('div');
        e.className = 'err'; e.textContent = err.message;
        el.prepend(e); setTimeout(() => e.remove(), 6000);
      }
    }
  };
  el.querySelectorAll('[data-join]').forEach(b => b.onclick = () =>
    act(() => call('/pane/community/join', {faction: b.dataset.join})));
  el.querySelectorAll('[data-kick-t]').forEach(b => b.onclick = () =>
    act(() => call('/pane/community/kick',
      {tenant: b.dataset.kickT, player: b.dataset.kickP})));
  const leave = el.querySelector('#leave');
  if (leave) leave.onclick = () =>
    act(() => call('/pane/community/leave', {}));
  const goalSet = el.querySelector('#goal-set');
  if (goalSet) goalSet.onclick = () => {
    const kind = el.querySelector('#goal-kind').value;
    const target = parseInt(el.querySelector('#goal-target').value, 10);
    if (!target || target <= 0) return;
    act(() => call('/pane/community/goal', {kind, target}));
  };
  const create = el.querySelector('#create');
  const name = el.querySelector('#new-name');
  const hint = el.querySelector('#create-hint');
  if (create && name) {
    pickedBanner = '';
    const ready = () => {
      const ok = name.value.trim().length >= 3 && pickedBanner;
      create.disabled = !ok;
      if (hint) hint.textContent = ok ? '' : 'name + sigil first';
    };
    name.addEventListener('input', ready);
    el.querySelectorAll('[data-banner]').forEach(c => c.onclick = () => {
      el.querySelectorAll('[data-banner]').forEach(x =>
        x.classList.toggle('sel', x === c));
      pickedBanner = c.dataset.banner;
      ready();
    });
    create.onclick = () => act(() => call('/pane/community/create',
      {name: name.value.trim(), banner: pickedBanner}));
  }
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
