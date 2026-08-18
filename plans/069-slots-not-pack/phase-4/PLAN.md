# Phase 4 — Actions: wear into a slot, move to the pack

## Goal
Every slot item can go to the pack (or is refused with the exact
reason); every wearable pack item goes to its slot with the level gate
enforced.

## Steps
- `core.pack_actions` / `_pack_use`: `unequip_<slotkey>` for each
  filled slot: mid-fight → refuse; `not pack_can_take` → "Pack full
  (n/n). Sell or drop something, or buy a bigger pack at the forge.";
  last weapon → "You keep one blade in hand."; success moves slug (and
  its `durability` → `durability_pack`); a bow's quiver returns to the
  pack with it (capacity counted); oil on that weapon is lost (note
  line "the oil dries on the shelf").
- `wear_<slug>`: target = `SLOTS` by kind; weapon → first empty
  weapon slot else replaces lead (capacity check first); charm →
  requires `charm_slot`; add level gate (`rung_player_level_req`, shoe
  `level`) with "🔒 level N" refusal; labels "Wear" / "Hold" / "Set in
  pouch".
- Every refusal is a `shard_note` line the pane already paints red.

## Verification
- pytest: pack 6/6 + `unequip_armor` → refusal text, doc unchanged;
  pack 5/6 → armour in pack, `gear.armor=None`, DEF drops; wear shoes
  level 11 at level 9 → refusal; wear bow with slot 2 open → lands in
  weapon2, lead unchanged; charm set without `charm_slot` → refusal.

## Rollback
`git revert`.
