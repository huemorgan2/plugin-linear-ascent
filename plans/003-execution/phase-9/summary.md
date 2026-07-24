# Phase 9 — execution summary (FINAL: everything in production)

Status: **shipped end to end.** Luna core 056 landed and was verified live;
plugin 0.3.1 published; worldd redeployed with vendor sync.

## Luna core (056, implemented by Luna, verified here)

Pulled `luna` @ 0.47.004: `post_chat_card` SDK + card history exclusion,
`kind:"card"` bubble-less full-width render, `luna:embed:height` auto-size
(source-checked, 900px cap), empty-bubble suppression, dojo fixture — plus
the 057 card-action bridge and `send_muted_message`. Rebuilt the UI
(`pnpm build` in `luna/ui` — the served bundle is `ui/dist`, NOT committed;
a rebuild is required after every pull that touches `ui/src`).

Live verification on QA Luna (8777), in **world mode against production
worldd** (tenant `roys-luna-38c3d3d2`):

- Scene card renders as its own timeline row: `data-testid="card-row"`,
  full message-column width (724px at 1280 viewport), **no avatar, no
  bubble, no inner scroll** (532px = exact content height; auto-height on
  first paint for live-appended cards).
- Mid-turn cards live-append without refetch; reload reproduces the exact
  chronological timeline (card between tool receipt and reply).
- Sidekick voice: "◆ First floor. Only way is forward." / "Scrappy mutt's
  still standing. Keep at it." — short flavor beats, zero card narration.
- Phase-8 regression: settings status OK, vault join intact, world health
  green.

### Fork followup we contributed (branch `056-followup-card-ordering`)

`message.created` events can reach the global SSE after the turn's rows
are committed, appending live cards out of order. The emit now carries the
row's server `created_at` and the UI live-append inserts by timestamp.
Pushed to `huemorgan/luna` for Luna to merge. (Note: within a streaming
turn Luna renders the text bubble above its tool receipts by design —
that's her turn-block convention, not a bug; reload shows true order.)

## Plugin 0.3.1 (published, sha256 verified against the index)

- **Resize re-report fix** (this session): the card height script now also
  listens to `window` resize and observes `body` — documentElement's
  ResizeObserver misses host-side iframe resizes, which left stale heights
  after layout changes.
- **Clickable card options (057, from the parallel session, shipped
  here)**: option buttons in the card post `card-action` to the host
  bridge; `POST /api/p/plugin-linear-ascent/act` runs the pure engine loop
  (no model in the path) and posts the next scene as a new card.
  Death/boss beats fire a real sidekick reaction via `send_muted_message`;
  present/letter/loot land as awareness for the next turn; ordinary scenes
  stay silent. Verified live: bogus option → steering card posted, agent
  untouched.
- Voice rules extended: the model is told the player can click cards
  directly and to re-sync via `ascent_scene` when the player's words don't
  match its last-seen scene.
- Tests 42/42 (incl. new `test_card_actions.py`).

## worldd

- Vendor sync (21 py / 100 yaml), tests 13/13 (one drive-contention flake,
  green in isolation), redeployed via `git push origin main` (Render
  blueprint). Health verified post-deploy.
- No schema/API changes this phase.

## Production state

- worldd: `https://ascent-worldd.onrender.com` — healthy, world day
  rolling.
- Marketplace: `official/plugin-linear-ascent` **0.3.1**, sha256 matches
  local artifact.
- Luna fork: 0.47.004 + `056-followup-card-ordering` (PR-able).
