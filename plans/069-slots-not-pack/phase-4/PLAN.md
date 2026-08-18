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

## Execution status
Executed 2026-08-18. core.py: `slot_actions(p, key)` (locked → lock text;
empty → nothing; filled → "Move to the pack" + the Forge trip; in a fight
→ `NOT_IN_A_FIGHT`; last blade → `LAST_BLADE`; pack full → the row keeps
its hint and the click refuses in red), `_unequip` (weapons leave their
slot, lead pointer moves to the first blade left via `_promote_held` so
wear pools swap; a bow's quiver returns with the last bow, capacity
counted; oil on that blade lost — "the oil dries on the shelf"; worn
steel's wear → `durability_pack`; shield/armour honing reset), `_wear_charm`
("Set in pouch": needs `charm_slot`, swaps the old one to the pack,
capacity checked, luck charm gets `CHARM_POOL` when its pool is 0),
`_wear_from_pack` level gate (`rung_player_level_req`, "🔒 level N") and
pack-full guard on the piece it would displace; pack rows now read "Hold"
(weapon/shield) / "Wear" (armour/shoes) / "Set in pouch"; salves keep
"Use a Medgel" next to the pouch row. Deviation from the plan text: a
weapon worn into a free slot LEADS (phase-1 law, tested) — the plan's
"lead unchanged" line is dropped. Tests: 9 new in test_069 (pack 6/6 →
refusal + doc unchanged; 5/6 → armour moves, DEF drops, back on with
"Wear"; shoes level 11 at level 9 → 🔒; bow into weapon2 and back with
quiver + oil note; lead leaves → next leads with its pool; last blade;
slot_actions locked/empty/fight; pouch set/swap/needs pouch; wear refused
when the displaced piece has no room). test_045 labels updated. Suite:
1287 passed, 6 pre-existing failures.
