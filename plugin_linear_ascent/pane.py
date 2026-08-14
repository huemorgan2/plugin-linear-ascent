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
no popups. The one sanctioned exception (050): a refused action toasts a
single red line pinned to the top of the viewport for three seconds —
nothing to click, nothing to dismiss, the card underneath never moves.

Auth: the shell posts {type:'luna-auth', token} into the iframe on load and
whenever the session changes; the pane also answers 401s by asking again
(luna-request-auth), matching PluginIframe's contract in Shell.tsx.
"""

from __future__ import annotations

from . import icons
from .render import (AETHER, ART, BORDER, BRIGHT, DIM, FAINT, FONT_STACK,
                     GOLD, INK, INTERACT_JS, PANEL, PANEL2, RED, SCENE_CSS,
                     SWAP_JS, TEXT, TIP_JS, VIOLET, VIOLET_SOFT)
from .sfx import SFX_JS

_API = "/api/p/plugin-linear-ascent"

_CSS = f"""
:root {{ color-scheme: dark; }}
html,body{{margin:0;padding:0;background:{INK};min-height:100%;}}
body{{color:{TEXT};
 font:16px/1.5 {FONT_STACK};
 -webkit-font-smoothing:none;font-smooth:never;text-rendering:optimizeSpeed;
 font-variant-numeric:tabular-nums;}}
.wrap{{max-width:760px;margin:0 auto;padding:14px 12px 64px;}}
.tabs{{display:flex;gap:2px;margin-bottom:12px;border:1px solid {BORDER};
 background:{PANEL};}}
.tab{{flex:1;background:none;border:0;border-right:1px solid {BORDER};
 color:{DIM};font:inherit;letter-spacing:.14em;text-transform:uppercase;
 padding:9px 0;cursor:pointer;border-radius:0;}}
.tab:last-child{{border-right:0;}}
.tab:hover{{color:{TEXT};}}
.tab.active{{background:{GOLD};color:{INK};}}
.pane{{display:none;}}
.pane.active{{display:block;}}
.dim{{color:{DIM};}} .faint{{color:{FAINT};}}
.placeholder{{background:{PANEL};border:1px solid {BORDER};padding:18px 2ch;
 color:{DIM};}}
.placeholder .eyebrow{{color:{FAINT};text-transform:uppercase;
 letter-spacing:.08em;margin-bottom:6px;}}
.err{{border:1px solid {BORDER};
 background:{PANEL};color:{DIM};padding:12px 2ch;margin-top:10px;}}
/* 050: the refusal line — a rule said no. One thin bright-red line on
   black, pinned to the top of the viewport over whatever is scrolled
   there, then it slides up and is gone. Not a popup: nothing to click,
   nothing to dismiss, the card underneath never moves. */
#latoast{{position:fixed;top:0;left:0;right:0;z-index:120;
 background:{INK};color:{RED};border-bottom:1px solid {RED};
 font:inherit;line-height:1.5;padding:5px 2ch;
 text-align:center;white-space:nowrap;overflow:hidden;
 text-overflow:ellipsis;transition:transform .28s steps(4,end);}}
#latoast.gone{{transform:translateY(-110%);}}
a{{color:{AETHER};}}
{SCENE_CSS}
.opt.busy{{opacity:.7;}}
/* ── 010: score & community ── */
.panel{{background:{PANEL};border:1px solid {BORDER};padding:12px 2ch 10px;
 margin-bottom:12px;}}
.panel .eyebrow{{margin-bottom:8px;}}
.trow{{display:grid;grid-template-columns:3ch 1fr 5ch 5ch 9ch 9ch 12ch;
 gap:1ch;padding:3px 0;border-bottom:1px dashed {BORDER};align-items:baseline;
 white-space:nowrap;overflow:hidden;}}
.trow.head{{color:{FAINT};text-transform:uppercase;letter-spacing:.08em;}}
.trow .r{{text-align:right;}}
.trow .gold{{color:{GOLD};text-align:right;}}
/* 030: gold reads gold wherever it is written, coin mask included. */
.gold{{color:{GOLD};}}
.trow.me{{color:{AETHER};}}
.fbanner{{width:160px;aspect-ratio:320/112;background-color:{DIM};
 mask-size:100% 100%;-webkit-mask-size:100% 100%;mask-repeat:no-repeat;
 -webkit-mask-repeat:no-repeat;image-rendering:pixelated;flex:none;}}
