# 059 — the faction block under the profile, and one word: FACTION

Under the player profile (portrait + meters + pack), a block that says
where you stand with the factions. A member sees their banner on the
left, then the faction's name, how many climbers sit at the table and
how many of them are online right now, plus a door into the Playing
panel's faction tab. A climber with no faction sees one clear ask —
JOIN A FACTION — with the count of factions flying, and it walks them to
the page that lists every faction they can join.

Alongside: the game says **faction** and only faction for the group. A
faction *has* a banner (its colors, the PNG); "banner" stops meaning the
group. The Guildhall is the building where the factions live.

## The word

- faction = the group. `ascent_factions`, the Playing tab, the homepage
  and the profile line ("brother of the X faction") already say it.
- banner = the object a faction flies (its art). Kept for that only:
  "pick the mark your faction flies", the sigil grid, `f["banner"]`.
- guild = never a noun for the group in the UI. "Guildhall" stays as the
  building's name. Internal ids (`found_guild`, `guild_leave`,
  `hall_ledger`, `p["guild"]`) don't change — they're wire, not words.
- group = not used.

Guildhall header: `ROOTHOLLOW · THE GUILDHALL — home of all the factions`.

## Level gates (facts, so the copy is honest)

- Joining has **no** global level gate — a level-1 climber can join any
  faction whose door (steward-set `min_level`, default 0) admits them.
  So the profile block never locks JOIN behind a level; the per-faction
  door is shown on the listing page as today.
- Founding is gated: `FOUND_MIN_LEVEL = 4`, `◈ 300`. Below level 4 the
  block adds a faint second line: `found your own · 🔒 level 4`.

## Data (worldd → engine → renderer)

1. `worldd/app/factions.py:members_of` — add `p.updated_at` and
   `p.doc->>'stage'` to the SELECT; each member row gains
   `online: bool` = `stage == 'playing' and updated_at > now() - 5 min`
   (same window as `social.ONLINE_WINDOW_MIN`).
2. `worldd/app/social.py:_faction_panel` — return two new ints:
   `"members_count": len(members)`, `"online": sum(m["online"])`. The
   `members` list already rides in `w["faction"]`; each entry also gets
   `"online"`.
3. Non-members already get `w["factions_total"]` (count of factions).
4. `engine/scene.py:Meters` — four new fields, all defaulted so an older
   wire omits the block:
   `faction_banner: str = ""`, `faction_members: int = 0`,
   `faction_online: int = 0`, `factions_total: int = -1` (-1 = not sent).
5. `engine/combat.py:meters(p)` fills them from `p["_world"]["faction"]`
   / `p["_world"]["factions_total"]`. Local dev mode (no `_world`):
   member of a legacy doc-guild → name only, counts 0; else block shows
   JOIN with no count.

## Renderer (`render.py`)

`_faction_block(m)` appended right after `_profile_html` in
`render_scene_fragment` (`render.py:1974`), full card width, class
`.facblk later`:

- **Member:**
  `[banner img 40px tall, width auto] NAME · 12 climbers · 3 online now
  [ FACTION ACTIVITY → ]`
  Banner via `_banner_data_url(slug)` (base64, ~5 KB). The button is
  `<button class="opt facact" data-play="faction">` — not a `data-opt`
  (no server round trip); the pane opens the Playing panel on the
  faction tab.
- **No faction:**
  `[ JOIN A FACTION · 7 factions ]` — `<button class="opt facjoin"
  data-tab="community">`; below level 4 a faint line
  `found your own · 🔒 level 4`. When `factions_total == 0`:
  `no faction flies yet — be the first (level 4)`.
- CSS: `.facblk` grid `auto 1fr auto`, dashed top border like the pack,
  phone stacks to two rows. Reuse ANSI palette constants.

## Pane (`pane.py`)

- Export `window.__laPlaying = (tab) => { ply.tab = tab; plyOpen(); }`
  next to `plyOpen` (matches `__laSfx`/`__laWire` convention).
- Delegated click on `#game`: `[data-play]` → `__laPlaying(tab)`;
  `[data-tab]` → `switchTab(tab)`.
- COMMUNITY tab made clearer as "the page with all the factions":
  ledger eyebrow → `ALL FACTIONS — N flying · ask to join any row`,
  the CTA panel headline → `you climb in no faction`, copy uses
  "faction" throughout, browse limit 10 → 50 (`factions.search_factions`).

## Guildhall (`engine/social.py`)

- Eyebrow `ROOTHOLLOW · THE GUILDHALL — home of all the factions`.
- `_join_rows` / `_hall_list`: the directory row is **always** present:
  `Join a faction` · hint `N factions · the directory` (or `none fly yet
  — found the first`). Founding row → `Found a new faction`.
- Word pass over every user-facing string in `engine/social.py`,
  `engine/hall.py`, `engine/profile.py`, `engine/tips.py`,
  `engine/notices.py`, `unlocks.py`, `pane.py`, `render.py`, worldd
  `social.py`/`factions.py` lines that reach the feed: "banner" as the
  group → "faction" ("Leave the banner" → "Leave the faction", "Every
  banner that flies" → "Every faction that flies", "the {name} banner
  takes you" → "the {name} faction takes you", "One banner per climber"
  → "One faction per climber", "no banner" → "no faction", etc.). Kept:
  "Name your faction" / "Pick the mark your faction flies" (that IS the
  banner), art slugs, `banner=` fields.
- Tests asserting the old strings are updated in the same commit.

## Tests

- worldd `tests/test_059_faction_block.py`: `members_of` marks a fresh
  playing member online and a stale one not; `_faction_panel` returns
  `members_count`/`online`; `inject_world` non-member carries
  `factions_total`.
- plugin `tests/test_059_faction_block.py`: `meters()` fills the four
  fields from `_world`; fragment for a member contains `.facblk`, the
  name, `N climbers`, `M online now`, `data-play="faction"`; for a
  non-member contains `JOIN A FACTION`, `data-tab="community"`, the lock
  line under level 4 and not at 4+; guildhall scene eyebrow and always
  offers `hall_ledger`; no user-facing "banner"-as-group strings in the
  guildhall/directory scenes (assert on the specific renamed lines).

## Order

1. worldd: `members_of` + `_faction_panel` + tests.
2. engine: Meters + `meters()`; guildhall copy; word pass; test fixes.
3. render: `_faction_block` + CSS; pane: `__laPlaying`, delegated clicks,
   COMMUNITY copy.
4. Bump, vendor, commit both repos.
