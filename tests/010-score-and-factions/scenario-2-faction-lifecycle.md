# 010 · Scenario 2 — found a faction, name it, pick a sigil

Goal: the COMMUNITY tab supports the full faction lifecycle: create
(name + banner from the 30 sigils, ◈500 fee), join, steward goal
setting, kick, leave.

## Steps

1. With a character holding ≥ ◈500, open COMMUNITY.
2. **Expect:** "banners flying" list (possibly empty) + the founding
   panel: name input, a grid of 30 one-bit sigils, a disabled "Raise
   the banner" button that enables only when name + sigil are set.
3. Type a name, click a sigil (it highlights), click create.
   **Expect:** the view swaps to "your banner": chosen sigil rendered
   large, member table with you as steward, goal panel with the
   steward's kind/target form and fair-target suggestions.
4. Verify the fee: GAME tab meters show ◈ down by 500; worldd ledger
   has a `faction_found` row.
5. As steward, set a goal (e.g. CULL 10). **Expect:** goal line with
   progress bar appears; `ascent_factions.goal_target` updated.
6. Second tenant joins the faction (via API or second Luna).
   **Expect:** member table shows 2 rows; base prize flips to 15%→15%
   (still <4 members) — the label must show 15%, not 20%.
7. Steward kicks the second member. **Expect:** row gone; the kicked
   tenant's doc loses its guild on next scene load.
8. Leave the faction. **Expect:** back to the hall view; the faction
   dissolves if empty (gone from the list).

## Pass criteria

- Full lifecycle works from the pane with no raw errors.
- Fee charged exactly once; DB rows match every step.
- 15%/20% and steward-only controls render correctly.
