# Scenario 1 — No auto-level; train at the Guildhall

Fresh player (or a player with a full XP bar) in the game pane on QA Luna.

## Steps

1. Hunt the wilds on the frontier floor until the XP bar fills
   (`XP x/need` with x >= need — bar renders solid).
   - **Check**: no level-up happens on any kill. The level (LV chip in the
     rail) stays put, HP does not snap to full, no "LEVEL n" line appears.
   - **Check**: a victory card with the bar full carries a nudge line
     pointing at the Guildhall with the ◈ fee.
   - **Check**: XP per kill is visibly LOWER than gold per kill on every
     victory card (floor 1: +4ish XP vs +8ish gold).
2. Return to Roothollow → The Guildhall.
   - **Check**: a **Train** option is present, hint shows the ◈ fee
     (level 1 → ◈ 200).
3. Click Train with enough gold.
   - **Check**: level increments (LV chip), gold drops by the fee, the XP
     bar loses one bar's worth (leftover XP kept), HP reads full.
4. Click Train again immediately (bar now short).
   - **Check**: refusal prose — needs a full XP bar; nothing is charged.
5. Meters rail everywhere: reads `XP n/m`, and `LV n` sits next to
   `◈ gold`. No ✦ glyph anywhere a cost or the meter means XP.

## Pass

All checks above by eye (screenshots + DOM). The feel: leveling is a
purchase you walk to and pay for, and XP is the scarcer currency.
