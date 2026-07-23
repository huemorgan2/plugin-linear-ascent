# Game execution — Phase 1: Solo core loop

Parent: [001-buildfirst](../../001-buildfirst/plan.md) phase 1.

## Goal

Floors 1–10 fully playable solo on the local backend: creation, town, combat, meters, death, vault, presents, sidekick v1.

## Deliverables

- **Creation flow** (stage-aware; each step refuses skips with steering hints): race (Human/Elf/Dwarf/Halfling — nudges per story.md) → class (Warrior/Sorcerer/Archer — option-deck classes per ideas.md §2; decision 001-Q1: class at creation, v1 keeps first session simple by defaulting suggestions) → name.
- **Roothollow menus** as scenes: Forge (economy §6 tier catalog), Apothecary & Medlab (§6 items), Lodge (10×level/night), Vault (deposit/withdraw/interest), pawn shop (sell 40%), Stone (read-only stub), tower gate (floor select of unlocked floors).
- **Combat resolver** (economy §2–3): ATK/DEF/HP math, stand/attack/run, class-specific extra options, potion use mid-fight, monster stats 4F+2/3F/12F+25, XP 12F ±25%, gold 8F ±50%, fade rule.
- **Meters**: lazy regen from timestamps (1⚡/45min cap 24+L/10; 1✦/90min cap 10+L/20); costs (wilds 1⚡, warden 3⚡); energy cell 1/day.
- **Death**: carried gold gone, armor+shield destroyed, respawn scene in Roothollow.
- **Vault**: 5%/day compound, accrued on visit; server timestamps.
- **Presents**: ≥20h away roll (economy §7 table), luck charm + halfling modifiers.
- **Content tier 1**: floors 1–10 real YAML (Greenreach biome) — encounter tables, wardens 1–9, Gnarl solo-tuned fallback.
- **Sidekick v1**: whisper advice on options (insight-scaled accuracy), scout (2✦), one death-save/day, carried-item slot.
- **Telemetry**: per-action log rows (XP/gold/energy deltas) for §9 tuning.

## Exit gate (browser)

In the QA Luna chat: create a character, buy gear, fight to floor 2+, die once and respawn, deposit gold and see interest math; unit tests cover combat math vs economy.md sample rows, interest, death, regen; all through real chat turns with tool chips visible.
