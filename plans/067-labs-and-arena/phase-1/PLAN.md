# Phase 1 — Labs: the flag, the flask, the card

## Goal
A player can open Labs from the bottom bar and switch the Arena on or
off; the choice persists on the player doc and survives reload. Nothing
else changes for anyone.

## Steps
- `engine/state.py`: `new_player` gets `"labs": {}`; `ensure_current`
  self-heals `p.setdefault("labs", {})`.
- `engine/labs.py` (new): `FEATURES = {"arena": Feature(name, blurb,
  floors={6,7})}`, `enabled(p, key, floor=None)`, `set_flag(p, key,
  on)`, `labs_scene(p)` (the card: one row per feature, "on"/"off",
  option ids `labs_toggle_<key>`, `labs_back`), `is_labs_option(oid)`.
- `engine/core.py`: `_dispatch` routes `labs`, `labs_toggle_*`,
  `labs_back` before location dispatch; the Labs card is reachable
  from anywhere except mid-encounter (then a refusal). `apply_choice`
  accepts these ids on any scene (they are not in `scene.options`).
- `icons.py`: `flask` grid (Erlenmeyer).
- `pane.py`: `#labsbtn` in `.sndbar` after feedback; click →
  `window.__laAct('labs')`; the button reads `on` when any feature is
  on (`data-labs` on the card root, painted by `__laScene`).
- `render.py`: `data-labs="arena"` root attr listing enabled features.
- tips: `labs_toggle_arena` tip text.

## Verification
- `tests/test_067_labs.py`: new doc has `labs == {}`; old doc heals;
  `labs` option returns the card with `labs_toggle_arena` (off);
  toggling flips the flag and the row text; `labs_back` returns to the
  scene; mid-fight `labs` refuses; render_pane contains `#labsbtn` and
  the flask data URL.

## Rollback
Revert the commit. A doc carrying `labs` loads on the previous engine
(unknown key kept, ignored).

## Execution status
Done 2026-08-18 — commit ab7767a. `p["labs"]` dict + `engine/labs.py`, flask on the bar (`#labsbtn`, reads "labs"/"labs on" from `data-labs`), Labs card with the arena switch. Dojo 0036: switch off→ON→off round-trips in UI and DB (`doc->'labs'->>'arena'`).
