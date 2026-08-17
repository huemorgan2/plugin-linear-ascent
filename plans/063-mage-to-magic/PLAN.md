# 063 — "mage" → "magic", everywhere the game speaks

## Problem
The game names its caster line "caster" and its shop "the Arcanum", but
the word **mage** still leaks in a few places. Roy: "change mage to magic
in all the game — search everything and make it clear."

## Evidence (2026-08-17 sweep)
`grep -rniIw -E "mages?"` over plugin_linear_ascent, tests, tools, content,
vision, worldd/app, worldd/static/site (excluding vendor, fight3d, and
substrings like da**mage** / i**mage**):

| where | line | kind |
|---|---|---|
| plugin_linear_ascent/engine/core.py:1093 | `"mage gear"` — the square's Arcanum door hint | **player-visible** |
| plugin_linear_ascent/engine/core.py:1931 | `# 006: the mage relics` | comment |
| plugin_linear_ascent/economy.py:2301 | `# … the mage's wall-push cost …` | comment |
| tests/test_017_death_relics.py:649 | docstring "the mage vials" | comment |
| tests/test_022_001_one_list_of_bosses.py:151 | `playing("Mage", …)` character name | test data |
| tools/generate_banners.py:102 | Arcanum banner prompt "tall narrow mage shop" | art prompt |
| vision/economy.md:182 | "mage vials" retune note | doc |
| vision/lore/floors/floor_077.md:91 | "even without a mage" | lore |
| worldd/static/site/mock/roothollow.html:49 | old tip "The mage shop — …" | static mock |
| vision/kingdom-rush.md (8) | notes about Kingdom Rush's own "mage towers" | **left as is** — describes another game's units |

content/*.yaml, tips.py, render.py, worldd/app: 0 hits.

## Fix (one phase)
1. core.py:1093 `"mage gear"` → `"magic gear"`.
2. Comments/docstrings/prompt/docs/mock: mage → magic (phrasing kept
   grammatical: "the magic relics", "the caster's wall-push", "magic
   vials", "magic shop", "without magic").
3. Test character "Mage" → "Magic".
4. Guard test: `tests/test_063_no_mage.py` — no whole-word "mage" in any
   scene the engine can render for a fresh character (square, forge,
   arcanum, medlab, board, hall) nor in content/*.yaml, tips, render.

## Verification
- `grep -rniIw -E "mages?" plugin_linear_ascent tests tools content` → 0.
- New test passes; full plugin suite passes (minus the other session's 3
  known combat failures).

## Rollback
`git revert <commit>`; the strings are inert.

## Operational notes
Concurrent session holds uncommitted hunks in core.py / economy.py —
stage only the mage hunks (`git apply --cached` of a filtered diff).
