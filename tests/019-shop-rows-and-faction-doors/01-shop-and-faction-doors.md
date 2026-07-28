# 019 E2E — locked shop rows and faction doors

Run against the local stack (worldd 8600 + Luna 8765, tenant qa007)
with a FRESH low-level character, in a real browser. You are the
assertion engine: screenshot + read the DOM at every step.

## Scenario 1 — the Forge rack

1. Create/land a level-1..3 character; walk: town → The Forge.
2. READ the option rows. PASS iff:
   - the worn starter-adjacent rung appears as a BUYABLE row (hint
     carries "worn — buy a spare") — not as a `✓ …` prose line;
   - the next rung above your level appears as a DIMMED locked row
     with the 1-bit padlock glyph + `level N · ◈ price` in the hint —
     not as a prose line;
   - no `✓` / lock prose lines remain in the body.
3. Click the LOCKED row. PASS iff the scene returns with a shard note
   naming the required level (no purchase, no gold change).
4. Buy the piece you are WEARING. PASS iff gold drops, the pack strip
   count for that item rises, the equipped piece is unchanged (still
   worn, honing untouched), and the body line says it went to the pack.

## Scenario 2 — the Guildhall doors (level < 4)

1. Walk: town → The Guildhall (character below level 4, no faction).
2. READ the options. PASS iff:
   - "Raise a new banner" is a DIMMED locked row: padlock + `level 4 ·
     ◈ 300`;
   - "Join a banner" row exists with the live faction total in the
     hint and points at the Community tab;
   - neither exists as prose-only.
3. Click "Raise a new banner". PASS iff refusal names level 4 and no
   gold moves.
4. Click "Join a banner" IN THE PANE. PASS iff the pane switches to
   the Community tab (no game-state change, no server error).

## Scenario 3 — the Community tab doors

1. On the Community tab with the same unaffiliated character:
2. PASS iff the board shows a call-to-action panel for the
   unaffiliated: join pitch + "raise your own at the Guildhall —
   ◈ 300, level 4+" with a button that switches back to the Game tab.
3. PASS iff each ledger row of a joinable banner carries an inline
   ASK TO JOIN button; click one — the row flips to "your request
   waits at their desk" (or equivalent) without leaving the board.
4. A member (or the same character after acceptance, if feasible):
   the CTA panel is absent.

## Scenario 4 — founding at level 4+

1. Level the character to 4 (guild training) with ≥ ◈ 300 carried.
2. The Guildhall now shows "Raise a new banner — ◈ 300" unlocked.
3. Click it. PASS iff the founding flow starts (name step) and, on
   completion, exactly ◈ 300 left the purse (ledger row `found`).
4. Re-enter the Guildhall as a member. PASS iff no founding row
   exists at all.
