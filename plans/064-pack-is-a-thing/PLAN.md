# 064 — the pack is a thing

## Problem
The Forge's "Larger pack — 9 slots" is a bare text row on a card wall
(every other buyable is a card with art). And buying a bigger pack makes
the old one vanish — the player paid for it and it is gone. Roy: "create
a card for it with an image, both resolutions; and if I buy another pack
the older pack goes into the newer pack as an item that can be sold or
placed in the guild box."

## Fix (one phase)
1. **economy.PACKS** — five pack items, one per tier: `pack_6` (the
   starter, worth ◈ 20), `pack_9` ◈ 40, `pack_12` ◈ 120, `pack_15` ◈ 300,
   `pack_18` ◈ 600 (the tier's buy price). `pack_slug(slots)`.
2. **Art** — tools/generate_gear_art.py grows the five prompts (group
   "packs"); shipped to content/art/gear/{large,icons}/pack_N_*.png.
3. **Forge card** — `buy_pack` rides `scene.option_art["buy_pack"] =
   pack_slug(next slots)`; render's `_opt_gear_icon` / `_gear_card_preview`
   take that art slug for `buy_pack`, so the row becomes a card with the
   portrait, name, price and the grow-in preview like every other item.
4. **The old pack becomes an item** — `_forge_pack` puts
   `pack_slug(old_slots)` into the inventory (the new pack has 3 more
   slots, so it always fits). Strip cell kind "pack", name from PACKS.
5. **Sell** — the broker's sundries include PACKS (price × rate).
6. **Guild chest** — `_donatable` / `_chest_put_scene` / `_chest_put`
   accept PACKS (card stats "N slots"); worldd/app/armory.py `_gear`
   accepts PACKS too (deposit validation + shelf listing, frac 1.0).
   Take side is slug-generic already.
7. Tips: `buy_pack` tip mentions the old pack stays yours.

## Verification
- tests/test_064_pack_item.py: buying the 9-slot pack leaves `pack_6`
  in the inventory; the pawn lists it and pays; the chest PUT wall lists
  it and `_chest_put` shelves it; the Forge scene renders `buy_pack` as a
  card with the pack art and a preview; every pack art ships both sizes.
- worldd/tests: armory deposit of `pack_6` is accepted.
- Screenshot of the Forge wall.

## Rollback
`git revert`; a `pack_N` slug left in an inventory renders as a plain
"pack N" item (unknown slugs already do) and the broker ignores it.

## Execution status
- Done 2026-08-17. Plugin c494094 (game 0.87.1), root 7bdde34.
- economy.PACKS (5 tiers, pack_6..pack_18); art shipped both sizes
  (content/art/gear/{large,icons}/pack_N_*); Forge `buy_pack` renders
  as a card with the next tier's face + grow-in preview; `_forge_pack`
  keeps the old pack in the inventory; broker sells it (price × rate);
  guild chest PUT accepts it (plugin + worldd armory shelf/deposit).
- tests/test_064_pack_item.py 8/8; full plugin suite 1223 pass, 3
  pre-existing combat failures from the concurrent session (017/026);
  worldd tests/test_armory.py 6/6.
- Local 8777 restarted on 0.87.1. Not deployed, not published.
