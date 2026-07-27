# 016 — Intro movie E2E scenario

Run in a real browser against a QA Luna with the plugin loaded (run-dojo
preflight), as a BRAND-NEW player (fresh tenant/user, no existing character).

## Scenario 1 — the movie plays, in order, unskippable

1. Open the game pane (or say `play linear ascent` in chat).
2. Expect scene I: "THE STORY SO FAR · I" eyebrow, the Aldervale panorama
   GIF animating in the banner slot (river, signal towers, glowing forest),
   body text typing on letter by letter, then a single `Next` option
   fading in. There must be NO skip option on any step.
3. Click Next through all nine story scenes. Verify each has:
   - the right GIF (II theft, III tower, IV warden, V refugee, VI Roothollow,
     VII stone, VIII shard, IX muster) — read the art, don't just count;
   - eyebrow numbering I…IX; body text matches the plan's story copy.
4. On scene II (the theft): watch ~6 s. The action (land tearing free and
   rising) must play ONCE, then settle into the ambient hang — NOT freeze
   on a dead frame, NOT restart the rise. Same check on V, VII, VIII.
5. After scene IX, expect the title card: LINEAR ASCENT art, headline
   "Climb the Ascent. Cast down the Demon King.", option
   "Walk to the tower gate".
6. Click it → the registrar / race pick scene (creation flow unchanged).

## Scenario 2 — numbered text fallback still works

1. Fresh player again, in CHAT (not the pane).
2. The intro scenes must arrive as cards; replying `1` in plain text must
   advance exactly one step (the state machine treats Next as option 1).
3. Get to the title card by numbers only; `1` walks to the tower gate.

## Scenario 3 — no regression for existing players

1. As a player who already finished creation (stage=playing), open the
   pane: the normal town/wilds scene must render — no intro replay.
2. Die once (or inspect a death scene fixture): respawn copy unchanged.

Pass = all three scenarios hold, judged from screenshots + DOM reading.
