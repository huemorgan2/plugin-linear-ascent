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
   - 005 retro: wear lives on the ITEM — a weapon lost to death must
     drop its `durability_pack` stash too; the Reincarnation "repaired
     to full" means both equipped `durability` pools AND every stash
     in `durability_pack` (spell prose promises "all weapons+armor").
     The −50% durability hit uses `economy.item_pool(g)` (rung-aware),
     never `durability_pool(g.tier)`.
2. `economy.py`: relic table v1 (plan §3.7 — items, DI-anchored prices,
   band availability, exclusivity groups); faucet cuts (alpha charm
   10%, warden charm 15%); pawn variable rate 25–55% by world_day.
   **Tuned in execution:** Reincarnation Spell 1.0 DI → **0.5 DI** —
   at 1.0 the spell only beat the expected unprotected death cost
   (0.60 DI at band 2, 0.83 at band 3) from band 4 on; the plan's own
   gate says "EV-positive by band 2". Warden charm 15% → **12%** — the
   gate is ≤ 1/3 of the old 40% and 15 missed it by a hair. Both live
   as named constants (`ALPHA_CHARM_PCT`, `WARDEN_CHARM_PCT`).
3. `engine/combat.py` relic effects: quiver arrow types (poison DoT
   no-stack, slowing −2 spd, piercing, fire), oils, net, sky-hook,
   strip potion, curse scroll, polymorph (skip, no loot/XP), veil,
   golden apple (overshield + half damage), stone of undying (30% HP
   revive, hold-1), severing word (non-Warden instakill, hold-1).
   Life-insurance exclusivity: one of Stone/Apple/Veil per fight.
4. `engine/core.py`: shop stock wiring (Forge quiver/tools, Arcanum
   mage relics, apothecary insurance); pawn scene shows today's rate;
   hold-1 purchase refusals.
   **Shipped as prose, deliberately:** each shelf row is ONE line
   (name — effect. The catch: limit.) — the [i]-card dossier pattern
   earns its keep on stat-dense payloads, not one-liners; the law is
   already said verbatim on the shelf, in the tooltip, and in
   `to_text` for the agent, with zero new render surface.
   Original note — 003 retro: relic inspection (effect + limitation)
   should be a structured payload rendered as a `<details>` dossier,
   not prose —
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
  005 retro (hard rule): compute every recurring cost as a fraction of
  `daily_income` at EVERY band IN THE PLAN before coding — 005's pool
  curve read fine as flavor and missed the gate by 14× at T10. Death
  cost + repair tax + relic prices must be summed per band: the
  combined drain at-level must stay under ~40% of income or the climb
  stalls.
- Dojo: die unprotected (read the loss list); die holding one spell
  (nothing lost, gear repaired); die holding three (watch a spare
  leak); try to buy a second Stone of Undying (refused).

Exit: all green, published, worldd synced, `execution_summary.md`.
