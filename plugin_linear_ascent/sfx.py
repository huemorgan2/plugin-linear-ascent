"""042 — the 8-bit sound layer. 043 — the score.

Every effect and every bar of music is synthesized in the browser:
square waves, sample-held noise and a hard 8-bit quantize, rendered into
AudioBuffers at 22,050 Hz. Same doctrine as the art — zero files, zero
network, the whole voice of the game lives in this one script.

The score (043) is written the way the old sound chips forced it: three
voices — a melody, an active bassline, and rapid "fake chord" arpeggios
that fake harmony a monophonic channel can't hold — over noise-channel
percussion. One long looping track per meaningful room, keyed off the
card's data-loc (Scene.location on the wire), with combat and the warden
fight overriding whatever room the player stood in:

  town      Roothollow square + street rooms — warm C-major folk walk
  lodge     the Lodge (and turning in)       — a 6/8 dorian jig
  vault     the Vault + grants desk          — sparse E-minor music box
  guildhall the Guildhall + faction hall     — stately G-major fanfare
  smithy    the Forge + pawn shop            — E-minor riff, anvil ring
  arcane    the Arcanum + Medlab             — lydian shimmer arps
  dungeon   the floors, keeps, anywhere else — the original dark loop
  combat    any wilds fight                  — driving A-harmonic-minor
  warden    the warden fight                 — half-step bass + tritone

Tracks crossfade on scene change. Hooks:
  window.__laSfx(name, delay)  — one effect, if SOUND is on
  window.__laScene(d, root)    — reads a fresh card: picks the track,
                                 fires event stings, and the weapon-
                                 flavored hit (plus the warden boom)
  the sound bar                — #sndfx / #sndmus buttons, prefs in
                                 localStorage (la_snd_*), default ON.
"""

from __future__ import annotations

