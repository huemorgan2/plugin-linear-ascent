# Phase 1 — execution summary

Status: **engine complete, unit-tested; browser-verified for the core path** (full multi-day dojo scheduled with the consolidated run).

## Built (all in phase 0's push — the engine shipped whole)

- Creation flow with stage gates and steering refusals (race → class → free-text name).
- Roothollow: Forge (tier catalog, buy/equip/auto-pack old), Apothecary & Medlab (7 items, 1/day caps on cell & philtre), Lodge (10×level, lodged-until-day), Vault (5%/day compound credited on visit; deposit/withdraw), pawn shop (40% buyback), Stone (read-only), tower gate (floor select).
- Combat: attack/stand/run + class options (shield wall / sleep spell / treeline shot), trollblood mid-fight, scout scans, monster stats 4F+2/3F/12F+25, XP 12F±25%, gold 8F±50% (halfling/luck tightens spread), fade rule, level-ups w/ full heal.
- Death: daily shardmind death-save at 1 HP, else carried gold gone + armor/shield destroyed + respawn scene.
- Meters: lazy regen from timestamps (45min/⚡, 90min/✦), race cap nudges, energy gates on wilds/warden.
- Presents: ≥20h-away roll with the §7 table, luck/halfling weighting, delivered as pending-event scene.
- Sidekick v1: insight-scaled whispers (sometimes wrong on purpose), scout charges, daily death-save. (Carried-item slot deferred — noted for phase 7 polish.)
- Telemetry: every gold/xp delta appends an `ascent_ledger` row.

## Verified

- 26 unit tests: economy vs design tables, gates, fights, death costs, death-save once/day, interest compounding + single credit, forge/pawn cycle, lazy regen, scene idempotency.
- Browser (real chat): creation → town → gate → floor 1 → wolf → sleep spell (+6 XP correct), energy deduction visible in meters rail.

## Notes

- Floor-10 Gnarl runs a solo-tuned fallback (regular warden stats, half milestone reward) until quorums arrive in phase 5.
- Gate-town healer (2×floor gold) added as designed support; lodge purchase requires carried coin.
