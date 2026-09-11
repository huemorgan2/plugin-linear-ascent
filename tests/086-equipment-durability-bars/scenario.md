# Equipment durability bar placement

## Preconditions
Use the shared renderer and isolated local QA game. Include equipment at
75%, 25%, zero and full durability, packed and read-only cells. Record
the source commit and take a baseline screenshot before the CSS change.

## Scenario
1. Open the rendered equipment in a real browser at desktop width.
2. Inspect each tile and its bar. Focus/click equipment to check its tip
   and existing action popup still work.
3. Repeat at 390px and 320px widths, then reload the page.
4. In QA Luna type `show me my equipment`, then `show me the scene`.
   Inspect the rendered gear and ensure the read did not change its state.

## Expected behavior
The durability track is a thin borderless strip across the exact bottom
edge of the frame. The remaining fraction is readable. Green, gold and
red continue to mean the same thing. Undamaged/empty slots are unchanged.
Tooltips and actions remain usable; reload retains the styling.

## Fail conditions
Any gap below or beside the strip, a border enclosing it, protruding
corners, a covered icon/count, distorted fill, overflow or broken action.

## Verify
Save screenshots and inspect track/frame bounding rectangles: left,
right and bottom differences must all be zero, height 3px, bar border 0px.
Record test results, QA environment, commits and observed regressions.
