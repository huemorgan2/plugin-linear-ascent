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
2. **Shared-world migration rehearsal:** export prod player docs
   (worldd, render-production skill), run `ensure_current` v2 over all
   of them locally, diff meters/gear/race outcomes, fix surprises.
   Then: staged deploy — worldd first (engine is backward-tolerant),
   plugin publish after.
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
  003 retro: "no unexplained numbers" has a concrete test now — every
  active modifier must be NAMED on screen (header chip or dossier
  line); run the one-glance check ("why is this fight bad for me")
  on each [i] card the playtest opens.
- Marketplace serves the final version; production worldd healthy.

Exit: 017 done — the tower has teeth, and they're readable.
