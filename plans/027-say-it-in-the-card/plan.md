# 027 — Say it in the card

Five complaints, one theme: **the card knows things it never says out loud, and
asks for things it cannot take.** A `(1)` that means nothing. A salve that
stacks up because the only mouth that eats it is a menu row two rooms away. A
banner that is a filename. A name the game demands you type into the chat like
a command line.

Everything here is presentation and reach — no combat math, no pools, no prices.

---

## Phase 1 — The notice board: a `(n)` nobody can misread

**What's wrong.** `_town_waiting()` bakes `" (1)"` into `Option.label` as plain
text. It is the same grey as the label, it appears only on the town square, and
the lodge's `(1)` is not even a claim — it means *tonight is unplanned*, which
reads exactly like *there is loot behind this door*. The player planned nothing,
clicked around, and the number vanished; of course it felt broken.

**What ships.**

1. `Option.badge: int` — the count leaves the label string and becomes a real
   field, rendered as a **bright blue chip** (`#5eaefc` on ink), tabular, always
   the same width. `to_text()` keeps writing `(n)` after the label so the agent
   and the plain-text fallback are unchanged.
2. `Scene.notices: list[dict]` — a new **notice board slot at the very top of
   the card**, under the art, above the eyebrow. Entries are
   `{opt, n, kind, text}` with `kind ∈ collect | plan`. Each row is a clickable
   shortcut straight to the thing: blue rule down the left, blue count chip, and
   a sentence that leads with the verb and names the room:
   - `COLLECT · 10 · The Vault holds 10 interest stubs — ◈ 250 to the bank`
   - `PLAN · The Lodge — tonight is unplanned; rest it or work it before dawn`
   The header of the box says `WAITING FOR YOU`, and a `plan` row never says
   "collect".
3. One source of truth: `engine/notices.py::pending(p, w)`. `_town_waiting()`
   becomes a thin projection of it (`{door: n}`), so the door chips and the
   notice rows can never disagree.
4. **Two new doors get badges** — the complaint said "also in the forge and
   everywhere else":
   - **The Forge** — a held repair token (a free mend sitting in the pack) and
     broken gear (`dur <= 0`, fighting at half strength).
   - **The Guildhall** — the XP bar is full *and* the training fee is in hand:
     the level is bought, not earned, so a full bar with no notice is a level
     rotting on the shelf.
   Both are real claims, never mere availability — the 023 badge law holds.
5. The notice board rides **every town-side room**, not just the square, so
   walking into the Forge still tells you the Vault is holding money.

## Phase 2 — The pack has a mouth: click an item, use it

**What's wrong.** "I keep getting more medgels — why?" Because **90% of every
alpha kill drops one** (plus a 25% present roll), and the only place that eats
one is a menu row that appears at the gate camp when HP is already down. The
pack strip is hover-text; nothing in it is clickable. (For the record: the item
is *Medgel*, `+25 HP`, ◈25 — the number the player remembered as energy is the
heal.)

**What ships.**

1. `core.pack_actions(p, slug)` — what this item can do **right now**, wherever
   the player is standing. Heals become usable anywhere out of combat (town,
   camp, lodge, forge — any room). Mid-fight the law is unchanged: the trollblood
   tonic stays the only heal in a fight; quivers and relics keep their existing
   ids.
2. The pack strip carries those actions (`data-acts`) and every cell becomes a
   button. Clicking one opens a **small popup menu** at the icon: the item's
   name, the actions (`Use a Medgel · +25 HP`), and — when nothing can be done
   here — the reason plus where it *can* be done. The menu posts the ordinary
   option id through `/act`; the engine gains no new verbs it did not already
   validate.
3. `tips.py` answers the "why do I keep getting these" question in the item's
   own tip: medgel and luck charm now name their faucet (alpha spoils, presents,
   strongbox).
4. **The count-up.** The pane remembers the last rail; when a scene lands with a
   different HP / ⚡ / XP / gold, the number **counts** to its new value and the
   block bar fills a cell at a time (~600ms, 25 steps for a 25-point heal —
   exactly the animation asked for), green up, red down. Meters carry
   `data-m/data-v/data-max` so the tween is machine-read, never parsed out of
   text. `prefers-reduced-motion` shows the final number instantly.

## Phase 3 — Type it in the card, not in the chat

**What's wrong.** Six flows (`stage=creation_name`, banner name, join fee,
weekly dues, donation amount, letter body) set `Scene.awaits_text` and then tell
the player *"Say it in chat"*. `/act` has accepted `text` the whole time; no
card ever offered a box to put it in.

**What ships.**

1. `Scene.ask: dict | None` — `{kind: "text"|"number", label, placeholder, max,
   min, submit}`. Rendered as one monospace input row in the card's own type:
   same font, same border, same key-chip grammar as an option row, with the
   submit button on the right. Numbers get `inputmode="numeric"` and a min/max
   the engine already enforces.
2. Wired in both clients — the pane (`/act` with `{text}`) and the legacy chat
   card (the 057 bridge, same `luna:card:action` message with `text` in the
   body). Enter submits.
3. `awaits_text` stays exactly as it is, so the sidekick can still take a typed
   chat answer for anyone who prefers the chat. The card is the fast path, never
   the only path.

## Phase 4 — A banner is a picture

