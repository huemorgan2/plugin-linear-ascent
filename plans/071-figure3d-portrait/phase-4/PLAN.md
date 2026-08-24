# Phase 4 — hover highlight + worn overlay

## Goal
Hovering a filled slot icon tints that piece on the climber. Armour,
boots, charm, shield, and every held weapon attach from the catalog
(or family fallback). Swapping a weapon in the slots changes the hold.

## Steps
- JS: each attached mesh tagged `userData.slot = key`.
- `#game` mouseover on `.gearmap [data-key]` sets a highlight colour
  on matching meshes (weapon=gold, charm=cyan, armor=text-ink,
  shoes=orange, shield=violet). Post shader passes saturated pixels
  through (the allowed colour exception).
- Armor / boots / charm / shield / focus attach using the hold table.
- Payload already lists worn slugs; no engine change.

## Verification
- Wear cobbled boots → two boot meshes on the feet.
- Set luck charm → pendant on the neck.
- Hold a bow and a sword → bow on the back, sword on the hip.
- Hold a staff → in the right hand.
- Hover the armour slot → the chest piece goes coloured; leave → 1-bit.

## Rollback
Revert the JS. Meshes stay; highlight dies.

## Execution status
2026-08-24 — Implemented in the working tree: attached meshes carry their
slot key, the post pass preserves saturated highlight ink, and the hold table
handles weapons, overlays, two boots, and duplicate blades/staffs. Visual
acceptance is still pending an authenticated browser player: local worldd
offers Gmail-only account creation and its OAuth flow fails locally.
