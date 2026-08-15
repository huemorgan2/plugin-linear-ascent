# 060 — the Playing button speaks: notices from the tower's pulse

Every happening in the game (the same rows the Playing panel lists)
surfaces as a small notice popping out of the **▶ playing** button in
the sound bar — even while the panel is closed. Wide and low, one line
each, a caret pointing down at the button so it is obvious where it
comes from, an ✕ top-right, gone on its own after 3 seconds. Several at
once stack upward. Two switches inside the Playing panel — **world
notices on/off**, **faction notices on/off** — both on by default.

Rides the 2 s `/pane/peek` poll exactly as it is. No new poll, no push.

## Mechanism

Client (`pane.py`, the 056 block):

- New cursor `ply.seen`. First peek that carries `feed_head` sets
  `seen = head` (no burst of history on page load). On a later peek
  where `head > seen` and at least one switch is on: one
  `GET /pane/playing/feed?scope=both&since=<seen>`; then `seen = head`.
  Rows come back newest-first with a `scope` field; the client shows
  those the switches allow, oldest first, capped at 4 per burst (the
  rest are dropped silently — the panel has them).
- Both switches off ⇒ no fetch at all; the peek's two ints remain the
  whole cost, as 056 promised.
- If the panel is open, the same rows are also merged into `ply.rows`
  (no double fetch when the panel is open: `plyLoad` sets `seen` too).
- Luna door: its `/pane/peek` echoes a 60 s-cached `feed_head`, so
  toasts there lag up to a minute. Acceptable; noted.

Server (`worldd/app/social.py:playing_feed`):

- `scope == "both"`: `WHERE (scope='world' OR faction=$mine) AND id > $since`
  (for a memberless caller: world only). Rows carry `scope`.
- In-process cache so a world-wide burst of closed panels never lines
  up on Postgres: `_feed_cache[key] = (head, rows)` where key is
  `"world"` or `f"faction:{name}"`, holding the newest `FEED_LIMIT`
  rows; served when the entry's head equals the current head, filtered
  `id > since` in Python; refilled from the DB otherwise. `add_happening`
  already bumps the head, which invalidates every entry.
- HMAC twin `/v1/playing_feed` and the Luna proxy already pass `scope`
  through unchanged (`PlayingFeedIn.scope` ≤ 16 chars).

## The toast

- Container `#plytoasts`, `position:fixed`, bottom = sound bar height +
  10 px, centered horizontally over `#plybtn` (left computed from the
  button's rect on each show, clamped to the viewport), `width:min(720px,
  calc(100vw - 24px))`, `display:flex; flex-direction:column-reverse;
  gap:6px` — newest nearest the button.
- Each `.plytoast`: ink background, `TEXT` border, one line
  (`white-space:nowrap; overflow:hidden; text-overflow:ellipsis`),
  `padding:6px 3ch 6px 1.5ch`, small eyebrow `PLAYING ·` in `DIM` before
  the line, `F{floor}` tag faint on the right, ✕ button absolute
  top-right. Kind tints as the panel: `war` gold, `boss` aether.
- The bottom-most toast draws a caret (`::after`, 8 px rotated square)
  pointing down at the button.
- Enter: slide up 6 px + fade, `steps(4,end)`; auto-remove after 3000 ms
  (timer per toast); ✕ removes at once. `prefers-reduced-motion`: no
  transition.
- Nothing while `document.hidden` (peek already bails).

## The switches

- Rendered in `plyRender` under the tabs:
  `notices: [world on] [faction on]` as `.plytab`-styled toggle buttons
  with `aria-pressed`; click flips and repaints, no reload.
- Persisted in localStorage `la_ply_world` / `la_ply_faction`
  (`'1'`/`'0'`, default on) — same store shape as `sfx.py:41`, three-line
  local copy in the pane IIFE.
- The faction switch renders regardless of membership (a memberless
  climber simply never receives faction rows).

## Tests

- worldd `tests/test_060_playing_toasts.py`: `scope=both` returns world
  rows plus my faction's rows and not another faction's; memberless
  caller gets world only; every row carries `scope`; the cache serves
  the same head without a DB hit (monkeypatch `conn.fetch` to raise
  after warm-up) and refills after `add_happening`.
- plugin `tests/test_060_playing_toasts.py`: `render_pane()` contains
  `#plytoasts`, `la_ply_world`, `la_ply_faction`, `scope=both`, and the
  ✕ button markup; the toast lifetime constant is 3000.

## Order

1. Server: `scope=both` + row `scope` + the cache + tests.
2. Client: `seen` cursor, toast container/CSS/JS, switches, tests.
3. Bump, vendor, commit both repos.
