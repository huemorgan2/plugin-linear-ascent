# Plan 019 — One list per shop, and a pack worth opening

Goal: a shop card where **the list is the shop**. Every piece of gear the
counter can show you is one row in one list — buyable rows numbered,
locked rows carrying a lock instead of a number, owned rows saying so and
still buyable. Then make the pack a real place: see every copy you own,
wear it, stash it, repair it, spend the repair tokens the game already
hands out.

## 1. What's wrong today

The Forge card is two lists that describe the same shelf in two
different orders, plus a third list that only exists in prose:

| Today | Where it comes from |
|---|---|
| `Ashwood Bow, straight-grain ash, dependable — +8 ATK` (prose) | `_rack()` — `core.py:652-658` |
| `[1] Ashwood Bow ◈ 250` (row) | same loop, `opts.append(...)` |
| `🔒 Sinew-Backed Bow — level 6 (+12, ◈ 450)` | `_rack()` — `core.py:659-663`, **prose only, never a row** |
| `✓ Scrapwood Buckler — worn` | `_rack()` — `core.py:650-651`, **pulled out of the rack entirely** |
| `Pigsticker — not your weapon: ×3 the coin…` | `_forge_scene()` — `core.py:752-759`, a paragraph three lines away from row `[4]` |

Four concrete faults:

1. **Every item is printed twice** — once as a prose line with its stat,
   once as a numbered row with its price. The player has to correlate the
   two by name.
2. **Locked rungs aren't in the list at all.** They're prose. So the list
   answers "what can I buy" and the prose answers "what exists", and the
   two never line up.
3. **What you're wearing leaves the rack** (`_rack()` filters `worn` out
   of the buyable rows). You cannot buy a second copy of the piece on
   your body — even though the engine handles that fine (`_gear_purchase`
   already sends the replaced copy to the pack).
4. **The stat lives in the prose, the price lives in the row.** Neither
   row is self-describing, which is exactly what 004 §3.1's own retro
   asked for ("build shop rows on a STRUCTURED payload, not prose").

Same shape repeats in `_arcanum_scene`, `_medlab_scene`, `_relic_rows`
and `_pawn_scene` — fix the grammar once, all four shops inherit it.

## 2. The target card

```
ROOTHOLLOW · THE FORGE
Tier 1 steel, scrap to plasma
Blades, bows, plate and boots. A lock means the rung exists — come back with the level.

  — bows —
[1] 🏹 Ashwood Bow                                          ◈ 250
    +8 ATK · straight-grain ash, dependable                        [i]
[2] 🏹 Hunting Bow                                          ◈ 450
    +10 ATK · you have 1 already — worn                            [i]
[🔒] 🏹 Sinew-Backed Bow                                    ◈ 450
    level 6 · +12 ATK                                              [i]
  — armour —
[3] 🛡 Padded Jerkin                                        ◈ 200
    +7 DEF · you have 1 in your pack                               [i]
...
  — the other line —
[6] ⚔ Pigsticker                              ◈ 750 · off-class
    ×3 the coin, half the bite, one shot in four goes wide         [i]
  — the bench —
[7] Repair Pigsticker                              ◈ 1 + 2 XP
[8] Repair Scrapwood Buckler                       free · repair token
[9] Your pack                                      4 pieces, 2 relics
[10] Back to the square
```

Laws:

- **One row per thing.** The stat, the flavour and the "you have one"
  note ride the row as a dim sub-line. Prose keeps only atmosphere and
  purchase confirmations.
- **Locked rows sit in place**, in ladder order, with a lock chip where
  the number would be. Not clickable, not numbered — so numbers never
  shift when you level up past a lock.
- **Owning it doesn't hide it.** Worn or in the pack, the row stays
  buyable and says `you have N already`.

## 3. Phases

### Phase 1 — Option grammar (`scene.py`, `render.py`, `pane.py`)

1. `engine/scene.py` — three fields on `Option`, defaults keep every
   existing call site working:
   - `note: str = ""` — the dim sub-line (stat, flavour, ownership,
     unlock level).
   - `locked: bool = False` — lock chip instead of a number, not
     clickable, skipped by the numbering.
   - `section: str = ""` — a dim divider drawn before the first row that
     carries a new section name (retires the prose `— the relic shelf —`
     divider and the `▣` fold hack for shop shelves).
   - Carry all three through `to_dict` / `from_dict` (stored pending-event
     scenes from older docs load fine — defaults).
