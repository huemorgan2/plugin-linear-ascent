# 067 — Labs, and the first Labs feature: the Arena (turn-based 3D fight)

## Problem (roy, 2026-08-18)
Two asks, one plan:

1. **Labs.** A flask icon on the bottom bar. On/off. Inside: features
   that can be switched on and off for testing on the live game
   without touching what works. Design them isolated so a promoted
   feature deletes the old path and a dropped one deletes itself.
2. **The Arena** — first Labs feature, floors 6 and 7 only. Today a
   fight is a card: creature close-up, one text line per round, both
   blows in one breath. Wanted: after the first strike the banner
   becomes the same 3D setting as the kill scene, but persistent and
   turn-based — Pokémon-style. HUD over the scene (monster top-right,
   player top-left), icon options at the foot of the box with the key
   number and an [i], the 3D playing every beat separately: player
   strikes / misses / is blocked, everyone returns to place, THEN the
   monster answers. Floating "-XX HP" / "BLOCKED N" / "MISS" over the
   heads. Explanation lines accumulate under the scene. Distance =
   the player walks backward. Frame 320×300 (was 320×112) — same 3D
   characters, remade backgrounds. Every other floor, and every player
   with Labs off, sees today's fight unchanged.

## Root cause / why it is not a patch
- The bar has no per-player server setting today (sound is
  localStorage). A Labs switch must be a PLAYER flag so the ENGINE
  can branch (the arena changes what the card carries).
- `combat._resolve_round` resolves the whole round in one call and
  narrates it in one string. The numbers are right; the 3D needs them
  as an ORDERED SCRIPT (who / what / how much / hp after), which no
  layer produces today.
- `fight3d.js` is a 320×112 one-shot finisher keyed to a kill card. It
  has every primitive the arena needs (rigs, monsters, effects, one-
  color post) but as module-private singletons at a fixed size.

## The two questions (answered here, and in chat)

**Q1 — does DEF come from things not in hand? Can pack items raise DEF?**
No. `state.dfs(p) = economy.player_def(level, shield_bonus, armor_bonus,
race)` = `round(2·1.3^(level−1)) + shield + armor` (giant: armor ×1.05).
The two bonuses come only from the WORN slots `p["gear"]["shield"]` and
`p["gear"]["armor"]` (`state.gear_bonus`), honed by `honed_bonus`,
halved while broken. Nothing in `p["inventory"]` (the pack) or in
`p["held"]` (side-arms) adds DEF. Shoes add SPEED only (dodge / flee /
close). Armor additionally adds `4 × armor_bonus` max HP. So the
"in hand" row (weapon + shield) plus the worn armor row is the whole
defence; the pack is inert.

