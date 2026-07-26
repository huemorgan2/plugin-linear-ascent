# 007 — Forced Multiplayer: one world, mandatory, and visibly alive

Two decisions from the 004 follow-up conversation:

1. **Connection to the shared world is mandatory.** Local single-player
   mode stops being a fallback the player can silently land in; it
   becomes a developer flag. Every real install plays in the one world.
2. **Players must see and feel the crowd.** Not a menu you can visit,
   but presence woven into the scenes you already play.

Two more from the follow-up conversation (2026-07-26):

3. **One boss per level, for everyone, on every floor.** The live
   Warden at the world frontier is a single shared monster: one HP pool
   in `ascent_world`, any climber strikes it for 3⚡, slow regen, and
   when it falls the floor opens for every player. Rewards split by
   damage dealt. (This generalizes Phase 3's "floors 40+" idea to the
   whole climb — the frontier Warden is always shared.) Floors below
   the frontier stay open; their keeps offer per-player echo bouts for
   XP as before.
4. **World news, daily.** A "Morning Crier" scene on the first turn of
   each world day: climber census (how many at the frontier, at the
   bottom, on your floor), the shared Warden's condition, gossip from
   your floor, and the shard's advice on the fastest way to advance.

## Current state (verified in code)

- `runtime.py`: the plugin boots in `local` mode; world mode is opt-in
  via the settings page (vault creds or env). If worldd is unreachable
  or never joined, the player solos a private world without knowing it.
- worldd is already **one shared world**: players are rows keyed
  `(tenant, player)`, and the frontier — plus the social surface
  (stone, happenings, muster) — is shared across tenants
  (`app/game.py`, "frontier is shared across tenants").
- Self-service enrollment exists (`POST /v1/enroll`, rate-limited,
  idempotent per `install_id`) — the plugin can join without any human
  handing out credentials.
- Phase C of 004 already shipped: Muster Roll, free letters,
  happenings. The raw material for "feel the crowd" is live; it just
  is not mandatory and not pushed into the moment-to-moment scenes.

## Phase 1 — mandatory world connection

1. **Auto-enroll at startup.** On plugin load, if no vault creds:
   call `/v1/enroll` with a persistent `install_id` (vault), store the
   returned tenant+secret in the vault, `configure_remote(...)`. The
   settings page's "join" flow becomes a status display (world URL,
   tenant, connection health) plus a "re-check connection" button.
2. **Local backend behind a dev flag.** `ASCENT_DEV_LOCAL=1` (env only,
   never vault/settings) keeps the local backend for tests and dojo
   runs. Without the flag, `runtime.state["local"]` is not consulted
   for play; unit tests set the flag in conftest.
3. **Honest failure scene.** If worldd is unreachable, tools and card
   actions return a real scene — "The lift is down. The Ascent waits."
   with a retry option — instead of silently switching to a private
   world. The agent gets a muted awareness note so it can empathize
   rather than improvise.
4. **Migration for existing local characters.** One-time import: local
   doc (if any) is pushed to the world on first connect if the world
   has no character for this install — nobody loses their climber.
   If both exist, world wins (the local one was the outage shadow).

## Phase 2 — presence in every scene (feel the crowd)

Server-side (worldd `social.inject_world` already decorates docs):

1. **Floor presence counts.** Gate-town and wilds scene eyebrows carry
   "· 3 CLIMBERS HERE TODAY" (distinct players who acted on that floor
   this world-day). Town square: "N climbers awake today, M this hour."
2. **Kill/clear feed lines.** One line in gate-town scene bodies:
   "Torvald felled a marsh wolf here an hour ago." Warden keeps list
   the last few attempts: "2 climbers fell to Brackjaw today; it is
   wounded — 61% HP." (Warden HP persisting per world-day is Phase 3
   groundwork.)
3. **First-clear and milestone broadcasts.** Already in happenings —
   also deliver as a muted agent nudge ("awareness") so the sidekick
   mentions it naturally, and as a line in the next scene.
4. **Arrival letter.** On enrollment, the nearest-level active climber
   is offered a one-tap "welcome the newcomer" letter (letters are
   free now); if none, the Muster Roll is shown in the welcome scene.
5. **Muster Roll on the square.** The town scene body always carries a
   one-line census ("31 climbers · highest camp floor 12 · 4 new this
   week") linking to the full roster location.

## Phase 3 — needing others (mechanical, not cosmetic)

This is 004 Phase D, unchanged in scope, now with a deadline attached
to the progression math (table in `004-difficulty-review/`): solo the
climb stalls at ~floor 40–50 (over-level +9 → +55, ~324 days to 100);
groups are supposed to make 40+ normal-paced.

1. **Shared warden strikes (floors 40+):** warden HP is a world value
   for the day; any climber commits 3⚡ per strike; regen ~8%/hour makes
   solo chipping ~10× slower than a 5-climber day. Class complements:
   warrior strikes shred DEF, archer opens windows (first-strike bonus
   to the next striker), sorcerer slows regen.
2. **Milestone quorums for real** (2 at floor 10 → 12 at floor 100):
   the Guildhall commit window replaces the solo-tuned fallback.

## Order & risks

Phase 1 is small (runtime + settings + one migration) and unblocks
everything. Phase 2 is mostly worldd (`social.py`) with scene string
changes in the engine. Phase 3 is its own execution plan.

Risks: (a) empty-world cold start — presence lines must degrade
gracefully when counts are 0–1 ("the fields are quiet today"), never
fake players; (b) worldd availability becomes hard-required — add a
status ping to the settings page and keep the failure scene honest;
(c) enrollment abuse — already rate-limited per IP, keep an eye on it.
