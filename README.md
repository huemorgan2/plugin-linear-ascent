# plugin-linear-ascent

Linear Ascent — a LORD-style multiplayer text RPG for [Luna](https://luna.com.ai). Players in the frontier village of Roothollow climb a 100-floor arcanotech tower: daily energy pacing, bank interest, offline PvP, letters and grants between players, milestone Wardens fought by guild quorum, and the Luna agent embedded in the fiction as the player's shardmind sidekick. Arrival moments render full-width 1-bit dithered scene banners.

Part of the [luna-linear-ascent](https://github.com/huemorgan2/luna-linear-ascent) project, which also holds `worldd` — the shared-world Render service this plugin talks to from phase 3 on.

## Layout

| Path | What |
|---|---|
| `vision/` | game design: vision, story bible, world, 100-floor economy, ideas |
| `design/` | chat card components (`chat_components.html` mockup) + 1-bit banner styleguide (`pixel_art.md`) |
| `plans/001-buildfirst/` | phased build order (0 scaffold → 7 release) |
| `plans/002-full-game/` | how the whole game gets produced: engine, 100 floors of content, art set, service integration |
| `content/art/banners/` | generated 320×112 white-ink 1-bit banners (`raw/` model originals are untracked) |
| `tools/` | `generate_banners.py` (Gemini → Bayer 1-bit pipeline), `banners.py` (procedural fallback) |

Plugin code lands per plan 001 phase 0 (`plugin_linear_ascent/`, tool surface `ascent_*`).

## Regenerating banners

```
LUNA_GEMINI_API_KEY=... python tools/generate_banners.py [slug ...]
```

Requires PIL + httpx and a sibling checkout of `plugin-image-gen` (provider client). See `design/pixel_art.md`.

## License

MIT — see [LICENSE](LICENSE).
