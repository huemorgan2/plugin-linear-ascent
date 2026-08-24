# 072 — other-player avatar (reusable sheet)

## Problem
The other climber's page is a text dump plus a tiny tile. Loot says
"loot their camp" — you are looting the player, not a camp. Roy
(2026-08-24) wants the page to open with the same look as the
player's own profile (ident, figure, worn slots, HP/energy/XP,
ATK/DEF/SPD) and that block to be a reusable component.

## Root cause
`_profile_html` is the *viewer's* interactive sheet (pack, unequip,
live `data-m` counters, Gmail gate). The Stone of Names scene never
shipped a second sheet, and worldd's public payload omitted slots,
speed, XP and energy cap.

## Fix
- `Scene.avatar` — the subject's public sheet. Old clients drop it.
- `profile.public_sheet(doc)` — one builder (no bank, no slot acts).
- `render.player_avatar_html(sheet)` — read-only look + gear +
  parameters. Not `_profile_html`.
- Profile card: avatar on top; slim body; option **Loot them**.
- worldd `_profiles` fills the new fields. Loot headlines drop "camp".

## Verification
- Opening another climber shows their name, portrait, slots, meters.
- "Loot them" on the option; no "Loot their camp".
- Bank never on the wire. Viewer's pack/slots unchanged.
- `player_avatar_html` has no `data-m` and no unequip acts.

## Rollback
Revert. Old payload still renders the text page.

## Execution status
Done 2026-08-24. Plugin tests `test_072_player_avatar.py` + `test_042` +
`test_071` 27 passed. worldd `test_042_guilds_looting.py` + `test_071`
10 passed. Option is **Loot them**. `Scene.avatar` +
`render.player_avatar_html` ship the read-only sheet.