.fbanner.big{{width:100%;max-width:320px;background-color:{ART};}}
/* 027: the sigil rides beside a name in tight rows too. */
.fbanner.small{{width:64px;background-color:{ART};}}
.lrow .lname{{display:flex;align-items:center;gap:1ch;min-width:0;}}
.frow{{display:flex;gap:2ch;align-items:center;padding:8px 0;
 border-bottom:1px dashed {BORDER};}}
.frow .meta{{flex:1;min-width:0;}}
.btn{{background:{PANEL2};border:1px solid {BORDER};color:{TEXT};
 font:inherit;padding:6px 1.5ch;cursor:pointer;border-radius:0;}}
.btn:hover:not(:disabled){{background:{GOLD};border-color:{GOLD};
 color:{INK};}}
.btn:disabled{{opacity:.5;cursor:default;}}
.btn.danger:hover:not(:disabled){{background:{RED};border-color:{RED};
 color:{INK};}}
.bgrid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));
 gap:8px;margin:8px 0;}}
.bgrid .cell{{border:1px solid {BORDER};padding:6px;cursor:pointer;
 background:{PANEL2};}}
.bgrid .cell.sel{{border-color:{AETHER};}}
.bgrid .fbanner{{width:100%;}}
.bgrid .cap{{color:{FAINT};margin-top:4px;
 text-align:center;overflow:hidden;text-overflow:ellipsis;}}
input.ti{{background:{INK};color:{TEXT};border:1px solid {BORDER};
 font:inherit;padding:6px 1ch;width:100%;box-sizing:border-box;
 caret-color:{GOLD};}}
input.ti:focus,select.ti:focus,textarea.ti:focus{{outline:none;
 border-color:{AETHER};}}
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
.back:hover{{background:{GOLD};border-color:{GOLD};color:{INK};}}
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
.btn.mini{{padding:3px 1ch;}}
.btn.armed{{border-color:{RED};color:{RED};}}
.tag{{color:{VIOLET_SOFT};}}
.tag.founder{{color:{GOLD};}}
.deskmsg{{color:{DIM};padding:6px 0 0;min-height:18px;}}
.deskmsg.bad{{color:{RED};}}
.deskmsg.good{{color:{AETHER};}}
.deskbar{{border:1px solid {BORDER};
 background:{PANEL};color:{DIM};padding:9px 2ch;margin-top:10px;
 cursor:pointer;letter-spacing:.06em;}}
.deskbar:hover{{background:{GOLD};border-color:{GOLD};color:{INK};}}
.savebar{{display:flex;gap:6px;margin-top:6px;}}
.savebar input{{flex:1;}}
/* ── 042: the sound bar — pinned under everything, ANSI like the rest */
.sndbar{{position:fixed;left:0;right:0;bottom:0;z-index:40;
 background:{PANEL};border-top:1px solid {BORDER};
 display:flex;justify-content:center;gap:8px;padding:6px 12px;}}
.sndbtn{{display:flex;align-items:center;gap:1ch;background:none;
 border:1px solid {BORDER};color:{DIM};font:inherit;
 letter-spacing:.14em;text-transform:uppercase;padding:5px 1.5ch;
 cursor:pointer;border-radius:0;}}
.sndbtn:hover{{color:{TEXT};}}
.sndbtn.off{{color:{DIM};}}
.sndbtn.off .sndico{{opacity:.35;}}
.sndico{{width:16px;height:16px;background:currentColor;flex:none;
 mask-size:100% 100%;-webkit-mask-size:100% 100%;mask-repeat:no-repeat;
 -webkit-mask-repeat:no-repeat;image-rendering:pixelated;}}
/* ── 051: the postbox — feedback, replies, the admin desk ── */
.sndbtn{{position:relative;}}
.fbbadge{{position:absolute;top:-7px;right:-7px;background:{AETHER};
 color:{INK};line-height:1;padding:2px 4px;
 letter-spacing:0;}}
#fbpanel{{display:none;position:fixed;inset:0;z-index:110;background:{INK};
 overflow-y:auto;}}
#fbpanel.open{{display:block;}}
#fbpanel .fbwrap{{max-width:760px;margin:0 auto;padding:14px 12px 90px;}}
textarea.ti{{background:{INK};color:{TEXT};border:1px solid {BORDER};
 font:inherit;padding:6px 1ch;width:100%;box-sizing:border-box;
 min-height:110px;resize:vertical;display:block;}}
