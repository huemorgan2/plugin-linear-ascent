# 014 — the pack strip & the whisper glyph (inventory + [i] tooltips)

Two directives from the operator, both about making the game explain
itself at a glance:

1. **The pack strip** — under the power meters (HP / ⚡ / XP / LV / ◈)
   every scene shows the player's inventory as a row of **32×32
   single-color 1-bit pixel icons**: equipped gear first (weapon, shield,
   armor — hone level shown), then pack items with counts. Hovering an
   item explains what it does and how it helps the climb.

2. **The whisper glyph** — every selection option gets an **[i] on its
   right** with an **instant tooltip** (no browser title-delay) that
   explains the option: what can be achieved there and — above all — how
   it advances the climb. Most important for the town places. Written in
   the game's voice, but unambiguous.

This covers the WHOLE game: creation, Roothollow and all nine buildings,
the tower gate, gate towns, fights (class moves included), warden/boss
keeps, the Relay, the Vault grants desk, the fields, and the Guildhall
faction flows.

## Where the UI actually renders (read first, believe it)

`render.render_scene_fragment` is the single card renderer: the pane's
GAME tab fetches `/pane/scene` → `{fragment, scene_id}` and injects it;
legacy chat cards wrap the same fragment in a document. So **one change
in render.py + SCENE_CSS covers both hosts**. In remote mode the plugin
gets the scene as JSON from worldd (`Scene.from_dict`) and renders
locally — so:

- **tooltip text is looked up render-side by option id** (no schema
  change, no version-skew break against an older worldd);
- **inventory must travel on the Scene** (the plugin has no player doc in
  remote mode) — engine stamps it, `to_dict`/`from_dict` carry it, an old
  worldd simply omits it and the strip doesn't render.

## 1. `icons.py` — the 1-bit icon set

New module `plugin_linear_ascent/icons.py`:

- Icons are hand-drawn **16×16 pixel masks** (strings of `.` / `#`),
  rendered at **32×32** (each art pixel = 2×2 device pixels,
  `shape-rendering: crispEdges`, `image-rendering: pixelated`) — true
  1-bit, single ink, same white-ink-mask-tinted-by-CSS technique as the
  banners. Encoded as inline **SVG data URLs** (one `<rect>` per pixel
  run), zero network, zero files.
- The set (10): `weapon` (blade), `shield`, `armor` (cuirass),
  `medgel` (sealed gel vial), `trauma_kit` (case + cross),
  `trollblood_tonic` (round-bellied bottle), `energy_cell`
  (cell + bolt), `luck_charm` (charm on a cord), `scout_optics`
  (lens pair), `pack` (fallback crate).
- `icon_data_url(key) -> str | None`; gear slugs map by their FORGE
  slot, apothecary slugs map by name, anything unknown falls back to
  `pack`.

## 2. `engine/tips.py` — one registry, the whole game

New module with two tables and two functions:

