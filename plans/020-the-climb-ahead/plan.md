# Plan 020 — The Climb Ahead: nothing locked is invisible

Goal: a player at any level can answer **"what opens next, what does it cost,
and what do I lose"** without dying to find out. Every gate in the game comes
from one declarative registry; locked things sit visibly where they will
eventually live; the square carries the nearest one; the Stone carries the
whole ladder; and the sheet hands the same list to Luna.

## 1. The bug that started it

A level-3 climber cannot see that factions exist to be founded. Three
separate reasons, all of them structural:

| Fault | Where |
|---|---|
| The level-4 founding line is **prose at the bottom of the hall list** — printed after up to 5 faction rows, the armory block and the request counter. It is the least prominent thing on the longest card in the game. | `engine/social.py:409-412` |
| In **local dev mode** (no connected world) the gate is not mentioned at all, and `found_guild` is offered as a live option at *any* level as long as you carry ◈500 — then refused when clicked. | `engine/social.py:302-316` vs `:564-568` |
| The `found_guild` tooltip sells the feature in four lines and **never names the level**. The square's Guildhall hint reads `training` — founding is not in it. | `engine/tips.py:181-184`, `engine/core.py:528-529` |

And the near-miss: `GET /v1/faction/list` already returns `found_min_level`
and `found_fee` (`worldd/app/main.py:235-240`), and the COMMUNITY pane throws
both away.

## 2. The real problem behind it

The founding gate is not special. It is one of **31 gates** and the game has
no single owner for any of them. Each one hardcodes its own threshold at its
own call site and advertises itself — or doesn't — in its own way:

| Advertising style | Gates using it |
|---|---|
| `🔒 level N` in an option hint | Arcanum, Relay, the fields (`core.py:518-542`) |
| Prose body line | founding, next forge rung, hone cap |
| Support text only | grant receiver level 5 (`social.py:212`) |
| Nothing — you find out by failing | floor level req at the gate picker, relic floor/class gates, energy cap growth |
| Nothing, ever | **beginner's mercy ending**, **PvP immunity ending**, milestone quorum before floor 10 |

That last row is the dangerous one. Two protections **expire** and the game
never says so:

- `BEGINNER_MERCY_MAX_LEVEL = 3` (`economy.py:1050`) — at level 4 a PvE death
  stops keeping your gear. It starts rolling 20% weapon loss and 40-60% of
  carried gold (`combat.py:826-836`). The player who is level 3 right now
  buys that downgrade with the same ◈200 that buys them factions, and
  nothing on any card mentions it.
- `BEGINNER_PROTECTION_MAX_LEVEL = 5` (`economy.py:1049`) — at level 6 other
  climbers can ambush you (`worldd/app/social.py:290-293`). Never stated in
  the plugin at all.

So the fix is not "add a line about factions". It is: **make the gate table
data, generate every surface from it, and make it impossible to add a gate
without it appearing.**

## 3. The target

### 3.1 The square, always

```
ROOTHOLLOW · THE SQUARE
Roothollow — floor 3 is the frontier
The last free settlement. Everything starts and restarts here.

· Kettle opened floor 4
NEXT — LEVEL 4: your own banner at the Guildhall (◈ 500) · and beginner's
mercy ends: deaths start costing gear                          [i]
```

One dim line. The nearest unlock, its cost, its home — and any protection
that dies with it, because that is the half a player never sees coming.

### 3.2 The Guildhall, at level 3

```
ROOTHOLLOW · THE GUILDHALL
Banners for hire
Milestone Wardens fall to war parties, not heroes.

A banner pools coin, fields a war party, racks shared gear and enters the
world's weekly challenges — its prize is minted, not taken.

[1] Train to LEVEL 4                                        ◈ 200
    XP 340/340 — full bar, the fee is the only thing left           [i]
[2] Ask to join Kettle's Own                    join ◈ 0 · dues ◈ 5/wk
    4 at the table · admins settle requests at the desk             [i]
[🔒] Raise a new banner                                     ◈ 500
    level 4 · you set the join fee and dues, and steward the store  [i]
[3] Back to the square
```

