# Phase 2 — execution summary

Status: **complete** (specimen-verified at width + live iframe confirmed in chat).

## Built

- `render.py`: single `Scene → embed_iframe HTML` renderer implementing the card grammar — banner → eyebrow → headline → support → shard whisper (aether stripe) → body → numbered options (gold keys, aether for class/shard options) → status rail (HP bar `█░`, ⚡ ✦ ◈).
- Tokens per chat_components.md: ink `#0b0e14`, panel `#11151f`, dim/text/gold/aether/violet/red, monospace 14px single-size, no webfonts, no rounded corners in the card.
- Banners: white-ink 1-bit PNGs copied into the package (`content/art/banners/`, 17 files, 80 KB total), inlined as data URLs, tinted per role via CSS mask (dim default, red death, gold present, violet Gnarl), `image-rendering: pixelated`.
- Event stripes: gold loot/present, red death, aether letter, violet boss.
- Tool payloads now return `embed_iframe` + `scene_text` + instructions telling the agent NOT to repeat the card and to add one shardmind line. Plain-text fallback (`Scene.to_text`) always present.
- Option actuation: typing a number (or words the agent maps) — buttons deferred as planned (sandboxed iframe has no API path).

## Verified

- 4 renderer tests (escaping incl. script-injection body lines, banner presence for all referenced slugs, stripes, meters rail).
- Specimen sheet of 8 card types reviewed in a real browser at full width: creation/town/forge/vault/floor-arrival/combat/loot/death — all legible, banner art reads, colors correct.
- Live chat: tool result rendered as sandboxed iframe in the QA Luna.
- Fixed along the way: specimen page charset (mojibake was specimen-only; chat page is UTF-8).

## Screenshots

Cursor screenshots: `ascent-specimens-1.png`, `ascent-specimens-combat.png`, `ascent-specimens-death.png` (also visible in the dojo run to come).
