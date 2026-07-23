# Game execution — Phase 2: Chat UI components

Parent: [001-buildfirst](../../001-buildfirst/plan.md) phase 2 · design: [chat_components.md](../../../design/chat_components.md), [pixel_art.md](../../../design/pixel_art.md).

## Goal

The game renders as the designed ANSI cards in chat, not raw text — banners included; text-only fallback always works.

## Deliverables

- `render.py` — one `Scene → embed_iframe HTML` function implementing the card grammar: banner (when `banner` slug set) → eyebrow → headline → support → shardmind whisper → body lines → numbered options → status rail.
  - Tokens per chat_components.md (ink `#0b0e14`, panel, gold `#f5a524`, aether `#5eaefc`, violet, ok/red), monospace 14px single size, no rounded corners, `ch` spacing, meters `█░`, keys `[n]`.
  - Tool results returned as **JSON string** with `embed_iframe` (host contract), plus a plain-text transcription in the payload so the model can narrate and plain "2" always works.
  - Banners: white-ink PNGs from `content/art/banners/` inlined as data URLs (sandboxed iframe; `loading="eager"`), tinted per role via CSS filter or pre-tinted, `image-rendering: pixelated`, cache concerns moot with data URLs.
  - Event cards with left stripe: gold loot/present, red death, aether letter, violet boss.
- Options clickable AND numbered: buttons post the choice (sandboxed iframe cannot call the API — v1: buttons render but the payload instructs "reply 2"; typing the number is the actuation path; clickable actuation deferred until a safe postMessage path exists).
- Constraints honored: no pip deps for UI, no webfonts, static text-only fallback verified.

## Exit gate (browser)

Every card type renders correctly in the QA Luna chat (scene, combat, loot, death, present, vault); screenshots read cleanly; typing "2" in plain chat picks option 2; reduced-motion/text fallback verified by reading the payload text.