.fbrow{{display:grid;grid-template-columns:1fr auto;gap:1ch;padding:7px 0;
 border-bottom:1px dashed {BORDER};cursor:pointer;align-items:baseline;}}
.fbrow .fbsub{{color:{TEXT};min-width:0;}}
.fbrow:hover .fbsub{{color:{AETHER};}}
.fbrow .sub{{color:{FAINT};overflow:hidden;
 text-overflow:ellipsis;white-space:nowrap;}}
.fbnew{{color:{AETHER};}}
.fbmsg{{border:1px solid {BORDER};background:{PANEL};padding:8px 2ch;
 margin:10px 0;max-width:85%;}}
.fbmsg.me{{margin-left:15%;border-color:{GOLD};}}
.fbmsg.them{{margin-right:15%;}}
.fbmsg .meta{{color:{FAINT};text-transform:uppercase;
 letter-spacing:.08em;margin-bottom:5px;}}
.fbmsg .mbody{{white-space:pre-wrap;overflow-wrap:anywhere;}}
.fbatt{{display:flex;gap:8px;margin-top:8px;flex-wrap:wrap;}}
.fbatt img{{max-width:140px;max-height:100px;border:1px solid {BORDER};
 cursor:pointer;display:block;background:{PANEL2};min-width:40px;
 min-height:30px;}}
.fbthumbs{{display:flex;gap:10px;margin:8px 0;flex-wrap:wrap;}}
.fbthumbs .twrap{{position:relative;}}
.fbthumbs img{{max-width:90px;max-height:70px;border:1px solid {BORDER};
 display:block;}}
.fbthumbs .tx{{position:absolute;top:-7px;right:-7px;background:{INK};
 color:{RED};border:1px solid {RED};font:inherit;
 line-height:1;padding:2px 4px;cursor:pointer;}}
#fblight{{display:none;position:fixed;inset:0;z-index:130;
 background:#000000dd;align-items:center;justify-content:center;
 padding:20px;cursor:pointer;}}
