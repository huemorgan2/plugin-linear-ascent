"""042 — the 8-bit sound layer.

Every effect is synthesized in the browser at play time: square waves,
sample-held noise and a hard 8-bit quantize, rendered into AudioBuffers
at 22,050 Hz. Same doctrine as the art — zero files, zero network, the
whole voice of the game lives in this one script. The music is a
seamless 12.8 s dungeon loop (bass ostinato, sparse pentatonic answers
with an echo, wind) built from the same parts.

Hooks (all optional, all guarded by the callers):
  window.__laSfx(name, delay)  — play one effect if SOUND is on
  window.__laScene(d, root)    — read a fresh scene: event_kind stings
                                 (loot/death/boss/letter/present) and the
                                 weapon-flavored combat hit (.chit spans +
                                 the card's data-dtype)
  the sound bar               — #sndfx / #sndmus buttons, wired here,
                                 prefs in localStorage (la_snd_*),
                                 default ON; audio unlocks on the first
                                 gesture as browsers require.

A sting squelches the meter blips for a beat so a loot card doesn't fire
the fanfare AND a coin per meter tween.
"""

from __future__ import annotations

# Plain string on purpose: real braces everywhere — no f-string doubling.
SFX_JS = r"""
(() => {
const SR = 22050;
let ctx = null, fxGain = null, muGain = null, muSrc = null;
const store = {
  get(k, d) { try { const v = localStorage.getItem(k);
    return v === null ? d : v === '1'; } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem(k, v ? '1' : '0'); } catch (e) {} }
};
let sfxOn = store.get('la_snd_sfx', true);
let musOn = store.get('la_snd_music', true);

function ensure() {
  const AC = window.AudioContext || window.webkitAudioContext;
  if (!AC) return false;
  if (!ctx) {
    ctx = new AC();
    fxGain = ctx.createGain(); fxGain.gain.value = 0.6;
    fxGain.connect(ctx.destination);
    muGain = ctx.createGain(); muGain.gain.value = 0.55;
    muGain.connect(ctx.destination);
  }
  if (ctx.state === 'suspended') ctx.resume();
  return true;
}

/* ── the synth ─────────────────────────────────────────────────────── */
const sqw = (f, t, d) => (t * f) % 1 < (d || 0.5) ? 1 : -1;
const env = (i, n, d) =>
  Math.max(0, 1 - Math.max(0, i / n - (1 - d)) / d);
function prng(a) {
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
// sample-held noise: hold is brightness (1 = white, higher = darker)
function nz(seed) {
  const r = prng(seed); let h = 0, c = 0;
  return hold => { if (c-- <= 0) { h = r() * 2 - 1; c = hold; } return h; };
}
function render(dur, fn) {
  const n = (SR * dur) | 0, o = new Float32Array(n);
  for (let i = 0; i < n; i++) o[i] = fn(i, n, i / SR);
  for (let i = 0; i < n; i++)   // the 8-bit quantize IS the timbre
    o[i] = Math.round(Math.max(-1, Math.min(1, o[i])) * 127) / 127;
  return o;
}
// a sum of square-wave note events {t,f,dur,amp,duty,decay}
function notes(ev, total) {
  return render(total, (i, n, t) => {
    let s = 0;
    for (const e of ev) {
      if (t >= e.t && t < e.t + e.dur) {
        const li = i - ((e.t * SR) | 0), ln = (e.dur * SR) | 0;
        s += sqw(e.f, t, e.duty) * env(li, ln, e.decay || 0.9)
          * (e.amp || 0.5);
      }
    }
    return s;
  });
}

/* ── the effects ───────────────────────────────────────────────────── */
const DEFS = {
  click: () => render(0.045, (i, n, t) =>
    sqw(660, t, 0.5) * env(i, n, 0.9) * 0.22),
  coin: () => notes([{t: 0, f: 988, dur: 0.07, amp: 0.4},
    {t: 0.07, f: 1319, dur: 0.2, amp: 0.4}], 0.27),
  spend: () => notes([{t: 0, f: 659, dur: 0.07, amp: 0.32},
    {t: 0.07, f: 494, dur: 0.16, amp: 0.32}], 0.23),
  xp: () => notes([{t: 0, f: 1175, dur: 0.05, amp: 0.28},
    {t: 0.05, f: 1568, dur: 0.12, amp: 0.28}], 0.17),
  heal: () => notes([523.25, 659.25, 783.99].flatMap((f, k) => [
    {t: k * 0.09, f, dur: 0.3, amp: 0.24, decay: 1.0},
    {t: k * 0.09, f: f * 2, dur: 0.3, amp: 0.07, decay: 1.0}]), 0.6),
  hurt: () => { const w = nz(15); return render(0.2, (i, n, t) =>
    sqw(110 - 55 * i / n, t, 0.25) * env(i, n, 0.9) * 0.5
    + w(3) * env(i, n, 0.7) * 0.18); },
  melee: () => { const w = nz(11); return render(0.22, (i, n, t) => {
    const slash = w(1 + ((4 * i / n) | 0)) * env(i, n, 0.85) * 0.55;
    const ring = (sqw(1247, t) + sqw(1873, t) * 0.7)
      * env(i, n, 1.0) ** 2 * 0.12;
    return slash + ring; }); },
  ranged: () => { const w = nz(13); return render(0.24, (i, n, t) => {
    const twang = t < 0.06
      ? sqw(400 - 4500 * t, t, 0.25) * (1 - t / 0.06) * 0.45 : 0;
    return twang + w(2) * Math.sin(Math.PI * i / n) * 0.3; }); },
  magic: () => {
    const r = prng(21), sp = [];
    for (let k = 0; k < 5; k++)
      sp.push({t: 0.04 + k * 0.06,
        f: [1047, 1319, 1568, 1760][(r() * 4) | 0],
        dur: 0.05, amp: 0.2});
    const base = render(0.38, (i, n, t) =>
      sqw(500 + 900 * i / n + Math.sin(t * 45) * 40, t, 0.5)
      * env(i, n, 0.6) * 0.3);
    const s = notes(sp, 0.38);
    return base.map((v, i) => v + s[i]); },
  loot: () => notes([783.99, 987.77, 1174.7, 1568].map((f, k) =>
    ({t: k * 0.08, f, dur: 0.25, amp: 0.32, decay: 0.9})), 0.6),
  death: () => render(0.9, (i, n, t) =>
    sqw(300 * (1 - i / n) + 60, t, 0.5) * env(i, n, 1.0) * 0.42),
  boss: () => notes([{t: 0, f: 98, dur: 0.35, amp: 0.5, duty: 0.25},
    {t: 0.3, f: 92.5, dur: 0.55, amp: 0.5, duty: 0.25}], 0.9),
  letter: () => notes([{t: 0, f: 1047, dur: 0.15, amp: 0.28},
    {t: 0.12, f: 1319, dur: 0.3, amp: 0.22, decay: 1.0}], 0.45),
  present: () => notes([523.25, 659.25, 783.99, 1046.5].map((f, k) =>
    ({t: k * 0.07, f, dur: 0.12, amp: 0.3})), 0.4),
};

/* ── the dungeon loop: seamless 12.8 s ─────────────────────────────── */
function ambience() {
  const DUR = 12.8;
  const bass = [110, 164.81, 87.31, 130.81, 98, 146.83, 110, 82.41];
  const ev = [];
  for (let r = 0; r < 2; r++) bass.forEach((f, k) => ev.push(
    {t: r * 6.4 + k * 0.8, f, dur: 0.78, amp: 0.11, decay: 1.0}));
  const r = prng(77), scale = [440, 523.25, 587.33, 659.25, 783.99];
  for (let slot = 0; slot < 8; slot++) {
    if (r() < 0.6) {
      const f = scale[(r() * scale.length) | 0], t0 = slot * 1.6 + 0.2;
      if (t0 + 1.9 < DUR) {
        ev.push({t: t0, f, dur: 1.2, amp: 0.07, decay: 1.0});
        ev.push({t: t0 + 0.35, f, dur: 1.0, amp: 0.035, decay: 1.0});
        ev.push({t: t0 + 0.7, f, dur: 0.8, amp: 0.018, decay: 1.0});
      }
    }
  }
  const music = notes(ev, DUR), w = nz(78);
  return render(DUR, (i, n, t) => {
    // wind LFO in phase at both ends so the loop point is silent
    const lfo = 0.03 + 0.03 * Math.sin(2 * Math.PI * t / 6.4 - Math.PI / 2);
    return music[i] + w(6) * lfo;
  });
}

/* ── playback ──────────────────────────────────────────────────────── */
const cache = {};
function buf(name, make) {
  if (!cache[name]) {
    const d = make();
    const b = ctx.createBuffer(1, d.length, SR);
    b.copyToChannel(d, 0);
    cache[name] = b;
  }
  return cache[name];
}
let quietUntil = 0;
const METER = {coin: 1, spend: 1, xp: 1, heal: 1, hurt: 1};
window.__laSfx = function (name, delay) {
  if (!sfxOn || !DEFS[name] || !ensure()) return;
  if (METER[name] && performance.now() < quietUntil) return;
  const s = ctx.createBufferSource();
  s.buffer = buf(name, DEFS[name]);
  s.connect(fxGain);
  s.start(ctx.currentTime + (delay || 0));
};
const KIND = {loot: 'loot', death: 'death', boss: 'boss',
  letter: 'letter', present: 'present', matchup: 'boss'};
window.__laScene = function (d, root) {
  const sting = KIND[(d && d.event_kind) || ''];
  if (sting) {
    window.__laSfx(sting);
    quietUntil = performance.now() + 900;  // the sting speaks alone
  }
  if (root && root.querySelector('.chit')) {
    const card = root.querySelector('.card');
    const dt = (card && card.dataset.dtype) || 'melee';
    window.__laSfx(dt === 'ranged' ? 'ranged'
      : dt === 'magic' ? 'magic' : 'melee');
  }
};

function music(on) {
  musOn = on;
  if (!on) { if (muSrc) { muSrc.stop(); muSrc = null; } return; }
  if (!ensure() || muSrc) return;
  const s = ctx.createBufferSource();
  s.buffer = buf('__amb', ambience);
  s.loop = true;
  s.connect(muGain);
  s.start();
  muSrc = s;
}

/* browsers hold audio until a gesture — the first tap opens the tap */
function unlock() {
  if (musOn && !muSrc) music(true);
  else if (ctx && ctx.state === 'suspended') ctx.resume();
}
document.addEventListener('pointerdown', unlock, true);
document.addEventListener('keydown', unlock, true);

/* ── the sound bar ─────────────────────────────────────────────────── */
const bs = document.getElementById('sndfx');
const bm = document.getElementById('sndmus');
if (bs && bm) {
  const paint = () => {
    bs.classList.toggle('off', !sfxOn);
    bs.querySelector('.sndlab').textContent =
      'sound ' + (sfxOn ? 'on' : 'off');
    bs.setAttribute('aria-pressed', sfxOn ? 'true' : 'false');
    bm.classList.toggle('off', !musOn);
    bm.querySelector('.sndlab').textContent =
      'music ' + (musOn ? 'on' : 'off');
    bm.setAttribute('aria-pressed', musOn ? 'true' : 'false');
  };
  bs.addEventListener('click', () => {
    sfxOn = !sfxOn; store.set('la_snd_sfx', sfxOn);
    if (sfxOn) window.__laSfx('click');
    paint();
  });
  bm.addEventListener('click', () => {
    music(!musOn); store.set('la_snd_music', musOn);
    paint();
  });
  paint();
}
})();
"""
