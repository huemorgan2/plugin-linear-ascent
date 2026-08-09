# 045 dojo — hold and endure, four fronts

## Preconditions
- Production serving 0.59.0 on BOTH halves: `/health` reports
  `"game":"0.59.0"` AND the marketplace index lists
  plugin-linear-ascent 0.59.0 with a sha matching the local zip.
- A throwaway enrolled install (HMAC probe pattern) with a fresh
  character walked past the intro onto floor 1.

## Scenario
1. Start a hunt on floor 1; while the fight card is up, list its rows.
2. Finish the fight (win). List the rows on the victory card.
3. Open the Forge. Read the shield and armour buy-card hints.
4. Buy the cheapest shield, then buy a second (spare goes to pack).
   Click the packed spare's cell; list the popup actions; dispatch
   "Use as shield".
5. Take a few blows in one more hunt; re-read the shield's pack-cell
   hover / item tip.

## Expected behavior
- Step 1: no "Ask the shard to scan it" row; the `[i]` dossier still
  carries ATK/DEF/HP. Medlab shelf (checked any time) has no Scout
  optics.
- Step 2: victory card offers the floor menu — hunt again, keep, town,
  and (being hurt) stew/heal rows — not just hunt + warden.
- Step 3: every shield/armour card hint shows `◈ price · +N DEF · END n`,
  END larger on costlier rungs; warded > base > keen at the same rung.
- Step 4: popup shows "Use as shield"; after dispatch the hand row
  holds the spare and the old shield sits in the pack.
- Step 5: END reads `left/total` with `left` reduced by roughly the
  damage the shield turned.

## Fail conditions
- A scan/scout row anywhere (fight card or Medlab) — stale vendor or
  stale marketplace half.
- Victory card with only hunt/keep/town while hp < max.
- A gear card hint with a price but no END number.
- Pack popup still answering "The Forge swaps gear in and out of the
  pack." for a wearable piece.
- Dispatching wear from the popup returns an error card or an unchanged
  hand row.

## Verify (beyond the surface)
- `/health` `game` field says 0.59.0 (scene half); rendered fight card
  markup comes from the 0.59.0 renderer (grid cards carry END — render
  half).
- Server scene JSON for the victory card: option ids include `stew`
  and `keep`; no `scout` id anywhere in the payload.
- After the wear dispatch, the scene's inventory strip shows the swap
  (equipped flag moved), proving state — not just markup — changed.
