# Linear Ascent — 1-bit Scene Banner Styleguide

Full-width dithered 1-bit illustrations at the top of arrival cards — classic Macintosh / Playdate / 1-bit-Akira aesthetic, NOT sprites. Companion to [chat_components.md](./chat_components.md); live examples in section 9 of [chat_components.html](./chat_components.html).

## 1. The style (rules every banner follows)

- **True 1-bit:** exactly two states per pixel — ink or nothing. All midtones via ordered (Bayer) dithering. No grayscale, no anti-aliasing, no outlines in a second color.
- **The ink color is the card's role color** (same discipline as the text): locations/zones → `--dim`, boss arrivals → `--violet`, death → `--red`, present → `--gold`, shardmind/tech scenes → `--aether`. Assets ship as white-ink PNGs on transparency; the renderer tints. Background is transparent — the card panel shows through, so banners sit in the terminal, not on a pasted rectangle.
- **Format:** banner spans the full card width, edge to edge (full bleed above the eyebrow), height ≈ half the card. Native 320×112 px (20:7), upscaled ~2× with `image-rendering: pixelated` — chunky pixels are the point.
- **Designed gradients:** every banner carries at least one large dither-gradient — a sky fading from dense ink to nothing, a radial glow ramp around a light source, a light pool on the ground. Gradients are what keep 1-bit alive; flat silhouette-on-black is the failure mode.
- **Composition:** wide shot, low horizon, one dominant subject; dense dithered texture in the ground/sky like the 1-bit Akira poster; light from top-left; one arcanotech tell per scene (antenna, floodlight, cable, plasma arc). No text inside the image.
- **Files:** `content/art/banners/<slug>_320x112.png`, cache-busted `?v=<manifest.version>`.

## 2. Production pipeline

1. **Generate** with [tools/generate_banners.py](../tools/generate_banners.py) (Gemini `gemini-3-pro-image` via plugin-image-gen's provider client, `LUNA_GEMINI_API_KEY`): shared style preamble demands strict two-color output with big designed gradients, aspect 21:9; per-slug scene prompts live in the script's `SCENES` table. `python tools/generate_banners.py [slug ...]` regenerates any subset.
2. **Post-process** (same script): center-crop to 20:7 → downscale to 320×112 → autocontrast (keeps gradient ramps wide) → Bayer 8×8 ordered dither → white ink on alpha. The model can return anything; the grid and the 1-bit discipline are enforced here. Raw model outputs kept in `content/art/banners/raw/` for regeneration reference, tinted 2× previews in `preview/`.
3. **Fallback/blocking:** [tools/banners.py](../tools/banners.py) renders procedural placeholder banners (shape painting → Bayer 8×8 dither, 160×56) so layout work never waits on art or an API key.

## 3. Where banners appear (and where they don't)

| Card type | Banner? |
|---|---|
| Village arrival, entering a building (Forge, Vault, Lodge, Medlab, Relay, Guildhall) | **yes** |
| Zone entry (each tier biome), gate town, Warden's keep approach | **yes** |
| Milestone boss arrival (violet) | **yes** |
| Death card (red), present on return (gold) | **yes** |
| Combat rounds, loot lists, letters, grants, daily happenings, status rail, shop rows | **no** — pure text |

Rule of thumb: a banner marks **arriving somewhere or a moment that stops the game** (death, the day's present). Repeating events never get one — images stay a reward, not wallpaper.

## 4. Starter set (build these first, iterate)

| Banner | Used | Scene |
|---|---|---|
| `roothollow` | entering the village | shack rooflines at night, tower leg cutting the starry sky diagonally, moon, antenna, dirt path in |
| `forge` | entering The Forge | anvil silhouetted against the plasma arc glow, hanging chains, tool wall |
| `vault` | entering The Vault | wheel-lock door in a heavy stone face, keypad glow, coin scatter on the counter |
| `lodge` | lodge / sleep confirm | longhouse at night, one lit window, smoke, palisade line |
| `medlab` | entering Apothecary & Medlab | shelves of flasks, IV stand, cross sign, dithered lamplight pool |
| `relay` | entering The Relay | lattice mast against clouds, dish pair, letters pigeonholed below |
| `guildhall` | entering the Guildhall | banners from crossbeams over a round table, hearth glow |
| `stone` | Stone of the Climb | monolith with glowing name-lines, small crowd of silhouettes |
| `gate` | tower gate / floor select | massive doorframe, lift cage, chain and cable running out of frame |
| `greenreach` | tier-1 zone entry | rolling meadow, dead tree, floodlight tower with beam, wolf on the crest |
| `gnarl` (violet) | floor 10 boss arrival | throne of rifle crates, fat crowned silhouette, goblin banners |
| `death` (red) | death card | cracked skull in an ash field, broken shard floating above, faint rays |
| `present` (gold) | return present | strapped crate on the doorstep at dawn, cable bow, long shadows |

Per remaining tier (with content authoring, ~phase 6): 1 zone banner + 1 milestone-boss banner ≈ 18 more.

## 5. Open

- Small inline icons (16px, for shop rows / loot lines) are a separate, later decision — the banner set comes first.