# Plain string on purpose: real braces everywhere — no f-string doubling.
SFX_JS = r"""
(() => {
const SR = 22050;
let ctx = null, fxGain = null, muGain = null, muSrc = null, muSrcG = null;
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
    muGain = ctx.createGain(); muGain.gain.value = 0.5;
    muGain.connect(ctx.destination);
  }
  if (ctx.state === 'suspended') ctx.resume();
  return true;
}

/* ── the synth ─────────────────────────────────────────────────────── */
const sqw = (f, t, d) => (t * f) % 1 < (d || 0.5) ? 1 : -1;
const env = (i, n, d) =>
  Math.max(0, 1 - Math.max(0, i / n - (1 - d)) / d);
const M = m => 440 * Math.pow(2, (m - 69) / 12);   // midi -> Hz
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
function quant(o) {
  for (let i = 0; i < o.length; i++)   // the 8-bit quantize IS the timbre
    o[i] = Math.round(Math.max(-1, Math.min(1, o[i])) * 127) / 127;
  return o;
}
function render(dur, fn) {
  const n = (SR * dur) | 0, o = new Float32Array(n);
  for (let i = 0; i < n; i++) o[i] = fn(i, n, i / SR);
  return quant(o);
}
/* additive baker: events are {t, dur, amp, decay} plus either
   {f, duty} (square) or {noise: hold} — O(event samples), so a
   half-minute track with hundreds of notes bakes in a blink */
function bake(ev, total) {
  const n = (SR * total) | 0, o = new Float32Array(n);
  for (const e of ev) {
    const s0 = (e.t * SR) | 0, ln = Math.max(1, (e.dur * SR) | 0);
    const dec = e.decay == null ? 0.9 : e.decay, a = e.amp || 0.5;
    if (e.noise) {
      const w = nz((s0 % 97) + 3);
      for (let i = 0; i < ln && s0 + i < n; i++)
        o[s0 + i] += w(e.noise) * env(i, ln, dec) * a;
    } else {
      const d = e.duty || 0.5, f = e.f;
      for (let i = 0; i < ln && s0 + i < n; i++) {
        const t = (s0 + i) / SR;
        o[s0 + i] += ((t * f) % 1 < d ? 1 : -1) * env(i, ln, dec) * a;
      }
    }
  }
  return quant(o);
}
const notes = bake;

/* ── the songwriter ────────────────────────────────────────────────── */
/* a hand-authored voice: pat items are null (rest), a midi number, or
   [midi, slots] for a held note; each item advances one slot */
function line(ev, step, pat, o, t0) {
  o = o || {}; t0 = t0 || 0;
  pat.forEach((p, k) => {
    if (p === null) return;
    const m = Array.isArray(p) ? p[0] : p;
    const len = Array.isArray(p) ? p[1] : 1;
    ev.push({t: t0 + k * step, f: M(m), dur: step * len * (o.gate || 0.92),
      amp: o.amp || 0.09, duty: o.duty,
      decay: o.decay == null ? 0.9 : o.decay});
  });
}
const oct = (pat, d) => pat.map(p => p === null ? null
  : Array.isArray(p) ? [p[0] + d, p[1]] : p + d);
/* noise-channel percussion: k kick, h hat, s snare, a anvil, t tritone */
function drums(ev, step, pat, amp, t0) {
  t0 = t0 || 0;
  Array.prototype.forEach.call(pat, (c, k) => {
    const t = t0 + k * step;
    if (c === 'k') ev.push({noise: 14, t, dur: 0.09, amp: amp * 1.3,
      decay: 0.95});
    else if (c === 'h') ev.push({noise: 1, t, dur: 0.03, amp: amp * 0.45,
      decay: 0.9});
    else if (c === 's') ev.push({noise: 3, t, dur: 0.09, amp, decay: 0.9});
    else if (c === 'a') { ev.push({f: 1247, t, dur: 0.14, amp: amp * 0.5,
      duty: 0.5, decay: 0.95});
      ev.push({f: 1873, t, dur: 0.12, amp: amp * 0.35, duty: 0.5,
        decay: 0.95}); }
    else if (c === 't') { ev.push({f: M(47), t, dur: 0.16, amp: amp * 0.6,
      duty: 0.25, decay: 0.9});
      ev.push({f: M(53), t, dur: 0.16, amp: amp * 0.45, duty: 0.25,
        decay: 0.9}); }
  });
}
/* bars of [rootMidi, minor?] make the bass + fake-chord arps; the
   melody and drum patterns are authored on top */
function song(cfg) {
  const ev = [], beats = cfg.beats || 4, bar = beats * cfg.beat;
  cfg.bars.forEach((c, i) => {
    const r = c[0], mi = c[1], t0 = i * bar, third = r + (mi ? 3 : 4);
    if (cfg.bass === 'walk')
      line(ev, cfg.beat, [r - 12, r - 5, third - 12, r - 5],
        {amp: cfg.bamp || 0.1, decay: 1}, t0);
    else if (cfg.bass === 'drive')
      line(ev, cfg.beat / 2, [r - 12, r - 12, r, r - 12,
        r - 12, r, r - 12, r - 12],
        {amp: cfg.bamp || 0.09, duty: 0.25, decay: 1}, t0);
    else if (cfg.bass === 'jig')
      line(ev, cfg.beat, [r - 12, null, null, r - 5, null, null],
        {amp: cfg.bamp || 0.1, decay: 1}, t0);
    else if (cfg.bass === 'whole')
      line(ev, bar, [[r - 12, 1]],
        {amp: cfg.bamp || 0.085, gate: 0.98, decay: 1}, t0);
    if (cfg.arp) {
      const tones = [r + 12, third + 12, r + 19, third + 12];
      const st = cfg.beat / 2;
      for (let k = 0; k < beats * 2; k++)
        ev.push({t: t0 + k * st, f: M(tones[k % 4]), dur: st * 0.9,
          amp: cfg.aamp || 0.038, duty: 0.25, decay: 0.85});
    }
    if (cfg.drums) drums(ev, cfg.beat / 2, cfg.drums, cfg.damp || 0.1, t0);
  });
  if (cfg.mel) line(ev, cfg.melStep || cfg.beat, cfg.mel,
    {amp: cfg.mamp || 0.085, decay: cfg.mdecay == null ? 1 : cfg.mdecay,
     duty: cfg.mduty});
  return bake(ev, cfg.bars.length * bar);
}

/* ── the score, one track per room ─────────────────────────────────── */
const TRACKS = {
  /* Roothollow square — a warm folk walk, C major, ~35 s */
  town: () => song({beat: 0.55, bass: 'walk', arp: true,
    bars: [[48,0],[48,0],[53,0],[55,0],[48,0],[57,1],[53,0],[55,0],
           [57,1],[52,1],[53,0],[48,0],[50,1],[57,1],[55,0],[48,0]],
    mel: [64,null,67,64, 62,60,62,null, 64,67,[69,2],null, 67,64,[62,2],null,
          64,null,67,69, [72,2],null,69,67, 69,67,64,62, [60,3],null,null,null,
          69,null,72,69, 67,64,67,null, 65,67,[69,2],null, 64,62,[64,2],null,
          62,null,65,64, 62,60,57,null, 67,65,64,62, [60,4],null,null,null]}),

  /* the Lodge — a 6/8 dorian jig with a second verse up the octave */
  lodge: () => {
    const J = [
      62,64,65, 67,65,64, 62,65,64, [62,3],null,null,
      65,67,69, 71,69,67, 69,65,67, [69,3],null,null,
      74,72,71, 69,71,69, 67,69,67, [65,3],null,null,
      64,65,67, 65,64,62, 60,62,64, [62,3],null,null,
      62,64,65, 67,65,64, 62,65,64, [62,3],null,null,
      69,71,72, 74,72,71, 72,71,69, [67,3],null,null,
      65,67,69, 67,65,64, 62,64,65, 64,62,60,
      [57,3],null,null, [62,6],null,null, null,null,null];
    const B = [[50,1],[53,0],[48,0],[50,1],[50,1],[53,0],[55,0],[50,1],
               [53,0],[55,0],[57,1],[50,1],[48,0],[55,0],[57,1],[50,1]];
    return song({beat: 0.17, beats: 6, bass: 'jig',
      bars: B.concat(B), mel: J.concat(oct(J, 12)), mamp: 0.075});
  },

  /* the Vault — a sparse music box counting coins, E minor, ~29 s */
  vault: () => song({beat: 0.9, bass: 'whole',
    bars: [[52,1],[52,1],[48,0],[55,0],[57,1],[52,1],[47,0],[52,1]],
    drums: '..h...h.', damp: 0.05,
    melStep: 0.45, mduty: 0.125, mamp: 0.07, mdecay: 0.6,
    mel: [76,null,79,null, null,81,null,null,
          79,null,76,null, null,null,71,null,
          72,null,76,null, 79,null,null,null,
          74,null,71,null, null,67,null,null,
          76,null,81,null, null,79,null,null,
          79,76,null,null, 71,null,null,null,
          75,null,71,null, null,null,null,null,
          [76,4],null,null,null, null,null,null,null]}),

  /* the Guildhall — stately G major, drones and a fanfare, ~44 s */
  guildhall: () => song({beat: 0.68, bass: 'whole', arp: true,
    bars: [[55,0],[55,0],[48,0],[50,0],[55,0],[52,1],[48,0],[50,0],
           [55,0],[50,0],[52,1],[48,0],[55,0],[48,0],[50,0],[55,0]],
    mel: [67,71,[74,2],null, [71,2],null,67,69, [72,2],null,74,72,
          [69,2],null,71,69, 67,71,[74,2],null, [76,2],null,74,71,
          72,74,[76,2],null, [74,4],null,null,null,
          67,null,74,null, [69,2],null,74,null, 71,[67,2],null,64,
          72,[76,2],null,72, 67,71,[74,2],null, 72,[74,2],null,71,
          [74,2],null,72,69, [67,4],null,null,null]}),

  /* the Forge & pawn shop — a low riff under the anvil, ~32 s */
  smithy: () => {
    const P = [52,null,55,57, 55,52,null,null, 55,null,59,62,
      [52,2],null,null,null, 50,null,53,57, 48,null,52,55,
      55,57,59,62, [52,3],null,null,null];
    const B = [[52,1],[52,1],[55,0],[52,1],[50,0],[48,0],[55,0],[52,1]];
    return song({beat: 0.5, bass: 'drive', drums: 'k.h.a.h.',
      bars: B.concat(B), mel: P.concat(oct(P, 12)), mamp: 0.06});
  },

  /* the Arcanum & Medlab — lydian shimmer, slow and bright, ~26 s */
  arcane: () => song({beat: 0.8, bass: 'whole', arp: true, aamp: 0.045,
    bars: [[48,0],[50,0],[52,1],[50,0],[48,0],[50,0],[47,1],[48,0]],
    mel: [[72,3],null,null,74, [78,2],null,74,null, [76,2],null,71,null,
          [74,4],null,null,null, 72,null,76,null, [79,2],null,78,74,
          [71,3],null,null,null, [72,4],null,null,null],
    mamp: 0.07}),

  /* the floors and keeps — the original dark loop, doubled to 25.6 s */
  dungeon: () => {
    const bass = [110, 164.81, 87.31, 130.81, 98, 146.83, 110, 82.41,
                  110, 164.81, 87.31, 130.81, 116.54, 98, 92.5, 110];
    const ev = [];
    bass.forEach((f, k) => ev.push(
      {t: k * 1.6, f, dur: 1.56, amp: 0.11, decay: 1.0}));
    const r = prng(77), scale = [440, 523.25, 587.33, 659.25, 783.99];
    for (let slot = 0; slot < 16; slot++) {
      if (r() < 0.6) {
        const f = scale[(r() * scale.length) | 0], t0 = slot * 1.6 + 0.2;
        if (t0 + 1.9 < 25.6) {
          ev.push({t: t0, f, dur: 1.2, amp: 0.07, decay: 1.0});
          ev.push({t: t0 + 0.35, f, dur: 1.0, amp: 0.035, decay: 1.0});
          ev.push({t: t0 + 0.7, f, dur: 0.8, amp: 0.018, decay: 1.0});
        }
      }
    }
    const music = bake(ev, 25.6), w = nz(78);
    return render(25.6, (i, n, t) => {
      // wind LFO in phase at both ends so the loop point is silent
      const lfo = 0.03 + 0.03 * Math.sin(2 * Math.PI * t / 6.4
        - Math.PI / 2);
      return music[i] + w(6) * lfo;
    });
  },

  /* wilds combat — driving A minor, pumping bass, ~26 s */
  combat: () => song({beat: 0.4, bass: 'drive', bamp: 0.1, arp: true,
    aamp: 0.045, drums: 'k.h.s.h.', damp: 0.11,
    bars: [[57,1],[57,1],[53,0],[55,0],[57,1],[57,1],[50,1],[52,0],
           [57,1],[53,0],[55,0],[57,1],[50,1],[52,0],[57,1],[52,0]],
    mel: [69,null,69,71, 72,71,69,67, 65,null,65,67, 69,67,65,64,
          69,null,69,71, 72,74,76,74, 62,64,65,67, [68,2],null,64,null,
          76,null,74,72, 69,null,72,null, 74,72,71,69, [69,2],null,67,69,
          65,67,69,71, [68,2],null,71,68, 69,72,76,72, [64,2],null,68,null],
    mamp: 0.08}),

  /* the warden — half-step bass, tritone stabs, ~32 s */
  warden: () => {
    const P = [64,null,65,null, [64,2],null,null,null, 64,null,65,67,
      [65,2],null,64,null, 64,65,64,62, [59,2],null,64,null,
      63,null,63,64, [64,4],null,null,null];
    const B = [[41,1],[40,1],[41,1],[40,1],[41,1],[40,1],[39,1],[40,1]];
    return song({beat: 0.5, bass: 'drive', bamp: 0.11,
      drums: 'k.k.t.k.', damp: 0.14,
      bars: B.concat(B), mel: P.concat(oct(P, 12)), mamp: 0.065});
  },
};

/* which room hears which track; combat overrides in __laScene */
const LOC2TRACK = {town: 'town', stone: 'town', board: 'town',
  gate: 'town', relay: 'town', fields: 'town', memorial: 'town',
  muster: 'town',
  lodge: 'lodge', sleep_menu: 'lodge', sleeping: 'lodge',
  vault: 'vault', grants: 'vault',
  guildhall: 'guildhall', hall: 'guildhall',
  forge: 'smithy', pawn: 'smithy',
  arcanum: 'arcane', medlab: 'arcane',
  gate_town: 'dungeon', boss_keep: 'dungeon', warden_keep: 'dungeon'};

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
  /* 043: the warden takes the blow — a floor-shaking boom laid under
     the weapon's own sound */
  wboom: () => { const w = nz(31); return render(0.4, (i, n, t) =>
    sqw(55 - 18 * i / n, t, 0.5) * env(i, n, 1.0) * 0.55
    + w(10) * env(i, n, 0.8) * 0.3
    + sqw(1873, t) * env(i, n, 1.0) ** 3 * 0.08); },
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

/* the track deck: one looping source, crossfaded on change */
let curTrack = 'town';
function startTrack(name) {
  if (muSrc) {
    const o = muSrc, og = muSrcG;
    og.gain.setTargetAtTime(0.0001, ctx.currentTime, 0.3);
    o.stop(ctx.currentTime + 1.5);
    muSrc = null;
  }
  const g = ctx.createGain(); g.gain.value = 0.0001; g.connect(muGain);
  const s = ctx.createBufferSource();
  s.buffer = buf('t_' + name, TRACKS[name]);
  s.loop = true; s.connect(g); s.start();
  g.gain.setTargetAtTime(1, ctx.currentTime, 0.4);
  s._name = name; muSrc = s; muSrcG = g;
}
function setTrack(name) {
  if (!TRACKS[name]) name = 'dungeon';
  curTrack = name;
  if (musOn && ctx && muSrc && muSrc._name !== name) startTrack(name);
}
function music(on) {
  musOn = on;
  if (!on) { if (muSrc) { muSrc.stop(); muSrc = null; } return; }
  if (!ensure()) return;
  if (!muSrc) startTrack(curTrack);
}

const KIND = {loot: 'loot', death: 'death', boss: 'boss',
  letter: 'letter', present: 'present', matchup: 'boss'};
let lastBoss = false;
window.__laScene = function (d, root) {
  const card = root && root.querySelector('.card');
  const loc = (card && card.dataset.loc) || '';
  const fight = (card && card.dataset.fight) || '';
  setTrack(fight === 'warden' ? 'warden'
    : fight ? 'combat' : (LOC2TRACK[loc] || 'dungeon'));
  const k = (d && d.event_kind) || '';
  const sting = KIND[k];
  // a warden fight keeps event_kind=boss on every exchange — the sting
  // announces the first card, then yields to the battle track
  if (sting && !(k === 'boss' && lastBoss)) {
    window.__laSfx(sting);
    quietUntil = performance.now() + 900;
  }
  lastBoss = k === 'boss';
  if (root && root.querySelector('.chit')) {
    const dt = (card && card.dataset.dtype) || 'melee';
    if (fight === 'warden') window.__laSfx('wboom');
    window.__laSfx(dt === 'ranged' ? 'ranged'
      : dt === 'magic' ? 'magic' : 'melee',
      fight === 'warden' ? 0.06 : 0);
  }
};

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
