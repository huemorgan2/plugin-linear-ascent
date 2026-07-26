# 010 · Scenario 2 — faction life at the Guildhall (fourth directive)

Goal: joining, founding and managing a faction happens IN-GAME at the
Guildhall in Roothollow — game scenes, not pane forms. Founding sets the
purse numbers (join fee + weekly dues); both land in the faction store.

## Steps

1. With a character holding ≥ ◈500, walk to Roothollow → The Guildhall.
2. **Expect:** the hall card lists existing banners as options with the
   purse shown up front (`join ◈ 25 · dues ◈ 5/wk`), plus "Raise a new
   banner · ◈ 500" and the training option.
3. Click "Raise a new banner". **Expect:** "Name your banner" — typed in
   chat, like character naming. Type a name.
4. **Expect:** a sigil pick — 8 one-bit sigil options + "Never mind".
   Pick one.
5. **Expect:** "Set the join fee" (typed, ◈ 0–500). Type `25`.
6. **Expect:** "Set the weekly dues" (typed, ◈ 1–50). Type `5`.
7. **Expect:** back at the hall as steward: the member panel shows
   `STORE ◈ 0 · dues ◈ 5/week · join ◈ 25`, your attendance pips, this
   week's world challenge with its entry cost, options Donate / Enter
   the week's challenge / Leave the banner. GAME meters show ◈ down by
   exactly 500; worldd has the faction row with join_fee=25,
   weekly_dues=5.
8. Second player (other tenant, scripted client) walks to the Guildhall.
   **Expect:** the hall lists the new banner with `join ◈ 25 · dues
   ◈ 5/wk`; joining charges ◈25 (gold first, then bank) and the
   steward's panel now shows `STORE ◈ 25` and a `join_fee` row in
   `ascent_faction_ledger`.
9. Member clicks Donate, types `30`. **Expect:** carried gold −30,
   store +30, ledger `donation` row, card note names the new balance.
10. Steward clicks "Enter the week's challenge" (◈5 × members).
    **Expect:** if the store covers it, the entry lands: store drops by
    the entry, the panel shows the challenge as "entered" with progress;
    `ascent_faction_weeks` has the entered row with kind = week % 3.
    If short, the card refuses and SHOWS the shortfall.
11. Steward clicks "Remove a member" → picks the member. **Expect:** the
    kicked player's doc loses its colors on next scene load.
12. Leave the banner. **Expect:** back to the hall list; an empty
    faction dissolves (the store burns — the Ascent keeps it).

## Pass criteria

- The full lifecycle works from GAME CARDS in chat (or the pane GAME
  tab) — the COMMUNITY tab has NO join/create/manage controls.
- Founding fee charged exactly once; join fee lands in the store;
  every store movement has a ledger row.
- Steward-only options (enter, kick) never render for plain members.
- The refusal messages carry numbers (shortfall, carried gold).
