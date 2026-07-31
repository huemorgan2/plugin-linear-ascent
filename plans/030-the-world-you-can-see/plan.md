# 030 — The world you can see

One theme: **the game plays well and shows almost nothing.** The shardmind is a
text block with a diamond character. The forge is a strip of art the height of
two lines. The player — the one thing you own — has no face, no body, no armour
you can look at. Attack and defense are numerals in a fold. The vault answers
"where is my money" with a comma-formatted string. The news is a wall of near
duplicate warden lines. The floors you choose between are rows of words. Nobody
in Roothollow talks to you, and a new floor opens with a paragraph instead of a
scene.

This plan makes every one of those a picture, without breaking the three
standing laws: 1-bit ink, numberless content, version-skewed wire.

**Scope rule for everything below (the level-10 rule):** *code* ships for the
whole game — a renderer, a Scene field, a pip row works on floor 97 the same as
floor 3. *Content and tuning* ship for floors/levels **1–10 only**: per-floor
art beyond the systems' fallbacks, per-floor NPCs, per-floor movies, and any
sim-based tuning tests stop at 10. The rest of the tower gets fast closed-form
checks only. This is deliberate, to save time — floors 11–100 inherit the code
and the fallbacks, and get their content in a later pass.

> plan 029 does not exist and never will: `tests/test_029_*.py` was already
> claimed by shipped work, and a plan whose tests carry another plan's number is
> a trap. This plan is 030; its tests are `test_030_*`.

---

## The ask (2026-07-31, condensed from the complaint)

- a small image of the shard helper on the left where it writes
- an image for **every** place you visit, forge included, and larger — 320×200
- a full-body player profile image, 100×200, bottom of the card left of the
  pack; the portrait suits up as the armour improves — near-rags at first
- to its right, top: HP / XP / energy; below: **Defense and Attack as rows of
  ten 16×16 icons** (armour / sword), outline → half (vertical) → full, one half
  per 3 points
- coin and XP text painted the same colour as their icons; **the win-card coin
  icon is the coin icon, everywhere**
- the vault shows the money: a 320×50 strongbox-interior strip, large monospace
  `DEPOSITED: 40 ⟨coin⟩` centered on black
- town news in a 1-bit paper box, 320×150, an X that closes it for the day, no
  item over 100px
- condense the warden feed — `75% → 50% → 25% → killed` is one story, not four
  lines
- energy cost in energy-blue on the hunt selection; in general **everything in
  its own colour, everywhere** — gold in gold, and so on
- the floor list shows each floor's fields and its warden as pictures, rows ~3×
  taller
- NPCs: a lodge keeper who tells how climbers make money here; one lore
  character per floor's fields who talks monsters and warden
- every monster wears its ATK / DEF / HP on top of its art, top-right, player
  pip-style, black chips behind; its `[i]` gains a one-line story plus bulleted
  coin and XP drop ranges
- a once-per-floor entry movie: the animals, the floor's story, its warden — or
  the warden's demise and who felled it, if it already fell
- all new icons 16×16 (or displayed 32×32) per the 018 convention; tuning tests
  to level 10 only, quick tests for the rest

## The audit (read first, believe it)

Ranked worst-first, with the code that proves it.

1. **The player has no body.** There is no portrait anywhere — the pack strip
   (`render.py::_inventory_html` :548) and the meters rail (`_meters_html`
   :380) are the whole bottom of the card. Ten armour tiers exist with names
   and prices (`economy._FORGE_ROWS` :932-964, Padded Jerkin → Aegis of the
   Vale) and none of them has ever been *seen*.
2. **ATK/DEF are invisible.** `state.atk` :330 / `state.dfs` :334 are computed
   every scene and surface only in `sheet.py` text and the fight opener
   (`combat.py::fight_scene` :432-436).
3. **The coin exists in exactly one place.** `_TALLY_MARK` (`render.py:254`)
   ties the 16×16 `coin`/`aether` masks to the win-card haul and nothing else;
   everywhere else gold is the `◈` character (`_meters_html` :405-409,
   `core.py:1699`, pane literals). `MUST_BE_DONE_LATER.md` §7 already names
   this debt.
