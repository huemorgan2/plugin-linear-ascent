# Phase 006 — execution summary

Shipped in plugin **0.23.0**, worldd engine vendored and synced.

## What was built

- **Death economy (§3.6).** Unprotected death (level > 3, daily save
  spent): gold −rng(40–60%), every paid weapon (equipped or stashed)
  rolls 20% gone-for-good, armor/shield/shoes take −50% of a pool in
  wear instead of destruction. Banked gold stays sacred. The death
  scene lists exactly what was lost, with the singular/plural verb
  branch (004's lesson).
- **Weapon Reincarnation Spell.** Held: the death takes NOTHING and
  every weapon and armor piece — equipped pools AND `durability_pack`
  stashes — repairs to full. Each SPARE spell rolls 50% lost, the only
  possible loss on a protected death (Roy's rule).
- **Stone of Undying.** Cancels the death itself: revive mid-fight at
  30% HP, consumed, hold exactly one, one life-guard per fight. The
  free daily save spends BEFORE the stone (free before bought).
- **Relic catalog v1 (§3.7).** 15 relics across three shops, each one
  dramatic effect + one hard limitation, said verbatim on the shelf,
  in the tooltip, and in the refusal prose: four quiver types (poison
  DoT no-stack, slowing −2 spd, piercing, fire ×1.5), weapon oil,
  entangling net, sky-hook, strip potion, curse scroll, polymorph
  dust, veil draught, golden apple (2× overshield, 20% rot/round,
  damage halved), reincarnation spell, stone, severing word.
  DI-anchored prices via `relic_price` + `_pretty` (two leading
  digits); stock filtered by shop / unlocked floor / class.
- **Fight integration.** `_relic_options` shows an option only when
  the relic can do its thing (nets never on Wardens, hooks only on
  flyers, strip only on spellguard). Nocking is free; the special
  arrow rides the next shot including the treeline shot. `_fx_tick`
  runs venom/apple upkeep once per round-spending action. Every
  effect and every refusal is NAMED on screen (003 law).
- **Faucets & pawn (§3.8).** Alpha charm 30%→10%, warden charm
  40%→12% (named constants). Pawn buyback is now `pawn_rate(day)` —
  deterministic 25–55% by world day, same for everyone; relics can be
  pawned too.
- **Icons.** 11 new 1-bit glyphs (quiver shared by the four arrow
  packs, oil, net, hook, scroll, dust, draught, apple, sigil, stone,
  severing ring) — drawn in the same commit, and the shop option rows
  now resolve relic glyphs too (`_opt_gear_icon` gap found by the
  dojo screenshot, exactly as 004 predicted).

## Tuned in execution (the 005 retro rule, applied)

- **Reincarnation Spell 1.0 DI → 0.5 DI.** Expected unprotected death
  cost (carrying a day's gold): 0.60 DI at band 2, 0.83 at band 3,
  1.07 at band 4, rising to 2.5 at band 10. At 1.0 DI the spell was
  only EV-positive from band 4; the plan's own gate says band 2.
- **Warden charm 15% → 12%.** The gate is ≤ 1/3 of the old 40% rate;
  15 missed by a hair.

## Verification

- **371 plugin tests green** (42 new in `test_017_death_relics.py`:
  catalog law, shop wiring, hold-1/class refusals, pawn rate walk,
  every relic effect + its limitation, the full death matrix
  including a 300-trial weapon-loss rate check and a 200-trial spare
  -leak rate check, faucet gate, and the three economy gates).
- **48 worldd tests green** after vendor sync.
- **Economy gates:** death cost climbs smoothly 0.6→2.5 DI with no
  band cliff >0.5 DI; one spell strictly cheaper than the death it
  cancels at every band; hoarding-3 leak ≥0.4 DI per protected death;
  combined drain (repairs + rational death line) ≤40% of DI per band.
- **Dojo (browser, real screens):** Forge shelf renders all six
  warrior relics with effect+catch and "(you hold 1)"; relic rows
  wear their own glyphs; Stone hold-1 refusal on screen ("One,
  exactly", gold untouched); oil use names its buff; Stone revive at
  88/292 HP mid-fight; protected death showed "nothing is lost /
  every weapon and armor piece stands repaired" and "− 2 SPARE spells
  lost in the flare" (both spares leaked — the dissuasion, live);
  DB confirmed pools back to 1300. Unprotected death: "− ◈ 37,694
  carried gold (47%), gone", guards at 650/1300, bank untouched,
  weapon survived its rolls. Poison arrows: free nock, "18 true
  damage a round, 3 rounds, past any plate", second dose refused.

## Learnings for later phases

1. **Shop shelves scale as prose.** Six relics = six body lines and
   the Forge page is now LONG. Phase 007's town reorder and any
   phase adding shop stock should consider a collapsed
   `<details>` shelf once a shop crosses ~8 prose rows.
2. **Option-icon resolution is a separate surface.** The pack strip
   picked up relic glyphs automatically; the shop OPTION rows needed
   their own hook (`_opt_gear_icon`). Any new item family must wire
   BOTH — and only the browser screenshot catches the miss.
3. **EV gates before prices.** Both 006 tunings (spell DI, charm pct)
   fell out of writing the gate arithmetic first. The 007 armory tax
   and 008 band retunes should state their EV inequality in the plan
   BEFORE constants are chosen.
4. **Injected-state dojo works mid-fight.** `jsonb_set` on the live
   encounter (atk 999, hp 1, death_save true) drives death paths in
   seconds. The 007/008 dojo lists should lean on it for rare paths
   (armory races, flyer bands) instead of long natural fights.
