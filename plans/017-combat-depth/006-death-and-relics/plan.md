# Phase 006 — Death economy & the relic catalog

Goal: death gets its decided shape (random gold+weapon loss, cancelled
by the Weapon Reincarnation Spell) and the relic catalog v1 ships —
every relic one dramatic effect + one hard limitation. Faucets tighten
so the new sinks matter.

## Tasks

1. `engine/combat.py` `_death` rework (plan §3.6):
   - level > 3, unprotected: gold −rng(40–60%); each paid weapon rolls
     20% gone; armor/shield/shoes take −50% durability (never destroyed
     by death anymore).
   - Protected: consume one Reincarnation Spell — nothing lost, all
     weapons+armor repaired to full; each SPARE spell rolls 50% lost
     (the only possible loss on a protected death — Roy's rule).
   - death_save + mercy (L≤3) unchanged; death scene lists exactly what
     was lost/saved.
2. `economy.py`: relic table v1 (plan §3.7 — items, DI-anchored prices,
   band availability, exclusivity groups); faucet cuts (alpha charm
   10%, warden charm 15%); pawn variable rate 25–55% by world_day.
3. `engine/combat.py` relic effects: quiver arrow types (poison DoT
   no-stack, slowing −2 spd, piercing, fire), oils, net, sky-hook,
   strip potion, curse scroll, polymorph (skip, no loot/XP), veil,
   golden apple (overshield + half damage), stone of undying (30% HP
   revive, hold-1), severing word (non-Warden instakill, hold-1).
   Life-insurance exclusivity: one of Stone/Apple/Veil per fight.
4. `engine/core.py`: shop stock wiring (Forge quiver/tools, Arcanum
   mage relics, apothecary insurance); pawn scene shows today's rate;
   hold-1 purchase refusals.
   003 retro: relic inspection (effect + limitation) should be a
   structured payload rendered as a `<details>` dossier, not prose —
   the [i]-card pattern (zero JS, agent reads the same facts via
   `to_text`). Active relic effects in a fight must be NAMED on
   screen (002/003 lesson: unexplained number changes read as bugs).
   004 retro: ~14 new relics = ~14 new 1-bit glyphs (quiver types can
   share the arrow grid with tint variants like the 008 specimen
   inks). Draw them in the same commit — only the dojo screenshot
   catches a relic wearing the pack-crate fallback. Death-scene loss
   lists join gear names: verb agreement needs the singular/plural
   branch (004's "focus soak" bug).
5. Vendor sync + deploy; version bump + publish.

## Tests / acceptance

- Unit: every relic effect + its limitation (no-stack, hold-1,
  not-on-Wardens, spare-spell leak, exclusivity refusal); death matrix
  (mercy / save / unprotected / protected / protected-with-spares).
- 002 retro: the slowing arrow (−2 spd) feeds straight into the chase
  curves — a fast (7) monster slowed to 5 loses its close pressure
  (p_close 0.55→0.25) AND its counter status. Sim the archer-vs-fast
  matchup with slowing arrows equipped; price/availability must keep
  it a purchased answer, not a free one. Fight-test helpers: pin
  `encounter["range"]` explicitly (002 made range part of every fight).
- **Economy sim gate:** expected unprotected death cost at band 2–4 ≈
  1–2 hunting days (visible sting, not a wipe); one held Reincarnation
  Spell is EV-positive by band 2 (the intended buy); hoarding 3+ is
  EV-negative vs banking (the intended dissuasion); charm faucet ≤ 1/3
  of today's rate in sim.
- Dojo: die unprotected (read the loss list); die holding one spell
  (nothing lost, gear repaired); die holding three (watch a spare
  leak); try to buy a second Stone of Undying (refused).

Exit: all green, published, worldd synced, `execution_summary.md`.
