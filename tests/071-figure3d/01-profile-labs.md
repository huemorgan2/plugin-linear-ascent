# 071 — Figure 3D Labs portrait

## Preconditions
- A QA Luna or local `/play` session has an authenticated, mid-game climber.
- The climber has a filled weapon slot, shoes, charm, armour, and shield; use a
  bow in a second weapon slot when available.
- The 071 plugin/vendor build and `worldd/static/site/figure3d/` bundle are
  loaded. Begin with **Figure — 3D climber in the profile** off.

## Scenario
1. Open the climber's current scene and record the portrait, meters, and filled
   gear slots.
2. Open Labs and turn on **Figure — 3D climber in the profile**.
3. Return to the same scene. Capture a screenshot and DOM snapshot.
4. Confirm the portrait position contains a 100×200 canvas (140×260 for a
   giant) with `data-figure3d`, then watch it for a calm breath/idle motion.
5. Hover the sword/blade slot, then the armour, boots, charm, shield, and bow
   slots. Capture a screenshot while each matching mesh is highlighted.
6. If both a bow and sword are worn, confirm the bow rides the back while the
   blade hangs on the hip. If a staff is worn, confirm it is held upright in
   the right hand.
7. Open Labs, turn Figure 3D off, return to the profile, and capture a final
   screenshot and DOM snapshot.

## Expected behavior
- Off uses the unchanged PNG portrait and has no `canvas.figure3d`.
- On replaces only the portrait with a crisp 1-bit climber; the rest of the
  card, slots, meters, and game state do not change.
- Filled-slot hover applies the slot's one allowed saturated colour only to
  the matching worn mesh. Leaving the slot restores the 1-bit render.
- Turning the feature off removes the canvas and restores the original PNG.

## Fail conditions
- Raw payload JSON, a WebGL error, missing body or item mesh, blank canvas, or
  a permanently visible fallback image.
- A sword in the hand, bow at the hip, staff on the back, boots not on both
  feet, or gear hover colouring the wrong object.
- Any game-state mutation caused by viewing, hovering, or toggling the
  portrait; any changed meter, inventory, gold, or scene progression fails.

## Verify
- Browser console has no module, GLTF, or WebGL errors.
- `/play` includes `/static/site/figure3d/figure3d.js` once.
- Toggle the feature twice and inspect the scene payload: only
  `labs.figure3d` and the optional `figure3d` scene key change.
