# 074 — Gmail recovery strip

## Problem
Legacy password players who have not linked Gmail see the connection request
inside the profile's portrait slot. It hides both the regular portrait and
the optional Labs 3D figure, even though Gmail is only needed for account
recovery.

Evidence: worldd sets `scene.portrait_locked` on every web card and
`render._profile_html()` substitutes the Gmail box for the figure.

## Root cause
Account recovery status was coupled to character presentation. A web-account
concern is injected into every game scene and enforced by the shared card
renderer.

## Fix
- Always render the regular portrait or Labs 3D figure, regardless of Gmail.
- Remove `portrait_locked` from the card-rendering path.
- Check Gmail status once while building the authenticated web pane.
- For an unlinked account, render a slim full-width recovery box below all
  pane content and outside the game card frame.
- Keep the notice to one line: explain that Gmail enables player recovery
  and provide the existing `/auth/google/start` link.
- Luna/plugin panes and Gmail-linked web accounts do not show the box.

## Verification
- Renderer test proves Gmail state cannot replace either portrait form.
- Pane tests prove the one-line recovery box is opt-in and outside `#game`.
- worldd tests prove unlinked `/play` shows the box while linked `/play`
  does not.
- Browser walkthrough confirms an unlinked player sees the full profile and
  the separate recovery box before and after refresh.

## Rollback
Revert the renderer, pane, worldd wiring, tests, and vendored copy. No data
rollback is required; Gmail links and player documents are unchanged.

## Execution status
Done locally 2026-08-24.

- Shared renderer always emits the regular portrait or Labs 3D canvas.
- Unlinked web accounts receive a 36px, nowrap recovery strip below the pane;
  the strip is hidden for linked accounts and Luna panes.
- Plugin renderer/pane regression set: 45 passed.
- Focused worldd web/Gmail set: 11 passed.
- Browser: Roothollow loaded, regular profile rendered, Labs Figure switched
  on and rendered its canvas, recovery strip remained outside `#game`, and a
  full refresh preserved both the 3D profile and strip. `/me` stayed
  `gmail: false`.
- The broader worldd selection had one unrelated existing failure:
  `test_leaderboard_marks_only_you` found the just-created test player outside
  the capped local score list in the long-lived 600+ player database.
