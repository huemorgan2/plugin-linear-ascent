# Phase 007 — execution summary (2026-07-28, v0.24.0)

## What shipped

**Faction armory (worldd + engine).** New `ascent_armory` +
`ascent_armory_takes` tables (migration `009_armory.sql`, additive,
auto-applied on boot). `app/armory.py` holds the three moves: `shelf`
(injected into `w["armory"]` for members, with cap and took-today
flags), `deposit` (via the `armory_deposit` effect from the pawn
scene), `take` (via `armory_take` from the Guildhall desk). The EV law
is structural: no gold ever crosses the armory boundary — deposit
moves `(slug, wear-stash)` out of the doc into a row, take moves the
same pair back, so a donate/take round-trip is worth exactly zero at
any pawn rate. Caps guard the residue: 50 rows per faction, one take
per player per world day, members only both ways, and a taken piece's
wear merges into the pack by `min()` (the worse stash survives — the
one direction laundering could hide in). Race losses (row gone,
cooldown hit between scene and click) hand the piece back or skip the
take and say so by armory-keeper letter — never a silent vanish.

**Matchup moment (the one agent beat).** `combat._hard_counter` maps
the walls per damage type — melee×flying, ranged×armor med+,
magic×resist med+ (soft drags like fast-vs-kiting deliberately
excluded). First encounter per hard-countering TYPE flags
`matchup_seen` in the doc and stamps `event_kind="matchup"` on the
opener; `routes._MOMENT_KINDS` now fires a moment for it with a
dedicated frame that orders the sidekick to name THIS enemy as the
scene names it (001's "Brackjaw" hallucination guard). Everything
else stays silent (0.17.2 holds).

**Town readability.** The Tower Gate leads the square ("leave town
and climb"); Relay locks at level 3 and the fields at level 5
(`economy.RELAY_LEVEL/FIELDS_LEVEL`), both with the Arcanum's
grammar: 🔒 hint row + shard-note refusal, no scene change. Long shop
shelves fold: `_relic_rows` wraps the shelf in ▣ markers when the
page already runs past 8 prose rows; `render.py` turns the markers
into a zero-JS `<details class="fold">`, `to_text` degrades them to a
plain divider.

**Shop owned-state (004 dojo carryover).** The rung on your body
leaves the rack — `_rack` shows "✓ <name> — worn" as a line and the
two buy rows are always NEW steps. Re-buying your own rung is gone
(the pack swap and next-rung purchase cover the legitimate cases).

## Tests

- Plugin: 380 passed (13 new in `test_017_world_agent.py`: matchup
  once-per-type + class map, town order/locks, worn-rung rack, fold
  render/degrade, donate/take engine halves with effects payloads,
  tips). Smoothness gate 4/4 — untouched by this phase, as expected.
- worldd: 53 passed (5 new in `test_armory.py`: full donate→take
  round-trip with gold frozen on both ends, one-take-a-day, cap
  bounce, members-only both ways, min-wear no-launder).
- Dojo (browser, local worldd 8600 + Luna 8765, screenshots in
  `dojo/`): town order + 🔒 rows + refusal note; Forge with ✓ worn
  lines, new-step rows, folded shelf opened by click; pawn donate
  (◈ frozen at 14,995 through the whole loop); Guildhall ARMORY
  section with wear% and donor name; take + next-day cooldown
  ("you already took your piece today", no Take row); glare-moth
  hunt fired exactly one "LINEAR ASCENT — MATCHUP" chat moment that
  named the Pigsticker and the airborne trait.

## Decisions made in execution

- **Take flows through the effects pipeline, not a new HTTP
  endpoint.** The desk is an engine scene; `armory_take` rides
  `execute_effects` like every other social move — same HMAC, same
  doc-in-flight semantics, no new surface. The plan's "endpoints"
  wording was written before 015 moved the desk into the engine.
- **Deposit carries the worn copy first.** The pack keeps one stash
  per slug; donating always pops the stash with the piece, and taking
  merges by `min()` — both ends chosen so wear can only survive or
  worsen, never reset.
- **Cap refusal is engine-side first.** The injected shelf lets
  `_pawn_donate` refuse a full rack before the piece moves; the
  worldd guard behind it only fires on races (and answers by letter).

## Learnings pushed into future plans

- 008: matchup moments now scale with the bestiary — spread rule
  keeps the cadence sane; dojo by `data-opt` ids; act-scenes render
  before effects land.
- 009: same dojo mechanics; ▣ fold available for long scenes.
- 010: the armory is a zero-sum transfer by construction — retune
  ignores it as faucet/sink; playtest listens for exactly one matchup
  tip per wall per class.

## Gotchas hit

- Playwright label regexes (`^Run$`) silently miss buttons — the
  rendered text embeds the key digit and [i] glyph. `data-opt` ids
  are the only stable hooks.
- The worldd dev DB had accumulated a dozen stale level-97 players
  from prior `test_muster_roll` runs, filling the capped board — the
  test now sweeps its own leftovers first.
- `ascent_players` docs mid-fight keep a CACHED scene: every DB edit
  in dojo still needs one navigation click before reading the screen
  (005 rule, held).
