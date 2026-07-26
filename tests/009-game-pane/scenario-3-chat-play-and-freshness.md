# 009 · Scenario 3 — chat-driven play still works; the pane stays fresh

Goal: the agent can still act for the player on request (ascent_choose)
— the result shows up in the pane, not as a chat card; the pane notices
state changes it didn't cause.

## Steps

1. With the pane open in one view, note the current scene headline.
2. In the chat, tell the agent: "take option 1 for me".
   **Expect (chat):** the agent calls ascent_choose (tool chip), then
   replies with at most one short line — and does NOT paste the scene
   text or render a card; it may point at the pane.
3. Watch the pane. **Expect:** within one poll cycle (~15s, or on
   tab refocus) the pane swaps to the new scene without a manual
   reload.
4. In the chat, ask "where am I?" **Expect:** ascent_scene tool chip,
   compact text answer, no card, no scene dump.
5. Mobile viewport (390×844): **Expect:** Linear Ascent reachable
   from the bottom nav, pane fills the screen, tabs tappable, options
   tappable.

## Pass criteria

- ascent_choose still mutates state; result appears in the pane.
- No scene cards or scene-text dumps in chat from tools.
- Pane self-refreshes after out-of-band state change.
- Mobile nav + pane usable.
