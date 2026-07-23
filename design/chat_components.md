# Linear Ascent — Chat Component Spec

How game messages render inside the Luna chat. Live mockup: [chat_components.html](./chat_components.html). Visual rules inherited from [world.md](../vision/world.md) §2 and `vision/ux_guidelines.md`.

## Principles

1. **One card grammar for every message type:** eyebrow (where/what) → headline (the bottom line, numbers included) → support line → body → options → status rail. A player learns it once.
2. **Cards are enhancement, never a gate.** Options are always numbered; typing "2" in plain chat must always work. Text-only fallback ships first (plan phase 2).
3. **The UI is diegetic** — the whole feed is your shardmind's terminal. Monospace narration IS the sci-fi layer; no glows, no scanlines, calm surfaces.
4. **Single-theme dark by design.** The game commits to the ink terminal; it does not invert in light mode.

## Tokens

Luna base tokens (`--bg #0b0e14`, `--panel #11151f`, `--panel-2 #161b28`, `--line #232a3a`, `--text #e6e9f2`, `--dim #8b93a7`, `--faint #5b6275`, radius 12px) plus game roles:

| Token | Value | Only used for |
|---|---|---|
| gold | `#f5a524` | gold amounts (`◈`), loot, value — nothing else |
| aether | `#5eaefc` | shardmind speech, tech items, ✦ meter |
| violet | `#8b5cf6` | interactive chrome: option keys, chosen state, quorum, player names |
| ok / red | `#3ad29f` / `#f4645f` | HP, gains/losses, death |

Fonts: **one face, one size** — the `ui-monospace` stack at 14px for everything, eyebrows included (ASCII/ANSI discipline). Hierarchy comes from weight, color, and UPPERCASE, never from size. No webfont downloads (CSP + hosted-widget constraints). Numbers use `tabular-nums`.

ANSI grid rules: **no rounded corners anywhere** (`border-radius: 0` on cards, buttons, chips); horizontal padding and gaps in `ch` units so spacing scales with the character cell; state glyphs are characters, not shapes — meters `█░`, quorum `■■□`, option keys `[1]`, attachment marker `▪`, cursor `▌`.

### Motion (typewriter)

- Narration types **letter by letter** (~7ms/char) with a blinking aether-cyan block cursor `▌` that follows the text — the shardmind feed writing itself. Options, status rail, and quorum dots fade in only after the card's text finishes, staggered 90ms.
- Each card animates once, when it scrolls into view; cards play one at a time in feed order.
- `prefers-reduced-motion: reduce` renders everything instantly, no cursor.
- In the real plugin, only the *newest* card types; history renders instantly.

## Components

| Component | Anatomy | Notes |
|---|---|---|
| **Scene card** | eyebrow `FLOOR 12 · IRONVALE · <zone>` → headline with comparable numbers (`ATK 6 / DEF 7` in gold) → 1 support line → optional shardmind whisper → options → status rail | The workhorse; every location and encounter uses it |
| **Option row** | numbered key chip + label + right-aligned hint (`cost`, `class · 2 ✦`) | Button posts the choice; class-specific options get an aether key chip; after a pick, chosen row highlights violet, siblings go 45% opacity and disable |
| **Status rail** | HP / ⚡ / ✦ meters + carried gold, always this order, always last | Meters are ANSI block glyphs — filled `█` in the meter's color, empty `░` in `--line` (10 blocks, rounded ratio); HP blocks turn red below 30%; numeric value always present as text (blocks are `aria-hidden` decoration); rail appears only on cards where the numbers can change |
| **Shardmind whisper** | left aether stripe, `◆` glyph, dim text | The sidekick's advice/scan; visually distinct from narration so its (possibly wrong) advice reads as a voice, not fact |
| **Event card** | scene card + 3px left stripe: gold = loot/present, red = death, aether = letter, violet = boss | Body is a `la-lines` list: one line per fact, deltas right-aligned (`+ ◈ 96` green, `− ◈ 214` red) |
| **Letter card** | eyebrow `THE RELAY`, sender in violet, dashed-border letter body, attachment pill | Attachment pill (purse/item) in gold |
| **Boss commit card** | quorum dots (filled violet = committed) + names + window countdown → commit options | Countdown is server-computed text ("16h left"), never client time |
| **Daily happenings** | eyebrow `DAILY HAPPENINGS · STONE OF THE CLIMB`, headline = the day's bottom line, one line per event | Player names violet; deltas right-aligned; this is the gossip engine — keep it one line per event, no paragraphs |
| **Present card** | gold-striped event card, shardmind flavor line as support | The variable daily gift |

## Renderer contract (plugin side)

- The engine emits a `Scene` object (`eyebrow, headline, support, shard_note?, body_lines[], options[], meters?, event_kind?`); one renderer maps it to a card. No hand-written HTML per encounter — content files never contain markup.
- Options carry stable ids; the card's buttons and the plain-text number both resolve to `ascent_choose(option_id)`.
- All static assets cache-busted with `?v=<manifest.version>`.
- Accessibility: buttons are real `<button>`s, focus-visible outlines, meter values always present as text (bars are decoration).
