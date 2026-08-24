# Profile stays visible beside the recovery strip

## Preconditions
- Local worldd is running with Postgres and the current plugin checkout.
- A legacy password account exists with `google_sub IS NULL`.
- The account has a character with a visible profile.

## Scenario
1. Sign in and open `/play`.
2. Open a normal card that shows the player profile.
3. Turn Labs figure mode on, then return to the profile if needed.
4. Refresh the page.

## Expected behavior
- The regular player portrait is visible; no Gmail box covers its slot.
- Labs mode can replace the regular portrait with the 3D figure normally.
- A bordered, full-width, one-line recovery notice sits below the pane,
  outside the game card.
- The notice explains that connecting Gmail allows player recovery and links
  to the Gmail connection flow.
- Refreshing keeps both the profile and recovery notice visible.

## Fail conditions
- Gmail hides, replaces, dims, or disables either portrait.
- The recovery notice is inside the game card or changes its layout.
- The notice wraps into a large panel at normal desktop width.
- A Gmail-linked account or a Luna plugin pane sees the notice.

## Verify
- `/me` reports `gmail: false` for the test account.
- DOM order places `#gmail-recovery` after the pane content, not inside
  `#game`.
- No player document or account field changes merely by viewing the notice.