**Q2 — what is total attack made of? Two weapons combined?**
`state.atk(p) = round(3·1.3^(level−1)) + weapon_bonus`, where
`weapon_bonus` is the LEAD hand only — `p["gear"]["weapon"]`, honed,
halved while broken. Held side-arms are NOT summed: each held weapon is
its own attack row (`attack_<slug>`), and choosing it PROMOTES it to
the lead hand (`_promote_held`) and swings with that weapon alone. A
second weapon in hand does not strengthen the strike; it widens the
choice (blade vs fly = 0, bow vs armoured = ×0.15, staff vs resist =
×0.15 — the triangle is per weapon in hand). The strike itself is
`raw ∈ [floor(rank)·ATK, ATK]` with `floor = (30+4·rank)%`, then
`typed_damage_048` (staff ignores DEF; blade/bow lose DEF//2), ×oil,
×mastery, ×quiver arrow, ×bow gap. Hit chance is the hand: miss% =
`max(0, 25 − 2.5·rank)` on the weapon's training path.

The arena HUD shows exactly this: ATK = base + lead weapon; DEF =
base + shield + armor; each held weapon is its own option tile.

## Design — isolation contract
- **`p["labs"]`** — a dict of feature flags on the player doc,
  `{"arena": False}` by default (self-heal in `ensure_current`, no
  version bump). One module `engine/labs.py` owns the flag names,
  the floor gates and the Labs card. Promoting a feature = flip the
  default, delete the old branch, delete the flag; dropping it =
  delete `labs.py` entries + the feature module.
- **`engine/arena.py`** — the arena engine is a RECORDER, not a second
  combat engine. Combat resolves exactly as today (same rolls, same
  numbers, same text). At the choke points (`_player_hit`,
  `_monster_hit`, the miss branch, `_advance_chase`, the range moves,
  run) one `arena.record(p, ev)` call appends an event when the arena
  is on for this player+floor. `fight_scene` / `_victory` / `_death`
  attach `Scene.arena = arena.payload(...)` — top-level Scene field
  (wire law), unknown to old clients, dropped safely.
- **render.py** — when `scene.arena` is set the fight card renders the
  ARENA VARIANT: a bare 320×300 banner slot carrying `data-arena`,
  option TILES (icon + `[n] LABEL` + `[i]`), and the log. Every other
  card is byte-identical to today (test).
- **JS** — `fight3d.js` keeps its kill-scene behaviour and its module
  observer untouched; it grows `export`s of its primitives (loaders,
  `buildPlayer`, `tripoMonster`, effects, registries) and a
  parametric `createStage(W,H)`. New `arena3d.js` (own module, own
  canvas, own observer on `.card[data-arena]`) builds the 320×300
  stage, keeps the GL scene alive across card swaps, plays the event
  script beat by beat, draws HUD/floating text/log as HTML over the
  canvas. If WebGL is dead the card still works — options are real
  buttons, the log is real text; only the picture is missing.
- **Backgrounds** — new sheets `backgrounds300/<id>.png` (320×7200 =
  24 × 320×300) for the 14 floor-6/7 creatures, from fresh 1:1 Gemini
  stills cropped to 16:15. The 320×112 sheets stay for the kill scene.
- **Keys** — the pane's `1..9` handler clicks the Nth visible
  `button.opt`; the arena tiles ARE `button.opt`, ordered as
  `scene.options`, so `[1] BOW` is key 1 with no new key code.

## Turn script (the contract JS plays)
`Scene.arena = {v:1, floor, foe:{id,name,hp,hp_max,def,spd,atk,type,
armoured,resist_tier,breed,specimen,tint}, me:{hp,hp_max,def,spd,atk,
race,line,weapons:[{slug,name,path,lead}],shield,armor,broken:[…]},
range:{state,gap}, events:[…], phase:"opener"|"round"|"victory"|"death"|
"fled", log:[…]}`.
Events, in order of occurrence:
- `{who:"me", kind:"strike", path, weapon, outcome:"hit"|"miss"|"glance"|"blocked", dmg, blocked, foe_hp, why, text}`
- `{who:"foe", kind:"strike", outcome:"hit"|"blocked"|"dodged"|"netted"|"veiled"|"none", dmg, blocked, raw, me_hp, riposte, text}`
- `{who:"me", kind:"move", what:"close_in"|"open"|"back"|"run_fail"|"run_ok"|"stand"|"wall", gap, text}`
- `{who:"foe", kind:"move", what:"close"|"advance"|"hold", gap, range, text}`
- `{who:"foe", kind:"die"}` / `{who:"me", kind:"die"}` / `{kind:"note", text}`
`text` is the human line that lands under the scene ("Player misses
magic attack because skill level is 4 of 10.").

## Fix — phases
1. **Labs** — flag, `labs.py`, bar flask icon, Labs card with the
   arena switch (floors 6–7 note). `phase-1/PLAN.md`.
2. **Arena engine + card** — `arena.py`, combat hooks, `Scene.arena`,
   render variant, option tiles + icons. `phase-2/PLAN.md`.
3. **Arena 3D** — `fight3d.js` exports, `arena3d.js`, HUD, floating
   texts, turn machine, walk-back, finisher. `phase-3/PLAN.md`.
4. **Backgrounds 320×300** — 14 stills, sheets, loader. `phase-4/PLAN.md`.
5. **Tests + release** — pytest, dojo scenario, bump 0.90.0, vendor,
   commit. Not deployed unless roy says so.

## Verification (whole plan)
- Plugin suite green (minus the 6 pre-existing failures noted in 066).
- New tests: labs flag round-trip / self-heal; labs card toggles;
  arena OFF ⇒ fight card HTML identical to HEAD for floors 1–20;
  arena ON floor 5 ⇒ identical; arena ON floor 6/7 ⇒ `data-arena`
  JSON with ordered events whose dmg/hp numbers equal the encounter
  deltas; player-miss event carries rank; blocked event `blocked ==
  raw − dmg`; option tiles carry `[n]` labels and `[i]`; wire law:
  `Scene.from_dict(to_dict())` keeps `arena`, old dict without it
  loads.
- Sheets: 14 × 320×7200 1-bit PNGs; JS loads them by id.
- Dojo: `luna/dojo/tests/labs-arena/scenario.md` walked on local
  8777: flask on bar → Labs → arena on → floor 6 hunt → opener shows
  the close-up → first strike → 3D arena 320×300 → tiles → miss
  jitter → -XX HP → distance walk-back → kill → banish → floor 5
  unchanged → arena off → floor 6 unchanged.

## Rollback
Each phase is one commit; `git revert` in reverse order. The player
flag `labs.arena` is inert without `arena.py` hooks (a doc with the
key loads on any older engine — unknown keys are kept). Sheets are
additive files. `fight3d.js?v=` bump reverts with the file.
