# Phase 008 — execution summary

Shipped as plugin v0.25.0 + worldd vendor sync. The whole tower speaks
the counter language: floors 11-100 retrofitted from 3 flat encounters
each to 4-5 traited, lored, illustrated encounters with a deliberate
per-band spread.

## What was built

- **Content, 90 floors in 9 band batches** (Ironvale → The Crown).
  Every encounter on floors 11+ now carries `lore:` (≤160 chars, prose
  lint) and the band's trait story: armor in the fusion-halls and
  knight bands, resist in the bio-lit and haunted bands, flyers dense
  in Stormreach, plus ≥1 fast, ≥1 slow, ≥1 bulwark per band. 100 new
  encounters authored; specs live in `bands/band_*.py` and are applied
  by `tools/patch_floor_content.py` (formatting-preserving).
- **Lint at scale** (`content/schema.py`): floors 11+ require 4-5
  encounters, lore everywhere, ≥2 full-damage hunts per class per
  floor, and the band spread rule (armor_med+, resist_med+, flying,
  bulwark, fast, slow present in every 10-floor band).
- **Art**: 75 new 1-bit creature banners (Gemini pipeline), every
  encounter id covered — `test_011_art.py` gate green with zero
  skips.
- **At-scale sim gate** (`tests/test_017_bestiary.py`): the 001
  matchup gate run over every floor 11-100 × class — prey dies ≥80%,
  ≥2 viable hunts per floor per class, and every hard counter is FELT
  (risky win ≤75% or drag ≥1.6× — never safe AND quick). Lore-to-
  dossier payload asserted per band.
- **Weight tuner** (`tune_weights.py` in this folder): greedy search
  over integer encounter weights against the exact smoothness-gate
  math; smoothed the income curve after traits changed it (19 weights
  moved, zero trait/pool/spread lint impact).

## Tuning decisions

- **Wins-only drag.** Averaging rounds over all fights let the
  deadliest monsters (45% win) read as "not dragging" because deaths
  end fights early. Drag now = rounds over victories.
- **"Felt" instead of "walls".** At scale the 30%-win wall test failed
  legit counters: an armor_med knight at 45% win IS felt (006 death
  economy makes 1-in-4 deaths ruinous EV). The gate now fails only
  prey-grade counters (safe AND quick).
- **slow+armor_med is prey-grade for archers** — kiting a slow monster
  is free, so the armor tax never lands. Eleven such monsters deepened
  to armor_high; the slow bulwark stallion went normal-speed.
- **Income smoothing by weights, not traits.** Trait gold mults made
  the per-floor paycheck swing 1.04-1.32 with six >10% down-cliffs;
  re-weighting encounters (bulwarks stay ≤2) fixed all of them without
  touching design texture.

## Verification

- 386 plugin tests green, including all prior 017 gates (smoothness,
  shops, durability, death/relics, damage types, speed/chase).
- Dojo in a real browser (`tests/017-combat-depth-008/01-bestiary-dojo.md`):
  nine bands spot-checked (floors 15-95), dossiers show named traits +
  lore, new art renders, alpha tint works, matchup moments fired
  exactly once per predator (2 in ~25 hunts), energy refusal correct.

## Learnings (propagated to 009/010 plans + dojo skill)

1. **The stale-vendor trap**: turns resolve in worldd's vendored
   engine; Luna renders. The first dojo fight had art but no lore —
   unit tests can't catch it. Vendor-sync + worldd restart is now a
   dojo precondition in the skill.
2. Content authoring at this scale needs a patch script + per-band
   spec files; hand-editing 90 YAMLs would have destroyed formatting
   and taken days. ~2.5k lines of spec applied cleanly.
3. Sim-gate semantics drift at scale — revisit measurement (wins-only)
   before revisiting design when a gate fails en masse with one shape.
4. The weight knob is free smoothing: it can't break lint and the
   optimizer converges in seconds. Keep design in traits, balance in
   weights.
