# 068 — the faction hall, read at a glance

## Problem (roy, 2026-08-18)

Eight things in the hall read wrong or read as nothing:

1. THE CHEST says "the works sell a bigger chest" and sends you away to buy one.
2. "Leave the faction" reads like "back to town" — no colour, no confirmation,
   and it fires the leave on one tap.
3. THE DESK's colour row lists nine names with no colour on them.
4. That row's "Never mind" doesn't say where it goes.
5. Inside the hall the sigil banner is tinted violet no matter what ink the
   faction flies (`_banner_tint` → VIOLET_SOFT for every sigil).
6. THE WORKS carries a door icon and a name nobody reads as "improve the hall".
7. Most hall rows have no [i] — beds, chest, board, coffer, works, desk,
   donate presets, take/put, work rows, colour picks all render without a tip.
8. The unentered week draws the same GOAL box as an entered week with a
   0% bar and "not entered yet" — a goal that is live and empty, then a
   row "ENTER THE WEEK" that reads like a duplicate. It should be a
   promotion: what the challenge is, what it pays, and one row that says
   "pay to enter".

## Root cause

Copy and rendering were written for the 032 launch and never audited as
a member walks the rooms; the renderer has no per-option colour or swatch
grammar; the week box has one shape for two states.

## Fix (one phase — engine copy + renderer + tips)

Files: `engine/hall.py`, `engine/social.py`, `engine/scene.py`,
`engine/tips.py`, `render.py`, `colors.py` (read only), tests.

1. **Chest buys itself.** `_chest_scene` looks up the `chest` row in
   `hall["works"]` and appends `work_<id>` — "Buy a bigger chest — N slots"
   priced from the coffer, locked when short or when the viewer isn't the
   steward (hint says who buys). `_work_buy` for `hall_chest_up` doubles the
   optimistic cap (4→8→16→32 is worldd's ladder) so the sockets grow on the
   same card. Buying from the chest returns to the chest (`hall_area` stays).
2. **Leave is red and asks.** `Option` gains `danger: bool = False`
   (renderer: `.opt.danger` — red label, red key). `guild_leave` in the hall
   sets `p["hall_leaving"]` and draws a confirmation card:
   headline "Leave the faction?", body "You're about to leave X and no
   longer be part of it — no access to the faction hall and no part in its
   events. Dues stop, prize shares stop, the coffer keeps what it holds."
   Options: `leave_confirm` "Leave the faction" (danger),
   `hall_cancel` "Back to the faction hall", `town` "Don't leave — go to town".
   `leave_confirm` runs the old `social.guildhall_action(p, "guild_leave")`.
   The Guildhall's own leave rows (old-worldd panel) get the same
   `p["guild_leaving"]` two-step with `leave_confirm` / `guild_stay`.
   The `town` global nav must clear `hall_leaving` (added to the two
   pop-lists in `core.py`) and `clear_state`.
3. **Colour swatches.** Renderer: an option whose id starts `hcol_` (hall)
   or `col_` (founding wizard) gets `<span class="swatch" style="background:INK">`
   before the label — INK from `colors.faction_ink(slug)`.
4. **Copy.** Recolor cancel row → "Back to the desk without changing colour".
5. **Banner ink.** `Scene.banner_ink: str = ""` (new top-level key — old
   clients drop it). Hall scenes that fly the faction sigil set it from
   `colors.faction_ink(fac["color"])`; `render_scene_fragment` uses it over
   `_banner_tint` when set and the banner is a sigil.
6. **The works.** Home row: `Option("hall_works", "Improve the faction's hall",
   "beds, a bigger chest, a deeper coffer, a bigger room — from the coffer")`,
   dropped from `_DOOR_ART` (no icon). Works scene headline
   "Improve the faction's hall".
7. **[i] everywhere.** `tips._TIPS` gains: hall_coffer, hall_chest,
   hall_board, hall_bunks, hall_works, hall_desk, hall_home, chest_put,
   bed_claim, write_note, rename_banner, recolor_banner, promote,
   donate_custom, hall_cancel, leave_confirm, guild_stay; `option_tip`
   prefixes: `donate_N`, `work_`, `take_arm_`, `put_`, `hcol_`, `req_ok_`,
   `req_no_`, `promote_`.
8. **The unentered week is a promotion.** `_week_lines`, not entered:
   box title `▜ ENTER THIS WEEK'S CHALLENGE — {KIND}`, lines:
   "this week your faction needs to {verb}", "days left: N",
   "win it and every member gets up to {prize(1.75)}" plus the three
   attendance rungs; no progress bar, no "not entered yet". Steward row:
   `enter_week` "Pay to enter this week's challenge" — hint
   "◈ cost from the coffer (◈ bal)". Member line unchanged ("the steward
   signs the faction in — nudge them"). Entered: box unchanged.

## Verification

- `../worldd/.venv/bin/python -m pytest tests/ -q` — full suite green;
  new tests in `tests/test_068_hall_ui.py` cover each of the eight.
- Rendered HTML: `.opt.danger` on the leave row, `.swatch` on the nine
  colour rows, `banner` div background = faction ink in the hall, no
  `ftile` on hall_works, `[i]` present on every hall option.
- Dojo: `luna/dojo/tests/068-hall-ui/` walkthrough — steward walks
  chest → buys the bigger chest in place; leave → confirm card → back
  to hall; desk → colours show swatches; unentered week shows the
  promotion box; enters; box turns into the goal box.

## Rollback

`git revert` of the 068 commit in plugin-linear-ascent, re-vendor. No
data or wire shape changes on worldd — the effects emitted are the same
(`hall_chest_up`, `guild_leave`, `faction_recolor`, `faction_enter`).

## Operational notes

Version bump + `worldd/tools/vendor_game.sh` after tests; deploy only on
roy's word.