The locked row **sits where the live row will be**, in the same list, one
level away. Nothing to hunt for in prose.

### 3.3 The Stone of the Climb — the whole ladder

The Stone already reads the world's record. Give it the personal one:

```
ROOTHOLLOW · THE STONE OF THE CLIMB
Floor 3 is the frontier · 14 climbers on the roll
...

▣ THE CLIMB AHEAD
  LEVEL 4   ◈ 200 to train, XP 340/340 — bar full
            + raise your own banner — Guildhall, ◈ 500
            − beginner's mercy ends: a death starts costing gear
  LEVEL 5   + the fields — ambush other climbers, 3 ⚡ a raid
            + other climbers can send you gold at the Vault
  LEVEL 6   + the Arcanum — staves, focuses, caster relics
            + Sinew-Backed Bow at the Forge (◈ 450, +12 ATK)
            − climbers can ambush you back
  FLOOR 6   + poison, slow and oiled arrows on the relic shelf
  FLOOR 10  ▲ Gnarl is a milestone Warden — no solo kill. A war party of
            2 pledges 5 ⚡ each at the Guildhall
  FLOOR 11  + tier-2 steel, the shoes' second rung, the honing cap resets
```

`+` opens, `−` closes, `▲` changes the rules. Same three-glyph grammar
everywhere, including `to_text()` so Luna reads the player's ladder verbatim.

## 4. Phases

### Phase 0 — prerequisite

020 renders locked things as rows, which is **plan 019 Phase 1**
(`Option.locked` / `.note` / `.section`, `Scene.numbered()`, the locked-id
guard, `.opt.locked` in `render.py` + `pane.py`). If 019 has not landed when
020 starts, land 019 Phase 1 first — it is six edits and everything below
assumes it. Do not build a second locked-row mechanism.

### Phase 1 — the registry (`unlocks.py`, new)

1. `plugin_linear_ascent/unlocks.py` — one frozen dataclass, one table:

   ```python
   @dataclass(frozen=True)
   class Unlock:
       id: str          # "found_faction"
       gate: str        # "level" | "floor"
       at: int          # the threshold
       effect: str      # "opens" | "closes" | "changes"
       title: str       # "raise your own banner"
       where: str       # "guildhall" — the location that hosts it
       why: str         # one line, the game's voice, numbers included
       cost: str = ""   # "◈ 500"
   ```

   Every entry reads its threshold **from the existing constant** —
   `economy.ARCANUM_LEVEL`, `social.FOUND_MIN_LEVEL`,
   `economy.BEGINNER_MERCY_MAX_LEVEL + 1`, … The registry is a view over the
   constants, never a second copy of the numbers.

2. Contents — 20 static entries plus two generated families:
   - **level, opens:** relay (3), shoes rung 2 (3), found a banner (4),
     the fields (5), receive grants (5), the Arcanum (6), tier-1.5 gear (6),
     tier-2 gear (11), …
   - **level, closes:** beginner's mercy (4), PvP immunity (6).
   - **level, changes:** energy cap +1 every 10 levels
     (`economy.energy_cap`).
   - **floor, opens:** relic shelf tiers (6, 11, 21, 31 — read from the
     relic catalog, not hand-listed), gear bands and the honing cap reset
     (`economy.band_start`).
   - **floor, changes:** milestone Wardens every 10 floors with their
     quorum — generated, so floor 40's "war party of 5" needs no new entry.
   - **generated:** the next floor's level requirement
     (`economy.floor_level_req`).

3. API:
   - `met(p, u) -> bool`
   - `ahead(p, limit=0) -> list[Unlock]` — unmet, sorted by distance then
     `gate`, grouped by `(gate, at)` for rendering.
   - `just_reached(p, old_level, old_floor) -> list[Unlock]` — for the
     level-up and floor-open announcements.
   - `for_option(oid) -> Unlock | None` — so a locked row and the registry
     never disagree on the reason.

