# Phase 2 — Arena engine (recorder) + the arena card

## Goal
On floors 6–7 with `labs.arena` on, every fight Scene carries
`scene.arena` — the ordered event script with the same numbers the
text already says — and the fight card renders the arena variant
(320×300 bare slot, tile options, log). Everywhere else: byte-identical.

## Steps
- `engine/arena.py` (new): `enabled(p, floor)`, `begin(p)` (clear
  `e["_arena"]`), `record(p, **ev)`, `payload(p, floor, phase)` (foe /
  me / range / events / log / option meta), `_why_miss`, `_text_*`.
- `engine/combat.py` hooks (one line each): `resolve_fight_action`
  → `arena.begin`; miss branch → `record(who=me, kind=strike,
  outcome=miss)`; `_player_hit` → `record(kind=strike, outcome=hit|
  glance)`; `_monster_hit` → `record(who=foe, …)`; `_advance_chase` →
  `record(who=foe, kind=move)`; close_in / open_distance /
  create_distance / run / stand / shield_wall → `record(who=me,
  kind=move)`; `fight_scene`, `_victory`, `_death`, run-success →
  `scene.arena = arena.payload(...)`.
- `engine/scene.py`: `arena: dict | None = None` (+ to_dict/from_dict).
- `render.py`: `if scene.arena:` banner slot
  `<div class="banner arena" style="aspect-ratio:320/300">`, root
  `data-arena` JSON; options render as `.opt.atile` (icon + key +
  label + [i]) inside `.arena-opts`; body lines from the previous
  round are NOT repeated (the arena log has them) — `arena.log`
  drawn as `.alog` lines. `_arena_icon(opt_id)` maps
  attack/attack_<slug> → weapon icon (bow/sword/staff), close_in →
  `t_speed`, open_distance/create_distance → `back`, run → `run`,
  stand → `shield`, shield_wall → `shield`, others → gear/relic icon
  or `focus`.
- `icons.py`: `back` (arrow), `run` (figure), `flask` (phase 1),
  `hp` (heart), `def` (shield outline), `spd` (chevrons), `atk`
  (blade) — HUD glyphs used by JS via `data-icons` JSON on the card
  (data URLs), so JS ships no art.
- `economy`-derived HUD facts: `type` sign, `resist_tier`, armoured
  when `def/hp_max ≥ 0.06` or profile type armoured.

## Verification
- `tests/test_067_arena.py`: floor 6, arena on → `s.arena.events`
  order me-strike then foe-strike; `foe_hp` after == `e["hp"]`;
  `me_hp` == `p["hp"]`; miss event has `rank`; blocked ==
  raw − dmg; victory scene has `kind:"die"` last and `kill3d` set;
  floor 5 → `arena is None`; labs off → None; HTML of a floor-6 fight
  with labs off equals HTML with the flag absent; wire round trip.

## Rollback
Revert. Hooks are no-ops when `enabled` is False.

## Execution status
Done 2026-08-18 — commit 14dd4fa (+ 067 phase 3 commit adds `start` to the payload). Recorder hooks in combat choke points, `Scene.arena` top-level field, arena card on floors 6–7 with the flag on; nothing anywhere else (dojo 0036: floor 5 with labs on and floor 6 with labs off both render the regular card).