4. **Interiors are half-size.** All room banners are 320×112
   (`content/art/banners/`), shown full-bleed but shallow; 320×200 exists in
   the pipeline (milestone bosses, the title, all intro-movie GIFs) and rooms
   don't use it.
5. **The news repeats itself.** worldd inserts one line per warden wound
   threshold (`W/app/social.py:820-831`) and one on the fall (:1133-1137);
   `inject_world` selects the last 5 raw (:88-90) and the town square prints
   them verbatim (`core.py:729-733`). A busy warden day is four lines about one
   warden.
6. **The floor list is words.** `_gate_scene` (`core.py:1994-2030`) emits one
   thin text row per floor while every floor already owns a zone banner
   (`floor_NNN.yaml: banner`) and warden art (`creatures/warden_NNN…png`).
7. **The shardmind is a `◆`.** `render.py:945-948` + CSS :1157 — a text glyph,
   no image, and no `shard` key exists in `icons.py`.
8. **Nobody talks.** Zero NPC/dialogue code. The lodge keeper, vault clerk and
   registrar exist only as narration inside scene prose (`core.py:1602`,
   :1714, :644).
9. **A floor opens with a paragraph.** `_gate_pick` :2033-2070 prints arrival
   prose. The once-only movie machinery from 016 (`_INTRO_MOVIE` :552-608,
   split intro/loop GIFs, `_fx_split` `render.py:166-180`) has never been
   reused.
10. **Tuning tests spend time above the line players are at.**
    `test_017_bestiary.py` sims floors 11–100 × 40 seeds every run; the slow
    suites don't distinguish the tuned band (1–10, per 025) from the untuned
    tower.

## The laws

1. **The level-10 rule.** Code everywhere, content and tuning to 10. Any
   per-floor asset or test loop must read its ceiling from one constant:
   `economy.TUNED_FLOOR_CAP = 10`.
2. **One coin.** The 16×16 `coin` mask is the *only* coin the game draws; the
   16×16 `aether` shard is the only XP mark; `◈`/`✦` survive only in
   `to_text()` (the wire/agent fallback is text and stays text).
3. **A number wears its colour.** Gold = `GOLD`, XP = `VIOLET_SOFT`, energy =
   `AETHER`, HP = `OK`/`RED` — in hints, body lines, meters, dossiers, news.
   Blue stays the notification ink for counts/notices only (027 law); energy
   amounts are the one legitimate second use of `AETHER`, always with the bolt
   glyph so the two readings can't collide.
4. **Every icon is a 16×16 grid in `icons.py`** (018 laws apply), displayed at
   16 or 32 px. Every scene image is Bayer-dithered white ink at a declared
   size. New sizes introduced by this plan and frozen here: **320×200**
   (rooms, movies), **320×150** (the paper), **320×50** (the vault strip),
   **100×200** (the portrait). Nothing else.
5. **The wire law holds.** Every new Scene field is top-level, guarded with
   `getattr(scene, x, None)` in the renderer, ignored by old clients, and
   mirrored into `to_text()` when it carries a number the player needs.
6. **Content stays numberless.** NPC speech and movie text live in YAML under
   the existing lint (`schema._FORBIDDEN_NUMERIC_KEYS`, `PROSE_CAP`); every
   number they *seem* to say (warden strength, drop ranges) is injected at
   scene-build time from `economy.py`.

---

## Phase 1 — One coin, one colour

**What's wrong.** Audit #3 and the colour scatter: gold is `◈` text except on
the win card; XP is the word `XP`; the hunt row's `1 ⚡` hint renders in
`FAINT` like every hint (`core.py:2084`, `.opt .hint` `render.py:1193`).

**What ships.**

1. `icons.icon_data_url` keeps its signature; `render._eglyph` grows siblings:
   `_coin(n)` and `_xp(n)` — amount + 16×16 mask + colour, one helper each, so
   every call site paints the pair identically (icon and numeral share one
   `<span>` colour).
