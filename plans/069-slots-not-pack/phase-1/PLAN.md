# Phase 1 — Slot map + doc migration (engine only, no behaviour change)

## Goal
The player doc knows seven slots. Weapons keep their own hone, `held`
order is stable, `quiver`/`oil` are keyed per weapon slug, `gear.charm`
exists (empty, locked). Every fight number and every rendered card is
identical to 0.90.0.

## Steps
- `economy.py`: `Slot(key, side, row, kinds, lock)`; `SLOTS` in map
  order: charm, armor, shoes | shield, weapon, weapon2, weapon3.
  `slot_locked(p, key) -> str|None` (lock text or None):
  weapon2 → `p["slots"]<2` "School — second grip (60 XP · ◈30)";
  weapon3 → `p["slots"]<3` "School — third grip, level 8";
  charm → `not p["charm_slot"]` "School — charm pouch, level 9".
  `CHARM_KINDS` = {luck_charm} ∪ APOTHECARY heals ∪ RELICS − QUIVER_SLUGS
  − {weapon_oil}. `hone_key(slot, slug)`: `"weapon:"+slug` for weapons.
- `state.py`: `new_player`: `gear.charm=None`, `charm_slot=False`,
  `quiver={}`, `oil={}` (dict), `charm_dur=0`. `ensure_current` v11:
  `hone["weapon"]` → `hone["weapon:"+gear["weapon"]]`; int `oil` →
  `{lead: n}`; `setdefault` all new keys; held cap as today but no
  reorder — repair only `gear["weapon"] not in held → held[0]`.
  `hone_level(p, slot)` reads the per-weapon key for `slot=="weapon"`.
- `combat._promote_held`: no reorder, just `gear["weapon"]=slug` +
  durability swap as today. `_player_hit` reads `p["oil"].get(lead)`.
- Every reader of `p["oil"]` as int, `hone["weapon"]` and `held[0]`
  updated (grep list in execution).

## Verification
- pytest: 0.90.0 fixture doc → v11 → same `atk/dfs/max_hp`; honed
  sword + bow leads → bow bonus without hone; `attack_<slug>` leaves
  `held` order unchanged; render of every scene in the golden set is
  byte-identical to HEAD.

## Rollback
`git revert`; v11 keeps legacy `hone["weapon"]` and int-oil untouched
(copied, not moved) until phase 6, so 0.90.0 engine reads the doc.