- `option_tip(option_id) -> str` — exact ids first, then prefix rules:
  - **town buildings** (the priority): `forge`, `medlab`, `lodge`,
    `vault`, `pawn`, `relay`, `fields`, `guildhall`, `stone`, `gate`,
    `muster` — each tip says what the place does, what it costs, and the
    advancement loop it feeds (e.g. the Forge: better ATK/DEF → higher
    floors survivable → more gold/XP per hunt).
  - **gate town**: `hunt`, `heal`, `stew`, `keep`, `town`;
    **lodge**: `sleep`; **vault**: `deposit_all`, `deposit_half`,
    `withdraw_all`, `grants`; **fight**: `attack`, `stand`, `run`,
    `scout`, `drink_tonic`, `shield_wall`, `sleep_spell`,
    `treeline_shot`; **keeps**: `strike`, `boss_commit`;
    **guildhall**: `guild_train`, `found_guild`, `donate`, `enter_week`,
    `kick`, `guild_leave`, the `cancel_*` trio; **relay**: `collect`;
    **creation**: `begin`, the four races, the three classes;
    **navigation**: `town`, `back`.
  - **prefix rules**: `buy_<slug>` (gear tip built from FORGE
    slot/bonus/tier + level req; apothecary tip from the item's effect),
    `hone_<slot>`, `sell_<slug>` (pawn pays 40%), `floor_<n>`,
    `write_<name>`, `grantto_<name>`, `grantamt_<n>`, `join_<name>`,
    `sig_<slug>`, `kick_<name>`, `attack_<name>`.
  - Unknown ids return `""` → no glyph renders. Never a broken [i].
- `item_tip(slug) -> str` — pack-strip tooltips: apothecary items by
  effect ("Medgel — +25 HP from your pack…"), gear by its numbers and
  the sell/re-equip loop, fallback for unknown slugs.

Voice rule: lore-flavored, **numbers included, purpose explicit** —
every tip ends by answering "how does this advance the climb?".

## 3. Engine — the Scene carries the pack

- `engine/scene.py`: `Scene.inventory: list[dict]` (default `[]`), each
  entry `{"slug", "name", "count", "kind"}` where kind ∈
  `weapon|shield|armor|item` (+ `"equipped": True` on worn gear;
  equipped weapon/shield/armor include hone level in the name, e.g.
  "Pigsticker +2"). Serialized in `to_dict`/`from_dict`.
- `engine/core.py `_stamp``: already wraps every scene return — build
  the inventory there when `p["stage"] == "playing"`: equipped gear
  first, then `p["inventory"]` sorted (apothecary before gear-in-pack).
  Creation/intro scenes stay clean (no meters → no strip).

## 4. render.py — the strip and the glyph

- **Options**: each option row becomes
  `<div class="orow"><button class="opt">…</button><span class="info"
  tabindex="0">i</span><span class="tipbox">…</span></div>` — the [i]
  sits OUTSIDE the button (clicking it never fires the option; focusable
  for touch/keyboard). Tooltip is **instant** via one shared
  `#tipbox` (position:fixed, JS-positioned and viewport-clamped —
  pure-CSS tips would clip on the card's `overflow:hidden`); wiring is
  delegated at document level, so the pane's fragment swaps need no
  re-wiring. No tip text → no [i].
- **Pack strip**: after `_meters_html`, `_inventory_html(scene)` renders
  `<div class="inv later">` — one cell per entry: the 32×32 mask-tinted
  icon (equipped = brighter ink, pack = dim), name, ×count, and the same
  instant tooltip carrying `item_tip(slug)`.
- **Meters**: swap the native `title=` tooltips for the same instant
  tipbox mechanism, so every explanation in the card behaves identically.
- All CSS lands in `SCENE_CSS` → the pane inherits everything with zero
  pane.py changes. Chat-card typewriter (`.type`) skips tipboxes so the
  reveal doesn't type hidden text.

## 4b. The gap the strip exposes: unusable healing items

Medgel (+25 HP) and Trauma kit (+80 HP) can be bought and looted but
**no code path consumes them** — a tooltip explaining their purpose
would be a lie. Fix inside this plan: gate-town scenes offer
`use_medgel` / `use_trauma_kit` when the item is carried and HP is
down (the tonic stays the only MID-fight heal, per 013). Heals cap at
max HP, item decrements, ledger row written.

## 5. Tests

- `tests/test_014_inventory_tooltips.py`:
  - icons: every advertised key yields a data-URL; gear slugs resolve by
    slot; unknown → `pack`.
  - tips: every STATIC option id the engine can emit has a non-empty
    tip (walk the registry); prefix rules produce numbers (buy_ shows
    the stat, sell_ the 40%); unknown id → `""`.
  - scene: playing scenes carry inventory (equipped shiv from creation),
    round-trips `to_dict`/`from_dict`; intro/creation scenes carry none.
  - render: fragment contains `.orow` + `.tipbox` for a town scene; the
    pack strip renders icons + counts; an option without a tip renders
    no [i].
  - coverage guard: for a scripted full walk (creation → town → every
    building → gate → fight), **every rendered option has a tip**.
- Scenario `tests/014-inventory-tooltips/scenario-1-pack-and-glyphs.md`
  for the live walkthrough.

## 6. Ship

Vendor into worldd, run both suites, dojo walkthrough (hover a town
option, hover a pack item, verify instant tooltips + icons in the pane),
bump to **0.14.0**, merge to main, deploy worldd to Render, package +
publish to marketplaces.com.ai, verify SHA256.

## Acceptance

- Every scene with meters shows the pack strip beneath them; icons are
  32×32, single-color, 1-bit, crisp.
- Every option in the whole game shows an [i] whose tooltip appears
  instantly on hover/focus and explains purpose + advancement, town
  places most thoroughly.
- Clicking/tapping the [i] never triggers the option.
- Old chat cards and the pane both render the new grammar; remote mode
  against an older worldd degrades gracefully (no strip, tips still
  work).