2. A render-side pass `_paint_amounts(html)` applied to option hints and body
   lines: `◈ 1,234` → coin mask + `1,234` in `GOLD`; `⚡` amounts → bolt +
   `AETHER`; `n XP` / `✦` → aether mask + `VIOLET_SOFT`; `+n HP` stays `OK`.
   It runs *after* the existing `+`/`−` gain-loss tint so a green line keeps a
   gold-coloured amount inside it.
3. Call-site sweep, plugin and pane: meters rail gold (`render.py:405-409`),
   vault lines (`core.py:1699` et al.), forge/shop prices, pawn, lodge prices,
   grants, pane literals (`pane.py:355-356, 662, 701`). The win card is the
   reference, not the exception — closes `MUST_BE_DONE_LATER.md` §7.
4. `to_text()` untouched: it keeps `◈`/`⚡`/`XP` characters. Law 2.

## Phase 2 — The player you can see

**What's wrong.** Audit #1 and #2.

**What ships.**

1. **Portraits, 100×200, armour-keyed.** Six full-body 1-bit portraits keyed
   by the equipped armour's forge tier: `portrait_rags` (no/starter armour —
   near-bare, patched cloth), `portrait_leather` (tiers 1–2),
   `portrait_chain` (3–4), `portrait_scale` (5–6), `portrait_plate` (7–8),
   `portrait_aegis` (9–10). Resolver `render._portrait_slug(p_gear)` maps via
   `economy.forge_tier`; unknown/absent → rags. Files
   `content/art/portraits/portrait_*_100x200.png`, generated through the
   existing `tools/generate_banners.py` pipeline with a `size=(100,200)`
   entry set. One silhouette, six wardrobes — the *suit-up* is the reward for
   the buy ladder.
2. **The profile block.** A new bottom-of-card `.profile` grid, sitting
   directly left of the pack strip: portrait (100px column, masked, tinted
   `TEXT`) on the left; right column top-to-bottom: the meters rail content
   (HP, XP, energy, gold, LV — `_meters_html` moves inside), then the two pip
   rows. The old free-standing rail row is retired in the same commit — the
   numbers live in one place.
3. **Pip rows: Defense and Attack.** Ten 16×16 icons each (`armor` grid for
   defense, `weapon` grid for attack). `icons.icon_data_url(key, mode)` gains
   `mode ∈ full | half | outline`, all derived from the same grid — no new
   grids for states: `outline` = rim ink only (any ink pixel touching a hole
   or the edge), `half` = left 8 columns full ink + right 8 columns rim only
   (the vertical half-fill), `full` = the `_painted` art as today. **3 points
   = one half**: `halves = clamp(round(stat / 3), 0, 20)`; icons fill left to
   right; past 60 the row is all-full and the numeral says the rest. The
   numeral always rides at the row's end (`ATK 37` / `DEF 12`) — text parity
   and the >60 case in one stroke. Defense pips tint `AETHER`-adjacent steel
   (`DIM`), attack pips `ORANGE`; empty outlines `FAINT`.
4. **Wire:** the profile needs nothing new — gear, level and stats already
   ride the player snapshot the plugin holds. Scene gains nothing; this is
   pure renderer. Pane and legacy card both get it (shared fragment).

## Phase 3 — Every room is a picture (and the shard has a face)

**What's wrong.** Audit #4 and #7.

**What ships.**

1. **320×200 interiors.** Regenerate every *visited space* at 320×200 through
   `tools/generate_banners.py`: `forge, lodge, vault, medlab, relay,
   guildhall, stone, gate, arcanum, roothollow` + the ten zone banners'
   gate-town variants for floors 1–10 (level-10 rule: floors 11–100 keep
   their 320×112 zone art via fallback). `_banner_data_url` (`render.py:99`)
   already searches sizes in order — put `320x200` first for the `banners/`
   tree; rooms that only have 320×112 fall through unchanged. The lru_cache
   restart note applies (new art = new process).
