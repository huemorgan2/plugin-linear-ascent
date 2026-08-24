# 076 — opaque lift loader stage

## Preconditions
- Local `/play` is authenticated with a playing climber.
- The climber can ride up from the gate and return down to Roothollow.
- Both lift GIF URLs return `200 image/gif`.

## Scenario
1. Open the gate and choose an available higher floor.
2. During the ascent, capture a screenshot and DOM snapshot of `#liftlay`.
3. Confirm the destination card is already mounted beneath the overlay.
4. Wait for the overlay to fade and interact with the destination.
5. Return to Roothollow and repeat the checks during descent.
6. Reload the destination and attempt an invalid floor choice.

## Expected behavior
- The animated GIF ink sits over a solid black 320:112 box; transparent GIF
  pixels are black, never a window through to the destination.
- The destination card exists underneath throughout the ride and is ready
  immediately when the overlay fades.
- Up uses the ascent GIF and down uses the descent GIF.
- Reload, peek, and refusal do not replay the lift.

## Fail conditions
- Destination art or text is visible through transparent GIF pixels.
- Blank/stale origin card underneath the overlay, destination mounted only
  after animation, wrong-direction GIF, overlay lasting over seven seconds,
  blocked destination after fade, or any console/network error.

## Verify
- `#liftlay .car` has an opaque black computed background.
- `#liftlay .car .ink` carries the GIF mask with a nonce.
- The game card carries the destination `data-loc` while `#liftlay` exists.
- Overlay is removed after the fade and the destination accepts input.
