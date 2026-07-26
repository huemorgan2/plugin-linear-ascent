# 009 · Scenario 2 — the agent sees every move, speaks only when it matters

Goal: every pane click sends the agent the new state (awareness rows);
big beats (death, boss) still trigger a spoken moment; grind stays
silent; the agent can answer "what just happened" accurately without
having driven any of it.

## Steps

1. In the pane, perform 3–4 ordinary acts (hunt, travel, shop).
2. Switch to the chat. **Expect:** the agent said NOTHING on its own
   during those acts — no reaction messages for grind.
3. Ask the agent: "what just happened in my game?" **Expect:** an
   accurate, in-character answer that reflects the acts just performed
   in the pane (it read the awareness rows) — e.g. it knows the last
   fight, current floor, roughly the gold. It must NOT claim it can't
   see the game or hallucinate different events.
4. Keep hunting in the pane until HP is low, then deliberately die
   (or trigger a boss/warden fight). **Expect:** the agent posts ONE
   short in-character reaction in the chat on its own (moment channel)
   — and only one; no card restating, no option-listing.
5. Screenshot the chat: verify the reaction is ≤2 short sentences,
   in-world voice, no "tool"/"plugin"/"state" leakage.

## Pass criteria

- Ordinary acts: zero unprompted agent messages.
- "What just happened" answered accurately from awareness history.
- Death/boss: exactly one short unprompted in-character line.