2. **The shard avatar.** New 16×16 grid `shard` in `icons._GRIDS` — a cut
   crystal, rim-lit per 018 law. The `.shard` block (`render.py:945-948`)
   replaces the `◆` character with the mask at **32×32**, tinted `AETHER`,
   top-aligned left of the text — the small image "where it writes."
   `to_text()` keeps `◆`. The `◆` stays in chip/inline contexts elsewhere.
3. **The floor list shows its floors.** `_gate_scene` rows become tall tiles
   (~3× today's row: the 32px-icon row precedent scaled up): left, the
   floor's **fields** (zone banner, thumbnail ~96×60 via the same mask
   technique as `.gpic`); beside it, the **warden** (`warden_NNN` creature
   art, or milestone-boss 320×200 art on 10/20/…); then the label, the
   `🔒 level n` or gate-town hint (now colour-painted per Phase 1). Resolved
   render-side by option id `floor_{n}` through `content.get_floor` — the
   tips.py precedent: zero wire change, old clients render the plain row.

## Phase 4 — The vault shows the money

**What's wrong.** Audit: `_vault_scene`'s first body line *is* the balance
(`core.py:1699`) — a string among strings.

**What ships.**

1. One new asset: `banners/vault_interior_320x50.png` — the inside of the
   strongbox, coin-heaped, 1-bit, generated at `size=(320,50)`.
2. A new render slot `Scene.strip: {art, text} | None` (top-level, wire-law
   guarded): a full-width band — the art as a dim mask over `INK` black, and
   centered over it, large monospace (`18px`, `tabular-nums`):
   `DEPOSITED: 1,240 ⟨coin⟩` — amount and coin mask in `GOLD` per Phase 1.
   `to_text()` writes `DEPOSITED: ◈ 1,240`.
3. `_vault_scene` emits it; the carried/interest lines stay as body lines
   below. The strip renders in any room that sets it — one slot, not a vault
   special.

## Phase 5 — The Morning Crier is a paper

**What's wrong.** Audit #5. Also `_maybe_news` (`core.py:277-289`) makes the
news a whole interstitial scene; the square then repeats the same 5 raw lines.

**What ships.**

1. **Condense at the source.** In `W/app/social.py::inject_world`, the
   happenings/gossip selection dedupes per `(kind='war'|'boss', floor)`:
   if a `boss` (fell) line exists for a floor in the window, every `war`
   threshold line for that floor is dropped; otherwise only the *lowest*
   threshold line survives. One warden, one line, always the latest chapter.
   The `floor` column from `005_news.sql` makes this a filter, not a parse.
2. **The paper.** New asset `banners/paper_320x150.png` — a 1-bit broadsheet
   texture (torn edge, fold shadow, dithered grain). New render slot
   `Scene.paper: {headline, items[], closable} | None` (top-level, guarded):
   a 320×150-proportioned box, paper art as the *background* mask in `DIM`
   over `PANEL`, items typeset on top in `INK`-on-paper inverse, an `✕`
   button top-right. Each item is clamped to two lines (`PROSE`-capped at
   selection, ~100px including leading is two lines at 14px/1.6 in the
   320-wide frame — enforce by truncation with `…`, never overflow).
3. **X closes it for the day.** The `✕` posts option id `news_close`;
   `core.py` stamps `p["news_day"] = today` — the exact guard `_maybe_news`
   already keys on, so closed stays closed until dawn. The interstitial
   `_news_scene` reduces to setting the `paper` slot on the town scene; the
   raw `· line` dump at `core.py:729-733` is deleted.
4. `to_text()` prints `THE MORNING CRIER` + the item lines — the agent reads
   the same paper.

## Phase 6 — People to talk to

**What's wrong.** Audit #8.

**What ships.**