2. `Scene.numbered() -> list[tuple[int, Option]]` — the **one** place
   numbers are assigned: unlocked options only, 1..N in list order.
   `Scene.to_text()`, `render.render_scene_fragment()` and
   `core.apply_choice()`'s digit fallback all consume it, so the number
   the player sees is the number they can type, on every surface.
   `Scene.locked_ids()` for the guard below.
3. `to_text()` — locked rows print `(locked) Name — note` (the existing
   `🔒 → "locked"` substitution keeps `test_no_emoji` green); the note
   prints as a continuation line so the agent reads the same shop the
   player sees.
4. `core.apply_choice()` — two fixes:
   - digit fallback indexes `numbered()`, not `options` (today
     `options[int(x)-1]` — `core.py:102-103` — would count locked rows);
   - a locked id (from the agent, or a stale card) returns the scene with
     a `shard_note` built from the row's note ("Sinew-Backed Bow answers
     to level 6 hands"), and locked ids are excluded from the
     `Pick one of: …` list at `core.py:109-111`.
5. `render.py`:
   - `.orow` becomes a two-line grid: icon | label + note | hint.
   - `.opt.locked` — `disabled`, dim border, no hover, the 1-bit `lock`
     glyph (already in `icons._GRIDS`) in the `.key` cell, icon tinted
     `FAINT`.
   - section divider row (`.osec`), dim uppercase, same rhythm as
     `.eyebrow`.
6. Click wiring must ignore locked rows in **both** hosts: the card
   script (`render.py:543`) and the pane (`pane.py:265`) select
   `button.opt:not([disabled])`.

### Phase 2 — the racks read like a rack (`engine/core.py`)

1. Rewrite `_rack()` to emit rows, not prose pairs:
   - window per ladder = the worn rung (if buyable) + the last two
     buyable rungs + the next **1** locked rung;
   - `note` = stat + flavour, then ownership: `you have 1 already — worn`
     / `you have N in your pack`;
   - the worn rung is a **buyable row again** (drop the `g.slug != worn`
     filter) — a second copy is a legitimate purchase and the engine
     already stashes the replaced one;
   - locked row = `Option(f"buy_{slug}", name, hint=f"◈ {price:,}",
     note=f"level {req} · {stat}", locked=True, section=…)`;
   - no `body_lines` writes at all.
2. `_forge_scene()` — sections `bows`/`blades`, `shields`, `armour`,
   `boots`, `the other line`, `the relic shelf`, `the bench`, and the
   pack row. Off-class rows carry the ×3/half/miss line as `note`
   (paragraph deleted). `body_lines` shrinks to the honing-bench summary
   plus purchase confirmations; `support` re-worded to teach the lock.
3. `_relic_rows()` — rows carry `effect` + `The catch: limit` in `note`
   and `you hold N`; the `▣` fold and the prose block go away. Relics
   gated by floor/class appear **locked** with `floor N` / `sorcerer's
   work` as the note, so the shelf stops being invisible until it isn't.
4. `_arcanum_scene`, `_medlab_scene`, `_pawn_scene` — same grammar.
   Pawn note = `worn to 62% · you have 2`. Medlab items note their
   effect. Town square locked doors (`🔒 level N` in the hint —
   `core.py:518-542`) move to `locked=True` + note, and their existing
   refusal notes (`core.py:572-592`) become the locked-guard's message.
5. Length guard: the Forge list grows by up to 4 locked rows and up to 4
   retained worn rows, but loses ~14 prose lines — net shorter. A test
   pins "≤ 24 rows on a level-20 warrior card".

### Phase 3 — the pack becomes a place

1. **New location `pack`** (`_pack_scene`), reached from the square
   (`Your pack — N pieces, M relics`), the Forge and the Pawn shop.
   - worn block: 4 slots, each with stat + hone + durability % + damage
     type, or `nothing worn — the slot is free DEF you're not taking`;
   - pack block, sectioned: `spare gear` / `relics` / `kit` (apothecary,
     arrows, tokens), each row with count and per-copy wear;
   - rows act: `wear_{slug}` (exists), **`stash_{slot}`** (new — unequip
     to the pack keeping its durability; free starter gear warns that it
     goes to the scrap bin; the weapon slot falls back to the starter in
     stat math, which `state.gear_bonus` already does —
     `state.py:301-306`), `use_{slug}` where town-legal, and cross-links
     to the Forge (repair/hone) and the Pawn (sell).
