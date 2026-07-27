# 015 / 03 — The admin desk: rename, promote, kick, challenge

As a faction admin (founder), on the faction's page in COMMUNITY.

## Steps

1. RENAME: type a new name in the inline input, click SAVE. The page and
   every board mention update to the new name; the faction's win history
   stays attached. A taken/invalid name shows an inline error line.
2. PROMOTE: promote a member to admin. Their roster row gains the ADMIN
   tag. (They can now open the same desk.)
3. KICK: kick a member — first click arms the button (SURE?), second
   executes. The row leaves the roster inline. Verify an admin cannot
   kick another admin (button absent or refused) unless founder.
4. CHALLENGE: if the week isn't entered, the desk shows the challenge,
   the entry cost, and the vault (store) balance. Click ACCEPT — the
   treasury drops by exactly the entry cost and the block flips to the
   entered state.
5. FOUNDER: through all of the above, the founder's roster row keeps the
   ★ FOUNDER mark.

## Pass

- All four actions work inline, server-persisted (reload the pane and
  the state holds), ANSI-block styling, monospace inputs.

## Fail

- Any action needs a popup, doesn't persist, or the founder mark moves.
