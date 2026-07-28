# 017 — Combat depth: plan execution summary

Ten phases, shipped one at a time (each with unit tests, a real-browser
dojo test, publish + deploy, an execution summary, and a retro that
amended every future phase plan before the next began). The plugin went
from v0.17.x to **v0.27.0**; every release is live on the marketplace
and the worldd vendor is deployed on Render.

## What the plan delivered

Combat went from "attack until the bar empties" to a game about
reading the enemy and bringing the right tool:

- **Damage types & counters (001, 0.18.0)** — melee/arrow/magic vs
  armor/resist/evasion tiers; every monster floor 1–10 got a profile.
- **Speed & chase (002, 0.19.0)** — range, closing, flee/chase; slow
  bruisers and fast skirmishers feel different before the first hit.
- **Enemy [i] dossier (003, 0.20.0)** — every modifier the fight card
  uses is named and explained one tap away; zero unexplained numbers.
- **Shops, rungs, shoes, Arcanum (004, 0.21.0)** — the gear ladder and
  the counter tools became purchasable progression.
- **Durability (005, 0.22.0)** — gear wears, repairs cost 8–12% of
  daily income; the pawn rate went variable.
- **Death & relics (006, 0.23.0)** — 40–60% carried gold on death,
  20% weapon roll, half durability pool; the Reincarnation Spell and
  the shardmind's once-a-day save (which fires FIRST).
- **Armory, matchup moment, town (007, 0.24.0)** — shared armory,
  first-contact matchup lines on a strict once-per-type budget, town
  readability.
- **Bestiary at scale (008, 0.25.0)** — floors 11–100 fully populated;
  gate math (win ≤ 0.75 for the countered class OR drag ≥ 1.6×) and
  `tune_weights.py`, the greedy integer-weight search that is the
  income-smoothness knob.
- **Races, movies, kill FX (009, 0.26.0)** — halfling retired (doc v4
  migration with an in-world registrar letter), three showcase
  characters, the intro movie reshot, 18 typed kill GIFs, icon audit.
- **Balance & release (010, 0.27.0)** — margin scan (near-margin walls
  count as unshipped), six retraits + weight re-tune, stacked-drain
  gate extended with the daily wall-push, consumable reprice (vials
  0.1 DI, quivers 0.2), prod migration rehearsal (8/8 docs clean),
  docs refresh, and a three-class release playtest in a real browser.

## The economy, as shipped

Daily income is the unit. Repairs 8–12%, the rational death line
~12.5%, one wall-push 8–12% per class — the stacked total ≤ 40% for
every class at every tier (gated). Consumables are progression tools,
not farming tools: every breaker costs more than a kill pays.
Income smoothness across all 100 floors is gated per class; margins
(not just passes) are scanned.

## Process notes that made this work

- **Phased execution with retro-propagation**: after each phase's
  summary, every future phase plan was amended with what was learned —
  by 010 the plan already contained the vendor-sync checklist, the
  restart checklist, the day-pin rule, and the browser mechanics.
- **Dojo tests are non-negotiable**: a real browser, real agent
  conversation, screenshots actually read. They caught things no unit
  test could — stale lru caches, per-shot arrow consumption, the
  matchup moment's silence budget, the in-fiction timeout UX.
- **Pin the world day in sims** (`_SIM_DAY = 137`): RNG keys on
  `(user, world_day, counter)`; unpinned gates re-roll every 06:00 UTC.
- **Weights are the smoothing knob**: never hand-poke floors after a
  trait retune — rerun `tune_weights.py`.
- **Stale-vendor trap**: turns resolve in worldd's vendored engine;
  the full ship checklist is vendor sync → restart worldd → restart
  Luna (art caches miss forever otherwise).

Per-phase details live in each phase's `execution_summary.md`; the
010 playtest record is `tests/017-combat-depth-010/01-release-playtest.md`.
