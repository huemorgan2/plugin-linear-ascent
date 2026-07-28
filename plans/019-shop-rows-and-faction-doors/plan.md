# 019 — locked rows in the shops, and doors into factions

## The complaint (verbatim intent)

Three things, all from one Forge screenshot and one tour of the
Guildhall:

1. The locked rungs at the top of a shop card are prose lines, not
   rows. If they are things you will one day buy, they belong in the
   options list, rendered as **locked line items**.
2. Owning a piece must not remove it from the shop. A player can hold
   multiples of the same item — spares exist to be donated to the
   faction armory. Today the worn rung leaves the rack.
3. Factions need doors. Founding one should be a **visible, locked**
   option in the Guildhall (◈ 300, level 4+, impossible while you
   already sit at a table). The Community tab should tell the
   unaffiliated to join, let them ask to join from right there, and
   point at the Guildhall to found. The Guildhall should point back:
   "Join a banner (N flying)" → the Community tab.

Plus one rule that covers the "unclear option at the bottom" note:
**every actionable or aspirational state is a proper option row** with
a clear label and hint — no prose-only calls to action, no conditional
rows that appear only when you already qualify.

## What exists (so we change little)

- `core._rack` (core.py ~637) already computes buyable rungs, hides the
  worn one as a `✓ … — worn` prose line, and prints the next rung as a
  `🔒 …` prose line. The 🔒 marker already renders as a 1-bit glyph
  since 0.27.2 — nothing new needed there.
- `core._gear_purchase` (~881) already refuses under-leveled buys with
  a shard note. A locked row can therefore keep its real `buy_<slug>`
  id: clicking it *is* the explanation path.
- Factions are fully built (social.py 010/015): founding flow, join
  requests, dues, armory, admin desk. `GUILD_FOUND_FEE = 500`,
  `FOUND_MIN_LEVEL = 4`. worldd mirrors the fee in
  `worldd/app/factions.py: FOUND_FEE = 500`.
- The Community pane tab already has the full ledger with search
  (`/pane/factions`, `d.total`), a faction detail page with ASK TO
  JOIN / WITHDRAW, and the admin desk. The pane already switches tabs
  in JS (`switchTab('community')` is wired to the faction bar).

## §1 The rack: locked rows, and nothing leaves the shop

`Option` (scene.py) gains one field: `locked: bool = False`
(serialized in `to_dict`, defaulted in `from_dict`; old stored scenes
are unaffected).

`core._rack` changes:

- **The worn rung stays on the rack.** Drop the `g.slug != worn`
  filter; the last two rungs are options regardless of what's on your
  body. The worn one's hint says so: `◈ 450 · worn — buy a spare`.
- **Buying a duplicate of the worn piece goes to the pack**, fresh
  pool, no re-equip (`_gear_purchase`: when `g.slug ==
  p["gear"][g.slot]`, skip the equip/hone/durability swap and do
  `inventory[slug] += 1` with a body line like
  `+ Ashwood Bow — a spare for the pack (the armory takes donations)`).
  Wear bookkeeping caveat: `durability_pack` is keyed by slug, one
  value per slug. A fresh spare sets it to the full pool only if the
  key is absent — an already-stashed worn copy keeps its value. One
  wear value per slug in the pack is a known, accepted simplification.
- **The locked next rung becomes an option row**, not a prose line:
  `Option(f"buy_{g.slug}", g.name, f"🔒 level {req} · ◈ {price:,}",
  locked=True)`. Clicking it hits the existing level-gate refusal in
  `_gear_purchase`, which already names the level and points at the
  Guildhall. The prose line disappears.
- The `✓ … — worn` prose line disappears too (the row now carries it).

The Arcanum uses the same `_rack`, so staves/focuses get all of this
for free. The off-class offer and relic shelf are untouched.

Renderer (`render.py`): a `locked` option renders dimmed (label and
hint in `DIM`, no hover brighten), keeps its `[i]` tooltip, stays
clickable — clicking is how you ask "why is this locked". The 🔒 in
the hint already becomes the 1-bit padlock via the 0.27.2 marker swap;
the no-emoji guard keeps covering it.

## §2 The Guildhall: founding is visible, joining has a door

Fee change: **◈ 500 → ◈ 300**, in both places that must agree —
`social.GUILD_FOUND_FEE` and `worldd/app/factions.py: FOUND_FEE`.
`FOUND_MIN_LEVEL` stays 4.

`social._hall_list` (the non-member view) changes:

