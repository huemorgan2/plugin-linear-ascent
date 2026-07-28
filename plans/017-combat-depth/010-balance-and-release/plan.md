# Phase 010 — Balance retune & release

Goal: the whole overhaul plays as one game. Full-economy retune pass,
shared-world migration check, end-to-end dojo playtest, release.

## Tasks

1. **Retune pass:** run ALL sim gates together (matchup, chase,
   economy, death, days-in-tier) and fix the numbers that only break in
   combination — e.g. repair drag + death loss + relic spend stacking
   on the same income. Amend `plan.md` §2–3 constants in place with a
   dated note for every change.
   005 retro: the repair tax is live at ~8→12% of daily income per
   band (`test_017_durability.py` gates ≤20% and ≤10 pp between
   bands) — the stacked-drain budget for death + relics starts from
   there, and 005's lesson stands: express every drain as a fraction
   of `daily_income` per band BEFORE touching constants.
   006 retro: the stacked-drain gate exists now —
   `test_017_death_relics.py::test_the_combined_drain_leaves_room_to_climb`
   models repairs + the rational death line (min(unprotected cost,
   spell price) / 4 days) under a 40% ceiling. The retune must extend
   it with the relic consumable spend (quivers, oils) at each band's
   intended usage rate, not replace it. Shipped anchors to retune
   AROUND: spell 0.5 DI (EV-positive from band 2 by ~0.1 DI — thin on
   purpose), death cost 0.6→2.5 DI band 2→10, charms 10%/12%,
   pawn 25–55%.
   007 retro: the armory is economically NEUTRAL by construction (no
   gold crosses its boundary, wear rides through) — the retune can
   ignore it as a faucet/sink and only sanity-check its caps
   (50 rows, one take/day). That's the pattern worth repeating: when
   a new system can be written so the exploit inequality is zero by
   definition, no tuning budget is spent guarding it.
   008 retro — two tools and two rules the retune inherits:
   - WEIGHTS are the smoothing knob. Trait placement is design; the
     per-floor weighted mix is tunable by integer encounter weights
     without touching any pool/spread lint.
     `plans/.../008-.../tune_weights.py` runs greedy search against
     the exact gate math (imports `tests/test_smoothness.py`) — rerun
     it after ANY income/trait retune instead of hand-poking floors.
   - Drag is measured over VICTORIES only (deaths end fights early
     and flatter the very monsters that kill you), and a hard counter
     must not be PREY-GRADE: risky (win ≤75%) or a drag (≥1.6×), never
     safe AND quick (`test_017_bestiary.py`). The playtest should use
     the same words: a counter you farm safely at full speed is a
     content bug, not a tuning knob.
   - Content rule found the hard way: slow+armor_med is prey-grade
     for archers (kiting slow is free — the armor tax never lands).
     Slow armored monsters need armor_high; fast-or-normal speed can
     carry armor_med.
   009 retro — the gates are DAY-PINNED now (`_SIM_DAY = 137` in
   `test_017_damage_types._sim_fight`): every roll keys on
   `(user, world_day, counter)`, so unpinned gates re-rolled each UTC
   morning and marginal matchups flipped with the date (three
   "passing" walls were actually prey-grade: rod_wisp 15, shroud_crab
   66 — an armor_med+slow that slipped 008's own rule — and
   glade_dancers 74; all bumped to high tiers). For the retune this
   means: (a) any test failing "for no reason" after 06:00 UTC is the
   day seed until proven otherwise; (b) when a threshold gate passes,
   check the MARGIN (`plans/.../009-.../scan_walls.py` prints every
   wall's win/drag numbers — rerun it after the retune and treat
   anything within ~0.1× of a bar as unshipped); (c) med tiers barely
   register at reference gear — a wall the player should FEEL wants
   the high tier.
