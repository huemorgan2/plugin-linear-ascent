# Phase 001 — Damage types & defense profiles

Goal: the engine knows WHO is hitting (melee/ranged/magic) and WHAT
they're hitting (armor tier, resist tier, flying, bulwark). Floors 1–10
teach the system one rule per floor. Nothing UI-fancy yet (003 does
that) — but every effect is already spelled out in fight prose.

## Tasks

1. `economy.py`: damage-type map per class; tier multiplier table
   (Low ×0.75 / Med ×0.50 / High ×0.25, physical and magic axes);
   trait gold bumps (armor/resist ×1.1/×1.25/×1.4, flying ×1.2,
   bulwark ×1.5 — replaces `ARMORED_*` multipliers); bulwark HP ×2.2
   +1 armor tier; warden/milestone profile defaults (plan §2.2).
2. `content/schema.py`: `ALLOWED_TRAITS` grows to
   {armor_low, armor_med, armor_high, resist_low, resist_med,
   resist_high, flying, bulwark, slow, fast} (slow/fast priced in 002
   but authorable now); legacy `armored` rejected by lint after content
   migration.
3. `engine/combat.py`: `_player_hit` takes the class damage type —
   magic ignores flat DEF; tier multiplier applied to final damage;
   min-chip ≥1 preserved except melee-vs-flying = 0 with an explaining
   line; treeline-shot double lost vs armor_med+; sleep refused vs
   resist_high; shield-wall counter 0 vs flying.
4. `engine/state.py`: doc version 2 — `ensure_current` adds the class
   basic weapon (basic_bow / worn_staff; shiv renamed Rusted Sword) +
   a pending-event letter for existing archers/sorcerers.
5. Content: floors 1–10 retrofit — floor 1 all-plain (strip the
   goblin's trait), staircase per plan §2.3, each floor 4 encounters
   with at least one good and one bad matchup per class in the band.
6. Vendor sync + worldd deploy; version bump + publish.

## Tests / acceptance

- Unit: tier math table-driven; magic-vs-DEF; flying-vs-melee zero (and
  the ≥1 chip everywhere else); sleep/treeline/shield-wall edges.
- **Matchup sim gate:** at-level reference player of each class vs each
  floor-1..10 profile: intended-victim win rate ≥80%, hard-countered
  win <30% or rounds ≥2× baseline. Committed as a pytest sim like the
  specimen gate.
- Content lint passes (staircase rule: the introducing floor carries
  exactly one monster with the new trait).
- Doc migration: v1 docs (fixtures for each class) upgrade losslessly;
  idempotent on re-run.
- Dojo: fight an armored monster as archer (see the lost double
  explained in prose), as sorcerer (see armor ignored).

Exit: all green, published, worldd synced, `execution_summary.md`.
