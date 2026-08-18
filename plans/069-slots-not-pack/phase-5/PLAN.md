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

## Execution status
Executed 2026-08-18. Engine: `Scene.slots` (wire field, `to_dict`/
`from_dict`), `core._slot_map(p)` → 7 dicts `{key, side, row, label,
kind, state locked|empty|filled, lock_text, slug, name, icon, count, …
equipped/stat/dur/lead/charm_dur/acts/why}` set on every stamped scene;
`_pack_strip` is pack-only (worn/held/empty_slot cells gone).
Render: `.profile` = `.gearmap` (`.slotcol.left` charm·armour·boots ·
`.pwrap` portrait · `.slotcol.right` shield·weapon·weapon 2·weapon 3)
+ `.pcol` meters; the pack grid rides under it full width. Slot states:
locked = `#222` box, `#555` 2px border, lock glyph, hover carries the
lock text ("School, level 9 …"); empty = 2px dotted, hover names what
goes there; filled = the item cell with the phase-4 acts (click → "Move
to the pack"), lead weapon gold-bordered. `wirePack` wires
`.gearmap .item`; `sizePortrait` sets the figure to the taller slot
column (258px desktop / 210px ≤520px, 48px slots on phone). Tips for
medgel/trauma kit/tonic/luck charm rewritten for the pouch. Arena:
`me.charm {slug,name,dur}`, `weapons[].atk`, `tile().atk` on attack
rows → `.aatk` corner on the tile, `.apouch` line under the climber's
HP; drink_medgel/drink_trauma_kit tile art. Screenshots (Playwright,
760 and 420 px): both columns, figure between, pack under; click on a
gear-map cell opens the popover with "Move to the pack"; pack medgel
offers "Use a Medgel" + "Set in pouch". Tests: 6 new render/arena
tests in test_069; test_012/014/017_durability/027/031/049_1/049_2
moved from the hand row to `scene.slots`. Suite: 1293 passed, 6
pre-existing failures.

Note: the phase-4 code (core.py/tests) was left out of commit b7831fb
by mistake (only its PLAN.md landed); it is committed with this phase.
