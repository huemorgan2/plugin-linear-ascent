# 009 · Scenario 1 — the game lives in the pane, not the chat

Goal: the whole interface moved out of the chat. A "Linear Ascent"
entry sits in the left menu; entering it renders the current scene in
the middle pane with the GAME / SCORE / COMMUNITY tab bar; clicking
options swaps scenes in place; the chat receives NO cards.

## Steps

1. Open the QA Luna in the browser, logged in as the owner.
2. Look at the left sidebar. **Expect:** a "Linear Ascent" item with
   its icon, between the builtin sections (sort order ~45).
3. Click it. **Expect:** the middle pane fills with the game UI:
   - top tab bar `GAME · SCORE · COMMUNITY` in the same monospace
     font as the cards, active tab visually distinct;
   - below it the CURRENT scene, pixel-identical grammar to the old
     chat card: 1-bit banner (if the scene has one), eyebrow,
     headline, `[n]` option rows, `█░` meters rail;
   - the typewriter reveal plays.
4. Screenshot. Read it. Flag any layout drift from the card grammar.
5. Click option `[1]`. **Expect:** within ~2s the scene swaps IN
   PLACE (no navigation, no new chat message). Meters/gold move if
   the action costs or pays.
6. Switch to the chat section. **Expect:** NO new scene card was
   posted — the conversation shows only whatever was there before.
7. Back to the pane; click through 3–4 more options (a hunt if
   available). **Expect:** every click resolves in place; stale
   double-clicks don't fire twice; option keys stay `[n]`-styled.
8. Click SCORE and COMMUNITY tabs. **Expect:** placeholder panels in
   the same panel style (or live content once plan 010 ships) — no
   blank white, no errors.
9. Reload the page, reopen the pane. **Expect:** the same current
   scene renders (state persisted server-side; no ghost/blank pane).

## Pass criteria

- Sidebar entry present and functional on desktop.
- Scene renders in pane with identical card grammar; options work.
- Zero scene cards posted to chat during pane play.
- Tab bar renders and switches without errors.
- Reload-safe.
