# Phase 010 — Balance retune & release

Goal: the whole overhaul plays as one game. Full-economy retune pass,
shared-world migration check, end-to-end dojo playtest, release.

## Tasks

1. **Retune pass:** run ALL sim gates together (matchup, chase,
   economy, death, days-in-tier) and fix the numbers that only break in
   combination — e.g. repair drag + death loss + relic spend stacking
   on the same income. Amend `plan.md` §2–3 constants in place with a
   dated note for every change.
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
- Migration rehearsal: 100% of prod docs upgrade cleanly; no player
  loses gear, gold, or floors (race change + basic-weapon swap are the
  only visible deltas, both announced in-world).
- Dojo playtest: no dead ends, no unexplained numbers, the sidekick
  speaks only at moments — reviewed against the pre-plan's promises.
- Marketplace serves the final version; production worldd healthy.

Exit: 017 done — the tower has teeth, and they're readable.