2. **Shared-world migration rehearsal:** export prod player docs
   (worldd, render-production skill), run `ensure_current` v2 over all
   of them locally, diff meters/gear/race outcomes, fix surprises.
   Then: staged deploy — worldd first (engine is backward-tolerant),
   plugin publish after.
   009 retro: the tool exists — `plans/.../009-.../soak.py` runs
   `ensure_current` over every doc (local docker by default, any
   `DATABASE_URL` for prod), reports doc shapes + halfling counts +
   errors, never writes. The local pass covered 1,535 docs / 17
   shapes / zero errors; the rehearsal is that script pointed at the
   prod export. Doc v4 = halfling→human with a one-time registrar
   letter (playing docs only; mid-creation docs migrate silently).
3. **Full dojo playtest** (run-dojo skill, all three classes):
   creation → floor 1 kindergarten → first armored / resistant / flyer
   / fast / bulwark floors → shoes purchase → kite → repair → die
   unprotected → buy a Reincarnation Spell → die protected → Arcanum →
   a relic of each family → [i] cards throughout. DOM timeline +
   screenshots archived.
4. Docs: update `vision/economy.md` with the new systems (it is the
   stated source of `economy.py`); README gameplay section refresh.
5. Release: final version bump, publish, worldd deploy, parent-repo
   pointers, `execution_summary.md` for the phase AND a rollup summary
   for the whole 017 plan.

## Tests / acceptance

- Every sim gate green in one run; no phase's gate regressed.
  001 retro: economy changes legitimately shift frozen baselines
  (e.g. warden stats in `test_008_pace`) — update them deliberately
  with a dated note rather than loosening the assertion; income
  smoothness allows upward steps, forbids down-cliffs/regressions.
  004 retro: run the WORLDD suite in the same pass — the plugin suite
  went green while a worldd test still asserted the pre-017 fight
  grammar (`attack` vs `close_in`); the vendor sync makes worldd's
  tests part of every phase's definition of green, and a "flaky"
  worldd failure is guilty until re-run in isolation proves
  otherwise.
- Migration rehearsal: 100% of prod docs upgrade cleanly; no player
  loses gear, gold, or floors (race change + basic-weapon swap are the
  only visible deltas, both announced in-world).
- Dojo playtest: no dead ends, no unexplained numbers, the sidekick
  speaks only at moments — reviewed against the pre-plan's promises.
  007 retro: "moments" now = death, boss, AND first-contact matchup
  (once per hard-counter type, `matchup_seen` in the doc) — the
  playtest should hear exactly one tip at the first flyer/plate/
  spellguard wall per class and silence at the second. Drive dojo
  clicks by `data-opt` id, and add one navigation after any
  effect-backed click before reading state.
  003 retro: "no unexplained numbers" has a concrete test now — every
  active modifier must be NAMED on screen (header chip or dossier
  line); run the one-glance check ("why is this fight bad for me")
  on each [i] card the playtest opens.
  008 retro: vendor-sync worldd + restart BEFORE the playtest (turns
  resolve in the vendored engine — Luna only renders), teleport per
  band with `plans/.../008-.../dojo/teleport.py`, refill via
  `energy_val`. Expected moment budget from the 008 pass: ~25 hunts
  across nine bands = 2 matchup moments; anything chattier regressed.
  009 retro (browser mechanics + art): restart LUNA too after any art
  lands — `render._fx_data_url` lru-caches misses. On
  `/p/linear-ascent` the pane iframe is the one whose src contains
  `plugin-linear-ascent` (index 3 after brain/talk/voice). After a
  psql doc edit, reload the iframe and wait ~3 s in a SEPARATE
  evaluate — clicks in the same evaluate land on the stale scene.
  `doc->'scene'->>'fx'` is ground truth for which kill ending played
  (expect `<family>_kill_<melee|arrow|magic>` per class on floors
  1–3). If a Veo slug fails twice with error code 13 while others
  pass, reword the prompt ("ghostly/translucent" tripped it); chain
  generator commands with `;` not `&&` — one bad slug aborts the
  whole batch.
- Marketplace serves the final version; production worldd healthy.

Exit: 017 done — the tower has teeth, and they're readable.
