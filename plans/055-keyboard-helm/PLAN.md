# 055 — the keyboard helm

Full keyboard control of the game card. The first press of Tab (or any
arrow) lights the first option from the top; arrows walk within a
section; Tab jumps to the next section. Works in the pane (web /play
and the Luna app view) AND in the standalone card view, over every
list-shaped menu: the notices on top, the main options, grid-mode card
walls, and the players grid.

## What exists today

- Digit keys 1–9 already press option rows
  ([pane.py:531-540](../../plugin_linear_ascent/pane.py#L531-L540)); the
  card view has no keys at all beyond native browser Tab.
- Every actionable is already a real `<button>` wired through one door:
  `button.opt` (rows and `gcard` wall cards), `button.nrow` (notices),
  `button.gtile` (sigil tiles), `button.ptile` (player faces),
  `button.pmore`, `button.pclose`
  ([render.py:1516](../../plugin_linear_ascent/render.py#L1516)).
- `:focus-visible` styles exist (aether outline on nrow/gtile; the
  hover ink-flip already covers `.opt:focus-visible` and `.pmore`).

So this plan is a focus CONTROLLER, not a markup rework.

## Design

**Sections** (in DOM order, only those present on the card):

1. notices — `.notices .nrow` (the "waiting for you" board on top)
2. options — `.options button.opt` (rows; in grid scenes these are the
   `gcard` wall cards), plus `.pact` profile actions when shown
3. players — `.pgrid .ptile` + the trailing `.pmore`
4. stray closers — `.pclose` (the Crier's ✕) joins the section it sits
   nearest rather than owning one

**Keys** (dormant while an INPUT/TEXTAREA/SELECT owns the keyboard, or
while the feedback overlay is open — the overlay keeps native Tab):

- First Tab or arrow with nothing focused → focus the first item of the
  first section. This is the "wake" — the highlight appears on the top
  option.
- ↑/↓ — previous/next item in the section, clamped (no wrap) so the
  list edges feel like edges.
- ←/→ — same as ↑/↓ in single-column lists; in grids (gcard wall,
  pgrid) they move one column, ↑/↓ move one ROW (column count read from
  `getComputedStyle(...).gridTemplateColumns`).
- Tab / Shift+Tab — first item of the next / previous section, wrapping
  across the card. preventDefault so the browser never tabs into the
  sound bar mid-card.
- Enter / Space — native button activation (free).
- Escape — blur; the next Tab wakes at the top again.
- Digits 1–9 keep their direct-press behavior, untouched.

**Roving tabindex**: every controlled button gets `tabindex="-1"` from
the controller at wire time; the focused one gets `0`. Native focus is
the highlight — no parallel "selected" class, so `:focus-visible` CSS
is the single source of truth for the look.

**After an act**: the card swaps. If the act was keyboard-driven, the
controller re-wakes on the new card's first option so a run of fights
plays hands-on-keys; mouse-driven acts leave focus asleep.

**Look**: focus mirrors hover exactly. One CSS pass: wherever a rule
says `:hover:not(:disabled)`, add the `:focus-visible` twin (opt rows,
gcards, ptiles, nrow, pmore already have most of it; audit for gaps —
notably `.gcard` and `.ptile` reverse-video flips).

## Files

- **[pane.py](../../plugin_linear_ascent/pane.py)** — new `kbdWire()`
  called from `wireOptions()` (it already runs after every card swap
  and after MORE unfolds): builds the section list from the live DOM,
  sets the roving tabindex, and one document-level keydown handler
  (installed once, guarded like the digit handler at
  [pane.py:531](../../plugin_linear_ascent/pane.py#L531)).
- **[render.py](../../plugin_linear_ascent/render.py)** — the same
  controller, compact, added to the card-actions IIFE
  ([render.py:1512](../../plugin_linear_ascent/render.py#L1512)) so the
  standalone card view (Luna chat card) obeys the same keys. Shared
  grammar, duplicated on purpose — the two scripts ship in different
  documents.
- **render.py CSS** — the focus-twin audit pass described above.

## Tests

- `tests/test_card_actions.py` — the card document carries the
  controller (marker string, e.g. `kbd`) and every controlled button
  class appears in its selector list.
- `tests/test_render.py` — CSS: each hover ink-flip rule has its
  `:focus-visible` twin.
- Manual QA on :8600 — wake on Tab, arrows down the town menu, Tab to
  the players grid, arrows across the 7-column grid, Enter opens a
  profile, Escape sleeps. Feedback overlay keeps native tabbing.

## Out of scope

- The site homepage and admin console (native tab order is fine there).
- The feedback overlay's internals.
- Any markup or server change — this is pure client JS + CSS.
