# Linear Ascent — World Plan

The whole world, top to bottom, plus the visual design of the text. Story in [story.md](./story.md), numbers in [economy.md](./economy.md).

## 1. Geography

### Roothollow (the base village — everyone's home)

Every player starts, respawns, and banks here. Locations (each is one multiple-choice menu):

Setting is arcanotech ([story.md](./story.md)) — a refugee shantytown built from the wreckage of the realms, plasma forge next to a horse trough.

| Location | What it does |
|---|---|
| **The Forge** (blacksmith) | Buy/upgrade weapons, shields, armor — scrap-steel to plasma-tempered. Named gear per tier. |
| **Apothecary & Medlab** | Medgels, stims, energy cells, luck charms, scout optics. |
| **Lodge** | Sleep safe. Skip it and you can be attacked while offline. Price scales with level. |
| **The Vault** (bank) | Deposit/withdraw, 5%/day interest, survives death. Player-to-player gold grants. |
| **Pawn shop** | Sell loot, trophies, and salvage; occasional rotating rare item to buy. |
| **The Relay** (courier) | Send letters to other players; town notice board. |
| **Guildhall** | Found/join a guild, guild board, commit to group boss attacks. |
| **Stone of the Climb** | Read the world's progress: highest floor, aether-lit carved names, daily happenings feed. |
| **Tower gate** | Enter the Ascent — pick any unlocked floor. |

### The Ascent (100 floors, 10 tiers)

Each floor has the same anatomy, so scenes are learnable and authorable:

1. **Gate town** — small safe zone: healer, floor-local rumors, sometimes a mini-shop.
2. **The wilds** — 2–3 explorable zones (this tier's forest / caves / peaks variant) where the grind happens: random encounters, choices, loot.
3. **Warden's keep** — the floor boss guarding the stair. Milestone floors (every 10th) need a group.

Tiers, biomes, and enemy families:

| Tier | Floors | Biome | Enemies | Milestone Warden (floor) |
|---|---|---|---|---|
| 1 | 1–10 | **Greenreach** — stolen meadows under the tower's floodlights | wolves, boars, goblins with scrap-rifles | Gnarl, the Goblin King (10) |
| 2 | 11–20 | **Ironvale** — dwarven fusion-halls and dead mines | kobolds, orcs in salvaged warframes | Warlord Skarn of the Red Orcs (20) |
| 3 | 21–30 | **The Barrows** — drowned marsh, tombs, rusted exo-rigs | ghouls, wights | The Barrow King (30) |
| 4 | 31–40 | **Webdeep** — lightless caverns and server-deeps | cave spiders, deep trolls | Matriarch Vyx (40) |
| 5 | 41–50 | **The Scorch** — ash desert over reactor slag | salamanders, ogres | Cindermaw the Wyrm (50) |
| 6 | 51–60 | **Frosthold** — glacier fortress, frozen coolant seas | ice trolls, frost giants | Jarl Hrimgar (60) |
| 7 | 61–70 | **Stormreach** — open-sky peaks, wrecked sky-ships | harpies, storm drakes | Zephyra, the Storm Queen (70) |
| 8 | 71–80 | **The Gloom** — shadow forest, dead signals walking | shades, nightmares | The Pale Huntsman (80) |
| 9 | 81–90 | **Hellmarch** — demon outworks, flesh welded to engine | imps, hellknights | Malgrim, Herald of the King (90) |
| 10 | 91–100 | **The Crown** — obsidian citadel and reactor-throne | archdemons, the court | **Vharuk, the Demon King (100)** |

Floor 50 (Cindermaw) is the mid-game spike — the dragon fight from the original vision, canonized.

### Rules of the tower

- A floor is **open to everyone** once its Warden has been killed once (by anyone). Old floors stay open — new players catch up on cleared floors.
- Non-milestone Wardens (floors ending 1–9) are soloable at-level. Milestone Wardens need a committed group (quorum sizes in [economy.md](./economy.md) §5).
- You can grind any open floor, but XP/gold fade if the floor is far below your level (see economy §3) — nudging players up, never forcing.
- Player-built structures (guild watchtowers, traps, shrines) attach to floors and become encounters for others ([ideas.md](./ideas.md) §2).

## 2. Visual design of the world (fonts, background, text)

Nothing fancy. The game is text in a chat — the design job is making that text feel like a place. Complies with `vision/ux_guidelines.md` (eyebrow → headline → support → options; no jargon; calm surfaces).

### Palette (Luna tokens, one game accent)

- **Background:** ink `#0b0e14` (`--bg`), panels `#11151f`, hairline borders `#232a3a`. Flat, dark, no textures — the BBS terminal feel comes free.
- **Narration text:** `#e6e9f2`; secondary/flavor `#8b93a7`.
- **Game accent: amber-gold `#f5a524`** — gold amounts, treasure, loot lines. This is the game's signature color; use it *only* for value.
- HP uses `--ok` green (dropping toward `--red`), energy/mana use `--blue`/`--violet`. Violet stays reserved for Luna UI chrome (buttons, progress), not for narration.
- **Tech signal: cyan-blue `#5eaefc`** for aether/tech elements — scan readouts, shardmind (sidekick) speech, tech item tags. The arcanotech feel comes from the terminal aesthetic itself: the whole UI is diegetically your shardmind's feed, so the monospace text IS the sci-fi layer. No neon glows, no scanline effects — calm surfaces per the guidelines.
- Exactly one gradient allowed: an optional per-tier tint in the floor banner. Everything else flat.

### Type

- **Narration and menus: monospace** — `"IBM Plex Mono", "JetBrains Mono", ui-monospace`. This is the single strongest "BBS door game" signal and keeps stat blocks aligned (`ATK 6 / DEF 7` columns for free).
- **UI chrome (pane headers, buttons): Inter**, per the Luna style guide. Two fonts total, never more.
- Sizes: narration 14–15px; scene eyebrow 11px uppercase letter-spaced; scene headline 18–20px weight 650.

### The scene grammar (every screen, same shape)

```
FLOOR 12 · IRONVALE · THE FLOODED MINE          ← eyebrow: where you are
A dragon blocks the road — ATK 6 / DEF 7        ← headline: the bottom line
Its wings are torn. It is guarding something.   ← one support line, dim
────────────────────────────────────────
 1) Stand your ground
 2) Attack
 3) Run
HP ██████░░ 34/50   ⚡ 12/24   ✦ 6/10   gold 214
```

- **Options are always a numbered list** — multiple choice is the entire interface. 2–5 options, one line each.
- **Status line always last, always same order:** HP, energy, mana, carried gold. Thin bars or block glyphs, no words.
- Dividers are plain rules (`────`), no ASCII art walls. No images in v1; the per-tier banner (name + tint) is the only decoration.
- Numbers the player must compare (enemy ATK/DEF vs. yours) go in the **headline**, not buried in prose.
- Kill news, letters, and Stone of the Climb entries render in the same grammar — eyebrow `DAILY HAPPENINGS`, one line per event.

## 3. Time (world clock)

- One **world day** = one real day, rolls at a fixed UTC hour. Interest pays, lodge protection expires, presents roll, PvP attack allotments reset.
- Energy/mana regenerate continuously (rates in economy §1) — sessions are 10–20 minutes, two or three a day is optimal, per the pacing goal in [vision.md](./vision.md).
