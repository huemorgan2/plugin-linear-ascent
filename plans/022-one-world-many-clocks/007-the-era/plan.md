# Phase 007 — The era: the ending and reincarnation

Goal: the game ends, together, on purpose — and the Tower remembers.

## Tasks

1. The grand siege at 100: declared, not stumbled into — when the
   frontier reaches 100 the game announces the siege window in advance
   (Crier, Stone, letters). Kill requires `R100` strikers inside the
   window per 002's curve. Failure closes the wound, schedules the next
   siege, ticks the pity ramp. v1 ruling: eras cannot end in defeat.
2. Era-end sequence: the fall announced everywhere; the era ledger
   frozen — first clears, top strikers, faction standings, the finisher;
   a closing ceremony scene for every player's next visit.
3. **Stone of Eras** (worldd, permanent, outside reset scope): each era's
   frozen ledger, readable in-game forever.
4. **Reincarnation ledger** (worldd, permanent): one point per player of
   the completed era who reached level 5. Earned tiers: stood on floor
   100 · struck Vharuk in the final siege · the final blow (one per era,
   ever). Glyphs by the name (✦, ✦✦ …) on every social surface.
5. Perks — **prestige buys time, never power**: Relay + Arcanum open from
   day 1, a pre-filled rested pool, echoes from day 1. No stats, no gear,
   nothing that compounds across eras.
6. Reset tooling: wipe `ascent_players` / `ascent_world` / factions /
   letters / bank; the two permanent tables survive; a dry-run mode
   against a scratch DB, rehearsed before the real one. PvP history wipes
   with the era (v1 ruling).
7. New-era boot: frontier 1, warden 1 waiting, the Stone's first line
   names the era number.
8. Vendor sync + worldd deploy; version bump + publish.

## Tests / acceptance

- Reset dry run: permanent tables byte-identical across the wipe; every
  transient table empty; a reincarnated player boots with glyph, perks,
  and a level-1 character.
- Grant rule: level-5 line enforced; tiers awarded from the frozen
  ledger, not live state.
- Ceremony scene renders for a player who was offline during the fall.