1. **The lodge keeper.** New option `talk` in `_lodge_scene` → a dialogue
   scene in the keeper's voice: how climbers make money under this roof —
   the night shift ladder (`economy.NIGHT_SHIFTS`), rest-for-aether, the
   vault's 5% and stubs, pawning spoils. Numbers injected from `economy.py`
   at build time (law 6); the prose is a rotation of 3–4 tellings so the
   second visit isn't a replay. Scene uses the lodge 320×200 art,
   `shard_note` stays out of it — this is the keeper's room.
2. **A voice in every fields, floors 1–10.** Each `floor_00N.yaml` (N ≤ 10)
   gains an `npc:` block — `{name, role, greet, lore, warn}` — numberless,
   linted by the schema (new keys added to the allowed set, prose caps
   apply). A new option `talk` at the gate town (`_gate_town_options`) →
   the character speaks: who they are, what hunts here (their `lore` +
   the encounter names from the same YAML), and the warden — strength said
   in *derived* numbers (`economy.warden_stats(floor)` ATK/DEF/HP injected
   into the line) — warning you off or thanking you, keyed to whether the
   world warden on that floor stands or fell (`p["_world"]["warden"]`).
   Floors 11–100: no `npc:` block → no `talk` row. Code is floor-agnostic
   (law 1).
3. No dialogue *system* — these are ordinary Scenes built the way every room
   already is. First-visit emphasis (the keeper introduces themself once)
   rides `p["flags"]["met_keeper"]` / `["met_npc_{floor}"]`, the existing
   idiom (`dur_taught_*` precedent, `core.py:1256`).

## Phase 7 — The monster wears its numbers

**What's wrong.** The fight headline *says* `ATK 12 / DEF 6` (`fight_scene`)
but the art is clean and the numbers are prose; drop ranges appear nowhere.

**What ships.**

1. **The stat plate.** `_enemy_head_html` (`render.py:463`) moves onto the
   art: absolutely positioned **top-right over `.banner`**, stacked chips,
   each on a solid `INK` black plate (the black-background rule — ink art
   under white pips needs the plate to read): ATK as sword pips, DEF as
   armour pips — the *same* `icon_data_url(key, mode)` pips as the player's,
   at 16px, same 3-points-a-half scale, capped 10 icons with the numeral
   beside — and HP as the existing block-bar meter, `OK`→`RED`. Player pips
   and monster pips are one visual language; you read a matchup at a glance.
2. **The dossier learns the story and the odds.** `combat._enemy_payload`
   (:285-305) gains `story` (the YAML `lore` line, already carried, now
   always shown first in the `[i]`) and `drops`: coin and XP ranges computed
   from the same math `_victory` rolls — `gold_per_kill(floor) ±50%` and
   `xp_per_kill(floor) ±25%`, times `kill_reward_mult(specimen, traits)` —
   rendered as two bullets:
   `· coins ⟨coin⟩ 10–12` · `· XP ⟨aether⟩ 3–4`, painted per Phase 1.
   Additive keys on the `enemy` dict — old renderers ignore them (wire law).
   `to_text()` gains the two ranges on the fight card.

## Phase 8 — The floor movie

**What's wrong.** Audit #9.

**What ships.**

1. **The machinery (all floors).** `_floor_movie(p, n)` — a 2–3 beat
   scripted sequence on the 016 pattern (`fx` + headline + body + `Next`),
   driven by `p["flags"][f"floor_seen_{n}"]`; `_gate_pick` routes through it
   exactly once per floor per character, then lands on the arrival scene.
   No skip, like the intro. Beat script per floor:
   - **Beat 1 — the fields:** the floor's world loop GIF; text from the
     YAML `arrival`/`npc.lore` register — the animals, the place.
   - **Beat 2 — the warden:** if the world warden stands: the warden GIF +
     its strength (derived, `warden_stats`); **if it fell:** the same art
     under the shared `warden_fall` demise GIF treatment, and the text
     names the killers — worldd's `_world_warden` payload gains
     `fallen_by` (the names `_warden_fall` already formats into the stone
     line at :1133) so the movie states *who*, not just *that*.
