# Phase 003 — The enemy [i] card: execution summary

Shipped as **0.20.0** (plugin published, worldd vendor synced + deployed,
production health green). Branch `017-combat-depth`, merged to `main`.

## What landed

- **`scene.enemy` payload.** Every fight scene now carries a structured
  enemy block (name, hp/hp_max, atk/def, profile, named tiers, range,
  lore, specimen, both speeds, damage type, dodge%). Survives the
  to_dict/from_dict roundtrip and feeds both the HTML card and the
  `to_text()` fallback, so the agent sees the same facts the player does.
- **Fight header.** Always-on enemy HP bar from round 1 (mirrors the
  player meters, goes `low` under 35%), a range chip (`at range` /
  `close`), and an active-modifier chip — "bow ×0.6", "its hits ×0.5",
  "can't swing yet", "it can't be reached" — the 002-retro fix: the bow
  collapse now says why on screen.
- **The [i] dossier.** A `<details>` element styled as an `[i]` badge.
  Opens to trait rows with 1-bit mask icons (armor shield, magic shield,
  wing, hare, bulwark; wrench reserved for 005): each row names the tier
  and what it means for YOUR damage type ("plate — Medium. Spellwork
  ignores it."). Speed row reads the chase for both sides. Active
  modifiers are named in full sentences. Lore closes the card.
- **The bare ◆ retired** (001 retro): the opener's profile line and the
  range line left `body_lines`; the header + dossier own that job now.
  Headline keeps ATK/DEF, never HP.
- **Scout upgrade.** Exact stats + profile + next-intent line: "It will
  try to close this round — 55% it makes it." / warnings about the fast
  in close quarters.
- **Lore.** Optional `lore:` per encounter, ≤160 chars, prose-linted.
  Authored for all 40 encounters on floors 1–10.
- **Icons.** Six new 16×16 1-bit grids in `icons.py`, shipped as
  CSS-mask SVG data-URLs (zero network requests, tintable).

## Verification

- 264/264 tests. New `test_017_info_card.py` (21 tests): payload
  presence + roundtrip, lore reach/lint/coverage, dossier renders every
  profile combination, modifier naming, chase reading, HP-bar math and
  low state, range/modifier chips, fragment wiring, icon masks, scout
  intent both ways, headline shape.
- Card specimens: dossier cases added to `tools/card_specimens.py`
  (armored / flying / fast, forced `<details open>`).
- Dojo (browser, local Luna + worldd, qa007): armored kingsguard as
  sorcerer — dossier says "plate — Medium. Spellwork ignores it.";
  flying glare moth as warrior — "airborne" row, swing "cuts empty air",
  HP bar unmoved; fast courser as archer — "bow ×0.6" chip visible in
  close quarters; scout mid-fight named stats, profile and the close
  intent with a percentage. The one-glance test passes: "why is this
  fight bad for me" is answerable from the card alone.

## Learnings (applied to future phase plans)

1. **HTML-escaping bites assertions.** `can't` renders as `can&#x27;t`
   — dossier/card tests must assert on apostrophe-free substrings or
   unescape first. Applies to every phase that tests rendered HTML.
2. **`<details>` needs no JS and no card-action plumbing.** The plan
   budgeted 057 action plumbing for the [i] badge; a styled `<details>`
   did it with zero round-trips. Prefer it for any collapsible UI
   (004 shop rows, 006 relic inspection).
3. **Specimen `player()` must skip intro beats** — fixed in
   `card_specimens.py`; any phase adding specimens builds on a player
   already in `stage=play`.
4. **Injected fights race the client.** Forcing a state via SQL then
   reading the card can catch mid-render output; inject, reload, settle,
   then read (twice on a miss) — same rule as the 002 range-line lesson.
5. **Structured scene payloads beat prose lines.** Moving enemy facts
   from `body_lines` into `scene.enemy` made both the UI and the agent
   grounding cheaper to test. 004 (shop rows) and 006 (relics) should
   carry structured payloads from day one rather than parsing prose.
