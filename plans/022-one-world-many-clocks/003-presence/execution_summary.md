# Phase 003 — Presence: execution summary

Status: **done** (deploy + version bump deferred to the end of the 022
run; the browser walkthrough batched into the final pass). 508 plugin
tests + 61 worldd tests green.

## What shipped

- **worldd** (`app/social.py`): `_presence(conn)` — one query over
  players active within the hour, aggregated into
  `{"by_floor": {floor: {hot, camped}}, "torches": {floor: [...]}}`.
  Hot = acted ≤ 3 min, camped = ≤ 60 min (Roy's tiers), cached 30
  seconds (`PRESENCE_TTL_S` — gated strictly under the hot window so
  the number can never be staler than the tier it claims). Torch
  entries carry a derived one-word status: hurt (< 40% HP), at the
  keep, hunting, at the fire. **Only field locations count** —
  `gate_town` / `warden_keep` / `boss_keep` or a live encounter; a
  climber idling in Roothollow keeps a floor number in the doc but is
  not "with you".
- **Injection**: `w["presence"]` rides the existing per-act sync — no
  new endpoint for grade 1. Torches inject for ALL floors, not just the
  doc's current one: injection runs BEFORE the act, and the act may be
  the move onto a new floor.
- **Plugin surfaces** (all degrade to silence without a world):
  - gate list rows append " · 3 hot · 2 camps";
  - the floor card opens with "N blades hot on this floor." (or the
    camped-only "embers, not company" line), then the torch block —
    named hot climbers with status, own torch filtered out;
  - fight scenes re-read the count every round and fold changes in as
    story ("Another torch on the ridge since you last looked." / "A
    torch has guttered out…") via a `presence_seen` watermark on the
    doc. Data helpers live in `state.py` (combat cannot import core).
- **Grade-2 liveness**: `/pane/peek` now returns `floor_presence` from
  an in-process per-user cache (`runtime.floor_presence`) refreshed via
  the new signed `POST /v1/presence` at most once a minute; the hot
  path never leaves the process, and a failed refresh keeps the last
  honest number.

## Learnings

1. **Emoji gate**: the first cut used a 🔥 marker on presence lines —
   `test_no_emoji` rightly refused it (1-bit design language, only
   ⚡/🔒 renderer markers exist). Presence speaks in words.
2. **Injection order matters**: torches for "the player's floor" would
   have been the WRONG floor on every move (inject runs pre-act) —
   shipping the whole per-floor torch dict and letting the engine pick
   is both simpler and correct.
3. **Auth's first refusal is 426** (missing API version header), not
   401 — worth remembering for every future endpoint test.

## Deliberately not done

- No new worldd round trip for grade-1 surfaces (rides injection).
- No presence for Roothollow itself — floors only; the square already
  has the census line in the Crier.
- Browser walkthrough (two accounts, count breathing 1 → 2 → 1)
  batched into the end-of-run agent-live-walkthrough pass.

## Files

`worldd/app/social.py` (presence + cache), `worldd/app/main.py`
(`/v1/presence`), `plugin_linear_ascent/engine/state.py` (presence
reads + delta watermark), `engine/core.py` (gate hints, floor card,
torch block), `engine/combat.py` (round refresh), `runtime.py` (peek
cache), `routes.py` (peek contract), `backend/remote.py` (client),
`tests/test_022_003_presence.py` (9 gates),
`worldd/tests/test_presence.py` (6 gates).
