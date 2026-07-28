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
- Marketplace serves the final version; production worldd healthy.

Exit: 017 done — the tower has teeth, and they're readable.