#fblight.open{{display:flex;}}
#fblight img{{max-width:100%;max-height:100%;border:1px solid {BORDER};}}
"""

# Plain string on purpose: real braces everywhere — no f-string doubling.
_JS = r"""
(() => {
const API = '__API__';
/* 005 web play: served at linearascent.net/play the pane keeps no token —
   the session cookie rides every same-origin fetch, and a 401 walks back
   to the door instead of asking a Luna shell that isn't there. */
const WEB = __WEB__;
let token = new URLSearchParams(location.search).get('token') || '';
let sceneId = '';
let loading = false;

/* ── auth handshake (PluginIframe contract) ─────────────────────────── */
window.addEventListener('message', (e) => {
  const d = e.data || {};
  if (!WEB && d.type === 'luna-auth' && d.token) {
    const fresh = d.token !== token;
    token = d.token;
    if (fresh && !sceneId) loadScene(true);
  }
});
if (!WEB) {
  try { parent.postMessage({type: 'luna-ui-ready'}, '*'); } catch (e) {}
}

function hdrs() {
  return {'Content-Type': 'application/json',
          ...(!WEB && token ? {'Authorization': 'Bearer ' + token} : {})};
}
async function call(path, body) {
  const r = await fetch(API + path, body === undefined
    ? {headers: hdrs()}
    : {method: 'POST', headers: hdrs(), body: JSON.stringify(body)});
  if (r.status === 401) {
    if (WEB) { location.href = '/#door-signin'; throw new Error('auth'); }
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
/* 041: any click while the ink is still wet quadruples the pen — the
   flag resets when the next scene lands, so every card starts slow. */
let fast = false;
document.addEventListener('pointerdown', () => { fast = true; });
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
      for (let c = 3; c < t.length + 3; c += 3) {
        n.nodeValue = t.slice(0, Math.min(c, t.length));
        await sleep(fast ? 2 : 7);
        if (!el.isConnected) { cur.remove(); return; }
      }
    }
    cur.remove();
  }
  let d = 0;
  for (const el of later) {
    setTimeout(() => el.classList.add('shown'), d); d += fast ? 8 : 30;
  }
}

/* ── 016 split fx: the action gif plays once, then the ambient loop ─── */
function swapFX() { __SWAP_JS__ }

/* ── the game loop: swap fragments in place, act directly ───────────── */
const game = document.getElementById('game');
function showScene(d) {
  sceneId = d.scene_id || '';
  fast = false;             // 041: every fresh card starts at ink speed
  game.innerHTML = d.fragment;
  // 041: on the phone a new scene walks the page back up to its art —
  // without this the player lands mid-card and reads bottom-first.
  if (matchMedia('(max-width: 520px)').matches) {
    const art = game.querySelector('.bwrap, .banner') || game;
    requestAnimationFrame(() =>
      art.scrollIntoView({behavior: 'smooth', block: 'start'}));
  }
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
  // 042: the stings and the weapon hit — before __laWire so a loot
  // fanfare can squelch the meter blips its own tweens would fire.
  if (window.__laScene) window.__laScene(d, game);
  // 027: the pack popup, the card's input box and the rail count-up
  if (window.__laWire) window.__laWire(game);
  if (WEB) armHistory();    // browser back = the card's own back door
  // 051: the first working scene proves auth — light the postbox badge
  if (!fbPolled) { fbPolled = true; fbPoll(); }
}
/* ── browser back walks the game home (WEB only) ────────────────────
   Every card that carries a back-style row arms one history entry and
   names itself in the address bar (#roothollow-the-square). Pressing
   the browser's back pops that guard and acts the row — deeper cards
   walk home door by door. Cards with no back row (the square, a
   fight) leave the button to the browser: nothing is fled by
   accident, and a second press leaves the site. Inside the Luna
   iframe (!WEB) the shell owns the history — hands off. */
const BACK_IDS = ['back', 'dr_back', 'gdir_back', 'guild_leave', 'town'];
let armed = false;
function backOpt() {
  const b = [...game.querySelectorAll('button.opt')]
    .find(x => BACK_IDS.indexOf(x.dataset.opt) !== -1);
  return b ? b.dataset.opt : '';
}
function armHistory() {
  const label = ((game.querySelector('.eyebrow') || {}).textContent || '')
    .toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
  const url = label ? '#' + label : location.pathname + location.search;
  if (backOpt()) {
    if (armed) history.replaceState({laGuard: 1}, '', url);
    else { history.pushState({laGuard: 1}, '', url); armed = true; }
  } else {
    history.replaceState(armed ? {laGuard: 1} : {laBase: 1}, '', url);
  }
}
if (WEB) {
  history.replaceState({laBase: 1}, '', location.href);
  window.addEventListener('popstate', () => {
    armed = false;                     // the guard entry was consumed
    const opt = backOpt();
    if (opt && !loading) window.__laAct(opt);   // showScene re-arms
  });
}
/* 027: one door for everything that isn't a menu row — the pack popup's
   actions and the card's own text/number box. */
window.__laAct = async function (option, text) {
  if (loading) return;
  loading = true;
  try {
    const d = await call('/act', {option: option || '', text: text || '',
      scene_id: sceneId, mode: 'pane'});
    if (d.refusal) {
      // 050: a rule said no — toast the line, keep the card as it is.
      showToast(d.refusal);
      const f = game.querySelector('form.ask');
      if (f) { f.querySelectorAll('input,button').forEach(
        x => { x.disabled = false; }); }
    } else {
      showScene(d);
    }
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
/* 050: the refusal toast — shows instantly at the top of the viewport,
   holds 3 seconds, slides up and is gone. One at a time: a new refusal
   replaces the line instead of stacking. */
let toastTimer = 0;
function showToast(msg) {
  const old = document.getElementById('latoast');
  if (old) { clearTimeout(toastTimer); old.remove(); }
  const t = document.createElement('div');
  t.id = 'latoast'; t.textContent = msg;
  document.body.appendChild(t);
  toastTimer = setTimeout(() => {
    t.classList.add('gone');
    t.addEventListener('transitionend', () => t.remove(), {once: true});
    setTimeout(() => { t.remove(); }, 600);  // reduced-motion fallback
  }, 3000);
}
function wireOptions() {
  /* 027: everything that carries a data-opt acts the same way — menu rows,
     notice-board shortcuts, sigil tiles and the pack popup's actions. */
  const btns = [...game.querySelectorAll('button.opt, button.nrow, '
    + 'button.gtile, button.ptile, button.pclose')];
  const hint = game.querySelector('.reply');
  btns.forEach(b => {
    if (b.__wired) return;
    b.__wired = true;
    b.addEventListener('click', async () => {
    if (loading) return;
    if (window.__laSfx) window.__laSfx('click');   // 042
    loading = true;
    btns.forEach(x => { x.disabled = true;
      x.classList.add(x === b ? 'busy' : 'stale'); });
    if (hint) hint.textContent = '…';
    const restore = () => {
      btns.forEach(x => { x.disabled = false;
        x.classList.remove('busy', 'stale'); });
      if (hint) hint.textContent = 'click an option — or reply with a number';
    };
    try {
      const d = await call('/act',
        {option: b.dataset.opt, scene_id: sceneId, mode: 'pane'});
      if (d.refusal) {
        // 050: a rule said no — toast the line, no card swap, no
        // typewriter replay; the rows come straight back to hand.
        // Adopt the answer's scene id: the stored card was re-stamped,
        // and without this the 2s peek reads "scene changed" and
        // reloads the whole card right after the toast.
        if (d.scene_id) sceneId = d.scene_id;
        showToast(d.refusal);
        restore();
      } else {
        showScene(d);
      }
    } catch (err) {
      restore();
      if (err.message !== 'auth') showErr(err.message);
    } finally { loading = false; }
  });
  });
  wireMore();
}
/* the presence grid's MORE N PLAYERS — fetches the rest of the room
   (server caps at 200) and unfolds it into the same grid */
function wireMore() {
  const pm = game.querySelector('button.pmore');
  if (!pm || pm.__wired) return;
  pm.__wired = true;
  pm.addEventListener('click', async () => {
    pm.disabled = true;
    try {
      const d = await call('/pane/room_more', {});
      const grid = game.querySelector('.pgrid');
      if (grid && d.html) {
        const have = new Set([...grid.querySelectorAll('.ptile')]
          .map(b => b.dataset.opt));
        const box = document.createElement('div');
        box.innerHTML = d.html;
        [...box.querySelectorAll('.ptile')].forEach(b => {
          if (!have.has(b.dataset.opt)) grid.appendChild(b);
        });
      }
      const row = pm.closest('.pmrow');
      if (row) row.remove(); else pm.remove();
      wireOptions();
    } catch (err) {
      pm.disabled = false;
      if (err.message !== 'auth') showErr(err.message);
    }
  });
}
/* 041: the number row presses the menu — 1 clicks the first option row,
   2 the second, and so on. Quiet while any input owns the keyboard. */
document.addEventListener('keydown', (e) => {
  if (e.ctrlKey || e.metaKey || e.altKey) return;
  const tag = (document.activeElement || {}).tagName;
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
  if (e.key.length !== 1 || e.key < '1' || e.key > '9') return;
  const btns = [...game.querySelectorAll('button.opt')]
    .filter(b => !b.disabled && b.offsetParent !== null);
  const b = btns[e.key - 1];
  if (b) { e.preventDefault(); b.click(); }
});
async function loadScene(force) {
  if (loading || (!WEB && !token && !force)) return;
  loading = true;
  try { showScene(await call('/pane/scene', {})); }
  catch (err) { if (err.message !== 'auth') showErr(err.message); }
  finally { loading = false; }
}

/* ── freshness: chat-driven acts and world events reach the pane ────── */
async function peek() {
  if ((!WEB && !token) || document.hidden || loading) return;
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

/* ── 051: the postbox — feedback, replies, the admin desk ───────────────
   A FEEDBACK switch on the sound bar opens a full-viewport overlay in the
   pane's own ANSI grammar. Players file subject + message + up to three
   screenshots; each thread reads like a chat. The two named wardens get
   an ADMIN switch: every thread, WhatsApp-sorted, same chat inside.
   Unread counts ride small red badges — polled once a minute and after
   every postbox act, never on the 2s peek hot path. */
const fbPanel = document.getElementById('fbpanel');
const fbLight = document.getElementById('fblight');
const fbBtn = document.getElementById('fbbtn');
const fbAdminBtn = document.getElementById('fbadmin');
let fbPolled = false;
let fb = {view: 'list', id: 0, asAdmin: false, admin: false};
let fbDraft = [];              // pending screenshots [{mime, data}]
let fbBusy = false;

async function fetchBlob(path) {
  const h = (!WEB && token) ? {'Authorization': 'Bearer ' + token} : {};
  const r = await fetch(API + path, {headers: h});
  if (!r.ok) throw new Error('att');
  return URL.createObjectURL(await r.blob());
}

function fbBadges(d) {
  fb.admin = !!d.admin;
  fbAdminBtn.hidden = !fb.admin;
  const b = document.getElementById('fbbadge');
  b.hidden = !d.unread; b.textContent = d.unread || '';
  const a = document.getElementById('fbabadge');
  const n = d.admin_unread || 0;
  a.hidden = !n; a.textContent = n || '';
}
async function fbPoll() {
  if (!WEB && !token) return;
  try { fbBadges(await call('/pane/feedback/unread')); } catch (e) {}
}
setInterval(fbPoll, 60000);

const fbWhen = iso => {
  try {
    return new Date(iso).toLocaleString(undefined,
      {month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'});
  } catch (e) { return ''; }
};

function fbOpen(view) {
  fb.view = view; fb.id = 0; fb.asAdmin = view === 'admin';
  fbDraft = [];
  fbPanel.classList.add('open');
  fbLoad();
}
function fbClose() { fbPanel.classList.remove('open'); fbPoll(); }
fbBtn.addEventListener('click', () => {
  if (window.__laSfx) window.__laSfx('click');
  fbOpen('list');
});
fbAdminBtn.addEventListener('click', () => {
  if (window.__laSfx) window.__laSfx('click');
  // on the site the button opens the full admin desk (/admin) in its
  // own tab — the session cookie is the key; in Luna the pane's inline
  // postbox desk remains the whole desk. An anchor click, not a popup
  // call (015): the browser treats it as plain navigation.
  if (WEB) {
    const a = document.createElement('a');
    a.href = '/admin'; a.target = '_blank'; a.rel = 'noopener';
    document.body.appendChild(a); a.click(); a.remove();
    return;
  }
  fbOpen('admin');
});
fbLight.addEventListener('click', () => fbLight.classList.remove('open'));
document.addEventListener('keydown', (e) => {
  if (e.key !== 'Escape') return;
  if (fbLight.classList.contains('open')) {
    fbLight.classList.remove('open');
  } else if (fbPanel.classList.contains('open')) {
    if (fb.id) { fb.id = 0; fbDraft = []; fbLoad(); } else fbClose();
  }
});

async function fbLoad() {
  try {
    if (fb.id) {
      fbRenderThread(await call('/pane/feedback/thread',
        {id: fb.id, as_admin: fb.asAdmin}));
    } else if (fb.view === 'admin') {
      fbRenderAdmin(await call('/pane/feedback/admin'));
    } else {
      fbRenderList(await call('/pane/feedback/mine'));
    }
  } catch (err) {
    if (err.message === 'auth') return;
    fbPanel.innerHTML = '<div class="fbwrap">'
      + '<span class="back" id="fbback">◀ THE GAME</span>'
      + '<div class="placeholder"><div class="eyebrow">the postbox</div>'
      + esc(err.message) + '</div></div>';
  }
}

/* the composer — the new-feedback form and every chat's reply box */
function fbComposer(withSubject) {
  return (withSubject
      ? '<input id="fbsub" class="ti" maxlength="80" placeholder='
        + '"subject — what is this about?" style="margin-bottom:8px">'
      : '')
    + '<textarea id="fbbody" class="ti" maxlength="4000" placeholder="'
    + (withSubject
        ? 'tell the wardens — what happened, what you loved, what broke…'
        : 'write back…') + '"></textarea>'
    + '<div class="fbthumbs" id="fbthumbs"></div>'
    + '<div class="savebar" style="margin-top:8px">'
    + '<button class="btn" id="fbattach">+ SCREENSHOT</button>'
    + '<button class="btn" id="fbsend">SEND ▸</button></div>'
    + '<input type="file" id="fbfile" accept="image/*" multiple hidden>'
    + '<div class="deskmsg" id="fbnote"></div>';
}
function fbMsg(text) {
  const el = document.getElementById('fbnote');
  if (el) { el.textContent = text; el.className = 'deskmsg bad'; }
}
function fbThumbs() {
  const t = document.getElementById('fbthumbs');
  if (!t) return;
  t.innerHTML = fbDraft.map((a, i) =>
    '<span class="twrap"><img src="data:' + a.mime + ';base64,' + a.data
    + '"><button class="tx" data-i="' + i + '">✕</button></span>')
    .join('');
}
/* screenshots shrink client-side: ≤1400px JPEG, so even the HMAC
   door's signed JSON bodies stay small */
function fbShrink(file) {
  return new Promise((res, rej) => {
    const img = new Image();
    img.onload = () => {
      const scale = Math.min(1, 1400 / Math.max(img.width, img.height));
      const c = document.createElement('canvas');
      c.width = Math.max(1, Math.round(img.width * scale));
      c.height = Math.max(1, Math.round(img.height * scale));
      c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
      URL.revokeObjectURL(img.src);
      res(c.toDataURL('image/jpeg', 0.85).split(',')[1]);
    };
    img.onerror = rej;
    img.src = URL.createObjectURL(file);
  });
}
async function fbAddFiles(files) {
  for (const f of files) {
    if (fbDraft.length >= 3) { fbMsg('three screenshots at most'); break; }
    try { fbDraft.push({mime: 'image/jpeg', data: await fbShrink(f)}); }
    catch (e) { fbMsg('that file is not an image'); }
  }
  fbThumbs();
}
function fbWireComposer(send) {
  const file = document.getElementById('fbfile');
  document.getElementById('fbattach').addEventListener('click',
    () => file.click());
  file.addEventListener('change', () => {
    fbAddFiles([...file.files]); file.value = '';
  });
  document.getElementById('fbthumbs').addEventListener('click', (e) => {
    const x = e.target.closest('.tx');
    if (x) { fbDraft.splice(+x.dataset.i, 1); fbThumbs(); }
  });
  document.getElementById('fbsend').addEventListener('click', send);
}
async function fbSendNew() {
  if (fbBusy) return;
  fbBusy = true;
  try {
    await call('/pane/feedback/create', {
      subject: (document.getElementById('fbsub').value || '').trim(),
      body: (document.getElementById('fbbody').value || '').trim(),
      attachments: fbDraft.map(a => ({mime: a.mime, data: a.data}))});
    fbDraft = [];
    fbLoad();
  } catch (err) {
    if (err.message !== 'auth') fbMsg(err.message);
  } finally { fbBusy = false; }
}
async function fbSendReply() {
  if (fbBusy) return;
  fbBusy = true;
  try {
    await call('/pane/feedback/reply', {
      id: fb.id, as_admin: fb.asAdmin,
      body: (document.getElementById('fbbody').value || '').trim(),
      attachments: fbDraft.map(a => ({mime: a.mime, data: a.data}))});
    fbDraft = [];
    fbLoad();
  } catch (err) {
    if (err.message !== 'auth') fbMsg(err.message);
  } finally { fbBusy = false; }
}

function fbRenderList(d) {
  let h = '<span class="back" id="fbback">◀ THE GAME</span>';
  h += '<div class="panel"><div class="eyebrow">the postbox — write '
    + 'to the wardens</div>'
    + '<div class="faint" style="margin-bottom:8px">a bug, an idea, a '
    + 'grievance — file it here; replies land right back in this '
    + 'box.</div>' + fbComposer(true) + '</div>';
  h += '<div class="panel"><div class="eyebrow">your feedback</div>'
    + (d.threads.length ? d.threads.map(t =>
        '<div class="fbrow" data-id="' + t.id + '"><span class="fbsub">'
        + esc(t.subject)
        + (t.unread ? ' <span class="fbnew">● ' + t.unread
            + ' NEW</span>' : '')
        + '<div class="sub">' + (t.last_sender === 'admin'
            ? 'the wardens answered' : 'you wrote') + ' · '
        + fbWhen(t.last_msg_at) + '</div></span>'
        + '<span class="dim">▸</span></div>').join('')
      : '<div class="faint">nothing filed yet</div>') + '</div>';
  fbPanel.innerHTML = '<div class="fbwrap">' + h + '</div>';
  fbThumbs();
  fbWireComposer(fbSendNew);
}

function fbRenderAdmin(d) {
  let h = '<span class="back" id="fbback">◀ THE GAME</span>';
  h += '<div class="panel"><div class="eyebrow">the admin desk — '
    + 'all feedback, freshest first</div>'
    + (d.threads.length ? d.threads.map(t =>
        '<div class="fbrow" data-id="' + t.id + '"><span class="fbsub">'
        + esc(t.author) + ' — ' + esc(t.subject)
        + (t.unread ? ' <span class="fbnew">● NEW</span>' : '')
        + '<div class="sub">' + esc(t.last_line) + '</div>'
        + '<div class="sub">' + (t.last_sender === 'player'
            ? 'awaiting reply' : 'answered') + ' · '
        + fbWhen(t.last_msg_at) + ' · ' + esc(t.tenant) + '/'
        + esc(t.player) + '</div></span>'
        + '<span class="dim">▸</span></div>').join('')
      : '<div class="faint">the box is empty — no feedback yet</div>')
    + '</div>';
  fbPanel.innerHTML = '<div class="fbwrap">' + h + '</div>';
}

function fbRenderThread(d) {
  const mine = fb.asAdmin ? 'admin' : 'player';
  let h = '<span class="back" id="fbback">◀ '
    + (fb.asAdmin ? 'ALL FEEDBACK' : 'THE POSTBOX') + '</span>';
  h += '<div class="panel"><div class="eyebrow">' + esc(d.subject)
    + (fb.asAdmin ? ' — ' + esc(d.author) + ' <span class="faint">('
        + esc(d.tenant) + '/' + esc(d.player) + ')</span>' : '')
    + '</div>';
  d.messages.forEach(m => {
    h += '<div class="fbmsg ' + (m.sender === mine ? 'me' : 'them') + '">'
      + '<div class="meta">' + esc(m.author)
      + (m.sender === 'admin' ? ' <span class="tag">◆ WARDEN</span>'
          : '')
      + ' · ' + fbWhen(m.at) + '</div>'
      + '<div class="mbody">' + esc(m.body) + '</div>'
      + (m.attachments.length ? '<div class="fbatt">'
          + m.attachments.map(a => '<img data-att="' + a.id
            + '" alt="screenshot">').join('') + '</div>' : '')
      + '</div>';
  });
  h += fbComposer(false) + '</div>';
  fbPanel.innerHTML = '<div class="fbwrap">' + h + '</div>';
  fbThumbs();
  fbWireComposer(fbSendReply);
  [...fbPanel.querySelectorAll('img[data-att]')].forEach(async img => {
    try { img.src = await fetchBlob('/pane/feedback/att/' + img.dataset.att); }
    catch (e) { img.alt = 'screenshot lost'; }
  });
  fbPanel.scrollTop = fbPanel.scrollHeight;   // the chat opens at its end
  fbPoll();          // opening marked the thread read — repaint badges
}

/* one delegated ear: back walks up, rows open, screenshots enlarge */
fbPanel.addEventListener('click', (e) => {
  if (e.target.closest('#fbback')) {
    if (fb.id) { fb.id = 0; fbDraft = []; fbLoad(); } else fbClose();
    return;
  }
  const row = e.target.closest('.fbrow[data-id]');
  if (row) { fb.id = +row.dataset.id; fbDraft = []; fbLoad(); return; }
  const img = e.target.closest('.fbatt img');
  if (img && img.src) {
    fbLight.innerHTML = '<img src="' + img.src + '">';
    fbLight.classList.add('open');
  }
});

if (token || WEB) loadScene();
})();
"""


def render_pane(api_base: str = _API, web: bool = False) -> str:
    """The pane. Defaults are the Luna iframe (bearer token, postMessage
    auth); web=True is linearascent.net/play — same HTML, cookie auth,
    401 walks back to the site's door. 005: one pane, two doors."""
    title = "<title>LINEAR ASCENT</title>" if web else ""
    spk = icons.icon_data_url("speaker")
    note = icons.icon_data_url("note")
    post = icons.icon_data_url("postbox")
    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">{title}
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
<div class="sndbar">
  <button id="sndfx" class="sndbtn" aria-pressed="true"><span class="sndico"
    style="mask-image:url('{spk}');-webkit-mask-image:url('{spk}')"
    aria-hidden="true"></span><span class="sndlab">sound on</span></button>
  <button id="sndmus" class="sndbtn" aria-pressed="true"><span class="sndico"
    style="mask-image:url('{note}');-webkit-mask-image:url('{note}')"
    aria-hidden="true"></span><span class="sndlab">music on</span></button>
  <button id="fbbtn" class="sndbtn"><span class="sndico"
    style="mask-image:url('{post}');-webkit-mask-image:url('{post}')"
    aria-hidden="true"></span><span class="sndlab">feedback</span><span
    id="fbbadge" class="fbbadge" hidden></span></button>
  <button id="fbadmin" class="sndbtn" hidden><span class="sndico"
    style="mask-image:url('{post}');-webkit-mask-image:url('{post}')"
    aria-hidden="true"></span><span class="sndlab">admin</span><span
    id="fbabadge" class="fbbadge" hidden></span></button>
</div>
<div id="fbpanel"></div>
<div id="fblight"></div>
<script>{INTERACT_JS}</script>
<script>{_JS.replace("__API__", api_base)
           .replace("__WEB__", "true" if web else "false")
           .replace("__SWAP_JS__", SWAP_JS)
           .replace("__COIN__", icons.icon_data_url("coin"))}</script>
<script>{TIP_JS}</script>
<script>{SFX_JS}</script></body></html>"""