- **"Raise a new banner" is always a row** for the unaffiliated:
  - level < 4 → `Option("found_guild", "Raise a new banner",
    "🔒 level 4 · ◈ 300", locked=True)`; clicking explains the gate
    (new refusal in the `found_guild` handler — today it only checks
    gold).
  - level ≥ 4 but broke → normal row, `◈ 300`; clicking gets the
    existing "costs ◈ 300" refusal.
  - The two prose fallbacks ("The hall charters…", "Raising a new
    banner costs…") go away — the row and its refusals carry it.
- **New row: `Option("hall_ledger", "Join a banner",
  f"{total} flying · the Community tab")`.** worldd's guildhall
  payload gains `factions_total` (it already computes the count for
  `/pane/factions`; `worldd/app/social.py: _faction_hall` returns it
  alongside the top-5 list). Clicking the row from chat returns the
  same scene with a shard note: "the full ledger hangs in the
  Community tab — every banner, every desk". In the pane, the option
  click is intercepted client-side (`pane.py` option handler: id
  `hall_ledger` → `switchTab('community')`, no server call).

Members (`_member_panel`) get **no founding row at all** — one banner
per climber; leaving first is the path, and `guild_leave` is already a
row. A typed/forced `found_guild` while in a faction refuses with
"you already sit at the {name} table — leave it before you raise your
own" (guard in the handler, since chat can submit any id).

## §3 The Community tab: tell them, then open the door

All in `pane.py` (the tab is plugin-rendered; worldd data is already
sufficient — `viewer.in_faction` and `requested` ship on the detail
payload, the board knows `d.total`).

- **Non-member CTA panel at the top of the board** (before the
  ledger): "You climb alone. A banner pays — shared armory, weekly
  prize, a table that notices when you're gone. Ask to join below, or
  raise your own at the Guildhall — ◈ 300, level 4+." The Guildhall
  mention is a button: `THE GUILDHALL →` switches to the Game tab
  (`switchTab('game')`); the game card is where the walk to the hall
  happens. Members see nothing new.
- **ASK TO JOIN moves up to the ledger rows.** Each row (for a
  non-member, when that banner isn't already requested) gets the same
  `data-desk="request"` mini-button the detail page has — one click
  from the board, reusing the existing desk action, inline error
  handling and all. The detail page keeps its button.
- A pending request shows `requested` on the row instead of the
  button (the payload already carries which banner is requested).

## §4 Tests

In `tests/test_019_shop_rows.py` (new):

- the rack keeps the worn rung as a buyable row, hint says spare
- buying the worn slug again increments the pack and does not
  re-equip / reset honing
- the next rung is a `locked=True` option row and no 🔒 prose line
  remains; clicking it refuses with the level in the note
- `Option.locked` round-trips `to_dict`/`from_dict`; old dicts
  without the key still load

In `tests/test_019_faction_doors.py` (new):

- level-3 non-member: `found_guild` row present and locked; choosing
  it refuses and names level 4
- level-4 with ◈ 300: founding starts (fee actually charged is 300)
- member: no `found_guild` row; forcing the id refuses
- non-member: `hall_ledger` row present with the total in the hint;
  choosing it returns the scene with the Community-tab note
- the no-emoji guard (`test_no_emoji.py`) stays green — new hints use
  the 🔒 marker only

worldd side (`worldd/tests/`): `_faction_hall` payload carries
`factions_total`; `FOUND_FEE` change covered by the existing founding
test (update the constant there).

## §5 Ship

- Both fee constants change together; grep for `500` near founding
  before the commit.
- Version: **0.28.0** (features, no doc migration — the player doc
  shape is untouched; `Option.locked` lives only in transient scenes
  and pending events, which default cleanly both ways).
- Note for the release train: 0.27.2 was the last published version;
  another line of work may take 0.27.3/0.28.x first — take the next
  free number at publish time, the plan does not own it.
- Standard train: full plugin suite → vendor sync → worldd suite →
  dojo pass in a real browser (Forge card: worn row + locked row with
  the padlock glyph; Guildhall: locked founding at level 1; Community:
  CTA panel + row-level ASK TO JOIN) → publish, deploy, update both
  agents.

## Out of scope

- Per-copy wear for duplicate slugs in the pack (needs an inventory
  shape migration; not worth it for spares meant to be donated).
- Faction browsing inside the game card (the Community tab is the
  ledger; the card only points at it).
- The 533-banner scale problem (pagination past top-10 exists via
  search; nothing new needed).
