# Dojo — 017 phase 008: the bestiary at scale

Run 2026-07-28, local Luna (8765) → local worldd (8600), tenant qa007,
real browser via Playwright. Player: the `owner` doc teleported per
band with the reference loadout (`plans/.../008-.../dojo/teleport.py`
mirrors the sim gate's at-level player: level = floor, current-tier
gear, hone 2 behind, full HP).

## The stale-vendor catch (the run's big save)

First fight on floor 15 rendered art + dossier but NO lore and an
untraited profile — while unit tests passed. Cause: the game turns
resolve inside **worldd's vendored engine copy**, which was still on
the 007 sync; Luna's editable plugin install only does the rendering.
Content phases MUST `worldd/tools/vendor_game.sh` + restart worldd
before any dojo conclusion. After the sync, the same hunt produced
traits + lore correctly.

## Scenarios & results

1. **One floor per band, 3-5 hunts each** — floors 15, 25, 35, 45, 55,
   65, 75, 85, 95. Every [i] dossier showed named trait lines and the
   authored lore line; every encounter had creature art. PASS.
   - 15 Ironvale: glow-sick kobold, Red Orc fuel-thief (new art).
   - 25 Barrows: procession-wight (resist_med), passing-bell light
     (resist_low + flying).
   - 35 Webdeep: aisle-runner (fast), rack-weaver (resist_low),
     signal husk (resist_med).
   - 45 Scorch: kiln vulture (flying), kiln goat (plain), kiln
     salamander (resist_med).
   - 55 Frosthold: freeholder giant reads all three rows (plate low +
     bulwark + slow), steading hound (fast).
   - 65 Stormreach: kite-line cutter (fast), column drake
     (resist_low + flying), updraft duelist (flying) — sky band.
   - 75 Gloom: grazing nightmare (resist_low), pasture hound (fast),
     black crake (flying).
   - 85 Hellmarch: warren tough, flue bat (flying).
   - 95 Crown: case moth (flying), exhibit-awake (plate HIGH),
     the curator (resist_med, met as a gold-tinted ALPHA).
2. **Spread is felt** — the warrior always had prey (plain/resist
   monsters) and met its predator (airborne) on 25/45/65/75/85/95;
   fast monsters appeared on 35/55/65/75. PASS.
3. **Matchup moment, not a stream** — ~25 hunts across nine floors
   produced exactly 2 matchup cards in chat (glare moth, black crake),
   each once, each with a tactical read ("It's airborne — your blade
   can't reach it until it dives."). `matchup_seen` in the doc
   confirms per-type once. PASS.
4. **Energy refusal note** — burning all ⚡ produced "You're spent — ⚡
   regenerates one point every 45 minutes. Rest, bank, or read the
   Stone." PASS. (DB gotcha: energy lives in `energy_val`+`energy_ts`,
   not a plain counter — set `energy_val` when refilling in dojo.)

## Screenshots (plans/017-combat-depth/008-bestiary-at-scale/dojo/)

- `008-02-floor15-dossier.png` — new kobold art, dossier open.
- `008-03-floor15-lore.png` — fuel-thief with the italic lore row.
- `008-04-floor35-dossier.png` — Webdeep signal husk, spellguard row.
- `008-05-floor95-dossier.png` — alpha curator, gold tint, Crown band.