**What's wrong.** Faction sigils exist — 31 of them, 1-bit 320×112, already
served at `/art/factions/{slug}.png` — and the game shows them in exactly two
places. Founding a banner asks you to pick a sigil from a list of *words*
(`Wolf Howl`, `Gear Sword`). The Guildhall, the hall list, THE LEDGER, the
hall of banners and last week's results all print a name.

**What ships.**

1. `_banner_data_url()` learns to look in `banners/factions/`, so a faction
   sigil can be a card banner anywhere — chat card included, no pane needed.
2. `Scene.gallery: list[dict]` — `{opt, slug, label, sub}`, rendered as a grid
   of **clickable sigil tiles** (art + name under it, blue border on hover).
   Used by:
   - **founding, sigil step** — pick the mark by looking at it;
   - **the hall list** — every banner on offer shows its colors with its fee and
     dues, and the tile is the "ask to join" button.
3. The member panel's card banner becomes **your own sigil** instead of the
   generic guildhall art, and the roster header names it.
4. Community tab: THE LEDGER rows, HALL OF BANNERS wins and last week's results
   all get the sigil chip that MOST CLIMBERS already had.

## Phase 5 — Blue means "there is something for you"

One token, used consistently: `AETHER #5eaefc` is the notification color.

- Count chips on doors (`.badge`) — blue fill, ink numeral.
- Notice rows — blue left rule, blue header, blue count.
- Pack popup — blue border, matching the `[i]` dossier grammar.
- The gold/HP/XP counters keep their own colors; blue never means a stat, only
  *"something waits"*.

---

## Played, not just tested

Walked on the QA stack at level 15, in the pane, one surface at a time.

- **The square** carries the board: header **"waiting for you"** in
  `#5eaefc`, one row — *"PLAN · The Lodge — tonight is unplanned. One
  action a night: rest it to bank aether, work it for coin. Dawn settles
  it either way."* — and the Lodge's own chip reads `1` in ink on blue.
  The `(1)` that meant nothing now says what it wants.
- **The pack** answers a click: the Medgel opened its menu *above* the
  lore bubble (`.pmenu` z-index 100, `#tipbox` hidden on open), *"Use a
  Medgel — +25 HP · 1 left"*, and HP went 132 → 157 with *"+ 25 HP — the
  medgel does its work."* The rail really counts: buying one walked gold
  **3,077 → 3,052 one coin at a time**, ~24 ms a step, ~600 ms total.
- **Typed in the card:** the Relay's letter box (`text`, max 200) sealed
  *"the stair holds at the third landing"* with **"+ sealed and slotted
  for Fleet"** — no chat line. Founding asked for numbers with
  `type="number" inputmode="numeric" min/max` (fee 0–500, dues 1–50).
- **Banners are pictures:** the sigil step showed 8 tiles of real 1-bit
  art, blue because they are pickable; the table that came out of it flies
  Iron Heart as its card art in violet; the Community rows carry the same
  sigil beside the name.

### Two bugs the walkthrough caught, both fixed here

**The card contradicted itself.** *"the Third Landing banner goes up over
your table"* sat directly above *"No banners fly yet. Yours could be the
first."* worldd is the single writer, so the snapshot the engine holds at
that moment still has no faction in it. Founding and leaving now render
**their own** cards — *"The Third Landing banner flies"* with the chosen
sigil as its art and the fee and dues it just fixed forever, and *"You
fold your colors"* instead of a roster you have already left. Both offer
the hall, which reads the fresh snapshot on the next turn. Walked live:
both cards, then the table, then the empty hall.

**worldd 500'd on `/v1/presence` until its first scene.** `app/social.py`
reached for the engine without putting the vendor copy on the path,
borrowing it from whichever sibling module got imported first — and
main.py imports the game modules lazily, inside endpoints. A freshly
booted worldd asked for presence before a scene answered
`ModuleNotFoundError`. `worldd/tests/test_gamepath.py` now imports each
game module in its own interpreter.

---

## Tests

`tests/test_027_say_it_in_the_card.py`:

- a door's count is a field, not a label — and the text fallback still says `(n)`
- the lodge notice says PLAN and never says collect; it clears only on
  `night_rest` / `night_work`
- the forge badges a held repair token and broken gear; the guildhall badges a
  bought level the player can afford
- notices ride the forge and the vault, not just the square
- `pack_actions` offers a heal in town, refuses at full HP with the reason, and
  never offers a medgel mid-fight
- using a medgel from the pack popup heals 25 and burns one
- a scene that awaits text renders an input with the right kind/max, and posting
  `{text}` through `/act` lands the same as a typed chat reply
- the founding sigil step ships a gallery whose every slug resolves to real art
- the hall list gallery carries fee and dues per tile
- every sigil slug on disk resolves through `_banner_data_url`
- a scene from this engine still parses on a 0.28–0.32 install (`badge` rides
  beside the options, never inside one), a field from a newer engine is ignored
  rather than fatal, and a drawn haul (`tally`) crosses the wire
- the lore bubble never covers the menu it opened
- the founding card flies the new banner instead of the empty hall, and the
  leave card doesn't still seat you at the table

Existing suites to update: `test_029_collect_badges.py`, `test_023_interest.py`
(badge is a field now), `test_render.py` (new slots).