2. **The assets (floors 1–10, law 1).** Per floor: `floorN_world` loop GIF
   and `floorN_warden` loop GIF, both **320×200**, via
   `tools/generate_event_gifs.py` (Veo → Bayer → white ink, `size:(320,200)`
   entries, split intro/loop where motion warrants it). Plus **one** shared
   `warden_fall_320x200.gif` demise loop — the fallen variant is one asset +
   per-floor text, not ten more GIFs. Floors 11–100: the movie machinery
   falls back to the floor's still banner as the beat art — the code path
   is identical, only the motion is missing until a later art pass.
3. Movie beats are ordinary Scenes — `to_text()` carries the story, the
   agent narrates it in chat as ever.

## Phase 9 — Tests go quick

**What's wrong.** Audit #10 — and the ask is explicit: tune to 10, quick
checks for the whole game, save the time.

**What ships.**

1. `economy.TUNED_FLOOR_CAP = 10`, and the slow sim suites read it:
   `test_017_bestiary.py` `FLOORS = range(11, 101)` → gated behind
   `ASCENT_FULL_SIMS=1` (env), default run covers nothing above the cap;
   `test_022_002_retune.py` warden sims likewise sim floors ≤ 10 by default,
   full tower only under the flag. `test_017_damage_types.py` already stops
   at 10 — untouched.
2. The whole-tower *fast* gates stay on every run, because they're
   arithmetic, not sims: `test_smoothness.py` (1–100 no-cliffs),
   `test_008_pace.py` (monotonic HP), `test_021_floor_is_not_level.py`,
   `test_024_first_gate.py` closed-form pools, `test_011_art.py` coverage.
   Quick tests for the whole game — literally.
3. CI/dev default becomes minutes, not the sim wall; the flag run is the
   pre-ship ritual, not the inner loop.

---

## The asset ledger

Every new visual, its size, and its maker. All 1-bit white ink, Bayer where
toned. (16×16 icons: hand grids in `icons.py`, zero build step.)

| Asset | Size | Count | Tool |
|---|---|---|---|
| `shard` icon grid | 16×16 | 1 | `icons.py` |
| pip modes `outline/half` | derived | 0 files | `icons.py` code |
| player portraits `portrait_*` | 100×200 | 6 | `tools/generate_banners.py` |
| room banners (interiors + floors 1–10 gate towns) | 320×200 | ~20 | `tools/generate_banners.py` |
| `vault_interior` | 320×50 | 1 | `tools/generate_banners.py` |
| `paper` | 320×150 | 1 | `tools/generate_banners.py` |
| floor movies world+warden, floors 1–10 | 320×200 GIF | 20 | `tools/generate_event_gifs.py` |
| `warden_fall` shared demise | 320×200 GIF | 1 | `tools/generate_event_gifs.py` |

The no-emoji gate (`tests/test_no_emoji.py`) and the `set(row) <= {'#','.'}`
grid audit apply to all of it.

## Decisions taken (change here, not in code)

- **Pip scale:** 3 stat points = one half-icon; 10 icons; >60 = full row +
  numeral. The numeral always prints — the pips are the *feel*, the numeral
  is the fact.
- **Portrait buckets:** six, by armour forge tier (0 / 1–2 / 3–4 / 5–6 / 7–8 /
  9–10). Race/class variants rejected for now — 6 assets, not 72.
- **Warden demise art is shared** (one GIF) — per-floor demise is text.
- **News condensing lives in worldd's selection**, not in the renderer —
  single writer, single condenser; the plugin never parses news strings.
- **029 is skipped** in the plans sequence, permanently.

## What was rejected first

- Runtime image composition (PIL in the plugin) for portraits-with-gear-
  overlays — breaks the no-PIL-at-runtime architecture for marginal gain over
  six baked portraits.
- Three hand-drawn state grids per pip icon — `mode` derivation from the one
  grid keeps 018's audit and halves the drawing.
- A generic dialogue engine for NPCs — two `talk` options and YAML prose do
  the job; a system without a second customer is scaffolding.
