# All floors retain regional contrast and point to exact destinations

## Preconditions

- QA Luna is restarted with the implementation plugin checkout.
- Local worldd is healthy and the existing map QA player is enrolled.
- The player is unlocked through floor 10 and can return to each gate town.

## Scenario

1. Open the existing QA Luna conversation in Chrome and ask `show me floor 3 map`.
2. Inspect the rendered map, then hover the center and edge destination labels.
3. Send a bare displayed option number and confirm the destination changes through `ascent_choose`.
4. Return to the gate town and repeat visual inspection for floors 4, 7, and 10.
5. Resize Chrome to a phone-width pane and recheck one map with left-, center-, and right-anchored labels.
6. Reload the page and ask `where am I?` to confirm the same game state renders again.

## Expected behavior

- Dark terrain and water remain visibly distinct from lit roads, stone, snow, and open ground.
- Every destination chip has a small stepped yellow point with a black outline; its center indicates the linked landscape position.
- The point remains visible on both bright and dark regions and does not cover the label text.
- Tooltips appear immediately on hover/focus, digit navigation chooses the displayed destination, and all chips remain inside the phone-width map.
- Luna uses game tools and stays in-world.

## Fail conditions

- Any map is missing, flat enough that broad terrain regions merge, or is blurred instead of pixelated.
- A chip has no point, has a smooth antialiased dot, or points to a different coordinate after edge anchoring.
- A tooltip is delayed or clipped, a bare number is ignored, or a map appears only through Labs.
- Luna describes a move that the engine did not make.

## Verify

- Capture and read screenshots for floors 3, 4, 7, and 10 plus the phone-width layout.
- Confirm each served asset URL carries the new plugin version and its response hash matches the packaged PNG.
- Read the player scene after digit navigation and confirm floor/location/energy agree with the visible result.
