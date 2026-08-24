# 070 — Choose one reward: an ANSI pick box inside "waiting for you"

Status: executed (roy, 2026-08-23: carry on). Not deployed.

## Problem (roy, 2026-08-23)
1. **The weekly pick is a riddle.** A pending week puts four Vault
   options next to Deposit / Withdraw: "The gold lump", "The aether
   lump", "The smith's token", "The relic". Nothing says it is a
   choice of one. The receipt is one buried body line. Roy clicked
   one, did not know which, did not know what arrived.
2. **It lives on the bank desk.** The Vault is a lodge for money
   (deposit, withdraw, interest stubs, grants). The week-pick is a
   loot chest. Parking it there (WoW Great Vault homage, 022/005)
   made a bank visit feel like a mystery shop.

Evidence: `engine/weekly.py:77-88` labels; `engine/core.py:2873-2878`
appends `pick_*` onto the Vault option list; `engine/notices.py:106-112`
adds a COLLECT row that only walks you to the Vault ("last week's
strongbox is unopened"). Tips still describe the luck charm as a
one-day drink (069 made it a worn pouch item).

## Root cause
The week-pick was implemented as extra Vault menu rows plus a door
shortcut. The notice board (027) can only point at a room; it cannot
host a choice. The copy was engine slang (aether, relic, rested,
strongbox, slot) written for the person who designed the table.

## Design

### What the player sees
When last week opened at least one prize, **waiting for you** grows a
nested ANSI box — a complete square around a number rail, labels
outside to the right, BBS-menu grammar. Other waiting rows
(interest, letters, lodge night, forge mend) stay as they are.

```
waiting for you
  COLLECT  The Vault holds 2 interest stubs — ◈ 40 to the bank

  You have a reward from last week. Choose one. You only get one.
  ┌──┐
  │ 1│  Gold — About as much as half a day's hunting. It is added
  │  │  to the gold you are carrying.                              ◈ 247
  │ 2│  Extra XP — Your next fights will give extra experience,
  │  │  until this bonus runs out.                                 ✦ 12
  │ 3│  Free repair — The Forge will fully repair one piece of
  │  │  gear you are wearing, for free.
  │ 4│  Luck charm — You will find better loot while you wear it.
  │  │  It goes into your pack. Put it in the charm slot on your
  │  │  profile to use it.
  └──┘

  PLAN     The Lodge — tonight is unplanned …
```

The square is one continuous 1px rectangle around the whole number
column (not per-row boxes, not the broken segments on the reference
shot). Sharp corners, `border-radius: 0`. Numbers tabular, centred,
two-ch wide. The rail uses notification ink (`AETHER`), same as the
waiting header — we keep the terminal law (black card, cyan box), we
do not paint IBM-blue over the card. Hover reverse-videos the text
row the way `.nrow` already does; the number cell stays boxed.

Rows 3 and 4 appear only when last week hit 6 points (today's slot-3
table). A 2-point week shows only gold. A 4-point week shows gold +
extra XP.

### Copy law — no engine slang
Banned on this box and its receipt: strongbox, aether, relic, lump,
rested, slot (except "charm slot", which is the thing on the
profile), vanish, pay/paid (weeks and fights do not pay people),
"the week owed you", sentence fragments.

Full sentences only. A person earned something; they choose.

Locked lines (amounts filled at render time):

| id | title | sentence |
|---|---|---|
| `pick_gold` | Gold | About as much as half a day's hunting. It is added to the gold you are carrying. |
| `pick_aether` | Extra XP | Your next fights will give extra experience, until this bonus runs out. |
| `pick_token` | Free repair | The Forge will fully repair one piece of gear you are wearing, for free. |
| `pick_relic` | Luck charm | You will find better loot while you wear it. It goes into your pack. Put it in the charm slot on your profile to use it. |

Header: `You have a reward from last week. Choose one. You only get one.`
Receipt after a click (then the box is gone):

- Gold: `You chose the gold. ◈ N has been added to the gold you are carrying.`
- Extra XP: `You chose extra experience. Your next fights will give more XP until ✦ N runs out.`
- Repair: `You chose a free repair. Take it to the Forge to mend one piece of gear you are wearing.`
- Charm: `You chose a luck charm. It is in your pack. Put it in the charm slot on your profile to use it.`

Fallback (unpicked week auto-gives gold, already law):
`You did not choose a reward in time, so the gold (◈ N) was added to what you are carrying.`

### Where the pick lives
- **The ANSI box is the only chooser.** Click a row → that `pick_*`
  resolves. Valid from every notice room (the board already rides
  the town, the Forge, the Vault…). Same reach as pack-use / Labs:
  the id is owned by `weekly.pick`, not by the current menu.
- **Vault options lose `pick_*`.** The Vault keeps the this-week
  progress sentence (kills · keeps · floors). It does not offer the
  prizes. The Vault door is not badged for the week-pick.
- Keyboard 1–9 stay on `button.opt` (town doors). The ANSI numbers
  are the look, not a second key row — click the line. Collision
  with "1 = first town door" is why.

### Engine shape
- `notices.pending` replaces the strongbox COLLECT row with one
  `kind: "weekpick"` entry: `{kind, text, choices:[{opt,n,title,text,hint}]}`.
  `n` on the entry is 0 (no door chip). `door` is omitted so
  `notices.doors` does not badge the Vault.
- `weekly.rewards` grows a fourth field (title, sentence) or a
  parallel `weekly.choices(p, n)` that the notice and the renderer
  both read. Labels above are the source of truth.
- `core.apply_choice`: `pick_*` while pending → `weekly.pick` →
  stamp the current room with the receipt as `p["strongbox_note"]`
  (already popped onto the next card). Do this next to pack-use,
  before scene-option validation.
- `weekly.pick` return strings become the receipt lines above.
- `tips.py` `pick_*` rewritten to the same sentences (069 charm
  wear, not "until tomorrow").

### Text fallback
`Scene.to_text` already prints `! {notice.text}`. For `weekpick`,
also print each choice as `!  1  Gold — About as much as half a day's hunting…`.

## Fix — phases
1. **Copy + engine reach** — `weekly.choices` / receipt lines;
   `pick_*` valid from any notice room; Vault options drop the
   picks; notice becomes `weekpick` (no door badge). No new look
   yet — a `weekpick` row may render as a plain sentence until
   phase 2. `phase-1/PLAN.md`.
2. **ANSI box** — `render._notices_html` draws the nested square
   (`._weekbox` / `._wrail` / `._wrow`); CSS; hover; to_text
   choices. `phase-2/PLAN.md`.
3. **Tests + dojo + release** — pytest, dojo walk, bump, vendor.
   Not deployed unless roy says so. `phase-3/PLAN.md`.

## Verification (whole plan)
- Pytest: pending week → notices has exactly one `weekpick` and no
  Vault COLLECT about a strongbox; `notices.doors` does not increment
  `vault` for it; `_vault_scene` options contain no `pick_*`;
  `apply_choice(p, "pick_gold")` from `location="town"` pays gold,
  clears pending, returns the gold receipt; same from the Forge;
  a 2-slot pending list is gold only; a 3-slot list is all four
  rows; jargon words above are absent from `choices` titles/texts
  and from the receipt; unpicked-week fallback gold line uses the
  new sentence; `Scene.to_text` lists the numbered choices.
- Render: `_notices_html` for a `weekpick` contains one
  `.weekbox` whose number rail is a single element (one border
  rectangle, not N stacked boxes); four `data-opt="pick_*"`
  buttons; header sentence present.
- Dojo `luna/dojo/tests/waiting-week-box/`: seed a level-6+ doc
  with `strongbox.pending.slots = 3`; open town → waiting for you
  shows the nested square, four plain-language rows, complete
  corners; Vault card has deposit/withdraw and no prize rows;
  click Extra XP → box gone, receipt names extra XP and that
  fights will pay more; inventory/rested pool matches; 390px
  width still a complete square, labels wrap, numbers stay
  inside the rail.

## Rollback
One commit per phase, `git revert` in reverse order. No doc
version bump — `strongbox.pending` is unchanged. Old clients that
do not draw `.weekbox` still receive `notices` and `pick_*` as
data-opt buttons (wire law: unknown notice kinds must not crash
`_notices_html`; phase 2 keeps a sentence fallback).

## Open decisions (defaults chosen)
- IBM-blue BBS skin: **no.** Structure only. Terminal law holds.
- Keys 1–4 on the box: **no.** Town doors keep 1–9.
- Leave a "go to the Vault to pick" row as well: **no.** One
  chooser.
- Rename the mechanic off "strongbox" in code: **not this plan.**
  Player-facing copy only.

## Execution status
Phases 1–3 done 2026-08-23. Game **0.97.0**, vendored. Plugin pytest:
30 targeted tests green (`test_070`, `test_022_005`, `test_029`); full
suite 1304 passed / 6 pre-existing failures (same baseline as 069).
Card render verified in the browser: waiting-for-you shows the nested
square, four English rows, Vault options are gone from this surface.
Dojo runner written at `luna/dojo/tests/waiting-week-box/` — not walked
against a live worldd this session (no local server). Not deployed.
