# Phase 003 — Presence: the grounds feel inhabited

Goal: the floor you hunt shows who hunts it with you, right now. Roy's
rule: **hot = acted on this floor within 3 minutes** — the only tier that
counts as "with you". A stale count is worse than a small one.

Independent of 001/002 — can ship any time; warms everything.

## Tasks

1. worldd: per-floor presence from the heartbeat that already exists
   (player row's floor + last_seen, updated on every effect sync). Two
   tiers: hot (≤3 min), camped (≤60 min). Indexed count, cache TTL 30s —
   the TTL must stay under the window or the number lies.
2. World payload: `presence` per relevant floor rides the existing sync —
   no new endpoint for grade-1.
3. Plugin surfaces: gate list ("Floor 12 — 3 hot · 2 camps"), floor
   header ("Ember Gulch — 3 blades hot"), fight scenes refresh it every
   round.
4. Torches block on the floor card: named hot players with a one-word
   status (hunting / at the keep / hurt).
5. Deltas as story: presence changes since the player's last card fold in
   as lines — "two more torches on the ridge since you last looked",
   "Kettle's torch gutters… and flares again".
6. Grade-2 liveness: add `floor_presence` int to `/pane/peek`
   (`routes.py:265`), served from the cached value, lazily refreshed at
   most once/min while the pane is open.
7. Vendor sync + worldd deploy; version bump + publish.

## Tests / acceptance

- A player who acted 2 min ago is hot; 4 min ago is camped; 61 min ago is
  neither. TTL test: cache age can never exceed the hot window.
- Peek contract: `floor_presence` present, cheap (no world round trip on
  the hot path), and monotonic with the underlying count.
- Browser walkthrough with two accounts: watch the count move 1 → 2 → 1
  and the delta lines arrive.
