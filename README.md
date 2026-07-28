# plugin-linear-ascent

Linear Ascent — a LORD-style multiplayer text RPG for [Luna](https://luna.com.ai). Players in the frontier village of Roothollow climb a 100-floor arcanotech tower: daily energy pacing, bank interest, offline PvP, letters and grants between players, milestone Wardens fought by guild quorum, and the Luna agent embedded in the fiction as the player's shardmind sidekick. Arrival moments render full-width 1-bit dithered scene banners; first clears and floor-1–3 kills play short dithered movies cut to the killing blow's damage type.

Combat speaks a counter language (017): three classes — human warrior, elf archer, dwarf sorcerer — each deal one damage type into monsters traited with armor, spellguard, wings, speed, and bulwark bulk; every floor 11–100 carries a deliberate trait spread, an enemy dossier [i] card explains every modifier on screen, and the economy hangs durability repair, a death you can insure against, and a relic catalog (one dramatic effect + one hard limitation each) off the same daily income — gated in tests so the whole stack never eats more than 40% of a hunting day.

Part of the [luna-linear-ascent](https://github.com/huemorgan2/luna-linear-ascent) project, which also holds `worldd` — the shared-world Render service this plugin talks to from phase 3 on.

## Layout

| Path | What |
|---|---|
| `vision/` | game design: vision, story bible, world, 100-floor economy, ideas |
| `design/` | chat card components (`chat_components.html` mockup) + 1-bit banner styleguide (`pixel_art.md`) |
| `plans/001-buildfirst/` | phased build order (0 scaffold → 7 release) |
| `plans/002-full-game/` | how the whole game gets produced: engine, 100 floors of content, art set, service integration |
| `content/art/banners/` | generated 320×112 white-ink 1-bit banners (`raw/` model originals are untracked) |
| `plugin_linear_ascent/content/floors/` | 100 floor YAMLs — encounters, traits, lore, wardens |
| `plugin_linear_ascent/content/art/events/` | shipped 1-bit event movies (intro, first clears, typed kill endings) |
| `tools/` | `generate_banners.py` (Gemini → Bayer 1-bit), `generate_event_gifs.py` (Veo → 1-bit movie pipeline), `banners.py` (procedural fallback) |

Plugin code lands per plan 001 phase 0 (`plugin_linear_ascent/`, tool surface `ascent_*`).

## Regenerating banners

```
LUNA_GEMINI_API_KEY=... python tools/generate_banners.py [slug ...]
```

Requires PIL + httpx and a sibling checkout of `plugin-image-gen` (provider client). See `design/pixel_art.md`.

## License

MIT — see [LICENSE](LICENSE).
