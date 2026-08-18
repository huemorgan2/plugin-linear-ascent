# Phase 5 — UI: the gear map

## Goal
The profile card shows the portrait between two slot columns (3 left,
4 right), all seven slots always drawn in their three states, the pack
grid beneath, and the card scales (desktop and ≤520px). Arena HUD
shows the charm and per-weapon ATK.

## Steps
- `core._pack_strip`: emit `scene.slots` = 7 dicts `{key, side, row,
  state: locked|empty|filled, lock_text, slug, icon, count, dur, acts}`
  from `economy.SLOTS`; pack cells lose the worn/hand buckets.
- `render._profile_html`: `.gearmap` grid `auto 1fr auto`; left/right
  `.slotcol` (flex column, gap 6px); portrait fills the middle and
  stretches to the column height; `_inventory_html` becomes pack-only.
- `render._slot_cell`: `.slot.locked` (`border:2px solid #555;
  background:#222`, lock glyph centred, `data-tiph`=lock_text),
  `.slot.empty` (`border:2px dotted`), filled as today; charm potion
  `×1`.
- `SCENE_CSS`: `.gearmap`, `.slotcol`, `.slot.locked`, `.slot.empty`
  dotted, mobile: 48px slots, portrait min-height 200px; `.slotgrid`
  full width below.
- Popover: slot click → acts from phase 4 (`unequip_*` first); pack
  click → `wear_*` first; greyed rows carry the refusal as tip.
- `arena.py` payload `me.charm`, `me.weapons[].atk`; `arena3d.js` HUD:
  charm icon under player HP, tile shows its ATK.
- icons: `lock`, `charm` (pouch), `potion`.

## Verification
- render tests: 7 slots always present; states by doc; lock text; pack
  count label; golden HTML for locked/empty/filled trio.
- Dojo (phase 6) covers the visual pass and mobile.

## Rollback
`git revert`; `scene.slots` is an added Scene field, unknown to old
clients (wire law).