### Phase 2 — the surfaces read the registry

1. **The Guildhall** (`engine/social.py`) — the whole point:
   - `_hall_list()` opens with the value line ("A banner pools coin, fields
     a war party, racks shared gear…") so a non-member learns what the
     feature *is* before the price.
   - `found_guild` becomes **always a row**: live when eligible, else
     `locked=True` with `note` from the registry (`level 4` or
     `◈ 500 — you carry ◈ 120`). The prose lines at `:409-417` go away.
   - The **dev-mode branch** (`:302-316`) calls the same helper, so the gate
     exists with or without a world. This kills the offer-then-refuse bug.
   - `guildhall_scene` shows the row in both the member and non-member
     panels — a member sees `[🔒] Raise a new banner — leave your banner
     first`, because "why is this not here" is a real question.
2. **The square** (`engine/core.py`):
   - the `NEXT — …` footer line from `unlocks.ahead(p, 1)`, with a tip;
   - the three hardcoded `🔒 level N` hints (`:518-542`) and their three
     refusal `shard_note`s (`:572-592`) are generated from the registry —
     one grammar, three fewer places to forget;
   - the Guildhall hint becomes `training · banners`.
3. **The Stone** (`_stone_scene`) — the `THE CLIMB AHEAD` fold from
   `ahead(p, limit=8)`, grouped by threshold, `+ / − / ▲` per entry.
4. **The gate floor picker** — floors past `floor_level_req` become locked
   rows (`level N legs`) instead of live rows that refuse
   (`core.py:1436-1441`); milestone floors carry `war party of N` in the
   note whether or not they are reachable.
5. **The Vault / grants desk** — the level-5 receiver rule moves from
   support prose into the registry-fed note.
6. **The COMMUNITY pane** (`pane.py`) — the ledger prints the
   `found_min_level` / `found_fee` the API already returns, and the
   "no banners raised yet" empty state names the level.

### Phase 3 — the moment it changes

1. **`guild_train()`** — the level-up note appends `just_reached()`:
   `+ LEVEL 4 … The hall will charter your banner now (◈ 500). And the
   tower stops being gentle: a death from here costs gear.` Levels are
   *bought*, so this is a card the player is guaranteed to read.
2. **Warden victory** (`combat.py:719-752`) — a first clear appends what the
   new frontier opened: the relic tier, the gear band, the honing cap reset.
3. **The first unprotected death** — the death card names the change once
   (`the tower is no longer gentle with you`) so the loss is legible even if
   the player skipped Phase 3.1.
4. **Milestone floor pre-warning** — entering the floor *below* a milestone
   (9, 19, 29…) warns that the next Warden takes a war party, at the gate,
   before the ⚡ is spent.

### Phase 4 — Luna knows the ladder

1. `sheet.character_sheet()` gains `next_unlocks: list[dict]` (the registry
   rows, distance included) and `protections_active: list[str]`. Luna can
   then answer "what should I do next" and "what do I lose at level 4" from
   data instead of guessing.
2. `_GUIDE_RULES` (`plugin.py:53-78`) — early-game coaching names the
   level-4 double edge and points at `ascent_character` for the ladder.
   Today it stops at "◈200 buys your first level".
3. `engine/tips.py` — `found_guild` names the level and the fee; new tips for
   the square footer, the Stone fold, locked floor rows and every locked
   row the registry generates (`_locked_tip(u)` from `u.why` + `u.cost`, so
   coverage is automatic and `test_014`'s guard stays green).

### Phase 5 — tests, sync, publish

1. `tests/test_020_unlocks.py`:
   - **coverage guard** — every `economy.py` constant matching
     `*_LEVEL|*_MIN_LEVEL|*_MAX_LEVEL` and every `FOUND_MIN_LEVEL` has a
     registry entry. Adding a gate without registering it fails here. This
     is the test that keeps 020 true a year from now.
   - `ahead()` ordering and grouping; nothing already met appears; a
     level-1 player and a level-95 player both get a sane list (the level-95
     one may be empty — assert it renders as "the ladder is yours").
   - `just_reached(level 3 → 4)` returns exactly founding + mercy-ends.
   - registry thresholds equal the live constants (no drift copies).
2. `tests/test_020_visible_gates.py` — the walk test: a level-3 player with
   ◈600 and a level-3 player with ◈0, **in both world mode and dev mode**,
   sees a `found_guild` row on the Guildhall card, locked, with the level in
   its note. Plus: no card offers a live option the engine then refuses
   (walk every town scene at levels 1-6, cross-check every option id against
   the registry).
3. `worldd/tests/` — assert `factions.FOUND_MIN_LEVEL` matches the plugin
   registry entry, so the two repos cannot drift.
4. Update `test_015_desk.py` — its four gating tests assert on
   `body_lines` prose (`"level 4+" in ln`). They move to asserting a locked
   row, which is the actual contract now.
5. E2E scenarios in `tests/020-the-climb-ahead/*.md`, then the browser
   walkthrough (devprocess §4-5) as a **level-3 climber**: read the square
   footer, open the Guildhall and find the locked banner row, open the Stone
   and read the ladder, train to level 4 and see both halves announced, then
   raise the banner. Ask Luna "what's next for me?" in chat and check she
   answers from `next_unlocks` and mentions the mercy ending.
6. Vendor sync into `worldd/vendor/plugin_linear_ascent`, bump `version.py`,
   publish the zip. Per `.cursor/rules/no-branches.mdc` this commits straight
   to `main` in both repos — no branch, whatever devprocess §1 says.

## 5. Decisions taken (change here, not in code)

- **The registry is a view, not a source.** Thresholds stay in `economy.py`
  and `social.py`; `unlocks.py` imports them. A registry that restates the
  numbers is a second place to be wrong.
- **Closing things are first-class.** `effect="closes"` exists because the
  two most expensive surprises in the game are protections expiring, not
  features arriving. A ladder that only lists gifts is a lie.
- **Locked rows sit in their real list**, in their real position (019's law).
  A separate "locked stuff" panel would be read once and never again.
- **The nearest unlock only, on the square.** One line. The full ladder is
  one click away at the Stone. The square is already 12 options long.
- **Eight entries max at the Stone**, then `…and the tower keeps the rest`.
  A level-1 player must not read floor 91's gear band.
- **No new town location.** The Stone of the Climb is already "the record of
  the climb" — the personal ladder belongs to it, and it needs no new door,
  no new banner art, no new tip family.
- **Founding stays level 4 and ◈500.** This plan makes the gate legible; it
  does not renegotiate it. If playtest says level 4 is wrong, that is a
  balance change in a later plan.

## 6. Risks

- **Card length.** The Guildhall member panel is already the longest card in
  the game (store, week, up to 8 members, armory, requests). Adding a locked
  row is +2 lines, but the pre-warnings in Phase 3.4 and the Stone fold need
  the row budget watched — pin a max-rows test like 019 §Phase 2.5 does.
- **Registry drift with worldd.** Founding is gated in two repos
  (`social.py:254` and `worldd/app/factions.py:39`). Phase 5.3's
  cross-repo assertion is the only thing stopping a silent split; it must
  run in both test suites, not just one.
- **Spoiler surface.** Generated floor entries could leak the whole bestiary
  and relic catalog to a new player. `ahead()` is capped and floor entries
  are limited to bands and milestones — never named monsters.
- **`test_015_desk.py` and `test_no_emoji.py`** both key off the current
  prose. Expect to rewrite the four desk gating tests, and check the
  `🔒 → "locked"` substitution still covers the new `+ / − / ▲` glyphs in
  `to_text()` (`scene.py:101`).
- **Old stored scenes.** Docs holding a pending scene from before 019 must
  still load; `Option` defaults cover it, but the Guildhall's typed-reply
  founding flow (`founding_guild` state) is the one place a stale scene can
  land mid-flow — test a v-old doc through it.

Exit: all green, published, worldd synced, `execution_summary.md` written.