- Per-floor demise GIFs ×10 — cost without story gain.
- Condensing news in the renderer by regex — parsing prose is how bugs are
  born; worldd owns the rows and the `floor` column.

## Tests

`tests/test_030_the_world_you_can_see.py`:

- `_paint_amounts` colours `◈`/`⚡`/`XP` amounts and leaves `to_text()`
  untouched; the win card and the vault draw the *same* coin mask URL
- `icon_data_url(key, "outline"|"half"|"full")` returns three distinct URLs
  from one grid; outline is a strict subset of full; half's right columns
  equal outline's
- pip math: 0 def → 10 outlines; 3 → one half; 6 → one full; 61 → ten fulls +
  numeral; player and enemy use the same function
- `_portrait_slug`: starter armour → rags; each forge tier lands its bucket;
  missing art falls back silently (no broken mask)
- the profile block renders portrait + meters + both pip rows, and the old
  free-standing rail is gone from the fragment
- every visited room resolves a 320×200 banner; floors 11–100 gate towns
  still resolve (the 320×112 fallback path)
- the shard note carries the `shard` mask at 32px and `to_text()` still says
  `◆`
- gate-scene floor rows carry fields art + warden art per opened floor,
  resolved by option id with no new Scene field
- `Scene.strip` round-trips `to_dict`/`from_dict`, renders the vault band
  with the coin in gold, is ignored when absent, and `to_text()` prints
  `DEPOSITED: ◈ n`
- `Scene.paper` renders ≤2 lines per item, its `✕` posts `news_close`, and
  `news_close` stamps `news_day` so the paper stays shut till dawn
- worldd condense: threshold lines for a floor collapse to the lowest; a
  fall line silences that floor's thresholds (worldd suite,
  `W/tests/`)
- lodge `talk` exists, speaks derived numbers, and rotates its telling;
  gate-town `talk` exists on floors 1–10 and is absent on floor 11
- the enemy plate: pips + HP over the banner top-right, each chip on an
  `INK` plate; dossier lists story first, then coin and XP ranges that
  bracket what `_victory` can actually roll (property test across specimens)
- floor movie: first `floor_3` entry plays beats then arrives; second entry
  goes straight to town; the fallen-warden beat names the killers from
  `fallen_by`; floor 11 plays the still-banner variant
- a 0.34 client renders a 030 scene: unknown `strip`/`paper` ignored, no
  crash (skew test, the `_known()` path)

Existing suites to update: `test_render.py` (new slots, rail moved),
`test_014_inventory_tooltips.py` (icon mode addition must not change `full`),
`test_017_bestiary.py` + `test_022_002_retune.py` (the `ASCENT_FULL_SIMS`
gate), `test_011_art.py` (portraits + new sizes join the coverage walk),
`test_no_emoji.py` (new surfaces).

## Ship

Straight to `main` per `no-branches.mdc`. Order: Phase 1 (the coin sweep
touches everything — land it first, alone), then 2–4 (renderer work, one
commit each), 5 (worldd + plugin, vendor-synced together), 6–8 (content +
assets as they bake), 9 last (flip the sim gate once the tuned band is
green). Vendor sync via `W/tools/vendor_game.sh` → worldd suite → dojo
browser pass at level 1 (rags portrait, empty pips) and level ~10 (suited,
pips half-full, a floor movie, a talkative fields NPC) → version bump →
publish → deploy → submodule pointer bump.

Wire note: every new Scene field rides top-level and skew-guarded; a 0.34
install must render a 030 scene as today's card, minus the new blocks.

Exit: `execution_summary.md` written here, including deviations.

## Out of scope

- Floors 11–100 per-floor art, NPCs, and movie motion (machinery ships,
  content later — the level-10 rule).
- Race/class portrait variants; portrait reactions (damage, death poses).
- Any combat-math, price, or pacing change — this plan draws, it does not
  retune.
- The sheet/pack cards of 028 Phase 4 (still 028's to ship); the town/lodge
  option icons of 028 remain 028's scope, though Phase 1's helpers will
  serve them.
- Animated portraits or per-gear-slot overlays.