2. **Per-copy wear (doc v6).** `durability_pack` is `slug → int` today —
   one wear number for a whole stack, so the second copy the player is
   now allowed to buy silently inherits or overwrites the first copy's
   wear. Make it `slug → list[int]`, one entry per copy:
   - migration `int → [int]` in `state.ensure_current` (never drop data);
   - wear-from-pack takes the freshest copy, pawn/donate takes the most
     worn (keeps 007's "the racks can never launder wear away" law);
   - touch points: `_gear_purchase` (`core.py:918-930`),
     `_wear_from_pack`, `_pawn_frac/_pawn_offer/_pawn_action`,
     `_pawn_donate`, `_repair_everything`, `_pack_strip`
     (`core.py:53-69` — the strip shows the worst copy's bar and `×N`).
3. **`repair_token` stops being dead code.** It's awarded by away
   presents (`core.py:251-253`) and nothing consumes it. Give it a row —
   `repair_{slot}` gains a free variant `hint="free · repair token"` at
   the Forge and in the pack — spending one token, no gold, no XP.
4. `sheet.character_sheet()` returns a structured pack (slug, name, kind,
   count, uses_left, stat) instead of the raw `inventory` dict, so
   `ascent_character` lets Luna talk about copies and wear accurately.
5. `engine/tips.py` — tips for `pack`, `stash_{slot}`, the token repair,
   locked buy rows (`_buy_tip` already names the level requirement) and
   locked relic rows.

### Phase 4 — tests, sync, publish

1. Unit — `tests/test_019_shop_rows.py`:
   - `numbered()` skips locked rows; the digit a player types resolves to
     the row that showed that digit, on card **and** in `to_text`;
   - a locked id refuses with a reason and moves no gold, no inventory;
   - the worn rung is still buyable; buying a second copy leaves the old
     copy in the pack with **its own** wear;
   - no name appears twice on one shop card (the anti-duplication guard);
   - forge row count ≤ 24 at level 20; `to_text` stays emoji-free.
2. Unit — `tests/test_019_pack.py`: stash → wear round-trips durability
   per copy; v5 → v6 migration (`int` → `[int]`) preserves every number;
   pawn sells the most-worn copy first; a repair token repairs exactly
   once and is consumed.
3. Update `tests/test_014_inventory_tooltips.py` — the walk visits the
   pack screen and asserts locked rows have tips too. Its `choose(p, "1")`
   digit calls exercise the new numbering for free.
4. `tests/test_render.py` — `.opt.locked` renders `disabled`, no `[n]`,
   a lock glyph; sections render as dividers; both hosts' click wiring
   skips disabled rows.
5. E2E scenarios in `tests/019-shop-rows-and-inventory/*.md` (devprocess
   §2), then the browser walkthrough (§4–5): as a level-3 archer, open
   the Forge and read the whole list top to bottom — every row explains
   itself, the locked rung sits in its ladder with a lock, the worn bow
   is still buyable and says so; buy a second Ashwood Bow and find both
   copies in the pack with different wear; stash the shield and see the
   DEF drop on the rail; spend a repair token.
   First-user query check: **reply with a plain number in chat** — the
   text fallback must select the same row the card numbered.
6. Vendor sync into `worldd/vendor/plugin_linear_ascent`, bump
   `version.py`, publish the zip. Per `.cursor/rules/no-branches.mdc`
   this work commits straight to `main` in both repos — no branch, even
   though devprocess §1 says otherwise.

## 4. Decisions taken (change here, not in code)

- **One locked rung ahead per ladder**, not the whole ladder — keeps 004
  §3.1's "the rung you're saving for" and the card short.
- **Locked rows are not clickable at all** (rather than clickable and
  refused, which is how the town's locked doors work today). The refusal
  path stays for agent/stale-card calls.
- **`inventory` stays `slug → count`** — only `durability_pack` becomes
  per-copy. A list-of-instances pack would be a bigger migration for no
  visible gain.
- **Numbers are assigned to unlocked rows only**, so levelling past a
  lock never renumbers the rows above it.

## 5. Risks

- Numbering is consumed in four places (card, pane, `to_text`, digit
  fallback). If any keeps its own `enumerate`, the player types 3 and
  buys 4. `Scene.numbered()` is the single source — a test asserts card
  and text agree row for row.
- `durability_pack` shape change touches pawn, donate, wear, purchase,
  strip and reincarnation. Migration must be idempotent and lossless
  (devprocess data rule).
- Longer option lists mean more `[i]` glyphs; the tips coverage guard
  will catch the missing ones, but locked/relic tips need writing.

Exit: all green, published, worldd synced, `execution_summary.md`.
