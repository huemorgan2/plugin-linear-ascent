"""The game pane — the interface, out of the chat (plans 009 + 010).

One self-contained HTML app served at /api/p/plugin-linear-ascent/ui/ and
rendered by Luna's shell as a sidebar-section iframe. GAME reuses the exact
card grammar (render.SCENE_CSS + render_scene_fragment served by
/pane/scene and /act) so the pane is pixel-identical to the old chat cards;
clicks call /act directly with the host token — no card bridge, no model in
the path. SCORE is the full-world leaderboard. COMMUNITY (015) is the
faction surface: the news board, THE LEDGER (top 10 + server-side search),
and per-faction pages where names are clickable everywhere. Admins get the
ADMIN DESK inline — rename, join requests (accept/reject), kick/promote,
and the week's challenge paid from the coin vault. Founding still happens
IN-GAME at the Guildhall (level 4+); joining files a request the admins
settle at the desk. Everything is ANSI-block styled, monospace, in-pane —
no popups.

Auth: the shell posts {type:'luna-auth', token} into the iframe on load and
whenever the session changes; the pane also answers 401s by asking again
(luna-request-auth), matching PluginIframe's contract in Shell.tsx.
"""

from __future__ import annotations

from . import icons
from .render import (AETHER, BORDER, DIM, FAINT, INK, INTERACT_JS, PANEL,
                     PANEL2, SCENE_CSS, SWAP_JS, TEXT, TIP_JS, VIOLET,
                     VIOLET_SOFT)

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
.err{{border:1px solid {BORDER};
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
/* 030: gold reads gold wherever it is written, coin mask included. */
.gold{{color:#f5a524;}}
.trow.me{{color:{AETHER};}}
.fbanner{{width:160px;aspect-ratio:320/112;background-color:{DIM};
 mask-size:100% 100%;-webkit-mask-size:100% 100%;mask-repeat:no-repeat;
 -webkit-mask-repeat:no-repeat;image-rendering:pixelated;flex:none;}}
.fbanner.big{{width:100%;max-width:320px;background-color:{VIOLET_SOFT};}}
/* 027: the sigil rides beside a name in tight rows too. */
.fbanner.small{{width:64px;background-color:{VIOLET_SOFT};}}
.lrow .lname{{display:flex;align-items:center;gap:1ch;min-width:0;}}
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
/* ── 015: the faction desk ── */
.facname{{color:{TEXT};cursor:pointer;text-decoration:none;
 border-bottom:1px dotted {DIM};}}
.facname:hover{{color:{AETHER};border-bottom-color:{AETHER};}}
.back{{display:inline-block;color:{DIM};cursor:pointer;margin-bottom:10px;
 border:1px solid {BORDER};background:{PANEL};padding:5px 1.5ch;}}
.back:hover{{color:{TEXT};border-color:{VIOLET};}}
.findrow{{display:flex;gap:1ch;margin-bottom:8px;align-items:center;}}
.findrow .k{{color:{FAINT};letter-spacing:.08em;}}
.lrow{{display:grid;grid-template-columns:3ch 1fr 9ch 9ch;gap:1ch;
 padding:4px 0;border-bottom:1px dashed {BORDER};align-items:center;
 white-space:nowrap;overflow:hidden;}}
.lrow .r{{text-align:right;}}
.lrow.joinable{{grid-template-columns:3ch 1fr 9ch 9ch auto;
 align-items:center;}}
.drow{{display:grid;grid-template-columns:1fr auto;gap:1ch;padding:5px 0;
 border-bottom:1px dashed {BORDER};align-items:center;}}
.drow .who .sub{{color:{FAINT};}}
.rowbtns{{display:flex;gap:6px;}}
.btn.mini{{padding:3px 1ch;font-size:12px;}}
.btn.armed{{border-color:#f4645f;color:#f4645f;}}
.tag{{color:{VIOLET_SOFT};}}
.tag.founder{{color:#f5a524;}}
.deskmsg{{color:{DIM};padding:6px 0 0;min-height:18px;}}
.deskmsg.bad{{color:#f4645f;}}
.deskmsg.good{{color:{AETHER};}}
.deskbar{{border:1px solid {BORDER};
 background:{PANEL};color:{DIM};padding:9px 2ch;margin-top:10px;
 cursor:pointer;letter-spacing:.06em;}}
.deskbar:hover{{color:{TEXT};border-color:{VIOLET};}}
.savebar{{display:flex;gap:6px;margin-top:6px;}}
.savebar input{{flex:1;}}
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
/* 030: the one coin — the 16×16 mask, tinted by the .gold span it sits
   in. The ◈ character stays a text-surface mark only. */
const COIN = "__COIN__";
const coin = n => '<span class="eg" aria-hidden="true" style="'
  + "-webkit-mask-image:url('" + COIN + "');mask-image:url('" + COIN
  + "')\"></span> " + num(n);
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
function switchTab(name) {
  tabs.forEach(x => x.classList.toggle('active', x.dataset.tab === name));
  document.querySelectorAll('.pane').forEach(p =>
    p.classList.toggle('active', p.id === name));
  if (name === 'game') loadScene(true);
  if (name === 'score') loadScore();
  if (name === 'community') loadCommunity();
}
tabs.forEach(t => t.addEventListener('click',
  () => switchTab(t.dataset.tab)));

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

/* ── 016 split fx: the action gif plays once, then the ambient loop ─── */
function swapFX() { __SWAP_JS__ }

/* ── the game loop: swap fragments in place, act directly ───────────── */
const game = document.getElementById('game');
function showScene(d) {
  sceneId = d.scene_id || '';
  game.innerHTML = d.fragment;
  // 015: the Guildhall opens straight onto the faction desk
  if ((d.fragment || '').indexOf('THE GUILDHALL') !== -1) {
    const bar = document.createElement('div');
    bar.className = 'deskbar';
    bar.textContent = '\u25ba FACTION DESK \u2014 the ledger, requests '
      + 'and admin live in COMMUNITY';
    bar.addEventListener('click', () => switchTab('community'));
    game.appendChild(bar);
  }
  wireOptions();
  runFX(game);
  swapFX();               // 016: split banner art settles into its loop
  // 027: the pack popup, the card's input box and the rail count-up
  if (window.__laWire) window.__laWire(game);
}
/* 027: one door for everything that isn't a menu row — the pack popup's
   actions and the card's own text/number box. */
window.__laAct = async function (option, text) {
  if (loading) return;
  loading = true;
  try {
    showScene(await call('/act', {option: option || '', text: text || '',
      scene_id: sceneId, mode: 'pane'}));
  } catch (err) {
    if (err.message !== 'auth') showErr(err.message);
    const f = game.querySelector('form.ask');
    if (f) { f.querySelectorAll('input,button').forEach(
      x => { x.disabled = false; }); }
  } finally { loading = false; }
};
function showErr(msg) {
  const e = document.createElement('div');
  e.className = 'err'; e.textContent = msg;
  game.appendChild(e);
  setTimeout(() => e.remove(), 6000);
}
function wireOptions() {
  /* 027: everything that carries a data-opt acts the same way — menu rows,
     notice-board shortcuts, sigil tiles and the pack popup's actions. */
  const btns = [...game.querySelectorAll('button.opt, button.nrow, '
    + 'button.gtile, button.pclose')];
  const hint = game.querySelector('.reply');
  btns.forEach(b => b.addEventListener('click', async () => {
    if (loading) return;
    // 019: the Guildhall's "Join a banner" row IS the Community tab —
    // no server round trip, the door just opens.
    if (b.dataset.opt === 'hall_ledger') { switchTab('community'); return; }
    loading = true;
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
/* 0.29.5: 2s — the pane FOLLOWS the agent's play move by move (peek is
   an in-process scene-id read; the presence number inside it is cached
   server-side, so this cadence costs no world round trips). */
setInterval(peek, 2000);
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
        + '<span class="gold">' + coin(p.gold) + '</span>'
        + '<span class="gold">' + coin(p.bank) + '</span>'
        + '<span class="faint">' + (esc(p.faction) || '—') + '</span></div>';
    });
    score.innerHTML = h + '</div>';
  } catch (err) {
    if (err.message !== 'auth') paneFail(score, 'muster roll', err.message);
  }
}

/* ── COMMUNITY: the board, THE LEDGER, faction pages + admin desk (015) */
const community = document.getElementById('community');
let comm = {view: 'board', name: '', q: ''};
let deskBusy = false;

const fac = name => '<span class="facname" data-fac="' + esc(name) + '">'
  + esc(name) + '</span>';

async function loadCommunity() {
  try {
    if (comm.view === 'detail') {
      const d = await call('/pane/faction/detail', {name: comm.name});
      comm.name = d.name;                 // follows a rename
      community.innerHTML = renderFaction(d);
      return;
    }
    const [board, ledger] = await Promise.all([
      call('/pane/community'),
      call('/pane/factions?q=' + encodeURIComponent(comm.q))]);
    community.innerHTML =
      renderCta(ledger) + renderLedger(ledger) + renderBoard(board);
    wireFind();
  } catch (err) {
    if (err.message !== 'auth')
      paneFail(community, 'the faction board', err.message);
  }
}

const KIND_LABEL = {hoard: 'HOARD — gold earned',
                    cull: 'CULL — kills made',
                    climb: 'CLIMB — experience won'};

function chipRow(name, banners, right) {
  /* 032 §10: the sigil rides small to the LEFT of the name here — the
     stat is the row's point, the colors are its face. */
  const slug = banners[name] || '';
  return '<div class="frow">'
    + (slug ? sig(slug, 'small') : '<div class="fbanner small"></div>')
    + '<div class="meta"><div>' + fac(name) + '</div></div>'
    + '<span class="dim">' + right + '</span></div>';
}

/* 027: the same row, with the LEFT column already rendered (a rank, a
   star, a challenge name) — the sigil rides in front of it either way. */
function chipRow2(name, banners, left, right) {
  const slug = banners[name] || '';
  return '<div class="frow">'
    + (slug ? sig(slug, 'small') : '<div class="fbanner small"></div>')
    + '<div class="meta"><div><span class="facname" data-fac="'
    + esc(name) + '">' + left + '</span></div></div>'
    + '<span class="dim">' + right + '</span></div>';
}

/* ── 019: the pitch to the unbannered — join here, or found there ───── */
function renderCta(d) {
  if (d.in_faction) return '';
  let h = '<div class="panel"><div class="eyebrow">you climb '
    + 'unbannered</div><div>A faction table means a shared armory, '
    + 'weekly challenges, and people who notice when you fall. '
    + 'Ask to join any banner below';
  if (d.requested)
    h += ' \u2014 you\u2019ve already knocked at ' + fac(d.requested)
      + ', their steward decides';
  h += '.</div><div class="faint" style="margin-top:6px">Or raise your '
    + 'own at the Guildhall in Roothollow \u2014 \u25c8 '
    + num(d.found_fee || 300) + ', level ' + (d.found_min_level || 4)
    + ' and up.</div>'
    + '<button class="btn mini" id="ctahall" style="margin-top:8px">'
    + 'THE GUILDHALL \u2192</button></div>';
  return h;
}

/* ── THE LEDGER: top 10 + server-side search ────────────────────────── */
function ledgerRows(d) {
  if (!d.factions.length)
    return '<div class="faint">no banner answers to that name</div>';
  const open = !d.in_faction;   // the unbannered can knock from any row
  return d.factions.map((f, i) => {
    let act = '';
    if (open)
      act = f.name === d.requested
        ? '<span class="r tag">ASKED</span>'
        : '<span class="r"><button class="btn mini" data-desk="request" '
          + 'data-name="' + esc(f.name) + '">ASK TO JOIN</button></span>';
    return '<div class="lrow' + (open ? ' joinable' : '') + '">'
      + '<span class="faint">' + (i + 1) + '</span>'
      + '<span class="lname">'
      + (f.banner ? sig(f.banner, 'small') : '')
      + fac(f.name) + '</span>'
      + '<span class="r dim">' + f.members + ' at table</span>'
      + '<span class="r gold">\u25c8 ' + num(f.treasury) + '</span>'
      + act + '</div>';
  }).join('');
}

function renderLedger(d) {
  return '<div class="panel"><div class="eyebrow">the ledger \u2014 '
    + num(d.total) + ' banner' + (d.total === 1 ? '' : 's')
    + ' \u00b7 top 10 by table</div>'
    + '<div class="findrow"><span class="k">FIND</span>'
    + '<input id="find" class="ti" maxlength="24" '
    + 'placeholder="a banner\u2019s name\u2026"></div>'
    + '<div id="ledgerlist">' + ledgerRows(d) + '</div></div>';
}

function wireFind() {
  const fi = community.querySelector('#find');
  if (!fi) return;
  fi.value = comm.q;
  let t = 0;
  fi.addEventListener('input', () => {
    comm.q = fi.value;
    clearTimeout(t);
    t = setTimeout(async () => {
      try {
        const d = await call('/pane/factions?q='
          + encodeURIComponent(comm.q));
        const el = community.querySelector('#ledgerlist');
        if (el) el.innerHTML = ledgerRows(d);
      } catch (e) {}
    }, 250);
  });
}

/* ── the faction page + the admin desk ──────────────────────────────── */
function memberRow(m, v) {
  let tags = '';
  if (m.founder) tags += ' <span class="tag founder">\u2605 FOUNDER</span>';
  else if (m.role === 'steward') tags += ' <span class="tag">\u25c6 ADMIN</span>';
  if (m.arrears) tags += ' <span class="dim">\u25b2 arrears</span>';
  if (m.you) tags += ' <span class="faint">\u2190 you</span>';
  let btns = '';
  if (v.admin && !m.you) {
    if (m.role !== 'steward')
      btns += '<button class="btn mini" data-desk="promote" data-t="'
        + esc(m.tenant) + '" data-p="' + esc(m.player)
        + '">PROMOTE</button>';
    if (m.role !== 'steward' || v.founder)
      btns += '<button class="btn mini danger" data-desk="kick" data-t="'
        + esc(m.tenant) + '" data-p="' + esc(m.player) + '">KICK</button>';
  }
  return '<div class="drow"><div class="who">' + esc(m.name)
    + ' <span class="faint">L' + m.level + '</span>' + tags
    + '<div class="sub">' + m.days + 'd at the table this week</div></div>'
    + '<div class="rowbtns">' + btns + '</div></div>';
}

function requestRow(r) {
  return '<div class="drow"><div class="who">' + esc(r.name || r.player)
    + ' <span class="faint">L' + (r.level || 1) + '</span>'
    + '<div class="sub">asked on day ' + (r.requested_day || 0) + '</div></div>'
    + '<div class="rowbtns">'
    + '<button class="btn mini" data-desk="approve" data-t="'
    + esc(r.tenant) + '" data-p="' + esc(r.player) + '">ACCEPT</button>'
    + '<button class="btn mini danger" data-desk="reject" data-t="'
    + esc(r.tenant) + '" data-p="' + esc(r.player) + '">REJECT</button>'
    + '</div></div>';
}

const ROOM_NAMES = {1: 'the back room', 2: 'a hall of your own',
                    3: 'the long hall', 4: 'the high hall'};

function renderFaction(d) {
  const v = d.viewer || {};
  /* 032 \u00a710: the hall's numbers on the public page \u2014 the room for
     everyone, the coffer/chest/beds/board only when the API exposes
     them (members). An older worldd sends neither; nothing renders. */
  const hall = d.hall || null;
  const room = d.room_name
    || (hall && ROOM_NAMES[hall.room_tier])
    || (d.room_tier ? ROOM_NAMES[d.room_tier] : '');
  let h = '<span class="back" id="back">\u25c0 THE BOARD</span>';
  h += '<div class="panel">' + sig(d.banner, 'big')
    + '<div class="eyebrow" style="margin-top:8px">' + esc(d.name)
    + '</div>'
    + '<div class="kv"><span class="k">founded by</span>'
    + '<span><span class="tag founder">\u2605</span> ' + esc(d.founder)
    + '</span></div>'
    + (room ? '<div class="kv"><span class="k">the hall</span><span>'
        + esc(room) + '</span></div>' : '')
    + '<div class="kv"><span class="k">at the table</span><span>'
    + d.members.length + '</span></div>'
    + '<div class="kv"><span class="k">the coffer</span>'
    + '<span class="gold">\u25c8 ' + num(d.store)
    + (hall && hall.coffer && hall.coffer.cap
        ? ' of \u25c8 ' + num(hall.coffer.cap) : '')
    + '</span></div>'
    + (hall && hall.chest
        ? '<div class="kv"><span class="k">the chest</span><span>'
          + num(hall.chest.used) + ' of ' + num(hall.chest.cap)
          + ' slots</span></div>' : '')
    + (hall && hall.beds
        ? '<div class="kv"><span class="k">the bunks</span><span>'
          + num(hall.beds.count) + ' bed'
          + (hall.beds.count === 1 ? '' : 's') + ' \u00b7 '
          + ((hall.beds.tonight || []).length) + ' claimed tonight'
          + '</span></div>' : '')
    + '<div class="kv"><span class="k">join fee</span><span>\u25c8 '
    + num(d.join_fee) + '</span></div>'
    + '<div class="kv"><span class="k">weekly dues</span><span>\u25c8 '
    + num(d.dues) + '</span></div>'
    + '<div class="kv"><span class="k">weeks won</span><span>' + d.wins
    + '</span></div>'
    + (hall && (hall.notes || []).length
        ? '<div class="faint" style="margin-top:6px">DAY '
          + num(hall.notes[0].day) + ' \u00b7 '
          + esc(hall.notes[0].player) + ' \u2014 '
          + esc(hall.notes[0].line) + '</div>' : '');
  // an outsider's call to action
  if (!v.in_faction) {
    h += v.requested
      ? '<div class="deskmsg good">your request waits at their desk</div>'
        + '<button class="btn" data-desk="withdraw">WITHDRAW THE '
        + 'REQUEST</button>'
      : '<button class="btn" data-desk="request" data-name="'
        + esc(d.name) + '">ASK TO JOIN \u2014 \u25c8 ' + num(d.join_fee)
        + ' if accepted</button>';
  } else if (!v.member) {
    h += '<div class="deskmsg">you sit at another table</div>';
  }
  h += '</div>';

  h += '<div class="panel"><div class="eyebrow">the roster</div>'
    + d.members.map(m => memberRow(m, v)).join('') + '</div>';

  if (v.admin) {
    const wk = d.week || {};
    h += '<div class="panel"><div class="eyebrow">admin desk \u2014 '
      + 'the banner</div>'
      + '<div class="faint">rename flies new colors for everyone \u2014 '
      + '3\u201324 letters</div>'
      + '<div class="savebar"><input id="rn" class="ti" maxlength="24" '
      + 'value="' + esc(d.name) + '">'
      + '<button class="btn" data-desk="rename">SAVE</button></div>'
      + '<div class="deskmsg" id="deskmsg"></div></div>';
    h += '<div class="panel"><div class="eyebrow">admin desk \u2014 '
      + 'requests</div>'
      + ((d.requests || []).length
         ? d.requests.map(requestRow).join('')
         : '<div class="faint">no one waits at the desk</div>')
      + '</div>';
    h += '<div class="panel"><div class="eyebrow">admin desk \u2014 '
      + 'the week\u2019s challenge</div>'
      + '<div class="kv"><span class="k">the Ascent demands</span><span>'
      + esc((KIND_LABEL[wk.kind] || wk.kind || '').toString())
      + '</span></div>'
      + '<div class="kv"><span class="k">entry, from the coffer</span>'
      + '<span class="gold">\u25c8 ' + num(wk.entry_cost) + '</span></div>'
      + '<div class="kv"><span class="k">the coffer holds</span>'
      + '<span class="gold">\u25c8 ' + num(d.store) + '</span></div>'
      + (wk.entered
         ? '<div class="deskmsg good">entered \u2014 everything the table '
           + 'earns this week counts (target ' + num(wk.target) + ')</div>'
         : '<button class="btn" data-desk="enter">ACCEPT THE CHALLENGE '
           + '\u2014 PAY \u25c8 ' + num(wk.entry_cost)
           + ' FROM THE COFFER</button>')
      + '</div>';
  }
  return h;
}

/* ── desk actions: delegated, inline, no popups ─────────────────────── */
function deskMsg(text, cls) {
  const el = community.querySelector('#deskmsg');
  if (el) { el.textContent = text; el.className = 'deskmsg ' + (cls || ''); }
}

community.addEventListener('click', async (e) => {
  // 019: the CTA's founding pitch walks straight to the Guildhall card
  if (e.target.closest('#ctahall')) { switchTab('game'); return; }
  const back = e.target.closest('#back');
  if (back) { comm.view = 'board'; comm.name = ''; loadCommunity(); return; }
  const fname = e.target.closest('[data-fac]');
  if (fname) {
    comm.view = 'detail'; comm.name = fname.dataset.fac;
    loadCommunity(); return;
  }
  const btn = e.target.closest('[data-desk]');
  if (!btn || deskBusy) return;
  const kind = btn.dataset.desk;
  // destructive acts arm on first click — confirm inline, never a popup
  if (kind === 'kick' && !btn.classList.contains('armed')) {
    btn.classList.add('armed'); btn.textContent = 'SURE?';
    setTimeout(() => {
      if (btn.isConnected) { btn.classList.remove('armed');
        btn.textContent = 'KICK'; }
    }, 2600);
    return;
  }
  deskBusy = true; btn.disabled = true;
  try {
    if (kind === 'request')
      await call('/pane/faction/request', {name: btn.dataset.name});
    else if (kind === 'withdraw')
      await call('/pane/faction/cancel_request', {});
    else if (kind === 'rename') {
      const rn = community.querySelector('#rn');
      const d = await call('/pane/faction/rename',
        {name: (rn ? rn.value : '').trim()});
      comm.name = d.name || comm.name;
    } else if (kind === 'enter')
      await call('/pane/faction/enter', {});
    else
      await call('/pane/faction/' + kind,
        {tenant: btn.dataset.t, player: btn.dataset.p});
    await loadCommunity();
  } catch (err) {
    btn.disabled = false;
    if (err.message !== 'auth') {
      deskMsg(err.message, 'bad');
      if (!community.querySelector('#deskmsg')) {
        const m = document.createElement('div');
        m.className = 'deskmsg bad'; m.textContent = err.message;
        btn.parentElement.appendChild(m);
      }
    }
  } finally { deskBusy = false; }
});

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
  h += '<div class="faint">entry <span class="gold">'
    + coin(d.challenge.entry_per_member)
    + '</span> a head, paid from the faction coffer — the steward signs '
    + 'up at the hall</div>';
  if (d.last_week.length) {
    /* 027: a banner is a picture wherever it is named. */
    h += '<div style="margin-top:8px">';
    d.last_week.forEach(wk => {
      h += chipRow2(wk.faction, banners,
        (wk.won ? '★ ' : '') + esc(wk.faction) + ' — '
        + esc(wk.goal_kind).toUpperCase(),
        esc(wk.prize_note || (num(wk.progress) + '/'
        + num(wk.goal_target))));
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
      h += chipRow2(w.faction, banners,
        (i === 0 ? '#1 ' : (i + 1) + '  ') + esc(w.faction),
        w.wins + ' win' + (w.wins === 1 ? '' : 's'));
    });
  } else {
    h += '<div class="faint">no challenge has been won yet</div>';
  }
  h += '</div>';

  h += '<div class="panel"><div class="eyebrow">most climbers</div>'
    + d.most_members.map(f => chipRow(f.name, banners,
        f.members + ' member' + (f.members === 1 ? '' : 's'))).join('')
    + '</div>';
  h += '<div class="panel"><div class="eyebrow">richest coffer</div>'
    + d.richest.map(f => chipRow(f.name, banners,
        '<span class="gold">' + coin(f.treasury) + '</span>')).join('')
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
<script>{INTERACT_JS}</script>
<script>{_JS.replace("__API__", _API).replace("__SWAP_JS__", SWAP_JS)
           .replace("__COIN__", icons.icon_data_url("coin"))}</script>
<script>{TIP_JS}</script></body></html>"""
